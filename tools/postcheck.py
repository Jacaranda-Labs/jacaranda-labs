#!/usr/bin/env python3
"""postcheck — does every post carry an image, and is the value:promo ratio honest?

Two owner rules, checked against the platforms themselves rather than against our own logs:

  1. Every post carries an image.
  2. Value posts outnumber promo posts at least 2:1 over the trailing window.

    python3 tools/postcheck.py                # audit every configured identity
    python3 tools/postcheck.py --only op      # one identity
    python3 tools/postcheck.py --strict       # exit 1 on any violation (default)
    python3 tools/postcheck.py --no-strict     # report only
    python3 tools/postcheck.py --markdown      # the report as a table, for a PR or a note
    python3 tools/postcheck.py --selftest      # no network

Classification is a heuristic and says so. A post is *promo* when it names the venture and asks the
reader for something - an invitation ("try it", "start free", "sign up", "no card") or a link to the
venture's own door (brand_hosts in identity.json). Naming the product is not enough: our products are
the subject of most of what we write, and a topic word is not a brand. Everything else is *value*.
`tools/identity.json` carries manual overrides when the heuristic is wrong — `"promo_ids": [...]` and
`"value_ids": [...]` by platform post id.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "identity.json"
UA = "jacaranda-postcheck/1.0 (+https://jacaranda-labs.pages.dev)"
TIMEOUT = 25
WINDOW = 12          # posts per identity in the ratio
MIN_RATIO = 2.0      # value posts per promo post

CTA = re.compile(
    r"\b(try|start|begin|sign ?up|join|open|claim|get|buy|book|free|subscribe|download|"
    r"available now|new|launch(?:ed|ing)?)\b", re.I)

# 2026-11-14: the rule for a promo is "it names the product AND asks the reader for something".
# The old implementation used one broad regex that contained topic words (open, free, new, get),
# so a DeskOS weekly roundup ("35 public contracts in Ukraine close... 96 open in all") and a
# Tapstall market note ("the same $10 payment costs about $0.34") were both scored as promos. The
# audit then reported 5-6 promos in a row for feeds that were mostly data posts, which is the
# opposite failure of a silenced audit: a wrongly red build nobody can trust either.
#
# ASK is the actual ask: an invitation addressed to the reader, or the product's own door.
ASK = re.compile(
    r"(\btry it\b|\btry (the|our|a)\b|\bget started\b|\bsign ?up\b|\bjoin (free|us|today)\b"
    r"|\bclaim\b|\bbook a\b|\bbuy\b|\bavailable now\b|\bfree for \d+ days\b|\bno card\b"
    r"|\bdownload the\b|\binstall the\b|\b(run|take|open) a free\b|\bfree (audit|scan|version|plan) (on|for)\b"
    r"|\bopen your own\b|\bget your (own|free)\b|\bstart (today|now|free|your)\b)",
    re.I)
# "Try <product> ..." is an ask even though the verb is not in the list above, and so is a bare
# "free" next to the product in the first line: those are how a short promo actually opens.
ASK_NEAR_BRAND = re.compile(r"\b(try|start|join|open)\b[^.\n]{0,40}$", re.I)


LINKED = re.compile(r"https?://(?:www\.)?([a-z0-9.-]+)", re.I)


# --------------------------------------------------------------------------- model
@dataclass
class Post:
    id: str
    platform: str
    at: str
    text: str
    has_image: bool
    image_kind: str = ""      # "media" | "embed" | "pin" | "imeta" | "card" | ""
    url: str = ""
    label: str = ""           # "value" | "promo" | ""

    @property
    def kind(self) -> str:
        return self.label or classify(self.text)


def classify(text: str, markers: list[str] | None = None, brand_hosts: list[str] | None = None) -> str:
    """promo = it names the product AND asks the reader for something.

    Naming the product is not enough: our products are the subject of most of what we write. The
    ask is what makes a post a promo - an invitation, or a link to the product's own door.
    """
    t = text or ""
    markers = [m for m in (markers or []) if m]
    names = any(m.lower() in t.lower() for m in markers)
    if not names:
        return "value"
    hosts = [h.lower() for h in (brand_hosts or [])]
    linked = [m.group(1).lower() for m in LINKED.finditer(t)]
    own_link = any(any(h and (host == h or host.endswith("." + h)) for h in hosts) for host in linked)
    if own_link or ASK.search(t):
        return "promo"
    # "...Try Open Practice this week": the verb sits immediately before the product's own name.
    first = t.splitlines()[0] if t else ""
    for m in markers:
        idx = first.lower().find(m.lower())
        if idx > 0 and ASK_NEAR_BRAND.search(first[:idx]):
            return "promo"
    return "value"


# --------------------------------------------------------------------------- platforms
def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def fetch_bluesky(ident: dict, n: int) -> list[Post]:
    desc = json.loads(_get("https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle="
                           + urllib.parse.quote(ident["handle"])))
    did = desc["did"]
    feed = json.loads(_get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
                           f"?actor={did}&limit={min(n, 50)}&filter=posts_no_replies"))
    out = []
    for item in feed.get("feed", []):
        if item.get("reason"):          # reposts are not ours to judge
            continue
        p = item["post"]
        rec = p["record"]
        embed = rec.get("embed") or {}
        emb = embed.get("$type", "")
        # a link card with a thumbnail is an image on the post: DeskOS and the other presses all
        # publish through that path, and counting only `images[]` reported them as text-only.
        thumb = bool((embed.get("external") or {}).get("thumb"))
        has_img = "images" in emb or thumb
        out.append(Post(
            id=p["uri"].rsplit("/", 1)[-1], platform="bluesky", at=p["indexedAt"][:16],
            text=rec.get("text", ""), has_image=has_img,
            image_kind=("images" if "images" in emb else "thumb") if has_img else "",
            url=f"https://bsky.app/profile/{ident['handle']}/post/{p['uri'].rsplit('/', 1)[-1]}",
        ))
    return out


def fetch_mastodon(ident: dict, n: int) -> list[Post]:
    inst = ident.get("instance", "mastodon.social")
    acct = json.loads(_get(f"https://{inst}/api/v1/accounts/lookup?acct={ident['handle']}"))
    st = json.loads(_get(f"https://{inst}/api/v1/accounts/{acct['id']}/statuses"
                         f"?limit={min(n, 40)}&exclude_replies=true&exclude_reblogs=true"))
    out = []
    for p in st:
        media = len(p.get("media_attachments") or [])
        out.append(Post(
            id=str(p["id"]), platform="mastodon", at=p["created_at"][:16],
            text=re.sub(r"<[^>]+>", "", p.get("content", "")),
            has_image=media > 0, image_kind="media" if media else ("card" if p.get("card") else ""),
            url=p.get("url", ""),
        ))
    return out


def fetch_nostr(ident: dict, n: int) -> list[Post]:
    """Kind-1 notes by this key, read back off the relays. Needs websocket-client."""
    try:
        import websocket  # type: ignore
    except ImportError:
        raise RuntimeError("websocket-client not installed (pip install websocket-client)")
    ch = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

    def bech32_to_hex(s: str) -> str:
        data = [ch.index(c) for c in s.split("1", 1)[1]][:-6]
        acc = bits = 0
        out = bytearray()
        for v in data:
            acc = (acc << 5) | v
            bits += 5
            while bits >= 8:
                bits -= 8
                out.append((acc >> bits) & 0xFF)
        return bytes(out).hex()

    pk = bech32_to_hex(ident["npub"]) if ident["npub"].startswith("npub") else ident["npub"]
    if len(pk) != 64:
        raise ValueError(f"npub does not decode to a 32-byte public key (got {len(pk) // 2} bytes)")
    out: list[Post] = []
    for relay in ident.get("relays") or ["wss://relay.nostr.net", "wss://relay.primal.net"]:
        try:
            ws = websocket.create_connection(relay, timeout=15)
            ws.send(json.dumps(["REQ", "pc", {"authors": [pk], "kinds": [1], "limit": n}]))
            while True:
                m = json.loads(ws.recv())
                if m[0] == "EVENT":
                    ev = m[2]
                    tags = ev.get("tags") or []
                    imeta = any(t and t[0] == "imeta" for t in tags)
                    out.append(Post(
                        id=ev["id"], platform="nostr:" + relay.split("//")[1].split("/")[0],
                        at=str(ev["created_at"]), text=ev.get("content", ""),
                        has_image=imeta, image_kind="imeta" if imeta else "",
                        url="https://njump.me/" + ev["id"]))
                if m[0] in ("EOSE", "CLOSED", "NOTICE"):
                    break
            ws.close()
        except Exception as exc:                      # one dead relay must not kill the audit
            out.append(Post(id="", platform="nostr:" + relay.split("//")[1].split("/")[0],
                            at="", text="", has_image=False,
                            image_kind="", url="", label="__relay_error__:" + type(exc).__name__))
    seen, uniq = set(), []
    for p in out:
        if p.id and p.id in seen:
            continue
        seen.add(p.id)
        uniq.append(p)
    return uniq


FETCHERS = {"bluesky": fetch_bluesky, "mastodon": fetch_mastodon, "nostr": fetch_nostr}


# --------------------------------------------------------------------------- the two rules
@dataclass
class Verdict:
    ident: str
    platform: str
    posts: list[Post] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    error: str = ""
    legacy: list = field(default_factory=list)   # published before this identity had a rail
    note: str = ""

    @property
    def n(self) -> int:
        return len([p for p in self.posts if p.kind in ("value", "promo")])

    @property
    def promo(self) -> int:
        return len([p for p in self.posts if p.kind == "promo"])

    @property
    def value(self) -> int:
        return len([p for p in self.posts if p.kind == "value"])

    @property
    def with_image(self) -> int:
        return len([p for p in self.posts if p.has_image and p.kind in ("value", "promo")])

    @property
    def ratio(self) -> float:
        return (self.value / self.promo) if self.promo else float("inf")

    @property
    def ok(self) -> bool:
        return not self.error and not self.problems


def _epoch(stamp: str) -> int:
    """A post's time as an epoch second. Bluesky/Mastodon posts carry ISO text, Nostr an epoch."""
    try:
        return int(float(stamp))
    except (TypeError, ValueError):
        pass
    from datetime import datetime, timezone
    s = str(stamp).replace("Z", "+00:00")
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except ValueError:
        return 0


