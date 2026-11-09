---
title: The Mechanism Audit: Evidence-First Review for Products That Act Without an Operator
series: Jacaranda Labs Think Tank Working Paper 2026-04
byline: Courage Garikai — Jacaranda Labs, Harare, Zimbabwe
programme: Jacaranda Labs — Distributed Cognitive Autonomous Infrastructure
date: November 2026
slug: mechanism-audit
---

# Abstract

Software reviews were built on the assumption that a human performed each action and a second human watched. That assumption has failed quietly. Products now change themselves: agents commit, workflows publish, models write the copy, and the operator's role is reduced to reading a green tick. The instruments of review — the demo, the screenshot, the QA script, the changelog — were designed to certify **effort witnessed**. They cannot certify **a mechanism governed**, because nobody was in the room when it acted.

This paper sets out a method for reviewing that class of product, and the evidence for it comes from a single estate of seven ventures run by one operator and a set of agents. The audit asks for five artefacts: a **claim ledger** (what the product says it does), a **mechanism map** (what actually decides), an **evidence trail** (what the mechanism leaves behind when it runs), a **detector** (a check that fails when the mechanism stops working), and a **response** (what happens when it fails, and who is told). A product is audited when all five exist, agree, and can be re-run by a stranger.

Six failure signatures are formalised, each with a production incident attached from the same week: the green run that names no subject; the allowlist that excludes what it was built to catch; the credential that authenticates but cannot act; the retry that published twice; the fallback that looked like output; and the origin that had not yet propagated. They collapse into six gap classes — claim–evidence, scope, capability, ownership, propagation, attribution — which is what a review is actually looking for.

The contribution is architectural and forensic, not statistical. The sample is one estate, the author is its owner, and the incidents were cheap. That is disclosed here rather than argued around: what is claimed is that the method found the failures before they cost money, and that every detector described is in a public repository and can be run against this sentence's author.

**Keywords:** product audit; mechanism governance; silent failure; evidence trail; agentic software; deploy verification; small-operator infrastructure; sub-Saharan digital infrastructure

# 1. The review that no longer fits

A demo is a claim made in the presence of a witness. For thirty years that was enough, because the software could not do anything the demonstrator did not do. The witness could ask "show me again", and the second showing was evidence, because a human had to be involved for it to happen.

Three changes broke the instrument:

1. **Authorship moved.** The code that ran in production was written, in part, by a system that was not in the meeting. The reviewer's question — *did you build what you said?* — has no witness to answer it.
2. **Action moved.** Products act on their own schedule: they publish, invoice, email, deploy. The interval between reviews is now full of acts that nobody watched.
3. **Success became a colour.** Continuous integration turned verification into a tick. A tick is a *statement about a run*, not a statement about the product, and the two are routinely confused — including by the people who configured the pipeline.

The consequence is specific and it is not "AI is risky". It is that **the evidence a reviewer needs is no longer produced by the process that used to produce it**. Nothing about the demo is dishonest; it is simply measuring a world that has gone.

This paper describes an audit built for the world that replaced it. The audit was developed while operating seven ventures — a desk system for customs and tender firms, a document tool, a storefront kit, an audit practice, a mechanism record, an open teaching practice, and a press — from one desk in Harare, with agents doing the work and one person accountable for it. The incidents quoted are not case studies assembled afterwards. They are this week's failures, and each one is still in the repository's history, detector included.

# 2. What an audit is

An audit is not an opinion about quality. It is an answer to a narrow question:

> For each thing this product claims, what would have to be true, what is true, and how would we know if it stopped being true?

That question decomposes into five artefacts. Their order matters; each is worthless without the one before it.

## 2.1 The claim ledger

Every claim the product makes, in the product's own words, written down once, with a pointer to where it is made — the landing page, the pricing table, the onboarding email, the API documentation. The purpose is not marketing review. It is to make the set **finite**. An audit has a scope, and the scope is exactly this list.

The discipline that makes the ledger useful is brutal: a claim that cannot be attached to a mechanism is a claim that must be removed. In the estate this paper describes, that rule deleted several sentences from product pages — "handles every payment rail", "works offline", "audited" — not because they were false in spirit, but because there was no mechanism whose failure would have made them false. A claim whose failure mode cannot be described is not a claim; it is a mood.

## 2.2 The mechanism map

