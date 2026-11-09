"""Build the hero still from the jacaranda source photo.

One JPEG instead of a video: the home page used to autoplay a 224 KB webm plus a 336 KB mp4 fallback
(and a 2.4 MB PNG in the repo) to show a flower. A photograph with a slow CSS drift on top gives the
same sense of movement for about 170 KB, one decode, no media pipeline, and nothing to go wrong on a
phone. Run this again only if the source photo changes.

    python3 tools/make_hero.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "art" / "jacaranda-hero-v1.jpg"
OUT = ROOT / "assets" / "art" / "hero.jpg"
W, H = 1920, 1080


def cover(path: Path, w: int, h: int, focus_x: float = 0.5, focus_y: float = 0.5) -> Image.Image:
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = round((im.width - w) * focus_x)
    y = round((im.height - h) * focus_y)
    return im.crop((x, y, x + w, y + h))


def grade(im: Image.Image) -> Image.Image:
    """Pull the photo into the site's palette: cooler shadows, violet highlights, less green."""
    r, g, b = im.split()
    # knock the green foliage back so the violets are what carries the frame
    g = g.point(lambda v: int(v * 0.88))
    r = r.point(lambda v: min(255, int(v * 1.04)))
    b = b.point(lambda v: min(255, int(v * 1.10 + 4)))
    im = Image.merge("RGB", (r, g, b))
    im = ImageEnhance.Color(im).enhance(1.12)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Brightness(im).enhance(1.10)
    # a soft bloom on the highlights, the way the old artwork glowed
    blur = im.filter(ImageFilter.GaussianBlur(18))
    im = Image.blend(im, Image.blend(im, blur, 0.55), 0.22)
    return im


def scrim(im: Image.Image) -> Image.Image:
    """Darken the left third and the bottom so white type sits on it without a box."""
    w, h = im.size
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(veil)
    for x in range(w):
        t = x / w
        a = int(200 * max(0.0, 1 - t * 1.9) + 18)
        d.line([(x, 0), (x, h)], fill=(10, 7, 16, a))
    vgrad = Image.new("L", (1, h))
    for y in range(h):
        t = y / (h - 1)
        vgrad.putpixel((0, y), int(24 + 168 * t ** 2.6))     # heavier at the foot of the frame
    veil = Image.alpha_composite(veil, Image.merge("RGBA", (
        Image.new("L", (w, h), 10), Image.new("L", (w, h), 7),
        Image.new("L", (w, h), 16), vgrad.resize((w, h)))))
    return Image.alpha_composite(im.convert("RGBA"), veil).convert("RGB")


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing source: {SRC}")
    im = grade(cover(SRC, W, H, focus_x=0.26, focus_y=0.38))
    im = scrim(im)
    im.save(OUT, "JPEG", quality=74, optimize=True, progressive=True, subsampling=2)
    kb = OUT.stat().st_size // 1024
    # a 960px variant for phones: half the bytes on the device that cares most
    small = im.resize((960, 540), Image.LANCZOS)
    small.save(OUT.with_name("hero-960.jpg"), "JPEG", quality=72, optimize=True, progressive=True)
    print(f"  {OUT.name:<16} {im.width}x{im.height}  {kb} KB")
    print(f"  hero-960.jpg     960x540      {OUT.with_name('hero-960.jpg').stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
