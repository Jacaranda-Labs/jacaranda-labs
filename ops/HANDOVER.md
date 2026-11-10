# Handover — the ops site

* **Live:** https://jacaranda-ops.pages.dev (deployed by `.github/workflows/ops.yml`)
* **Passphrase:** `harare-three-touches-2026` — entered once per device, stored in that browser only.
  To change it: `python3 ops/build_ops_site.py --bible ../operator-bible.html --out ops --pass '<new>'`,
  commit, push.
* **Plaintext manual:** `../operator-bible.html` (v1.1) — never committed, never deployed.
* **Public statement page:** https://jacaranda-ops.pages.dev/live.html — unsealed, no scripts.
* **What a visitor without the phrase sees:** a lock screen and 112 KB of ciphertext. Nothing else.
* **Why sealed at all:** the manual says how the estate is run, what fails, what it costs. Unlisted is
  not private; encrypted is.
