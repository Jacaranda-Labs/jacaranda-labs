#!/usr/bin/env python3
"""Turn a manuscript in data/editions/*.md into a readable edition in the house style.

The existing read editions were built by a tool that is not in this repository, so rather than
re-invent the typography this borrows the exact <head> — every style block, print rules included — from
an edition that already ships, and swaps the title and running head. The result is indistinguishable
from the rest of the catalogue, which is the point: a reader should not be able to tell which
publications were typeset by which process.

Markdown supported: h1/h2/h3, paragraphs, **bold**, *italic*, `code`, - and 1. lists, > quotes,
pipe tables, --- rules, and fenced code. That is everything the manuscripts use.

    python3 tools/make_edition.py data/editions/mechanism-audit.md
    python3 tools/make_edition.py --all
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "editions"
OUT = ROOT / "assets" / "read"
TEMPLATE = OUT / "grounded-cadence.html"


def head(title: str, series: str) -> str:
    """The <head> of a shipped edition, with the title and running head swapped."""
    text = TEMPLATE.read_text()
    end = text.index("</head>") + len("</head>")
    head_html = text[:end]
    head_html = re.sub(r"<title>.*?</title>", f"<title>{html.escape(title)}</title>", head_html,
                       flags=re.S)
    head_html = re.sub(r'(header\.mast \.series \{ string-set: runhead content\(\); \})', r"\1",
                       head_html)
    return head_html


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def convert(md: str) -> str:
    out: list[str] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # fenced code
        if line.startswith("```"):
            body = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(html.escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre>" + "\n".join(body) + "</pre>")
            continue
        if re.match(r"^(-{3,}|\*{3,})$", line.strip()):
            # no rule immediately before a heading: the heading already carries one
            nxt = next((x for x in lines[i + 1:] if x.strip()), "")
            if not re.match(r"^#{1,3}\s", nxt):
                out.append("<hr>")
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 1:
                out.append(f'<h1 id="{slug(title)}">{inline(title)}</h1>')
            elif level == 2:
                out.append(f"<h2>{inline(title)}</h2>")
            else:
                out.append(f"<h3>{inline(title)}</h3>")
            i += 1
            continue
        if line.strip().startswith("<div"):
            block = [line]
            i += 1
            while i < len(lines) and "</div>" not in lines[i]:
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
                i += 1
            inner = "\n".join(block[1:-1])
            out.append('<div class="card-sheet">' + "".join(
                "<p>" + inline(x.strip()) + "</p>" for x in inner.split("\n\n") if x.strip()) + "</div>")
            continue
        # table
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header)
                       + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                                 for r in rows)
                       + "</tbody></table>")
            continue
        # figure: ![alt](/read/fig/x.svg)  then  *Figure n — caption*
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", line.strip())
        if m:
            alt, src = m.group(1), m.group(2)
            i += 1
            caption = ""
            if i < len(lines) and re.match(r"^\*[^*].*\*$", lines[i].strip()):
                caption = inline(lines[i].strip()[1:-1])
                i += 1
            num = re.match(r"^Figure\s+(\S+)", caption)
            cap = (f'<figcaption><b>{"Figure " + num.group(1) if num else "Figure"}</b>'
                   f'{html.escape(caption[num.end():].lstrip(" —-")) if num else html.escape(caption)}</figcaption>'
                   if caption else "")
            # A figure is inlined rather than linked. Three reasons, all of them practical: the edition
            # then renders in a sandboxed frame with no network, it survives being copied as a single
            # file, and Chromium's PDF printer draws inline SVG as vectors where an <img src="*.svg">
            # comes out blank. The source of truth stays assets/read/fig/*.svg.
            # /read/fig/x.svg is addressed from the site root, so it lives under assets/read/fig/x.svg
            local = ((ROOT / "assets" / src.lstrip("/")) if src.startswith("/")
                     else (Path(__file__).resolve().parent.parent / "data" / "editions" / src))
            if local.is_file() and local.suffix == ".svg":
                mark = local.read_text(encoding="utf-8")
                mark = re.sub(r'<\?xml[^>]*\?>', "", mark)
                mark = re.sub(r'(<svg[^>]*?)\s(?:width|height)="[^"]*"', r"\1", mark, count=1)
                mark = mark.replace("<svg ", '<svg role="img" aria-label="' + html.escape(alt) + '" ', 1)
                mark = re.sub(r"(<svg[^>]*?)>", r'\1 class="fig-svg">', mark, count=1)
                out.append(f"<figure>{mark}{cap}</figure>")
            else:
                out.append(f'<figure><img src="{html.escape(src)}" alt="{html.escape(alt)}" '
                           f'loading="lazy" decoding="async">{cap}</figure>')
            continue
        # blockquote
        if line.startswith(">"):
            body = []
            while i < len(lines) and lines[i].startswith(">"):
                body.append(inline(lines[i].lstrip("> ").rstrip()))
                i += 1
            out.append("<blockquote>" + " ".join(body) + "</blockquote>")
            continue
        # lists
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.\s+", line))
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(inline(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]).strip()))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
            continue
        # paragraph
        body = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3}\s|\||>|```|<div|!\[|\s*([-*]|\d+\.)\s)", lines[i]):
            body.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(body)) + "</p>")
    return "\n".join(out)


EXTRA_CSS = """
figure{margin:26px 0 30px;break-inside:avoid;page-break-inside:avoid}
figure svg.fig-svg{width:100%;height:auto;display:block;border:1px solid var(--rule);background:#fdfcf8}
figure img{width:100%;height:auto;border:1px solid var(--rule);background:#fdfcf8;display:block}
figcaption{font:12.5px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif;
  color:var(--muted);margin-top:9px;padding-left:2px;border-left:2px solid var(--accent);
  padding-left:11px}
figcaption b{color:var(--accent);font-weight:600;letter-spacing:.02em}
.card-sheet{border:2px solid var(--ink);border-radius:3px;padding:18px 20px;margin:22px 0 26px;
  background:#fff;font:13.5px/1.6 ui-sans-serif,system-ui,sans-serif;break-inside:avoid}
.card-sheet p{margin:0 0 9px}
.card-sheet p:first-child{font:600 11px/1.5 ui-sans-serif,system-ui,sans-serif;letter-spacing:.12em;
  text-transform:uppercase;color:var(--accent);border-bottom:1px solid var(--rule);padding-bottom:8px}
h1{page-break-after:avoid}
table{page-break-inside:auto}
tr{page-break-inside:avoid}
@media print{body{box-shadow:none;max-width:none}figure img{border:1px solid #ccc}
  a{color:inherit;text-decoration:none}}
@media (max-width:700px){figure img{width:100%}}
"""


def build(path: Path) -> Path:
    md = path.read_text()
    meta: dict[str, str] = {}
    if md.startswith("---"):
        end = md.index("\n---", 3)
        for line in md[3:end].strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body_md = md[end + 4:]
    else:
        body_md = md
    title = meta.get("title", path.stem)
    series = meta.get("series", title)
    byline = meta.get("byline", "Courage Garikai — Jacaranda Labs, Harare, Zimbabwe")
    programme = meta.get("programme", "Jacaranda Labs — Distributed Cognitive Autonomous Infrastructure")
    date = meta.get("date", "November 2026")
    body = convert(body_md)

    h = head(title, series)
    h = h.replace("</head>", "<style>" + EXTRA_CSS + "</style></head>")
    doc = (
        h
        + '<body><header class="mast">'
        + f'<div class="series">{html.escape(series)}</div>'
        + f'<h1>{html.escape(title)}</h1>'
        + f'<div class="byline"><b>{html.escape(byline)}</b> · {html.escape(programme)}</div>'
        + f'<div class="byline">{html.escape(date)}</div></header>'
        + body
        + f'<footer class="colophon">{html.escape(byline)} · {html.escape(programme)} · '
        + f'{html.escape(date)}. Published by Jacaranda Labs Press, Harare.</footer></body></html>'
    )
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / (meta.get("slug") or path.stem)
    target = target.with_suffix(".html")
    target.write_text(doc)
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    print(f"  {path.name:<34}→ {target.relative_to(ROOT)}  ({words:,} words)")
    # the markdown itself is a deliverable: keep it beside the edition, so it can be copied or diffed
    (OUT / (target.stem + ".md")).write_text(md)
    return target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    files = sorted(SRC.glob("*.md")) if a.all else [Path(f) for f in a.files]
    if not files:
        ap.print_help()
        return 2
    for f in files:
        build(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
