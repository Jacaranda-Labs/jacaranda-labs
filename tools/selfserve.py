#!/usr/bin/env python3
"""selfserve — can this venture take money and serve the buyer without the owner?

The owner's test is one sentence: *the business sells without my input*. That is
not a feeling, it is a chain, and every link can be checked from outside:

    1. OFFER      the site publishes a price
    2. LINK       a control on the site leads to a payment page
    3. CHECKOUT   the payment page renders, with that price, to a signed-out buyer
    4. DELIVERY   something tells the buyer what happens next (auto-attach, instant
                  file, a thanks page) rather than "the owner will email you"
    5. VOICE      the venture posts without being asked (distribution, not sales)

Links 1-3 need a renderer: Whop checkout pages are client-rendered, and a plain
HTTP 200 is returned even for invented plan ids, so a status code proves nothing.

    python3 tools/selfserve.py                # full render audit, all ventures
    python3 tools/selfserve.py --fast         # HTTP only: offer + link, no renderer
    python3 tools/selfserve.py --only deskos  # one venture
    python3 tools/selfserve.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass, field, asdict

UA = {"User-Agent": "Mozilla/5.0 (selfserve audit)"}

VENTURES = {
    "attestos":       "https://attestos-edge.proofhand.workers.dev/",
    "tightbucket":    "https://0x.tightbucket.workers.dev/",
    "deskos":         "https://deskos.bidfold.workers.dev/",
    "stpi":           "https://getstpi.pages.dev/",
    "tapstall":       "https://tapstall.tapstall.workers.dev/",
    "open-practice":  "https://open-practice.open-practice.workers.dev/",
    "mechanism-audit": "https://mechanism-audit.whop.site/",
}

# Where money can enter. A link that matches none of these is a page, not a sale.
PAY_HOSTS = ("whop.com/checkout", "whop.com/", "buy.stripe.com", "checkout.stripe",
             "lemonsqueezy", "gumroad.com", "paypal.", "paystack", "flutterwave")
PRICE_RE = re.compile(r"[$£€R]\s?\d[\d,]*(?:\.\d\d)?|\d+\s?(?:usd|zar|eur|gbp)\b", re.I)
FREE_WORDS = ("free, no signup", "no signup", "always free", "free forever")


@dataclass
class Venture:
    id: str
    url: str
    status: int = 0
    prices_on_site: list[str] = field(default_factory=list)
    buy_links: list[str] = field(default_factory=list)
    checkouts: list[dict] = field(default_factory=list)
    delivery: str = ""
    voice: str = ""
    verdict: str = ""
    notes: list[str] = field(default_factory=list)


def fetch(url: str, timeout: int = 30) -> tuple[int, str, str]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
        return r.status, r.read().decode("utf-8", "replace"), r.geturl()
    except Exception as e:                                    # noqa: BLE001
        return getattr(e, "code", 0) or 0, "", url


def plain(html: str) -> str:
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


PRICE_PAGE_RE = re.compile(r"/(pricing|plans|buy|upgrade|subscribe|start)\b", re.I)


def link_scan(html: str) -> list[str]:
    hrefs = set(re.findall(r'href="([^"#]+)"', html))
    out = []
    for h in hrefs:
        low = h.lower()
        if any(p in low for p in PAY_HOSTS) or PRICE_PAGE_RE.search(low):
            out.append(h)
    return sorted(out)[:12]


def render_checkout(url: str, limit: int = 5) -> list[dict]:
    """Open each buy link in a browser and read what a signed-out buyer sees."""
    from playwright.sync_api import sync_playwright
    seen: list[dict] = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for link in [u for u in url if True][:limit]:
            pg = b.new_page(viewport={"width": 1180, "height": 900})
            try:
                pg.goto(link, wait_until="domcontentloaded", timeout=60000)
                pg.wait_for_timeout(8000)
                body = plain(pg.content())[:400]
                prices = PRICE_RE.findall(body)[:3]
                sold = re.search(r"unavailable|sold out|no longer available", body, re.I)
                seen.append({"url": pg.url[:120], "price": prices[0] if prices else "",
                             "rendered": bool(prices) and not sold,
                             "snippet": body[:120]})
            except Exception as e:                            # noqa: BLE001
                seen.append({"url": link[:120], "price": "", "rendered": False, "snippet": str(e)[:80]})
            finally:
                pg.close()
        b.close()
    return seen


def audit(vid: str, url: str, fast: bool) -> Venture:
    v = Venture(vid, url)
    st, html, _ = fetch(url)
    v.status = st
    if not html:
        v.verdict = "DOWN"
        return v
    text = plain(html)
    v.prices_on_site = sorted(set(PRICE_RE.findall(text)))[:6]
    pages = [(url, html)]
    for price_page in [b for b in link_scan(html) if PRICE_PAGE_RE.search(b)][:2]:
        st2, h2, _ = fetch(abs_url(url, price_page))
        if h2:
            pages.append((abs_url(url, price_page), h2))
    controls: set[str] = set()
    for base, h in pages:
        for href in re.findall(r'href="([^"#]+)"', h):
            if PRICE_PAGE_RE.search(href) or re.match(r"^/go/", href) or any(p in href.lower() for p in PAY_HOSTS):
                controls.add(abs_url(base, href))
        for m in re.findall(r'href="(/go/[^"#]+)"', h):
            controls.add(abs_url(base, m))
    # real payment hosts first, then in-app buy routes, then pricing pages
    def rank(u: str) -> int:
        return 0 if any(x in u.lower() for x in PAY_HOSTS) else (1 if re.search(r"/go/|/buy|/checkout", u) else 2)
    v.buy_links = sorted(controls, key=lambda u: (rank(u), u))[:12]

    # a free product is a legitimate answer, but say so instead of leaving it blank
    free_by_design = any(w in text.lower() for w in FREE_WORDS) and not v.prices_on_site

    if fast:
        v.verdict = "SELLS?" if v.buy_links else ("FREE" if free_by_design else "NO PATH")
        return v

    checkouts = render_checkout([abs_url(url, b) for b in v.buy_links], limit=5)
    v.checkouts = [c for c in checkouts if c["rendered"] or "checkout" in c["url"]]
    working = [c for c in v.checkouts if c["rendered"]]
    v.delivery = "auto" if re.search(r"instant|immediately|attached|granted|access|download|thanks|webhook", text, re.I) else "unclear"

    if working:
        v.verdict = f"SELLS ({len(working)} live)" if free_by_design is False else "SELLS"
    elif v.checkouts:
        v.verdict = "LINK DEAD"
    elif free_by_design:
        v.verdict = "FREE BY DESIGN"
    else:
        v.verdict = "NO BUY PATH"
    return v


def abs_url(base: str, href: str) -> str:
    if href.startswith("http"):
        return href
    root = re.match(r"https?://[^/]+", base).group(0)
    return root + ("" if href.startswith("/") else "/") + href


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="no renderer: offer + link only")
    ap.add_argument("--only", action="append", default=[])
    ap.add_argument("--json", metavar="PATH")
    a = ap.parse_args()

    ids = a.only or list(VENTURES)
    rows = [audit(i, VENTURES[i], a.fast) for i in ids]

    w = max(len(r.id) for r in rows)
    print(f"\n{'venture':<{w}}  {'site':>4}  {'prices':<22} {'verdict':<16} delivery")
    print("-" * (w + 56))
    for r in rows:
        print(f"{r.id:<{w}}  {r.status:>4}  {','.join(r.prices_on_site[:3])[:22]:<22} {r.verdict:<16} {r.delivery}")
    selling = [r.id for r in rows if r.verdict.startswith("SELLS")]
    print(f"\n{len(selling)}/{len(rows)} take money without the owner: {', '.join(selling) or 'none'}")
    blocked = [r.id for r in rows if r.verdict in ("NO BUY PATH", "LINK DEAD", "DOWN")]
    if blocked:
        print(f"gap: {', '.join(blocked)}")

    if a.json:
        with open(a.json, "w") as fh:
            json.dump([asdict(r) for r in rows], fh, indent=1)
        print(f"wrote {a.json}")
    return 0 if not blocked else 1


if __name__ == "__main__":
    sys.exit(main())
