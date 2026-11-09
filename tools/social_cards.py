#!/usr/bin/env python3
"""Social cards for the lab's own posts: one real image per post, rendered here, for nothing.

The seven ventures each had a card engine and the lab itself had none, which is why its accounts were
empty — you cannot post daily if every post needs a picture somebody has to draw. This renders a card
per post in the press bank from the post's own words, so the image can never say something the post
does not.

Two shapes, because two rails want different ones:
  wide  1200x630   Bluesky link cards, Mastodon, OG
  pin   1000x1500  Pinterest (2:3), which is the one channel Buffer has connected for this account

    python3 tools/social_cards.py            # writes assets/cards/<id>.png and assets/cards/<id>-pin.png
    python3 tools/social_cards.py --list

Cards are served from https://jacaranda-labs.pages.dev/assets/cards/<id>.png because build.py copies
everything under assets/ into the site.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "assets" / "cards"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "rails" / "jacaranda"))

INK = (10, 7, 16)
VIOLET = (139, 92, 246)
ELECTRIC = (196, 160, 255)
MAGENTA = (232, 70, 124)
GOLD = (233, 184, 114)
MUTE = (168, 148, 196)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def gradient(w: int, h: int, top=(26, 16, 38), bottom=(9, 6, 14)) -> Image.Image:
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h), Image.BILINEAR).convert("RGBA")


def glow(size, centre, radius, colour, alpha=120) -> Image.Image:
    w, h = size
    s = 4
    small = Image.new("L", (w // s, h // s), 0)
    d = ImageDraw.Draw(small)
    cx, cy, r = centre[0] // s, centre[1] // s, radius // s
    for i in range(18, 0, -1):
        rr = r * i / 18
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=int(alpha * (1 - i / 18) ** 1.6))
    layer = Image.new("RGBA", (w, h), colour + (0,))
    layer.putalpha(small.filter(ImageFilter.GaussianBlur(max(2, r / 5))).resize((w, h), Image.BICUBIC))
    return layer


def mark(size: int) -> Image.Image:
    """The jacaranda mark: six petals, a gap, a gold centre. Same geometry as the site and the avatar."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = cy = s / 2
    pr, petal = s * .215, s * .195
    import math
    for i in range(6):
        a = -math.pi / 2 + i * 2 * math.pi / 6
        px, py = cx + math.cos(a) * pr, cy + math.sin(a) * pr
        d.ellipse([px - petal, py - petal, px + petal, py + petal], fill=(124, 82, 226, 255))
        d.ellipse([px - petal * .62, py - petal * .62, px + petal * .62, py + petal * .62],
                  fill=(160, 118, 250, 255))
    d.ellipse([cx - s * .128, cy - s * .128, cx + s * .128, cy + s * .128], fill=INK + (255,))
    d.ellipse([cx - s * .112, cy - s * .112, cx + s * .112, cy + s * .112], fill=GOLD + (255,))
    d.ellipse([cx - s * .055, cy - s * .055, cx + s * .055, cy + s * .055], fill=(255, 244, 222, 255))
    return im.resize((size, size), Image.LANCZOS)


