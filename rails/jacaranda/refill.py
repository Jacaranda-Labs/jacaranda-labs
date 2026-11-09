#!/usr/bin/env python3
"""Refill the press bank — from the site's own data, not from invention.

The twelve seed posts in press.py are written by hand and mapped one-to-one onto rendered cards. They
last about fifteen days at a thirty-hour cadence, and then the rail stops, which would put the whole
"seven ventures sell without the owner" rule on a fortnight's worth of typing. This closes that.

What it may use, and why it is safe:

  data/works.json     only works with a public read route (`read` is set). Private author-review
                      editions are catalogued on the site but must never be pushed, so they are not
                      candidates. This is the same rule the site states, enforced here in code.
  data/ventures.json  name, one line, who it is for, entry price and the buy link — the same facts the
                      site shows, so a post cannot promise something the venture page does not.

Every generated post gets a real card, rendered in the same style as the seed cards, and every post
is checked against the same rules the seed bank is: 2 value : 1 promo in every window of three, no two
promos adjacent, no post over Bluesky's 300 with its link, no post without a card.

    python3 rails/jacaranda/refill.py                 # top up to three unposted posts
    python3 rails/jacaranda/refill.py --ensure 6      # keep at least six ahead
    python3 rails/jacaranda/refill.py --plan          # what is left in the bank, and what is next
    python3 rails/jacaranda/refill.py --selftest      # check every rule without writing anything

Generated posts live in rails/jacaranda/bank.json and their cards in assets/cards/. Both are committed
by the press workflow, so a dead runner cannot lose a post or a picture.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CARDS_DIR = ROOT / "assets" / "cards"
CARDS = "https://jacaranda-labs.pages.dev/assets/cards"
SITE = "https://jacaranda-labs.pages.dev"
BANK_FILE = HERE / "bank.json"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))

SKY_LIMIT = 300          # Bluesky counts graphemes; a post plus its link must fit


# --------------------------------------------------------------------------- text
def clip(text: str, limit: int) -> str:
    """Cut on a sentence, then a clause, then a word — never mid-word if it can be helped."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    for sep in (". ", "; ", ", ", " "):
        cut = text[:limit]
        at = cut.rfind(sep)
        if at > limit * 0.55:
            return cut[:at].rstrip(" ,;:") + ("." if sep == ". " else "")
    return text[:limit].rstrip(" ,;:") + "…"


def short_title(work: dict, words: int = 7) -> str:
    """A title that fits a card headline: the subtitle is usually the better half."""
    title = (work.get("title") or "").strip()
    sub = (work.get("subtitle") or "").strip()
    if len(title) <= 46:
        return title
    if sub and len(sub) <= 46:
        return sub[0].upper() + sub[1:]
    return " ".join(title.split()[:words])


def first_sentence(blurb: str) -> str:
    blurb = re.sub(r"\s+", " ", blurb or "").strip()
    m = re.match(r"(.+?[.!?])(\s|$)", blurb)
    return (m.group(1) if m else blurb).strip()


def compose(body: str, link: str) -> str:
    """A post whose body, blank line and link fit inside the smallest rail's ceiling."""
    room = SKY_LIMIT - (len(link) + 2 if link else 0)
    body = clip(body, max(80, room))
    return f"{body}\n\n{link}" if link else body


# --------------------------------------------------------------------------- candidates
def public_works() -> list[dict]:
    works = json.loads((ROOT / "data" / "works.json").read_text())
    return [w for w in works if w.get("read")]


def ventures() -> list[dict]:
    return json.loads((ROOT / "data" / "ventures.json").read_text())


