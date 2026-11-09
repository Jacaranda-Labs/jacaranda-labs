#!/usr/bin/env python3
"""The one-click Tumblr handshake, in two steps.

Tumblr is OAuth 1.0a, so there is no such thing as a token you can just copy out of a dashboard:
you need a *request token*, a human click, and then an *access token* exchanged for it. This script
does all three parts that a machine can do, and prints the one URL a human has to open.

    # step 1 — ask Tumblr for a request token, get the consent URL
    python3 rails/jacaranda/tumblr_connect.py --start

    # ... open the URL it prints, click "Allow", copy the code Tumblr shows you ...

    # step 2 — trade the code for the permanent token pair
    python3 rails/jacaranda/tumblr_connect.py --finish THE_CODE

The consumer key and secret come from the credential sheet — for Jacaranda Labs that is the
consumer key/secret on the tumblr row, Jacaranda column. Pass them explicitly if they are not in
the environment:

    JACARANDA_TUMBLR_CK=... JACARANDA_TUMBLR_CS=... python3 ... --start

The result lands in ~/.jacaranda-tumblr.json (mode 600, outside the repo) and is printed as the five
environment lines that belong in GitHub → Settings → Secrets → Actions. Nothing here is ever
written into the repository.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REQUEST_URL = "https://www.tumblr.com/oauth/request_token"
AUTHORIZE_URL = "https://www.tumblr.com/oauth/authorize"
ACCESS_URL = "https://www.tumblr.com/oauth/access_token"
STORE = os.path.expanduser("~/.jacaranda-tumblr.json")
UA = "Jacaranda Labs/1.0 (+https://jacaranda-labs.pages.dev)"


def q(s: str) -> str:
    return urllib.parse.quote(str(s), safe="~-._")


def sign(method: str, url: str, params: dict, cs: str, tsec: str = "") -> str:
    pairs = sorted((q(k), q(v)) for k, v in params.items())
    base = "&".join([method.upper(), q(url), q("&".join(f"{k}={v}" for k, v in pairs))])
    key = f"{q(cs)}&{q(tsec)}".encode()
    return base64.b64encode(hmac.new(key, base.encode(), hashlib.sha1).digest()).decode()


def oauth_header(method: str, url: str, params: dict, ck: str, cs: str,
                 tok: str = "", tsec: str = "") -> str:
    oauth = {
        "oauth_consumer_key": ck,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    if tok:
        oauth["oauth_token"] = tok
    oauth.update(params)          # oauth_callback / oauth_verifier belong in the header, signed
    oauth["oauth_signature"] = sign(method, url, oauth, cs, tsec)
    return "OAuth " + ", ".join(f'{q(k)}="{q(v)}"' for k, v in sorted(oauth.items()))


def call(url: str, params: dict, ck: str, cs: str, tok: str = "", tsec: str = "") -> str:
    req = urllib.request.Request(url, data=b"", method="POST", headers={
        "Authorization": oauth_header("POST", url, params, ck, cs, tok, tsec),
        "User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{url} → HTTP {e.code}: {e.read()[:200].decode('utf-8', 'ignore')}")


def parse(body: str) -> dict:
    return dict(urllib.parse.parse_qsl(body.strip()))


def creds(args) -> tuple[str, str]:
    ck = args.ck or os.environ.get("JACARANDA_TUMBLR_CK", "").strip()
    cs = args.cs or os.environ.get("JACARANDA_TUMBLR_CS", "").strip()
    if not (ck and cs):
        raise SystemExit("need the app's consumer key and secret: --ck/--cs or "
                         "JACARANDA_TUMBLR_CK / JACARANDA_TUMBLR_CS")
    return ck, cs


def start(args) -> int:
    ck, cs = creds(args)
    body = call(REQUEST_URL, {"oauth_callback": args.callback}, ck, cs)
    tok = parse(body)
    if not tok.get("oauth_token"):
        raise SystemExit(f"no request token: {body[:200]}")
    pending = {"consumer_key": ck, "consumer_secret": cs,
               "request_token": tok["oauth_token"], "request_secret": tok["oauth_token_secret"]}
    with open(STORE + ".pending", "w") as f:
        json.dump(pending, f)
    os.chmod(STORE + ".pending", 0o600)
    url = f"{AUTHORIZE_URL}?oauth_token={tok['oauth_token']}"
    print("Open this, sign in as the Jacaranda Tumblr, and press Allow:\n")
    print(url + "\n")
    print(f"callback confirmed: {tok.get('oauth_callback_confirmed')}")
    print("\nAfter you press Allow, the browser comes back to jacaranda-labs.pages.dev with a long")
    print("address. Copy that whole address — or just the oauth_verifier= value in it — and send it")
    print("to me, or run:\n  python3 rails/jacaranda/tumblr_connect.py --finish <verifier>")
    return 0


def finish(args) -> int:
    path = STORE + ".pending"
    if not os.path.exists(path):
        raise SystemExit("no pending handshake — run --start first")
    with open(path) as f:
        p = json.load(f)
    body = call(ACCESS_URL, {"oauth_verifier": _verifier(args.finish)},
                p["consumer_key"], p["consumer_secret"], p["request_token"], p["request_secret"])
    got = parse(body)
    if not got.get("oauth_token"):
        raise SystemExit(f"no access token: {body[:200]}")
    blogs = []
    try:
        info = call("https://api.tumblr.com/v2/user/info", {},
                    p["consumer_key"], p["consumer_secret"],
                    got["oauth_token"], got["oauth_token_secret"])
        blogs = [b.get("name") for b in json.loads(info).get("response", {}).get("user", {}).get("blogs", [])]
    except SystemExit:
        pass
    rec = {"consumer_key": p["consumer_key"], "consumer_secret": p["consumer_secret"],
           "token": got["oauth_token"], "token_secret": got["oauth_token_secret"],
           "blogs": blogs, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(STORE, "w") as f:
        json.dump(rec, f, indent=1)
    os.chmod(STORE, 0o600)
    os.remove(path)
    blog = (os.environ.get("JACARANDA_TUMBLR_BLOG") or (blogs[0] if blogs else "jacarandalabs")).strip()
    print("connected. blogs on this account:", ", ".join(b for b in blogs if b) or "(none listed)")
    print("\nPaste these five into GitHub → Settings → Secrets → Actions:\n")
    print(f'JACARANDA_TUMBLR_CK="{rec["consumer_key"]}"')
    print(f'JACARANDA_TUMBLR_CS="{rec["consumer_secret"]}"')
    print(f'JACARANDA_TUMBLR_TOKEN="{rec["token"]}"')
    print(f'JACARANDA_TUMBLR_TOKEN_SECRET="{rec["token_secret"]}"')
    print(f'JACARANDA_TUMBLR_BLOG="{blog}"')
    print(f"\nsaved to {STORE} (mode 600). It is outside the repo and must stay there.")
    return 0


def _verifier(raw: str) -> str:
    """Accept the bare code, or the whole redirect URL pasted out of the address bar."""
    raw = (raw or "").strip()
    if "oauth_verifier=" in raw:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
        return (qs.get("oauth_verifier") or [""])[0]
    return raw


def main() -> int:
    ap = argparse.ArgumentParser(description="Tumblr OAuth 1.0a handshake for the Jacaranda rail")
    ap.add_argument("--start", action="store_true", help="get a request token and print the consent URL")
    ap.add_argument("--finish", metavar="VERIFIER", help="trade the code Tumblr showed you for a token")
    ap.add_argument("--ck", help="consumer key (or JACARANDA_TUMBLR_CK)")
    ap.add_argument("--cs", help="consumer secret (or JACARANDA_TUMBLR_CS)")
    ap.add_argument("--callback", default="https://jacaranda-labs.pages.dev/?tumblr=1",
                    help="OAuth callback Tumblr returns to. Tumblr refuses 'oob', so the site root is "
                         "used: it ignores the parameters and the verifier is readable in the address bar")
    a = ap.parse_args()
    if a.finish:
        return finish(a)
    if a.start:
        return start(a)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