For each claim, the thing that actually decides whether it holds. The map is not an architecture diagram; it is a list of decision points, each with an owner of record:

- the code path, with a file and a line, not a service name;
- the configuration that can change behaviour without a deploy (environment variables, feature flags, quotas, DNS, cache rules);
- the credential that authorises the action, and what it is scoped to;
- the human who can change any of the above, and how we would know they did.

Most audits in this class die here. The product's behaviour is decided, in practice, by a variable set in a web console that no file mentions. That is not a technicality: it means the mechanism is real but the map is fiction, and a review of a fiction is theatre.

## 2.3 The evidence trail

What the mechanism leaves behind when it runs, in a form a stranger can read: a run log that names the commit it ran from; a post identifier returned by the platform that accepted it; a state file written after the fact; a deployment identifier and the URL that serves it. The evidence trail is the difference between "the workflow succeeded" and "the workflow published *this* text at *this* time to *these* accounts, and here they are".

Two properties are essential and both are usually missing:

- **Attribution to an artefact.** Evidence that does not name the commit, deployment, or message it describes cannot be checked against anything. It is a rumour with a timestamp.
- **Independence from the thing being checked.** If the only evidence that publishing worked is the publisher's own exit code, the evidence is a self-report. The trail must include something the mechanism does not control — the platform's identifier, the published URL, the recipient's copy.

## 2.4 The detector

A check, cheap enough to run every time, that **fails** when the mechanism stops working. Not a dashboard. A detector has three properties: it is deterministic (the same inputs give the same verdict), it is adversarial (it was written by someone trying to make the product fail), and it is loud (its failure stops something).

The honest test of a detector is the mutation test: break the mechanism deliberately, and see whether the detector notices. In the estate, two detectors that had never been mutation-tested turned out to be incapable of failing — a scanner whose allowlist covered the exact paths where the leaks lived, and a post-check that passed when there was nothing to check. Both were green for weeks. This is the normal condition of an untested detector, and it is why the method insists on the mutation test rather than the existence of the check.

## 2.5 The response

What happens when the detector fires: who is told, in what channel, how fast, and what happens if they do not answer. This is where audits normally stop, and it is the part that decides whether the other four artefacts were decoration.

Two failure modes recur. The first is a detector that fires into a channel nobody reads, which is equivalent to no detector with extra steps. The second is a detector whose failure does not stop anything: the deploy proceeds, the post goes out, the invoice sends, and the red mark is filed under maintenance. **A control that does not block is a notification.**

# 3. Six signatures

The following signatures recurred across seven ventures in a single week of operation. They are presented as signatures because that is how an auditor actually works: you learn the smell, then you look for the mechanism that produces it.

| Id | Signature | What it looks like | Gap class |
|----|-----------|--------------------|-----------|
| S1 | The green run | Success that names no subject; the email says "failed" about a commit that no longer exists | attribution |
| S2 | The allowlist | A control that excludes the thing it was built to catch | scope |
| S3 | The credential that authenticates | Identity verifies; the action it exists for is refused | capability |
| S4 | The retry that published twice | A defensive retry produces a second, real, public act | ownership |
| S5 | The fallback that looked like output | A missing input is silently substituted; the artefact looks finished | claim–evidence |
| S6 | The origin that had not propagated | The build is correct, the deployment is correct, the address a user reads is not | propagation |

## 3.1 S1 — The green run

The operator received several automated emails reporting that the secret scanner had failed. The scanner had failed: on commits that had been superseded days earlier. The current heads were green, and had been green since the fix. The cost was not the failure; it was the operator's attention, spent three times on a solved problem, and the erosion of the signal's credibility — the fourth email, the one that would have mattered, would have been read as noise.

**Mechanism.** The notification described a run, not a commit, and did not say whether that commit was still the tip. The fix is one line of reporting discipline — every control's message names the artefact and its currency ("commit 5da922e, current") — but the general lesson is the signature: *a success that names no subject is not evidence, and a failure that names no subject is not a warning.*

## 3.2 S2 — The allowlist

The repository's secret scanner was configured with exceptions, so that public-by-design keys (a search-engine verification file, a newsletter address) would not fail the build. The exceptions were written by **path and by fingerprint**. Two private keys survived in a public repository for weeks, because the paths that carried them had been excluded, and because the fingerprints were computed over a shallow clone and so did not match the commits the scanner actually examined in continuous integration.

