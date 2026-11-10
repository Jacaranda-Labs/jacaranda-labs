---
title: The Point of Failure: An Operating Manual for the Person Running the Estate
series: The Operator's Books
byline: Courage Garikai — Jacaranda Labs, Harare, Zimbabwe
programme: Jacaranda Labs Press — Harare
date: First edition, November 2026
slug: the-point-of-failure
---

# Part One — The failure that is not the server

## 1. Everything here is redundant except the person

This book was written from inside a working estate: seven ventures, twenty-two works, five posting rails, a queue that refills itself, deploys that verify their own work, checkouts that take money at three in the morning without asking anyone. Every part of that was built for one reason, and it was not efficiency. It was so that one person could run it without being destroyed by it.

Inside that system, almost everything has a failover. The press rail retries. The bank refills before it empties. A deploy that lands wrong is redeployed and verified. A worker that returns a 404 at the front door is caught by an hourly check that says so in plain language. If a credential expires, the run says *credential missing* instead of going quiet. The design assumption is that any single component can be absent for a while and the estate keeps standing.

There is exactly one component with no redundancy at all. It is not the server. It is the operator.

That asymmetry is the reason this book exists. Every other risk in a one-person business is a technical problem with a technical answer — a retry, a monitor, a second copy, a smaller blast radius. The operator is a single point of failure with no replica, no warm standby, and no way to fail over to a second instance of oneself. Everything the estate does rests on one nervous system, one sleep pattern, one capacity to make a decision at four in the afternoon.

So the operator gets the same treatment every other component gets: written down, checked, given limits, monitored. Not as self-care. As engineering.

## 2. Three things are true at once, and holding all three is the skill

Most advice for people who work alone fails because it resolves one of these at the expense of the others. The person either works constantly, or they abandon the thing they built; they either micromanage every output, or they let a system run unattended and never look. The following three facts are simultaneously true, and the whole discipline of operating an estate is holding them without dropping one.

**The work is genuinely unbounded.** Seven ventures, twenty-two works, five rails. There is always another thing. No amount of finishing changes this. The list does not shrink because the work does not end; it changes shape. This is not a temporary phase to be survived until the calm arrives. "When it calms down" is not a plan, because the calm is not scheduled.

**You are the only one who can decide.** This is not a burden to be minimised; it is the job. A machine can draft, publish, verify and refill. It cannot decide which venture gets the next two weeks, whether a price is wrong, or whether a thing you built is good. The distinguishing feature of an operator is that the deciding is not delegable. But deciding is bounded work: it can be written down, scheduled, and finished. Worrying is unbounded and cannot be. The two get confused constantly, and the confusion is expensive.

**The machine is built to run without you.** Not as a metaphor. The rails post. The bank refills. The deploy verifies. Nothing charges a card while you sleep, and nothing needs you at the moment it happens. Resting is therefore not neglect; it is using the system as designed. A person who cannot rest inside a system built for their absence has not finished building it.

Hold all three and the shape becomes clear. You are not trying to do less work because work is bad. You are refusing to let an unbounded surface consume a bounded person, while accepting the one part that genuinely is yours — the deciding — and scheduling it like the finite resource it is.

## 3. Why "when it calms down" is not a plan

There is a specific error that ends one-person businesses, and it is not laziness or lack of talent. It is the belief that the current intensity is anomalous.

The belief goes like this: this month is heavy because of the launch; next month will be lighter, and then I will sleep, walk, see people, take the Sunday. The launch ships. The next month is heavy because of something else — a rail breaks, a customer writes, a price is wrong, a competitor appears, an idea arrives that is genuinely good. The intensity is not anomalous. It is the steady state of a business whose surface area grows faster than its operator.

This is why the constraints in this book are structural rather than aspirational. "I should rest more" is a wish, and wishes lose to urgency every single time, because urgency has a deadline and rest does not. "The shutdown happens at a fixed hour whether the work is finished or not" is a rule, and rules hold in exactly the circumstances where intentions fail — which is to say, on the bad days, when they matter.

A boundary that arrives by itself is not a boundary. It is a collapse. The difference between a person who has run something for ten years and a person who burned out in year two is rarely talent and almost never luck. It is whether the boundary was chosen in advance or discovered afterwards in a hospital corridor.

## 4. What this book is not

This is not therapy, and it is not a substitute for care from a professional. It has nothing to say about clinical depression, anxiety disorders, trauma, grief, or anything else that a clinician should see. If you need that, this book is not it, and no amount of system design will make it be.

