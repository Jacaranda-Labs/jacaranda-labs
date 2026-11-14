#!/usr/bin/env python3
"""Jacaranda — one site for three catalogues, rebuilt for 2026.

    Laboratories      /                      the ventures, how they are built, what is for sale
    Portfolio         /courage-garikai/      the operator behind them
    Publications      /publications/         every work, with a page each and the readable ones inline

Build:  python3 build.py            → dist/
Check:  python3 build.py --check    → build, then assert the invariants
Serve:  python3 build.py --serve    → build, then serve on 0.0.0.0:8080

The design is dark editorial: video heroes, motion on scroll, a command palette, filterable
catalogues, dialogs. All of it is inline — no CDN, no framework, no network at render time — so the
page works in a sandboxed frame, on a bad connection, and in ten years.

WHAT CHANGED FROM THE FIRST BUILD
    The first build inherited `default-src 'none'` from the publications repo: no scripts, no
    external images, every page a document. The owner's instruction on 2026-11-08 was explicit —
    images, motion and interaction are the standard now — so the CSP is gone, the JS and CSS are
    inlined, and the art is local. The catalogues, the data and the two owner rules are unchanged.

CONTENT
    data/works.json     24 works: blurbs, facts, contents, formats, availability, covers, read links
    data/ventures.json  the seven ventures and the works that study each one
    data/author.json    the author record
    assets/             art (generated), covers, readable editions, figures, share card
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DIST = ROOT / "dist"
STATIC = ROOT / "static"

SITE = "https://jacaranda-labs.pages.dev"
CONTACT = "couragegarikai@atomicmail.io"
LAB_NAME = "Jacaranda Labs"
TANK_NAME = "Jacaranda Labs AI Think Tank"
PUBLISHER = "Jacaranda Labs Press · Harare"
LOCATION = "Harare, Zimbabwe"

DISCLOSURE = (
    "Jacaranda Labs owns the ventures below and funds the publications through the Jacaranda Labs AI "
    "Think Tank. Every case study names the venture it studies and states that the work was "
    "commissioned by the same owner. That disclosure does not imply independent validation."
)
AVAILABILITY = (
    "Published editions are free to read here. Private author-review editions are catalogued, not "
    "distributed; editors and reviewers can request a copy of any of them by email."
)

# accents: one per section, used for the nav pill, the gradient and the cursor light
ACCENT = {"labs": "#8b5cf6", "portfolio": "#a78bfa", "publications": "#e8467c"}


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


WORKS = load("works.json")
VENTURES = load("ventures.json")
AUTHOR = load("author.json")
BY_ID = {w["id"]: w for w in WORKS}
N = len(VENTURES)
NUM = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
NWORD = NUM.get(N, str(N))

GROUPS = [
    ("books", "Books", "Long-form work, written to be taught from.",
     ["emotional-engineering", "tight-bucket", "proof-of-mechanism", "nobody-was-watching", "flower-and-bees"]),
    ("papers", "Working papers", "Design-science case studies with coded defect logs.",
     ["constraint-native-business-models", "simulated-completeness", "unwitnessed-autonomy",
      "sovereign-micro-enterprise"]),
    ("published", "Published editions", "Read them here, free.",
     ["ledger", "intelligence", "custody", "cadence", "the-mechanism-auditor", "mechanism-audit",
      "operatorship", "the-point-of-failure"]),
    ("trade", "Trade books and essays",
     ["musk-mirror", "traffic", "pinterest", "rocket-man", "unchained"]),
    ("earlier", "Earlier works", "Listed for the record.", ["governable", "autonomy"]),
]
GROUPS = [(g[0], g[1], (g[2] if len(g) > 3 else ""), g[-1]) for g in GROUPS]
GROUP_OF = {wid: g[0] for g in GROUPS for wid in g[3]}

CSS = (STATIC / "app.css").read_text(encoding="utf-8")
JS = (STATIC / "app.js").read_text(encoding="utf-8")

MARK = ('<svg class="mark" viewBox="-48 -48 96 96" aria-hidden="true"><g fill="currentColor">'
        + "".join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>'
                  for a in (0, 72, 144, 216, 288)) + "</g></svg>")
FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-48 -48 96 96">'
           '<rect x="-48" y="-48" width="96" height="96" rx="20" fill="#0a0710"/>'
           '<g fill="#a78bfa">'
           + "".join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>'
                     for a in (0, 72, 144, 216, 288))
           + '</g><circle r="7" fill="#e8467c"/></svg>')


# --------------------------------------------------------------------------- helpers
def e(s) -> str:
    return html.escape(str(s or ""), quote=True)


def inline(s: str) -> str:
    return re.sub(r"\*([^*]+)\*", r"<em>\1</em>", e(s))


def wordlist(items) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def work_url(w) -> str:
    return f"/publications/{w['id']}/"


def cover(w, w_=74, h_=111, cls="") -> str:
    if not w.get("cover"):
        return ""
    return (f'<img class="{cls}" src="{e(w["cover"])}" width="{w_}" height="{h_}" '
            f'alt="Cover of {e(w["title"])}" loading="lazy" decoding="async">')


def state_pill(w) -> str:
    s = w.get("availability", "private")
    return {
        "available": '<span class="pill gold">Read free</span>',
        "published": '<span class="pill gold">Published</span>',
        "catalogued": '<span class="pill dim">Catalogued</span>',
        "private": '<span class="pill">Author review</span>',
    }[s]


def photo_block(name: str, alt: str, cls: str = "hero-media", low: bool = False) -> str:
    """A hero photograph: one decode, no autoplay, no 500 KB of media to fail on a phone.

    The motion that used to be a video is a 28-second CSS drift on the image itself, which the
    compositor can run without touching layout or the main thread. A phone downloads the 960px
    version instead of the 1920px one, and anybody who has asked for reduced motion gets a still.
    """
    srcset = (f'srcset="/assets/art/{name}-960.jpg 960w, /assets/art/{name}.jpg 1920w" '
              f'sizes="100vw" ' if low else "")
    return (f'<div class="{cls}"><img src="/assets/art/{name}.jpg" {srcset} '
            f'width="1920" height="1080" alt="{e(alt)}" fetchpriority="high" decoding="async"></div>')


def video_block(name: str, alt: str, cls: str = "hero-media", poster_dir="art") -> str:
    base = f"/assets/{poster_dir}/{name}"
    return f'''<div class="{cls}">
<video data-lazy autoplay muted loop playsinline preload="metadata" poster="{base}-poster.jpg" aria-label="{e(alt)}">
<source src="{base}.webm" type="video/webm"><source src="{base}.mp4" type="video/mp4">
</video></div>'''


# --------------------------------------------------------------------------- shell
def ld_graph(path: str, title: str, desc: str, extra: list | None = None) -> str:
    """The machine-readable version of the page: who we are, what the page is, what it is part of.

    An answer engine that cannot find a declared entity has to infer one from prose, and it usually
    infers the wrong one. This is cheap to emit and it is the difference between being quoted and
    being paraphrased badly.
    """
    org = {"@type": "Organization", "@id": f"{SITE}/#org", "name": LAB_NAME, "url": SITE + "/",
           "logo": {"@type": "ImageObject", "url": f"{SITE}/og.png", "width": 1200, "height": 630},
           "founder": {"@type": "Person", "@id": f"{SITE}/#person", "name": AUTHOR["name"],
                       "jobTitle": AUTHOR["role"], "url": f"{SITE}/courage-garikai/"},
           "foundingDate": "2026", "address": {"@type": "PostalAddress", "addressLocality": "Harare",
                                              "addressCountry": "ZW"},
           "email": CONTACT, "sameAs": ["https://github.com/Jacaranda-Labs"],
           "description": ("Jacaranda Labs builds constraint-native software ventures from Harare and "
                           "funds the books and working papers that study them.")}
    site = {"@type": "WebSite", "@id": f"{SITE}/#site", "url": SITE + "/", "name": LAB_NAME,
            "publisher": {"@id": f"{SITE}/#org"}, "inLanguage": "en"}
    page = {"@type": "WebPage" if path != "/" else "CollectionPage", "@id": f"{SITE}{path}#page",
            "url": f"{SITE}{path}", "name": title, "description": desc,
            "isPartOf": {"@id": f"{SITE}/#site"}, "about": {"@id": f"{SITE}/#org"},
            "inLanguage": "en", "primaryImageOfPage": {"@type": "ImageObject",
                                                       "url": f"{SITE}/og.png"}}
    graph = [org, site, page] + (extra or [])
    return ('<script type="application/ld+json">'
            + json.dumps({"@context": "https://schema.org", "@graph": graph},
                         ensure_ascii=False, separators=(",", ":"))
            + "</script>")


def page(section: str, path: str, title: str, desc: str, body: str, active: str = "",
         light: bool = False, index: list | None = None, ld: list | None = None) -> str:
    full = f"{title} · {LAB_NAME}" if LAB_NAME not in title else title
    nav = "".join(
        f'<a href="{h}"{" aria-current=page" if k == active else ""}>{e(t)}</a>'
        for k, h, t in [("labs", "/", "Laboratories"), ("portfolio", "/courage-garikai/", "Portfolio"),
                        ("publications", "/publications/", "Publications"), ("about", "/about/", "About")])
    canonical = f"{SITE}{path}"
    idx = json.dumps(index or [], ensure_ascii=False).replace("</", "<\\/")
    robots = '<meta name="robots" content="noindex">' if path == "/404.html" else f'<link rel="canonical" href="{canonical}">'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}">
{robots}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{LAB_NAME}"><meta property="og:image" content="{SITE}/og.png">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/og.png">
{ld_graph(path, title, desc, ld)}
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0a0710">
<style>{CSS.replace('@@A@@', ACCENT.get(section, ACCENT['labs']))}</style></head>
<body class="{'is-light' if light else ''}">
<div class="cursor-glow" aria-hidden="true"></div><div class="progress" aria-hidden="true"></div>
<header class="nav"><div class="bar">
<a class="brand" href="/">{MARK}<span>{LAB_NAME}<small>Ventures · Portfolio · Publications</small></span></a>
<nav class="links" aria-label="Main">{nav}
<button class="kbtn" data-open-palette type="button" aria-label="Search the site">Search <kbd>⌘K</kbd></button>
</nav></div></header>
<main id="main">{body}</main>
{footer()}
<dialog class="palette" id="palette" aria-label="Search"><input type="search" placeholder="Search works and ventures…" aria-label="Search">
<ul role="listbox"></ul></dialog>
<script>window.__index={idx};</script>
<script>{JS}</script>
</body></html>
"""


