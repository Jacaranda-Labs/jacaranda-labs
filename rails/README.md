# The rails

Two things live here: the image branch that the AttestOS press engine had and the smaller company
rails did not, and the tool that finishes the estate's Nostr identities.

## Why this exists

The owner's rule since 2026-09-27 is that every post carries an image. The AttestOS / Tapstall press
engine implements it (`press/auto.py`: `make_image()`, a static fallback, `image_alerts()`). The
Mechanism Audit and Open Practice rails were built later and smaller, and only their Pinterest branch
ever attached an image — so a text-only post was not an error, and nothing complained.

Measured against the platforms on 2026-11-08, before this branch:

| identity | rail | posts | with image |
|---|---|---|---|
| AttestOS | Bluesky / Mastodon / Nostr | 7 / 6 / 10 | 7/7 · 6/6 · 10/10 |
| Open Practice | Bluesky / Mastodon / Nostr | 6 / 6 / 6 | **0/6 · 0/6 · 0/6** |
| Mechanism Audit | Bluesky / Mastodon / Nostr | 1 / 1 / 2 | **0/1 · 0/1 · 0/2** |
| DeskOS | Nostr | 6 | 5/6 |
| TightBucket | Nostr | 5 | 5/5 |

## What is in the box

| file | what it is |
|---|---|
| `postimage.py` | the shared branch: resolve a card, sniff and measure it, and build each platform's payload. Stdlib only, 21 self-checks (`python3 postimage.py --selftest`) |
| `apply_image_branch.py` | patches a rail's `social.py` in place, idempotently — same patcher for both twins |
| `update_tests.py` | brings an existing `test_social.py` up to the new contract |
| `test_image_branch.py` | 12 tests: no image means no post, and each rail carries the image once it has one |
| `nostr_identity.py` | `keys` / `presence` / `profile` / `sync` for the six identities |
| `mechanism-audit/` | the patched rail, its tests, its fallback card and its patched workflow |
| `open-practice/` | the same, in that repo's layout (`tools/social.py`) |

## The branch, per rail

| rail | how the image travels |
|---|---|
| Bluesky | `uploadBlob` → `app.bsky.embed.images`, with `aspectRatio` from the file header. One embed only, so the image wins over the link card and the link stays a clickable facet |
| Mastodon | `POST /api/v2/media` (multipart, with alt text) → `media_ids[]` on the status; a 202 is polled until the media is ready |
| Nostr | `["imeta", "url …", "m …", "dim WxH", "alt …"]` plus the URL on its own line in the content |
| Discord | `embeds[0].image.url` |
| Tumblr | inline markdown image + `native_inline_images=true`, so Tumblr hosts its own copy |
| Pinterest | `assets[0].image.url` — this rail already did it, and keeps its own tall pin art |

Resolution order: an explicit `--image`, then a `[[image:slug]]` hint in the text, then `*_CARD_URL`,
then the site's og card, then a second hosted card, then the bundled `assets/fallback-card.png`. If all
of that fails, **every rail fails** with the reason. `--allow-text-only` exists for the day the card
host is down and the news cannot wait; it is deliberately awkward to type.

## Using it in a rail repo

```bash
python3 apply_image_branch.py --file tools/social.py --prefix OP_ --brand "Open Practice"
python3 update_tests.py tools/tests/test_social.py
cp postimage.py tools/ && cp test_image_branch.py tools/tests/
mkdir -p assets && cp <brand og card> assets/fallback-card.png
python3 -m unittest discover -s tools/tests -p "test_*.py"
```

The patcher also adds `*_CARD_URL` to the workflow's env block, because a rail that reads a secret the
workflow never passes is exactly the bug that kept Tumblr offline for a day.

## Nostr identities

```bash
python3 nostr_identity.py keys        # do the nsecs match the npubs? 6/6
python3 nostr_identity.py presence    # what each key has published, read back off the relays
python3 nostr_identity.py sync        # re-broadcast existing signed events to every relay
python3 nostr_identity.py profile tightbucket   # publish a kind-0 profile for one identity
```

Keys are read from `~/.nostr-keys.json` (mode 0600). **No nsec is ever in this repository**, in a
commit, or in a log line. `sync` never signs anything: it re-sends events that already exist, which is
ordinary relay propagation and is idempotent.

Why `sync` matters: the estate's notes were not on the same relays. AttestOS was on `relay.nostr.net`
and `relay.primal.net`; TightBucket's five notes existed **only** on `nos.lol`. A reader whose client
ships with one of those sees an empty profile and concludes the rail is dead. After one sync pass and a
second confirm pass, all six identities are readable from all three relays that answer.