def work_posts(work: dict, round_no: int) -> dict:
    """Three angles on a public work. Value only: reading is free, so nothing here is a sell.

    The copy is built from the work's own subtitle, blurb and facts, and each angle uses a different
    one — a template that repeats the same sentence over ten works reads as a machine, which is the
    one thing a studio selling "built by agents, checked by a person" cannot afford.
    """
    wid = work["id"]
    title = short_title(work)
    url = f"{SITE}{work['read']}"
    sub = (work.get("subtitle") or "").strip().rstrip(".")
    facts = [f for f in (work.get("facts") or []) if f]
    kind_word = {"book": "book", "paper": "paper", "report": "report", "research": "working paper",
                 "essay": "essay"}.get(work.get("kind"), "work")
    base = dict(kind="value", work=wid)

    if round_no == 0:                                    # what it is, in its own words
        body = f"{title}: {sub}." if sub else f"A {kind_word} on {title}."
        body += " Free to read, no signup."
        return {**base, "id": f"work-{wid}", "card_id": f"work-{wid}",
                "kicker": f"FREE TO READ · {kind_word.upper()}",
                "headline": title,
                "card_body": clip(sub or first_sentence(work.get("blurb", "")), 130),
                "text": compose(body, url), "link": url,
                "tags": ["writing", "buildinpublic"]}
    if round_no == 1:                                    # the argument, from the blurb
        body = first_sentence(work.get("blurb", ""))
        body = f"{clip(body, 190)} It is free to read."
        return {**base, "id": f"work-{wid}-argument", "card_id": f"work-{wid}-argument",
                "kicker": "THE ARGUMENT",
                "headline": title,
                "card_body": clip(sub or first_sentence(work.get("blurb", "")), 130),
                "text": compose(body, url), "link": url,
                "tags": ["writing", "smallbusiness"]}
    numbers = ", ".join(facts[:2]) if facts else f"{kind_word}, free to read"
    return {**base, "id": f"work-{wid}-facts", "card_id": f"work-{wid}-facts",
            "kicker": "WHAT IS IN IT",
            "headline": title,
            "card_body": clip(sub or first_sentence(work.get("blurb", "")), 130),
            "text": compose(f"{numbers}. {title}, on the site in full.", url),
            "link": url, "tags": ["writing", "reading"]}


def venture_posts(v: dict) -> dict:
    """One promo per venture: what it is, who it is for, what it costs, where to buy."""
    line = (v.get("line") or "").strip().rstrip(".")
    # the audience is appended separately, so any "…, for stores, SaaS and agencies" tail comes off
    what = clip(first_sentence(v.get("what", "")), 150)
    what = re.sub(r",?\s+for [^.]*\.?$", "", what).rstrip(" ,;:")
    price = (v.get("from") or "").strip()
    who = (v.get("for") or "").strip().rstrip(".")
    body = what.rstrip(" ,;:.") + "."
    if who:
        body += f" For {who[0].lower() + who[1:]}."
    if price:
        body += f" From {price}."
    return dict(id=f"venture-{v['id']}", card_id=f"venture-{v['id']}", kind="promo",
                venture=v["id"],
                kicker=f"{v['name'].upper()} · FROM {price}" if price else v["name"].upper(),
                headline=clip(line or what, 46),
                card_body=clip(what, 120),
                text=compose(body, v.get("buy") or v.get("url") or SITE),
                link=v.get("buy") or v.get("url") or SITE,
                tags=["smallbusiness", v["id"]])


def candidates(used: set[str], rounds: int = 3) -> list[dict]:
    """Value, value, promo — interleaved, so no window of three can break 2:1.

    The two pools are built separately and then woven, because the work angles (value) are always
    going to be more numerous than the seven ventures (promo). Woven in 2:1 the bank stays balanced
    no matter how many of each are left, and the tail degrades to value-only rather than to a run
    of ads.
    """
    values: list[dict] = []
    promos: list[dict] = []
    works, vent = public_works(), ventures()
    for r in range(rounds):
        for w in works:
            p = work_posts(w, r)
            if p["id"] not in used:
                values.append(p)
        for v in vent:
            p = venture_posts(v)
            if p["id"] not in used:
                promos.append(p)
    out: list[dict] = []
    vi = pi = 0
    while vi < len(values) or pi < len(promos):
        for _ in range(2):
            if vi < len(values):
                out.append(values[vi])
                vi += 1
        if pi < len(promos):
            out.append(promos[pi])
            pi += 1
    return out


# --------------------------------------------------------------------------- cards
def render_cards(post: dict) -> list[Path]:
    """Render the wide and pin cards for one post, in the seed cards' style."""
    import social_cards
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    made = []
    card_post = {"headline": post["headline"], "body": post.get("card_body", ""),
                 "kicker": post.get("kicker", "HARARE · SINCE 2026")}
    for shape, suffix in (("wide", ""), ("pin", "-pin")):
        im = social_cards.render(card_post, shape)
        path = CARDS_DIR / f"{post['card_id']}{suffix}.png"
        from PIL import Image
        im.quantize(colors=200, method=Image.MEDIANCUT, dither=Image.FLOYDSTEINBERG) \
          .save(path, optimize=True)
        made.append(path)
    return made


# --------------------------------------------------------------------------- bank
def load() -> list[dict]:
    if BANK_FILE.exists():
        try:
            return json.loads(BANK_FILE.read_text())
        except Exception:
            return []
    return []


def save(bank: list[dict]) -> None:
    BANK_FILE.write_text(json.dumps(bank, indent=1, ensure_ascii=False) + "\n")


def seed_ids() -> set[str]:
    import press
    return {p["id"] for p in press.SEED}


def unposted(bank: list[dict]) -> list[dict]:
    import press
    sent = set(press.load_state().get("sent", []))
    return [p for p in bank if p["id"] not in sent]