def footer() -> str:
    vs = "".join(f'<li><a href="{e(v["url"])}/" rel="noopener">{e(v["name"])}</a></li>' for v in VENTURES)
    return f"""<footer><div class="wrap"><div class="fgrid">
<div><a class="brand" href="/">{MARK}<span>{LAB_NAME}<small>Since 2026</small></span></a>
<p class="small" style="margin-top:1rem;max-width:32ch">Small, constraint-native software ventures from
Harare, and the books and papers that study them.</p>
<button class="btn ghost" data-copy="{CONTACT}" type="button">{CONTACT}</button></div>
<div><h4>This site</h4><ul>
<li><a href="/">Laboratories</a></li><li><a href="/courage-garikai/">Portfolio</a></li>
<li><a href="/publications/">Publications</a></li><li><a href="/about/">About &amp; disclosure</a></li></ul></div>
<div><h4>Ventures</h4><ul>{vs}</ul></div>
<div><h4>Elsewhere</h4><ul>
<li><a href="https://github.com/Jacaranda-Labs" rel="noopener">GitHub</a></li>
<li><a href="https://jacaranda-labs.github.io/jacaranda-labs/" rel="noopener">Static mirror</a></li>
<li><a href="/llms.txt">llms.txt</a></li>
<li><a href="mailto:{CONTACT}">Email</a></li></ul></div>
</div>
<div class="copy"><p class="disc">{e(DISCLOSURE)} {e(AVAILABILITY)}</p>
<div style="text-align:right"><div>© {dt.date.today().year} Courage Garikai · {e(PUBLISHER)}</div>
<button class="totop" data-top type="button">Back to top ↑</button></div></div>
</div></footer>"""


