#!/usr/bin/env python3
"""nostr_identity.py — check, and complete, the estate's six Nostr identities.

Every venture has a key in the workbook. A key is not an identity until it has published a kind-0
profile, and it is not a rail until it has published a note. This tool reads the keys from a local
registry (`~/.nostr-keys.json`, mode 0600, never in a repo) and does three things:

    python3 nostr_identity.py keys                 # do the nsecs match the npubs? (pure crypto, no net)
    python3 nostr_identity.py presence             # what each key has on the relays right now
    python3 nostr_identity.py profile tapstall     # publish a kind-0 profile for one identity
    python3 nostr_identity.py profile tightbucket --dry

Why a profile matters more than a note: without kind-0 a client shows a hex string where a name should
be, and every reply is a reply to nobody. It is also the cheapest thing to publish — no image, no copy,
no risk of breaking the posting rules.

Needs: `pip install coincurve websocket-client`. The nsec is read from the registry and never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
GEN = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
REGISTRY = os.path.expanduser(os.environ.get("NOSTR_REGISTRY", "~/.nostr-keys.json"))
RELAYS = [r.strip() for r in os.environ.get(
    "NOSTR_RELAYS",
    "wss://relay.nostr.net,wss://relay.primal.net,wss://nos.lol").split(",") if r.strip()]
# Measured 2026-11-08: the estate's notes are not on the same relays. AttestOS lives on nostr.net and
# primal; TightBucket's five notes exist only on nos.lol. A reader whose client ships with a different
# relay sees nothing, which is exactly the "I don't see the Nostr posts" report. `sync` fixes that by
# re-broadcasting events that are already signed — it never creates one.


# --------------------------------------------------------------------------- bech32
def _polymod(values):
    chk = 1
    for v in values:
        top = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            chk ^= GEN[i] if ((top >> i) & 1) else 0
    return chk


def _hrp_expand(hrp: str) -> list[int]:
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]


def bech32_decode(s: str) -> tuple[str, list[int]]:
    pos = s.rfind("1")
    hrp, data = s[:pos], [CHARSET.index(c) for c in s[pos + 1:]]
    if _polymod(_hrp_expand(hrp) + data) != 1:
        raise ValueError(f"{hrp}1…: bad bech32 checksum")
    return hrp, data[:-6]


def to_bytes(bech: str) -> bytes:
    hrp, data = bech32_decode(bech)
    acc = bits = 0
    out = bytearray()
    for v in data:
        acc, bits = (acc << 5) | v, bits + 5
        while bits >= 8:
            bits -= 8
            out.append((acc >> bits) & 0xFF)
    return bytes(out)


def encode_bech32(hrp: str, payload: bytes) -> str:
    data, acc, bits = [], 0, 0
    for byte in payload:
        acc = (acc << 8) | byte
        bits += 8
        while bits >= 5:
            bits -= 5
            data.append((acc >> bits) & 31)
    if bits:
        data.append((acc << (5 - bits)) & 31)
    values = _hrp_expand(hrp) + data + [0] * 6
    mod = _polymod(values) ^ 1
    checksum = [(mod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(CHARSET[d] for d in data + checksum)


# --------------------------------------------------------------------------- registry
def registry() -> dict:
    if not os.path.exists(REGISTRY):
        raise SystemExit(f"no registry at {REGISTRY} — build it from the workbook first")
    with open(REGISTRY) as f:
        return json.load(f)


def pubkey_hex(entry: dict) -> str:
    nsec = entry.get("nsec") or ""
    if not nsec:
        raise SystemExit("this identity has no nsec in the registry")
    # derive the public key: an nsec is the secret, and filtering by a secret finds nothing
    from coincurve import PrivateKey
    return PrivateKey(to_bytes(nsec)).public_key.format(compressed=True)[1:].hex()


def check_keys(reg: dict) -> int:
    from coincurve import PrivateKey
    bad = 0
    print(f"{'identity':14} {'nsec → npub':12} {'npub':64}")
    print("-" * 94)
    for name, entry in reg.items():
        nsec, npub = entry.get("nsec", ""), entry.get("npub", "")
        if not nsec:
            print(f"{name:14} {'MISSING':12} {npub}")
            bad += 1
            continue
        sk = to_bytes(nsec)
        pub = PrivateKey(sk).public_key.format(compressed=True)[1:]
        derived = encode_bech32("npub", pub)
        ok = derived == npub and len(to_bytes(npub)) == 32
        bad += 0 if ok else 1
        print(f"{name:14} {'match' if ok else 'MISMATCH':12} {npub}")
        if not ok:
            print(f"{'':14} {'derived:':12} {derived}")
    print(f"\n{len(reg) - bad}/{len(reg)} identities have a key that matches their npub")
    return 1 if bad else 0


# --------------------------------------------------------------------------- relays
def _ws():
    try:
        import websocket
        return websocket
    except ImportError:
        raise SystemExit("needs websocket-client: pip install websocket-client")


def presence(reg: dict, limit: int = 50) -> int:
    ws = _ws()
    print(f"{'identity':14} {'kind-0':>7} {'notes':>6} {'newest note':>17}  relays")
    print("-" * 66)
    missing = []
    for name, entry in reg.items():
        pub = pubkey_hex(entry)
        prof = 0
        seen: set[str] = set()
        newest = 0
        live = 0
        for relay in RELAYS:
            try:
                c = ws.create_connection(relay, timeout=10)
                c.send(json.dumps(["REQ", "p", {"authors": [pub], "kinds": [0, 1], "limit": limit}]))
                while True:
                    m = json.loads(c.recv())
                    if m[0] == "EVENT":
                        if m[2]["kind"] == 0:
                            prof = max(prof, 1)
                        elif m[2]["id"] not in seen:      # the same note arrives from every relay
                            seen.add(m[2]["id"])
                            newest = max(newest, m[2]["created_at"])
                    if m[0] in ("EOSE", "CLOSED", "NOTICE"):
                        break
                c.close()
                live += 1
            except Exception:                      # noqa: BLE001 — one dead relay is not a failure
                pass
        when = time.strftime("%Y-%m-%d %H:%M", time.gmtime(newest)) if newest else "—"
        flag = "" if prof else "   ← no profile"
        print(f"{name:14} {prof:>7} {len(seen):>6} {when:>17}  {live}/{len(RELAYS)}{flag}")
        if not prof:
            missing.append(name)
    if missing:
        print(f"\nmissing a kind-0 profile: {', '.join(missing)}")
    return 0


# --------------------------------------------------------------------------- publish
PROFILES = {
    "deskos": {"name": "DeskOS", "about": "Working desks for customs, safari and tender firms. Calculators, "
                                          "ESG and DMC references, and daily open tender notices by region."},
    "tightbucket": {"name": "TightBucket", "about": "Website leak audits. Twenty-second audits that show where "
                                                    "a website loses revenue, with the evidence and the fix."},
    "tapstall": {"name": "Tapstall", "about": "A shop link for the markets the big platforms skip. Understands "
                                              "EcoCash, InnBucks and PayShap and matches exact payment amounts."},
    "attestos": {"name": "AttestOS", "about": "Invisible bot verification for sign-up, login and contact forms. "
                                              "One proof-of-work check, one server-side verify call."},
    "mecha": {"name": "Mechanism Audit", "about": "A five-day written audit of what your product actually does."},
    "open practice": {"name": "Open Practice", "about": "Free, practical AI learning. Six build paths, 86 guided "
                                                        "activities, 39 free tools. Independent, non-degree, "
                                                        "non-accredited."},
}
SITES = {
    "deskos": "https://deskos.whop.site/",
    "tightbucket": "https://0x.tightbucket.workers.dev/",
    "tapstall": "https://tapstall.tapstall.workers.dev/",
    "attestos": "https://attestos.whop.site/",
    "mecha": "https://mechanism-audit.whop.site/",
    "open practice": "https://open-practice.open-practice.workers.dev/",
}


def publish_profile(name: str, reg: dict, dry: bool = False, extra: dict | None = None) -> int:
    from coincurve import PrivateKey
    entry = reg.get(name) or next((v for k, v in reg.items() if k.lower().replace(" ", "") == name.lower().replace(" ", "")), None)
    if not entry:
        raise SystemExit(f"unknown identity {name!r}; have: {', '.join(reg)}")
    sk = to_bytes(entry["nsec"])
    pub = PrivateKey(sk).public_key.format(compressed=True)[1:].hex()
    meta = {"name": PROFILES.get(name, {}).get("name", name.title()),
            "about": PROFILES.get(name, {}).get("about", ""),
            "website": SITES.get(name, ""),
            "picture": entry.get("picture", "")}
    meta.update(extra or {})
    meta = {k: v for k, v in meta.items() if v}
    ev = {"pubkey": pub, "created_at": int(time.time()), "kind": 0,
          "tags": [], "content": json.dumps(meta, ensure_ascii=False)}
    import hashlib
    ser = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]],
                     separators=(",", ":"), ensure_ascii=False)
    eid = hashlib.sha256(ser.encode()).hexdigest()
    ev.update({"id": eid, "sig": PrivateKey(sk).sign_schnorr(bytes.fromhex(eid),
                                                            aux_randomness=os.urandom(32)).hex()})
    print(f"  kind-0 for {name} ({pub[:16]}…) → {json.dumps(meta, ensure_ascii=False)}")
    if dry:
        print("  dry run: nothing sent")
        return 0
    ws = _ws()
    taken = 0
    for relay in RELAYS:
        try:
            c = ws.create_connection(relay, timeout=12)
            c.send(json.dumps(["EVENT", ev]))
            reply = json.loads(c.recv())
            c.close()
            ok = isinstance(reply, list) and reply[0] == "OK" and reply[2] is True
            taken += 1 if ok else 0
            print(f"  {relay.split('//')[1]:22} {'accepted' if ok else reply[2] if len(reply) > 2 else 'refused'}")
        except Exception as exc:                   # noqa: BLE001
            print(f"  {relay.split('//')[1]:22} {type(exc).__name__}")
    print(f"  accepted by {taken}/{len(RELAYS)} relays")
    return 0 if taken else 1


def sync(reg: dict, dry: bool = False) -> int:
    """Re-broadcast every existing kind-0/1 event of every identity to every relay.

    Nothing new is signed. A relay stores events by id, so sending the same signed event to a relay
    that lacks it is ordinary propagation, and it is idempotent.
    """
    ws = _ws()
    total = 0
    for name, entry in reg.items():
        pub = pubkey_hex(entry)
        events: dict[str, dict] = {}
        holders: dict[str, set[str]] = {}
        for relay in RELAYS:
            try:
                c = ws.create_connection(relay, timeout=10)
                c.send(json.dumps(["REQ", "s", {"authors": [pub], "kinds": [0, 1], "limit": 200}]))
                while True:
                    m = json.loads(c.recv())
                    if m[0] == "EVENT":
                        events[m[2]["id"]] = m[2]
                        holders.setdefault(m[2]["id"], set()).add(relay)
                    if m[0] in ("EOSE", "CLOSED", "NOTICE"):
                        break
                c.close()
            except Exception:                      # noqa: BLE001
                pass
        if not events:
            print(f"  {name:14} nothing published yet — nothing to sync")
            continue
        moved = 0
        for eid, ev in events.items():
            missing = [r for r in RELAYS if r not in holders.get(eid, set())]
            for relay in missing:
                if dry:
                    moved += 1
                    continue
                try:
                    c = ws.create_connection(relay, timeout=12)
                    c.send(json.dumps(["EVENT", ev]))
                    reply = json.loads(c.recv())
                    c.close()
                    if isinstance(reply, list) and reply[0] == "OK" and reply[2] is True:
                        moved += 1
                except Exception:                  # noqa: BLE001
                    pass
        print(f"  {name:14} {len(events)} events, {moved} relay-copies {'would be ' if dry else ''}pushed")
        total += moved
    print(f"\n{total} relay copies {'to push' if dry else 'pushed'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["keys", "presence", "profile", "sync"])
    ap.add_argument("name", nargs="?", default="")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)
    reg = registry()
    if args.cmd == "keys":
        return check_keys(reg)
    if args.cmd == "presence":
        return presence(reg)
    if args.cmd == "sync":
        return sync(reg, dry=args.dry)
    if not args.name:
        raise SystemExit("name the identity: " + ", ".join(reg))
    return publish_profile(args.name, reg, dry=args.dry)


if __name__ == "__main__":
    raise SystemExit(main())
