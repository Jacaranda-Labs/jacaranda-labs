---
title: The Mechanism Auditor: How to Review a Product That Runs Without You
series: The Mechanism Auditor
byline: Courage Garikai — Jacaranda Labs, Harare, Zimbabwe
programme: Jacaranda Labs Press — Harare
date: First edition, November 2026
slug: the-mechanism-auditor
---

# Part One — The Witness Is Gone

## 1. The demo was a promise

For as long as software has been sold, it has been sold by demonstration. Someone sits with someone else and makes the thing work. The buyer's question — *does it do what you say?* — is answered by watching it happen, and the watching is the proof, because the person making it happen is the person who built it, and in thirty years of practice we have learned roughly how much they might be tempted to fudge.

That arrangement had a hidden requirement, and nobody ever wrote it down: **a human had to be present at every act**. The demonstration was evidence because a person was in the loop, doing the thing in front of a witness. If the demonstration was honest, the software was at least capable of the act. The reviewer's job was to spot the trick.

The trick is still possible, but it is no longer the interesting problem. The interesting problem is that the acts which matter now happen when nobody is watching. Software commits changes to itself on a schedule, publishes to accounts, sends invoices, rotates credentials, and reports its own success. By the time a human looks, the act is over, and all that remains is what the software chose to tell you about it.

I run seven small software businesses from one desk in Harare, with agents doing most of the building and one person — me — accountable for all of it. There is no QA department, no second pair of eyes, and no meeting in which someone says "show me again". Every failure I describe in this book happened in that estate, in one week of ordinary operation, and every one of them was invisible from the demo. They were visible only in the mechanism, and the mechanism is what this book teaches you to read.

## 2. What a green tick actually says

A build turns green. Everyone relaxes. This is the single most expensive habit in modern software, and it survives because of a small linguistic trick: we say *the build passed*, as though the build were the product.

A green tick says one thing: **a specific job, running a specific set of checks on a specific revision, exited zero**. It does not say the product works. It does not say the checks could have failed. It does not say the revision you deployed is the revision that ran. It does not say anything happened in the world outside the runner.

Four separate claims are being conflated, and each of them can be false while the tick stays green:

- **Coverage.** The checks might not touch the thing that broke.
- **Capability.** The checks might be incapable of failing, because of an exception, a skip, a dry run, or a missing prerequisite.
- **Currency.** The revision that ran might not be the revision you shipped.
- **Effect.** The job might have finished before the effect it was meant to have occurred, or the effect might have occurred somewhere you are not looking.

Every failure in Part Three is one of these four, and none of them is a bug in the usual sense. They are all failures of the *story the tick tells*.

So the audit begins with a decision that feels petty and is not: **stop treating a green tick as evidence, and start asking what evidence would look like.** The rest of this book is that question, answered five ways.

# Part Two — The Five Artefacts

An audit that produces a score has produced a second thing that cannot fail. An audit that produces artefacts has produced something a stranger can check. Five of them, in order, each worthless without the ones before it.


## 2a. The economics of silent failure

Silent failures are cheap in the way that a leaking roof is cheap: the cost is not the leak, it is the interval before anyone looks.

Every failure in this book has the same shape. A mechanism did not do what it claimed, a signal said it had, and the interval between those two facts was measured in days. In that interval the product was **confidently wrong**, and confidence is what makes a wrong thing expensive: a customer bought, an editor published, a payment ran, a promise went out attached to a name.

Three numbers decide whether an audit is worth its price, and none of them is the auditor's hourly rate:

- **The cost of the failure met by a customer** — a refund, a replacement, an apology, and the specific damage of having been confidently wrong to someone who trusted you.
- **The cost of the interval** — how many of those failures fit into the time between your looks.
- **The cost of looking** — an hour, a day, a job that runs every thirty hours.

For a product that acts a few times a day, the interval is the whole story. A control that reports weekly and a control that reports hourly differ by a factor of a hundred and sixty-eight in exposure, and no amount of dashboard polish closes that gap.

There is a fourth number, and it is the one that actually kills small operators: **the cost of the attention**. Every false alarm spends the same currency as a real one. That is why the grammar of a control's message — subject, currency, and what to do — is an economic decision and not a stylistic one.

## 3. The claim ledger