# --------------------------------------------------------------------------- home
def venture_data(v, i: int) -> str:
    studied = [BY_ID[s]["title"] for s in v.get("research", []) if s in BY_ID]
    facts = [("What it does", v["what"]), ("Who it is for", v["for"])]
    if studied:
        facts.append(("Studied in", ", ".join(studied)))
    extra = {
        "attestos": [("What it costs", "Free tier, then paid modules"), ("Where", "Cloudflare Workers")],
        "tightbucket": [("What it costs", "Per-audit pricing"), ("Where", "0x.tightbucket.workers.dev")],
        "deskos": [("What it costs", "Per-desk subscription"), ("Where", "deskos.whop.site")],
        "stpi": [("What it costs", "Placement fees"), ("Where", "getstpi.pages.dev")],
        "tapstall": [("What it costs", "Merchant rail, no custody"), ("Where", "tapstall.tapstall.workers.dev")],
        "open-practice": [("What it costs", "Free, no signup"), ("Where", "open-practice.workers.dev")],
        "mechanism-audit": [("What it costs", "$450 audit · $19 self-check · $1,450 sprint"),
                            ("Where", "mechanism-audit.whop.site")],
    }.get(v["id"], [])
    facts += extra
    d = {"kicker": f"Venture {i:02d}", "name": v["name"], "line": v["line"], "what": v["what"],
         "url": v["url"] + "/",
         "buy": v.get("buy", ""), "from": v.get("from", ""),
         "buy_label": v.get("buy_label", ""), "cta": f"Open {v['name']} →", "facts": facts}
    return e(json.dumps(d, ensure_ascii=False))


