#!/usr/bin/env python3
"""outreach — the three-touch sequence, per channel, that the estate now runs itself.

This changes a standing rule. Until 2026-11-10 the estate researched leads and a human pressed send
("never send from an automated system"). The owner reversed that on 2026-11-10:

    "after a lead is identified and their contacts got, the system drafts outreach for every channel
     we have their contacts. For rails we can actually autonomously send outreach — email, bluesky,
     mastodon — the system should send."

So this file is the sender. The sequence, per lead per channel:

    touch 1   T+0     emotional, plain text, no HTML, no links, no attachments.
                      The only call to action is a phrase: "reply TENDERS".
    touch 2   T+48h   the freebie: a link to a plain-text page written for that one organisation.
    touch 3   T+72h   one last touch, short, then the sequence ends for that channel for good.

A reply at any point — to any channel — stops every channel's sequence for that lead and moves them to
`freebie`. The sequence is capped, jittered, business-hours only, and it refuses to touch a domain on
the do-not-contact list. Every send is an event in an append-only log, so "what did we actually say to
whom" is a query, not a guess.

    python3 growth/outreach.py --status              # who is where in the sequence
    python3 growth/outreach.py --draft tensor.co.zw  # draft every channel we hold a contact for
    python3 growth/outreach.py --due --dry           # what would go out right now
    python3 growth/outreach.py --due                 # send what is due (caps, window, DNC respected)
    python3 growth/outreach.py --replied tensor.co.zw --channel email --phrase TENDERS
    python3 growth/outreach.py --selftest

Which rails can actually send is a property of the rail, not of optimism:

    email      SMTP_* env present       → sends
    mastodon   lead has a handle        → sends a direct status (visibility=direct)
    bluesky    no DM endpoint exists in the AT Protocol public API → drafts only
    reddit     needs a script app       → drafts only until configured
    whatsapp   no API for this          → drafts only, as a copy-paste block

Anything that cannot send still gets a draft in growth/outreach/outbox/, so the channel is never simply
dropped — and the status line says which is which, because a rail that silently does nothing is the
failure mode this estate keeps writing papers about.
"""
from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import hashlib
import json
import os
import random
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEADS = HERE / "leads"
STORE = LEADS / "store.jsonl"
DNC = HERE / "dnc.txt"
PROFILES = HERE / "ventures.yaml"
OUT = HERE / "outreach"
STATE = OUT / "state.jsonl"
OUTBOX = OUT / "outbox"
FREEBIES = ROOT / "assets" / "freebies"
PUBLIC_FREEBIE = "https://jacaranda-labs.pages.dev/assets/freebies"

TOUCH_GAP_2 = 48          # hours after touch 1
TOUCH_GAP_3 = 72          # hours after touch 2
MAX_TOUCHES = 3
DAILY_CAP = {"email": 20, "mastodon": 10, "bluesky": 10, "reddit": 5, "whatsapp": 5}
SEND_HOURS = (7, 18)      # Africa/Harare; outside this the sequence waits
UA = "JacarandaOutreach/1.0 (+https://jacaranda-labs.pages.dev; couragegarikai@atomicmail.io)"


# --------------------------------------------------------------------------- store
def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(t: dt.datetime | None = None) -> str:
    return (t or now()).isoformat().replace("+00:00", "Z")


def load_leads() -> list[dict]:
    rows = []
    if STORE.exists():
        for line in STORE.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    for csv_path in sorted(LEADS.glob("*.csv")):
        with csv_path.open() as f:
            for row in csv.DictReader(f):
                if row.get("domain") and not any(r.get("domain") == row["domain"] for r in rows):
                    rows.append(row)
    return rows


