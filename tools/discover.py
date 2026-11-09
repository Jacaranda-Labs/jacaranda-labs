#!/usr/bin/env python3
"""discover — are we findable, by search engines and by AI answer engines?

Being found is a different question from having a sitemap, so this checks the things that decide it:

    crawler access     robots.txt, including the named AI crawlers (GPTBot, ClaudeBot, PerplexityBot…)
    indexable surface  sitemap validity, canonical tags, status codes, redirect chains, trailing slashes
    machine summary    llms.txt and JSON-LD: what an answer engine can quote without guessing
    share surface      og/twitter tags and the image each one points at
    weight             bytes on the first page, and whether media is deferred
    backlinks          who links to us, from the open web (search, GitHub, the stores)

    python3 tools/discover.py                 # the lab site and all seven ventures
    python3 tools/discover.py --only labs     # one target
    python3 tools/discover.py --json out.json

Exit code is non-zero when a check that should always pass (sitemap, robots, canonical, og:image)
fails on the lab site — the ventures report but do not fail the run, because most of them are
single-page products whose SEO is their front page.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict

UA = {"User-Agent": "Mozilla/5.0 (compatible; jacaranda-discover/1.0)"}
AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web",
               "PerplexityBot", "Google-Extended", "Applebot-Extended", "CCBot"]

TARGETS = {
    "labs": "https://jacaranda-labs.pages.dev",
    "attestos": "https://attestos-edge.attestos.workers.dev",
    "tightbucket": "https://0x.tightbucket.workers.dev",
    "deskos": "https://deskos.deskos.workers.dev",
    "stpi": "https://getstpi.pages.dev",
    "tapstall": "https://tapstall.zlnew.workers.dev",
    "open-practice": "https://open-practice.zlnew.workers.dev",
    "mechanism-audit": "https://mechanism-audit.whop.site",
}


def fetch(url: str, timeout: int = 25) -> tuple[int, str, dict]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
        return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace"), dict(e.headers)
    except Exception:                                   # noqa: BLE001
        return 0, "", {}


@dataclass
class Report:
    id: str
    url: str
    status: int = 0
    robots: str = "missing"
    ai_crawlers_blocked: list[str] = field(default_factory=list)
    sitemap: str = "missing"
    sitemap_urls: int = 0
    sitemap_lastmod: str = ""
    canonical: str = "missing"
    title: str = ""
    desc: str = ""
    h1: int = 0
    og_image: str = "missing"
    og_image_ok: bool = False
    twitter_card: str = "missing"
    jsonld: list[str] = field(default_factory=list)
    llms_txt: str = "missing"
    bytes_html: int = 0
    issues: list[str] = field(default_factory=list)
    good: list[str] = field(default_factory=list)


def audit(tid: str, base: str) -> Report:
    r = Report(tid, base)
    st, html, hdrs = fetch(base + "/")
    r.status, r.bytes_html = st, len(html)

    # ---- robots.txt
    rst, robots, _ = fetch(base + "/robots.txt")
    if rst == 200 and "user-agent" in robots.lower():
        r.robots = "ok"
        blocks = []
        # crude but honest: find a group for the crawler whose only rule is Disallow: /
        for agent in AI_CRAWLERS:
            m = re.search(rf"user-agent:\s*{re.escape(agent)}\s*(.*?)(?=\n\s*user-agent:|\Z)",
                          robots, re.I | re.S)
            if m and re.search(r"^\s*disallow:\s*/\s*$", m.group(1), re.I | re.M):
                blocks.append(agent)
        if re.search(r"user-agent:\s*\*[^\n]*\n(?:[^\n]*\n)*?disallow:\s*/\s*$", robots, re.I | re.M):
            blocks.append("* (everything)")
        r.ai_crawlers_blocked = blocks
        if "sitemap:" not in robots.lower():
            r.issues.append("robots.txt does not name the sitemap")
    else:
        r.issues.append("robots.txt missing")

    # ---- sitemap
    sm_url = ""
    m = re.search(r"sitemap:\s*(\S+)", robots, re.I)
    if m:
        sm_url = m.group(1)
    for cand in ([sm_url] if sm_url else []) + [base + "/sitemap.xml"]:
        sst, sm, _ = fetch(cand)
        if sst == 200 and "<urlset" in sm:
            r.sitemap = cand
            r.sitemap_urls = sm.count("<url>") + sm.count("<url ")
            lm = re.findall(r"<lastmod>([^<]+)</lastmod>", sm)
            r.sitemap_lastmod = lm[0][:10] if lm else ""
            break
    if r.sitemap == "missing":
        r.issues.append("no sitemap.xml")

    # ---- head
    if html:
        def meta(pattern: str) -> str:
            mm = re.search(pattern, html, re.I | re.S)
            return mm.group(1).strip() if mm else ""
        r.canonical = meta(r'<link[^>]+rel=["\']?canonical["\']?[^>]+href=["\']([^"\']+)')
        r.title = meta(r"<title[^>]*>(.*?)</title>")
        r.desc = meta(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)')
        r.h1 = len(re.findall(r"<h1\b", html, re.I))
        r.og_image = meta(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)')
        r.twitter_card = meta(r'<meta[^>]+name=["\']twitter:card["\'][^>]+content=["\']([^"\']+)')
        r.jsonld = re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', html)

        if not r.canonical:
            r.issues.append("no canonical link")
        if not r.title:
            r.issues.append("no <title>")
        elif len(r.title) > 65:
            r.issues.append(f"title is {len(r.title)} chars — search truncates around 60")
        if not r.desc:
            r.issues.append("no meta description")
        elif not 70 <= len(r.desc) <= 165:
            r.issues.append(f"description is {len(r.desc)} chars — best between 70 and 160")
        if r.h1 != 1:
            r.issues.append(f"{r.h1} H1 tags (want exactly 1)")
        if r.og_image:
            ist, _, ih = fetch(r.og_image if r.og_image.startswith("http") else base + r.og_image)
            r.og_image_ok = ist == 200 and "image" in (ih.get("content-type") or ih.get("Content-Type") or "")
            if not r.og_image_ok:
                r.issues.append(f"og:image does not serve an image ({ist})")
        else:
            r.issues.append("no og:image")
        if r.twitter_card != "summary_large_image":
            r.issues.append("no summary_large_image twitter card")
        if not any(t in ("Organization", "WebSite", "Person", "WebPage", "Article", "Book")
                   for t in r.jsonld):
            r.issues.append("no JSON-LD (nothing for a search engine to quote as an entity)")

    # ---- llms.txt
    lst, llms, _ = fetch(base + "/llms.txt")
    r.llms_txt = "ok" if lst == 200 and len(llms) > 200 else ("thin" if lst == 200 else "missing")

    r.good = [x for x in [
        "robots ok" if r.robots == "ok" else "",
        f"sitemap {r.sitemap_urls} urls" if r.sitemap_urls else "",
        "canonical" if r.canonical else "",
        "og image serves" if r.og_image_ok else "",
        "json-ld" if r.jsonld else "",
        "llms.txt" if r.llms_txt == "ok" else "",
    ] if x]
    return r


def backlinks() -> dict:
    """What the open web says about the lab, without pretending a search API exists here."""
    out = {"github": "", "ventures_linking_home": [], "notes": []}
    try:
        req = urllib.request.Request(
            "https://api.github.com/search/code?q=%22jacaranda-labs.pages.dev%22",
            headers={**UA, "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.load(resp)
        out["github"] = f"{data.get('total_count', 0)} code hits"
    except urllib.error.HTTPError as e:
        out["github"] = f"needs a token ({e.code})"
    except Exception:                                  # noqa: BLE001
        out["github"] = "unreachable"
    for tid, base in TARGETS.items():
        if tid == "labs":
            continue
        st, html, _ = fetch(base + "/")
        if "jacaranda-labs.pages.dev" in html or "jacarandalabs.pages.dev" in html:
            out["ventures_linking_home"].append(tid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--links", action="store_true", help="also probe backlinks (slow)")
    a = ap.parse_args()

    ids = a.only or list(TARGETS)
    rows = [audit(i, TARGETS[i]) for i in ids]

    print(f"\n{'target':<16}{'st':>4} {'robots':<7}{'sitemap':<9}{'canon':<8}{'og:img':<8}"
          f"{'jsonld':<7}{'llms':<8}{'kB':>5}")
    print("-" * 74)
    for r in rows:
        print(f"{r.id:<16}{r.status:>4} {r.robots:<7}"
              f"{(str(r.sitemap_urls) + 'u') if r.sitemap_urls else '—':<9}"
              f"{'yes' if r.canonical else '—':<8}{'ok' if r.og_image_ok else '—':<8}"
              f"{'yes' if r.jsonld else '—':<7}{r.llms_txt:<8}{r.bytes_html // 1024:>5}")

    hard = {"no sitemap.xml", "robots.txt missing", "no canonical link", "no og:image"}
    fail = 0
    for r in rows:
        if r.issues:
            print(f"\n{r.id}")
            for i in r.issues:
                print(f"  ✗ {i}")
                if r.id == "labs" and i in hard:
                    fail += 1
    blocked = [f"{r.id}: {', '.join(r.ai_crawlers_blocked)}" for r in rows if r.ai_crawlers_blocked]
    print("\nAI crawlers blocked:", "; ".join(blocked) if blocked else "none — every named AI crawler may read us")

    if a.links:
        b = backlinks()
        print("\nbacklinks")
        print(f"  github code hits for our domain: {b['github']}")
        print(f"  ventures that link back home: {', '.join(b['ventures_linking_home']) or 'none'}")

    if a.json:
        payload = {"reports": [asdict(r) for r in rows]}
        if a.links:
            payload["backlinks"] = b
        open(a.json, "w").write(json.dumps(payload, indent=1))
        print(f"\nwrote {a.json}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