def build_home() -> dict:
    hero = f"""<section class="hero">
{photo_block("hero", "Jacaranda mimosifolia blossoms: violet trumpet flowers on a dark branch", low=True)}
<div class="wrap hero-inner">
<p class="kicker rv">{LOCATION} · since 2026</p>
<h1 class="rv" data-d="1">Six businesses became <em>seven</em>.<br>One operator.<br>A written record of both.</h1>
<p class="lede rv" data-d="2">Constraint-native software ventures, built with agents instead of a team — and
the books and working papers that study them, including the ones that did not work.</p>
<div class="hero-cta rv" data-d="3">
<a class="btn" href="#ventures">Meet the seven <span aria-hidden="true">↓</span></a>
<a class="btn ghost" href="/publications/">Read the catalogue</a></div>
<div class="hero-meta rv" data-d="4">
<div><b data-count="{N}">0</b>live ventures</div>
<div><b data-count="{len(WORKS)}">0</b>works catalogued</div>
<div><b data-count="{sum(1 for w in WORKS if w.get('read'))}">0</b>readable free</div>
<div><b data-count="15" data-suffix="+">0</b>years operating</div>
</div></div>
<a class="scroll-hint" href="#ventures">Scroll <span aria-hidden="true"></span></a>
</section>"""

    marquee_items = [v["name"] for v in VENTURES] + ["Harare", "Constraint-native", "Agent-operated",
                                                     "Published failures"]
    marquee = ('<div class="marquee" aria-hidden="true"><div class="marquee-track">'
               + "".join(f"<span>{e(m)} <i></i></span>" for m in marquee_items * 3) + "</div></div>")

    vcards = "".join(f"""<button class="vcard rv{' wide' if i == len(VENTURES) else ''}" data-tilt data-venture="{venture_data(v, i)}" data-d="{min(i % 4 + 1, 4)}" type="button">
<div class="vtop"><span class="vnum">{i:02d}</span>
{f'<span class="vprice">from {e(v["from"])}</span>' if v.get("from") else ''}
<span class="vdot" aria-hidden="true"></span></div>
<h3>{e(v["name"])}</h3>
<p class="vtag">{e(v["line"])}</p>
<p>{e(v["what"])[:132]}{'…' if len(v.get('what','')) > 132 else ''}</p>
<div class="vfoot"><span>Open details</span><span class="arrow" aria-hidden="true">→</span></div>
</button>""" for i, v in enumerate(VENTURES, 1))

    ventures = f"""<section class="sec" id="ventures"><div class="wrap">
<div class="sec-head rv"><div><p class="kicker">The ventures</p>
<h2>Seven businesses, each one its own blast radius</h2>
<p class="lede">Different GitHub account, different Cloudflare account, different Whop business. A leaked
key or an exhausted quota takes down one venture, never the set.</p></div>
<a class="btn ghost" href="/about/">How they are built</a></div>
<div class="vgrid">{vcards}</div></div></section>
<dialog class="vmodal" id="venture-modal"><div class="vhead"><p class="kicker" data-v-kicker></p>
<h3 data-v-name></h3><p class="vtag" data-v-line></p></div>
<div class="vbody"><dl data-v-facts></dl>
<div class="wactions"><a class="btn buy" data-v-buy href="#" rel="noopener"></a>
<a class="btn ghost" data-v-link href="#" rel="noopener">Open →</a>
<button class="btn ghost close" type="button" style="position:static;width:auto;border-radius:999px">Close</button></div>
</div></dialog>"""

    # a light band for the catalogue: the books are paper, the site is night
    picks = [BY_ID[i] for i in ["ledger", "proof-of-mechanism", "intelligence", "custody",
                                "musk-mirror", "tight-bucket"]]
    wcards = "".join(f"""<a class="wcard rv" data-d="{min(i % 4 + 1, 4)}" href="{work_url(w)}">
{cover(w)}<div class="wbody"><span class="wkind">{e(w["kind"])}</span><h4>{e(w["title"])}</h4>
<p class="wsub">{e(w["subtitle"])}</p>
<div class="wmeta">{state_pill(w)}</div></div></a>"""
                    for i, w in enumerate(picks))

    pubs = f"""<section class="sec light" id="library"><div class="wrap">
<div class="sec-head rv"><div><p class="kicker">Publications</p>
<h2>A catalogue you can actually read</h2>
<p class="lede">{sum(1 for w in WORKS if w.get('read'))} of the {len(WORKS)} works have a readable edition on
this site — no download, no email gate. The rest are private author-review copies and say so.</p></div>
<a class="btn" href="/publications/">All {len(WORKS)} works</a></div>
<div class="wgrid trip">{wcards}</div></div></section>"""

    band = f"""<section class="sec"><div class="wrap"><div class="band">
<div class="art rv">{video_block('mesh', 'A violet wireframe lattice', cls='', poster_dir='art')}
<style>.band .art video{{width:100%;height:100%;object-fit:cover;aspect-ratio:4/3}}</style></div>
<div><p class="kicker rv">The operator</p>
<h2 class="rv" data-d="1">Fifteen years of techno-preneurship, published failures included</h2>
<p class="lede rv" data-d="2">{e(AUTHOR["role"])}. I build the ventures, write the books that study them,
and put the numbers on the page — including the ones that did not move.</p>
<div class="stats rv" data-d="3">
<div class="stat"><b data-count="{N}">0</b><span>ventures</span></div>
<div class="stat"><b data-count="{len(WORKS)}">0</b><span>publications</span></div>
<div class="stat"><b data-count="0" data-suffix="">0</b><span>external funding</span></div></div>
<div class="hero-cta rv" data-d="4"><a class="btn" href="/courage-garikai/">Read the portfolio</a>
<a class="btn ghost" href="/about/">The disclosure</a></div></div>
</div></div></section>"""

    quote = f"""<section class="quote"><div class="wrap rv">
<blockquote>“A working product and a convincing demo look the same from the outside. Everything here is
an attempt to tell them apart in writing.”</blockquote>
<cite>Courage Garikai · Harare</cite></div></section>"""

    body = hero + marquee + ventures + pubs + band + quote
    index = ([{"title": v["name"], "kind": "venture", "url": v["url"] + "/"} for v in VENTURES]
             + [{"title": w["title"], "kind": w["kind"], "sub": w["subtitle"], "url": work_url(w)} for w in WORKS]
             + [{"title": t, "kind": "page", "url": u} for t, u in
                [("Courage Garikai", "/courage-garikai/"), ("Publications", "/publications/"),
                 ("About and disclosure", "/about/")]])
    desc = (f"Jacaranda Labs: {NWORD} constraint-native software ventures from Harare, built by one operator "
            f"and a set of agents, with {len(WORKS)} publications that study them.")
    return {"/": page("labs", "/", f"{LAB_NAME} · ventures, portfolio and publications", desc, body, "labs", index=index)}


