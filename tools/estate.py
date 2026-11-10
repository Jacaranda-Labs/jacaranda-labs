#!/usr/bin/env python3
"""The state of the estate, on one screen, in about two seconds.

The operating manual says the day's loop is one command. This is the command. It reads what the
estate already records about itself — the press state, the refilled bank, the venture catalogue, the
git history — and the one file a human maintains (data/ops.json). It never asks for a credential and
never touches a secret: a dashboard that needs the keys is a dashboard you will not run on a phone.

    python3 tools/estate.py             # the daily screen
    python3 tools/estate.py --check     # also fetch the public site and the card address
    python3 tools/estate.py --brief     # the same, as four lines, for a Sunday-evening skim

Exit codes: 0 nothing is on fire · 1 something needs a human today.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAIL = ROOT / "rails" / "jacaranda"

V = "\033[38;5;141m"
DIM = "\033[2m"
BOLD = "\033[1m"
RED = "\033[38;5;203m"
AMBER = "\033[38;5;215m"
GREEN = "\033[38;5;114m"
OFF = "\033[0m"


def paint(s: str, colour: str, on: bool) -> str:
    return f"{colour}{s}{OFF}" if on else s


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return ""


def hours_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        then = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (dt.datetime.now(dt.timezone.utc) - then).total_seconds() / 3600


def head(colour: str, title: str, on: bool) -> None:
    print(paint(f"\n {title}", colour, on))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="also fetch the public site and a card")
    ap.add_argument("--brief", action="store_true", help="four lines, nothing else")
    ap.add_argument("--no-colour", action="store_true")
    a = ap.parse_args()
    on = sys.stdout.isatty() and not a.no_colour

    ops = read_json(ROOT / "data" / "ops.json", {})
    ventures = read_json(ROOT / "data" / "ventures.json", [])
    works = read_json(ROOT / "data" / "works.json", [])
    state = read_json(RAIL / "press-state.json", {})
    bank = read_json(RAIL / "bank.json", [])

    sent = state.get("sent", [])
    last_at = state.get("last_at")
    since = hours_since(last_at)
    cadence = 30.0
    try:
        sys.path.insert(0, str(RAIL))
        import press  # noqa: E402  — the rail owns the cadence constant
        cadence = float(press.CADENCE_HOURS)
        total_posts = len(press.SEED) + len(bank)
    except Exception:
        total_posts = len(bank) + 12
    run_days = max(0, total_posts - len(sent)) * cadence / 24
    if since is None:
        due_in = 0.0
    else:
        due_in = max(0.0, cadence - since)

    actions = [x for x in ops.get("owner_actions", []) if not x.get("done")]
    decisions = ops.get("decisions", [])
    money = ops.get("money", {})
    blocked = [x for x in actions if x.get("blocks")]

    # ---------------------------------------------------------------- the one thing
    if blocked:
        one = blocked[0]
        headline = f"{one['what']} — {one.get('minutes', '?')} min, unblocks {one['blocks']}"
        alarm = True
    elif decisions:
        headline = f"Decide: {decisions[0]['question']}"
        alarm = True
    elif due_in <= 0:
        headline = "Nothing. The rail is due and will post by itself."
        alarm = False
    else:
        headline = "Nothing. The estate is running."
        alarm = False

    if a.brief:
        print(f"estate: {headline}")
        print(f"press:  {len(sent)} posted · next in {due_in:.0f}h · {run_days:.0f} days of bank")
        print(f"loops:  {len(actions)} owner action(s) · {len(decisions)} decision(s) waiting")
        print(f"money:  MRR {money.get('mrr') if money.get('mrr') is not None else '—'} · "
              f"cash {money.get('cash') if money.get('cash') is not None else '—'}")
        return 1 if alarm else 0

    print(paint("\n " + "─" * 66, DIM, on))
    print(paint("  JACARANDA LABS · state of the estate · ", DIM, on)
          + paint(dt.datetime.now().strftime("%a %d %b %H:%M"), DIM, on))
    print(paint(" " + "─" * 66, DIM, on))

    head(RED if alarm else GREEN, "THE ONE THING" + ("" if alarm else "  (nothing to do)"), on)
    print(f"   {paint(headline, BOLD if alarm else DIM, on)}")
    if len(actions) > 1:
        print(paint(f"   then, when you feel like it: {len(actions) - 1} more in data/ops.json", DIM, on))

    # ---------------------------------------------------------------- press
    head(V, "PRESS", on)
    print(f"   posted {len(sent)} · next in {due_in:.0f}h · bank {len(bank)} generated, "
          f"{run_days:.0f} days at {cadence:.0f}h")
    if run_days < 14:
        print(paint(f"   ! bank runs dry in {run_days:.0f} days — one new seed post, or accept a pause", AMBER, on))

    rails = ["bluesky", "mastodon", "nostr", "pinterest", "tumblr"]
    armed = [r for r in rails if {
        "bluesky": "JACARANDA_BSKY_ID", "mastodon": "JACARANDA_MASTODON_TOKEN",
        "nostr": "JACARANDA_NOSTR_NSEC", "pinterest": "JACARANDA_BUFFER_TOKEN",
        "tumblr": "JACARANDA_TUMBLR_TOKEN"}[r] in os.environ]
    extra = []
    for var, name in (("JACARANDA_DISCORD_WEBHOOK", "discord"), ("JACARANDA_REDDIT_CID", "reddit")):
        extra.append(f"{name} {'armed' if os.environ.get(var) else 'waiting'}")
    print(paint(f"   credentials in this shell: {', '.join(armed) or 'none'} · "
                f"{' · '.join(extra)} · medium+quora write drafts", DIM, on))
    if not armed:
        print(paint("   (no rail credentials in this shell — in CI they are repository secrets)", DIM, on))

    # ---------------------------------------------------------------- front doors
    head(V, "FRONT DOORS", on)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("uptime", ROOT / "tools" / "uptime.py")
        up = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(up)
        conf = json.loads((ROOT / "data" / "uptime.json").read_text())
        results = [up.check(c) for c in conf["checks"] if c.get("kind") == "product"]
        bad = [r for r in results if not r["ok"]]
        if bad:
            for r in bad:
                print(paint(f"   DOWN {r['name']:<20}{r['why'][:56]}", RED, on))
        else:
            print(paint(f"   all {len(results)} product pages answer 200 HTML", GREEN, on))
    except Exception as exc:                                       # noqa: BLE001
        print(paint(f"   check unavailable ({type(exc).__name__}) — run tools/uptime.py", DIM, on))

    # ---------------------------------------------------------------- the offer
    head(V, "WHAT IS FOR SALE", on)
    for v in ventures:
        price = v.get("from") or "free"
        print(f"   {v['name']:<18}{price:>6}   {paint((v.get('line') or '')[:46], DIM, on)}")
    print(paint(f"   {len(works)} works catalogued · "
                f"{sum(1 for w in works if w.get('read'))} readable free", DIM, on))

    # ---------------------------------------------------------------- money
    head(V, "MONEY", on)
    if all(money.get(k) is None for k in ("cash", "mrr", "monthly_costs")):
        print(paint("   not recorded. Open data/ops.json once and put three numbers in it — "
                    "cash, MRR, monthly costs.", AMBER, on))
        print(paint("   A business without those three numbers is a mood, not an operation.", DIM, on))
    else:
        for k, label in (("cash", "cash"), ("mrr", "MRR"), ("monthly_costs", "costs/mo")):
            val = money.get(k)
            print(f"   {label:<10}{'—' if val is None else val}")
        if money.get("next_bill"):
            print(f"   next bill {money['next_bill']}")

    # ---------------------------------------------------------------- loops
    head(V, "OPEN LOOPS", on)
    if not actions and not decisions:
        print(paint("   none. Close the laptop.", GREEN, on))
    for x in actions:
        print(f"   [ ] {x['what'][:64]:<66}{str(x.get('minutes', '?')) + ' min':>7}")
        print(paint(f"       because: {x.get('why', '')[:80]}", DIM, on))
    for d in decisions:
        print(f"   [?] {d['question'][:66]}")
        print(paint(f"       if you do nothing: {d.get('default', '')[:76]}", DIM, on))

    # ---------------------------------------------------------------- last commits
    log = git("log", "--oneline", "-3", "--format=%h %s").split("\n") if git("rev-parse", "--git-dir") else []
    if log and log[0]:
        head(V, "LAST CHANGES", on)
        for line in log:
            print(paint(f"   {line[:88]}", DIM, on))

    if a.check:
        head(V, "THE ADDRESS A READER USES", on)
        for url in ("https://jacaranda-labs.pages.dev/",
                    "https://jacaranda-labs.pages.dev/assets/cards/method.png"):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Jacaranda estate check"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    print(f"   OK   {resp.status}  {url}")
            except urllib.error.HTTPError as e:
                print(paint(f"   FAIL {e.code}  {url}", RED, on))
            except Exception as e:                                    # noqa: BLE001
                print(paint(f"   FAIL {type(e).__name__}  {url}", RED, on))

    print(paint("\n " + "─" * 66, DIM, on))
    print(paint("  The loop is over when this prints. Closing the laptop is part of the method.",
                DIM, on))
    print(paint(" " + "─" * 66 + "\n", DIM, on))
    return 1 if alarm else 0


if __name__ == "__main__":
    sys.exit(main())
