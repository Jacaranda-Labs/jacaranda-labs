#!/usr/bin/env python3
"""brand_assets — the avatar and profile banners for the Jacaranda accounts.

Drawn rather than generated, on purpose: a profile picture is read at 32 px, and a mark that has been
through an image model becomes mush at that size. Everything here is vector geometry rendered by PIL
at 4x and downsampled, from the same palette and the same artwork the site uses, so the account, the
site and the share card are the same brand rather than three approximations of it.

    python3 tools/brand_assets.py            # writes into ../brand/social/
    python3 tools/brand_assets.py --out DIR

Files
    avatar-1000.png         square; safe inside a circle (X, Bluesky, Mastodon, LinkedIn, GitHub)
    banner-1500x500.png     X / LinkedIn / Mastodon header
    banner-3000x1000.png    Bluesky banner (3:1, same design, larger canvas)
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ART = ROOT / "assets" / "art" / "hero-bloom.png"

INK = (10, 7, 16)
VIOLET = (139, 92, 246)
ELECTRIC = (196, 160, 255)
MAGENTA = (232, 70, 124)
GOLD = (233, 184, 114)
MUTE = (168, 148, 196)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def vertical_gradient(size, top, bottom) -> Image.Image:
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
    return g.resize((w, h), Image.BILINEAR)


def diagonal_glow(size, centre, radius, colour, alpha=255) -> Image.Image:
    """A soft radial light. Drawn small and scaled up: cheap, and no visible banding."""
    w, h = size
    s = 4
    small = Image.new("L", (w // s, h // s), 0)
    d = ImageDraw.Draw(small)
    cx, cy = centre[0] // s, centre[1] // s
    r = radius // s
    steps = 18
    for i in range(steps, 0, -1):
        rr = r * i / steps
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=int(alpha * (1 - i / steps) ** 1.6))
    small = small.filter(ImageFilter.GaussianBlur(r / 6))
    mask = small.resize((w, h), Image.BICUBIC)
    layer = Image.new("RGBA", (w, h), colour + (0,))
    layer.putalpha(mask)
    return layer


def jacaranda_mark(size: int, petals: int = 6) -> Image.Image:
    """The mark: six violet petals with a gold centre, transparent background, drawn at 4x."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    # glow underneath
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([s * .06, s * .06, s * .94, s * .94], fill=VIOLET + (90,))
    glow = glow.filter(ImageFilter.GaussianBlur(s * .06))
    im.alpha_composite(glow)

    d = ImageDraw.Draw(im)
    cx = cy = s / 2
    pr = s * .215                        # petal centre distance
    petal = s * .195                     # petal radius

    def disc(x, y, r, colour, outline=None, width=0):
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour, outline=outline, width=width)

    # petals: solid, with one lighter inner disc so the flower reads at 32 px instead of turning to mush
    for i in range(petals):
        a = -math.pi / 2 + i * 2 * math.pi / petals
        px, py = cx + math.cos(a) * pr, cy + math.sin(a) * pr
        disc(px, py, petal, (124, 82, 226, 255))
        disc(px - math.cos(a) * petal * .12, py - math.sin(a) * petal * .12,
             petal * .62, (160, 118, 250, 255))
    # a clean gap between petals and the centre, so the mark looks drawn rather than blended
    disc(cx, cy, s * .128, (10, 7, 16, 255))
    disc(cx, cy, s * .112, GOLD + (255,))
    disc(cx, cy, s * .055, (255, 244, 222, 255))
    return im.resize((size, size), Image.LANCZOS)