What this book is: the set of structural rules that stop *this specific way of working* from eating the person doing it. Running a business alone, on a machine that never stops, with an unbounded surface and one decider, produces a particular kind of wearing-down. It has a shape, the shape is predictable, and predictable things can be designed against.

That is the whole claim. Nine rules, a bad day, a pause switch, a way of holding the ledger apart from the self, and one chapter about where a book has to stop and a person has to start.

---

# Part Two — The nine non-negotiables

Nine rules. They are operational, they are checkable, and none of them requires motivation. That last clause is the important one: motivation is a resource that is already spent on the work. A rule that needs to be felt in order to be kept is not a rule; it is a mood with a checklist.

Each chapter below gives the rule, the mechanism it protects, what it looks like when it fails, and how to check it. The checks take seconds. Do them badly rather than skipping them.

## 5. Rule one — the shutdown happens every day

**The rule.** Five minutes, at a fixed hour, in writing, out loud, laptop closed, room left.

It sounds small enough to be an insult, which is why it is first. Write down every open loop — the thing you were in the middle of, the thing you are afraid you will forget, the message you owe someone. Name tomorrow's one outcome. Say out loud that the estate can run until eight in the morning, which is true and which your body does not believe. Close the laptop. Leave the room the laptop is in.

**The mechanism.** The mind does not have a way to know a day is over, because the work has no natural ending. A rail posts when it posts. A draft can always be improved. Every previous era of work had an external end — the shop closes, the shift ends, the light goes. A business that lives in a browser has no closing time unless one is imposed, and in the absence of one the mind keeps a background process open all night. That process is what wakes you at 3am with a sentence you should have written in an email.

The written list is the mechanism that actually works, and it works because of what it tells the background process: *it is recorded, you may stop holding it.* A loop held in the head is held by the part of the mind that cannot tell the difference between *unfinished* and *forgotten*. Written down, it becomes a task; in the head, it remains a threat.

**When it fails.** The failure is not dramatic. It is the person who "just checks one thing" after dinner, and then it is 11pm and they are rewriting copy on a page nobody is looking at. The tell is not exhaustion; it is the quality of the 11pm work, which is always worse than it feels.

**The check.** Did I say it out loud? The out-loud part is not theatre. Speaking closes a loop in a way that thinking about closing it does not.

## 6. Rule two — one day off a week, fully off

**The rule.** One day. Not "light". No estate screen, no money check, no drafts, no "just looking at the queue".

**The mechanism.** Attention does not recover in the gaps between tasks; it recovers in unbroken blocks. Twenty scattered hours of half-attention are not equivalent to one day of none, and the organism knows the difference even when the calendar does not. A day off is also the only honest test of the estate: on that day, you find out what actually depends on you.

**When it fails.** The half-day off. The day where you "only" answer one message and read one dashboard, which costs the whole day's recovery and delivers about ten minutes of work. This is the most common failure in the book, because it feels like diligence.

**The check.** Did anything from the business enter your head as a task? Then it was not a day off. Not a moral failing — a data point. Move it to the next one.

## 7. Rule three — sleep before midnight, and treat a short night as an incident

**The rule.** Sleep before midnight as the default. Three consecutive nights under six hours is not a busy week; it is an incident, and it is logged like one.

**The mechanism.** Sleep is not the reward for finishing work. It is the input to the only thing you are actually selling. Judgement, temper, the ability to notice that a number is wrong, the ability to say no to a plausible idea at 4pm — every one of those is paid for out of sleep. A person running on five hours does not feel impaired; they feel efficient, which is the dangerous part. They make decisions quickly and confidently, and the confidence is the symptom.

**When it fails.** It fails as a week that looks productive in the log and contains one or two expensive decisions. A price set too low. A message sent too sharp. A venture started because it seemed obvious at midnight. None of these show up as sleep damage; all of them are.

**The check.** Three nights. Count them. If you are at three, the next night is the work — not the queue, not the launch.

## 8. Rule four — the first ninety minutes belong to the day's one outcome

**The rule.** The first ninety minutes of the working day go to the one thing that matters, never to the inbox, never to other people's urgency.

**The mechanism.** Attention is not evenly distributed across a day; it is front-loaded, and the front is where the difficult, valuable, easily-avoided work has to happen. The inbox is the perfect thief because it is infinite, socially sanctioned, and always someone else's priority. An hour spent there in the morning is not an hour spent; it is the whole day's capacity to think, spent, before the thinking started.