# --------------------------------------------------------------------------- portfolio
def build_portfolio() -> dict:
    edu = "".join(f"<li>{e(x)}</li>" for x in AUTHOR["education"])
    hero = f"""<section class="workhero">
<div class="bg">{video_block('ribbon', 'Soft lilac ribbons', cls='', poster_dir='art')}
<style>.workhero .bg video{{width:100%;height:100%;object-fit:cover}}</style></div>
<div class="wrap"><p class="kicker rv">Portfolio</p>
<h1 class="rv" data-d="1">Courage Garikai</h1>
<p class="lede rv" data-d="2">{e(AUTHOR["role"])} · {e(LOCATION)} (CAT, UTC+2)</p>
<div class="hero-cta rv" data-d="3"><a class="btn" href="#ventures">The ventures</a>
<a class="btn ghost" href="/publications/">The publications</a>
<button class="btn ghost" data-copy="{CONTACT}" type="button">Copy email</button></div>
<div class="hero-meta rv" data-d="4">
<div><b data-count="{N}">0</b>ventures</div><div><b data-count="{len(WORKS)}">0</b>works</div>
<div><b data-count="15" data-suffix="+">0</b>years</div></div></div></section>"""

    about = f"""<section class="sec"><div class="wrap band">
<div><p class="kicker rv">Practice</p><h2 class="rv" data-d="1">What I do</h2>
<div class="prose rv" data-d="2">
<p>I build software businesses with a small number of AI agents doing the execution, then write down what
happened — including the audit findings and the numbers that did not move.</p>
<p>{e(AUTHOR["practice"])} The work is deliberately constraint-native: free tiers, quotas, one owner, no
capital. The constraint is the design material, not the excuse.</p></div>
<h4 class="rv" data-d="3" style="margin-top:2rem">Education</h4>
<ul class="rv" data-d="3" style="color:var(--mute)">{edu}</ul></div>
<div class="panel rv" data-d="2"><p class="kicker">At a glance</p>
<dl><dt>Based</dt><dd>{e(LOCATION)} (CAT, UTC+2)</dd><dt>Ventures</dt><dd>{N} live</dd>
<dt>Works</dt><dd>{len(WORKS)} catalogued, {sum(1 for w in WORKS if w.get('read'))} readable</dd>
<dt>Publisher</dt><dd>{e(PUBLISHER)}</dd><dt>Contact</dt><dd><a href="mailto:{CONTACT}">{CONTACT}</a></dd></dl>
<a class="btn" href="/about/" style="margin-top:1.2rem">Ownership &amp; disclosure</a></div>
</div></section>"""

    vcards = "".join(f"""<a class="wcard rv" data-d="{min(i % 4 + 1, 4)}" href="{e(v['url'])}/" rel="noopener">
<div class="wbody"><h4>{e(v['name'])}</h4><p class="wsub">{e(v['line'])}</p>
<p class="wsub">{e(v['what'])[:110]}…</p>
<div class="wmeta"><span class="pill dim">venture</span><span class="pill">live</span></div></div></a>"""
                    for i, v in enumerate(VENTURES))

    pubs = "".join(f"""<a class="wcard rv" data-d="{min(i % 4 + 1, 4)}" href="{work_url(w)}">
{cover(w)}<div class="wbody"><span class="wkind">{e(w["kind"])}</span><h4>{e(w["title"])}</h4>
<p class="wsub">{e(w["subtitle"])}</p><div class="wmeta">{state_pill(w)}</div></div></a>"""
                   for i, w in enumerate(WORKS))

    body = hero + about + f"""<section class="sec" id="ventures"><div class="wrap">
<div class="sec-head rv"><div><p class="kicker">Ventures</p><h2>What I run</h2></div>
<a class="btn ghost" href="/">Laboratories →</a></div><div class="wgrid">{vcards}</div></div></section>
<section class="sec light"><div class="wrap">
<div class="sec-head rv"><div><p class="kicker">Publications</p><h2>What I have written</h2>
<p class="lede">Four books and four working papers in author review, the published editions behind them,
and two earlier works listed for the record.</p></div>
<a class="btn" href="/publications/">Full catalogue</a></div>
<div class="wgrid">{pubs}</div></div></section>"""
    index = ([{"title": w["title"], "kind": w["kind"], "sub": w["subtitle"], "url": work_url(w)} for w in WORKS]
             + [{"title": v["name"], "kind": "venture", "url": v["url"] + "/"} for v in VENTURES])
    desc = (f"{AUTHOR['name']} — {AUTHOR['role']}. {N} ventures and {len(WORKS)} publications from "
            f"Jacaranda Labs, Harare.")
    return {"/courage-garikai/": page("portfolio", "/courage-garikai/", f"{AUTHOR['name']} · portfolio",
                                      desc, body, "portfolio", index=index)}


# --------------------------------------------------------------------------- publications
def work_card(w) -> str:
    hay = " ".join([w["title"], w["subtitle"], w["kind"], GROUP_OF.get(w["id"], "")]).lower()
    return f"""<a class="wcard rv" data-work data-group="{GROUP_OF.get(w['id'], '')}" data-haystack="{e(hay)}"
data-d="{min(len(hay) % 4 + 1, 4)}" href="{work_url(w)}">
{cover(w)}<div class="wbody"><span class="wkind">{e(w["kind"])}</span><h4>{e(w["title"])}</h4>
<p class="wsub">{e(w["subtitle"])}</p>
<div class="wmeta">{state_pill(w)}{'<span class="pill dim">Read online</span>' if w.get('read') else ''}</div></div></a>"""


def build_publications() -> dict:
    chips = "".join(f'<button class="chip" data-filter="{k}" type="button" aria-pressed="{str(k == "all").lower()}">'
                    f'{e(t)}</button>' for k, t in
                    [("all", f"All {len(WORKS)}")] + [(g[0], g[1]) for g in GROUPS])
    hero = f"""<section class="workhero">
<div class="bg">{video_block('ribbon', 'Soft lilac ribbons', cls='', poster_dir='art')}
<style>.workhero .bg video{{width:100%;height:100%;object-fit:cover}}</style></div>
<div class="wrap"><p class="kicker rv">Publications · {e(PUBLISHER)}</p>
<h1 class="rv" data-d="1">{len(WORKS)} works.<br><em style="font-style:normal;background:linear-gradient(100deg,var(--electric),var(--magenta));-webkit-background-clip:text;background-clip:text;color:transparent">{sum(1 for w in WORKS if w.get('read'))} you can read right now.</em></h1>
<p class="lede rv" data-d="2">Books, working papers and essays funded by the {TANK_NAME}. Public editions
open in place. Private author-review editions are catalogued, not distributed.</p>
<p class="small rv" data-d="3">Showing <b id="wcount">{len(WORKS)}</b> works
<span aria-hidden="true">·</span> press <kbd>⌘K</kbd> to search from anywhere</p></div></section>"""

    listing = f"""<section class="sec light"><div class="wrap">
<div class="rv" style="display:flex;gap:1rem;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:1.6rem">
<div class="chips">{chips}</div>
<div class="searchbox"><span aria-hidden="true">⌕</span>
<input id="wsearch" type="search" placeholder="Filter by title, subject or kind…" aria-label="Filter publications"></div></div>
<div class="wgrid">{''.join(work_card(w) for w in WORKS)}</div>
<p class="empty" id="wempty" hidden>Nothing matches that. <button class="chip" type="button" onclick="document.getElementById('wsearch').value='';document.querySelector('[data-filter=all]').click()">Reset</button></p>
</div></section>"""
    body = hero + listing
    index = ([{"title": w["title"], "kind": w["kind"], "sub": w["subtitle"], "url": work_url(w)} for w in WORKS]
             + [{"title": g[1], "kind": "section", "url": "/publications/"} for g in GROUPS])
    desc = (f"The catalogue: {len(WORKS)} books, working papers and essays from Jacaranda Labs Press, "
            f"{sum(1 for w in WORKS if w.get('read'))} of them free to read on the site.")
    cat_ld = [{"@type": "ItemList", "name": "Jacaranda Labs Press catalogue", "numberOfItems": len(WORKS),
               "itemListElement": [{"@type": "ListItem", "position": i, "url": f"{SITE}{work_url(x)}",
                                    "name": x["title"]} for i, x in enumerate(WORKS, 1)]}]
    return {"/publications/": page("publications", "/publications/", "Publications · the catalogue",
                                    desc, body, "publications", index=index, ld=cat_ld)}


