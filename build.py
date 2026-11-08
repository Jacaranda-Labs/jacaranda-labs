#!/usr/bin/env python3
"""Jacaranda — one site for three catalogues.

    Laboratories      /                      the six ventures, how they are built, the think tank
    Portfolio         /courage-garikai/      the author: ventures, works, earlier record
    Publications      /publications/         every work, with a page each

Build:  python3 build.py          → dist/
Check:  python3 build.py --check  → build, assert the invariants, print a summary

Stdlib only, no JavaScript, every page self-contained. The point is that this site can be served by
anything — a static host, a CDN, a USB stick — and still be readable in ten years.

WHERE THE CONTENT COMES FROM
    data/works.json      snapshotted from stpi-cloud/publications: README.md, each
                         edition-manifest.json, sites/data/legacy-catalogue.json and earlier.json
    data/ventures.json   the six ventures and the research each one is studied in
    data/author.json     the author record
Nothing here is invented. If a fact is not in those files it is not on the page.
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

SITE = "https://jacaranda-labs.pages.dev"       # change here, and in _headers/robots if you move it
CONTACT = "couragegarikai@atomicmail.io"
PHONE_DISPLAY = "+263 78 000 0000"              # placeholder: replace before launch
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
    "Published editions are free to read or download. Private author-review editions are catalogued, not "
    "distributed; editors and reviewers can request a copy of any of them by email."
)

sections = {
    "labs": ("#7B5EA7", "#f4eef9", "#2b2238"),
    "portfolio": ("#5d3f8e", "#f6f2fa", "#2a2233"),
    "publications": ("#6b2d5c", "#faf1f6", "#2c1c28"),
}

# --------------------------------------------------------------------------- data
def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


WORKS = load("works.json")
VENTURES = load("ventures.json")
AUTHOR = load("author.json")
EARLIER = load("earlier.json")
BY_ID = {w["id"]: w for w in WORKS}

GROUPS = [
    ("books", "Books", "Long-form works, written to be taught from. Each carries a discussion structure, "
                       "a framework compendium and exercises.",
     ["emotional-engineering", "tight-bucket", "proof-of-mechanism", "nobody-was-watching", "flower-and-bees"]),
    ("papers", "Working papers and reports", "Design-science case studies with coded defect logs, reference "
                                             "lists and propositions offered for testing.",
     ["constraint-native-business-models", "simulated-completeness", "unwitnessed-autonomy",
      "sovereign-micro-enterprise"]),
    ("published", "Published editions", "Editions that exist in public: read them, download them, teach from "
                                        "them.",
     ["ledger", "intelligence", "custody", "cadence"]),
    ("trade", "Other books and essays", "Shorter trade work and long essays, published under the press.",
     ["musk-mirror", "traffic", "pinterest", "rocket-man", "unchained"]),
    ("earlier", "Earlier works, listed for the record", "No manuscript online. Both use DeskOS as their case "
                                                        "and describe it before its October 2026 rebuild.",
     ["governable", "autonomy"]),
]
SECTION_OF = {wid: "publications" for key, _, _, ids in GROUPS for wid in ids}

# --------------------------------------------------------------------------- text helpers
def e(s) -> str:
    return html.escape(str(s or ""), quote=True)


def inline(s: str) -> str:
    """Escape, then restore the two bits of markup the source actually uses: *emphasis* and quotes."""
    out = e(s)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    return out


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def wordlist(items) -> str:
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def fmt_count(n: int) -> str:
    return f"{n:,}"


# --------------------------------------------------------------------------- chrome
MARK = ('<svg class="mark" viewBox="-48 -48 96 96" aria-hidden="true" focusable="false"><g fill="currentColor">'
        + "".join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>'
                  for a in (0, 72, 144, 216, 288))
        + '</g><circle r="7" fill="var(--paper)"/></svg>')
FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-48 -48 96 96">'
           '<rect x="-48" y="-48" width="96" height="96" rx="18" fill="#7B5EA7"/>'
           '<g fill="#FBF8FD">' + "".join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>'
                                          for a in (0, 72, 144, 216, 288))
           + '</g><circle r="7" fill="#7B5EA7"/></svg>\n')

NAV = [
    ("labs", "/", "Laboratories"),
    ("portfolio", "/courage-garikai/", "Portfolio"),
    ("publications", "/publications/", "Publications"),
]

CSS = """
:root{--a:%(a)s;--soft:%(soft)s;--deep:%(deep)s;--ink:#1e1a24;--mute:#5d5768;--line:#e6e0ec;--paper:#fdfcfe;--gold:#c8a24a}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%%}body{margin:0;background:var(--paper);color:var(--ink);
font:17px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--a);text-underline-offset:.18em}a:hover{color:var(--deep)}
a:focus-visible{outline:3px solid var(--a);outline-offset:2px;border-radius:3px}
.skip{position:absolute;left:-999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem 1rem;z-index:9}
.wrap{max-width:1100px;margin:0 auto;padding:0 24px}
h1,h2,h3,h4,.serif{font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
font-weight:600;letter-spacing:-.012em;line-height:1.18;margin:0}
h1{font-size:clamp(2.2rem,5vw,3.7rem);margin:.15em 0 .35em}h2{font-size:clamp(1.6rem,2.9vw,2.2rem);margin:0 0 .45em}
h3{font-size:1.32rem;margin:0 0 .25em}h4{font-size:1.02rem;margin:0 0 .3em}
p{margin:0 0 1em}.lede{font-size:1.22rem;line-height:1.55;color:var(--mute);max-width:44em}
.kicker{font-size:.76rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--a)}
.meta{font-size:.9rem;color:var(--mute)}
/* header */
header.top{position:sticky;top:0;z-index:5;background:rgba(253,252,254,.94);border-bottom:1px solid var(--line);
backdrop-filter:saturate(140%%) blur(6px)}
.bar{display:flex;align-items:center;justify-content:space-between;gap:1rem;min-height:68px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:.6rem;color:var(--ink);text-decoration:none;font-weight:650;letter-spacing:-.01em}
.brand .mark{width:30px;height:30px;color:var(--a)}
.brand small{display:block;font:600 .66rem/1.2 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}
nav.main{display:flex;gap:.35rem;flex-wrap:wrap;font-size:.95rem}
nav.main a{color:var(--mute);text-decoration:none;padding:.4rem .7rem;border-radius:999px}
nav.main a:hover{color:var(--ink);background:var(--soft)}
nav.main a[aria-current=page]{color:#fff;background:var(--a)}
/* hero */
.hero{position:relative;overflow:hidden;background:linear-gradient(175deg,var(--soft) 0%%,var(--paper) 78%%);padding:76px 0 60px;border-bottom:1px solid var(--line)}
.hero .wm{position:absolute;right:-90px;top:-70px;width:420px;height:420px;color:var(--a);opacity:.07;pointer-events:none}
.hero .mark{width:58px;height:58px;color:var(--a);display:block;margin-bottom:18px}
.hero.tight{padding:56px 0 44px}
/* sections */
section{padding:56px 0;border-top:1px solid var(--line)}section.hero{border-top:0;padding:76px 0 60px}
.sec-head{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin-bottom:26px}
.sec-head h2{margin:0}
/* the three doors */
.doors{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.door{display:flex;flex-direction:column;gap:.5rem;background:#fff;border:1px solid var(--line);border-radius:16px;
padding:24px 24px 20px;text-decoration:none;color:inherit;transition:transform .12s ease,border-color .12s ease}
.door:hover{transform:translateY(-2px);border-color:var(--a)}
.door .n{font:700 .74rem/1 system-ui,sans-serif;letter-spacing:.16em;text-transform:uppercase;color:var(--a)}
.door h3{font-size:1.42rem}.door p{color:var(--mute);font-size:.96rem;margin:0}
.door .go{color:var(--a);font-weight:650;font-size:.93rem;margin-top:.3rem}
/* cards + grids */
.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;display:flex;flex-direction:column;gap:.4rem}
.card h3{font-size:1.24rem}.card h3 a{color:var(--ink);text-decoration:none}.card h3 a:hover{color:var(--a)}
.card p{color:var(--mute);font-size:.96rem;margin:0}
.card .go{margin-top:auto;padding-top:.8rem;font-weight:650;font-size:.93rem}
.card .no{font:700 .72rem/1 system-ui,sans-serif;letter-spacing:.16em;color:var(--a);opacity:.75}
.tag{display:inline-block;font:700 .71rem/1.5 system-ui,sans-serif;letter-spacing:.07em;text-transform:uppercase;
color:var(--a);background:var(--soft);border-radius:999px;padding:.18rem .62rem;margin:0 .3rem .45rem 0;white-space:nowrap}
.tag.dim{color:var(--mute);background:#f2eff5}.tag.gold{color:#7a5c12;background:#fbf3dd}
.btn{display:inline-block;background:var(--a);color:#fff;text-decoration:none;font-weight:650;border-radius:10px;
padding:.62rem 1.05rem;margin:.3rem .45rem .3rem 0}.btn:hover{background:var(--deep);color:#fff}
.btn.ghost{background:transparent;color:var(--a);border:1.5px solid var(--a)}.btn.ghost:hover{background:var(--soft);color:var(--deep)}
/* work list */
.list{list-style:none;padding:0;margin:0}
.list>li{padding:22px 0;border-bottom:1px solid var(--line)}
.list>li:last-child{border-bottom:0}
.row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1rem;align-items:start}
.list h3 a{color:var(--ink);text-decoration:none}.list h3 a:hover{color:var(--a)}
.sub{color:var(--mute);margin:.15rem 0 .5rem;font-size:1.04rem;max-width:52em}
.meta-row{display:flex;gap:1rem;flex-wrap:wrap;font-size:.86rem;color:var(--mute);margin-top:.4rem}
/* facts */
dl.facts{display:grid;grid-template-columns:max-content minmax(0,1fr);gap:.5rem 1.3rem;margin:0 0 1.6rem;font-size:.96rem}
dl.facts dt{font-weight:650}dl.facts dd{margin:0;color:var(--mute);overflow-wrap:anywhere}
.note{overflow-wrap:anywhere}
/* notes */
.note{background:var(--soft);border-left:4px solid var(--a);border-radius:10px;padding:16px 18px;margin:1.3rem 0;font-size:.96rem}
.note p:last-child{margin:0}
.note.plain{background:#f6f5f8;border-left-color:#bab3c4}
.note.gold{background:#fdf8ea;border-left-color:var(--gold)}
.cols{display:grid;gap:44px;grid-template-columns:minmax(0,1fr) 300px}.cols.rev{grid-template-columns:300px minmax(0,1fr)}
/* work page */
.work-head{display:grid;grid-template-columns:150px minmax(0,1fr);gap:30px;align-items:start}
.plate{width:150px;aspect-ratio:2/3;border-radius:6px;background:linear-gradient(160deg,var(--soft),#e7dcf1);
display:flex;align-items:center;justify-content:center;box-shadow:0 8px 26px rgba(45,25,65,.16);color:var(--a)}
.plate .mark{width:56px;height:56px}
ol.toc{padding-left:1.3rem;color:var(--mute);columns:2 260px;column-gap:2.2rem;font-size:.95rem}
ol.toc li{break-inside:avoid;margin:0 0 .35rem}
/* footer */
footer{background:var(--deep);color:#e9e3f1;padding:50px 0 34px;margin-top:26px;font-size:.93rem}
footer a{color:#fff}footer h4{font:700 .74rem/1.4 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#c9b9e0;margin-bottom:.7rem}
footer ul{list-style:none;padding:0;margin:0}footer li{margin:.28rem 0}
.fgrid{display:grid;gap:28px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.small{font-size:.85rem;line-height:1.6;color:#cabfdb;margin-top:28px;border-top:1px solid rgba(255,255,255,.16);padding-top:18px}
/* print */
@media (max-width:820px){.cols,.cols.rev,.work-head{grid-template-columns:1fr}.plate{width:104px}}
@media print{header.top,footer,nav,.doors{display:none}body{font-size:11pt}a{color:#000;text-decoration:none}}
"""

HEADERS = """/*
  Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: interest-cohort=(), camera=(), microphone=(), geolocation=()
  X-Frame-Options: DENY

/favicon.svg
  Cache-Control: public, max-age=604800
"""


def page(section: str, path: str, title: str, desc: str, body: str, active: str = "") -> str:
    a, soft, deep = sections[section]
    full = f"{title} · {LAB_NAME}" if LAB_NAME not in title else title
    nav = "".join(
        f'<a href="{h}"{" aria-current=page" if key == active else ""}>{e(t)}</a>' for key, h, t in NAV)
    canonical = f"{SITE}{path}"
    robots = '<meta name="robots" content="noindex">' if path == "/404.html" else f'<link rel="canonical" href="{canonical}">'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title><meta name="description" content="{e(desc)}">
{robots}<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{LAB_NAME}"><meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Jacaranda Labs — six businesses, one operator, and a written record of both">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="{a}">
<style>{CSS % {"a": a, "soft": soft, "deep": deep}}</style></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar">
<a class="brand" href="/">{MARK}<span>{LAB_NAME}<small>Ventures · Portfolio · Publications</small></span></a>
<nav class="main" aria-label="Main">{nav}</nav></div></header>
<main id="main">{body}</main>
{footer()}
</body></html>
"""


def footer() -> str:
    vs = "".join(f'<li><a href="{e(v["url"])}/">{e(v["name"])}</a></li>' for v in VENTURES)
    return f"""<footer><div class="wrap"><div class="fgrid">
<div><h4>This site</h4><ul>
<li><a href="/">Laboratories</a></li>
<li><a href="/courage-garikai/">Courage Garikai</a></li>
<li><a href="/publications/">Publications</a></li>
<li><a href="/about/">About and disclosure</a></li>
</ul></div>
<div><h4>Ventures</h4><ul>{vs}</ul></div>
<div><h4>Contact</h4><ul>
<li><a href="mailto:{CONTACT}">{CONTACT}</a></li>
<li>{LOCATION}</li>
<li><a href="/publications/">Catalogue of {len(WORKS)} works</a></li>
</ul></div>
</div>
<p class="small">{e(DISCLOSURE)}</p>
<p class="small" style="border:0;padding:0;margin-top:8px">© {dt.date.today().year} Courage Garikai · {e(PUBLISHER)}.
{e(AVAILABILITY)}</p></div></footer>"""


# --------------------------------------------------------------------------- fragments
def work_url(w: dict) -> str:
    return f"/publications/{w['id']}/"


def open_licence(w: dict) -> bool:
    lic = (w.get("licence") or "").lower()
    return "cc " in lic or lic.startswith("cc") or "creative commons" in lic


AVAIL_TAG = {
    "available": ('<span class="tag gold">Read or download</span>'),
    "published": ('<span class="tag gold">Published edition</span>'),
    "catalogued": ('<span class="tag dim">Catalogued</span>'),
    "private": ('<span class="tag">Author review</span>'),
}


def tags_for(w: dict) -> str:
    out = [f'<span class="tag dim">{e(w["kind"])}</span>', AVAIL_TAG[w.get("availability", "private")]]
    if w.get("series") and len(w["series"]) <= 34:
        out.append(f'<span class="tag dim">{e(w["series"])}</span>')
    return "".join(out)


def work_row(w: dict) -> str:
    facts = " · ".join(w.get("facts") or [])
    return f"""<li><div class="row"><div>
<h3><a href="{work_url(w)}">{e(w["title"])}</a></h3>
<p class="sub">{e(w["subtitle"])}</p>
<div>{tags_for(w)}</div>
<p class="meta-row"><span>{e(facts)}</span></p>
</div></div></li>"""


def work_card(w: dict) -> str:
    return f"""<a class="card" href="{work_url(w)}">
<span class="no">{e(w["kind"])}</span>
<h3>{e(w["title"])}</h3>
<p>{e(w["subtitle"])}</p>
{f'<div>{tags_for(w)}</div>' if False else ''}
<span class="go">Read about it →</span></a>"""


def venture_card(v: dict, i: int) -> str:
    studied = [BY_ID[s]["title"] for s in v.get("research", []) if s in BY_ID]
    study = f'<p class="meta">Studied in {e(wordlist(studied))}</p>' if studied else ""
    return f"""<article class="card">
<span class="no">{i:02d}</span>
<h3><a href="{e(v["url"])}/">{e(v["name"])}</a></h3>
<p style="color:var(--ink);font-weight:600;margin:.1rem 0 .3rem">{e(v["line"])}</p>
<p>{e(v["what"])}</p>
<p class="meta">For {e(v["for"]).lower()}</p>{study}
<a class="go" href="{e(v["url"])}/">Open {e(v["name"])} →</a></article>"""


# --------------------------------------------------------------------------- pages
def build_labs() -> dict[str, str]:
    books = [BY_ID[i] for i in GROUPS[0][3]]
    papers = [BY_ID[i] for i in GROUPS[1][3]]
    doors = f"""<section style="border-top:0;padding-top:8px"><div class="doors">
<a class="door" href="/publications/"><span class="n">01 · The work</span><h3>Publications</h3>
<p>{len(WORKS)} works: {len(books)} books, {len(papers)} working papers and reports, and the published editions behind them.</p>
<span class="go">Browse the catalogue →</span></a>
<a class="door" href="/courage-garikai/"><span class="n">02 · The person</span><h3>Courage Garikai</h3>
<p>The operator and writer behind the lab: fifteen years of techno-preneurship, including the published failures.</p>
<span class="go">Read the portfolio →</span></a>
<a class="door" href="/about/"><span class="n">03 · The rules</span><h3>How this is run</h3>
<p>One owner, six ventures, agents that do the work — and the disclosure that follows from all three.</p>
<span class="go">About and disclosure →</span></a>
</div></section>"""

    hero = f"""<section class="hero"><div class="wrap" style="position:relative">
<svg class="wm" viewBox="-48 -48 96 96" aria-hidden="true"><g fill="currentColor">
{''.join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>' for a in (0,72,144,216,288))}
</g></svg>
{MARK}<p class="kicker">{LOCATION} · since 2026</p>
<h1>Six businesses,<br>one operator,<br>and a written record of both.</h1>
<p class="lede">Jacaranda Labs builds small, constraint-native software ventures and funds the research
that studies them — including the ones that did not work. This site is the lab, the person and the
publications in one place.</p>
</div></section>"""

    ventures = f"""<section id="ventures"><div class="wrap">
<div class="sec-head"><div><p class="kicker">The ventures</p><h2>What the lab runs</h2>
<p class="lede" style="font-size:1.02rem;margin-top:.5rem">Each is its own GitHub account, its own Cloudflare
account and its own Whop business. A key that leaks or a quota that runs out takes down one venture, not the set.</p>
</div><a class="btn ghost" href="/about/">How they are built</a></div>
<div class="grid">{''.join(venture_card(v, i+1) for i, v in enumerate(VENTURES))}</div>
</div></section>"""

    research = f"""<section id="research"><div class="wrap">
<div class="sec-head"><div><p class="kicker">The research</p><h2>Every venture is also a case study</h2>
<p class="lede" style="font-size:1.02rem;margin-top:.5rem">The think tank funds books and working papers that
study these ventures at close range: the audit logs, the commit history, the usage meters. The same owner
commissions both, and each work says so.</p></div>
<a class="btn ghost" href="/publications/">All {len(WORKS)} works</a></div>
<div class="grid">{''.join(work_card(w) for w in (books + papers)[:6])}</div>
</div></section>"""

    body = hero + doors + ventures + research
    desc = ("Jacaranda Labs: six constraint-native software ventures built by one operator and a set of agents, "
            "and the publications that study them.")
    return {"/": page("labs", "/", f"{LAB_NAME} · ventures, portfolio and publications", desc, body, "labs")}


def build_portfolio() -> dict[str, str]:
    edu = "".join(f"<li>{e(x)}</li>" for x in AUTHOR["education"])
    published = [BY_ID[i] for i in GROUPS[2][3]]
    n_avail = sum(1 for w in WORKS if w.get("availability") == "available")
    books = [BY_ID[i] for i in GROUPS[0][3]]
    papers = [BY_ID[i] for i in GROUPS[1][3]]
    hero = f"""<section class="hero tight"><div class="wrap" style="position:relative">
<svg class="wm" viewBox="-48 -48 96 96" aria-hidden="true"><g fill="currentColor">
{''.join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>' for a in (0,72,144,216,288))}
</g></svg>
<p class="kicker">Portfolio</p>
<h1>Courage Garikai</h1>
<p class="lede">{e(AUTHOR["role"])}. {e(AUTHOR["based"])}</p>
<p class="meta-row" style="font-size:.93rem;color:var(--mute)"><span>{len(VENTURES)} ventures</span>
<span>{len(WORKS)} publications</span><span>{e(LOCATION)}</span></p>
</div></section>"""

    about = f"""<section style="border-top:0;padding-top:38px"><div class="wrap"><div class="cols">
<div><p class="kicker">Practice</p><h2>What I do</h2>
<p>I build software businesses with a small number of AI agents doing the execution, then write down what
happened — including the failures, the audit findings and the numbers that did not move.</p>
<p>{e(AUTHOR["practice"])} The work is deliberately constraint-native: free tiers, quotas, one owner, no
capital. The constraint is the design material, not the excuse.</p>
<h4 style="margin-top:1.6rem">Education</h4><ul style="color:var(--mute)">{edu}</ul></div>
<div><div class="note"><p class="kicker">At a glance</p>
<dl class="facts" style="margin:0"><dt>Based</dt><dd>{e(LOCATION)} (CAT, UTC+2)</dd>
<dt>Ventures</dt><dd>{len(VENTURES)} live</dd><dt>Works</dt><dd>{len(WORKS)} catalogued, {len(published)} published</dd>
<dt>Publisher</dt><dd>{e(PUBLISHER)}</dd><dt>Contact</dt><dd><a href="mailto:{CONTACT}">{CONTACT}</a></dd></dl>
</div></div></div></div></section>"""

    ventures = f"""<section id="ventures"><div class="wrap">
<div class="sec-head"><div><p class="kicker">Ventures</p><h2>What I run</h2></div>
<a class="btn ghost" href="/">Laboratories →</a></div>
<div class="grid">{''.join(venture_card(v, i+1) for i, v in enumerate(VENTURES))}</div></div></section>"""

    pubs = f"""<section id="publications"><div class="wrap">
<div class="sec-head"><div><p class="kicker">Publications</p><h2>What I have written</h2>
<p class="lede" style="font-size:1.02rem;margin-top:.5rem">Four books and four working papers in author
review, {n_avail} editions anyone can read or download today, and the rest listed for the record.</p></div>
<a class="btn ghost" href="/publications/">Full catalogue →</a></div>
<ul class="list">{''.join(work_row(w) for w in (books + papers))}</ul></div></section>"""

    body = hero + about + ventures + pubs
    desc = (f"{AUTHOR['name']} — {AUTHOR['role']}. {len(VENTURES)} ventures and {len(WORKS)} publications from "
            f"Jacaranda Labs, Harare.")
    return {"/courage-garikai/": page("portfolio", "/courage-garikai/", f"{AUTHOR['name']} · portfolio",
                                      desc, body, "portfolio")}


def build_publications() -> dict[str, str]:
    out = {}
    counts = len(WORKS)
    n_avail = sum(1 for w in WORKS if w.get("availability") == "available")
    hero = f"""<section class="hero tight"><div class="wrap" style="position:relative">
<svg class="wm" viewBox="-48 -48 96 96" aria-hidden="true"><g fill="currentColor">
{''.join(f'<ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate({a})"/>' for a in (0,72,144,216,288))}
</g></svg>
<p class="kicker">Publications · {e(PUBLISHER)}</p>
<h1>{counts} works,<br>and what is actually<br>available.</h1>
<p class="lede">Books, working papers and essays, funded by the Jacaranda Labs AI Think Tank.
{n_avail} editions are published and downloadable below. The rest are catalogued, not distributed: private
author-review copies, sent to editors and reviewers on request.</p>
</div></section>"""

    blocks = []
    for key, title, blurb, ids in GROUPS:
        items = [BY_ID[i] for i in ids if i in BY_ID]
        if not items:
            continue
        blocks.append(f"""<section id="{key}"><div class="wrap">
<div class="sec-head"><div><p class="kicker">{len(items)} works</p><h2>{e(title)}</h2>
<p class="lede" style="font-size:1.02rem;margin-top:.5rem">{e(blurb)}</p></div></div>
<ul class="list">{''.join(work_row(w) for w in items)}</ul></div></section>""")

    body = hero + "".join(blocks)
    desc = (f"The catalogue: {counts} books, working papers and essays from Jacaranda Labs Press, with "
            f"availability stated for every one.")
    out["/publications/"] = page("publications", "/publications/", "Publications · the catalogue",
                                 desc, body, "publications")
    return out


def related(w: dict) -> str:
    """Three neighbours from the same group, or from anywhere in the catalogue."""
    group = [i for i in next(g[3] for g in GROUPS if w["id"] in g[3]) if i != w["id"]]
    picks = [BY_ID[i] for i in group[:3]] or [x for x in WORKS if x["id"] != w["id"]][:3]
    cards = "".join(work_card(x) for x in picks)
    return f"""<section style="border-top:1px solid var(--line);background:#faf8fc"><div class="wrap">
<p class="kicker">Also in the catalogue</p><div class="grid">{cards}</div></div></section>"""


def build_work(w: dict) -> str:
    section = SECTION_OF.get(w["id"], "publications")
    facts = "".join(f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in [
        ("Kind", w["kind"].capitalize()),
        ("Series", w.get("series")),
        ("Edition", w.get("edition")),
        ("Funded by", w.get("funded_by")),
        ("Licence", w.get("licence") if open_licence(w) else None),
    ] if v)
    for i, fact in enumerate(w.get("facts") or []):
        if fact:
            label = "Length" if i == 0 else ("Structure" if i == 1 else "Format")
            facts += f"<dt>{label}</dt><dd>{e(fact)}</dd>"

    state = w.get("availability", "private")
    if state == "available":
        links = "".join(
            f'<a class="btn{" ghost" if i else ""}" href="{e(u)}">{e(k)}</a>'
            for i, (k, u) in enumerate(w["formats"].items()))
        avail = (f'<div class="note gold"><p><strong>Available now.</strong> Read or download this edition'
                 f'{f", published under {e(w['licence'])}" if open_licence(w) else ""}:</p>'
                 f'<div>{links}</div></div>')
    elif state == "published":
        avail = ('<div class="note gold"><p><strong>Published edition.</strong> A public edition of this work '
                 'exists. It is not hosted on this site — email and I will send the file or the link.</p></div>')
    elif state == "catalogued":
        avail = ('<div class="note plain"><p><strong>Listed for the record.</strong> No copy is distributed '
                 'from this site and none is hosted here. Ask if you need to consult it.</p></div>')
    else:
        subject = f"Review copy request: {w['title']}".replace(" ", "%20").replace(":", "%3A")
        avail = (f'<div class="note"><p><strong>Not available to download.</strong> This is a private '
                 f'author-review edition: catalogued here, not distributed. Editors, reviewers and '
                 f'researchers can <a href="mailto:{CONTACT}?subject={subject}">request a review copy</a>.</p></div>')

    if w.get("merged_note"):
        avail += f'<p class="meta">{e(w["merged_note"])}</p>'

    disclosure = ""
    if w.get("case_disclosure"):
        disclosure = f'<h4 style="margin-top:1.6rem">Case disclosure</h4><p class="meta">{e(w["case_disclosure"])}</p>'

    toc = ""
    if w.get("toc"):
        toc = ('<div style="margin-top:2.2rem"><p class="kicker">Contents</p><ol class="toc">'
               + "".join(f"<li>{e(t)}</li>" for t in w["toc"]) + "</ol></div>")

    body = f"""<section class="wrap" style="border-top:0;padding-top:44px">
<p class="meta" style="margin-bottom:1.4rem"><a href="/publications/">Publications</a> › {e(w["kind"].capitalize())}</p>
<div class="work-head">
<div class="plate">{MARK}</div>
<div><p class="kicker">{e(w["kind"].capitalize())}</p>
<h1 style="font-size:clamp(1.9rem,3.8vw,2.9rem)">{e(w["title"])}</h1>
<p class="lede" style="font-size:1.12rem">{e(w["subtitle"])}</p>
<div style="margin-top:.6rem">{tags_for(w)}</div></div>
</div></section>
<section style="border-top:1px solid var(--line)"><div class="wrap"><div class="cols">
<div><p class="kicker">About this work</p>
<p style="font-size:1.06rem">{inline(w["blurb"])}</p>
{disclosure}{toc}</div>
<aside><dl class="facts">{facts}</dl>{avail}
<p class="meta"><a href="/publications/">← All publications</a></p></aside>
</div></div></section>
{related(w)}"""
    desc = (w.get("blurb") or w["subtitle"])[:180]
    return page(section, work_url(w), w["title"], desc, body, "publications")


def build_about() -> str:
    doors = "".join(f'<li>{e(x)}</li>' for x in [
        "Each venture has its own GitHub account, Cloudflare account and Whop business.",
        "Free tiers are treated as a design material: quotas are budgeted before features are written.",
        "Work is checked by mechanism audits — does the thing do what the page says it does.",
        "Failures are published with the same care as successes, and named as failures.",
    ])
    body = f"""<section class="hero tight"><div class="wrap">
<p class="kicker">About</p><h1>What this is,<br>and what it is not.</h1>
<p class="lede">Jacaranda Labs builds software ventures and funds the research that studies them. One owner,
a small number of AI agents doing the execution, and a written record of what happened.</p></div></section>
<section style="border-top:0"><div class="wrap"><div class="cols">
<div><h2>The lab</h2>
<p>Six ventures run from Harare: AttestOS, TightBucket, DeskOS, STPi, Tapstall and Open Practice. Each one is
small, self-hosted on free or near-free infrastructure, and sold directly rather than through an app store.</p>
<p>The {TANK_NAME} funds the books and working papers in the catalogue. It is a funding relationship, not a
publisher's peer review: no work here has been independently refereed.</p>
<h4 style="margin-top:1.8rem">How the ventures are built</h4><ul style="color:var(--mute)">{doors}</ul>
<h4 style="margin-top:1.8rem">The disclosure, in one paragraph</h4>
<p class="meta">{e(DISCLOSURE)}</p></div>
<aside><div class="note"><p class="kicker">At a glance</p>
<dl class="facts" style="margin:0"><dt>Ventures</dt><dd>{len(VENTURES)} live</dd>
<dt>Publications</dt><dd>{len(WORKS)} catalogued</dd><dt>Owner</dt><dd>{e(AUTHOR["name"])}</dd>
<dt>Based</dt><dd>{e(LOCATION)}</dd><dt>Press</dt><dd>{e(PUBLISHER)}</dd>
<dt>Contact</dt><dd><a href="mailto:{CONTACT}">{CONTACT}</a></dd></dl></div>
<div class="note plain"><p><strong>What is not claimed.</strong> No independent validation, no customer
outcomes, no certification. Works that study a venture say so in their own disclosure.</p></div></aside>
</div></div></section>"""
    desc = ("How Jacaranda Labs runs six ventures and funds the publications that study them, with the "
            "disclosure that follows from a single owner.")
    return page("labs", "/about/", "About and disclosure", desc, body, "labs")


def build_404() -> str:
    body = """<section class="hero tight"><div class="wrap"><p class="kicker">404</p>
<h1>That page is not here.</h1><p class="lede">It may have moved when the three catalogues were merged into one site.</p>
<p><a class="btn" href="/">Laboratories</a><a class="btn ghost" href="/publications/">Publications</a>
<a class="btn ghost" href="/courage-garikai/">Portfolio</a></p></div></section>"""
    return page("labs", "/404.html", "Page not found", "That page is not here.", body)


# --------------------------------------------------------------------------- extras
def llms_txt() -> str:
    lines = [f"# {LAB_NAME}", "",
             f"> Six software ventures built by one operator and a set of agents, and the publications that "
             f"study them. {LOCATION}.", "",
             "## Sections", "",
             f"- [Laboratories]({SITE}/): the six ventures and how they are built",
             f"- [Portfolio]({SITE}/courage-garikai/): {AUTHOR['name']}, {AUTHOR['role']}",
             f"- [Publications]({SITE}/publications/): {len(WORKS)} works with availability stated",
             f"- [About]({SITE}/about/): ownership and disclosure", "",
             "## Ventures", ""]
    for v in VENTURES:
        lines.append(f"- [{v['name']}]({v['url']}/): {v['line']} {v['what']}")
    lines += ["", "## Publications", ""]
    for key, title, _, ids in GROUPS:
        lines.append(f"### {title}")
        for i in ids:
            w = BY_ID[i]
            state = {"available": "published edition, free to read",
                     "published": "public edition, link on request",
                     "catalogued": "listed for the record, no copy distributed",
                     "private": "private author-review, request a copy"}[w.get("availability", "private")]
            lines.append(f"- [{w['title']}]({SITE}{work_url(w)}): {w['subtitle']} ({state})")
        lines.append("")
    lines += ["## Notes", "", f"- Contact: {CONTACT}", f"- {DISCLOSURE}"]
    return "\n".join(lines) + "\n"


def sitemap(paths) -> str:
    today = dt.date.today().isoformat()
    urls = "".join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>' for p in sorted(paths))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


# --------------------------------------------------------------------------- build
def write(rel: str, text: str) -> str:
    path = DIST / rel.lstrip("/")
    if rel.endswith("/"):
        path = path / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return rel


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="build, then assert the invariants")
    ap.add_argument("--serve", action="store_true", help="build, then serve on :8080")
    args = ap.parse_args(argv)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    pages: dict[str, str] = {}
    pages.update(build_labs())
    pages.update(build_portfolio())
    pages.update(build_publications())
    for w in WORKS:
        pages[work_url(w)] = build_work(w)
    pages["/about/"] = build_about()
    pages["/404.html"] = build_404()

    for path, html_text in pages.items():
        write(path, html_text)
    write("/favicon.svg", FAVICON)
    for asset in sorted((ROOT / "assets").glob("*")) if (ROOT / "assets").is_dir() else []:
        (DIST / asset.name).write_bytes(asset.read_bytes())
    write("/_headers", HEADERS)
    write("/robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    write("/sitemap.xml", sitemap([p for p in pages if p != "/404.html"]))
    write("/llms.txt", llms_txt())
    # the only file a stray request should ever find
    write("/.nojekyll", "")

    ok = True
    if args.check:
        ok = run_checks(pages)
    print(f"built {len(pages)} pages → dist/  ({sum(len(p) for p in pages.values())//1024} KB of HTML)")
    if args.serve:
        serve()
    return 0 if ok else 1


def run_checks(pages: dict[str, str]) -> bool:
    problems = []
    for path, text in pages.items():
        if "<script" in text:
            problems.append(f"{path}: contains a script tag (CSP is default-src 'none')")
        if 'href="/' not in text and path != "/404.html":
            problems.append(f"{path}: no internal links")
        for m in re.finditer(r'href="(/[^"#]*)"', text):
            target = m.group(1)
            if target in ("/favicon.svg", "/og.png", "/sitemap.xml", "/robots.txt", "/llms.txt"):
                continue
            if target not in pages and not (DIST / target.lstrip("/")).exists():
                problems.append(f"{path}: dead internal link {target}")
    # every work must be reachable and say what is available
    for w in WORKS:
        p = work_url(w)
        if p not in pages:
            problems.append(f"missing page for {w['id']}")
        elif not re.search(r"request a review copy|Available now\.|Listed for the record\.|Published edition\.", pages[p]):
            problems.append(f"{p}: does not state availability")
        elif "script" in pages[p].lower().replace("description", ""):
            pass
    for path, text in pages.items():
        if text.count("<h1") != 1:
            problems.append(f"{path}: expected exactly one h1, found {text.count('<h1')}")
    for p in problems:
        print("  ✗", p, file=sys.stderr)
    print(f"  {'✓' if not problems else '✗'} {len(pages)} pages checked, {len(problems)} problems")
    return not problems


def serve():  # pragma: no cover - convenience only
    import http.server, functools
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    print("serving dist/ on http://127.0.0.1:8080")
    http.server.ThreadingHTTPServer(("0.0.0.0", 8080), handler).serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
