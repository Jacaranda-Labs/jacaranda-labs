#!/usr/bin/env python3
"""Print the readable editions to PDF, from the same HTML the site serves.

A PDF of a book is not a screenshot of a web page. This uses the edition's own print rules (the ones
borrowed from the shipped editions), adds a page size, running heads where the browser gives them to
us, and asks Chromium for backgrounds. The result is a document a reader can print, annotate, or send
to someone who does not read things in browsers.

    python3 tools/make_pdfs.py                       # every edition in assets/read
    python3 tools/make_pdfs.py operatorship          # one, by slug
    python3 tools/make_pdfs.py --all --serve         # include the pages that need a running origin

Requires playwright with chromium installed (`python3 -m playwright install chromium`).
"""
from __future__ import annotations

import argparse
import functools
import html
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "read"
OUT = ROOT / "assets" / "download"

PRINT_CSS = """
/* the shipped editions carry a paged-media page counter from their print sheet; Chromium now honours
   @page margin boxes, so it would print a second number beside ours */
@page { size: A5; margin: 16mm 15mm 18mm 15mm;
        @bottom-center { content: ""; } @top-center { content: ""; } }
@page :first { margin-top: 24mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { box-shadow: none !important; max-width: none !important; padding: 0 !important;
       background: #fff !important; font-size: 10.5pt; line-height: 1.5; }
header.mast { border-bottom: 1.5pt solid #14171a; margin-bottom: 8mm; }
header.mast h1 { font-size: 20pt; }
h1 { font-size: 15pt; margin: 10mm 0 3mm; break-before: page; break-after: avoid; }
h1:first-of-type, header.mast + h1 { break-before: auto; }
h2 { font-size: 12pt; break-after: avoid; }
h3 { font-size: 10.5pt; break-after: avoid; }
p, li { orphans: 2; widows: 2; }
figure { break-inside: avoid; margin: 6mm 0 7mm; }
figure img { border: 0.5pt solid #ccc; }
figcaption { font-size: 8pt; }
table { font-size: 8.5pt; break-inside: auto; table-layout: auto; hyphens: none; }
th, td { hyphens: none; word-break: normal; overflow-wrap: normal; }
th:first-child, td:first-child { min-width: 24mm; }
td:last-child { hyphens: none; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
blockquote { break-inside: avoid; }
.card-sheet { break-inside: avoid; }
footer.colophon { break-before: page; }
#index h1 { break-before: page; }
#index .ixt-note { font-size: 8.5pt; color: #5b6670; margin-bottom: 6mm; }
#index p.ix { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,52%);
             column-gap: 4mm; align-items: baseline; margin: 0 0 1.8mm; font-size: 9pt;
             border-bottom: 0.3pt dotted #ccc; padding-bottom: 0.8mm; break-inside: avoid; }
#index .ixt { overflow-wrap: normal; word-break: normal; }
#index .ixp { color: #5b6670; font-family: ui-sans-serif, system-ui, sans-serif; font-size: 8pt;
              text-align: right; line-height: 1.35; }
a { color: inherit; text-decoration: none; }
"""


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a):        # a build tool should not print an access log
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def serve_background() -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    """Serve assets/ on a local port.

    Not a convenience: Chromium will not paint an <img src="x.svg"> that came from file:// into a PDF —
    the figure box is laid out and left empty. Over http it draws. So the printer serves the edition
    and its figures from an origin the browser trusts.
    """
    handler = functools.partial(_Quiet, directory=str(SRC.parent))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, t, f"http://127.0.0.1:{httpd.server_address[1]}"


# What gets an index entry. Curated rather than extracted: a naive term-finder indexes "the" eleven
# hundred times, and an index is a judgement about what a reader will look for, not a concordance.
TERMS = {
    "the-point-of-failure": [
        ("bad day, the protocol", ["bad-day protocol"]),
        ("boundary, chosen not inherited", ["boundary"]),
        ("card, the operator's", ["operator's card"]),
        ("check, definition of", ["The check."]),
        ("clock, the three units", ["the clock"]),
        ("component, the operator as", ["single point of failure", "no replica"]),
        ("deleting as a repair", ["Deleting counts"]),
        ("dependency audit", ["dependency audit"]),
        ("degenerate form of a rule", ["smallest version"]),
        ("estate, definition of", ["estate"]),
        ("failover", ["failover"]),
        ("Friendship Bench", ["Friendship Bench"]),
        ("incident, three short nights", ["three consecutive nights", "incident"]),
        ("ledger and self", ["Ledger and self"]),
        ("loop, open", ["open loop"]),
        ("mechanism, naming the", ["Name the mechanism"]),
        ("non-negotiables, the nine", ["non-negotiables"]),
        ("one outcome", ["one outcome"]),
        ("pause switch", ["pause switch"]),
        ("shutdown, the five minutes", ["shutdown"]),
        ("signals, the five", ["signals"]),
        ("sleep", ["sleep"]),
        ("surface, unbounded", ["unbounded surface"]),
        ("worry window", ["worry window"]),
    ],
    "operatorship": [
        ("accountability", ["accountability"]),
        ("arbitrage, technopreneurship as", ["arbitrage"]),
        ("attention, as scarce input", ["attention"]),
        ("automation debt", ["automation debt"]),
        ("capability as a utility", ["capability"]),
        ("coordination, moat of", ["coordination"]),
        ("curriculum, the replacement", ["syllabus"]),
        ("distribution, moat of", ["distribution"]),
        ("estate, the unit", ["estate"]),
        ("evidence trail", ["evidence trail"]),
        ("exam, the defence", ["Show me something running"]),
        ("ghost authority", ["ghost authority"]),
        ("impostors, the five", ["impostors"]),
        ("judgement, the priced unit", ["judgement"]),
        ("kill list", ["killable", "kill list"]),
        ("novelty drift", ["novelty drift"]),
        ("operator, definition of", ["owning the consequences"]),
        ("pause switch", ["pause switch"]),
        ("proof of operation", ["Proof of operation"]),
        ("superintelligence, defined narrowly", ["metered utility"]),
        ("taste", ["taste"]),
        ("technopreneurship, retired", ["technopreneurship"]),
        ("waves, the three", ["three waves"]),
    ],
}