def build_work(w) -> str:
    facts = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in [
        ("Kind", w["kind"].capitalize()), ("Series", w.get("series") if len(w.get("series") or "") < 46 else None),
        ("Edition", w.get("edition")), ("Funded by", w.get("funded_by"))] if v)
    for i, fact in enumerate(w.get("facts") or []):
        if fact:
            facts += f"<dt>{'Length' if i == 0 else ('Structure' if i == 1 else 'Format')}</dt><dd>{e(fact)}</dd>"

    state = w.get("availability", "private")
    if state == "available" and w.get("read"):
        links = (f'<a class="btn" href="{e(w["read"])}">Read it now</a>'
                 + "".join(f'<a class="btn ghost" href="{e(u)}">{e(k)}</a>'
                           for k, u in (w.get("formats") or {}).items() if k.upper() != "HTML"))
        notice = f'<div class="notice gold"><p><strong>Free to read.</strong> The full edition is on this '
        notice += f'site — no download, no email gate.</p><div class="wactions">{links}</div></div>'
    elif state == "available":
        links = "".join(f'<a class="btn ghost" href="{e(u)}">{e(k)}</a>' for k, u in (w.get("formats") or {}).items())
        notice = f'<div class="notice gold"><p><strong>Published edition.</strong> Download it directly.</p>' \
                 f'<div class="wactions">{links}</div></div>'
    elif state == "catalogued":
        notice = ('<div class="notice"><p><strong>Listed for the record.</strong> No copy is distributed '
                  'from this site. Ask if you need to consult it.</p></div>')
    else:
        subj = f"Review copy request: {w['title']}".replace(" ", "%20").replace(":", "%3A")
        notice = (f'<div class="notice"><p><strong>Private author-review edition.</strong> Catalogued here, '
                  f'not distributed. Editors and reviewers can '
                  f'<a href="mailto:{CONTACT}?subject={subj}">request a copy</a>.</p></div>')

    cover_html = (f'<div class="wcover rv">{cover(w, 600, 900)}</div>' if w.get("cover")
                  else f'<div class="wcover ph rv">{MARK}</div>')
    toc = ""
    if w.get("toc"):
        toc = ('<div><p class="kicker" style="margin-top:2.4rem">Contents</p><ol class="toc">'
               + "".join(f"<li>{e(t)}</li>" for t in w["toc"]) + "</ol></div>")
    disc = (f'<h4 style="margin-top:2rem">Case disclosure</h4><p class="small">{e(w["case_disclosure"])}</p>'
            if w.get("case_disclosure") else "")

    body = f"""<section class="workhero">
<div class="bg">{video_block('mesh', '', cls='', poster_dir='art')}<style>.workhero .bg video{{width:100%;height:100%;object-fit:cover}}</style></div>
<div class="wrap"><p class="crumbs"><a href="/publications/">Publications</a> / {e(w["kind"])}</p>
<div class="wlayout">{cover_html}
<div class="wtitle"><p class="kicker rv">{e(w["kind"])}{' · ' + e(w["series"]) if w.get("series") and len(w["series"]) < 46 else ''}</p>
<h1 class="rv" data-d="1">{e(w["title"])}</h1>
<p class="wsub rv" data-d="2">{e(w["subtitle"])}</p>
<div class="wactions rv" data-d="3">{state_pill(w)}{(' ' + f'<a class="btn" href="{e(w["read"])}">Read it now</a>') if w.get("read") else ''}
<a class="btn ghost" href="/publications/">Catalogue</a></div></div></div></div></section>
<section class="sec flush"><div class="wrap"><div class="wmain">
<div><p class="kicker rv">About this work</p>
<div class="prose rv" data-d="1"><p>{inline(w["blurb"])}</p></div>{disc}{toc}</div>
<aside class="rv" data-d="2"><div class="panel"><dl>{facts}</dl></div>{notice}</aside>
</div></div></section>
{related(w)}"""
    idx = [{"title": x["title"], "kind": x["kind"], "sub": x["subtitle"], "url": work_url(x)} for x in WORKS]
    kind_ld = {"book": "Book", "paper": "ScholarlyArticle", "research": "Report", "essay": "Article"}.get(
        (w.get("kind") or "").lower(), "CreativeWork")
    work_ld = [{"@type": kind_ld, "@id": f"{SITE}{work_url(w)}#work", "name": w["title"],
                "headline": w["title"], "alternativeHeadline": w.get("subtitle", ""),
                "abstract": (w.get("blurb") or "")[:500],
                "author": {"@type": "Person", "@id": f"{SITE}/#person", "name": AUTHOR["name"]},
                "publisher": {"@id": f"{SITE}/#org"},
                "inLanguage": "en",
                **({"image": f"{SITE}{w['cover']}"} if w.get("cover") else {}),
                **({"datePublished": "2026"} if "2026" in str(w.get("edition") or "") else {}),
                "isPartOf": {"@id": f"{SITE}/#site"},
                "url": f"{SITE}{work_url(w)}"},
               {"@type": "BreadcrumbList", "itemListElement": [
                   {"@type": "ListItem", "position": 1, "name": "Publications", "item": f"{SITE}/publications/"},
                   {"@type": "ListItem", "position": 2, "name": w["title"],
                    "item": f"{SITE}{work_url(w)}"}]}]
    return page("publications", work_url(w), w["title"], (w.get("blurb") or w["subtitle"])[:180],
                body, "publications", index=idx, ld=work_ld)


