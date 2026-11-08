#!/usr/bin/env python3
"""apply_image_branch.py — give the small company rails the image branch the AttestOS engine has.

Both rails are the same file shape with different env prefixes, so one patcher handles both:

    python3 apply_image_branch.py --check          # say what would change, touch nothing
    python3 apply_image_branch.py                  # patch in place
    python3 apply_image_branch.py --file path.py --prefix OP_ --brand "Open Practice"

What it rewrites, and why:

  post_bsky      uploadBlob → app.bsky.embed.images (one embed only; the image wins over the link card,
                 and the link stays as a facet so it is still clickable)
  post_mastodon  POST /api/v2/media → media_ids[] on the status
  post_nostr     ["imeta", "url …", "m …", "dim WxH", "alt …"] plus the url in the content
  post_discord   embeds[0].image.url
  post_tumblr    inline markdown image + native_inline_images=true
  post           resolves the image once, and fails every rail when there is none — no silent
                 text-only fallback, which is exactly how the rule got broken
  verify         reports the card, so a dead card URL is visible before a post goes out
  main           --image, --allow-text-only

The patch is idempotent: a file that already imports postimage is left alone.

Stdlib only. Run the tests afterwards:  python3 -m unittest discover -s tests -p "test_social.py"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- new function bodies
BSKY = '''def post_bsky(text: str, link: str = "", tags: list[str] | None = None,
              image: "postimage.Img | None" = None) -> tuple[bool, str]:
    ident, pw = env("{P}BSKY_ID", "{P}BSKY_PASS")
    if not (ident and pw):
        return False, "skip: {P}BSKY_ID/{P}BSKY_PASS not set"
    st, sess = _json_post("https://bsky.social/xrpc/com.atproto.server.createSession",
                          {{"identifier": ident, "password": pw}})
    if st != 200 or not isinstance(sess, dict) or "accessJwt" not in sess:
        return False, f"login failed: {{st}} {{str(sess)[:120]}}"
    auth = {{"Authorization": f"Bearer {{sess['accessJwt']}}"}}
    if image is None:
        try:
            image = _image(text, link)
        except postimage.NoImage as e:
            return False, f"no image, not posting: {{e}}"
    try:
        blob = postimage.bluesky_upload(
            image, auth,
            poster=lambda url, data, headers: _post_raw(url, data, headers))
    except (postimage.NoImage, RuntimeError) as e:
        return False, f"image upload failed, not posting: {{e}}"
    record = postimage.bluesky_record(
        text, _facets(text, link or ""), image, blob,
        time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()), tags=tags)
    st, body = _json_post("https://bsky.social/xrpc/com.atproto.repo.createRecord",
                          {{"repo": sess["did"], "collection": "app.bsky.feed.post", "record": record}}, auth)
    if st != 200:
        return False, f"createRecord {{st}}: {{str(body)[:150]}}"
    return True, (body or {{}}).get("uri", "posted")
'''

MASTODON = '''def post_mastodon(text: str, image: "postimage.Img | None" = None) -> tuple[bool, str]:
    inst, tok = env("{P}MASTODON_INSTANCE", "{P}MASTODON_TOKEN")
    if not (inst and tok):
        return False, "skip: {P}MASTODON_INSTANCE/{P}MASTODON_TOKEN not set"
    host = inst.replace("https://", "").strip("/")
    auth = {{"Authorization": f"Bearer {{tok}}"}}
    if image is None:
        try:
            image = _image(text, "")
        except postimage.NoImage as e:
            return False, f"no image, not posting: {{e}}"
    # media first: a status that names a media id that does not exist is rejected outright
    media_id = ""
    try:
        body, ctype = postimage.mastodon_media_body(image)
        st, media = _req(f"https://{{host}}/api/v2/media", body,
                         {{**auth, "Content-Type": ctype}}, "POST")
        if st in (200, 201, 202) and isinstance(media, dict) and media.get("id"):
            media_id = str(media["id"])
            if st == 202:                                   # accepted, still processing
                for _ in range(10):
                    time.sleep(1.5)
                    st2, m2 = _req(f"https://{{host}}/api/v1/media/{{media_id}}", headers=auth)
                    if st2 == 200:
                        break
        else:
            return False, f"media upload {{st}}, not posting: {{str(media)[:120]}}"
    except postimage.NoImage as e:
        return False, f"no image, not posting: {{e}}"
    fields = postimage.mastodon_status_fields(text, media_id)
    st, body = _req(f"https://{{host}}/api/v1/statuses", urllib.parse.urlencode(fields).encode(),
                    {{**auth, "Content-Type": "application/x-www-form-urlencoded"}}, "POST")
    if st not in (200, 201):
        return False, f"statuses {{st}}: {{str(body)[:150]}}"
    return True, (body or {{}}).get("url", "posted")
'''

NOSTR = '''def post_nostr(text: str, relays: list[str] | None = None,
               image: "postimage.Img | None" = None) -> tuple[bool, str]:
    sk = _sk()
    if not sk:
        return False, "skip: {P}NOSTR_NSEC not set"
    try:
        import coincurve
    except ImportError:
        return False, "skip: coincurve not installed"
    if image is None:
        try:
            image = _image(text, "")
        except postimage.NoImage as e:
            return False, f"no image, not posting: {{e}}"
    try:
        tags = [postimage.nostr_imeta(image)]
        content = postimage.nostr_content(text, image)
    except postimage.NoImage as e:
        return False, f"no image url, not posting: {{e}}"
    relays = relays or [r.strip() for r in (os.environ.get("{P}NOSTR_RELAYS") or
                        # measured 2026-11-08: nos.lol, relay.nostr.band and nostr.mom time out from
                        # here; these answer in under two seconds
                        "wss://relay.damus.io,wss://relay.primal.net,wss://relay.nostr.net").split(",") if r.strip()]
    pk = coincurve.PrivateKey(sk).public_key.format(compressed=True)[1:].hex()
    ev = {{"pubkey": pk, "created_at": int(time.time()), "kind": 1,
          "tags": tags, "content": content}}
    ser = json.dumps([0, ev["pubkey"], ev["created_at"], ev["kind"], ev["tags"], ev["content"]],
                     separators=(",", ":"), ensure_ascii=False)
    eid = hashlib.sha256(ser.encode()).hexdigest()
    sig = coincurve.PrivateKey(sk).sign_schnorr(bytes.fromhex(eid), aux_randomness=os.urandom(32)).hex()
    ev.update({{"id": eid, "sig": sig}})
    ok = _publish_nostr(ev, relays)
    return (ok, f"event {{eid[:16]}}… " + ("accepted by a relay" if ok else "no relay accepted it"))
'''

DISCORD = '''def post_discord(text: str, image: "postimage.Img | None" = None) -> tuple[bool, str]:
    (wh,) = env("{P}DISCORD_WEBHOOK")
    if not wh:
        return False, "skip: {P}DISCORD_WEBHOOK not set"
    if image is None:
        try:
            image = _image(text, "")
        except postimage.NoImage as e:
            return False, f"no image, not posting: {{e}}"
    st, body = _json_post(wh + ("&" if "?" in wh else "?") + "wait=true",
                          postimage.discord_payload(text, image, username="{BRAND}"))
    if st not in (200, 204):
        return False, f"webhook {{st}}: {{str(body)[:150]}}"
    return True, (body or {{}}).get("id", "posted") if isinstance(body, dict) else "posted"
'''

TUMBLR = '''def post_tumblr(text: str, tags: list[str] | None = None,
                image: "postimage.Img | None" = None) -> tuple[bool, str]:
    ck, cs, tok, tsec, blog = env("{P}TUMBLR_CK", "{P}TUMBLR_CS", "{P}TUMBLR_TOKEN",
                                  "{P}TUMBLR_TOKEN_SECRET", "{P}TUMBLR_BLOG")
    if not all([ck, cs, tok, tsec, blog]):
        return False, "skip: tumblr needs the OAuth exchange first (see tumblr_connect.py)"
    if image is None:
        try:
            image = _image(text, "")
        except postimage.NoImage as e:
            return False, f"no image, not posting: {{e}}"
    url = f"https://api.tumblr.com/v2/blog/{{blog}}/post"      # singular: the form-encoded route
    fields = {{"type": "text", "format": "markdown", "title": _tumblr_title(text)}}
    fields.update(postimage.tumblr_fields(text, image))
    if tags:
        fields["tags"] = ",".join(t.replace("#", "")[:40] for t in tags[:5])
    st, resp = _req(url, urllib.parse.urlencode(fields).encode(),
                    {{"Authorization": _oauth1("POST", url, fields, ck, cs, tok, tsec),
                     "Content-Type": "application/x-www-form-urlencoded"}}, "POST")
    if st not in (200, 201):
        return False, f"post {{st}}: {{str(resp)[:150]}}"
    return True, str((resp.get("response") or {{}}).get("id", "posted"))
'''

POST = '''def post(text: str, link: str = "", tags: list[str] | None = None,
         rails: list[str] | None = None, dry: bool = False,
         image: str = "", allow_text_only: bool = False) -> dict:
    """Post everywhere, with an image on every rail.

    `image` may be a URL or a local path; empty means "use the site card, then the bundled fallback".
    If neither resolves, every rail fails unless `allow_text_only` is set — the rule is that a post
    carries an image, so a missing image is an outage, not a style choice.
    """
    tags = tags or []
    # the link belongs in the text on every rail: a post without it is a dead end
    full = text if not link or link in text else f"{{text}}\\n\\n{{link}}"
    want = rails or armed()
    results: dict[str, tuple[bool, str]] = {{}}

    card = None
    why = ""
    try:
        card = _image(full, link, override=image)
    except postimage.NoImage as e:
        why = str(e)

    if card is None and not allow_text_only:
        for name in want:
            results[name] = (False, f"not posted: no image ({{why}})")
        return results

    for name in want:
        fn = globals().get(RAILS.get(name, ""))
        if not fn:
            results[name] = (False, "unknown rail")
            continue
        if dry:
            results[name] = (True, f"dry run" + (f" with {{card}}" if card else " WITHOUT AN IMAGE"))
            continue
        try:
            if name == "bsky":
                results[name] = post_bsky(full, link=link, tags=tags, image=card)
            elif name == "mastodon":
                results[name] = post_mastodon(full, image=card)
            elif name == "nostr":
                results[name] = post_nostr(full, image=card)
            elif name == "discord":
                results[name] = post_discord(full, image=card)
            elif name == "tumblr":
                results[name] = post_tumblr(full, tags=tags, image=card)
            elif name == "pinterest":
                # a pin has its own tall-format art; an explicit image or a [[image:]] hint wins,
                # otherwise the pin keeps the brand's pin card exactly as before
                explicit = bool(image or _IMAGE_HINT.search(full or ""))
                results[name] = post_buffer(full, link=link or SITE,
                                            image=(card.url if explicit else f"{PINTEREST_IMAGE}"),
                                            title=text.split("\\n")[0][:100])
            else:
                results[name] = fn(full)
        except Exception as e:  # noqa: BLE001
            results[name] = (False, f"raised {{e!r}}"[:180])
    return results
'''

HELPERS = '''# ----------------------------------------------------------------------------- the image branch
_HERE = os.path.dirname(os.path.abspath(__file__))
# the fallback sits beside the rail, or one level up if the rail lives in tools/
FALLBACK_CARD = next((p for p in (os.path.join(_HERE, "assets", "fallback-card.png"),
                                 os.path.join(os.path.dirname(_HERE), "assets", "fallback-card.png"))
                      if os.path.exists(p)), os.path.join(_HERE, "assets", "fallback-card.png"))
# a per-post image can be named in the text itself: [[image:slug]] or [[image:https://…]]
_IMAGE_HINT = re.compile(r"\\[\\[image:([^\\]]+)\\]\\]")


def _image(text: str, link: str = "", override: str = "") -> "postimage.Img":
    """Resolve the image for one post: an explicit one, a hint in the text, or the site card.

    Always ends with the bundled fallback, so a card 404 cannot silently produce a text-only post.
    A hint that is not a URL is resolved against the site's own asset folder.
    """
    alt = " ".join(text.split())[:280]
    want = (override or os.environ.get("{P}CARD_URL") or "").strip()
    hint = _IMAGE_HINT.search(text or "")
    if not want and hint:
        want = hint.group(1).strip()
        if not want.startswith(("http://", "https://")):
            want = SITE + "/{ASSETS}/" + want
    url = want or CARD
    return postimage.resolve_chain([url, CARD_FALLBACK], alt, FALLBACK_CARD)


def _post_raw(url: str, data: bytes, headers: dict) -> dict:
    """Raw body POST, for uploadBlob: the JSON helper would re-encode the image as a string."""
    st, body = _req(url, data, headers, "POST")
    if st != 200:
        raise RuntimeError(f"{url} → {st} {str(body)[:160]}")
    return body if isinstance(body, dict) else {}


'''
VERIFY_EXTRA = '''    # the card is part of the credential now: a dead card URL means the rail cannot post
    try:
        img = _image("", "")
        out["image"] = f"{{img.mime}} {{img.dim}} {{img.size}}B"
    except postimage.NoImage as e:
        out["image"] = f"FAIL {{e}}"
'''


def replace_function(src: str, name: str, new: str) -> tuple[str, bool]:
    """Replace one top-level function, from its `def` to the next top-level def or section marker."""
    pat = re.compile(rf"^def {re.escape(name)}\(.*?(?=^def |^# -{{10,}}|^RAILS =|\Z)", re.M | re.S)
    m = pat.search(src)
    if not m:
        return src, False
    return src[:m.start()] + new.rstrip("\n") + "\n\n\n" + src[m.end():], True


def render(body: str, prefix: str, brand: str) -> str:
    """Fill the per-file placeholders and undo the doubled braces these templates were written with."""
    return (body.replace("{P}", prefix).replace("{BRAND}", brand)
                .replace("{PINTEREST_IMAGE}", "{SITE}/brand/card-activities.png" if prefix == "OP_"
                         else "{SITE}/assets/product-audit-1200.png")
                .replace("{{", "{").replace("}}", "}"))


def patch(src: str, prefix: str, brand: str, brand_slug: str) -> tuple[str, list[str]]:
    done = []
    if "import postimage" in src:
        return src, ["already patched"]

    # 1. import + config
    src = src.replace("import urllib.request\n",
                      "import urllib.request\nimport re\n\ntry:\n    import postimage\nexcept ImportError:  # pragma: no cover - the module sits next to this file in the repo\n"
                      "    import sys as _sys\n    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))\n    import postimage\n", 1)
    assets = "assets" if prefix == "MA_" else "brand"
    second = "product-audit-1200.png" if prefix == "MA_" else "github-social-1280x640.png"
    src = re.sub(r"^CARD = .*$",
                 lambda m: (m.group(0)
                            + f'\n# the second hosted card: if the og card 404s, this is still a url a platform can fetch'
                            + f'\nCARD_FALLBACK = f"{{SITE}}/{assets}/{second}"'),
                 src, count=1, flags=re.M)
    helpers = (HELPERS.replace("{P}", prefix).replace("{BRAND}", brand)
               .replace("{ASSETS}", "assets" if prefix == "MA_" else "brand"))
    src = src.replace("TIMEOUT = 30", "TIMEOUT = 30\n" + helpers, 1)
    done.append("helpers")

    if "_tumblr_title" not in src:
        src = src.replace("def post_tumblr(", '''def _tumblr_title(text: str) -> str:
    """Tumblr themes render a title above the body; the first sentence is the least bad one."""
    first = (text.strip().split("\\n", 1)[0] or "").strip()
    if len(first) > 120:
        first = first.split(". ", 1)[0]
    return first[:120]


def post_tumblr(''', 1)

    for name, body in (("post_bsky", BSKY), ("post_mastodon", MASTODON), ("post_nostr", NOSTR),
                       ("post_discord", DISCORD), ("post_tumblr", TUMBLR)):
        new = render(body, prefix, brand)
        src, ok = replace_function(src, name, new)
        done.append(("replaced " if ok else "MISSING ") + name)

    src, ok = replace_function(src, "post", render(POST, prefix, brand))
    done.append(("replaced " if ok else "MISSING ") + "post")

    # verify(): say whether the image resolves
    marker = "    return out\n\n\ndef main("
    if marker in src:
        src = src.replace(marker, render(VERIFY_EXTRA, prefix, brand) + "    return out\n\n\ndef main(", 1)
    else:
        done.append("MISSING verify anchor")
    done.append("verify")

    # main(): the two flags
    src = src.replace('ap.add_argument("--dry", action="store_true")',
                      'ap.add_argument("--dry", action="store_true")\n'
                      '    ap.add_argument("--image", default="", help="image url or path for this post")\n'
                      '    ap.add_argument("--allow-text-only", action="store_true",\n'
                      '                    help="post without an image (breaks the rule; for a broken card only)")', 1)
    src = src.replace("results = post(args.text, link=args.link, tags=tags, rails=wanted, dry=args.dry)",
                      "results = post(args.text, link=args.link, tags=tags, rails=wanted, dry=args.dry,\n"
                      "                   image=getattr(args, \"image\", \"\"),\n"
                      "                   allow_text_only=getattr(args, \"allow_text_only\", False))", 1)
    done.append("main")
    return src, done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="")
    ap.add_argument("--prefix", default="MA_")
    ap.add_argument("--brand", default="")
    ap.add_argument("--brand-slug", default="")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    targets = ([Path(args.file)] if args.file else
               [HERE / "mechanism-audit" / "social.py", HERE / "open-practice" / "social.py"])
    bad = 0
    for path in targets:
        if not path.exists():
            print(f"  ✗ {path} not found")
            bad += 1
            continue
        prefix = args.prefix if args.file else ("MA_" if "mechanism" in str(path) else "OP_")
        brand = args.brand if args.file else ("Mechanism Audit" if prefix == "MA_" else "Open Practice")
        slug = args.brand_slug if args.file else ("mechanism-audit" if prefix == "MA_" else "open-practice")
        src = path.read_text(encoding="utf-8")
        out, done = patch(src, prefix, brand, slug)
        missing = [d for d in done if d.startswith("MISSING")]
        state = "would patch" if args.check else "patched"
        if out == src:
            print(f"  = {path.name} ({prefix}): {', '.join(done)}")
        else:
            print(f"  {'✓' if not missing else '✗'} {state} {path} ({prefix}): {', '.join(done)}")
            if not args.check:
                path.write_text(out, encoding="utf-8")
        if missing:
            bad += 1
    if not args.check:
        for path in targets:
            assets = path.parent / "assets"
            assets.mkdir(exist_ok=True)
            print(f"  · fallback card expected at {assets / 'fallback-card.png'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