Write down every claim the product makes, in the product's own words, with a pointer to where it is made. The pricing table. The landing page. The onboarding email. The line in the API documentation. The sentence in the sales call that you will deny later.

The ledger exists to make the set *finite*. An audit needs a scope, and this list is the scope. Without it, the audit is a wander — you check the things you happen to think of, which are the things you are already good at, which is why audits so often confirm the auditor.

Then apply the rule that makes the ledger worth keeping:

> **A claim with no mechanism behind it gets deleted, not qualified.**

Not "supports most payment providers". Not "designed for offline use". Deleted, and the deletion recorded. Because a claim is not a description of an aspiration, it is a promise about behaviour, and the only thing that keeps a promise is a mechanism whose failure would break it.

I deleted claims from my own product pages when I first did this, and it stung more than the engineering. "Audited" went, because no audit existed. "Works offline" went, because the offline path had been built once and never tested. "Handles every payment rail" went because it meant "handles the two we integrated". Each deletion was a real loss of persuasiveness in exchange for a real gain in truth, and the gain compounds: a page that only says things it can break is a page a reviewer can audit in an hour, and being auditable turns out to be a sales asset in a market full of confident noise.

## 4. The mechanism map

For each claim, the thing that actually decides whether it holds. Not an architecture diagram — diagrams describe intent. A map of decision points:

- **The code path**, named by file and function, that performs the act.
- **The configuration** that can change behaviour without a deploy: environment variables, feature flags, quota settings, DNS, cache rules, the project's production branch.
- **The credential** that authorises the act, and the scope it carries. Not "the API key" — which key, scoped to what, revocable by whom.
- **The human** who can change any of the above, and how you would find out that they did.

Most audits die here, and they die of a specific embarrassment: the behaviour is decided in a web console by a variable no file mentions. The mechanism is real and the map is fiction, and a review of a fiction is theatre.

I have lost an afternoon to exactly this. A publishing rail kept skipping one channel and reporting success. The map in my head said the credential was set. The credential *was* set — in the wrong environment, with a truncated value, in a file that shadowed the real one. The map was not wrong about the technology; it was wrong about where the truth lived.

The discipline that fixes it is dull: when a mechanism behaves unexpectedly, the first question is never "why is the code wrong" but **"which copy of the configuration is being read"**. Write the answer down. The map grows a line, and the line is worth more than the diagram.

## 5. The evidence trail

What the mechanism leaves behind when it runs, in a form a stranger can read. The run log that names its commit. The identifier the platform handed back when it accepted the post. The deployment identifier and the address that serves it. The state file written after the act, not before.

The trail is the difference between "the publisher succeeded" and "the publisher published *this* text at *this* time to *these* accounts, and here is where to look".

Two properties matter more than completeness:

**Attribution.** Evidence that does not name the artefact it describes cannot be checked against anything. An email saying "the scan failed" is a rumour with a timestamp. An email saying "the scan failed on commit 592975a, superseded by 5da922e, which passed" is a fact that costs the reader nothing. I spent three separate mornings reacting to the first kind of email before I understood that the problem was not the failures, it was the grammar.

**Independence.** If the only evidence that publishing worked is the publisher's exit code, the evidence is a self-report. The trail has to include something the mechanism does not control: the platform's own identifier, the published URL fetched from outside, the recipient's copy. Where a third party will hold your receipt, let them.

## 6. The detector

A check, cheap enough to run every time, that fails when the mechanism stops working. Not a dashboard. A detector has three properties:

- **Deterministic.** Same inputs, same verdict, no judgement.
- **Adversarial.** Written by someone trying to make the product fail, or at least by someone in that mood.
- **Loud.** Its failure stops something.

The honest test of a detector is mutation: break the mechanism on purpose and see whether anything notices. This is the step everyone skips, and skipping it is why so many controls are decorative.

Two of my own detectors passed their own mutation test by failing it. A secret scanner had an allowlist covering exactly the paths where two private keys lived; it was green for weeks while the keys were public. A content check confirmed that every post had a card, in a code path that ran only when there were posts to check — and in the week it mattered there were none. Both were well written. Both were incapable of failing. The only thing that distinguishes a check from a superstition is having watched it go red.


## 6a. A worked example: one publishing rail, end to end

Abstractions are cheap, so here is the whole instrument applied to one small mechanism — a rail that publishes a post to five networks — in the order an auditor would do it.

