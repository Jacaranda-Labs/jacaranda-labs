#!/usr/bin/env python3
"""Build the operator's site: the manual, sealed, installable, readable on a phone at 6am.

Why it is sealed rather than merely unlisted: the manual describes how the estate is run, what it
costs, what fails and who to call. A private URL is not privacy — this ships the manual **encrypted**
(AES-256-GCM, key from PBKDF2-SHA256 with 310k iterations) and decrypts it in the browser. The deployed
bytes are noise without the passphrase; there is no server to talk to and nothing to log in to.

    python3 ops-site/build_ops_site.py --pass 'your phrase'      # seal and write dist/
    python3 ops-site/build_ops_site.py --pass … --deploy         # seal, then push to Cloudflare Pages

What the site is, on purpose:

  * one file that works on any browser — phone, tablet, borrowed laptop, no terminal, no repo
  * installable to the home screen (manifest + service worker), and it opens offline once installed
  * a contents drawer instead of a sidebar, because a sidebar is a desktop idea
  * the card first: the morning/evening loop is the landing screen, the rest is one tap away
  * a "today" panel that reads the same sources as tools/estate.py, baked in at build time

The source of truth stays operator-bible.html. This builder wraps it; it never forks the words.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = HERE / "dist"
# The plaintext manual lives outside the repo on purpose; point at it with --bible.
BIBLE = Path(os.environ.get("OPS_BIBLE", "")).expanduser() if os.environ.get("OPS_BIBLE") else (
    ROOT / "operator-bible.html" if (ROOT / "operator-bible.html").exists()
    else ROOT.parent / "operator-bible.html")
REPO = ROOT if (ROOT / "data" / "ops.json").exists() else ROOT / "jacaranda-site"

ITERATIONS = 310_000
SALT_LEN = 16
PROJECT = "jacaranda-ops"


# --------------------------------------------------------------------------- crypto
def seal(plaintext: bytes, phrase: str) -> dict:
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", phrase.encode(), salt, ITERATIONS, dklen=32)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    return {"v": 1, "alg": "AES-256-GCM", "kdf": f"PBKDF2-SHA256-{ITERATIONS}",
            "salt": base64.b64encode(salt).decode(),
            "iv": base64.b64encode(iv).decode(),
            "ct": base64.b64encode(ct).decode(),
            "bytes": len(plaintext),
            "sealed_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


# --------------------------------------------------------------------------- estate snapshot
def snapshot() -> dict:
    """The same facts tools/estate.py prints, baked in so the phone needs no repo."""
    out = {"at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "press": {},
           "money": {}, "actions": [], "decisions": [], "offers": [], "works": 0,
           "seq": {"leads": 0, "sent": 0, "drafted": 0, "replied": 0, "due": 0,
                   "sending": [], "drafting": []}}
    try:
        ops = json.loads((REPO / "data" / "ops.json").read_text())
        out["money"] = ops.get("money", {})
        out["actions"] = [a for a in ops.get("owner_actions", []) if not a.get("done")]
        out["decisions"] = ops.get("decisions", [])
    except Exception:
        pass
    try:
        state = json.loads((REPO / "rails/jacaranda/press-state.json").read_text())
        bank = json.loads((REPO / "rails/jacaranda/bank.json").read_text())
        out["press"] = {"sent": len(state.get("sent", [])), "last_at": state.get("last_at"),
                        "bank": len(bank)}
    except Exception:
        pass
    try:                                    # the sequence, read the same way estate.py reads it
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("outreach", REPO / "growth" / "outreach.py")
        oc = ilu.module_from_spec(spec)
        spec.loader.exec_module(oc)
        ev = oc.events()
        leads = oc.load_leads()
        rl = oc.rails()
        out["seq"] = {
            "leads": len(leads),
            "sent": sum(1 for e in ev if e.get("event") == "sent"),
            "drafted": sum(1 for e in ev if e.get("event") == "drafted"),
            "replied": sum(1 for e in ev if e.get("event") == "replied"),
            "due": sum(len(oc.next_due(le)) for le in leads),
            "sending": [k for k, v in rl.items() if v.get("can")],
            "drafting": [k for k, v in rl.items() if not v.get("can")],
        }
    except Exception:
        pass
    try:
        out["offers"] = [{"name": v["name"], "from": v.get("from") or "free"}
                         for v in json.loads((REPO / "data/ventures.json").read_text())]
        out["works"] = len(json.loads((REPO / "data/works.json").read_text()))
    except Exception:
        pass
    return out


# --------------------------------------------------------------------------- html
SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>The Operator's Bible · Jacaranda Labs</title>
<meta name="theme-color" content="#0a0710">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Ops">
<meta name="description" content="Private operating manual. Sealed.">
<meta name="robots" content="noindex,nofollow">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon-192.png">
<style>
  :root{
    --ink:#0a0710; --panel:#171024; --line:#2a2140; --text:#ece7f6; --mute:#a99cc4; --dim:#7d719a;
    --violet:#a78bfa; --violet2:#8b5cf6; --gold:#e8b872; --red:#e8567c; --green:#7fe0a8;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
    --sans:ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
    --safe-b:env(safe-area-inset-bottom,0px);
  }
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
  html,body{margin:0;background:var(--ink);color:var(--text);font:16px/1.62 var(--sans)}
  body{min-height:100dvh}
  button{font:inherit;color:inherit;background:none;border:0;padding:0;cursor:pointer}
  input{font:inherit}
  .wrap{max-width:820px;margin:0 auto;padding:0 18px}
  /* ---------- lock ---------- */
  #lock{position:fixed;inset:0;display:grid;place-items:center;padding:24px;
        background:radial-gradient(900px 500px at 50% -10%,#1a1030 0%,var(--ink) 60%);z-index:60}
  .lockcard{width:100%;max-width:360px;text-align:center}
  .lockcard .mark{width:56px;height:56px;margin:0 auto 18px}
  .lockcard h1{font:400 25px/1.2 var(--serif);margin:0 0 6px}
  .lockcard p{color:var(--mute);font-size:14px;margin:0 0 22px}
  .lockcard input{width:100%;padding:14px 15px;border-radius:12px;border:1px solid var(--line);
    background:var(--panel);color:var(--text);font-size:17px;text-align:center}
  .lockcard button{margin-top:12px;width:100%;padding:14px;border-radius:12px;
    background:linear-gradient(180deg,var(--violet2),#6d3ff0);color:#fff;font-weight:600;font-size:16px}
  .lockcard .err{color:var(--red);font-size:13px;margin-top:12px;min-height:18px}
  .lockcard .fine{color:var(--dim);font-size:11.5px;margin-top:20px;line-height:1.5}
  /* ---------- top bar ---------- */
  header.bar{position:sticky;top:0;z-index:30;background:rgba(10,7,16,.86);
    backdrop-filter:saturate(140%) blur(12px);border-bottom:1px solid var(--line);
    padding:calc(8px + env(safe-area-inset-top,0px)) 0 8px}
  header.bar .row{display:flex;align-items:center;gap:10px}
  header.bar .t{font:600 11px/1.4 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:var(--mute)}
  header.bar .t b{color:var(--text);font-weight:700}
  header.bar .sp{flex:1}
  .ibtn{width:38px;height:38px;border-radius:10px;border:1px solid var(--line);display:grid;
        place-items:center;background:var(--panel);color:var(--text)}
  .ibtn svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;
            stroke-linecap:round;stroke-linejoin:round}
  #drawer{position:fixed;inset:0;z-index:50;display:none}
  #drawer.open{display:block}
  #drawer .scrim{position:absolute;inset:0;background:rgba(0,0,0,.62)}
  #drawer .panel{position:absolute;right:0;top:0;bottom:0;width:min(86vw,340px);background:var(--ink2,#120c1c);
    border-left:1px solid var(--line);padding:calc(16px + env(safe-area-inset-top,0px)) 16px 28px;
    overflow:auto}
  #drawer .panel h4{font:600 10px/1.4 var(--sans);letter-spacing:.16em;text-transform:uppercase;
    color:var(--dim);margin:18px 0 8px}
  #drawer .panel h4:first-of-type{margin-top:4px}
  #drawer .panel a{display:block;color:var(--text);text-decoration:none;padding:11px 10px;
    border-radius:9px;font-size:15px;border-bottom:1px solid rgba(42,33,64,.55)}
  #drawer .panel a:active{background:var(--panel)}
  /* ---------- today ---------- */
  main{padding:18px 0 120px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px;margin:0 0 12px}
  .card .lbl{font:600 10px/1.4 var(--sans);letter-spacing:.15em;text-transform:uppercase;color:var(--violet)}
  .card h2{font:400 21px/1.25 var(--serif);margin:6px 0 4px}
  .card p{margin:0;color:var(--mute);font-size:14px}
  .big{font:400 26px/1.22 var(--serif);margin:4px 0 8px}
  .stat{display:grid;grid-template-columns:repeat(auto-fit,minmax(72px,1fr));gap:9px;margin-top:10px}
  .stat div{background:rgba(255,255,255,.04);border:1px solid var(--line);
            border-radius:11px;padding:9px 10px;min-width:0}
  .stat b{display:block;font:600 17px/1.2 var(--sans)}
  .stat span{font:10.5px/1.4 var(--sans);color:var(--dim);letter-spacing:.06em;text-transform:uppercase}
  .check{list-style:none;padding:0;margin:8px 0 0}
  .check li{display:grid;grid-template-columns:22px 1fr;gap:10px;padding:11px 0;align-items:start;
            border-bottom:1px solid rgba(42,33,64,.8)}
  .check li:last-child{border-bottom:0}
  .check .box{width:20px;height:20px;border-radius:6px;border:1.6px solid #4a3b6b;margin-top:2px;
    display:grid;place-items:center;transition:background .15s,border-color .15s}
  .check li.done .box{background:var(--green);border-color:var(--green)}
  .check li.done .box svg{opacity:1}
  .check .box svg{width:12px;height:12px;stroke:#0a0710;stroke-width:3;fill:none;opacity:0}
  .check li.done span{color:var(--dim);text-decoration:line-through}
  .tabs{display:flex;gap:6px;margin:2px 0 12px;overflow:auto}
  .tabs button{padding:8px 13px;border-radius:999px;border:1px solid var(--line);color:var(--mute);
    font-size:13.5px;white-space:nowrap}
  .tabs button.on{background:var(--violet2);border-color:var(--violet2);color:#fff;font-weight:600}
  .pill{display:inline-block;font:600 10.5px/1.4 var(--sans);letter-spacing:.1em;text-transform:uppercase;
    border-radius:999px;padding:3px 9px;border:1px solid var(--line);color:var(--mute)}
  .pill.bad{border-color:rgba(232,86,124,.5);color:var(--red)}
  .pill.good{border-color:rgba(127,224,168,.45);color:var(--green)}
  /* ---------- the manual (rendered inside) ---------- */
  #manual .wrap{max-width:none;padding:0}
  #manual header.mast{display:block;padding:22px 0 16px;border-bottom:1px solid var(--line)}
  #manual header.mast h1{font:400 30px/1.1 var(--serif);margin:8px 0 0}
  #manual header.mast .kicker{font:600 10px/1.4 var(--sans);letter-spacing:.16em;text-transform:uppercase;
    color:var(--violet)}
  #manual header.mast .meta{display:none}
  #manual nav{display:none}
  #manual h2{font:400 24px/1.2 var(--serif);margin:34px 0 6px;padding-top:22px;border-top:1px solid var(--line)}
  #manual h2 .num{display:block;font:600 10px/1 var(--sans);letter-spacing:.16em;color:var(--violet2);
    margin-bottom:10px;text-transform:uppercase}
  #manual h3{font:600 15.5px/1.35 var(--sans);margin:22px 0 8px}
  #manual h4{font:600 11px/1.4 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--dim);
    margin:18px 0 6px}
  #manual p,#manual li{font-size:15.5px;color:#ded8ec}
  #manual .lede{font:18px/1.55 var(--serif);color:#f2edfa}
  #manual blockquote{margin:18px 0;padding-left:14px;border-left:3px solid var(--violet2);
    font:17px/1.5 var(--serif);color:#efe8fb}
  #manual table{width:100%;border-collapse:collapse;font-size:13.5px;display:block;overflow-x:auto}
  #manual th,#manual td{text-align:left;padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}
  #manual th{font:600 10px/1.4 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}
  #manual .grid{display:block}
  #manual .card{margin:0 0 10px}
  #manual .rule{display:grid;grid-template-columns:34px 1fr;gap:10px;padding:12px 0;
    border-top:1px solid var(--line)}
  #manual .rule .n{font:600 12px/1.6 var(--mono);color:var(--violet2)}
  #manual .note,#manual .warn{border-radius:12px;padding:14px 15px;margin:16px 0}
  #manual .note{background:rgba(139,92,246,.12);border:1px solid rgba(139,92,246,.3)}
  #manual .warn{background:rgba(232,86,124,.1);border:1px solid rgba(232,86,124,.28)}
  #manual .note .tag,#manual .warn .tag{font:600 10px/1.4 var(--sans);letter-spacing:.14em;
    text-transform:uppercase;margin-bottom:6px;color:var(--violet)}
  #manual .warn .tag{color:var(--red)}
  #manual code{font:13px/1.5 var(--mono);background:var(--panel);border:1px solid var(--line);
    padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
  #manual pre{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px;
    overflow:auto;font:12.5px/1.6 var(--mono);color:#d9cff0}
  #manual .stamp{border:2px solid var(--red);color:var(--red);border-radius:8px;padding:4px 9px;
    font:700 10px/1.3 var(--sans);letter-spacing:.1em;text-transform:uppercase}
  #manual .two-col{columns:1}
  #manual section[id]{scroll-margin-top:76px}
  #manual a{color:var(--violet);text-decoration:none}
  .foot{padding:30px 0 calc(40px + var(--safe-b));text-align:center;color:var(--dim);font-size:12px}
  .hidden{display:none !important}
</style>
</head>
<body>

<div id="lock">
  <div class="lockcard">
    <svg class="mark" viewBox="-48 -48 96 96" aria-hidden="true"><g fill="#a78bfa">
      <ellipse cx="0" cy="-24" rx="11" ry="20"/><ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate(72)"/>
      <ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate(144)"/><ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate(216)"/>
      <ellipse cx="0" cy="-24" rx="11" ry="20" transform="rotate(288)"/></g><circle r="7" fill="#e8467c"/></svg>
    <h1>The Operator's Bible</h1>
    <p>Sealed. Enter the passphrase, once per device.</p>
    <input id="phrase" type="password" autocomplete="current-password" autocapitalize="off"
           spellcheck="false" placeholder="passphrase" aria-label="passphrase">
    <button id="unlock">Unlock</button>
    <div class="err" id="err"></div>
    <p class="fine">Decrypted in this browser. Nothing is sent anywhere, there is no account,
      and the deployed file is ciphertext without this phrase.</p>
  </div>
</div>

<header class="bar hidden" id="bar">
  <div class="wrap row">
    <div class="t">OPS&nbsp;·&nbsp;<b>Jacaranda Labs</b></div>
    <div class="sp"></div>
    <button class="ibtn" id="openDrawer" aria-label="Contents">
      <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </button>
  </div>
</header>

<div id="drawer" aria-hidden="true">
  <div class="scrim"></div>
  <div class="panel">
    <h4>Today</h4>
    <a href="#today" data-close>This morning</a>
    <a href="#loop-check" data-close>The daily loop</a>
    <a href="#sequence" data-close>The sequence</a>
    <a href="#badday" data-close>If today is bad</a>
    <h4>The manual</h4>
    <div id="toc"></div>
    <h4>Device</h4>
    <a href="#" id="installHint" data-close>Install to home screen</a>
    <a href="#" id="lockNow" data-close>Lock this device</a>
  </div>
</div>

<main id="app" class="hidden">
  <div class="wrap">
    <div class="tabs" id="tabs">
      <button class="on" data-view="today">Today</button>
      <button data-view="manual">The manual</button>
      <button data-view="card">The card</button>
    </div>
    <section id="today"></section>
    <section id="manual" class="hidden"></section>
    <section id="card" class="hidden"></section>
  </div>
  <div class="foot" id="foot"></div>
</main>

<script id="payload" type="application/json">__PAYLOAD__</script>
<script id="snapshot" type="application/json">__SNAPSHOT__</script>
<script>
(function () {
  "use strict";
  const P = JSON.parse(document.getElementById("payload").textContent);
  const S = JSON.parse(document.getElementById("snapshot").textContent);
  const KEY = "ops.key.v1", HIDE = "ops.check.v1";
  const enc = new TextEncoder(), dec = new TextDecoder();
  const b64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));

  async function derive(phrase, salt) {
    const base = await crypto.subtle.importKey("raw", enc.encode(phrase), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey(
      { name: "PBKDF2", salt, iterations: P.iterations, hash: "SHA-256" }, base,
      { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  }

  async function open(phrase) {
    const key = await derive(phrase, b64(P.salt));
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b64(P.iv) }, key, b64(P.ct));
    return dec.decode(plain);
  }

  // ---- a tiny, safe wrapper: parse the manual into nodes, then extract the parts we render
  function parse(html) {
    const doc = new DOMParser().parseFromString(html, "text/html");
    return doc;
  }

  function tocFrom(doc) {
    const items = [];
    doc.querySelectorAll("section[id]").forEach(sec => {
      const h = sec.querySelector("h2");
      if (!h) return;
      const num = h.querySelector(".num");
      const label = h.textContent.replace(num ? num.textContent : "", "").trim();
      const group = num ? num.textContent.trim() : "Start here";
      items.push({ id: sec.id, label, group });
    });
    return items;
  }

  function renderToc(items) {
    const host = document.getElementById("toc");
    let group = "";
    items.forEach(it => {
      if (it.group !== group) {
        group = it.group;
        const h = document.createElement("h4");
        h.textContent = group;
        host.appendChild(h);
      }
      const a = document.createElement("a");
      a.href = "#m-" + it.id;
      a.textContent = it.label;
      a.dataset.close = "1";
      a.addEventListener("click", () => jump(it.id));
      host.appendChild(a);
    });
  }

  function jump(id) {
    document.getElementById("drawer").classList.remove("open");
    show("manual");
    const el = document.getElementById("m-" + id);
    if (el) setTimeout(() => el.scrollIntoView({ block: "start" }), 30);
  }

  // ---- today: the card, built from the manual's own sections plus a build-time snapshot
  function renderToday(doc) {
    const host = document.getElementById("today");
    const press = S.press || {}, money = S.money || {}, Q = S.seq || {};
    const actions = S.actions || [], decisions = S.decisions || [];
    const due = press.last_at ? hoursSince(press.last_at) : null;
    const nextIn = due === null ? 0 : Math.max(0, Math.round(30 - due));
    const runway = (press.bank || 0) + 12 - (press.sent || 0);

    const one = actions.length
      ? actions[0].what + " — " + (actions[0].minutes || "?") + " min"
      : (decisions.length ? "Decide: " + decisions[0].question : "Nothing. The estate is running.");

    host.innerHTML = `
      <div class="card">
        <div class="lbl">The one thing</div>
        <div class="big">${esc(one)}</div>
        <p>${actions.length ? esc(actions[0].blocks ? "unblocks " + actions[0].blocks : "") : "The machine runs; you steer."}</p>
        <div class="stat">
          <div><b>${press.sent ?? "—"}</b><span>posted</span></div>
          <div><b>${nextIn}h</b><span>next post</span></div>
          <div><b>${runway}d</b><span>bank</span></div>
          <div><b>${actions.length}</b><span>loops</span></div>
        </div>
      </div>

      <div class="card">
        <div class="lbl">Morning · 10 min</div>
        <ul class="check" data-group="am">
          <li data-k="am-estate"><i class="box">${tick}</i><span>Run the estate screen (or read the numbers above)</span></li>
          <li data-k="am-one"><i class="box">${tick}</i><span>Do the one thing, if it is under ten minutes</span></li>
          <li data-k="am-outcome"><i class="box">${tick}</i><span>Write today's single outcome</span></li>
          <li data-k="am-money"><i class="box">${tick}</i><span>Money channel only — no inbox, no feeds</span></li>
        </ul>
      </div>

      <div class="card">
        <div class="lbl">Evening · 5 min · the shutdown</div>
        <ul class="check" data-group="pm">
          <li data-k="pm-loops"><i class="box">${tick}</i><span>Write down every open loop</span></li>
          <li data-k="pm-tomorrow"><i class="box">${tick}</i><span>Name tomorrow's one outcome</span></li>
          <li data-k="pm-say"><i class="box">${tick}</i><span>Say it: the estate can run until 8am</span></li>
          <li data-k="pm-close"><i class="box">${tick}</i><span>Close the laptop, leave the room</span></li>
        </ul>
      </div>

      <div class="card">
        <div class="lbl">The three sentences</div>
        <p style="font:17px/1.5 var(--serif);color:#efe8fb;margin-top:6px">
          The machine runs; I steer, and steering has hours.<br>
          Three touches, then it ends. A reply is a person.<br>
          The business exists so that I can live.
        </p>
      </div>

      <div class="card" id="seqcard">
        <div class="lbl">The sequence · law 6</div>
        <h2 style="font-size:18px">Three touches, then it ends.</h2>
        <div class="stat">
          <div><b>${Q.leads ?? 0}</b><span>leads</span></div>
          <div><b>${Q.due ?? 0}</b><span>due</span></div>
          <div><b>${Q.sent ?? 0}</b><span>sent</span></div>
          <div><b>${Q.replied ?? 0}</b><span>replies</span></div>
        </div>
        <p style="margin-top:10px">${(Q.sending || []).length
          ? "Sending on " + (Q.sending || []).map(esc).join(", ") + "."
          : "Every rail is drafting only. SMTP or a Mastodon token arms a send."}
        ${(Q.drafting || []).length ? "<br>Drafting, not sending: " + (Q.drafting || []).map(esc).join(", ") + "." : ""}</p>
        <p style="margin-top:10px"><a href="#" data-jump="sequence" style="color:var(--violet)">How the sequence works →</a></p>
      </div>

      <div class="card">
        <div class="lbl">Money</div>
        <div class="stat">
          <div><b>${money.mrr ?? "—"}</b><span>MRR</span></div>
          <div><b>${money.cash ?? "—"}</b><span>cash</span></div>
          <div><b>${money.monthly_costs ?? "—"}</b><span>costs</span></div>
        </div>
        <p style="margin-top:10px">${money.mrr === null || money.mrr === undefined
          ? "Not recorded. Three numbers in data/ops.json once a week — a business without them is a mood."
          : "Recorded. Read on Mondays."}</p>
      </div>

      <div class="card" id="loop-check">
        <div class="lbl">If today is bad</div>
        <p style="margin-top:6px">1 · make it safe — run the screen, three-minute item or nothing.<br>
        2 · shrink the day — one outcome becomes none.<br>
        3 · leave it alone — no catch-up at 11pm.</p>
      </div>

      <div class="card">
        <div class="lbl">Overview</div>
        <div class="stat">
          <div><b>${S.works || "—"}</b><span>works</span></div>
          <div><b>${(S.offers || []).length || "—"}</b><span>ventures</span></div>
          <div><b>${(S.offers || []).filter(o => o.from === "free").length}</b><span>free</span></div>
        </div>
        <p style="margin-top:10px">${(S.offers || []).map(o => esc(o.name) + " · " + esc(o.from)).join("<br>")}</p>
        <p style="margin-top:10px;color:var(--dim);font-size:12px">snapshot ${esc(S.at || "")}</p>
      </div>`;

    host.querySelectorAll("[data-jump]").forEach(a => a.addEventListener("click", e => {
      e.preventDefault(); jump(a.dataset.jump);
    }));
    host.querySelectorAll(".check li").forEach(li => {
      li.addEventListener("click", () => {
        li.classList.toggle("done");
        const state = JSON.parse(localStorage.getItem(HIDE) || "{}");
        state[li.dataset.k] = li.classList.contains("done");
        localStorage.setItem(HIDE, JSON.stringify(state));
      });
      const st = JSON.parse(localStorage.getItem(HIDE) || "{}");
      if (st[li.dataset.k]) li.classList.add("done");
    });
  }

  function renderManual(doc) {
    const host = document.getElementById("manual");
    host.innerHTML = "";
    doc.querySelectorAll("header.mast").forEach(el => host.appendChild(el.cloneNode(true)));
    doc.querySelectorAll("main section").forEach(sec => {
      const clone = sec.cloneNode(true);
      clone.id = "m-" + sec.id;
      clone.querySelectorAll("a[href^='#']").forEach(a => {
        const target = a.getAttribute("href").slice(1);
        a.setAttribute("href", "#m-" + target);
        a.addEventListener("click", e => { e.preventDefault(); jump(target); });
      });
      host.appendChild(clone);
    });
  }

  function renderCard(doc) {
    const host = document.getElementById("card");
    const src = doc.getElementById("card");
    host.innerHTML = "";
    if (src) host.appendChild(src.querySelector("div[style*='border']") || src);
  }

  function hoursSince(iso) {
    const t = Date.parse(iso);
    return isNaN(t) ? null : (Date.now() - t) / 36e5;
  }
  const tick = '<svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5"/></svg>';
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function show(view) {
    ["today", "manual", "card"].forEach(v => {
      document.getElementById(v).classList.toggle("hidden", v !== view);
    });
    document.querySelectorAll("#tabs button").forEach(b =>
      b.classList.toggle("on", b.dataset.view === view));
    window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  }

  document.querySelectorAll("#tabs button").forEach(b =>
    b.addEventListener("click", () => show(b.dataset.view)));

  const drawer = document.getElementById("drawer");
  document.getElementById("openDrawer").addEventListener("click", () => drawer.classList.add("open"));
  drawer.addEventListener("click", e => {
    if (e.target.dataset.close !== undefined || e.target.classList.contains("scrim"))
      drawer.classList.remove("open");
  });
  document.getElementById("lockNow").addEventListener("click", () => {
    sessionStorage.removeItem("ops.plain");
    location.reload();
  });
  document.getElementById("installHint").addEventListener("click", () => {
    alert("iPhone: Share → Add to Home Screen.\\nAndroid: menu → Install app.\\n" +
          "Once installed it opens offline and asks for the passphrase once per device.");
  });

  async function unlock(phrase, remember) {
    const err = document.getElementById("err");
    err.textContent = "";
    const btn = document.getElementById("unlock");
    btn.disabled = true; btn.textContent = "Unsealing…";
    try {
      const html = await open(phrase);
      if (remember) localStorage.setItem(KEY, phrase);
      else sessionStorage.setItem("ops.plain", phrase);
      start(html);
    } catch (e) {
      err.textContent = "That phrase does not open this file.";
      btn.disabled = false; btn.textContent = "Unlock";
      localStorage.removeItem(KEY);
    }
  }

  function start(html) {
    const doc = parse(html);
    document.getElementById("lock").remove();
    document.getElementById("bar").classList.remove("hidden");
    document.getElementById("app").classList.remove("hidden");
    renderToc(tocFrom(doc));
    renderToday(doc);
    renderManual(doc);
    renderCard(doc);
    document.getElementById("foot").innerHTML =
      "Sealed " + esc(P.sealed_at) + " · " + esc(P.alg) + " · " + esc(P.kdf) +
      "<br>Private. Describes how the estate is run, not what it sells.";
    show("today");
  }

  const saved = localStorage.getItem(KEY);
  if (saved) {
    unlock(saved, true);
  } else {
    document.getElementById("phrase").addEventListener("keydown", e => {
      if (e.key === "Enter") document.getElementById("unlock").click();
    });
    document.getElementById("unlock").addEventListener("click", () => {
      const phrase = document.getElementById("phrase").value;
      if (phrase) unlock(phrase, true);
    });
    document.getElementById("phrase").focus();
  }
})();
</script>
</body>
</html>
"""