**Mechanism.** An allowlist is a scope decision disguised as a convenience. Excluding a path says "nothing in this file can be a secret", which is a claim about content made on the basis of a filename. The fix was to allowlist by **value** — the exact public strings, with a comment explaining why each is public — so an exception can only ever cover itself.

**Detector.** The mutation test found this, not a review: insert a fake key into an allowlisted path and confirm the scanner fails. It did not. It does now.

## 3.3 S3 — The credential that authenticates

A social account's token was verifying successfully against the identity endpoint — the right handle, the right scopes, a 200 — while the media upload the rail existed for returned 401. Two hours went into a plausible and wrong hypothesis (the app had been authorised without the media scope) that the scope list on the same credential disproved. The actual cause was duller: the local environment held a truncated copy of the token, 26 characters instead of 43, and the identity call was permissive enough to accept it while the write endpoint was not.

**Mechanism.** Identity and capability are separate claims, and only one of them is cheap to check. A verification routine that calls `verify_credentials` and reports "connected" is testing the wrong thing; the check that matters is a **canary act** — the smallest real action the credential exists to perform, performed against the real service, then cleaned up.

The estate's rail now reports, for each channel, whether it is *armed* (a credential exists), *verified* (identity resolves), and *capable* (the canary act succeeded). Only the last is worth a green tick, and only for the action it tested.

## 3.4 S4 — The retry that published twice

A defensive retry, added the same day to survive a fresh token being momentarily rejected, produced a second published post on two platforms before the third refused it as a duplicate. The duplicate was deleted by hand within minutes. The cost was small; the mechanism was not.

**Mechanism.** A retry is an ownership question. Retrying an act that changes the world requires an **idempotency key** — a stable identity for the intended act, sent with every attempt, so the receiving side can collapse duplicates. Without one, "did it work?" is unanswerable by the client and answered by luck.

The instructive part is that the platform that refused — "you have already scheduled or posted this" — had the control the publisher lacked. A rail that cannot tell whether it already posted should be reading the platform's own record, or sending a key, or both (this estate now does both). Where the platform offers no such control, the rail must keep a local ledger of acts *before* performing them, not after.

## 3.5 S5 — The fallback that looked like output

A card renderer fell back to a plain dark plate when its source photograph was absent. On a machine with a stale checkout the photograph was absent, and twenty-four cards rendered — plausibly, on brand, on time — without the image that carries the brand. Nothing failed. The artefacts were inspected, approved, and nearly published.

**Mechanism.** Fallbacks exist so that a small failure does not become a large one, and they are correct until the day they convert an outage into an undetected degradation. The rule that emerged: **a fallback may substitute for form, never for substance, and it must announce itself.** The renderer now reports which source it used, and the pipeline fails if the primary source is missing on a machine that claims to have it.

The same week produced a second instance in a different medium: a social post composed as text with the card inlined by URL. It looked correct on every screen. It was one redeploy away from being a post with a broken image, because the bytes belonged to us and the post did not. The fix was to post the picture as a picture, so the platform takes ownership of the evidence at the moment of publication.

## 3.6 S6 — The origin that had not propagated

A freshly generated set of cards returned 404 at the site's own domain for several minutes after the deployment that contained them had reported success — and returned 200 at the deployment's own address at the same moment. The publisher's card resolution is strict (no card, no post), so the rail would have skipped a post for a deploy that had, in fact, worked.

**Mechanism.** There are now three artefacts where there used to be one: the build, the deployment, and the **name users read**. They are correct at different times, and a check that tests any one of them while claiming to test "the site" is a category error. Detection must test the address that matters, with cache-busting, and must distinguish "not yet" from "not there" — the first deserves a retry, the second an alarm.

The fix in the estate is deliberately prosaic: every card is named by two origins (the site and a mirror built from the same commit) and the rail takes whichever answers first, in the knowledge that one of them lags.

# 4. The six gaps, and what a review is actually looking for

The signatures are symptoms. Underneath them are six classes of gap, and an audit that finds none of them has probably not looked.

