# The ops site — `jacaranda-ops.pages.dev`

The operator's bible, sealed, so it opens on any phone without a terminal, a laptop or a repo.

**What is in this folder is ciphertext only.** `index.html` is the manual encrypted with AES-256-GCM
(key derived with PBKDF2-SHA256, 310,000 iterations) and decrypted *in the browser* after the
passphrase is typed. The repository is public; the manual is not. Nothing here is plaintext, and the
passphrase is never stored anywhere but the reader's own `localStorage`.

```
# rebuild (needs the plaintext manual, which is never committed)
python3 ops/build_ops_site.py --pass '<passphrase>'           # → ops/index.html
python3 ops/build_ops_site.py --pass '<passphrase>' --deploy  # + push to Cloudflare Pages

# then commit the regenerated files; the workflow deploys them
```

`.github/workflows/ops.yml` deploys this folder to the `jacaranda-ops` Pages project on every push
that touches it.

## Two pages, one project

| path | what it is | sealed? |
|---|---|---|
| `/` | the operator's bible — Today, The manual, The card | **yes**, AES-256-GCM, passphrase once per device |
| `/live.html` | *"The business exists so that a person can live. Not the reverse."* — the statement the manual is written to serve. One file, no scripts, no fonts, 17 KB | no, it is meant to be read |

`/live.html` is phone-first on purpose: it is the page to open when the week has gone sideways and
the question is *what is this for*, not *what is next*.

## What the sealed site is

* **one page, one file plus four small assets** — no framework, no CDN, no font, no network at runtime
* **installable** to the home screen (manifest + service worker), and it opens **offline** once installed
* **contents drawer**, not a sidebar — a sidebar is a desktop idea
* **three screens**: *Today* (the card, the two loops with tap-to-tick checkboxes, the one thing, the
  three sentences, money), *The manual* (all 25 sections, re-typeset for a 390 px screen), *The card*
* `X-Robots-Tag: noindex`, `no-referrer`, `no-store`, and the site is not linked from anywhere

## If the passphrase is lost

Regenerate with a new one — `ops/build_ops_site.py --pass '<new>'` — and commit. There is no recovery
path by design: there is no account, no server and no reset link.
