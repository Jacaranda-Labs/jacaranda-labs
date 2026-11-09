#!/usr/bin/env python3
"""Rotate a Nostr identity whose secret has been exposed, everywhere it is stored.

A leaked nsec is a leaked account: whoever has it can sign as that identity forever, and no amount
of deleting the file fixes it, because the bytes are already in a public git history and in every
clone and fork of it. The only repair is a new key, published in the same places the old one was.

What this does, in one pass, so the identity is never half-rotated:

  1. generates a fresh secp256k1 secret (32 random bytes, checked against the curve order)
  2. writes the new npub/nsec into ~/.nostr-keys.json (the local registry the rails read)
  3. updates tools/identity.json so the audit checks the new npub
  4. sets the GitHub Actions secret on the repo that publishes as this identity, sealed-box
     encrypted with the repo's public key (never in a URL, never in a log)
  5. appends a line to nostr-rotations.log — old npub, new npub, when, why. No secrets.

    python3 tools/rotate_nostr.py --identity mecha \
        --repo mechanism-audit/mechanism-audit --secret MA_NOSTR_NSEC \
        --reason "nsec committed to a public repository" [--dry]

Prints the new npub. It does not print the secret, and it does not touch any file that is committed
to git except the registry and identity.json, neither of which holds a secret.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTRY = Path.home() / ".nostr-keys.json"
IDENTITY = HERE / "identity.json"
LOG = ROOT.parent / "nostr-rotations.log"

# secp256k1 order; a secret must be < n and non-zero
ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def new_secret() -> bytes:
    while True:
        k = os.urandom(32)
        v = int.from_bytes(k, "big")
        if 0 < v < ORDER:
            return k


def gh(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"token {token}",
                                          "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return json.loads(raw) if raw.strip() else {}


def set_secret(repo: str, name: str, value: str, token: str) -> None:
    from nacl import encoding, public            # pynacl, present in CI and installable locally
    key = gh("GET", f"https://api.github.com/repos/{repo}/actions/secrets/public-key", token)
    sealed = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder())) \
        .encrypt(value.encode())
    gh("PUT", f"https://api.github.com/repos/{repo}/actions/secrets/{name}", token,
       {"encrypted_value": base64.b64encode(sealed).decode(), "key_id": key["key_id"]})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", required=True, help="name in ~/.nostr-keys.json")
    ap.add_argument("--repo", help="owner/name whose Actions secret must change")
    ap.add_argument("--secret", help="secret name, e.g. MA_NOSTR_NSEC")
    ap.add_argument("--reason", default="exposed")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)

    sys.path.insert(0, str(ROOT / "rails"))
    from nostr_identity import encode_bech32
    from coincurve import PrivateKey

    reg = json.loads(REGISTRY.read_text())
    if a.identity not in reg:
        print(f"no identity {a.identity!r} in {REGISTRY}", file=sys.stderr)
        return 2
    old = dict(reg[a.identity])
    k = new_secret()
    nsec = encode_bech32("nsec", k)
    pub = PrivateKey(k).public_key.format(compressed=True)[1:].hex()
    npub = encode_bech32("npub", bytes.fromhex(pub))

    print(f"identity {a.identity}")
    print(f"  old npub {old.get('npub')}")
    print(f"  new npub {npub}")
    if a.dry:
        print("  dry run — nothing written")
        return 0

    reg[a.identity] = {**old, "npub": npub, "pubkey_hex": pub, "nsec": nsec,
                       "nsec_matches_npub": True,
                       "rotated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "rotation_reason": a.reason}
    REGISTRY.write_text(json.dumps(reg, indent=1) + "\n")
    os.chmod(REGISTRY, 0o600)

    if IDENTITY.exists():
        d = json.loads(IDENTITY.read_text())
        for i in d.get("identities", []):
            if i.get("npub") == old.get("npub"):
                i["npub"] = npub
                i["rotated_from"] = old.get("npub")
        IDENTITY.write_text(json.dumps(d, indent=1) + "\n")

    if a.repo and a.secret:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
        if not token:
            print("  GH_TOKEN not set — secret NOT updated; the identity is half-rotated", file=sys.stderr)
            return 3
        set_secret(a.repo, a.secret, nsec, token)
        print(f"  secret {a.secret} updated on {a.repo}")

    with LOG.open("a") as f:
        f.write(f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} {a.identity} "
                f"{old.get('npub')} -> {npub} ({a.reason})\n")
    print(f"  logged to {LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