**When it fails.** A day of small completions. Twelve replies sent, nothing decided, and a vague sense of having worked hard. This is the characteristic texture of a day that was lost at 9:05am.

**The check.** By 10:30, has the one outcome moved? If it has not, the morning was spent on other people, and tomorrow's version of the same choice is the whole fix.

## 9. Rule five — no money numbers between Sunday night and Monday's round

**The rule.** Between Sunday evening and the Monday review, do not check revenue, cash, or pipeline.

**The mechanism.** Checking a number you cannot change is not diligence; it is a way of feeling the fear on schedule. The number will be what it is on Sunday at 10pm and what it is on Monday at 9am. Looking at it on Sunday buys no information and costs a night's recovery — and the fear it produces is then carried into the Monday decision, which is the one place the number can actually be acted on.

**When it fails.** The Sunday-night dread that has no decision attached to it. It is one of the most reliable ways a one-person business ruins a weekend, and it disguises itself as being responsible.

**The check.** Did I open anything financial between Sunday sunset and Monday? The honest answer is usually yes. The second honest answer is that it changed nothing.

## 10. Rule six — move the body daily, outside if possible

**The rule.** Twenty minutes, no phone, no podcast about business.

**The mechanism.** It is the cheapest and most reliable regulator available, and it works on days that were not good. It is not optimising anything. It is the floor under a nervous system that spends its day in a chair, in a browser, in a state of mild alertness about things that are not physically present. Walking outside returns the body to a scale it can actually assess.

The "no podcast about business" clause is not contempt for podcasts. It is that the walk is the only twenty minutes in the day that is not an input to the business, and turning it into one converts rest into work with extra steps.

**When it fails.** It is dropped first, because it is the only rule with no visible output. This is exactly why it is a rule.

**The check.** Did you leave the building? Not the room, not the desk. The building.

## 11. Rule seven — one non-business conversation a day

**The rule.** One conversation with another human that has nothing to do with the estate.

**The mechanism.** A solo operator's isolation is not romantic; it is a slow loss of perspective, and perspective is the asset you are selling when you sell judgement. A person who has spoken only to their own systems for three weeks begins to find their own reasoning obvious, and obvious reasoning is how a business quietly walks into a wall. Other people are the only available instrument for calibrating what is normal.

**When it fails.** Badly and slowly. The first sign is not loneliness; it is certainty. The operator becomes increasingly sure of things nobody has checked, and increasingly uninterested in the conversations that would check them.

**The check.** Who did you talk to today about something that has no bearing on the work? If the answer is nobody, tomorrow's version of that is the task, and it is not optional because it feels inefficient.

## 12. Rule eight — the worry window

**The rule.** When anxiety arrives, give it twenty minutes with a pen: write the fear, the worst case, the next physical action. Then it is closed until the next window.

**The mechanism.** Anxiety written down becomes a list; anxiety held becomes a day. The writing does three distinct things. It converts a diffuse state into a named object, which is smaller than it felt. It forces the worst case onto paper, where it is usually survivable and occasionally specific. And it produces one physical action, which is the only part of the loop that can change anything.

**When it fails.** Anxiety is allowed to run as a background process all day, which is the mode it prefers: no conclusion to reach, no action to take, and a constant low tax on every other thought.

**The check.** Is there something written from the last twenty-four hours? If not, the worry is still circulating, and the window is twenty minutes you have not spent.

## 13. Rule nine — no new venture while two are unresolved

**The rule.** Do not start a new thing while two existing things are unresolved.

**The mechanism.** Novelty is the most seductive form of avoidance available to a builder. A new venture is pure possibility: no customers yet, no proof required, no judgment. An old venture that is stuck is the opposite — it is a question about whether the thing you built is good, and that question is unpleasant. So the builder, feeling stuck, begins something new, and the stall becomes structural instead of temporary.

The filing rule protects you from your own best ideas. Some of the ideas will be genuinely good. That is precisely why the rule has to be a rule and not a judgment call made in the moment by the person who wants to make it.

**When it fails.** The portfolio of six half-built things, each of which would have worked if anyone had stayed. It reads as ambition. It is usually avoidance with a release date.

**The check.** How many unresolved ventures do I have? If it is two or more, the answer is not a new one.

---

## 14. Keeping nine rules without a personality transplant

