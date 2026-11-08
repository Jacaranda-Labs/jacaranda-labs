# Jacaranda — one site for three catalogues

Laboratories (the six ventures) · Portfolio (Courage Garikai) · Publications (the catalogue).
Built with the Python standard library. No JavaScript, no framework, no build step beyond one file.

```
python3 build.py            # → dist/
python3 build.py --check    # build, then assert: no <script>, no dead internal links, one h1 per page,
                            # every work states its availability
python3 build.py --serve    # build, then serve on 0.0.0.0:8080
```

## What is in here

| path | what it is |
|---|---|
| `build.py` | the whole site generator, ~700 lines, stdlib only |
| `data/works.json` | 20 works: title, subtitle, blurb, facts, contents, formats, availability |
| `data/ventures.json` | the six ventures, their live URLs and the works that study each one |
| `data/author.json` | the author record used on the portfolio page |
| `data/earlier.json` | the two earlier works, kept for the record |
| `assets/og.png` | 1200×630 share card |
| `dist/` | the built site — 25 pages, 369 KB of HTML, fully self-contained |

## Where the content comes from

All of it is a snapshot of the private `stpi-cloud/publications` repository, taken 2026-11-07:

* `README.md` — the publication catalogue, source of the blurbs
* `books/*/edition-manifest.json`, `papers/*/edition-manifest.json` — title, subtitle, edition, funding,
  case disclosure, contents, `public_release_authorized`
* `sites/data/legacy-catalogue.json` — the ten published editions with their download links
* `sites/data/ventures.json`, `sites/data/author.json` — ventures and author record

Nothing on the site is invented. If a fact is not in those files it is not on a page. The only things added
here are navigation, layout and the availability statement.

## One deliberate data decision

The legacy catalogue and the current manifests both described *The Sovereign Micro-Enterprise* and
*Emotional Engineering*. They are the same works, so they are merged rather than listed twice: the report
carries the published edition's PDF/HTML/MD links, and *Emotional Engineering* stays a private author-review
book. That is why the catalogue reads 20 works, not 22.

## Availability, stated per work

| state | meaning | count |
|---|---|---|
| `available` | published edition, links to PDF/EPUB/HTML/MD in `formats` | 10 |
| `published` | a public edition exists but is not hosted here | 0 |
| `catalogued` | listed for the record, no copy distributed | 3 |
| `private` | private author-review edition, copy on request by email | 7 |

`--check` fails if a work page does not say which of these it is. Change the state in `data/works.json`;
the copy, tags and badges follow.

## postcheck — the two owner rules

`tools/postcheck.py` audits the estate's live social feeds against the two rules: every post carries an
image, and value posts outnumber promo at least 2:1. It reads Bluesky, Mastodon and Nostr back off the
platforms themselves. `.github/workflows/postcheck.yml` runs it daily and fails the run when a rail
breaks either rule. See `social-audit-2026-11-08.md` for the first run's findings.

## House rules the build keeps

* **No JavaScript.** The CSP is `default-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:` and
  every page is written to survive it — which is also why the preview renders correctly in a sandboxed frame.
* **Inline everything.** CSS is in the page, the mark is inline SVG, the favicon is a data-free SVG file.
  The only external references are ordinary links out to the ventures and the publishers' release files.
* **No download links for private editions.** Only the `formats` map produces a download button.
* **The disclosure travels with the work.** Case disclosures come from the manifests, not from this repo.

## Design (rebuilt 2026-11)

The front end was replaced wholesale. Dark editorial base (`--ink #0a0710`, violet `#8b5cf6`, magenta
`#e8467c`, gold `#e9b872`) with one paper-white band for the catalogue, because the books are paper and
the site is night.

* **Motion that carries meaning:** a 12-second video hero on every page (generated artwork, `zoompan`
  loops shipped as WebM + MP4 with a JPEG poster), scroll reveals, a cursor glow, a marquee of venture
  names, and cards that tilt under the pointer.
* **Interactive:** venture cards open one shared `<dialog>`; the catalogue has group chips, live search
  and an empty state; `⌘K` / `/` opens a palette over every venture, work and page.
* **Built, not fetched:** `static/app.css` and `static/app.js` are inlined into every page by `build.py`.
  No framework, no CDN, no external font. `window.__index` is the palette's data.
* **Cheap to keep:** artwork is generated once by `tools/make_og.py` (share card) and ffmpeg loops under
  `assets/art/` (76 s of encoding, ~250 KB per clip). `build.py --check` refuses a build whose media is
  missing.
* **Degrades:** `prefers-reduced-motion` drops the video and the reveals; print drops the chrome; the
  CSP in `_headers` is now `default-src 'self'` rather than `default-src 'none'`, since every asset is
  local and inline.

## Deploying

**Live:** https://jacaranda-labs.pages.dev (Cloudflare Pages) · https://jacaranda-labs.github.io/jacaranda-labs/
(static mirror) · source: https://github.com/Jacaranda-Labs/jacaranda-labs

A push to `main` builds, checks and deploys both. `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID` are repo secrets. Locally:

```
export CLOUDFLARE_API_TOKEN=...  CLOUDFLARE_ACCOUNT_ID=...  PROJECT=jacaranda-labs
./deploy.sh                 # builds, checks, uploads dist/ to Cloudflare Pages
./deploy.sh --dry-run       # prints what it would do, touches nothing
```

Replace `SITE` at the top of `build.py` with the final domain before the first real deploy — it feeds the
canonical tags, Open Graph URLs, sitemap and `llms.txt`.

Two placeholders are deliberately left in, and are the only content edits needed before launch:

* `PHONE_DISPLAY` in `build.py` is not rendered anywhere yet — supply the number if you want it on the site.
* `SITE` still points at `https://jacaranda-labs.pages.dev`. Point it at the domain you actually push to.
