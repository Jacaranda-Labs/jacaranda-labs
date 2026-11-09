#!/usr/bin/env python3
"""ask — tell the indexes we exist.

Google has no public way to submit a URL without Search Console, but Bing, Yandex, Seznam and Naver
all accept IndexNow, and Bing's index is what Copilot and a large share of answer engines quote. So
the one push we can make without an account is the one worth making.

    python3 tools/ask.py --urls            # every URL in the sitemap
    python3 tools/ask.py --page /about/    # one page, after an edit
    python3 tools/ask.py --urls --dry

The key is generated in build.py (INDEXNOW_KEY) and served at /<key>.txt. It is public by design:
its only job is to prove the ping came from someone who controls the host.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

SITE = "https://jacaranda-labs.pages.dev"
ENDPOINT = "https://api.indexnow.org/indexnow"


def key() -> str:
    src = open("build.py", encoding="utf-8").read()
    m = re.search(r'INDEXNOW_KEY\s*=\s*"([0-9a-f]{8,})"', src)
    if not m:
        raise SystemExit("no INDEXNOW_KEY in build.py")
    return m.group(1)


def urls() -> list[str]:
    sm = open("dist/sitemap.xml", encoding="utf-8").read()
    return re.findall(r"<loc>([^<]+)</loc>", sm)


def ping(batch: list[str], dry: bool = False) -> int:
    k = key()
    # the key file must already be live, or the ping is rejected — check before claiming success
    try:
        live = urllib.request.urlopen(f"{SITE}/{k}.txt", timeout=20).read().decode().strip()
    except Exception as e:                                  # noqa: BLE001
        print(f"✗ key file is not live at {SITE}/{k}.txt ({e}) — deploy first")
        return 2
    if live != k:
        print("✗ the key file live at the site is not the key in build.py — deploy first")
        return 2

    payload = {"host": "jacaranda-labs.pages.dev", "key": k,
               "keyLocation": f"{SITE}/{k}.txt", "urlList": batch}
    if dry:
        print(f"would submit {len(batch)} urls to {ENDPOINT}")
        print(json.dumps(payload, indent=1)[:400])
        return 0
    req = urllib.request.Request(ENDPOINT, data=json.dumps(payload).encode(),
                                 headers={"content-type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            # 200 = accepted, 202 = accepted, key pending validation
            print(f"✓ submitted {len(batch)} urls — HTTP {r.status} {r.reason}")
            return 0
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        print(f"✗ HTTP {e.code}: {body}")
        return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", action="store_true")
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    batch = urls() if a.urls else [SITE + p for p in a.page]
    if not batch:
        ap.print_help()
        return 2
    return ping(batch, a.dry)


if __name__ == "__main__":
    sys.exit(main())