Nine rules is a lot for a person who is already busy, and the predictable failure is not rebellion. It is a good week, then one rule slips, then the slip is treated as evidence that the whole structure was unrealistic, and by Friday none of the nine are running. The structure is not the problem in that story. The absence of a re-entry protocol is.

**Keep the smallest version.** Every rule has a degenerate form that still counts. The shutdown can be sixty seconds and three lines. The day off can be an afternoon in which nothing work-shaped happens. The walk can be to the end of the street. The conversation can be one message to one person about something that is not the estate. Scaled-down is not failed; it is the rule doing its job, which is to keep the habit's shape intact until there is room for its substance.

**Count, do not judge.** A seven-box week — one box per rule, ticked or not — is a better instrument than any feeling about how the week went. Six of nine is information. Four of nine, three weeks running, is a finding about the business rather than about your character, and it usually points at a specific component with no failover.

**A broken rule is a missed flight, not a lost ticket.** You do not compensate by taking two flights. The next scheduled instance of the rule is the recovery, and nothing is owed in between. The instinct to repay a lost night's sleep with a heroic catch-up day is the instinct that turns a bad week into a bad month.

**Do not restructure in a bad week.** This is the rule about the rules. A bad week is when the temptation is strongest to rewrite the constraints instead of keeping them, and a constraint rewritten at that hour is not a constraint; it is a negotiation you are having with yourself while tired. Change the rules at the monthly review, in daylight, when the week was ordinary.

**One rule at a time.** If the system is not running at all, do not start with nine. Start with the shutdown, because it is the one that makes the others possible: a day that ends properly produces a night that recovers, and a recovered night produces a morning with ninety minutes in it. Three weeks of the shutdown, then add the day off.

## 15. The signals that arrive before the bad day

The bad-day protocol is a response. It is better to have a warning, and the warning is almost never a feeling. Feelings lag. These are the leading indicators, in the order they tend to appear.

**The first signal is the shrinking of the non-work life.** The walk gets shorter. The conversation gets postponed. The thing you did on Saturdays stops happening, one Saturday at a time, each time for a good reason. Nothing about this feels like decline; it feels like focus. It is the earliest and most reliable sign that the system is being paid for out of the operator rather than out of the estate.

**The second is that the queue stops moving.** Not that the work is piling up — that the *decisions* are. The same item appears in the estate screen for nine days. That is not laziness; it is a capacity problem, and it usually means the operator's attention is being spent on something that does not appear in the queue at all.

**The third is that the numbers stop being read.** Not looked at — read. A person in a bad stretch will open the dashboard and not see anything, because seeing requires the capacity to interpret, and interpretation has been spent elsewhere. Skipping the Monday review has a specific character: it is relief rather than avoidance, and relief is the tell.

**The fourth is a tone change in the writing.** The messages get shorter and flatter, or more defensive. Outgoing copy becomes either curt or over-explained; there is rarely a middle. If you read back three days of your own sent messages and they sound like a person you would not want to work for, that is data, not self-criticism.

**The fifth is sleep, and it is last because it is the least subtle.** By the time sleep has gone, the earlier four have usually been running for a fortnight.

None of these requires a mood tracker. Four of them are visible in artefacts you already produce: a calendar, a screen, a dashboard, a sent folder. Look at them once a week, for a minute, as evidence rather than as a judgment. If three of the five are showing, treat the week as if it contained a bad day, and take the protocol early — because a bad day met in advance costs an afternoon, and a bad day met late costs the week.

---

# Part Three — The bad day

## 16. The bad-day protocol

Some days the machine is fine and the operator is not. This is not an emergency and it does not require the day to be rescued. Three steps, in order.

**Step one — 2 minutes. Make it safe.** Run the estate screen once. If the one thing is under three minutes, do it. If not: nothing today. The estate is designed for this — a day without the owner is a day the rails still post.

**Step two — 10 minutes. Shrink the day.** Cancel what can be cancelled. One outcome becomes none, or becomes "eat, walk, sleep at a reasonable hour". Nothing is lost: the queue in `data/ops.json` is preserved exactly where it is. The world does not record which day a decision was made.

**Step three — the day. Leave it alone.** No catching up later in the same day — a bad day repaid at 11pm becomes a bad week. The evening shutdown still happens, even if the day contained nothing.

The point of the protocol is not to salvage the day. It is to end it cleanly, so that tomorrow starts from a floor rather than from a debt. A day that is closed properly costs one day. A day that is repaid costs four.