**The claim.** "Posts to seven networks every thirty hours, with an image on every post, without an operator." Written on a product page, therefore in the ledger.

**The map.** The rail is a directory of Python modules; the schedule is a workflow file; the credential for each network is a repository secret; the image is a card rendered from a photograph and committed; the decision of *what* to post comes from a bank of posts checked by a self-test. Four decision points, three of which live outside the code: the secrets, the schedule, and the photograph.

**The trail.** For each post: the platform's identifier (`at://…` for one network, a numeric id for another, a pin id for a third), a state file recording what has been sent, and a run log naming the commit. The trail is only worth having because the identifiers are the *platforms'*, not ours — they can be fetched by a stranger and would not exist if nothing had been published.

**The detectors.** A self-test that fails if the bank ever drifts below two value posts for each promotional one, or if any post plus its link exceeds the tightest network's limit. A resolution rule that refuses to publish without an image. A post-deploy fetch of the card's public address. And a scheduler cadence check, so a run cannot publish twice inside the window.

**The response.** No image, no post — the run exits *zero* with a line saying it waited, rather than publishing a degraded artefact. A failure on one network does not stop the others, but it is printed, and the run is red if nothing at all landed.

Now the audit question for each claim. *"With an image on every post"* — which file decides it? The rail's resolution chain. What is the evidence? The image identifier attached to a published post, which the platform holds. What would tell us it stopped? A refusal, because the rail cannot publish text-only. Has that detector been watched failing? Yes: point it at a nonexistent card and it refuses.

*"Every thirty hours."* Which file? The workflow's schedule plus the rail's own cadence guard. Evidence? A state file with timestamps, cross-checked against the platforms' own timestamps. Detector? The cadence guard, mutation-tested by setting a last-run time one hour ago and watching it decline to publish.

*"Without an operator."* This is the claim that fails first in practice, and the assertion behind it is not technical. The audit asks: what is the operator's *only* remaining job, and could the mechanism report it? In this estate the answer was "paste a credential once", which is fine — and the failure mode to watch is the silent one, where a channel is skipped for want of a credential and the run is green. That is why the rail distinguishes `skip:` from `ok:` in its output, and why the count of armed channels is on the same line as the result.

Notice what the audit did not need: a meeting, a demo, or an opinion about quality. Five artefacts, four decision points, three detectors, one refusal. An hour.

## 7. The response

What happens when the detector fires. Who is told, on what channel, how quickly, and what happens if nobody answers.

Two failure modes recur, and both are commoner than no detector at all:

**The notification nobody reads.** A red mark in a tool that is opened weekly. This is equivalent to no control with extra steps, and it is worse than nothing because it generates the feeling of coverage.

**The control that does not block.** The detector fires, the pipeline continues, the post goes out, the invoice sends, and the red mark is filed under maintenance. **A control that does not block is a notification**, and a notification is a wish.

The response section of an audit is where you find out whether the other four artefacts were decoration. It is also where the design decision is cheapest: choose *fail closed* wherever the act is public or irreversible. My publishing rail's rule is "no card, no post" — if the image cannot be resolved, nothing is published and the job exits zero with a line saying it waited. That is not laziness about the failure; it is a refusal to publish a degraded artefact that would look like success.


## 7a. When an agent wrote it

Most code reviewed today was written by a system nobody can interview. This changes the audit in one specific way and leaves it unchanged in another.

**Unchanged:** the artefacts are identical. A mechanism map is a mechanism map whoever typed it, and the gaps are the same six.

**Changed:** the reviewer can no longer use the author's intent as a shortcut. When I review my own code, I can reason from "what I meant". With agent-authored code there was no *meant*; there was a specification and a generation, and the distance between them is exactly where the failures live.

Three habits close that distance:

**Keep the instruction as an artefact.** The prompt, the ticket, the specification — whichever form the instruction took — is a claim in the ledger. When the produced code does less than the instruction, that is a claim–evidence gap, and it is invisible if the instruction was a conversation. In my estate the instructions are files in the repository, which makes them diffable, and diffs are what audits eat.

**Read for what is absent.** Generated code is usually *plausible*: it handles the happy path, names things sensibly, and looks complete. The audit's job is to find the case that is not handled, and the reliable way is to write the mutation first: decide how you would break it, then look for the code that would notice. If there is none, there is your gap — regardless of how good the code reads.

