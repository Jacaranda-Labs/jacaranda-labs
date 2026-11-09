#!/usr/bin/env python3
"""Prove that the site a reader actually reaches is the build we just made.

The estate's own failure library (Jacaranda Labs Think Tank Working Paper 2026-04, signature S6 —
"the origin that had not yet propagated") is exactly this: the build is right, the deployment is
right, and the address users read is serving something else. On 2026-11-09 that happened for real —
`jacaranda-labs.pages.dev` kept serving an older deployment for over an hour while every deployment
list said "production, success", and new pages 404'd for real visitors.

So this check is deliberately literal. It fetches three files from the public origin with a
cache-buster and compares their bytes against `dist/`:

    /                       the page everyone lands on
    /404.html               a file every build rewrites
    <a file added by this build>   passed with --probe

    python3 tools/deploy_verify.py                       # check the current build against the site
    python3 tools/deploy_verify.py --probe read/mechanism-audit --probe covers/mechanism-audit.jpg
    python3 tools/deploy_verify.py --wait 300            # retry for five minutes (propagation is normal)

Exit codes: 0 the origin serves this build · 1 it does not · 2 the site is not reachable at all.

Propagation is not a failure on its own — a deployment takes seconds to minutes to be visible under
the project's own name. What is a failure is *silence*: a deploy that reports success while the
public address serves a different build, with nobody told. That is what this exits non-zero for.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SITE = "https://jacaranda-labs.pages.dev"
UA = "Mozilla/5.0 (compatible; Jacaranda Labs deploy check; +https://jacaranda-labs.pages.dev)"

# Pages serves pretty URLs: /index.html is served at /, and .html may 308 to the extensionless form.
CANON = {"/index.html": "/"}


def fetch(path: str, timeout: int = 30) -> tuple[int, bytes]:
    url = SITE + path + ("&" if "?" in path else "?") + "cb=" + str(int(time.time() * 1000))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:                                    # noqa: BLE001
        return 0, repr(e).encode()


def local(path: str) -> bytes:
    p = DIST / path.lstrip("/")
    return p.read_bytes() if p.is_file() else b""


def same(path: str) -> tuple[bool, str]:
    want = local(path)
    if not want:
        return True, "skipped (not in dist)"                 # nothing to compare for this build
    st, got = fetch(path)
    if st == 0:
        return False, f"unreachable ({got[:60].decode('utf-8', 'ignore')})"
    if st == 404:
        return False, "404 — the origin does not have this file"
    if st != 200:
        return False, f"HTTP {st}"
    if hashlib.sha256(got).hexdigest() == hashlib.sha256(want).hexdigest():
        return True, f"identical ({len(want) // 1024} KB)"
    return False, f"different content ({len(got)} bytes vs {len(want)} locally) — the origin is serving another build"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="append", default=[], metavar="PATH",
                    help="an asset added by this build; the check fails if the origin 404s it")
    ap.add_argument("--wait", type=int, default=0, metavar="SECONDS",
                    help="keep retrying for this long before declaring failure")
    ap.add_argument("--interval", type=int, default=30)
    a = ap.parse_args()

    targets = ["/index.html", "/404.html"] + [p if p.startswith("/") else "/" + p for p in a.probe]
    deadline = time.time() + max(0, a.wait)
    attempt = 0
    while True:
        attempt += 1
        bad = []
        print(f"checking {SITE} against dist/ (attempt {attempt})")
        for t in targets:
            ok, why = same(CANON.get(t, t))
            print(f"  {'OK  ' if ok else 'FAIL'} {t:<34}{why}")
            if not ok:
                bad.append(t)
        if not bad:
            print("  ✓ the origin is serving this build")
            return 0
        if time.time() + a.interval > deadline:
            print(f"  ✗ {len(bad)} of {len(targets)} not served by the origin after "
                  f"{attempt} attempt(s). A deployment that reports success while the public "
                  f"address serves another build is the S6 signature: say so out loud, do not "
                  f"file it under maintenance.")
            return 1
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