## 17. The pause switch

The estate must be pausable by one person in under a minute, without losing anything. It is, and the procedure is written down so it does not have to be invented on the worst day.

| To stop | How | What survives |
|---|---|---|
| Publishing | Disable the `press` workflow in the repo's Actions tab, or let the bank run down — it stops on its own and says so | State file, bank, cards, drafts. Nothing is re-sent when it resumes. |
| Deploying | Nothing to do. Deploys only run on a push. | The last verified deployment stays live. |
| Selling | Checkout links stay live. If a product must not be bought, say so on its page in one line — do not silently break the button. | Nothing. Orders already taken are honoured. |
| Everything | Do nothing at all for a week. The rails post, the site serves, the drafts accumulate in the outbox. | Everything. The outbox is a queue, not a deadline. |

**Pausing is a design feature, not a failure.** If pausing feels dangerous — if the thought of two days offline produces real dread rather than mild inconvenience — that is a finding about the business, not about you. It means something depends on your daily presence that should not. Fix it at the next monthly audit, and count it as the month's one thing killed.

The test of whether the estate was built properly is exactly this day: can it run while you cannot? If the answer is no, the fix is not more discipline. It is one more automation, and it is the highest-value work available to you.

## 18. The week after

The day after a bad day is not the day to catch up. It is the day to find out what happened.

Ask one question: what was the smallest thing I could not let go of yesterday? Whatever that is, it is the component with no failover. It is not the server and it is not the queue; it is some specific thing that only you can do, and it is holding you in place. That is the next automation, or the next delegation, or the next deletion. Deleting counts.

This is the discipline that turns a bad day into an engineering finding rather than a private failure. The estate is supposed to absorb your absence. Every day it does not is a bug report, and bug reports are the most useful thing a bad day produces.

---

# Part Four — The estate is not you

## 19. Ledger and self

The most useful sentence in this book, and the hardest to believe on a bad week:

> A venture that fails is a hypothesis that was tested. It is not a verdict on the person who tested it.

The estate is built on published failure — the ledger has a column for what did not work, and the catalogue carries the works that stalled. That posture has to apply to the operator as well, or it is a marketing position rather than a method.

Write failures in the ledger: with the mechanism, the cost, and the point at which it was obvious. Do not write them on yourself. The first produces a better estate; the second produces a worse operator. A failure recorded with its mechanism becomes a rule for next time. The same failure recorded as a fact about your character becomes a thing to carry, and carrying it costs the thing you need most, which is the willingness to try another one.

## 20. Record and worth

A quiet month is data. Zero sales is data. Both are inputs to a decision, and neither is a statement about whether you are allowed to rest on Sunday.

This separation is harder for a solo operator than for anyone else, because there is nobody in the building whose presence contradicts the story. In a company, a bad quarter is discussed in a room with other people, and the discussion itself is evidence that the quarter is a quarter and not a verdict. Alone, a bad quarter is a number in a browser at 10pm, and there is nothing in the room to disagree with the interpretation.

So the interpretation has to be given a structure. The next chapter is that structure, and it is deliberately short, because a method for bad months that requires energy will not be used in a bad month.

## 21. What to do with a bad month

Four steps, once, in writing:

1. **Name the number.** What actually happened, in one line. Not the story about what happened.
2. **Name the mechanism.** Which decision, or which absence of a decision, produced it.
3. **Name the next action.** One. Physical. Dated.
4. **Close the file.** Reviewed at the monthly audit, not re-read at night.

The fourth step is the one that gets skipped, and it is the one that matters. A bad month that is reviewed once becomes an input. A bad month that is re-read every night becomes the weather. The file is closed not because the problem is solved, but because the reading is finished.

## 22. The honest arithmetic of a solo estate

Running seven ventures alone is not a normal load, and the fact that the automation makes it possible does not make it light.

The automation does something specific and slightly deceptive: it removes the work that can be removed, which turns out to be most of the doing and almost none of the deciding. What remains is disproportionate — judgement, taste, and contact with other humans — and it arrives in a concentrated form that no traditional job trains a person for. In a company of fifty, one person might make three consequential decisions a week and be told by four people that they are wrong. In an estate, the same person makes thirty and is told by nobody.

That is a good job. It is also a job, and it needs hours, rest, and a life outside it to stay a good one. The number that matters is not how many ventures can be run by one person. It is how many can be run by one person who is still sleeping, still walking, still speaking to other humans, and still able to feel something other than urgency.

