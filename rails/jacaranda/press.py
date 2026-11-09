#!/usr/bin/env python3
"""The lab's own press: what Jacaranda Labs posts, in its own voice, on its own accounts.

The seven ventures each had a rail. The lab — the thing that owns them, publishes the books and does
the disclosure — had accounts with nothing on them, which is the wrong way round: a portfolio with no
publication history reads like a landing page, and a landing page is not what we are selling.

Twelve posts, mapped one-to-one onto cards rendered by tools/social_cards.py. Eight teach something
about building this way; four ask. The rotation is written out so it can be reviewed in a diff, and
the selftest fails the build if any window of three breaks 2 value : 1 promo.

    python3 rails/jacaranda/press.py --plan
    python3 rails/jacaranda/press.py --due        # one post at most, cadence-guarded
    python3 rails/jacaranda/press.py --post ledger --dry
    python3 rails/jacaranda/press.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "press-state.json"
CARDS = "https://jacaranda-labs.pages.dev/assets/cards"
SITE = "https://jacaranda-labs.pages.dev"
VENTURES = f"{SITE}/#ventures"
PUBLICATIONS = f"{SITE}/publications/"
DISCLOSURE = f"{SITE}/about/"

# kind: "value" is worth reading even if you never buy anything; "promo" asks.
# card: a real rendered card. No post ships without one — enforced in social.post().
BANK = [
    dict(id="method", kind="value", card=f"{CARDS}/method.png",
         kicker="CONSTRAINT-NATIVE SOFTWARE",
         headline="Built by agents instead of a team.",
         body="Seven ventures, one operator, no headcount — and the working papers that show what that "
              "actually costs.",
         text="The constraint is not a story about hustle. It is the design brief: if a thing cannot be "
              "built, priced, supported and documented by one operator and a set of agents, it is the "
              "wrong thing to build.\n\nThat rules a lot out, which is the point."),
    dict(id="promo-portfolio", kind="promo", card=f"{CARDS}/promo-portfolio.png",
         kicker="THE PORTFOLIO",
         headline="Seven ventures. One page. Real prices.",
         body="Every venture, what it sells, and what it costs — no calendar, no discovery call.",
         text="Seven businesses, described in the same length as a business card and priced in public. "
              "If you cannot tell what a venture does and what it costs from that page, the page is wrong "
              "and we fix it.\n\nStart here:", link=VENTURES),
    dict(id="ledger", kind="value", card=f"{CARDS}/ledger.png",
         kicker="THE RECORD",
         headline="The ledger has a column for what failed.",
         body="Twenty works, and the ones that did not work are catalogued too — including the reasons.",
         text="A portfolio that only publishes its wins is advertising. The catalogue carries the "
              "working papers for ventures that stalled, with the mechanism that failed, the cost and "
              "the point where it was obvious.\n\nIt is more useful than the successes.",
         link=PUBLICATIONS),
    dict(id="failure", kind="value", card=f"{CARDS}/failure.png",
         kicker="FAILURE CASES",
         headline="A failure case is cheaper than a case study.",
         body="You can copy someone's mistake for nothing. Their success needs their context.",
         text="Most post-mortems are written for the audience that already left. Ours are written for "
              "the next operator with the same constraint: this mechanism broke, here is the first "
              "signal, here is what it cost to find out.\n\nRead the failure before the framework."),
    dict(id="promo-publications", kind="promo", card=f"{CARDS}/promo-publications.png",
         kicker="PUBLICATIONS",
         headline="Twenty works, free to read.",
         body="Books, reports and working papers — no account, no email, no gate.",
         text="Everything we have written about building this way is free to read on the site: the "
              "books, the market reports, the failure cases. Some are still with the author; the rest "
              "are one click from here.", link=PUBLICATIONS),
    dict(id="harare", kind="value", card=f"{CARDS}/harare.png",
         kicker="HARARE, ZIMBABWE",
         headline="Built where the payment rails are the hardest part.",
         body="EcoCash, PayShap, ZIPIT, Mukuru. Every venture here handles money it cannot assume.",
         text="Operating from Harare is not a slogan; it is a set of constraints that show up in the "
              "code — exact-amount payment matching, offline-first pages, prices in two currencies, "
              "and support that works on a phone with intermittent data.\n\nSoftware built here travels. "
              "The reverse is not true."),
    dict(id="disclosure", kind="value", card=f"{CARDS}/disclosure.png",
         kicker="DISCLOSURE",
         headline="What this is, and what it is not.",
         body="The about page says where the money comes from and what has not been independently checked.",
         text="No external funding, no headcount, no university, no endorsement. Illustrations are "
              "AI-generated artwork, labelled as such, and the teaching material has not been "
              "independently validated.\n\nIt is written down rather than implied:", link=DISCLOSURE),
    dict(id="promo-ventures", kind="promo", card=f"{CARDS}/promo-ventures.png",
         kicker="SELF-SERVE",
         headline="Every venture sells without me in the room.",
         body="Published prices, a checkout that works at 03:00, delivery that does not wait for a reply.",
         text="A business that needs the founder to close is a job with extra steps. Each of the seven "
              "is priced in public, sells without a call, and delivers what it promised before anybody "
              "answers an email.\n\nThat is the standard we hold them to:", link=VENTURES),
    dict(id="numbers", kind="value", card=f"{CARDS}/numbers.png",
         kicker="THE NUMBERS",
         headline="Seven ventures. Twenty works. Zero funding.",
         body="And one operator, which is the number that decides everything else.",
         text="Not a growth story. A count of what exists: seven live ventures, twenty catalogued "
              "works — nine readable free — no outside capital, no employees.\n\nNumbers like these are "
              "only interesting because they are checkable, so they are printed on the front page."),
    dict(id="reading", kind="value", card=f"{CARDS}/reading.png",
         kicker="HOW THE PAPERS ARE MADE",
         headline="Every claim has an artefact behind it.",
         body="A working paper is not an essay. It is the thing that was built, measured and priced.",
         text="Each work starts as a venture decision with a cost attached. The paper records the "
              "mechanism, the numbers we could actually measure, what we could not, and where the "
              "reasoning was thin.\n\nThe failure cases are the honest ones."),
    dict(id="promo-read", kind="promo", card=f"{CARDS}/promo-read.png",
         kicker="READ IT FREE",
         headline="The readable editions need no account.",
         body="Open the catalogue, pick a title, read it in the browser.",
         text="No email wall, no PDF funnel, no \"request access\". The readable editions open in the "
              "browser and the downloadable ones are direct links.\n\nStart with the one about the "
              "venture that did not work:", link=PUBLICATIONS),
    dict(id="open", kind="value", card=f"{CARDS}/open.png",
         kicker="OPEN PRACTICE",
         headline="The teaching is free, and it stays free.",
         body="Fifty activities, thirty-nine tools, offline workspaces for bad connections.",
         text="Open Practice is the free half of this estate: practical AI training that runs in a "
              "classroom with no reliable internet, licensed so anyone can reuse it.\n\nIt is also the "
              "clearest example of the method — free to the user, cheap to run, no owner in the loop."),
]

# value first, and never two promos adjacent. Written out, not computed, so a diff shows the order.
ROTATION = ["method", "promo-portfolio", "ledger", "failure", "promo-publications", "harare",
            "disclosure", "promo-ventures", "numbers", "reading", "promo-read", "open"]

CADENCE_HOURS = 30          # same rhythm as the ventures: present, not a firehose


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            return {}
    return {}


def save_state(st: dict) -> None:
    STATE.write_text(json.dumps(st, indent=1) + "\n")


def by_id(post_id: str) -> dict:
    for p in BANK:
        if p["id"] == post_id:
            return p
    return {}


def next_post(st: dict) -> dict:
    sent = set(st.get("sent", []))
    for pid in ROTATION:
        if pid not in sent:
            return by_id(pid)
    return {}


def due(st: dict, now: dt.datetime | None = None) -> bool:
    last = st.get("last_at")
    if not last:
        return True
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        prev = dt.datetime.fromisoformat(last.replace("Z", "+00:00"))
    except ValueError:
        return True
    return (now - prev) >= dt.timedelta(hours=CADENCE_HOURS)


def publish(post: dict, dry: bool = False) -> int:
    import social
    if not post:
        print("the bank is spent — write the next post before the queue runs dry", file=sys.stderr)
        return 3
    print(f"→ {post['id']} ({post['kind']}) card={post['card'].rsplit('/', 1)[-1]}")
    res = social.post(post["text"], link=post.get("link", ""), tags=post.get("tags", []),
                      image=post["card"], dry=dry)
    good = sum(1 for ok, _ in res.values() if ok)
    for rail, (ok, detail) in res.items():
        print(f"  {'OK  ' if ok else 'FAIL'} {rail:9s} {detail}")
    if not dry and good:
        st = load_state()
        st["sent"] = list(st.get("sent", [])) + [post["id"]]
        st["last_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        st.setdefault("log", []).append({"id": post["id"], "at": st["last_at"], "rails": good})
        save_state(st)
    return 0 if good else 1


def plan(st: dict) -> None:
    sent = set(st.get("sent", []))
    print(f"{'#':<3}{'id':<18}{'kind':<7}{'state':<10}")
    for i, pid in enumerate(ROTATION, 1):
        p = by_id(pid)
        print(f"{i:<3}{pid:<18}{p['kind']:<7}{'sent' if pid in sent else 'queued'}")
    vals = sum(1 for pid in ROTATION if by_id(pid)["kind"] == "value")
    promos = len(ROTATION) - vals
    nxt = next_post(st)
    print(f"\n{vals} value : {promos} promo  ({vals / max(promos, 1):.1f}:1, rule is 2:1)")
    print(f"next: {nxt.get('id', '— bank spent —')} · cadence {CADENCE_HOURS}h · "
          f"last {st.get('last_at') or 'never'}")


def selftest() -> int:
    problems = []
    ids = [p["id"] for p in BANK]
    if len(ids) != len(set(ids)):
        problems.append("duplicate post id")
    for p in BANK:
        if not p.get("card", "").startswith("https://"):
            problems.append(f"{p['id']}: no card")
        total = len(p["text"]) + (len(p.get("link", "")) + 2 if p.get("link") else 0)
        if total > 300:
            problems.append(f"{p['id']}: {total} chars with its link — over Bluesky's 300")
        if p["kind"] not in ("value", "promo"):
            problems.append(f"{p['id']}: bad kind {p['kind']}")
        if not p.get("headline"):
            problems.append(f"{p['id']}: no card headline")
    if sorted(ids) != sorted(ROTATION):
        problems.append("rotation and bank disagree")
    kinds = [by_id(p)["kind"] for p in ROTATION]
    for i in range(len(kinds) - 2):
        if kinds[i:i + 3].count("value") < 2:
            problems.append(f"window at {i} is {kinds[i:i + 3]} — breaks 2 value : 1 promo")
    for i, k in enumerate(kinds):
        if k == "promo" and i and kinds[i - 1] == "promo":
            problems.append(f"two promos back to back at {i}")
    print("bank:", len(BANK), "posts ·", kinds.count("value"), "value ·", kinds.count("promo"), "promo")
    for p in problems:
        print("  ✗", p)
    print("  ✓ clean" if not problems else f"  {len(problems)} problem(s)")
    return 0 if not problems else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--due", action="store_true")
    ap.add_argument("--post", default="")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    st = load_state()

    if a.selftest:
        return selftest()
    if a.plan or a.status:
        plan(st)
        return 0
    if a.post:
        return publish(by_id(a.post), a.dry)
    if a.due:
        if not due(st):
            print(f"not due yet (last {st.get('last_at')}, cadence {CADENCE_HOURS}h) — nothing sent")
            return 0
        return publish(next_post(st), a.dry)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