MANIFEST = {
    "name": "Operator's Bible · Jacaranda Labs",
    "short_name": "Ops",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0a0710",
    "theme_color": "#0a0710",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

SW = """// Cache the shell so the manual opens offline, once unlocked. The ciphertext is what is cached —
// the passphrase never leaves the device and is never stored anywhere but this browser's storage.
const CACHE = "ops-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icon-192.png", "/icon-512.png"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(e.request, copy)).catch(() => {});
      return res;
    }).catch(() => caches.match("/index.html")))
  );
});
"""


def icon(size: int) -> bytes:
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (size, size), (10, 7, 16))
    d = ImageDraw.Draw(im)
    cx = cy = size // 2
    import math
    for a in range(0, 360, 72):
        rad = math.radians(a)
        rx, ry = size * 0.115, size * 0.21
        px, py = cx + math.sin(rad) * size * 0.25, cy - math.cos(rad) * size * 0.25
        d.ellipse([px - rx, py - ry, px + rx, py + ry], fill=(167, 139, 250))
    r = size * 0.07
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(232, 70, 124))
    from io import BytesIO
    buf = BytesIO()
    im.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="phrase", default=os.environ.get("OPS_PASSPHRASE", ""))
    ap.add_argument("--out", default=None, help="output folder (default ./dist)")
    ap.add_argument("--bible", default=None, help="path to the plaintext operator-bible.html")
    ap.add_argument("--deploy", action="store_true")
    ap.add_argument("--project", default=PROJECT)
    a = ap.parse_args()
    global DIST
    if a.out:
        DIST = Path(a.out).expanduser().resolve()
    if not a.phrase:
        print("need a passphrase: --pass '…' (or OPS_PASSPHRASE)", file=sys.stderr)
        return 2
    bible_path = Path(a.bible).expanduser() if a.bible else BIBLE
    if not bible_path.exists():
        print(f"missing {bible_path} — pass --bible", file=sys.stderr)
        return 2

    bible = bible_path.read_bytes()
    sealed = seal(bible, a.phrase)
    payload = {"v": sealed["v"], "iterations": ITERATIONS, "salt": sealed["salt"],
               "iv": sealed["iv"], "ct": sealed["ct"], "sealed_at": sealed["sealed_at"],
               "alg": sealed["alg"], "kdf": sealed["kdf"]}

    DIST.mkdir(parents=True, exist_ok=True)
    html = (SHELL.replace("__PAYLOAD__", json.dumps(payload))
                 .replace("__SNAPSHOT__", json.dumps(snapshot())))
    (DIST / "index.html").write_text(html)
    (DIST / "index.html").write_text(html)              # / and /index.html both resolve on Pages
    (DIST / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=1))
    (DIST / "sw.js").write_text(SW)
    (DIST / "icon-192.png").write_bytes(icon(192))
    (DIST / "icon-512.png").write_bytes(icon(512))
    (DIST / "_headers").write_text(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  X-Frame-Options: DENY\n"
        "  Referrer-Policy: no-referrer\n  Cache-Control: no-store\n"
        "/icon-*.png\n  Cache-Control: public, max-age=604800\n"
        "/manifest.webmanifest\n  Cache-Control: public, max-age=3600\n")

    size = (DIST / "index.html").stat().st_size
    print(f"sealed {len(bible) // 1024} KB of manual → {size // 1024} KB of ciphertext")
    print(f"  {sealed['kdf']} · {sealed['alg']} · sealed {sealed['sealed_at']}")

    if a.deploy:
        token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
        acct = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        if not (token and acct):
            print("need CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID to deploy", file=sys.stderr)
            return 2
        env = {**os.environ, "CLOUDFLARE_API_TOKEN": token, "CLOUDFLARE_ACCOUNT_ID": acct}
        subprocess.run(["npx", "--yes", "wrangler@4", "pages", "project", "create", a.project,
                        "--production-branch", "main"], env=env, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        r = subprocess.run(["npx", "--yes", "wrangler@4", "pages", "deploy", str(DIST),
                            "--project-name", a.project, "--branch", "main",
                            "--commit-dirty=true"], env=env, check=False)
        print(f"  → https://{a.project}.pages.dev")
        return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