> The business exists so that a person can live. The moment it is the other way round, the automation has failed no matter how green the pipeline is.

---

# Part Five — Asking for help

## 23. Where this book stops

If low mood, dread or sleeplessness persists for more than a couple of weeks, or if work starts to feel pointless in a way that does not lift, that is not a scheduling problem and this book cannot fix it. Nothing in the previous chapters is a treatment. Nine rules and a pause switch are a floor, not a cure, and a person who needs care and instead optimises their calendar has made the situation worse in an organised way.

Speak to a doctor or a counsellor. In Zimbabwe, **Friendship Bench** is a free, evidence-based lay-counselling service run through primary care clinics and community spaces, and a general practitioner can refer you. If you are outside Zimbabwe, your national mental-health line is the right first call.

The distinction that matters: this book is for the person whose work is eating their life and who needs the work restructured. It is not for the person who is ill. The tricky part is that the first can become the second, quietly, and the person best placed to notice is not usually the one experiencing it.

## 24. Tell one person

Telling one person — a friend, a sibling, a peer who runs something — is worth more than any amount of system design. Not because they will fix it, and not because they will have advice. Because being witnessed is a different mechanism from being organised, and the estate cannot supply it.

The estate was built to survive your absence. It cannot be a substitute for your company. That sentence needs to be read twice: the whole architecture of autonomy, the rails, the refills, the verification — none of it can do the thing that another human does, which is to know how you are and ask.

Pick the person now, while it is easy. A specific name, not a category. Tell them one true sentence about how the work is going. That is the entire instruction, and it is harder than every rule in Part Two.

## 25. For the person reading this on someone else's behalf

If you are reading this because someone you know runs something alone, here is what is useful and what is not.

Useful: asking about sleep, specifically and concretely. Asking what happens if they do nothing for a week — and listening to whether the answer is calm. Noticing when the conversation is only about the work. Offering a specific thing at a specific time rather than "let me know if you need anything", which asks them to do the work of asking.

Not useful: telling them to take a break, which they know; admiring their discipline, which reinforces the thing that is hurting them; and treating the business as the interesting part of them, which is how a person becomes their own output.

The most useful sentence you can say is the one this book keeps returning to: *the business exists so that you can live, not the other way round.* Say it once. Then say something that has nothing to do with the business.

---

# End matter

## The card

Nine rules. Print it. Put it where you work.

| # | Rule | Check |
|---|---|---|
| 1 | The shutdown happens every day — five minutes, written, out loud | Did I say it out loud? |
| 2 | One day off a week, fully off | Did the business enter my head as a task? |
| 3 | Sleep before midnight; three short nights is an incident | Count them: am I at three? |
| 4 | The first ninety minutes belong to the day's one outcome | By 10:30, has it moved? |
| 5 | No money numbers between Sunday night and Monday | Did I open anything financial? |
| 6 | Move the body daily, outside, no phone | Did I leave the building? |
| 7 | One non-business conversation a day | Who did I talk to about something else? |
| 8 | The worry window: twenty minutes, pen, then closed | Is there something written from the last day? |
| 9 | No new venture while two are unresolved | How many are unresolved? |

**The bad day:** make it safe · shrink the day · leave it alone.

**The pause switch:** disable the press workflow · stop pushing · leave the checkouts alone · or do nothing for a week and let the outbox fill.

**The three sentences:** The machine runs; I steer, and steering has hours. A failure is a hypothesis that was tested. The business exists so that a person can live.

## A closing statement

Almost every business I have seen is arranged the wrong way round. The person is the fuel. Their evenings are the runway, their health is the working capital, and the thing they built becomes the thing they answer to.

It arrives politely. A quiet week becomes a busy one. The work that pays gets done on Sunday because Sunday was free. Three nights under six hours is not a decision anyone makes; it is a subtraction nobody watched. Then a year has gone and the business is real, and the life it was supposed to fund is the thing on the invoice.

The alternative is not balance as an aesthetic. It is four ordinary things, in this order: sleep is not negotiable; the hours are fixed and the work fits inside them; nothing important depends on you being reachable; the money is a floor, not a score.

A machine can send at three in the morning. It should not. That is not a limit on the machine. It is a limit on the person who would otherwise be awake to supervise it.

*Courage Garikai · Jacaranda Labs · Harare · November 2026*