**Test the claim, not the diff.** A diff review asks "is this change reasonable?", which is unanswerable at scale. An audit asks "does the claim still hold, and can I watch the detector?" — a question with a verdict, and one that does not care whether the author was tired, clever, or a model.

The uncomfortable consequence is that agent-authored code makes the *claim ledger* more important than the code review. The code will be re-generated; the claim is what the business promised. Review the promise, and keep the mechanism honest underneath it.

# Part Three — Six Signatures

An auditor works by smell and confirms by mechanism. These six shapes recurred across seven unrelated products in one week. Learn them and you will start seeing them in software you did not write.

## 8. The green run

*A success that names no subject.*

The email said the scan failed. The scan had failed, on commits that had been superseded days earlier; the current heads were green and had been since the fix. Three mornings of attention went into a solved problem, and — this is the expensive part — the fourth email, the one that would have mattered, arrived into a mailbox that had learned to skim.

**What to look for.** Any automated message that cannot be answered with "about which revision, and is that revision current?" Controls should name their subject and their currency. It costs one line and it converts noise into evidence.

**The deeper version.** The same signature appears in dashboards that show a percentage without a date, in status pages that say "operational" while every individual component is red, and in any report whose author cannot say what would have made it say otherwise.

## 9. The allowlist

*A control that excludes the thing it was built to catch.*

The scanner excluded paths that were "known to be public by design" — a search-engine verification file, a newsletter address. Two private keys lived in one of those paths. The exclusion was written as a filename, which is a claim about content made on the basis of a name.

An allowlist is a scope decision disguised as a convenience. Every exclusion is a sentence of the form "nothing in here can be a secret", and that sentence is almost always false. Allowlist by **value**, with a comment explaining why that exact string is public, so an exception can only ever cover itself.

**The mutation test, in full.** Take the thing your control claims to catch. Put it where your control is supposed to look, in the way your control is supposed to look for it. Watch it fail. If it does not fail, you do not have a control; you have a ritual, and the ritual is protecting the wrong thing.

## 10. The credential that authenticates

*Identity verifies; the action it exists for is refused.*

The token authenticated. The handle was right, the scopes looked right, the endpoint returned 200. The media upload the rail existed for returned 401. Two hours went into a plausible hypothesis — the app had been authorised without the media scope — which the same credential's scope list disproved. The cause was duller: a truncated copy of the token in a local environment file, 26 characters where the real one is 43, and an identity check permissive enough to accept it while the write endpoint was not.

**The rule.** Identity and capability are separate claims, and only one of them is cheap to check. A connection test that calls the identity endpoint and reports "connected" is testing the wrong thing.

What to build instead is a **canary act**: the smallest real action the credential exists to perform, performed against the real service, then cleaned up. Post something private and delete it. Upload a one-pixel image and remove it. The rail should report, per channel, whether it is *armed* (a credential exists), *verified* (identity resolves), and *capable* (the canary act succeeded) — and only the third deserves a green tick, for the specific act it tested.

## 11. The retry that published twice

*A defensive retry produces a second, real, public act.*

A retry was added the same day to survive a fresh token being momentarily rejected. It worked. It also published twice, on two platforms, within a minute; the third platform refused it as a duplicate and was, embarrassingly, the only component with the right idea.

A retry is an ownership question. Any retry of an act that changes the world needs an **idempotency key**: a stable identity for the intended act, sent with every attempt, so the receiving side can collapse the duplicates. Without one, "did it work?" is unanswerable by the client, and is answered by luck.

Where the platform has no idempotency, keep a local ledger of acts written *before* the act, not after. The ordering matters: a record written afterwards is a record of what you believe happened, and the case you are protecting against is precisely the one where you do not know.

## 12. The fallback that looked like output

*A missing input is silently substituted; the artefact still looks finished.*

A card renderer fell back to a plain plate when its source photograph was missing. On a machine with a stale checkout, the photograph was missing, and twenty-four cards rendered — on brand, on time, plausibly — without the image that carries the brand. Nothing failed. They were inspected, approved, and nearly published.

Fallbacks exist so a small failure does not become a large one, and they are correct until they convert an outage into an undetected degradation. The rule: **a fallback may substitute for form, never for substance, and it must announce itself.** The renderer now reports which source it used, and the pipeline fails if the primary source is absent on a machine that claims to have it.