def related(w) -> str:
    group = [i for i in next(g[3] for g in GROUPS if w["id"] in g[3]) if i != w["id"]]
    picks = [BY_ID[i] for i in group[:3]] or [x for x in WORKS if x["id"] != w["id"]][:3]
    return f"""<section class="sec"><div class="wrap">
<div class="sec-head rv"><div><p class="kicker">Also in the catalogue</p><h2 style="font-size:1.7rem">Read next</h2></div></div>
<div class="wgrid">{''.join(work_card(x) for x in picks)}</div></div></section>"""


def build_about() -> dict:
    doors = "".join(f"<li>{e(x)}</li>" for x in [
        "Each venture has its own GitHub account, Cloudflare account and Whop business.",
        "Free tiers are design material: quotas are budgeted before features are written.",
        "Work is checked by mechanism audits — does the thing do what the page says it does.",
        "Failures are published with the same care as successes, and named as failures.",
    ])
    body = f"""<section class="workhero"><div class="bg">{video_block('mesh','',cls='',poster_dir='art')}
<style>.workhero .bg video{{width:100%;height:100%;object-fit:cover}}</style></div>
<div class="wrap"><p class="kicker rv">About</p><h1 class="rv" data-d="1">What this is,<br>and what it is not.</h1>
<p class="lede rv" data-d="2">One owner, {NWORD} ventures, agents doing the execution, and a written record
of what happened.</p></div></section>
<section class="sec"><div class="wrap band">
<div><h2 class="rv">The lab</h2><div class="prose rv" data-d="1">
<p>{NWORD.capitalize()} ventures run from Harare: {e(wordlist([v["name"] for v in VENTURES]))}. Each one is
small, self-hosted on free or near-free infrastructure, and sold directly rather than through an app store.</p>
<p>The {TANK_NAME} funds the books and working papers in the catalogue. It is a funding relationship, not a
publisher's peer review: no work here has been independently refereed.</p></div>
<h4 class="rv" data-d="2" style="margin-top:2rem">How the ventures are built</h4>
<ul class="rv" data-d="2" style="color:var(--mute)">{doors}</ul></div>
<div><div class="panel rv" data-d="1"><p class="kicker">At a glance</p>
<dl><dt>Ventures</dt><dd>{N} live</dd><dt>Publications</dt><dd>{len(WORKS)} catalogued</dd>
<dt>Readable free</dt><dd>{sum(1 for w in WORKS if w.get('read'))}</dd>
<dt>Owner</dt><dd>{e(AUTHOR["name"])}</dd><dt>Based</dt><dd>{e(LOCATION)}</dd>
<dt>Contact</dt><dd><a href="mailto:{CONTACT}">{CONTACT}</a></dd></dl></div>
<div class="notice rv" data-d="2"><p><strong>What is not claimed.</strong> No independent validation, no
customer outcomes, no certification. Works that study a venture say so in their own disclosure.</p></div>
<div class="notice rv" data-d="3"><p><strong>The disclosure, in one paragraph.</strong> {e(DISCLOSURE)}</p></div></div>
</div></section>"""
    desc = ("How Jacaranda Labs runs seven ventures and funds the publications that study them, with the "
            "disclosure that follows from a single owner.")
    index = [{"title": "About and disclosure", "kind": "page", "url": "/about/"},
             {"title": "Publications", "kind": "page", "url": "/publications/"},
             {"title": "Portfolio", "kind": "page", "url": "/courage-garikai/"}]
    return {"/about/": page("labs", "/about/", "About and disclosure", desc, body, "about", index=index)}


def build_404() -> dict:
    body = f"""<section class="workhero"><div class="bg">{photo_block("hero", "", cls="")}
<style>.workhero .bg img{{width:100%;height:100%;object-fit:cover}}</style></div>
<div class="wrap"><p class="kicker">404</p><h1>That page is not here.</h1>
<p class="lede">It may have moved when the three catalogues were merged into one site.</p>
<div class="hero-cta"><a class="btn" href="/">Laboratories</a>
<a class="btn ghost" href="/publications/">Publications</a>
<a class="btn ghost" href="/courage-garikai/">Portfolio</a></div></div></section>"""
    return {"/404.html": page("labs", "/404.html", "Page not found", "That page is not here.", body)}