def events() -> list[dict]:
    if not STATE.exists():
        return []
    out = []
    for line in STATE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def log(ev: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with STATE.open("a") as f:
        f.write(json.dumps({"at": iso(), **ev}, ensure_ascii=False) + "\n")


def dnc() -> set[str]:
    if not DNC.exists():
        return set()
    return {ln.strip().lower() for ln in DNC.read_text().splitlines()
            if ln.strip() and not ln.startswith("#")}


# --------------------------------------------------------------------------- rails
def smtp_env() -> dict:
    keys = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")
    return {k: os.environ.get(k, "") for k in keys}


def mastodon_env() -> tuple[str, str]:
    host = (os.environ.get("OUTREACH_MASTODON_INSTANCE") or
            os.environ.get("JACARANDA_MASTODON_INSTANCE") or "mastodon.social")
    tok = os.environ.get("OUTREACH_MASTODON_TOKEN") or os.environ.get("JACARANDA_MASTODON_TOKEN", "")
    return host.replace("https://", "").strip("/"), tok


def rails() -> dict[str, dict]:
    """What can send, today, and why not when it cannot."""
    sm = smtp_env()
    host, tok = mastodon_env()
    return {
        "email": {"can_send": all(sm.values()),
                  "why": "SMTP configured" if all(sm.values()) else
                         "no SMTP_HOST/PORT/USER/PASS — drafting only (.eml in outbox/)"},
        "mastodon": {"can_send": bool(tok),
                     "why": "direct status available" if tok else "no mastodon token — drafting only"},
        "bluesky": {"can_send": False,
                    "why": "the AT Protocol public API has no DM endpoint — drafting only"},
        "reddit": {"can_send": bool(os.environ.get("OUTREACH_REDDIT_CID")),
                   "why": "script app configured" if os.environ.get("OUTREACH_REDDIT_CID")
                          else "no reddit app — drafting only"},
        "whatsapp": {"can_send": False, "why": "no send API — drafting only, as a copy-paste block"},
    }


# --------------------------------------------------------------------------- copy
def venture_of(lead: dict) -> dict:
    prof = yaml.safe_load(PROFILES.read_text())
    v = (prof.get("ventures") or {}).get(lead.get("venture") or "", {})
    return {"id": lead.get("venture") or "jacaranda", **v,
            "sender": (prof.get("defaults") or {}).get("sender", "Courage Garikai")}


def first_name(lead: dict) -> str:
    for field in ("contact_name", "name"):
        v = (lead.get(field) or "").strip()
        if v:
            return v.split()[0]
    return ""


def keyword(venture: dict) -> str:
    return (venture.get("reply_phrase") or venture.get("name") or "YES").upper().replace(" ", "")


def host_of(lead: dict) -> str:
    return (lead.get("domain") or "").lower().replace("https://", "").strip("/")


def observation(lead: dict) -> str:
    """The one concrete thing we noticed about them. Comes from the hunter's `why` field."""
    why = (lead.get("why") or "").strip()
    if why:
        return why.rstrip(".")
    title = (lead.get("title") or host_of(lead)).split("|")[0].strip()
    return f"your page says what {title} does, and it is the kind of work this was built for"


def freebie_text(lead: dict, venture: dict) -> str:
    """The personalised, plain-text freebie. No HTML, no pitch, no links inside it."""
    name = first_name(lead)
    greet = f"Hello {name}," if name else "Hello,"
    company = (lead.get("title") or host_of(lead)).split("|")[0].strip() or host_of(lead)
    lines = [
        f"{venture.get('name', 'Jacaranda Labs')} · a note for {company}",
        "",
        greet,
        "",
        observation(lead) + ".",
        "",
        (venture.get("freebie_intro") or
         "So rather than send a brochure, here is the thing itself, written for you and nobody else:"),
        "",
        (venture.get("freebie_body") or
         "Three things worth doing this week, in the order I would do them, given what your site "
         "currently shows. Nothing here needs a purchase, an account, or a reply."),
        "",
        "1. " + (venture.get("freebie_step_1") or "Name the one number you would want to move this "
              "quarter, and write it where you can see it."),
        "2. " + (venture.get("freebie_step_2") or "Find the smallest change that would move it, and "
              "give it an owner and a date."),
        "3. " + (venture.get("freebie_step_3") or "Write down what would tell you it worked — before "
              "you start, not after."),
        "",
        "That is the whole freebie. If it is useful, I am glad. If you want the version built into "
        "your own site or desk, reply and say so, and I will send the price in one line — no call, "
        "no calendar.",
        "",
        "Either way: thank you for reading this far.",
        "",
        "Courage",
        "Jacaranda Labs · Harare",
    ]
    return "\n".join(lines)


def freebie_slug(lead: dict) -> str:
    return re.sub(r"[^a-z0-9]+", "-", f"{host_of(lead)}").strip("-")[:60] or "lead"


def write_freebie(lead: dict, venture: dict) -> str:
    """Write the freebie as a published plain-text file and return its URL."""
    d = FREEBIES / (venture.get("id") or "general")
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{freebie_slug(lead)}.txt"
    path.write_text(freebie_text(lead, venture))
    return f"{PUBLIC_FREEBIE}/{venture.get('id', 'general')}/{path.name}"


def touch_copy(lead: dict, venture: dict, step: int, freebie_url: str) -> tuple[str, str]:
    """Subject/body for one touch. Plain text only, and short enough to read on a phone."""
    name = first_name(lead)
    hi = f"{name}," if name else "Hello,"
    phrase = keyword(venture)
    company = (lead.get("title") or host_of(lead)).split("|")[0].strip() or host_of(lead)

    if step == 1:
        subject = f"{company} — one thing I noticed"
        body = (
            f"{hi}\n\n"
            f"{observation(lead)}.\n\n"
            f"I built {venture.get('name', 'something')} for exactly that kind of work — "
            f"{(venture.get('sells') or 'it helps with the part nobody has time for')}. "
            f"I would rather show you than describe it.\n\n"
            f"There is a short piece written for {company} specifically — no pitch, no links, "
            f"nothing to sign up for. If you want it, reply with the word {phrase} and it comes "
            f"back to you in plain text.\n\n"
            f"If it is not for you, reply STOP and I will not write again.\n\n"
            f"— Courage\n"
            f"Jacaranda Labs, Harare\n"
        )
        return subject, body

    if step == 2:
        subject = f"the {company} note (as promised)"
        body = (
            f"{hi}\n\n"
            f"Here is the piece I mentioned, written for {company}:\n\n"
            f"{freebie_url}\n\n"
            f"It is a plain text page — no images, no tracking, no forms. Read it on a phone in "
            f"about ninety seconds.\n\n"
            f"If you would rather have it in an email body, say the word and I will paste it in.\n\n"
            f"— Courage\n"
            f"Jacaranda Labs, Harare\n\n"
            f"(If you would prefer I stop, reply STOP.)\n"
        )
        return subject, body

    subject = f"last note, {company}"
    body = (
        f"{hi}\n\n"
        f"Last one from me — I said I would not keep writing if it was not useful, so this is the "
        f"end of it.\n\n"
        f"The note is still here if you ever want it: {freebie_url}\n\n"
        f"If {venture.get('name', 'this')} becomes relevant, the door is open and the price is on "
        f"the page — no call needed.\n\n"
        f"Wishing {company} a good quarter.\n\n"
        f"— Courage\n"
        f"Jacaranda Labs, Harare\n"
    )
    return subject, body


# --------------------------------------------------------------------------- sending
def send_email(lead: dict, subject: str, body: str, sender: str) -> tuple[bool, str]:
    sm = smtp_env()
    if not all(sm.values()):
        return False, "skip: no SMTP configured"
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = lead.get("email") or ""
    msg["Subject"] = subject
    msg["Message-ID"] = f"<{hashlib.sha1(f'{host_of(lead)}|{subject}|{time.time()}'.encode()).hexdigest()}@atomicmail.io>"
    msg["List-Unsubscribe"] = "<mailto:couragegarikai@atomicmail.io?subject=unsubscribe>"
    msg.set_content(body)                      # plain text only; no HTML part, ever
    port = int(sm["SMTP_PORT"] or 587)
    try:
        ctx = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(sm["SMTP_HOST"], port, context=ctx, timeout=30) as s:
                s.login(sm["SMTP_USER"], sm["SMTP_PASS"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(sm["SMTP_HOST"], port, timeout=30) as s:
                s.starttls(context=ctx)
                s.login(sm["SMTP_USER"], sm["SMTP_PASS"])
                s.send_message(msg)
        return True, f"sent to {lead.get('email')}"
    except Exception as exc:                    # noqa: BLE001
        return False, f"smtp {type(exc).__name__}: {str(exc)[:90]}"


def send_mastodon(lead: dict, body: str) -> tuple[bool, str]:
    handle = (lead.get("mastodon") or "").strip()
    host, tok = mastodon_env()
    if not tok:
        return False, "skip: no mastodon token"
    if not handle:
        return False, "skip: lead has no mastodon handle"
    if not handle.startswith("@"):
        handle = "@" + handle
    fields = urllib.parse.urlencode({"status": f"{handle}\n\n{body}"[:4900], "visibility": "direct"})
    req = urllib.request.Request(f"https://{host}/api/v1/statuses", data=fields.encode(),
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "application/x-www-form-urlencoded",
                                          "User-Agent": UA}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            doc = json.loads(r.read() or b"{}")
        return True, f"direct status {doc.get('url') or doc.get('id')}"
    except urllib.error.HTTPError as exc:
        return False, f"mastodon {exc.code}: {exc.read()[:90].decode('utf-8', 'ignore')}"
    except Exception as exc:                    # noqa: BLE001
        return False, f"mastodon {type(exc).__name__}"


def draft_file(lead: dict, channel: str, step: int, subject: str, body: str) -> Path:
    """A draft for a rail that cannot send: written where a human (or an app) will find it."""
    d = OUTBOX / channel
    d.mkdir(parents=True, exist_ok=True)
    slug = freebie_slug(lead)
    path = d / f"{slug}-touch{step}.txt"
    head = (f"to:      {lead.get(channel) or lead.get('email') or host_of(lead)}\n"
            f"channel: {channel}\nstep:    {step}\nsubject: {subject}\n"
            f"lead:    {host_of(lead)}\n---\n")
    path.write_text(head + body)
    return path


def send_one(lead: dict, channel: str, step: int, subject: str, body: str,
             sender: str) -> tuple[bool, str]:
    target = (lead.get(channel) if channel != "email" else lead.get("email")) or ""
    if not target and channel != "whatsapp":
        return False, f"skip: lead has no {channel} contact"
    if channel == "email":
        return send_email(lead, subject, body, sender)
    if channel == "mastodon":
        return send_mastodon(lead, body)
    return False, f"skip: {channel} cannot send"


# --------------------------------------------------------------------------- state machine
CHANNELS = ("email", "bluesky", "mastodon", "reddit", "whatsapp")


def contacts(lead: dict) -> list[str]:
    """Every channel we actually hold a contact for on this lead."""
    held = []
    if (lead.get("email") or "").strip():
        held.append("email")
    for ch in ("bluesky", "mastodon", "reddit", "whatsapp"):
        value = (lead.get(ch) or "").strip()
        if value:
            held.append(ch)
    if not held:
        emails = (lead.get("emails_all") or "").split(";")
        if any(e.strip() for e in emails):
            held.append("email")
    return held


def progress(lead: dict) -> dict[str, dict]:
    """{channel: {step, last_at, replied, stopped}} from the append-only log."""
    dom = host_of(lead)
    state: dict[str, dict] = {}
    for ev in events():
        if ev.get("domain") != dom:
            continue
        ch = ev.get("channel", "")
        s = state.setdefault(ch, {"step": 0, "last_at": None, "replied": False, "stopped": ""})
        if ev["event"] == "sent":
            s["step"] = max(s["step"], int(ev.get("step", 0)))
            s["last_at"] = ev["at"]
        elif ev["event"] == "replied":
            s["replied"] = True
            s["stopped"] = "replied"
        elif ev["event"] == "stopped":
            s["stopped"] = ev.get("reason", "stopped")
    return state


def next_due(lead: dict) -> list[dict]:
    """Every (channel, step) that is due right now for this lead."""
    if host_of(lead) in dnc():
        return []
    prog = progress(lead)
    if any(s.get("replied") for s in prog.values()):
        return []
    out = []
    for ch in contacts(lead):
        st = prog.get(ch, {"step": 0, "last_at": None, "replied": False, "stopped": ""})
        if st["stopped"] or st["replied"]:
            continue
        step = st["step"]
        if step >= MAX_TOUCHES:
            continue
        if step == 0:
            out.append({"channel": ch, "step": 1, "due": True})
            continue
        last = dt.datetime.fromisoformat(st["last_at"].replace("Z", "+00:00")) if st["last_at"] else None
        if last is None:
            continue
        gap = TOUCH_GAP_2 if step == 1 else TOUCH_GAP_3
        if now() - last >= dt.timedelta(hours=gap):
            out.append({"channel": ch, "step": step + 1, "due": True})
    return out


def in_window() -> bool:
    hour = (now() + dt.timedelta(hours=2)).hour          # Africa/Harare = UTC+2
    return SEND_HOURS[0] <= hour < SEND_HOURS[1]


def sent_today(channel: str) -> int:
    today = now().date().isoformat()
    return sum(1 for ev in events()
               if ev.get("event") == "sent" and ev.get("channel") == channel
               and ev.get("at", "").startswith(today))


def draft(domain: str) -> int:
    leads = [l for l in load_leads() if host_of(l) == domain.lower().strip("/")]
    if not leads:
        print(f"no lead for {domain}", file=sys.stderr)
        return 2
    lead = leads[0]
    venture = venture_of(lead)
    url = write_freebie(lead, venture)
    print(f"{host_of(lead)} · {venture.get('name')} · keyword {keyword(venture)}")
    print(f"  freebie → {url}")
    rs = rails()
    for ch in contacts(lead):
        subject, body = touch_copy(lead, venture, 1, url)
        can = rs.get(ch, {}).get("can_send")
        path = draft_file(lead, ch, 1, subject, body)
        print(f"  {ch:<9}{'SENDS' if can else 'draft':<6}{path.relative_to(HERE)}")
    return 0


def run(dry: bool = False, limit: int = 0) -> int:
    rs = rails()
    if not in_window() and not dry:
        print(f"outside the send window ({SEND_HOURS[0]}:00–{SEND_HOURS[1]}:00 Africa/Harare) — waiting")
        return 0
    sent = 0
    for lead in load_leads():
        for job in next_due(lead):
            ch, step = job["channel"], job["step"]
            rail = rs.get(ch, {"can_send": False, "why": "unknown rail"})
            venture = venture_of(lead)
            url = write_freebie(lead, venture)
            subject, body = touch_copy(lead, venture, step, url)
            tag = f"{host_of(lead):<26}{ch:<9}t{step}"
            if dry:
                print(f"  WOULD SEND {tag}{'' if rail['can_send'] else '  (draft only: ' + rail['why'] + ')'}")
                sent += 1
                continue
            if not rail["can_send"]:
                p = draft_file(lead, ch, step, subject, body)
                log({"event": "drafted", "domain": host_of(lead), "channel": ch, "step": step,
                     "path": str(p.relative_to(ROOT)), "why": rail["why"]})
                print(f"  DRAFT {tag}{rail['why']}")
                continue
            if sent_today(ch) >= DAILY_CAP.get(ch, 10):
                print(f"  CAP   {tag}daily cap for {ch} reached")
                continue
            ok, detail = send_one(lead, ch, step, subject, body, venture.get("sender", ""))
            log({"event": "sent" if ok else "failed", "domain": host_of(lead), "channel": ch,
                 "step": step, "detail": detail})
            print(f"  {'SENT ' if ok else 'FAIL '}{tag}{detail}")
            if ok:
                sent += 1
            time.sleep(random.uniform(1.5, 4.0))       # jitter: a machine can still be polite
        if limit and sent >= limit:
            print(f"  stop: limit {limit} reached")
            break
    if not sent and not dry:
        print("  nothing due")
    return 0


def replied(domain: str, channel: str = "", phrase: str = "") -> int:
    dom = domain.lower().strip("/")
    log({"event": "replied", "domain": dom, "channel": channel or "any", "phrase": phrase})
    # a reply stops every channel, and the freebie is what they get back
    for lead in [l for l in load_leads() if host_of(l) == dom]:
        venture = venture_of(lead)
        url = write_freebie(lead, venture)
        path = OUTBOX / f"REPLY-{freebie_slug(lead)}.txt"
        OUTBOX.mkdir(parents=True, exist_ok=True)
        path.write_text(freebie_text(lead, venture))
        print(f"{dom}: sequence stopped on every channel. Freebie to send by hand or by rail: {url}")
        print(f"  plain-text copy → {path.relative_to(HERE)}")
    return 0


def status() -> int:
    rs = rails()
    print("rails:")
    for name, r in rs.items():
        print(f"  {name:<9}{'SENDS ' if r['can_send'] else 'draft  '}{r['why']}")
    leads = load_leads()
    if not leads:
        print("\nno leads yet — run growth/leadhunt.py first")
        return 0
    print(f"\nleads: {len(leads)}")
    for lead in leads:
        prog = progress(lead)
        bits = []
        for ch in contacts(lead) or []:
            s = prog.get(ch, {"step": 0, "replied": False, "stopped": ""})
            mark = "replied" if s["replied"] else (f"t{s['step']}" if s["step"] else "—")
            bits.append(f"{ch}:{mark}")
        due = len(next_due(lead))
        print(f"  {host_of(lead):<26}{' / '.join(bits) or 'no contact':<34}due now: {due}")
    return 0


def selftest() -> int:
    problems = []
    lead = {"venture": "deskos", "domain": "example.co.zw", "title": "Example Ltd",
            "email": "info@example.co.zw", "why": "I looked at example.co.zw: your site says tender"}
    venture = {"id": "deskos", "name": "DeskOS", "sells": "a tender desk", "reply_phrase": "TENDERS"}
    for step in (1, 2, 3):
        subject, body = touch_copy(lead, venture, step, "https://x/y.txt")
        if not subject or len(body) < 120:
            problems.append(f"touch {step}: copy too thin")
        if step == 1 and ("http://" in body or "https://" in body):
            problems.append("touch 1 contains a link — the rule is no links in the first touch")
        if step == 1 and "<" in body:
            problems.append("touch 1 contains markup")
        if keyword(venture) not in touch_copy(lead, venture, 1, "")[1]:
            problems.append("touch 1 does not name the reply phrase")
    # ---- the clock: 0h → 48h → 72h → stop. Proven against a fake log, not a real inbox.
    global events
    real_events = events
    t0 = now() - dt.timedelta(hours=1)
    lead2 = dict(lead, domain="clock.co.zw", email="a@clock.co.zw")
    try:
        def fake(events_list):
            return lambda: events_list
        events = fake([])
        if [d["step"] for d in next_due(lead2)] != [1] and \
                [d["step"] for d in next_due(lead2)] != []:
            problems.append("a fresh lead with no log should be at touch 1")
        events = fake([{"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 1,
                        "at": iso(t0)}])
        steps = [d["step"] for d in next_due(lead2)]
        if steps != []:
            problems.append(f"touch 2 fired 1h after touch 1 (should wait 48h), got {steps}")
        events = fake([{"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 1,
                        "at": iso(now() - dt.timedelta(hours=48, minutes=1))}])
        if [d["step"] for d in next_due(lead2)] != [2]:
            problems.append("touch 2 did not fire at 48h")
        events = fake([{"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 1,
                        "at": iso(now() - dt.timedelta(hours=200))},
                       {"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 2,
                        "at": iso(now() - dt.timedelta(hours=72, minutes=1))}])
        if [d["step"] for d in next_due(lead2)] != [3]:
            problems.append("touch 3 did not fire at 72h after touch 2")
        events = fake([{"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 3,
                        "at": iso(now() - dt.timedelta(days=30))}])
        if next_due(lead2):
            problems.append("the sequence did not end after touch 3")
        events = fake([{"event": "sent", "domain": "clock.co.zw", "channel": "email", "step": 2,
                        "at": iso(now() - dt.timedelta(hours=100))},
                       {"event": "replied", "domain": "clock.co.zw", "channel": "email",
                        "at": iso(now() - dt.timedelta(hours=99))}])
        if next_due(lead2):
            problems.append("a reply did not stop the sequence")
    finally:
        events = real_events

    if MAX_TOUCHES != 3:
        problems.append("sequence must be three touches")
    if TOUCH_GAP_2 != 48 or TOUCH_GAP_3 != 72:
        problems.append("cadence must be 48h then 72h")
    print(f"outreach: {MAX_TOUCHES} touches · {TOUCH_GAP_2}h then {TOUCH_GAP_3}h · "
          f"caps {DAILY_CAP} · window {SEND_HOURS[0]}–{SEND_HOURS[1]} Harare")
    for p in problems:
        print("  ✗", p)
    print("  ✓ clean" if not problems else f"  {len(problems)} problem(s)")
    return 0 if not problems else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the estate's three-touch outreach sequence")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--draft", metavar="DOMAIN")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--replied", metavar="DOMAIN")
    ap.add_argument("--channel", default="")
    ap.add_argument("--phrase", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.status:
        return status()
    if a.draft:
        return draft(a.draft)
    if a.replied:
        return replied(a.replied, a.channel, a.phrase)
    if a.due:
        return run(a.dry, a.limit)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