The same week, in a different medium: a social post composed as text with its card inlined by URL. Correct on every screen. One redeploy away from a post with a broken image, because the bytes belonged to us and the post did not. The fix was to publish the picture as a picture, so the platform takes ownership of the evidence at the moment of publication. Any artefact whose integrity depends on a URL you can change later is not finished.

## 13. The origin that had not yet propagated

*The build is right, the deployment is right, the address a user reads is not.*

Freshly generated cards returned 404 at the site's own domain for several minutes after the deployment containing them reported success — and returned 200 at the deployment's own address at the same moment. My rail refuses to publish without a card, so it would have skipped a post for a deploy that had in fact worked.

There are now three artefacts where there used to be one: the **build**, the **deployment**, and the **name users read**. They become correct at different times, and a check that tests any one of them while claiming to test "the site" is a category error of the most ordinary kind.

Detection must test the address that matters, from outside, with cache-busting, and must distinguish **"not yet"** from **"not there"** — the first deserves a retry, the second an alarm. My fix is prosaic and I recommend it: name the artefact by two origins and take whichever answers first, in the knowledge that one of them lags.

# Part Four — Doing It

## 14. An hour, a day, forever

**The hour.** Read the claim ledger and the mechanism map. For each claim, ask for one artefact of evidence and one detector. Anything with neither comes out of the ledger on the spot. This finds the claim–evidence gap almost every time, because claims accumulate faster than detectors everywhere on earth.

**The day.** Add canary acts for every capability, mutation tests for every exclusion, and a read of the evidence trail from outside the system. This is where scope and capability gaps surface, and it is the cheapest moment at which they can be found — before a customer finds them with their money.

**Forever.** Every control names its subject and its currency; every act that changes the world is keyed; every publication is verified by reading the platform's own record; every detector's failure blocks something. This is not a programme. It is a handful of habits, and the enemy is not complexity, it is forgetting.


## 14a. The first week, concretely

What an audit actually changes, in the order I changed it. All of these are small; none of them is a project.

**Day one.** Wrote the claim ledger for seven products in one file, and deleted eleven claims that had no mechanism behind them. Two of the deletions were prices described as "from" a number that no configuration anywhere enforced.

**Day one, later.** Added a name and a currency to every automated message: which revision, which deployment, whether it is still the tip. This took an hour and stopped a class of attention theft that had been running for weeks.

**Day two.** Mutation-tested every exclusion in every scanner, and moved three allowlists from paths to values. Two private keys came out of a public repository that afternoon. That single change justified the week.

**Day three.** Wrote canary acts for the four channels that publish on their own, ran them, cleaned up. Two channels turned out to be *armed but not capable*, which is the state that looks identical to working from every dashboard I had.

**Day four.** Made every act that changes the world carry a key, and taught the publisher to read the platform's own record before it retries. The duplicate that had gone out on two networks stopped being possible rather than becoming less likely.

**Day five.** Turned the silent fallbacks into announcements: the renderer says which source it used, the rail says which channels it skipped and why, and both say it on the same line as the result.

**Day six.** Changed three detectors from "notify" to "block" — a missing image, a bank that breaks the ratio, a card that is not yet public at the address a reader uses. The first two now fail closed; the third waits and says so.

**Day seven.** Published the failure classes, in public, with the incidents attached. That is the step that makes the rest of it stick: once the failures are a published artefact, hiding one costs more than fixing it.

## 15. Reading someone else's product

An audit of a product you did not build is mostly an exercise in asking for the right artefact, and noticing which request is met with a diagram instead.

Ask, in this order:

1. **"What does it claim?"** — in writing, from the customer-facing page, not from the pitch.
2. **"Which file decides that?"** — for each claim. The answer "the platform does" means the mechanism is outside their control, which is a fact worth knowing before you rely on it.
3. **"Show me the record of the last ten times it ran."** — with identifiers, not screenshots. A system that cannot produce this is not being reviewed; it is being described.
4. **"What would tell you it had stopped working, and what would stop?"** — the two halves of the question are diagnostic. Most teams can answer the first and are silent on the second.
5. **"Break it in front of me."** — the mutation test, performed live. This single request separates the audited from the decorated more reliably than any document.

