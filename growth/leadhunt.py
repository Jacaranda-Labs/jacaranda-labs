#!/usr/bin/env python3
"""leadhunt — find organisations that match a venture's ICP, and draft the first email to each.

This is the lead-hunting pattern that already runs in Hunta, re-pointed at the seven ventures and
kept deliberately small. It researches; it does not send. Every lead leaves here as a row a person
reads before anything is mailed, because the two failure modes of outbound — mailing a list you did
not build, and mailing it at volume — are the two things that get a domain blocked.

    python3 growth/leadhunt.py --venture deskos --seeds growth/seeds/deskos.txt --max 8
    python3 growth/leadhunt.py --venture tapstall --search --max 12
    python3 growth/leadhunt.py --status
    python3 growth/leadhunt.py --mark example.co.zw contacted
    python3 growth/leadhunt.py --dnc example.co.zw --reason "asked us to stop"

What it does per candidate site:
  robots.txt is read and obeyed before anything is fetched (and the UA carries a contact address)
  the homepage and up to N contact/about pages are fetched, slowly, one host at a time
  emails/phones/WhatsApp numbers published by the organisation itself are extracted
  fit is scored from the venture's signals — and a lead with no contact detail is dropped, not kept
  the row is written to growth/leads/<venture>.csv and growth/leads/store.jsonl, deduplicated by domain

What it will not do:
  guess an address (no first.last@pattern harvesting — that is how you mail strangers)
  touch a site that disallows it in robots.txt, or a host on the do-not-contact list
  send anything. Sending needs a domain with SPF/DKIM/DMARC and a name behind it; when that exists,
  this tool's CSV is the input to it, and a human still presses send.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEADS = HERE / "leads"
STORE = LEADS / "store.jsonl"
DNC = HERE / "dnc.txt"
PROFILES = HERE / "ventures.yaml"
UA = "JacarandaLeadHunter/1.0 (+https://jacaranda-labs.pages.dev; research only; contact couragegarikai@atomicmail.io)"

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:(?:\+|00)\s?(?:27|263|260|254|234)|0)\s?(?:[\s\-().]*\d){8,11}")
WA_RE = re.compile(r"(?:api\.whatsapp\.com/send\?phone=|wa\.me/)(\+?\d{9,15})", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")

NOISE = {
    "example.com", "yourdomain.com", "domain.com", "email.com", "company.com", "sentry.io",
    "wixpress.com", "sentry-next.wixpress.com", "schema.org", "w3.org", "cloudflare.com",
    "googlemail.com",  # real, but usually a third-party widget; keep the list short and honest
}
SKIP_HOSTS = ("linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com",
              "wikipedia.org", "pinterest.com", "tiktok.com")
# Not buyers: governments, universities and hospitals publish contact pages and match half the
# signal words, and every one of them that lands in the CSV is a wasted read and a bad look.
EXCLUDE_SUFFIXES = (".gov", ".gov.zw", ".gov.za", ".gov.zm", ".ac.zw", ".ac.za", ".ac.zm", ".edu",
                    ".mil", ".org.zw", ".parliament")


# --------------------------------------------------------------------------- helpers
def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(400_000)
        charset = r.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, errors="ignore")


def allowed(url: str, cache: dict) -> bool:
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    if base not in cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.parse(get(base + "/robots.txt", timeout=10).splitlines())
        except Exception:
            rp = None                      # no robots.txt, or unreachable: treat as allowed
        cache[base] = rp
    rp = cache[base]
    return True if rp is None else rp.can_fetch(UA, url)


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html)).strip()


def domain_of(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def excluded(host: str) -> bool:
    h = host.lower()
    return any(h == x.lstrip(".") or h.endswith(x) for x in EXCLUDE_SUFFIXES)


def dnc_list() -> set[str]:
    if not DNC.exists():
        return set()
    out = set()
    for line in DNC.read_text().splitlines():
        line = line.split("#", 1)[0].strip().lower()
        if line:
            out.add(line)
    return out


# --------------------------------------------------------------------------- research
def candidates(host_or_url: str) -> list[str]:
    url = host_or_url if "://" in host_or_url else "https://" + host_or_url
    return [url]


def crawl(site: str, profile: dict, defaults: dict, robots_cache: dict) -> dict | None:
    """Fetch a site politely and return what it publishes about itself."""
    pages, seen = [], set()
    try:
        home = get(site)
    except Exception:
        try:                                    # bare http fallback for small business hosts
            home = get(site.replace("https://", "http://", 1))
        except Exception:
            return None
    pages.append((site, home))
    seen.add(site)
    base = urllib.parse.urlparse(site)
    for path in defaults.get("contact_paths", [])[: defaults.get("max_pages_per_site", 4)]:
        url = f"{base.scheme}://{base.netloc}{path}"
        if url in seen:
            continue
        if not allowed(url, robots_cache):
            continue
        try:
            pages.append((url, get(url, timeout=12)))
            seen.add(url)
        except Exception:
            continue
        time.sleep(float(defaults.get("delay_seconds", 2.0)))

    body = "\n".join(text_of(h) for _, h in pages)
    raw = "\n".join(h for _, h in pages)

    emails = []
    for e in EMAIL_RE.findall(raw):
        d = e.rsplit("@", 1)[-1].lower()
        if d in NOISE or d.endswith((".png", ".jpg", ".webp")):
            continue
        if e.lower() not in [x.lower() for x in emails]:
            emails.append(e)
    phones = list(dict.fromkeys(PHONE_RE.findall(body)))[:3]
    wa = list(dict.fromkeys(WA_RE.findall(raw)))[:1]

    title = (TITLE_RE.search(home).group(1) if TITLE_RE.search(home) else "").strip()
    lower = body.lower()

    strong = sum(1 for w in profile.get("signals", {}).get("strong", []) if w.lower() in lower)
    weak = sum(1 for w in profile.get("signals", {}).get("weak", []) if w.lower() in lower)
    hints = [c.lower() for c in defaults.get("country_hints", [])]
    country = next((h for h in hints if f".{h}" in urllib.parse.urlparse(site).netloc.lower()), "")

    score = 0
    score += min(strong, 4) * 18
    score += min(weak, 4) * 6
    score += 20 if emails else 0
    score += 8 if (phones or wa) else 0
    score += 6 if country else 0
    score += 4 if re.search(r"(contact|about)", raw, re.I) else 0

    why_bits = []
    if strong:
        words = [w for w in profile["signals"]["strong"] if w.lower() in lower][:3]
        why_bits.append("your site talks about " + ", ".join(f"“{w}”" for w in words))
    if weak and not strong:
        why_bits.append("your site reads like a " + profile["who"].split("—")[0].strip())
    why = ("I looked at %s: %s." % (domain_of(site), "; ".join(why_bits))) if why_bits else \
          "I looked at %s and it is the kind of business this is built for." % domain_of(site)

    return {"site": site, "domain": domain_of(site), "title": text_of(title)[:90],
            "email": emails[0] if emails else "", "emails_all": ";".join(emails[:4]),
            "phone": phones[0] if phones else "", "whatsapp": wa[0] if wa else "",
            "country_hint": country, "score": score, "why": why,
            "strong_hits": strong, "weak_hits": weak}


def search(query: str, limit: int = 8) -> list[str]:
    """Web search, through a provider that will actually answer a script.

    DuckDuckGo and Bing both return an anti-bot page to a datacentre IP, so scraping them is a dead
    end dressed up as a feature. Google Programmable Search answers properly, is free to 100 queries
    a day, and needs two environment variables. With no provider configured the hunt still works from
    seeds — and seeds are the better input anyway: a domain somebody chose beats a domain a query
    guessed.
    """
    key, cx = os.environ.get("GOOGLE_CSE_KEY", "").strip(), os.environ.get("GOOGLE_CSE_CX", "").strip()
    if not (key and cx):
        print("  ! --search needs GOOGLE_CSE_KEY and GOOGLE_CSE_CX (100 queries/day, free); "
              "running from seeds only", file=sys.stderr)
        return []
    url = ("https://www.googleapis.com/customsearch/v1?key=" + urllib.parse.quote(key)
           + "&cx=" + urllib.parse.quote(cx) + "&num=10&q=" + urllib.parse.quote(query))
    urls = []
    try:
        data = json.loads(get(url, timeout=20))
    except Exception as exc:
        print(f"  ! search failed for {query!r}: {type(exc).__name__}", file=sys.stderr)
        return urls
    for item in data.get("items", []):
        href = item.get("link", "")
        host = urllib.parse.urlparse(href).netloc.lower()
        if not host or any(s in host for s in SKIP_HOSTS):
            continue
        if href not in urls:
            urls.append(href)
        if len(urls) >= limit:
            break
    return urls


def directory(url: str, profile: dict, defaults: dict, robots_cache: dict, pages: int = 3) -> list[dict]:
    """Read a public member directory — a trade association's list of its own members.

    This is the strongest source available to us and the only one that needs no search provider: a
    federation publishes its members' names, phones and addresses because it wants to be called. It
    is one page per trade, and the firms on it are, by definition, the ones that bid for contracts.

    Extraction is deliberately blunt: an email is the anchor, and the nearest bold text or heading
    above it is the company name. Rows without an address are dropped.
    """
    out, seen = [], set()
    for n in range(max(1, pages)):
        u = url if n == 0 else f"{url}{'&' if '?' in url else '?'}p={n + 1}"
        if not allowed(u, robots_cache):
            break
        try:
            html = get(u, timeout=20)
        except Exception:
            break
        for m in EMAIL_RE.finditer(html):
            email = m.group(0)
            dom = email.rsplit("@", 1)[-1].lower()
            if dom in NOISE or "." not in dom:
                continue
            if email.lower() in seen:
                continue
            seen.add(email.lower())
            before = text_of(html[max(0, m.start() - 700):m.start()])
            name = ""
            for chunk in reversed(re.split(r"\s{2,}|(?<=[a-z)])(?=[A-Z][a-z]+\s)", before)):
                chunk = chunk.strip(" -–,|.")
                if 2 < len(chunk) < 70 and not EMAIL_RE.search(chunk) and not re.search(r"\d{3,}", chunk):
                    name = chunk
                    break
            after = text_of(html[m.end():m.end() + 220])
            phone = (PHONE_RE.search(after) or PHONE_RE.search(before))
            out.append({"site": f"https://{dom}", "domain": dom,
                        "title": (name or dom)[:90], "email": email, "emails_all": email,
                        "phone": phone.group(0).strip() if phone else "", "whatsapp": "",
                        "country_hint": next((h for h in defaults.get("country_hints", [])
                                              if f".{h.lower()}" in dom), ""),
                        "score": 55, "why": f"listed in a public {profile['name']} member directory",
                        "strong_hits": 0, "weak_hits": 0, "source": "directory"})
        time.sleep(float(defaults.get("delay_seconds", 2.0)))
    return out


# --------------------------------------------------------------------------- store
def load_store() -> list[dict]:
    if not STORE.exists():
        return []
    return [json.loads(line) for line in STORE.read_text().splitlines() if line.strip()]


def save(rows: list[dict]) -> None:
    LEADS.mkdir(parents=True, exist_ok=True)
    STORE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    by_v: dict[str, list[dict]] = {}
    for r in rows:
        by_v.setdefault(r["venture"], []).append(r)
    cols = ["venture", "found_at", "domain", "title", "country_hint", "email",
            "emails_all", "phone", "whatsapp", "score", "status", "why", "site"]
    for v, rs in by_v.items():
        p = LEADS / f"{v}.csv"
        with p.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(sorted(rs, key=lambda r: -r["score"]))
        print(f"  wrote {p.relative_to(ROOT)} ({len(rs)} leads)")


# --------------------------------------------------------------------------- commands
def hunt(venture: str, seeds: list[str], use_search: bool, limit: int) -> int:
    cfg = yaml.safe_load(PROFILES.read_text())
    defaults = cfg.get("defaults", {})
    profile = cfg["ventures"].get(venture)
    if not profile:
        print(f"no venture {venture!r} in {PROFILES.name}", file=sys.stderr)
        return 2

    dnc = dnc_list()
    rows = load_store()
    have = {(r["venture"], r["domain"]) for r in rows}
    robots_cache: dict = {}
    targets = list(seeds)
    if use_search:
        for q in profile.get("queries", []):
            targets += search(q, limit=6)
            time.sleep(3)
    seen_hosts = set()
    added = 0
    for t in targets:
        if added >= limit:
            break
        d = domain_of(t)
        if not d or d in seen_hosts:
            continue
        seen_hosts.add(d)
        if excluded(d):
            print(f"  – {d}: government, academic or otherwise not a buyer")
            continue
        if d in dnc or any(d.endswith("." + x) for x in dnc):
            print(f"  – {d}: on the do-not-contact list")
            continue
        if (venture, d) in have:
            print(f"  – {d}: already in the list")
            continue
        if not allowed(t, robots_cache):
            print(f"  – {d}: robots.txt disallows this crawler")
            continue
        rec = crawl(t, profile, defaults, robots_cache)
        if not rec:
            print(f"  – {d}: unreachable")
            continue
        if rec["score"] < defaults.get("min_score", 45):
            print(f"  – {d}: score {rec['score']} below {defaults.get('min_score')}")
            continue
        if not rec["email"]:
            print(f"  – {d}: no published address, dropped (no guessing)")
            continue
        rec.update({"venture": venture, "found_at": now(), "status": "new"})
        rows.append(rec)
        have.add((venture, d))
        added += 1
        print(f"  + {d}: score {rec['score']}, {rec['email']}")
        time.sleep(float(defaults.get("delay_seconds", 2.0)))

    save(rows)
    print(f"  {added} new lead(s) for {venture}")
    if added:
        print("\nNext: read each row, then send it yourself — the draft is in ventures.yaml first_touch.")
        print("      Mark it contacted when you do:  --mark <domain> contacted")
    return 0


def draft(venture: str, domain: str) -> int:
    cfg = yaml.safe_load(PROFILES.read_text())
    profile = cfg["ventures"].get(venture) or {}
    row = next((r for r in load_store() if r["venture"] == venture and r["domain"] == domain), None)
    if not row:
        print("no such lead", file=sys.stderr)
        return 2
    print(profile.get("first_touch", "").format(company=row["title"] or row["domain"],
                                                domain=row["domain"], why=row["why"]))
    print(f"\n-- to: {row['email']}\n-- venture: {venture} · {profile.get('url')}")
    return 0


def mark(domain: str, status: str) -> int:
    rows = load_store()
    n = 0
    for r in rows:
        if r["domain"] == domain:
            r["status"] = status
            r["status_at"] = now()
            n += 1
    save(rows)
    print(f"{n} row(s) marked {status}")
    return 0 if n else 2


def add_dnc(domain: str, reason: str = "") -> int:
    LEADS.mkdir(parents=True, exist_ok=True)
    with DNC.open("a") as f:
        f.write(f"{domain}  # {now()} {reason}\n")
    rows = [r for r in load_store() if r["domain"] != domain]
    save(rows)
    print(f"{domain} suppressed and removed from the store")
    return 0


def status() -> int:
    rows = load_store()
    if not rows:
        print("no leads yet")
        return 0
    print(f"{'venture':<18}{'domain':<30}{'score':>6}  status")
    print("-" * 66)
    for r in sorted(rows, key=lambda r: (r["venture"], -r["score"])):
        print(f"{r['venture']:<18}{r['domain']:<30}{r['score']:>6}  {r['status']}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--venture")
    ap.add_argument("--seeds", help="file of domains/URLs, one per line")
    ap.add_argument("--seed", action="append", default=[], help="a single domain/URL (repeatable)")
    ap.add_argument("--search", action="store_true", help="also run the venture's queries")
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--mark", nargs=2, metavar=("DOMAIN", "STATUS"))
    ap.add_argument("--dnc", metavar="DOMAIN")
    ap.add_argument("--reason", default="")
    ap.add_argument("--draft", nargs=2, metavar=("VENTURE", "DOMAIN"))
    ap.add_argument("--directory", help="URL of a public member directory to read")
    ap.add_argument("--directory-pages", type=int, default=3)
    a = ap.parse_args(argv)

    if a.status:
        return status()
    if a.mark:
        return mark(*a.mark)
    if a.dnc:
        return add_dnc(a.dnc, a.reason)
    if a.draft:
        return draft(*a.draft)

    if a.directory:
        cfg = yaml.safe_load(PROFILES.read_text())
        profile = cfg["ventures"].get(a.venture or "")
        if not profile:
            print("--directory needs --venture", file=sys.stderr)
            return 2
        dnc, rows = dnc_list(), load_store()
        have = {(r["venture"], r["domain"]) for r in rows}
        found = directory(a.directory, profile, cfg.get("defaults", {}), {}, a.directory_pages)
        added = 0
        for rec in found:
            if rec["domain"] in dnc or excluded(rec["domain"]) or (a.venture, rec["domain"]) in have:
                continue
            rec.update({"venture": a.venture, "found_at": now(), "status": "new"})
            rows.append(rec)
            have.add((a.venture, rec["domain"]))
            added += 1
        save(rows)
        print(f"  {added} new lead(s) from {a.directory}")
        return 0

    seeds = list(a.seed)
    if a.seeds:
        seeds += [l.strip() for l in Path(a.seeds).read_text().splitlines()
                  if l.strip() and not l.startswith("#")]
    if not a.venture:
        print("--venture is required (or use --status)", file=sys.stderr)
        return 2
    if not seeds and not a.search:
        print("nothing to hunt: give --seeds/--seed or --search", file=sys.stderr)
        return 2
    return hunt(a.venture, seeds, a.search, a.max)


if __name__ == "__main__":
    raise SystemExit(main())