def avatar(out: Path, px: int = 1000) -> Path:
    im = vertical_gradient((px, px), (26, 16, 38), (9, 6, 14)).convert("RGBA")
    im = Image.alpha_composite(im, diagonal_glow((px, px), (px * .5, px * .32), px * .72, VIOLET, 120))
    # a faint violet rim so the avatar keeps its edge on a white timeline
    ring = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([2, 2, px - 3, px - 3], outline=(139, 92, 246, 110), width=max(2, px // 180))
    im = Image.alpha_composite(im, ring)
    mark = jacaranda_mark(int(px * .70))
    im.alpha_composite(mark, ((px - mark.width) // 2, (px - mark.height) // 2))
    p = out / f"avatar-{px}.png"
    im.convert("RGB").quantize(colors=192, method=Image.MEDIANCUT,
                               dither=Image.FLOYDSTEINBERG).save(p, optimize=True)
    return p


def banner(out: Path, w: int, h: int) -> Path:
    base = Image.new("RGB", (w, h), INK).convert("RGBA")

    # the artwork, cropped to the right third and faded into the ink
    if ART.exists():
        art = Image.open(ART).convert("RGB")
        scale = max((w * .62) / art.width, h / art.height)
        art = art.resize((round(art.width * scale), round(art.height * scale)), Image.LANCZOS)
        art = art.crop((art.width - int(w * .62), (art.height - h) // 2,
                        art.width, (art.height - h) // 2 + h))
        art = art.resize((w, h), Image.LANCZOS)
        art = art.convert("RGBA")
        # horizontal fade: opaque at the right edge, invisible where the type sits
        fade = Image.linear_gradient("L").rotate(90, expand=True).resize((w, h))
        mask = Image.new("L", (w, h), 0)
        mask.paste(fade.crop((int(w * .38), 0, w, h)), (int(w * .38), 0))
        mask = mask.filter(ImageFilter.GaussianBlur(w // 300))
        # keep it dim under the text side
        veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        for x in range(w):
            t = x / w
            a = int(215 * max(0.0, 1 - t * 1.25))
            vd.line([(x, 0), (x, h)], fill=(10, 7, 16, a))
        art.putalpha(mask)
        base = Image.alpha_composite(base, art)
        base = Image.alpha_composite(base, veil)

    base = Image.alpha_composite(base, diagonal_glow((w, h), (int(w * .13), int(h * .2)), int(h * .95), VIOLET, 130))

    d = ImageDraw.Draw(base)
    pad = int(h * .13)

    # mark + wordmark
    mark = jacaranda_mark(int(h * .22))
    base.alpha_composite(mark, (pad, int(h * .16)))
    d = ImageDraw.Draw(base)

    name_size = int(h * .125)
    f_name = ImageFont.truetype(SERIF, name_size)
    d.text((pad + mark.width + int(h * .07), int(h * .165)), "Jacaranda Labs", font=f_name, fill=(255, 255, 255))

    f_kick = ImageFont.truetype(SANSB, int(h * .052))
    d.text((pad + mark.width + int(h * .075), int(h * .165) + name_size + int(h * .03)),
           "V E N T U R E S   ·   P O R T F O L I O   ·   P U B L I C A T I O N S",
           font=f_kick, fill=MUTE)

    # two lines, sized to the canvas rather than to a fixed point size: a banner that overflows is
    # worse than a banner with smaller type
    def fitted(text: str, kind: str, start: int, min_px: int, max_w: int) -> ImageFont.FreeTypeFont:
        size = start
        while size > min_px:
            f = ImageFont.truetype(kind, size)
            if d.textlength(text, font=f) <= max_w:
                return f
            size -= 2
        return ImageFont.truetype(kind, min_px)

    avail = w - pad * 2 - int(w * .18)          # leave the artwork its right-hand room
    line1_a, line1_b = "Six businesses became ", "seven."
    f_line = fitted(line1_a + line1_b, SERIF, int(h * .15), int(h * .07), avail)
    y = int(h * .47)
    d.text((pad, y), line1_a, font=f_line, fill=(255, 255, 255))
    w1 = d.textlength(line1_a, font=f_line)
    d.text((pad + w1, y), line1_b, font=f_line, fill=MAGENTA)

    f_line2 = fitted("One operator. A written record of both.", SERIF, int(h * .105), int(h * .055), avail)
    d.text((pad, int(h * .47) + f_line.size + int(h * .045)),
           "One operator. A written record of both.", font=f_line2, fill=(236, 230, 244))

    f_sub = ImageFont.truetype(SANS, int(h * .055))
    d.text((pad, int(h * .79)), "Constraint-native software ventures from Harare.",
           font=f_sub, fill=(200, 188, 216))

    f_url = ImageFont.truetype(SANSB, int(h * .045))
    d.text((pad, int(h * .88)), "jacaranda-labs.pages.dev", font=f_url, fill=GOLD)

    p = out / f"banner-{w}x{h}.png"
    card = base.convert("RGB")
    # platforms re-encode anyway; 8-bit with dithering halves the file with no visible loss at this size
    card.quantize(colors=192, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).save(p, optimize=True)
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "brand" / "social"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    made = [avatar(out), banner(out, 1500, 500), banner(out, 3000, 1000)]
    for p in made:
        im = Image.open(p)
        print(f"  {p.name:<24} {im.width}x{im.height}  {p.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