The answers you are listening for are boring: a file name, a variable name, a log line with a commit in it, an identifier a stranger could fetch. Enthusiasm is not evidence. Diagrams are not evidence. A demonstration proves that someone can make it work, which is the claim that was never in doubt.

## 16. What to do with what you find

Write it down in the product's own terms and fix in the order of irreversibility: **public acts first, money second, internal state third**. A wrong internal dashboard costs attention; a wrong public post costs credibility; a wrong invoice costs trust and a reconciliation.

Then do the thing that distinguishes an audit from a complaint: **attach a detector to every finding, or delete the finding.** A finding with no detector is an anecdote that will recur, and the second occurrence is worse than the first because it was predictable.

And publish it. The estate this book comes from publishes its failure classes as a matter of policy, which has two effects worth having: it makes the failures expensive to hide and cheap to fix, and it makes the claim "we audit ourselves" one that a reader can check instead of one they must believe.

# Part Five — The Business of It


## 16a. Auditing the business, not only the product

The same five artefacts apply to the commercial claims, and they are where the money is.

**"From $49."** Which file decides the price the customer is actually charged? If the answer is a page written by hand and a payment link configured somewhere else, the claim and the mechanism are two different things, and the gap is a support ticket with a card number attached.

**"Delivered in 48 hours."** What mechanism measures the clock, and what happens at hour 49? A delivery promise with no detector is a promise to be believed rather than kept.

**"Support replies within a day."** Who is told, on what channel, and what happens when they are asleep? This one is usually answered by a person's conscientiousness, which is the least auditable mechanism there is — not because people are unreliable, but because conscientiousness does not survive a bad week or scale past one operator.

**"Free to read."** Which mechanism enforces it, and would you know if it stopped? A paywall misconfigured in the customer's favour is a charming failure; the reverse is a refund and a screenshot on the internet.

The general rule: **every number in a sales sentence should have a file, a job, or a detector behind it** — and if it has none, the sentence is doing the work that the mechanism should be doing, which means it will eventually be doing that work alone.

## 17. What to charge

An audit is sold as attention, and attention prices badly when it is sold by the hour. Price the artefact instead. Three tiers, each with a different thing in the buyer's hands at the end:

- **Self-serve.** The instrument, sold cheap: the claim ledger template, the mutation-test list, the five artefacts, and a worked example. Sold at a price low enough that nobody needs a meeting. It exists so that the many small products that will never buy an audit can at least stop lying to themselves.
- **Written audit.** The five artefacts produced *for their product*, with the ledger they wrote, the map you drew, the detectors you ran, and a ranked list of gaps. Deliverable: a document they can hand to their own engineer, or to their customer who asked.
- **Audit with escalation.** The written audit plus the fixes, or the detectors implemented in their repository, plus one round of "break it in front of me" with their team present.

Price the third tier for the risk it removes rather than the hours it takes, and refuse to price the second by the page. An audit that costs the same whether or not it finds anything will, over time, stop finding things. That is not cynicism; it is what happens to any service whose revenue is independent of its findings.

## 18. What to refuse

Refuse three jobs, and say why, because the refusals are the product:

**Refuse to audit what you cannot read.** No repository access, no credentials, no configuration — you are being asked to review a claim ledger, and you should say so and price it as such.

**Refuse to certify.** An audit reports what is true now, with the artefacts attached. A certificate is a promise about the future made by someone who will not be there. The moment your name is used to mean "safe", the incentive to find something has gone.

**Refuse the score.** A maturity number, a grade, a percentage of compliance. All three are ways of converting an audit into a deliverable that cannot fail, which is the same disease this book is about. Give them the artefacts and the ranked gaps, and let them carry the judgement.


## 18a. What an audit is not

Four things that get sold as audits and are not, each with the tell that gives it away.

**A penetration test.** Valuable, adjacent, and about a different question: can an adversary make it do what it was not meant to? An audit asks whether the mechanism does what was claimed *when nobody is attacking*. The tell: a penetration test report that says nothing about whether the scanning control could fail.

**A compliance certification.** A statement about a checklist at a point in time, usually made by someone who will not be there when the mechanism drifts. The tell: the word "certified", and the absence of a detector.

**A code review.** A judgement about a diff, by a reader with partial context, at a moment that is already history. Useful for craft, useless as evidence about production. The tell: findings phrased as "consider…" rather than "this claim is unsupported because…".

