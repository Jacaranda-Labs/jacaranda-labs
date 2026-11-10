#!/usr/bin/env python3
"""Covers for the catalogue, drawn to the house style: cream stock, black rules, a red stamp.

The existing covers were handmade; this draws the same shape so a new title does not arrive looking
like a different publisher. 480x720, which is what the site asks for and what a shop thumbnail wants.

    python3 tools/make_covers.py            # every cover described below
    python3 tools/make_covers.py --list
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "covers"

CREAM = (245, 241, 232)
INK = (26, 24, 22)
RED = (168, 38, 30)
MUTE = (92, 88, 82)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

W, H = 480, 720

COVERS = [
    dict(file="the-mechanism-auditor.jpg",
         imprint="JACARANDA LABS PRESS",
         place="HARARE · 2026",
         title="The Mechanism\nAuditor",
         subtitle="How to review a product\nthat runs without you",
         author="COURAGE GARIKAI",
         footer="JACARANDA LABS · FIRST EDITION",
         stamp=["NO DETECTOR", "NO CLAIM"]),
    dict(file="mechanism-audit.jpg",
         imprint="JACARANDA LABS THINK TANK",
         place="WORKING PAPER 2026-04",
         title="The Mechanism\nAudit",
         subtitle="Evidence-first review for\nproducts that act alone",
         author="COURAGE GARIKAI",
         footer="JACARANDA LABS · HARARE",
         stamp=["SIX", "SIGNATURES"]),
    dict(file="operatorship.jpg",
         imprint="JACARANDA LABS PRESS",
         place="HARARE · 2026",
         title="Operatorship",
         subtitle="What ate technopreneurship,\nand what replaced it",
         author="COURAGE GARIKAI",
         footer="JACARANDA LABS · FIRST EDITION",
         stamp=["ONE NAME", "ONE SENTENCE"]),
    dict(file="the-point-of-failure.jpg",
         imprint="THE OPERATOR'S BOOKS",
         place="HARARE · 2026",
         title="The Point\nof Failure",
         subtitle="An operating manual for the\nperson running the estate",
         author="COURAGE GARIKAI",
         footer="JACARANDA LABS · FIRST EDITION",
         stamp=["NINE RULES", "NO REPLICA"]),
]


def paper(w: int, h: int) -> Image.Image:
    """Cream stock with a faint horizontal fibre, so a flat fill does not look like a flat fill."""
    im = Image.new("RGB", (w, h), CREAM)
    d = ImageDraw.Draw(im)
    for y in range(0, h, 3):
        shade = 244 if (y // 3) % 2 else 246
        d.line([(0, y), (w, y)], fill=(shade, shade - 4, shade - 13))
    grain = Image.effect_noise((w, h), 12).convert("L").filter(ImageFilter.GaussianBlur(0.6))
    im = Image.composite(Image.new("RGB", (w, h), (238, 233, 222)), im, grain.point(lambda v: v // 3))
    return im


def wrap(draw, text: str, font, width: int) -> list[str]:
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        for word in words:
            trial = (line + " " + word).strip()
            if draw.textlength(trial, font=font) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def fit(draw, text: str, path: str, start: int, floor: int, width: int, max_lines: int):
    size = start
    while size > floor:
        f = ImageFont.truetype(path, size)
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines:
            return f, lines
        size -= 2
    f = ImageFont.truetype(path, floor)
    return f, wrap(draw, text, f, width)[:max_lines]


def circles(d: ImageDraw.ImageDraw, x: int, y: int, count: int, r: int, gap: int):
    for i in range(count):
        cx = x + i * (r * 2 + gap)
        d.ellipse([cx, y, cx + r * 2, y + r * 2], fill=INK)


def stamp(im: Image.Image, lines: list[str]) -> Image.Image:
    """A red rubber stamp, rotated, half over the rules — the mark the press uses instead of a badge."""
    size = 150
    lay = Image.new("RGBA", (size * 2, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([10, 10, size * 2 - 10, size - 10], outline=RED + (235,), width=4)
    d.ellipse([22, 22, size * 2 - 22, size - 22], outline=RED + (170,), width=1)
    f = ImageFont.truetype(SANSB, 22)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=f)
        d.text(((size * 2 - tw) / 2, size / 2 - 24 + i * 26), line, font=f, fill=RED + (240,))
    lay = lay.rotate(12, expand=True, resample=Image.BICUBIC)
    im.paste(lay, (W - lay.width + 10, H - lay.height - 130), lay)
    return im


def draw(spec: dict) -> Path:
    im = paper(W, H)
    d = ImageDraw.Draw(im)
    pad = 34

    # imprint
    f = ImageFont.truetype(SANSB, 11)
    d.text((pad, 26), spec["imprint"], font=f, fill=INK)
    d.text((pad, 44), spec["place"], font=ImageFont.truetype(SANS, 10), fill=MUTE)

    # the row of discs
    circles(d, pad + 4, 66, 7, 15, 8)

    # title
    y = 168
    f_t, lines = fit(d, spec["title"], SERIF_B, 46, 26, W - pad * 2, 4)
    for line in lines:
        d.text((pad, y), line, font=f_t, fill=INK)
        y += int(f_t.size * 1.12)

    # subtitle
    y += 16
    f_s, sub = fit(d, spec["subtitle"], SERIF, 17, 12, W - pad * 2 - 20, 4)
    for line in sub:
        d.text((pad, y), line, font=f_s, fill=(58, 54, 50))
        y += int(f_s.size * 1.35)

    # author + rule
    y += 26
    d.text((pad, y), spec["author"], font=ImageFont.truetype(SANSB, 12), fill=INK)
    d.line([(pad, y + 26), (W - pad, y + 26)], fill=INK, width=1)
    d.text((pad, y + 34), spec["footer"], font=ImageFont.truetype(SANS, 9), fill=MUTE)

    # the band: heavy rules and a second set of discs, bottom third
    top = H - 232
    d.rectangle([0, top, W, top + 8], fill=INK)
    for i in range(5):
        d.rectangle([0, top + 22 + i * 26, W, top + 22 + i * 26 + 12], fill=INK)
    d.rectangle([0, top + 22 + 5 * 26 + 12, W, top + 22 + 5 * 26 + 20], fill=INK)
    circles(d, pad, top + 22 + 5, 7, 12, 10)

    im = stamp(im, spec["stamp"])
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / spec["file"]
    im.convert("RGB").save(path, quality=88, optimize=True)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    for spec in COVERS:
        p = draw(spec)
        print(f"  {p.name:<30}{p.stat().st_size // 1024} KB")
        if a.list:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