1. **Claim–evidence gap.** The product says something no mechanism decides. Remedy: delete the claim or build the mechanism.
2. **Scope gap.** A control excludes exactly the population it was built to inspect. Remedy: allowlist by value, never by path; mutation-test every exclusion.
3. **Capability gap.** Authorisation is verified, the act is not. Remedy: canary acts, per capability, with cleanup.
4. **Ownership gap.** The act can happen twice, or the evidence lives on a third party's origin that can change under you. Remedy: idempotency keys; take ownership of bytes at publication.
5. **Propagation gap.** The thing checked is not the thing used. Remedy: check the address, from outside, with cache-busting; know the difference between late and absent.
6. **Attribution gap.** Evidence cannot be tied to the artefact it describes. Remedy: every control names its subject and says whether that subject is current.

# 5. The audit, in practice

Three instruments, in increasing cost. All three are cheap enough that their absence is a choice.

**The one-hour audit.** Read the claim ledger and the mechanism map. For each claim, ask for one artefact of evidence and one detector. Anything with neither is deleted from the ledger on the spot. This finds the claim–evidence gap almost every time, because claims accumulate faster than detectors everywhere.

**The one-day audit.** Add the canary acts, the mutation tests, and a read of the evidence trail from outside the system. This is where the scope and capability gaps surface, and it is the cheapest point at which they can be found.

**The continuous audit.** Every control's output names its subject and its currency; every act that changes the world is keyed; every publish is verified by reading the platform's own record; every detector's failure blocks something. The estate described here runs this as a scheduled job whose failure stops the next act rather than colouring a chart.

What is deliberately not in the method: a maturity score, a checklist of best practices, or a number that can be reported upwards. All three are ways of converting an audit into a deliverable that cannot fail, which is the same disease this paper is about.

# 6. Limits and disclosure

The author owns the seven ventures audited. The estates' failures are self-reported, the sample is one, the incidents were inexpensive, and no external party has replicated the method. The claim made here is correspondingly narrow: that these six signatures were found by this method, before they cost money, and that each detector is in a public repository where a reader can run it against the author's own claims.

Two further limits are structural. First, the method assumes the auditor can read the mechanism — code, configuration, credentials — and an audit without that access degrades into a review of the claim ledger alone. Second, the method is expensive in attention rather than money: its detectors are cheap to run and costly to write, and the cost falls exactly on the operator who is already short of time. That is the case for doing it in the open, as this estate does, rather than for each operator reasoning alone.

# 7. Conclusion

Review used to be a social act: a person performed, a person watched. Products that act without an operator have removed the witness, and no amount of demonstration restores them. What remains is the mechanism and the record it leaves. An audit that asks for a claim ledger, a mechanism map, an evidence trail, a detector and a response is asking the only question that survives the loss of the witness: *if this stopped working tonight, what would tell us, and what would stop?*

The six signatures in this paper are the shapes that answer takes when the answer is no. They are cheap to look for and, in this estate's case, were all present within a week of looking. The uncomfortable arithmetic is that they were present *while the products were being described as governed* — which is the ordinary condition of small software, and the reason the audit is worth doing before anyone asks for one.

# Appendix A — Incident index

| Id | Date (2026) | Symptom | Class | Fix |
|----|-------------|---------|-------|-----|
| M1 | 9 Nov | Secret-scan emails about superseded commits | attribution | every message names commit and currency |
| M2 | 7 Nov | Two private keys public for weeks | scope | allowlist by value; mutation test |
| M3 | 9 Nov | Token verified, media upload 401 | capability | canary act per capability |
| M4 | 9 Nov | Retry published a duplicate post | ownership | idempotency key + platform record |
| M5 | 9 Nov | Cards rendered without the brand photograph | claim–evidence | renderer announces its source; pipeline fails |
| M6 | 9 Nov | Fresh card 404 at the site's own domain | propagation | two origins, take whichever answers |

# Appendix B — The five artefacts as they exist in the estate

- **Claim ledger:** `data/ventures.json` and `data/works.json` — every price, capability and publication the site asserts, in one file, checked by the build.
- **Mechanism map:** the rail registry (`rails/*/social.py`) plus the workflow files: each channel names its credential variable, its scope and the act it performs.
- **Evidence trail:** the platform identifiers returned at publication, the committed state file, and the deployment log naming its commit.
- **Detectors:** the bank selftest (ratio and length invariants), the card-resolution refusal, the scanner with value-based allowlists, and the post-deploy fetch of the address users read.
- **Response:** the scheduled job fails closed — no card, no post; no detector, no claim.