def judge(ident: dict, posts: list[Post], window: int = WINDOW) -> Verdict:
    v = Verdict(ident=ident["name"], platform=ident["platform"])
    relay_errors = [p for p in posts if p.label.startswith("__relay_error__")]
    posts = [p for p in posts if not p.label.startswith("__relay_error__")]
    if relay_errors and not posts:
        v.error = ("no relay answered (" + ", ".join(p.label.split(":", 1)[1] for p in relay_errors) + ")")
        return v
    if not posts:
        v.error = "no posts found — the identity is not publishing, or the key is wrong"
        return v

    posts = sorted(posts, key=lambda p: p.at, reverse=True)[:window]

    # Posts written before this identity had a rail are history, not a live breach: nothing can
    # retro-fit an image onto them, and a build that stays red forever is a build nobody reads.
    # They are still listed, with URLs, so they can be deleted — they just do not fail the run.
    since = ident.get("rail_since")
    legacy: list[Post] = []
    if since:
        cutoff = _epoch(since)
        legacy = [p for p in posts if _epoch(p.at) < cutoff]
        posts = [p for p in posts if _epoch(p.at) >= cutoff]
    v.legacy = legacy
    if not posts:
        v.note = (f"nothing published since the rail went live ({since}); "
                  f"{len(legacy)} older post(s) are history, not a breach")
        return v
    for p in posts:                                   # manual overrides win over the heuristic
        if p.id and p.id in (ident.get("promo_ids") or []):
            p.label = "promo"
        elif p.id and p.id in (ident.get("value_ids") or []):
            p.label = "value"
        elif ident.get("markers"):
            p.label = classify(p.text, ident["markers"], ident.get("brand_hosts"))
    v.posts = posts

    # rule 1 — every post carries an image
    bare = [p for p in posts if not p.has_image]
    if bare:
        v.problems.append(f"{len(bare)} of {len(posts)} posts carry no image "
                          f"(most recent: {bare[0].at} {bare[0].url or '(no url)'})")

    # rule 2 — value outnumbers promo at least 2:1.
    # Not judged on a two-post window: 1 value + 1 promo is a 1:1 ratio that says nothing, and a
    # press that posted twice today should not be called a failure for it.
    if len(posts) >= 3 and v.promo and (v.value / v.promo) < MIN_RATIO:
        v.problems.append(f"value:promo is {v.value}:{v.promo} over the last {len(posts)} posts, "
                          f"needs at least {int(MIN_RATIO)}:1")
    # a run of promos is a violation even if the window average looks fine
    run = best = 0
    for p in reversed(posts):
        run = run + 1 if p.kind == "promo" else 0
        best = max(best, run)
    if best >= 3:
        v.problems.append(f"{best} promo posts in a row")
    return v