def build_index(pdf: Path, slug: str) -> list[tuple[str, list[int]]]:
    """Read the typeset pages back and return [(heading, [page numbers])], body pages only."""
    import pymupdf

    doc = pymupdf.open(pdf)
    pages = [doc[i].get_text().replace("\n", " ") for i in range(doc.page_count)]
    first_body = next((i for i, t in enumerate(pages) if "About this book" in t or "About the word" in t), 0)
    out = []
    for heading, needles in TERMS.get(slug, []):
        hits = sorted({i + 1 for i, t in enumerate(pages) if i >= first_body and
                       any(n.lower() in t.lower() for n in needles)})
        if hits:
            out.append((heading, hits))
    doc.close()
    return out


def index_html(entries: list[tuple[str, list[int]]], title: str) -> str:
    def refs(ps: list[int]) -> str:
        # a term on nearly every page is a term about the subject, not a place to look: say "passim"
        if len(ps) > 7:
            return f"{ps[0]}, {ps[1]}, {ps[2]} … passim"
        return ", ".join(str(p) for p in ps)

    rows = "".join(
        f'<p class="ix"><span class="ixt">{html.escape(name)}</span>'
        f'<span class="ixp">{refs(pages)}</span></p>'
        for name, pages in entries)
    return ('<section id="index"><h1>Index</h1>'
            '<p class="ixt-note">Page numbers are the printed pages of this edition, '
            'not the web edition\'s.</p>' + rows + '</section>')


def render(slug: str, width: int = 900, base: str | None = None, extra_html: str = "") -> Path:
    from playwright.sync_api import sync_playwright

    src = SRC / f"{slug}.html"
    if not src.exists():
        raise SystemExit(f"no edition at {src}")
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f"{slug}.pdf"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 1200})
        url = f"{base}/read/{slug}.html" if base else src.resolve().as_uri()
        page.goto(url, wait_until="load")
        page.add_style_tag(content=PRINT_CSS)
        # lazy images do not load in paged media; make them eager and wait for decode
        page.evaluate("""async () => {
            const imgs = [...document.images];
            imgs.forEach(i => { i.loading = 'eager'; });
            await Promise.all(imgs.map(i => i.decode().catch(() => {})));
        }""")
        if extra_html:
            page.evaluate("""(markup) => {
                document.body.insertAdjacentHTML('beforeend', markup);
            }""", extra_html)
            page.wait_for_timeout(400)
        page.wait_for_timeout(600)
        page.pdf(path=str(target), format="A5", print_background=True,
                 margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"},
                 display_header_footer=True,
                 header_template=('<div style="font:7pt ui-sans-serif,system-ui;width:100%;'
                                  'padding:0 15mm;color:#8a8f95;">'
                                  'Jacaranda Labs Press · Harare</div>'),
                 footer_template=('<div style="font:7pt ui-sans-serif,system-ui;width:100%;'
                                  'padding:0 15mm;color:#8a8f95;display:flex;'
                                  'justify-content:flex-end;">'
                                  '<span class="pageNumber"></span></div>'))
        browser.close()
    kb = target.stat().st_size // 1024
    print(f"  {slug:<26}{kb:>5} KB  → assets/download/{slug}.pdf")
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true", help="every edition in assets/read")
    a = ap.parse_args()
    slugs = a.slugs or (sorted(p.stem for p in SRC.glob("*.html")) if a.all else [])
    if not slugs:
        ap.print_help()
        return 2
    httpd, _thread, base = serve_background()
    try:
        for s in slugs:
            pdf = render(s, base=base)                    # pass 1: pages, without an index
            entries = build_index(pdf, s)
            if entries:
                render(s, base=base, extra_html=index_html(entries, s))   # pass 2: index appended
                print(f"    index: {len(entries)} entries")
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