**A dashboard.** A picture of what a system says about itself, drawn by the system. The tell: green everywhere, and no one able to say what would make it red.

An audit is narrower than all four and, for the specific question of whether a product that runs without you is doing what it says, the only one of the five that answers it.
# Part Six — Rules and Arithmetic

## 19. Twelve rules

1. A claim with no mechanism behind it gets deleted, not qualified.
2. Every control names its subject and says whether that subject is current.
3. Identity is not capability; test the act, not the account.
4. Watch every control fail on purpose, or you have a superstition.
5. Allowlist by value, never by path.
6. A control that does not block is a notification.
7. Fail closed on anything public, paid, or irreversible.
8. Key every retry of an act that changes the world.
9. A fallback may substitute for form, never for substance, and it must announce itself.
10. Own the bytes of anything you publish; a URL you can change later is not an artefact.
11. Check the address a user reads, distinguish "not yet" from "not there".
12. A finding without a detector is an anecdote waiting to recur.

## 20. The uncomfortable arithmetic

The six signatures in this book were all present in my estate at the same time, in products that were, at that moment, being described — by me, to customers — as governed. That is the ordinary condition of small software. It is not a scandal; it is what happens when one person builds seven things and the instruments of review were designed for a building full of witnesses.

The arithmetic that follows is uncomfortable in two directions.

**The first direction:** the cost of these failures was near zero, and the cost was near zero because they were found by looking, in a week, by the person who built them, before a customer met them. The same failures, met by a customer, cost a refund, a reputation and an evening. The audit's value is almost entirely in the timing, which is why it is so hard to sell to someone who has not yet been embarrassed.

**The second direction:** the audit is not a one-off. Every new mechanism — a new channel, a new integration, a new agent with a new credential — re-opens all six gaps, and the only defence that scales is the habit of asking the question in the same shape every time. That is what an auditor is: not a person who knows the answers, but a person who will not accept a green tick as one.

The last thing worth saying is the least commercial. An audit that finds nothing is usually a failed audit. If you look at a running product with five artefacts in mind and come back with nothing, the likeliest explanation is not that the product is sound; it is that you were reading its claims instead of its mechanism. Look again, break something on purpose, and see what tells you.

# Appendix — The audit sheet

One page, five artefacts, filled in for any product in an afternoon.

| Artefact | The question | What counts as an answer | What means "no" |
|----------|--------------|--------------------------|-----------------|
| Claim ledger | What does it say it does? | A finite list, in its own words, with pointers | "It's obvious what it does" |
| Mechanism map | Which file decides that? | File, configuration, credential, owner | A diagram, or "the platform" |
| Evidence trail | What did it leave last time it ran? | Identifiers a stranger can fetch | Screenshots, or its own exit code |
| Detector | What would tell you it stopped? | A check that has been watched failing | A dashboard |
| Response | What stops, and who is told? | A blocked act, a named human, a channel | A red mark nobody reads |

Run it in an hour. Then run it again in a month, on the same product, and compare the two sheets. The comparison is the audit; the sheet is just the instrument.

# Appendix B — The mutation test list

Ten ways to break a mechanism on purpose. Each one takes minutes and each one has caught something real in the estate this book comes from. Run them on anything you are told is governed.

1. **Blank the credential.** Set the token to an empty string. Does the control fail, or does it skip and report success?
2. **Truncate the credential.** Cut it to twenty characters. Does anything distinguish "wrong key" from "wrong account"?
3. **Point the artefact at nothing.** Ask the publisher for an image that does not exist. Does it refuse, or substitute?
4. **Deploy the old build.** Serve a previous revision and check whether your checks notice which revision they tested.
5. **Put the leak where the allowlist looks.** Write a fake secret into every excluded path and confirm the scanner goes red.
6. **Run the job twice inside the window.** Does the second run duplicate the act, or decline?
7. **Break one channel.** Remove one credential from a five-channel publish. Does the run tell you *which* channel, on the same line as the result?
8. **Fire the alarm at 2am.** Does anything reach a human who will act, or does it land in a channel opened on Mondays?
9. **Cache the address.** Fetch the artefact through the public domain with a cold cache and with a warm one. Do the answers agree?
10. **Hand the artefact to a stranger.** Give someone the identifier and nothing else. Can they fetch the evidence without your help? If not, you have a report, not a trail.