# --------------------------------------------------------------------------- extras
def llms_txt() -> str:
    out = [f"# {LAB_NAME}", "",
           f"> {NWORD.capitalize()} software ventures built by one operator and a set of agents, and the "
           f"publications that study them. {LOCATION}.", "", "## Sections", "",
           f"- [Laboratories]({SITE}/): the {NWORD} ventures",
           f"- [Portfolio]({SITE}/courage-garikai/): {AUTHOR['name']}, {AUTHOR['role']}",
           f"- [Publications]({SITE}/publications/): {len(WORKS)} works, "
           f"{sum(1 for w in WORKS if w.get('read'))} readable free",
           f"- [About]({SITE}/about/): ownership and disclosure", "", "## Ventures", ""]
    for v in VENTURES:
        out.append(f"- [{v['name']}]({v['url']}/): {v['line']} {v['what']}")
    out += ["", "## Publications", ""]
    for key, title, _, ids in GROUPS:
        out.append(f"### {title}")
        for i in ids:
            w = BY_ID[i]
            state = ("free to read" if w.get("read") else
                     {"available": "published edition", "catalogued": "listed for the record",
                      "private": "private author-review, request a copy"}.get(w.get("availability"), ""))
            out.append(f"- [{w['title']}]({SITE}{work_url(w)}): {w['subtitle']} ({state})")
        out.append("")
    out += ["## Notes", "", f"- Contact: {CONTACT}", f"- {DISCLOSURE}"]
    return "\n".join(out) + "\n"


def sitemap(paths) -> str:
    today = dt.date.today().isoformat()
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p in sorted(set(paths)))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


# IndexNow: Bing, Yandex, Seznam and Naver accept a ping the moment a URL changes; Google does not,
# so this is the one index we can push without a Search Console login. The key is public by design —
# it is served at /<key>.txt and proves we own the host.
INDEXNOW_KEY = "5a7541fb26984a8bca8973a4024d8233"

HEADERS = """/*
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN

/assets/*
  Cache-Control: public, max-age=604800, immutable

/favicon.svg
  Cache-Control: public, max-age=604800
"""


# --------------------------------------------------------------------------- build
def write(rel: str, text: str) -> None:
    path = DIST / rel.lstrip("/")
    if rel.endswith("/"):
        path = path / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--serve", action="store_true")
    args = ap.parse_args(argv)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    pages: dict[str, str] = {}
    pages.update(build_home())
    pages.update(build_portfolio())
    pages.update(build_publications())
    for w in WORKS:
        pages[work_url(w)] = build_work(w)
    pages.update(build_about())
    pages.update(build_404())

    for path, html_text in pages.items():
        write(path, html_text)

    write(f"/{INDEXNOW_KEY}.txt", INDEXNOW_KEY)
    write("/favicon.svg", FAVICON)
    write("/_headers", HEADERS)
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    write("/sitemap.xml", sitemap([p for p in pages if p != "/404.html"]))
    write("/llms.txt", llms_txt())
    write("/.nojekyll", "")
    if (ROOT / "assets").is_dir():
        for asset in sorted((ROOT / "assets").rglob("*")):
            if asset.is_file():
                target = DIST / "assets" / asset.relative_to(ROOT / "assets")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, target)
        if (ROOT / "assets" / "og.png").is_file():      # the share card lives at the root too
            shutil.copy2(ROOT / "assets" / "og.png", DIST / "og.png")
        # covers, readable editions and their figures are addressed as /covers/… and /read/…,
        # so they sit at the site root rather than under /assets/
        for sub in ("covers", "read"):
            src = ROOT / "assets" / sub
            if src.is_dir():
                shutil.copytree(src, DIST / sub, dirs_exist_ok=True)

    ok = run_checks(pages) if args.check else True
    total = sum(len(p) for p in pages.values())
    weight = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"built {len(pages)} pages · {total // 1024} KB of HTML · {weight / 1e6:.1f} MB total → dist/")
    if args.serve:
        serve()
    return 0 if ok else 1


def run_checks(pages: dict) -> bool:
    problems = []
    for path, text in pages.items():
        if text.count("<h1") != 1:
            problems.append(f"{path}: expected exactly one h1, found {text.count('<h1')}")
        for m in re.finditer(r'(?:href|src)="(/[^"#]*)"', text):
            target = m.group(1)
            if target in ("/favicon.svg", "/og.png", "/sitemap.xml", "/robots.txt", "/llms.txt"):
                continue
            if target not in pages and not (DIST / target.lstrip("/")).exists():
                problems.append(f"{path}: dead internal reference {target}")
    for w in WORKS:
        p = work_url(w)
        if p not in pages:
            problems.append(f"missing page for {w['id']}")
            continue
        if not re.search(r"request a copy|Free to read\.|Download it directly\.|Listed for the record\.", pages[p]):
            problems.append(f"{p}: does not state availability")
        for key in ("cover", "read"):
            rel = w.get(key) or ""
            if rel and not (DIST / rel.lstrip("/")).is_file():
                problems.append(f"{w['id']}: {key} {rel} missing from dist/")
        if w.get("read") and w["read"] not in pages[p]:
            problems.append(f"{w['id']}: readable edition not linked from its page")
    for asset in ("art/hero.jpg", "art/hero-960.jpg", "og.png"):
        if not (DIST / "assets" / asset).is_file():
            problems.append(f"missing media: assets/{asset}")
    for p in problems:
        print("  ✗", p, file=sys.stderr)
    print(f"  {'✓' if not problems else '✗'} {len(pages)} pages checked, {len(problems)} problems")
    return not problems


def serve():
    import functools
    import http.server
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    print("serving dist/ on http://0.0.0.0:8080")
    http.server.ThreadingHTTPServer(("0.0.0.0", 8080), handler).serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