# --------------------------------------------------------------------------- report
def render(results: list[Verdict], markdown: bool = False) -> str:
    if markdown:
        lines = ["| identity | platform | posts | with image | value | promo | value:promo | legacy | verdict |",
                 "|---|---|---|---|---|---|---|---|---|"]
        for v in results:
            if v.error:
                lines.append(f"| {v.ident} | {v.platform} | — | — | — | — | — | — | **{v.error}** |")
                continue
            ratio = "∞" if v.promo == 0 else f"{v.ratio:.1f}:1"
            mark = "pass" if v.ok else "**fail**"
            lines.append(f"| {v.ident} | {v.platform} | {v.n} | {v.with_image}/{v.n} | {v.value} | "
                         f"{v.promo} | {ratio} | {len(v.legacy)} | {mark} |")
        hist = [v for v in results if v.legacy]
        if hist:
            lines += ["", "**History (pre-rail, not enforced)**", ""]
            lines += [f"- {v.ident}: {len(v.legacy)} post(s), "
                      f"{sum(1 for p in v.legacy if not p.has_image)} without an image" for v in hist]
        fails = [p for v in results for p in v.problems]
        errs = [f"{v.ident}: {v.error}" for v in results if v.error]
        if fails or errs:
            lines += ["", "**Problems**", ""]
            lines += [f"- {x}" for x in errs + fails]
        return "\n".join(lines)

    out = []
    w = 26
    out.append(f"{'identity':<{w}} {'platform':<14} {'posts':>5} {'image':>6} {'val':>4} {'promo':>5} {'ratio':>7}  verdict")
    out.append("-" * 92)
    for v in results:
        if v.error:
            out.append(f"{v.ident:<{w}} {v.platform:<14} {'—':>5} {'—':>6} {'—':>4} {'—':>5} {'—':>7}  ERROR {v.error}")
            continue
        ratio = "inf" if v.promo == 0 else f"{v.ratio:.1f}:1"
        out.append(f"{v.ident:<{w}} {v.platform:<14} {v.n:>5} {str(v.with_image) + '/' + str(v.n):>6} "
                   f"{v.value:>4} {v.promo:>5} {ratio:>7}  {'PASS' if v.ok else 'FAIL'}")
    if any(v.posts for v in results):
        out.append("")
        for v in results:
            if not v.posts:
                continue
            out.append(f"{v.ident} — last {len(v.posts)} posts")
            for p in v.posts:
                out.append(f"   {p.at:<12} {p.kind:<5} img={'yes' if p.has_image else 'NO ':<3} "
                           f"{p.text[:64].replace(chr(10), ' ')}")
    legacy = [v for v in results if v.legacy]
    if legacy:
        out.append("")
        out.append("HISTORY — published before the rail was in code, reported but not enforced")
        for v in legacy:
            out.append(f"{v.ident} — {len(v.legacy)} post(s)")
            for p in v.legacy[-6:]:
                out.append(f"   {p.at:<12} img={'yes' if p.has_image else 'NO ':<3} {p.text[:56]}")
                if not p.has_image and p.url:
                    out.append(f"   {'':<12} delete: {p.url}")

    problems = [f"{v.ident}: {v.error}" for v in results if v.error]
    problems += [f"{v.ident}: {p}" for v in results for p in v.problems]
    out.append("")
    if problems:
        out.append("PROBLEMS")
        out += ["  ✗ " + p for p in problems]
    else:
        out.append("✓ every identity passes both rules")
    return "\n".join(out)