def refill(keep_ahead: int = 3, quiet: bool = False) -> list[dict]:
    """Top the bank up until at least `keep_ahead` unposted generated posts wait behind the cursor."""
    bank = load()
    used = seed_ids() | {p["id"] for p in bank}
    waiting = unposted(bank)
    added: list[dict] = []
    if len(waiting) >= keep_ahead:
        if not quiet:
            print(f"bank is {len(waiting)} ahead — nothing to do")
        return added
    pool = candidates(used)
    if not pool:
        if not quiet:
            print("no unused sources left: every public work and every venture has been posted. "
                  "Write new seed posts in press.py.", file=sys.stderr)
        return added
    # draw in value, value, promo order while the pool allows it
    want = max(0, keep_ahead - len(waiting))
    i = 0
    while len(added) < want and i < len(pool):
        pick = pool[i]
        i += 1
        # never two promos back to back
        tail = (bank + added)[-1]["kind"] if (bank + added) else "value"
        if pick["kind"] == "promo" and tail == "promo":
            continue
        pick = dict(pick)
        pick["card"] = f"{CARDS}/{pick['card_id']}.png"
        pick.pop("card_id", None)
        render_cards({**pick, "card_id": Path(pick["card"]).stem})
        added.append(pick)
        if not quiet:
            print(f"  + {pick['id']:<32}{pick['kind']:<6}{len(pick['text'])} chars  {pick['card']}")
    if added:
        bank.extend(added)
        save(bank)
        if not quiet:
            print(f"  {len(added)} new post(s) → {BANK_FILE.relative_to(ROOT)}")
    return added


# --------------------------------------------------------------------------- checks
def selftest() -> int:
    import press
    problems = []
    bank = load()
    ids = [p["id"] for p in press.SEED] + [p["id"] for p in bank]
    if len(ids) != len(set(ids)):
        problems.append("duplicate post id across seed and generated bank")
    private = {w["id"] for w in json.loads((ROOT / "data" / "works.json").read_text()) if not w.get("read")}
    for p in bank:
        if not p.get("card", "").startswith("https://"):
            problems.append(f"{p['id']}: no card")
        total = len(p["text"]) + (len(p.get("link", "")) + 2 if p.get("link") else 0)
        if total > SKY_LIMIT:
            problems.append(f"{p['id']}: {total} chars with its link — over Bluesky's {SKY_LIMIT}")
        if p["kind"] not in ("value", "promo"):
            problems.append(f"{p['id']}: bad kind {p['kind']}")
        if not p.get("headline"):
            problems.append(f"{p['id']}: no card headline")
        if p.get("work") in private:
            problems.append(f"{p['id']}: names a private author-review edition — not publishable")
        card = CARDS_DIR / (p["card"].rsplit("/", 1)[-1])
        if not card.exists():
            problems.append(f"{p['id']}: card file missing ({card.name})")
        if p["kind"] == "promo" and not p.get("link"):
            problems.append(f"{p['id']}: promo with nothing to click")
    kinds = [p["kind"] for p in press.BANK]
    for i in range(len(kinds) - 2):
        if kinds[i:i + 3].count("value") < 2:
            problems.append(f"window at {i} is {kinds[i:i+3]} — breaks 2 value : 1 promo")
    for i, k in enumerate(kinds):
        if k == "promo" and i and kinds[i - 1] == "promo":
            problems.append(f"two promos back to back at {i}")
    print(f"generated bank: {len(bank)} posts · {kinds.count('value')} value · {kinds.count('promo')} promo")
    for p in problems:
        print("  ✗", p)
    print("  ✓ clean" if not problems else f"  {len(problems)} problem(s)")
    return 0 if not problems else 1


def plan() -> int:
    import press
    bank = load()
    sent = set(press.load_state().get("sent", []))
    left = [p for p in bank if p["id"] not in sent]
    print(f"seed posts:      {len(press.SEED)}  ({sum(1 for p in press.SEED if p['id'] not in sent)} unposted)")
    print(f"generated bank:  {len(bank)}  ({len(left)} unposted)")
    days = (sum(1 for p in press.SEED if p['id'] not in sent) + len(left)) * press.CADENCE_HOURS / 24
    print(f"runway at {press.CADENCE_HOURS}h: {days:.0f} days")
    for p in left[:5]:
        print(f"  {p['id']:<32}{p['kind']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="top up the press bank from the site's own data")
    ap.add_argument("--ensure", type=int, default=3, metavar="N",
                    help="keep at least N unposted generated posts waiting (default 3)")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.plan:
        return plan()
    if a.selftest:
        return selftest()
    refill(a.ensure)
    return 0


if __name__ == "__main__":
    sys.exit(main())
