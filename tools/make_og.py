"""Regenerate the 1200x630 share card from the hero artwork, in the current dark-editorial style."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 630
INK = (10, 7, 16)
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def cover(path, w, h, dx: float = .5, dy: float = .5):
    im = Image.open(path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x = int((im.width - w) * dx)
    y = int((im.height - h) * dy)
    return im.crop((x, y, x + w, y + h))


def grad(w, h, stops):
    g = Image.new("L", (1, h))
    for i in range(h):
        t = i / (h - 1)
        for (p0, a0), (p1, a1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                k = (t - p0) / max(p1 - p0, 1e-6)
                g.putpixel((0, i), int(a0 + (a1 - a0) * k))
                break
    return g.resize((w, h))


def main():
    # the photograph sits in the right 60% and fades into ink, so the headline is never over petals
    base = Image.new("RGB", (W, H), INK)
    art = cover("assets/art/jacaranda-hero-v1.jpg", int(W * .72), H, dx=.55)
    fade = Image.linear_gradient("L").rotate(90, expand=True).resize((art.width, H))
    mask = Image.new("L", (W, H), 0)
    mask.paste(fade.point(lambda v: min(255, int(v * 1.9))), (W - art.width, 0))
    art_canvas = Image.new("RGB", (W, H), INK)
    art_canvas.paste(art, (W - art.width, 0))
    base = Image.composite(art_canvas, base, mask)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for x in range(W):                                   # horizontal scrim
        t = x / W
        a = int(215 * max(0.0, 1 - t * 1.35) + 12)
        vd.line([(x, 0), (x, H)], fill=(10, 7, 16, a))
    top = grad(W, H, [(0, 150), (0.35, 30), (0.72, 60), (1, 210)])
    veil = Image.alpha_composite(veil, Image.merge("RGBA", (
        Image.new("L", (W, H), 10), Image.new("L", (W, H), 7), Image.new("L", (W, H), 16), top)))
    out = Image.alpha_composite(base.convert("RGBA"), veil)

    d = ImageDraw.Draw(out)
    f_logo = ImageFont.truetype(SANSB, 27)
    f_kick = ImageFont.truetype(SANSB, 17)
    f_h = ImageFont.truetype(SERIF, 66)
    f_sub = ImageFont.truetype(SANS, 25)
    f_foot = ImageFont.truetype(SANSB, 20)

    x = 74
    # jacaranda mark
    cx, cy, r = x + 15, 74, 15
    for i in range(6):
        import math
        a = math.pi / 3 * i
        d.ellipse([cx + math.cos(a) * r * .62 - 9, cy + math.sin(a) * r * .62 - 9,
                   cx + math.cos(a) * r * .62 + 9, cy + math.sin(a) * r * .62 + 9],
                  fill=(139, 92, 246))
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(233, 184, 114))
    d.text((x + 44, 60), "Jacaranda Labs", font=f_logo, fill=(255, 255, 255))
    d.text((x + 45, 96), "V E N T U R E S   ·   P O R T F O L I O   ·   P U B L I C A T I O N S",
           font=ImageFont.truetype(SANSB, 13), fill=(168, 148, 196))

    d.text((x, 178), "H A R A R E ,   Z I M B A B W E   ·   S I N C E   2 0 2 6",
           font=f_kick, fill=(168, 148, 196))

    lines = ["Six businesses", "became seven.", "One operator."]
    y = 236
    for i, ln in enumerate(lines):
        col = (255, 255, 255) if i < 2 else (255, 255, 255)
        d.text((x, y), ln, font=f_h, fill=col)
        y += 82
    # accent the word "seven"
    sw = d.textlength("became ", font=f_h)
    d.text((x + sw, 236 + 82), "seven.", font=f_h, fill=(232, 70, 124))

    d.text((x, 486), "Constraint-native software ventures, built by agents", font=f_sub, fill=(203, 191, 217))
    d.text((x, 518), "instead of a team — and the 20 works that study them.", font=f_sub, fill=(203, 191, 217))

    d.line([(x, 566), (x + 1052, 566)], fill=(60, 48, 78), width=1)
    d.text((x, 582), "7 ventures   ·   20 publications   ·   0 external funding",
           font=f_foot, fill=(233, 184, 114))
    d.text((x + 760, 582), "jacaranda-labs.pages.dev", font=f_foot, fill=(168, 148, 196))

    card = out.convert("RGB")
    # 8-bit palette keeps the card under ~200 KB without visible banding at this size
    card.quantize(colors=160, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG).save(
        "assets/og.png", optimize=True)
    print("assets/og.png", out.size)


if __name__ == "__main__":
    main()