# --------------------------------------------------------------------------- selftest
def selftest() -> int:
    markers = ["open practice", "open-practice"]
    cases = [
        ("You have watched enough tutorials. Today, build something real. 86 activities. Free, no signup. open-practice.workers.dev", "promo"),
        ("The part most courses skip: what done looks like. Every activity ships a checklist.", "value"),
        ("A practice record is not a certificate, and that is the point.", "value"),
        ("Try Open Practice this week — open for everyone.", "promo"),
    ]
    bad = 0
    for text, want in cases:
        got = classify(text, markers)
        if got != want:
            print(f"  ✗ classify({text[:40]!r}) → {got}, expected {want}", file=sys.stderr)
            bad += 1
    posts = [Post(id=str(i), platform="bluesky", at=f"2026-11-0{i+1}T00:00", text="",
                  has_image=(i != 3), label="promo" if i == 1 else "value") for i in range(6)]
    v = judge({"name": "t", "platform": "bluesky", "markers": []}, posts)
    if v.ok:
        print("  ✗ a post without an image did not fail the audit", file=sys.stderr)
        bad += 1
    promo_heavy = [Post(id=str(i), platform="x", at=f"2026-11-0{i+1}T00:00", text="",
                        has_image=True, label="promo" if i % 2 else "value") for i in range(6)]
    if judge({"name": "t", "platform": "x"}, promo_heavy).ok:
        print("  ✗ a 3:3 value:promo feed did not fail the ratio rule", file=sys.stderr)
        bad += 1
    print(f"  {'✓' if not bad else '✗'} selftest: {len(cases) + 2 - bad}/{len(cases) + 2} checks")
    return 1 if bad else 0


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="substring of an identity name or key")
    ap.add_argument("--window", type=int, default=WINDOW)
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--strict", dest="strict", action="store_true", default=True)
    ap.add_argument("--no-strict", dest="strict", action="store_false")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    idents = cfg["identities"]
    if args.only:
        idents = [i for i in idents if args.only.lower() in (i["key"] + " " + i["name"]).lower()]
        if not idents:
            print(f"no identity matches {args.only!r}", file=sys.stderr)
            return 2

    results = []
    for ident in idents:
        fetch = FETCHERS[ident["platform"]]
        try:
            results.append(judge(ident, fetch(ident, args.window), args.window))
        except Exception as exc:
            results.append(Verdict(ident=ident["name"], platform=ident["platform"],
                                   error=f"{type(exc).__name__}: {exc}"))

    print(render(results, markdown=args.markdown))
    if not args.strict:
        return 0
    return 0 if all(v.ok for v in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
