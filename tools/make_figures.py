#!/usr/bin/env python3
"""Draw the figures for the two new books, in the press's own idiom.

Same vocabulary as the covers: cream stock, black rules, one red accent, DejaVu serif for prose and
a small sans for labels. Everything is hand-placed SVG — no chart library, no external font, no
JavaScript — because a figure in this catalogue has to survive being printed at A5 and read on a
phone, and because a diagram that is generated from data would need data this book does not have.

    python3 tools/make_figures.py           # every figure, into assets/read/fig/
    python3 tools/make_figures.py --list    # what it would draw

Naming: a-*.svg belongs to The Point of Failure, b-*.svg to Operatorship. The manuscripts reference
them as /read/fig/<name>.svg so the paths work from the built site.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "read" / "fig"

CREAM = "#fdfcf8"
INK = "#14171a"
MUTE = "#5b6670"
RULE = "#dfe3e7"
ACCENT = "#7a1f1f"
PANEL = "#f4f5f3"
SERIF = "Iowan Old Style,Palatino Linotype,Palatino,Georgia,serif"
SANS = "ui-sans-serif,system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def svg(w: int, h: int, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" font-kerning="normal">'
            f'<rect width="{w}" height="{h}" fill="{CREAM}"/>' + body + "</svg>")


def t(x, y, s, size=13, fill=INK, font=SERIF, weight=400, anchor="start", ls=None, style=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    l = f' letter-spacing="{ls}"' if ls else ""
    w = f' font-weight="{weight}"' if weight != 400 else ""
    return (f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" fill="{fill}"{w}{a}{l} '
            f'style="{style}">{esc(s)}</text>')


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def label(x, y, s, size=9.5, fill=MUTE, anchor="start", ls=".12em"):
    return t(x, y, s.upper(), size=size, fill=fill, font=SANS, weight=600, anchor=anchor, ls=ls)


def rule(x1, y1, x2, y2, colour=RULE, width=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{colour}" stroke-width="{width}"{d}/>'


def box(x, y, w, h, fill="none", stroke=RULE, rx=3, width=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"{d}/>')


def wrap(px_width: int, text: str, char_avg: float = 6.2) -> list[str]:
    """Greedy wrap by estimated width — good enough for label-sized type, and it never overflows."""
    limit = max(8, int(px_width / char_avg))
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if len(trial) <= limit:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def tick(x, y, colour=INK, scale=1.0):
    return (f'<path d="M{x} {y} l{4*scale} {4.5*scale} l{9*scale} {-10*scale}" fill="none" '
            f'stroke="{colour}" stroke-width="{2.2*scale}" stroke-linecap="round" '
            f'stroke-linejoin="round"/>')


def cross(x, y, colour=ACCENT, scale=1.0):
    return (f'<path d="M{x} {y} l{9*scale} {9*scale} M{x+9*scale} {y} l{-9*scale} {9*scale}" '
            f'fill="none" stroke="{colour}" stroke-width="{2.2*scale}" stroke-linecap="round"/>')


def arrow(x1, y1, x2, y2, colour=INK, width=1.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{colour}" stroke-width="{width}" fill="none"{d} '
            f'marker-end="url(#ah)"/>')


HEAD = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" '
        'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#14171a"/></marker></defs>')


# --------------------------------------------------------------------------- book A
def a01_single_point() -> str:
    """The estate has a failover everywhere except one place."""
    w, h = 760, 470
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 1"))
    b.append(t(40, 74, "Every component has a failover except one", 21))
    b.append(t(40, 98, "The estate is designed so that any single part can be absent for a while. "
                       "One part cannot.", 12.5, MUTE))

    rows = [("Publishing rail", "retries · says so when it fails"),
            ("Post bank", "refills before it empties"),
            ("Deploy", "rebuilds · verifies the origin"),
            ("Checkouts", "take money without anyone awake"),
            ("Front doors", "checked hourly from outside"),
            ("Credentials", "expire loudly, not quietly")]
    y = 130
    for name, note in rows:
        b.append(box(40, y, 400, 34, PANEL, RULE))
        b.append(t(54, y + 22, name, 13.5))
        b.append(t(196, y + 22, note, 11.5, MUTE, SANS))
        b.append(tick(414, y + 12, "#2f6b3a", 0.9))
        y += 40

    # the operator, alone and without a copy
    b.append(box(470, 130, 250, 232, "#fbf3f2", ACCENT, 4, 1.5))
    b.append(label(490, 158, "no replica", fill=ACCENT))
    b.append(t(490, 196, "The operator", 19))
    b.append(t(490, 220, "One nervous system.", 11.5, MUTE, SANS))
    b.append(t(490, 236, "One sleep pattern.", 11.5, MUTE, SANS))
    b.append(t(490, 252, "One capacity to decide", 11.5, MUTE, SANS))
    b.append(t(490, 268, "at four in the afternoon.", 11.5, MUTE, SANS))
    b.append(cross(490, 292, ACCENT, 1.1))
    b.append(t(512, 302, "no warm standby", 12, ACCENT, SANS, 600))
    b.append(t(490, 330, "Everything rests on it.", 12.5, INK, SERIF, 400, "start", None, "font-style:italic"))

    b.append(rule(40, 392, 720, 392, INK, 1))
    b.append(t(40, 418, "The operator therefore gets what every other component gets:", 12.5))
    for i, word in enumerate(["written down", "checked", "given limits", "monitored"]):
        x = 40 + i * 172
        b.append(box(x, 430, 158, 26, PANEL, RULE, 13))
        b.append(t(x + 79, 447, word, 11.5, INK, SANS, 600, "middle"))
    return svg(w, h, "".join(b))


def a02_nine() -> str:
    """Nine rules, and the check that keeps each one."""
    w, h = 760, 430
    rules = [("01", "Shutdown", "said out loud?"),
             ("02", "Day off", "business in my head?"),
             ("03", "Sleep", "am I at three nights?"),
             ("04", "First 90 min", "has it moved by 10:30?"),
             ("05", "No money Sunday", "did I open it?"),
             ("06", "Move", "did I leave the building?"),
             ("07", "One conversation", "who did I talk to?"),
             ("08", "Worry window", "is it written down?"),
             ("09", "No new venture", "how many unresolved?")]
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 2"))
    b.append(t(40, 74, "Nine rules, and the question that checks each one", 21))
    b.append(t(40, 98, "A rule that needs to be felt in order to be kept is not a rule. "
                       "Each of these has a check that takes seconds.", 12.5, MUTE))
    for i, (n, name, check) in enumerate(rules):
        col, row = i % 3, i // 3
        x, y = 40 + col * 232, 122 + row * 96
        b.append(box(x, y, 216, 84, PANEL, RULE))
        b.append(t(x + 14, y + 26, n, 12, ACCENT, MONO, 600))
        b.append(t(x + 44, y + 26, name, 14.5, INK, SERIF, 600))
        b.append(rule(x + 14, y + 38, x + 202, y + 38))
        b.append(t(x + 14, y + 58, "check", 8.5, MUTE, SANS, 600, "start", ".12em"))
        b.append(t(x + 14, y + 74, check, 11.5, INK, SANS))
    b.append(t(40, 418, "Six of nine is information. Four of nine, three weeks running, is a finding "
                        "about the business.", 12, MUTE, SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


def a03_clock() -> str:
    """The day, the week, the month — three rings of the same clock."""
    w, h = 760, 330
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 3"))
    b.append(t(40, 74, "The only three units of time in the method", 21))
    panels = [("THE DAY", "10 min · morning", "the one outcome, before the inbox"),
              ("THE DAY", "5 min · evening", "the shutdown: written, out loud, closed"),
              ("THE WEEK", "45 min", "the review, same hour, one page"),
              ("THE MONTH", "2 h · first Monday", "kill one thing · amend one rule")]
    for i, (unit, span, what) in enumerate(panels):
        x = 40 + i * 174
        b.append(box(x, 108, 158, 150, PANEL, RULE))
        b.append(label(x + 14, 132, unit, size=8.5, fill=ACCENT))
        b.append(t(x + 14, 158, span, 13.5))
        b.append(rule(x + 14, 170, x + 144, 170))
        words, line, lines = what.split(), "", []
        for word in words:
            trial = (line + " " + word).strip()
            if len(trial) <= 20:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for j, ln in enumerate(lines):
            b.append(t(x + 14, 192 + j * 17, ln, 11.5, MUTE, SANS))
    b.append(rule(40, 288, 720, 288))
    b.append(t(40, 310, "The clock is the constant. If the work does not fit the clock, the work is wrong.",
               12.5, INK, SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


def a04_badday() -> str:
    """Three steps, in order."""
    w, h = 760, 400
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 4"))
    b.append(t(40, 74, "The bad day: three steps, in order, and none of them is rescuing the day", 20))
    steps = [("STEP ONE", "2 minutes", "Make it safe",
              ["Run the estate screen once.",
               "If the one thing is under three minutes, do it.",
               "If not: nothing today."]),
             ("STEP TWO", "10 minutes", "Shrink the day",
              ["Cancel what can be cancelled.",
               "One outcome becomes none — or becomes",
               "eat, walk, sleep at a reasonable hour."]),
             ("STEP THREE", "the rest of it", "Leave it alone",
              ["No catching up later in the same day.",
               "The shutdown still happens,",
               "even if the day contained nothing."])]
    for i, (n, mins, title, lines) in enumerate(steps):
        x = 40 + i * 232
        b.append(box(x, 108, 216, 216, PANEL, RULE))
        b.append(f'<rect x="{x}" y="108" width="216" height="4" fill="{INK}"/>')
        b.append(label(x + 16, 138, n, size=8.5, fill=ACCENT))
        b.append(t(x + 16, 162, mins, 11, MUTE, SANS, 600))
        b.append(t(x + 16, 190, title, 16))
        b.append(rule(x + 16, 202, x + 200, 202))
        for j, ln in enumerate(lines):
            b.append(t(x + 16, 224 + j * 17, ln, 11, MUTE, SANS))
        if i < 2:
            b.append(arrow(x + 220, 216, x + 228, 216, MUTE, 1.2))
    b.append(rule(40, 348, 720, 348, INK))
    b.append(t(40, 374, "A day that is closed properly costs one day. A day that is repaid costs four.",
               12.5, INK, SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


def a05_worry() -> str:
    """The loop, and the list."""
    w, h = 760, 380
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 5"))
    b.append(t(40, 74, "Anxiety written down becomes a list; anxiety held becomes a day", 20))

    # left: the loop
    b.append(box(40, 104, 330, 210, PANEL, RULE))
    b.append(label(56, 128, "held", fill=ACCENT))
    cx, cy, r = 205, 218, 62
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{ACCENT}" stroke-width="1.2"/>')
    b.append(f'<path d="M{cx+r*0.86} {cy-r*0.5} A{r} {r} 0 0 1 {cx+r*0.5} {cy+r*0.86}" fill="none" '
             f'stroke="{ACCENT}" stroke-width="2" marker-end="url(#ah)"/>')
    for ang, s in ((-150, "the fear"), (-30, "no action"), (90, "the fear, again")):
        import math
        rad = math.radians(ang)
        x, y = cx + (r + 40) * math.cos(rad), cy + (r + 16) * math.sin(rad)
        b.append(t(x, y, s, 10, MUTE, SANS, 600, "middle"))
    b.append(t(56, 300, "no conclusion · a constant tax on everything else", 10.5, MUTE, SANS))

    # right: the list
    b.append(box(390, 104, 330, 210, "#fbf8f2", RULE))
    b.append(label(406, 128, "written · 20 minutes"))
    rows = ["the fear — named, in one line",
            "the worst case — survivable?",
            "the next physical action — one",
            "then: closed until the next window"]
    for i, s in enumerate(rows):
        y = 158 + i * 34
        b.append(box(406, y - 13, 298, 26, "#fff", RULE, 2))
        b.append(t(418, y + 4, s, 11.5, INK, SANS))
        b.append(tick(682, y - 9, "#2f6b3a", 0.8))
    b.append(t(406, 300, "a list has an end · a task is smaller than a threat", 10.5, MUTE, SANS,
               400, "start", None, "font-style:italic"))
    b.append(rule(40, 336, 720, 336))
    b.append(t(40, 360, "Twenty minutes with a pen, then the window is closed. Not because the worry is "
                        "solved, but because the reading is finished.", 12, MUTE))
    return svg(w, h, "".join(b))


def a06_signals() -> str:
    """Five leading indicators."""
    w, h = 760, 360
    b = [HEAD]
    b.append(label(40, 42, "The Point of Failure · figure 6"))
    b.append(t(40, 74, "Five signals that arrive before the bad day", 21))
    b.append(t(40, 98, "Feelings lag. These four are visible in artefacts you already produce; the fifth "
                       "is the least subtle.", 12.5, MUTE))
    sig = [("1", "The non-work life shrinks", "walk · conversation · Saturdays", "calendar"),
           ("2", "The queue stops moving", "the same item, nine days", "the estate screen"),
           ("3", "The numbers stop being read", "relief, not avoidance", "the Monday review"),
           ("4", "The tone changes", "curt, or over-explained", "your sent folder"),
           ("5", "Sleep goes", "the last to show, the least subtle", "the week")]
    y = 128
    for n, head, detail, where in sig:
        b.append(f'<circle cx="56" cy="{y + 14}" r="13" fill="{"#fbf3f2" if n == "5" else PANEL}" '
                 f'stroke="{ACCENT if n == "5" else RULE}"/>')
        b.append(t(56, y + 19, n, 12, ACCENT if n == "5" else INK, MONO, 600, "middle"))
        b.append(t(84, y + 18, head, 14))
        b.append(t(320, y + 18, detail, 11.5, MUTE, SANS))
        b.append(t(586, y + 18, where, 10.5, MUTE, SANS, 600))
        b.append(rule(40, y + 34, 720, y + 34))
        y += 44
    b.append(t(40, 350, "Three of five showing: treat the week as if it contained a bad day, and take the "
                        "protocol early.", 12, INK, SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


# --------------------------------------------------------------------------- book B
def b01_moats() -> str:
    """Three moats, three waves."""
    w, h = 760, 440
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 1"))
    b.append(t(40, 74, "Three moats, repriced one at a time", 21))
    b.append(t(40, 98, "Each wave commoditised the layer above the previous one. The moat moved down one "
                       "level each time.", 12.5, MUTE))

    x0, x1 = 60, 700
    waves = [("1999–2008", "software as a service", "capital", "you still had to build it"),
             ("2009–2020", "no-code and platforms", "product shape", "you had to beat the template"),
             ("2021–2026", "capability as a utility", "thought", "you had to know what to think")]
    for i, (span, name, killed, survived) in enumerate(waves):
        x = x0 + i * 214
        b.append(box(x, 126, 202, 150, PANEL, RULE))
        b.append(label(x + 14, 148, span, size=8.5, fill=ACCENT))
        b.append(t(x + 14, 172, name, 12.5))
        b.append(rule(x + 14, 184, x + 188, 184))
        b.append(t(x + 14, 204, "priced at zero:", 9, MUTE, SANS, 600))
        b.append(t(x + 14, 222, killed, 13))
        b.append(t(x + 14, 246, "what survived:", 9, MUTE, SANS, 600))
        for j, ln in enumerate(wrap(178, survived, 5.6)[:2]):
            b.append(t(x + 14, 264 + j * 14, ln, 11, MUTE, SANS))
    # the descent
    for i in range(2):
        b.append(arrow(x0 + 202 + i * 214, 200, x0 + 214 + i * 214, 200, MUTE, 1.2))
    b.append(arrow(210, 282, 210, 316, ACCENT, 1.4))
    b.append(t(224, 306, "what is underneath thought is consequence", 11.5, ACCENT, SANS, 600))
    b.append(box(60, 320, 640, 54, "#fbf3f2", ACCENT, 3, 1.2))
    b.append(t(78, 344, "Nothing sits under consequence.", 14, INK))
    b.append(t(78, 362, "The last wave that can reprice the fundamentals — "
                        "which is why the name has to change now.", 11.5, MUTE, SANS))
    b.append(t(60, 404, "The same gift every time: your advantage, handed to everybody.", 12.5, INK,
               SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


def b02_cost() -> str:
    """What a launch costs, and what being believed costs."""
    w, h = 760, 400
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 2"))
    b.append(t(40, 74, "Two curves that crossed", 21))
    b.append(t(40, 98, "The cost of making the thing fell to nothing. The cost of being believed did not "
                       "move — and then became the whole job.", 12.5, MUTE))
    ox, oy, iw, ih = 90, 130, 580, 200
    b.append(f'<path d="M{ox} {oy} L{ox} {oy+ih} L{ox+iw} {oy+ih}" fill="none" stroke="{INK}" stroke-width="1.2"/>')
    b.append(label(ox, oy - 12, "cost per unit"))

    b.append(t(ox + 8, oy + 16, "high", 9.5, MUTE, SANS))
    b.append(t(ox + 8, oy + ih - 6, "low", 9.5, MUTE, SANS))
    for yr, frac in (("2000", 0.06), ("2008", 0.3), ("2016", 0.58), ("2026", 0.96)):
        x = ox + iw * frac
        b.append(rule(x, oy + ih, x, oy + ih + 5, MUTE))
        b.append(t(x, oy + ih + 20, yr, 9.5, MUTE, SANS, 400, "middle"))
    # falling cost of a launch
    b.append(f'<path d="M{ox+18} {oy+30} C {ox+180} {oy+40}, {ox+260} {oy+120}, {ox+330} {oy+160} '
             f'S {ox+480} {oy+186}, {ox+iw-10} {oy+190}" fill="none" stroke="{INK}" stroke-width="2"/>')
    b.append(t(ox + 108, oy + 146, "what a launch costs", 11.5, INK, SANS, 600))
    # rising cost of being believed
    b.append(f'<path d="M{ox+18} {oy+178} C {ox+200} {oy+176}, {ox+300} {oy+150}, {ox+420} {oy+96} '
             f'S {ox+520} {oy+40}, {ox+iw-10} {oy+26}" fill="none" stroke="{ACCENT}" stroke-width="2"/>')
    b.append(t(ox + 330, oy + 34, "what being believed costs", 11.5, ACCENT, SANS, 600))
    # crossing
    b.append(f'<circle cx="{ox+265}" cy="{oy+117}" r="4" fill="{ACCENT}"/>')
    b.append(t(ox + 278, oy + 112, "the crossover", 10.5, ACCENT, SANS, 600))
    b.append(rule(40, 352, 720, 352))
    b.append(t(40, 376, "After the crossover, capability is a subscription and judgement is the scarce "
                        "input. The word for an operator is not a courtesy; it is a price.", 12, MUTE))
    return svg(w, h, "".join(b))


def b03_owns() -> str:
    """What the operator owns."""
    w, h = 760, 430
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 3"))
    b.append(t(40, 74, "Five things the operator owns, and the machine cannot", 21))
    cx, cy = 380, 250
    spokes = [("Consequence", "the name on the act", 0.0),
              ("Taste", "which of ten is good", 72.0),
              ("The naming of things", "what it refuses to do", 144.0),
              ("The truth about the numbers", "evidence that could say otherwise", 216.0),
              ("Contact with humans", "a reply is a person", 288.0)]
    import math
    b.append(f'<circle cx="{cx}" cy="{cy}" r="62" fill="{PANEL}" stroke="{INK}" stroke-width="1.4"/>')
    b.append(t(cx, cy - 4, "the", 11, MUTE, SANS, 400, "middle"))
    b.append(t(cx, cy + 16, "operator", 15, INK, SERIF, 600, "middle"))
    for name, note, ang in spokes:
        rad = math.radians(ang - 90)
        x, y = cx + 150 * math.cos(rad), cy + 122 * math.sin(rad)
        b.append(rule(cx + 62 * math.cos(rad), cy + 62 * math.sin(rad),
                      x - 8 * math.cos(rad), y - 8 * math.sin(rad), RULE, 1))
        b.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{ACCENT}"/>')
        anchor = "middle" if abs(math.cos(rad)) < 0.35 else ("start" if math.cos(rad) > 0 else "end")
        # labels sit outside the dot; the top one needs room for two lines above it
        dy = -34 if math.sin(rad) < -0.85 else (-14 if math.sin(rad) < -0.3 else (18 if math.sin(rad) > 0.3 else 4))
        b.append(t(x + (0 if anchor == "middle" else (10 if anchor == "start" else -10)), y + dy,
                   name, 12.5, INK, SERIF, 600, anchor))
        b.append(t(x + (0 if anchor == "middle" else (10 if anchor == "start" else -10)), y + dy + 16,
                   note, 10.5, MUTE, SANS, 400, anchor))
    b.append(rule(40, 392, 720, 392))
    b.append(t(40, 416, "All five are burdens, not skills. That is how you know you have found the "
                        "scarce input.", 12, MUTE))
    return svg(w, h, "".join(b))


def b04_estate() -> str:
    """The estate, not the venture."""
    w, h = 760, 400
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 4"))
    b.append(t(40, 74, "The unit is the estate, not the venture", 21))
    b.append(t(40, 98, "The machinery is expensive and durable. The ventures are cheap, and must be "
                       "individually killable.", 12.5, MUTE))
    b.append(box(40, 122, 320, 196, PANEL, INK, 4, 1.2))
    b.append(label(56, 146, "the estate · durable"))
    shared = ["publishing rails", "checkout + delivery", "deploy and verify",
              "the outreach sequence", "the record of what was said", "the operator's calibration"]
    for i, s in enumerate(shared):
        y = 172 + i * 24
        b.append(t(56, y, "· " + s, 11.5, INK, SANS))
    b.append(t(56, 306, "fixed cost, paid once", 10.5, MUTE, SANS, 600))

    for i in range(4):
        y = 122 + i * 50
        b.append(box(400, y, 250, 42, "#fff", RULE, 3))
        b.append(t(414, y + 26, f"venture {i+1} — a hypothesis", 11.5))
        b.append(t(636, y + 26, "killable", 9, MUTE, SANS, 600, "end"))
    b.append(box(400, 322, 250, 42, "#fbf3f2", ACCENT, 3, 1.2))
    b.append(t(414, y + 26 + 8, "the kill list", 11.5, ACCENT, SANS, 600))
    b.append(arrow(360, 220, 398, 220, MUTE, 1.3))
    b.append(t(370, 210, "shares", 9, MUTE, SANS, 600, "end"))
    b.append(rule(40, 372, 720, 372))
    b.append(t(40, 394, "Anyone can build a venture now. The compounding asset is the machinery, the "
                        "record, and the calibration.", 12, MUTE))
    return svg(w, h, "".join(b))


def b05_syllabus() -> str:
    """Two syllabi."""
    w, h = 760, 460
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 5"))
    b.append(t(40, 74, "Two syllabi for the same subject", 21))
    b.append(t(40, 98, "Everything that was produced has been commoditised. Everything that was carried "
                       "is now the curriculum.", 12.5, MUTE))
    old = ["The business plan", "Marketing plan", "Financial projections",
           "Intellectual property", "Operations management", "Legal and ethics",
           "Networking", "Technology (as a module)"]
    new = ["Proof of operation", "Mechanism literacy", "The economics of a test",
           "The accountability contract", "Distribution as being believed",
           "Supervision of machine work", "The evidence trail", "The pause switch"]
    b.append(label(40, 126, "was taught", fill=ACCENT))
    b.append(label(400, 126, "has to be taught"))
    for i, s in enumerate(old):
        y = 148 + i * 34
        b.append(box(40, y, 320, 28, PANEL, RULE, 2))
        b.append(t(54, y + 19, s, 12, MUTE, SANS))
        b.append(arrow(366, y + 14, 396, y + 14, RULE, 1.1))
    for i, s in enumerate(new):
        y = 148 + i * 34
        b.append(box(400, y, 320, 28, "#fff", INK, 2, 1))
        b.append(t(414, y + 19, s, 12, INK, SANS, 600))
    b.append(rule(40, 430, 720, 430))
    b.append(t(40, 452, "Plus a ninth module the old course could not have taught: how to be a person "
                        "who can live.", 12, MUTE, SERIF, 400, "start", None, "font-style:italic"))
    return svg(w, h, "".join(b))


def b06_failures() -> str:
    """Five failure modes."""
    w, h = 760, 380
    b = [HEAD]
    b.append(label(40, 42, "Operatorship · figure 6"))
    b.append(t(40, 74, "Five ways an operator fails", 21))
    b.append(t(40, 98, "The first four are failures of the estate. The fifth is the operator.", 12.5, MUTE))
    items = [("Novelty drift", "starting is always available as a way of avoiding finishing"),
             ("Unbounded surface", "every surface must arrive with the check that watches it"),
             ("Ghost authority", "a green tick from a system nobody read is a rumour with a colour"),
             ("Automation debt", "a machine nobody can explain, including its owner"),
             ("The sole decider", "thirty consequences a week, and nobody to say are you sure")]
    for i, (head, detail) in enumerate(items):
        col, row = i % 2, i // 2
        x, y = 40 + col * 348, 126 + row * 88
        danger = i == 4
        b.append(box(x, y, 332, 76, "#fbf3f2" if danger else PANEL, ACCENT if danger else RULE,
                     3, 1.2 if danger else 1))
        b.append(t(x + 16, y + 28, head, 14.5, ACCENT if danger else INK, SERIF, 600))
        # naive wrap
        words, line, lines = detail.split(), "", []
        for word in words:
            trial = (line + " " + word).strip()
            if len(trial) <= 46:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        for j, ln in enumerate(lines[:2]):
            b.append(t(x + 16, y + 50 + j * 15, ln, 11, MUTE, SANS))
    b.append(rule(40, 320, 720, 320))
    b.append(t(40, 344, "Each one has a rule that holds it. The fifth is the subject of a different "
                        "book in this series.", 12, MUTE))
    return svg(w, h, "".join(b))


FIGURES = {
    "a-01-single-point.svg": a01_single_point,
    "a-02-nine.svg": a02_nine,
    "a-03-clock.svg": a03_clock,
    "a-04-badday.svg": a04_badday,
    "a-05-worry.svg": a05_worry,
    "a-06-signals.svg": a06_signals,
    "b-01-moats.svg": b01_moats,
    "b-02-cost.svg": b02_cost,
    "b-03-owns.svg": b03_owns,
    "b-04-estate.svg": b04_estate,
    "b-05-syllabus.svg": b05_syllabus,
    "b-06-failures.svg": b06_failures,
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        for name in FIGURES:
            print(name)
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in FIGURES.items():
        path = OUT / name
        path.write_text(fn(), encoding="utf-8")
        print(f"  {name:<26}{path.stat().st_size // 1024 or 1} KB")
    print(f"{len(FIGURES)} figures → assets/read/fig/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