def wrap(draw, text: str, font, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def fit(draw, text: str, kind: str, start: int, min_px: int, width: int, max_lines: int):
    size = start
    while size > min_px:
        f = ImageFont.truetype(kind, size)
        lines = wrap(draw, text, f, width)
        if len(lines) <= max_lines:
            return f, lines
        size -= 3
    f = ImageFont.truetype(kind, min_px)
    return f, wrap(draw, text, f, width)[:max_lines]


ART = ROOT / "assets" / "art" / "jacaranda-hero-v1.jpg"


def artwork(w: int, h: int, fraction: float) -> Image.Image:
    """The jacaranda photograph, cropped into the right of the card and faded out to the left.

    Same picture as the site hero, so a card in a timeline and the page it links to are visibly the
    same brand. If the photograph is missing the card still renders — ink and type only.
    """
    base = Image.new("RGB", (w, h), INK).convert("RGBA")
    if not ART.exists():
        return base
    aw = int(w * fraction)
    art = Image.open(ART).convert("RGB")
    scale = max(aw / art.width, h / art.height)
    art = art.resize((round(art.width * scale), round(art.height * scale)), Image.LANCZOS)
    left = int((art.width - aw) * .55)
    top = int((art.height - h) * .38)
    art = art.crop((left, top, left + aw, top + h)).convert("RGBA")
    canvas = Image.new("RGBA", (w, h), INK + (255,))
    canvas.paste(art, (w - aw, 0))
    fade = Image.linear_gradient("L").rotate(90, expand=True).resize((aw, h))
    mask = Image.new("L", (w, h), 0)
    mask.paste(fade.point(lambda v: min(255, int(v * 2.2))), (w - aw, 0))
    mask = mask.filter(ImageFilter.GaussianBlur(max(2, w // 220)))
    out = Image.composite(canvas, base, mask)
    # keep it quiet behind the type
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for x in range(w):
        t = x / w
        vd.line([(x, 0), (x, h)], fill=(10, 7, 16, int(200 * max(0.0, 1 - t * 1.15) + 26)))
    return Image.alpha_composite(out, veil)


def render(post: dict, shape: str) -> Image.Image:
    w, h = (1200, 630) if shape == "wide" else (1000, 1500)
    im = artwork(w, h, .62 if shape == "wide" else .78)
    im = Image.alpha_composite(im, glow((w, h), (int(w * .14), int(h * .88)), int(w * .38), VIOLET, 90))
    d = ImageDraw.Draw(im)

    pad = int(w * .075)
    m = mark(int(h * (0.075 if shape == "wide" else 0.05)))
    im.alpha_composite(m, (pad, pad))
    d = ImageDraw.Draw(im)

    brand_font = ImageFont.truetype(SANSB, int(h * (0.032 if shape == "wide" else 0.022)))
    d.text((pad + m.width + int(w * .018), pad + m.height // 2 - brand_font.size),
           "JACARANDA LABS", font=brand_font, fill=(255, 255, 255))
    sub = ImageFont.truetype(SANS, int(h * (0.024 if shape == "wide" else 0.017)))
    d.text((pad + m.width + int(w * .018), pad + m.height // 2 + int(h * .012)),
           post.get("kicker", "HARARE · SINCE 2026"), font=sub, fill=MUTE)

    y = int(h * (0.36 if shape == "wide" else 0.28))
    head_font, head_lines = fit(d, post["headline"], SERIF,
                                int(h * (0.095 if shape == "wide" else 0.062)),
                                int(h * 0.042), w - pad * 2, 4 if shape == "wide" else 6)
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle([pad - 18, y - 14, int(w * .82), y + len(head_lines) * head_font.size * 1.2 + 8],
                 fill=(8, 5, 12, 120))
    im = Image.alpha_composite(im, shade.filter(ImageFilter.GaussianBlur(18)))
    im = Image.alpha_composite(im, Image.new("RGBA", (w, h), (0, 0, 0, 0)))
    d = ImageDraw.Draw(im)
    for line in head_lines:
        d.text((pad, y), line, font=head_font, fill=(255, 255, 255))
        y += int(head_font.size * 1.12)
    d.rectangle([pad, y + int(h * .015), pad + 64, y + int(h * .015) + 3], fill=GOLD + (255,))

    if post.get("body"):
        y += int(h * .035)
        body_font, body_lines = fit(d, post["body"], SANS, int(h * (0.038 if shape == "wide" else 0.028)),
                                    int(h * 0.022), w - pad * 2, 3 if shape == "wide" else 6)
        for line in body_lines:
            d.text((pad, y), line, font=body_font, fill=(206, 196, 222))
            y += int(body_font.size * 1.35)

    foot = ImageFont.truetype(SANSB, int(h * (0.028 if shape == "wide" else 0.019)))
    label = post.get("footer", "jacaranda-labs.pages.dev")
    d.text((pad, h - pad - foot.size * 1.4), label, font=foot, fill=GOLD)
    d.line([(pad, h - pad - foot.size * 2.4), (w - pad, h - pad - foot.size * 2.4)],
           fill=(255, 255, 255, 26), width=1)
    return im.convert("RGB")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)

    try:
        import press as lab_press            # the same bank the rail publishes from
    except Exception as exc:
        print(f"cannot import the press bank: {exc}", file=sys.stderr)
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for post in lab_press.BANK:
        for shape, suffix in (("wide", ""), ("pin", "-pin")):
            im = render(post, shape)
            path = OUT / f"{post['id']}{suffix}.png"
            im.quantize(colors=200, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG) \
                .save(path, optimize=True)
            made.append((path, im.size))
            if a.list:
                print(f"  {path.name:<28}{im.width}x{im.height}  {path.stat().st_size // 1024} KB")
    print(f"  {len(made)} cards from {len(lab_press.BANK)} posts → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
