#!/usr/bin/env python3
"""Watch every front door in the estate, and say which one is answering like a machine.

This exists because of 2026-11-10: the owner opened STPi and got

    {"ok":false,"error":"not found"}

from a worker that was, in fact, completely healthy — its `/health` said pass 3, last tick five
minutes earlier. The service was fine and the front door was missing, and the only detector for that
was the owner's bad luck. A control that depends on the owner noticing is not a control.

What it checks, from data/uptime.json:

  product   a page a customer lands on  →  200, HTML, has a <title>
  service   a worker or API             →  answers; a JSON 404 at the root is a warning, not a pass
  health    a status endpoint           →  JSON predicates (ok == true, tick.age_min < 120)
  redirect  a gated console             →  2xx or 3xx, 401/403 is correct
  asset     a file that must resolve    →  200 and not an error page

    python3 tools/uptime.py                 # all checks, table, exit 1 on a failure
    python3 tools/uptime.py --only stpi     # substring filter
    python3 tools/uptime.py --json          # machine output
    python3 tools/uptime.py --quiet         # only problems

Exit codes: 0 everything a customer touches is up · 1 a product is down or a service is degraded.
Warnings (a service root that answers JSON) do not fail the run — they are reported, because they cost
attention rather than money — except for a `service` marked `"strict": true`, which does.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONF = ROOT / "data" / "uptime.json"
UA = "Mozilla/5.0 (compatible; Jacaranda uptime; +https://jacaranda-labs.pages.dev)"

RED, AMBER, GREEN, DIM, OFF = "\033[38;5;203m", "\033[38;5;215m", "\033[38;5;114m", "\033[2m", "\033[0m"


def paint(s: str, c: str, on: bool) -> str:
    return f"{c}{s}{OFF}" if on else s


def fetch(url: str, timeout: int = 20) -> tuple[int, str, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*",
                                               "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("content-type", ""), r.read(4096)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(2048)
        except Exception:                                    # noqa: BLE001
            body = b""
        return e.code, e.headers.get("content-type", ""), body
    except Exception as e:                                   # noqa: BLE001
        return 0, f"error: {type(e).__name__}", str(e).encode()[:200]


def dig(obj, path: str):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def check(c: dict) -> dict:
    name, url, kind = c["name"], c["url"], c.get("kind", "product")
    status, ctype, body = fetch(url)
    text = body.decode("utf-8", "ignore")
    ok, why, warn = True, "", False

    if kind == "health":
        if status == 0:
            ok, why = False, f"unreachable ({ctype})"
        else:
            try:
                doc = json.loads(text)
            except Exception:                                # noqa: BLE001
                    ok, why = False, f"not JSON ({status})"
            else:
                for path, limit in (c.get("json") or {}).items():
                    val = dig(doc, path)
                    if val is None:
                        ok, why = False, f"{path} missing"
                    elif path.endswith("age_min") and isinstance(val, (int, float)) and val > limit:
                        ok, why = False, f"stale: {path} is {val} min (limit {limit})"
                    elif path == "ok" and val is not True:
                        ok, why = False, f"reports ok={val}"
                why = why or f"ok · " + ", ".join(f"{k}={dig(doc, k)}" for k in (c.get("json") or {}))
    elif kind == "product":
        if status != 200:
            ok, why = False, f"HTTP {status}"
        elif "html" not in ctype:
            ok, why = False, f"200 but {ctype or 'no type'} — a browser gets not-a-page"
        elif "<title" not in text.lower():
            ok, why = False, "200 HTML with no <title>"
        else:
            title = text.lower().split("<title", 1)[1].split(">", 1)[1].split("<", 1)[0].strip()
            why = f"200 · {title[:52]}"
    elif kind == "service":
        if status == 0:
            ok, why = False, f"unreachable ({ctype})"
        elif status == 404 and "json" in ctype:
            warn = True
            why = "404 JSON at the root — alive, but no front door (see stpi-entry-fix/)"
        elif status == 404:
            warn = True
            why = f"404 {ctype or 'no type'} at the root — alive, but no front door"
        elif status == 401 and "html" in ctype:
            why = "401 HTML — closed console, as intended"
        elif "json" in ctype:
            why = f"{status} JSON"
        else:
            why = f"{status} {ctype or ''}".strip()
    elif kind == "redirect":
        if status == 0:
            ok, why = False, f"unreachable ({ctype})"
        elif status in (200, 204, 301, 302, 303, 307, 308, 401, 403):
            why = f"{status} — gated, as intended"
        else:
            ok, why = False, f"HTTP {status}"
    else:  # asset
        if status != 200 or len(body) < 1024:
            ok, why = False, f"HTTP {status}, {len(body)}b"
        else:
            why = f"200 · {len(body)}b"

    return {"name": name, "url": url, "kind": kind, "ok": ok, "warn": warn, "why": why,
            "note": c.get("note", "")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--no-colour", action="store_true")
    a = ap.parse_args()
    on = sys.stdout.isatty() and not a.no_colour and not a.json

    conf = json.loads(CONF.read_text())
    checks = [c for c in conf["checks"] if a.only.lower() in c["name"].lower()] if a.only else conf["checks"]
    results = [check(c) for c in checks]

    if a.json:
        print(json.dumps({"at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(), "results": results}, indent=1))
    else:
        bad = [r for r in results if not r["ok"]]
        warns = [r for r in results if r["ok"] and r["warn"]]
        for r in results:
            if a.quiet and r["ok"] and not r["warn"]:
                continue
            tag = paint("DOWN", RED, on) if not r["ok"] else (
                paint("WARN", AMBER, on) if r["warn"] else paint("OK  ", GREEN, on))
            print(f"  {tag} {r['name']:<24}{r['why'][:74]}")
        print()
        if bad:
            print(paint(f"  ✗ {len(bad)} front door(s) failing. These are pages a customer can reach.", RED, on))
        if warns:
            print(paint(f"  ! {len(warns)} warning(s): alive but answering like a machine.", AMBER, on))
            for r in warns:
                print(paint(f"      {r['name']}: {r['note'] or 'no front door'}", DIM, on))
        if not bad and not warns:
            print(paint("  ✓ every entry in the estate answers as it should", GREEN, on))

    strict_fail = any((not r["ok"]) or (r["warn"] and
                       any(c.get("strict") for c in checks if c["name"] == r["name"]))
                      for r in results)
    return 1 if strict_fail else 0


if __name__ == "__main__":
    sys.exit(main())
