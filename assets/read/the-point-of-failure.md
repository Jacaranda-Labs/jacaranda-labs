---
title: The Point of Failure: An Operating Manual for the Person Running the Estate
series: The Operator's Books
byline: Courage Garikai — Jacaranda Labs, Harare, Zimbabwe
programme: Jacaranda Labs Press — Harare
date: First edition, November 2026
slug: the-point-of-failure
---

# Front matter

## About this book

This is a manual for one person: the operator of a business small enough that they are the only human in it, and automated enough that the business keeps working while they are not there. It is written for the person who owns the consequences of machine work they did not perform, and who has discovered that the machine has a failover everywhere except the one place that matters.

It is not a book about productivity. Productivity books assume the work is a fixed quantity and the person a variable to be optimised. This book assumes the opposite: the work is unbounded, the person is finite, and the only way to hold both is to design the business so that the finite thing is never asked to be infinite.

## How to read it

**If you have an hour**, read Part One and Part Three. That is the diagnosis and the bad day.

**If you have a day**, read it straight through, then fill in the instruments in Appendix B. The instruments are the book; the prose is the argument for them.

**If the week is already bad**, start at the bad-day protocol in chapter 16, do the three steps, and come back when a day has room in it. There is no penalty for arriving at the book sideways.

**If you are reading this for someone else**, chapter 23 is addressed to you, and it is four paragraphs.

Each part opens with a statement of what it is for and closes with the thing you should be able to do afterwards. The activities in Part Six are not homework; they are the parts of the method that a reader has to perform once in order to own.

## A note on evidence and on what this is not

This book is not therapy and it is not a substitute for care from a professional. It has nothing to say about clinical depression, anxiety disorders, trauma or grief, and no amount of system design will make it say anything. Chapter 22 says where the book stops and a person has to start, and that chapter is not decoration; it is the one that matters if the earlier ones have stopped helping.

What the book does claim is narrower and testable: that a particular way of working — one person, a machine that acts at all hours, an unbounded surface, one decider — produces a predictable kind of wearing-down, and that predictable things can be designed against. The nine rules are the design. They are operational, they are checkable, and none of them requires motivation.

The evidence is one estate: seven ventures, twenty-two works at the time of writing (twenty-four including the two new books in this series), five publishing rails, an hourly monitor, a three-touch outreach sequence, and roughly three hours twenty minutes a week of human attention, of which about seventeen minutes is genuinely manual. One estate is a case, not a study. The rules are stated in a form you can falsify in your own operation within a month, and Appendix C is the form on which to do it.

---

# Part One — The failure that is not the server

*What this part is for: to establish that the operator is a component, with the same obligations as any other component, and that the obligations have been neglected. By the end you should be able to say which single part of your business has no failover, and why.*

## 1. Everything here is redundant except the person

This book was written from inside a working estate: seven ventures, twenty-two works, five posting rails, a queue that refills itself, deploys that verify their own work, checkouts that take money at three in the morning without asking anyone. Every part of that was built for one reason, and it was not efficiency. It was so that one person could run it without being destroyed by it.

Inside that system, almost everything has a failover. The press rail retries. The bank refills before it empties. A deploy that lands wrong is redeployed and verified. A worker that returns a 404 at the front door is caught by an hourly check that says so in plain language. If a credential expires, the run says *credential missing* instead of going quiet. The design assumption is that any single component can be absent for a while and the estate keeps standing.

There is exactly one component with no redundancy at all. It is not the server. It is the operator.

> Figure 1 sets the two columns side by side: six components that fail and recover, and one that fails and does not.

![Figure 1](/read/fig/a-01-single-point.svg)

*Figure 1 — Every component has a failover except one. The list on the left is the estate's own design assumption; the box on the right is the assumption nobody wrote down.*

That asymmetry is the reason this book exists. Every other risk in a one-person business is a technical problem with a technical answer — a retry, a monitor, a second copy, a smaller blast radius. The operator is a single point of failure with no replica, no warm standby, and no way to fail over to a second instance of oneself. Everything the estate does rests on one nervous system, one sleep pattern, one capacity to make a decision at four in the afternoon.

So the operator gets the same treatment every other component gets: written down, checked, given limits, monitored. Not as self-care. As engineering.

**Activity 1.1 — Name the component.** Take a sheet of paper and write the six things in your business that could stop for a day without the business stopping. Then write the one thing that cannot. Be specific: not "me" but "me deciding what to build next", or "me answering a customer's complaint", or "me noticing that a number is wrong". The specific version is the one you can act on later. *(5 minutes. Appendix B, sheet 1.)*

## 2. Three things are true at once, and holding all three is the skill

Most advice for people who work alone fails because it resolves one of these at the expense of the others. The person either works constantly, or they abandon the thing they built; they either micromanage every output, or they let a system run unattended and never look. The following three facts are simultaneously true, and the whole discipline of operating an estate is holding them without dropping one.

**The work is genuinely unbounded.** Seven ventures, twenty-two works, five rails. There is always another thing. No amount of finishing changes this. The list does not shrink because the work does not end; it changes shape. This is not a temporary phase to be survived until the calm arrives. "When it calms down" is not a plan, because the calm is not scheduled.

**You are the only one who can decide.** This is not a burden to be minimised; it is the job. A machine can draft, publish, verify and refill. It cannot decide which venture gets the next two weeks, whether a price is wrong, or whether a thing you built is good. The distinguishing feature of an operator is that the deciding is not delegable. But deciding is bounded work: it can be written down, scheduled, and finished. Worrying is unbounded and cannot be. The two get confused constantly, and the confusion is expensive.

**The machine is built to run without you.** Not as a metaphor. The rails post. The bank refills. The deploy verifies. Nothing charges a card while you sleep, and nothing needs you at the moment it happens. Resting is therefore not neglect; it is using the system as designed. A person who cannot rest inside a system built for their absence has not finished building it.

Hold all three and the shape becomes clear. You are not trying to do less work because work is bad. You are refusing to let an unbounded surface consume a bounded person, while accepting the one part that genuinely is yours — the deciding — and scheduling it like the finite resource it is.

**Activity 1.2 — The three-column test.** Write three headings: *unbounded*, *mine to decide*, *already handled*. For ten minutes, put everything currently on your mind into one column. Anything in the first column gets a boundary, not a plan. Anything in the second gets a slot in the week. Anything in the third gets struck through, and you are allowed to feel the relief. Most people find that the first column is much longer than the second, and that the second is where the business actually is. *(10 minutes.)*

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

*What this part is for: to give you nine rules that survive a bad week, each with the mechanism it protects and a check that takes seconds. By the end you should be running at least the first, and know which of the other eight you are currently failing.*

Nine rules. They are operational, they are checkable, and none of them requires motivation. That last clause is the important one: motivation is a resource that is already spent on the work. A rule that needs to be felt in order to be kept is not a rule; it is a mood with a checklist.

Each chapter below gives the rule, the mechanism it protects, what it looks like when it fails, and how to check it. The checks take seconds. Do them badly rather than skipping them.

![Figure 2](/read/fig/a-02-nine.svg)

*Figure 2 — The nine rules and their checks. Appendix B, sheet 2 is the same table as a seven-box week you can keep on a wall.*

## 5. Rule one — the shutdown happens every day

**The rule.** Five minutes, at a fixed hour, in writing, out loud, laptop closed, room left.

It sounds small enough to be an insult, which is why it is first. Write down every open loop — the thing you were in the middle of, the thing you are afraid you will forget, the message you owe someone. Name tomorrow's one outcome. Say out loud that the estate can run until eight in the morning, which is true and which your body does not believe. Close the laptop. Leave the room the laptop is in.

**The mechanism.** The mind does not have a way to know a day is over, because the work has no natural ending. A rail posts when it posts. A draft can always be improved. Every previous era of work had an external end — the shop closes, the shift ends, the light goes. A business that lives in a browser has no closing time unless one is imposed, and in the absence of one the mind keeps a background process open all night. That process is what wakes you at 3am with a sentence you should have written in an email.

The written list is the mechanism that actually works, and it works because of what it tells the background process: *it is recorded, you may stop holding it.* A loop held in the head is held by the part of the mind that cannot tell the difference between *unfinished* and *forgotten*. Written down, it becomes a task; in the head, it remains a threat.

**When it fails.** The failure is not dramatic. It is the person who "just checks one thing" after dinner, and then it is 11pm and they are rewriting copy on a page nobody is looking at. The tell is not exhaustion; it is the quality of the 11pm work, which is always worse than it feels.

**The check.** Did I say it out loud? The out-loud part is not theatre. Speaking closes a loop in a way that thinking about closing it does not.

**Activity 5.1 — The five-minute shutdown, once, properly.** Tonight: set a timer for five minutes. Write every open loop on one page, including the trivial ones. Write tomorrow's one outcome as a single sentence with a verb in it. Say out loud, to the room: "It is recorded. The estate can run until eight." Close the laptop. Stand up and leave the room. Do not evaluate how it felt; the first one always feels like nothing. Do it seven nights and then evaluate. *(5 minutes × 7. Template in Appendix B, sheet 3.)*

## 6. Rule two — one day off a week, fully off

**The rule.** One day. Not "light". No estate screen, no money check, no drafts, no "just looking at the queue".

**The mechanism.** Attention does not recover in the gaps between tasks; it recovers in unbroken blocks. Twenty scattered hours of half-attention are not equivalent to one day of none, and the organism knows the difference even when the calendar does not. A day off is also the only honest test of the estate: on that day, you find out what actually depends on you.

**When it fails.** The half-day off. The day where you "only" answer one message and read one dashboard, which costs the whole day's recovery and delivers about ten minutes of work. This is the most common failure in the book, because it feels like diligence.

**The check.** Did anything from the business enter your head as a task? Then it was not a day off. Not a moral failing — a data point. Move it to the next one.

**Activity 6.1 — The dependency audit.** Take your day off. In the evening, write down every business event you would have wanted to know about during it. Then look at the list: each item is either (a) something the estate should have told you afterwards and did not, (b) something you did not need to know at all, or (c) something that genuinely needed you, which is a design fault with a date on it. Category (c) items become the month's automation work. *(The day, then 10 minutes.)*

## 7. Rule three — sleep before midnight, and treat a short night as an incident

**The rule.** Sleep before midnight as the default. Three consecutive nights under six hours is not a busy week; it is an incident, and it is logged like one.

**The mechanism.** Sleep is not the reward for finishing work. It is the input to the only thing you are actually selling. Judgement, temper, the ability to notice that a number is wrong, the ability to say no to a plausible idea at 4pm — every one of those is paid for out of sleep. A person running on five hours does not feel impaired; they feel efficient, which is the dangerous part. They make decisions quickly and confidently, and the confidence is the symptom.

**When it fails.** It fails as a week that looks productive in the log and contains one or two expensive decisions. A price set too low. A message sent too sharp. A venture started because it seemed obvious at midnight. None of these show up as sleep damage; all of them are.

**The check.** Three nights. Count them. If you are at three, the next night is the work — not the queue, not the launch.

**Activity 7.1 — The incident log.** For two weeks, record only two numbers: hours slept, and the single most consequential decision of the day. Do not analyse as you go. At the end, lay the two columns beside each other and mark which decisions you would make again. Most people find the correlation in the first fortnight, and after that the rule stops needing to be believed. *(1 minute a day, 14 days. Appendix B, sheet 4.)*

## 8. Rule four — the first ninety minutes belong to the day's one outcome

**The rule.** The first ninety minutes of the working day go to the one thing that matters, never to the inbox, never to other people's urgency.

**The mechanism.** Attention is not evenly distributed across a day; it is front-loaded, and the front is where the difficult, valuable, easily-avoided work has to happen. The inbox is the perfect thief because it is infinite, socially sanctioned, and always someone else's priority. An hour spent there in the morning is not an hour spent; it is the whole day's capacity to think, spent, before the thinking started.

**When it fails.** A day of small completions. Twelve replies sent, nothing decided, and a vague sense of having worked hard. This is the characteristic texture of a day that was lost at 9:05am.

**The check.** By 10:30, has the one outcome moved? If it has not, the morning was spent on other people, and tomorrow's version of the same choice is the whole fix.

**Activity 8.1 — The one-outcome sentence.** An outcome is not a task. "Work on pricing" is a task. "The price on three ventures is changed, published, and the page no longer apologises" is an outcome. Write tomorrow's outcome tonight, in that form: a state of the world that will be true by lunchtime or will not. Then tomorrow, before the inbox, work only on it for ninety minutes. *(5 minutes to write, 90 to do.)*

## 9. Rule five — no money numbers between Sunday night and Monday's round

**The rule.** Between Sunday evening and the Monday review, do not check revenue, cash, or pipeline.

**The mechanism.** Checking a number you cannot change is not diligence; it is a way of feeling the fear on schedule. The number will be what it is on Sunday at 10pm and what it is on Monday at 9am. Looking at it on Sunday buys no information and costs a night's recovery — and the fear it produces is then carried into the Monday decision, which is the one place the number can actually be acted on.

**When it fails.** The Sunday-night dread that has no decision attached to it. It is one of the most reliable ways a one-person business ruins a weekend, and it disguises itself as being responsible.

**The check.** Did I open anything financial between Sunday sunset and Monday? The honest answer is usually yes. The second honest answer is that it changed nothing.

**Activity 9.1 — The Monday round.** Replace the checking with a scheduled reading. Mondays, at the same hour, fifteen minutes: cash, revenue, pipeline, and one sentence on what the numbers imply. Written down. Outside that window the numbers do not exist. The point is not to look less; it is to look in the only hour in which looking produces a decision. *(15 minutes, weekly. Appendix B, sheet 5.)*

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

**Activity 11.1 — The certainty audit.** Once a month, write down the three things you are most sure about in the business. Then, for each, write the name of a person outside the business who has heard the claim and disagreed, or the name of a person you could ask. Certainty with no second reader is not conviction; it is an unexamined position, and it is the one most likely to be wrong. *(20 minutes, monthly.)*

## 12. Rule eight — the worry window

**The rule.** When anxiety arrives, give it twenty minutes with a pen: write the fear, the worst case, the next physical action. Then it is closed until the next window.

**The mechanism.** Anxiety written down becomes a list; anxiety held becomes a day. The writing does three distinct things. It converts a diffuse state into a named object, which is smaller than it felt. It forces the worst case onto paper, where it is usually survivable and occasionally specific. And it produces one physical action, which is the only part of the loop that can change anything.

> The difference between the two columns in Figure 5 is not optimism. It is that one of them has an end.

![Figure 5](/read/fig/a-05-worry.svg)

*Figure 5 — The loop and the list. Both take about twenty minutes; only one of them finishes.*

**When it fails.** Anxiety is allowed to run as a background process all day, which is the mode it prefers: no conclusion to reach, no action to take, and a constant low tax on every other thought.

**The check.** Is there something written from the last twenty-four hours? If not, the worry is still circulating, and the window is twenty minutes you have not spent.

**Activity 12.1 — The first window.** The next time you notice the feeling, set a timer for twenty minutes and write, in this order: the fear in one sentence; the worst realistic case and whether you would survive it; the next physical action, small enough that you could do it today. Then close the notebook. If it comes back outside a window, write one line — "this is the worry, the window is at four" — and continue. *(20 minutes.)*

## 13. Rule nine — no new venture while two are unresolved

**The rule.** Do not start a new thing while two existing things are unresolved.

**The mechanism.** Novelty is the most seductive form of avoidance available to a builder. A new venture is pure possibility: no customers yet, no proof required, no judgment. An old venture that is stuck is the opposite — it is a question about whether the thing you built is good, and that question is unpleasant. So the builder, feeling stuck, begins something new, and the stall becomes structural instead of temporary.

The filing rule protects you from your own best ideas. Some of the ideas will be genuinely good. That is precisely why the rule has to be a rule and not a judgment call made in the moment by the person who wants to make it.

**When it fails.** The portfolio of six half-built things, each of which would have worked if anyone had stayed. It reads as ambition. It is usually avoidance with a release date.

**The check.** How many unresolved ventures do I have? If it is two or more, the answer is not a new one.

**Activity 13.1 — The unresolved register.** List every venture you are currently running or half-running. Beside each, write one of four words: *growing*, *steady*, *stalled*, *unknown*. Count the last two. If the count is two or more, the next new idea goes in a file called *after*, with the date it arrived, and nothing else happens to it this month. *(10 minutes. Appendix B, sheet 6.)*

## 14. Keeping nine rules without a personality transplant

Nine rules is a lot for a person who is already busy, and the predictable failure is not rebellion. It is a good week, then one rule slips, then the slip is treated as evidence that the whole structure was unrealistic, and by Friday none of the nine are running. The structure is not the problem in that story. The absence of a re-entry protocol is.

**Keep the smallest version.** Every rule has a degenerate form that still counts. The shutdown can be sixty seconds and three lines. The day off can be an afternoon in which nothing work-shaped happens. The walk can be to the end of the street. The conversation can be one message to one person about something that is not the estate. Scaled-down is not failed; it is the rule doing its job, which is to keep the habit's shape intact until there is room for its substance.

**Count, do not judge.** A seven-box week — one box per rule, ticked or not — is a better instrument than any feeling about how the week went. Six of nine is information. Four of nine, three weeks running, is a finding about the business rather than about your character, and it usually points at a specific component with no failover.

**A broken rule is a missed flight, not a lost ticket.** You do not compensate by taking two flights. The next scheduled instance of the rule is the recovery, and nothing is owed in between. The instinct to repay a lost night's sleep with a heroic catch-up day is the instinct that turns a bad week into a bad month.

**Do not restructure in a bad week.** This is the rule about the rules. A bad week is when the temptation is strongest to rewrite the constraints instead of keeping them, and a constraint rewritten at that hour is not a constraint; it is a negotiation you are having with yourself while tired. Change the rules at the monthly review, in daylight, when the week was ordinary.

**One rule at a time.** If the system is not running at all, do not start with nine. Start with the shutdown, because it is the one that makes the others possible: a day that ends properly produces a night that recovers, and a recovered night produces a morning with ninety minutes in it. Three weeks of the shutdown, then add the day off.

**Activity 14.1 — The four-week installation.** Write the nine rules as a column. Beside each, write the date you will start it. Start with the shutdown. Add one rule a week; do not add a second until the first has seven consecutive days. Four weeks from today you have a system that has actually been run, rather than a system that was designed. *(10 minutes to plan, 4 weeks to do.)*

## 15. The clock

The method has three units of time and no others. The day has two instances. The week has one review. The month has one long review. Nothing else is scheduled, and in particular there is no hourly loop for the operator — the rails have those, and that is the point.

![Figure 3](/read/fig/a-03-clock.svg)

*Figure 3 — The only three units. Everything in this book fits into them, and if something does not fit, it is not in the method.*

| When | How long | What | Where |
|---|---|---|---|
| Morning | 10 min | the estate screen · the one thing · today's outcome | wherever the screen runs |
| Evening | 5 min | the shutdown: written, out loud, closed | the doorway, not the desk |
| Weekly | 45 min | the review: nine boxes, one page, next week's outcome | same hour every week |
| Monthly | 2 h, first Monday | kill one thing · amend one rule · read the money | away from the desk |
| Quarterly | half a day | the honest arithmetic: is this still a business that supports a life? | out of the building |

The shutdown is daily because the mind needs a daily boundary. The review is weekly because a week is the shortest period in which a business can be seen to have a direction. The month is monthly because that is the shortest period in which a bad decision has finished revealing itself. The quarter is quarterly because that is how long it takes to know whether the whole thing is working, and asking the question more often produces anxiety rather than information.

---

# Part Three — The bad day

*What this part is for: to give you a procedure for the day when the machine is fine and you are not, and a switch that stops the machine when you cannot. By the end you should be able to end a bad day in fifteen minutes without owing anything to the next one.*

## 16. The bad-day protocol

Some days the machine is fine and the operator is not. This is not an emergency and it does not require the day to be rescued. Three steps, in order.

![Figure 4](/read/fig/a-04-badday.svg)

*Figure 4 — The three steps. Note what is missing from the diagram: nothing about catching up.*

**Step one — 2 minutes. Make it safe.** Run the estate screen once. If the one thing is under three minutes, do it. If not: nothing today. The estate is designed for this — a day without the owner is a day the rails still post.

**Step two — 10 minutes. Shrink the day.** Cancel what can be cancelled. One outcome becomes none, or becomes "eat, walk, sleep at a reasonable hour". Nothing is lost: the queue in `data/ops.json` is preserved exactly where it is. The world does not record which day a decision was made.

**Step three — the day. Leave it alone.** No catching up later in the same day — a bad day repaid at 11pm becomes a bad week. The evening shutdown still happens, even if the day contained nothing.

The point of the protocol is not to salvage the day. It is to end it cleanly, so that tomorrow starts from a floor rather than from a debt. A day that is closed properly costs one day. A day that is repaid costs four.

**Activity 16.1 — Pre-decide it.** Today, while you are well, decide what your bad day looks like: which outcome you will drop, who you will tell, what the smallest version of the day is. Write it on the back of the card in Appendix A. A protocol invented on the day is not a protocol; it is an improvisation by a person with less capacity than usual. *(10 minutes, once.)*

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

**Activity 17.1 — Time the pause.** Put a timer on. Stop every automated thing you run, one at a time, and record how long each took and what you had to remember in order to do it. Anything that took more than sixty seconds, or that required a fact you had to look up, is a defect. Write the defect down with a date. *(15 minutes, quarterly.)*

## 18. The week after

The day after a bad day is not the day to catch up. It is the day to find out what happened.

Ask one question: what was the smallest thing I could not let go of yesterday? Whatever that is, it is the component with no failover. It is not the server and it is not the queue; it is some specific thing that only you can do, and it is holding you in place. That is the next automation, or the next delegation, or the next deletion. Deleting counts.

This is the discipline that turns a bad day into an engineering finding rather than a private failure. The estate is supposed to absorb your absence. Every day it does not is a bug report, and bug reports are the most useful thing a bad day produces.

---

# Part Four — The estate is not you

*What this part is for: to separate the record from the person, so that a failure produces a rule rather than a verdict. By the end you should have a way of closing a bad month in four steps that you can actually perform while having one.*

## 19. Ledger and self

The most useful sentence in this book, and the hardest to believe on a bad week:

> A venture that fails is a hypothesis that was tested. It is not a verdict on the person who tested it.

The estate is built on published failure — the ledger has a column for what did not work, and the catalogue carries the works that stalled. That posture has to apply to the operator as well, or it is a marketing position rather than a method.

Write failures in the ledger: with the mechanism, the cost, and the point at which it was obvious. Do not write them on yourself. The first produces a better estate; the second produces a worse operator. A failure recorded with its mechanism becomes a rule for next time. The same failure recorded as a fact about your character becomes a thing to carry, and carrying it costs the thing you need most, which is the willingness to try another one.

**Activity 19.1 — The mechanism sentence.** Take a failure from the last six months that you still think about. Write it twice. First as a verdict: "I am the kind of person who…" Then as a mechanism: "the decision was X, the information missing was Y, and it was obvious by Z." Destroy the first. Keep the second. The point is not positive thinking; it is that only one of the two sentences can be acted on. *(15 minutes.)*

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

**Activity 22.1 — The quarter-hour audit.** Once a quarter, answer four questions in numbers, not adjectives: How many hours did I work last week? How many nights under six hours? How many non-business conversations did I have? What did I do that had no return except that I wanted to? If any of the first three has moved in the wrong direction for two quarters running, the problem is not the market. *(30 minutes, quarterly. Appendix B, sheet 7.)*

## 23. The signals that arrive before the bad day

The bad-day protocol is a response. It is better to have a warning, and the warning is almost never a feeling. Feelings lag. These are the leading indicators, in the order they tend to appear.

![Figure 6](/read/fig/a-06-signals.svg)

*Figure 6 — Five signals. Four of them are visible in artefacts you already produce; none of them requires a mood tracker.*

**The first signal is the shrinking of the non-work life.** The walk gets shorter. The conversation gets postponed. The thing you did on Saturdays stops happening, one Saturday at a time, each time for a good reason. Nothing about this feels like decline; it feels like focus. It is the earliest and most reliable sign that the system is being paid for out of the operator rather than out of the estate.

**The second is that the queue stops moving.** Not that the work is piling up — that the *decisions* are. The same item appears in the estate screen for nine days. That is not laziness; it is a capacity problem, and it usually means the operator's attention is being spent on something that does not appear in the queue at all.

**The third is that the numbers stop being read.** Not looked at — read. A person in a bad stretch will open the dashboard and not see anything, because seeing requires the capacity to interpret, and interpretation has been spent elsewhere. Skipping the Monday review has a specific character: it is relief rather than avoidance, and relief is the tell.

**The fourth is a tone change in the writing.** The messages get shorter and flatter, or more defensive. Outgoing copy becomes either curt or over-explained; there is rarely a middle. If you read back three days of your own sent messages and they sound like a person you would not want to work for, that is data, not self-criticism.

**The fifth is sleep, and it is last because it is the least subtle.** By the time sleep has gone, the earlier four have usually been running for a fortnight.

None of these requires a mood tracker. Four of them are visible in artefacts you already produce: a calendar, a screen, a dashboard, a sent folder. Look at them once a week, for a minute, as evidence rather than as a judgment. If three of the five are showing, treat the week as if it contained a bad day, and take the protocol early — because a bad day met in advance costs an afternoon, and a bad day met late costs the week. *(Activity: Appendix B, sheet 8 — the weekly five-signal check, 1 minute.)*

---

# Part Five — Asking for help

*What this part is for: to say plainly where this book stops, and what to do at that line.*

## 24. Where this book stops

If low mood, dread or sleeplessness persists for more than a couple of weeks, or if work starts to feel pointless in a way that does not lift, that is not a scheduling problem and this book cannot fix it. Nothing in the previous chapters is a treatment. Nine rules and a pause switch are a floor, not a cure, and a person who needs care and instead optimises their calendar has made the situation worse in an organised way.

Speak to a doctor or a counsellor. In Zimbabwe, **Friendship Bench** is a free, evidence-based lay-counselling service run through primary care clinics and community spaces, and a general practitioner can refer you. If you are outside Zimbabwe, your national mental-health line is the right first call.

The distinction that matters: this book is for the person whose work is eating their life and who needs the work restructured. It is not for the person who is ill. The tricky part is that the first can become the second, quietly, and the person best placed to notice is not usually the one experiencing it.

## 25. Tell one person

Telling one person — a friend, a sibling, a peer who runs something — is worth more than any amount of system design. Not because they will fix it, and not because they will have advice. Because being witnessed is a different mechanism from being organised, and the estate cannot supply it.

The estate was built to survive your absence. It cannot be a substitute for your company. That sentence needs to be read twice: the whole architecture of autonomy, the rails, the refills, the verification — none of it can do the thing that another human does, which is to know how you are and ask.

Pick the person now, while it is easy. A specific name, not a category. Tell them one true sentence about how the work is going. That is the entire instruction, and it is harder than every rule in Part Two.

**Activity 25.1 — The name.** Write one name. Not a role, not "my friend" — a name. Then write the sentence you would say to them, in the words you would actually use, which will not be the words in this book. Then send it this week. There is no template for this because a template would defeat the purpose. *(10 minutes, then one message.)*

## 26. For the person reading this on someone else's behalf

If you are reading this because someone you know runs something alone, here is what is useful and what is not.

Useful: asking about sleep, specifically and concretely. Asking what happens if they do nothing for a week — and listening to whether the answer is calm. Noticing when the conversation is only about the work. Offering a specific thing at a specific time rather than "let me know if you need anything", which asks them to do the work of asking.

Not useful: telling them to take a break, which they know; admiring their discipline, which reinforces the thing that is hurting them; and treating the business as the interesting part of them, which is how a person becomes their own output.

The most useful sentence you can say is the one this book keeps returning to: *the business exists so that you can live, not the other way round.* Say it once. Then say something that has nothing to do with the business.

---

# Part Six — The activities

*What this part is for: to hold every exercise in one place, in the order the book uses them, so that a reader can work through the method without re-reading the prose. Everything here is also in Appendix B as a printable sheet.*

## 27. How to use the activities

There are eighteen activities. They are not all for everyone, and they are not all for now. Three groups:

**The installation set (do these first, in this order).** Activity 5.1 (the shutdown), 7.1 (the incident log), 14.1 (the four-week installation), 16.1 (pre-decide the bad day), 25.1 (the name). Together these take about an hour of planning and four weeks of practice, and they produce a working floor.

**The diagnostic set (do these when something feels wrong).** 1.1 (name the component), 1.2 (the three-column test), 6.1 (the dependency audit), 11.1 (the certainty audit), 13.1 (the unresolved register). These are the instruments you reach for when the week has gone sideways and you cannot say why.

**The quarterly set (do these four times a year).** 9.1 (the Monday round), 17.1 (time the pause), 19.1 (the mechanism sentence), 22.1 (the quarter-hour audit). These produce the numbers that tell you whether the method is working, as opposed to whether it is being practised.

## 28. The activity index

| # | Activity | Time | When | Sheet |
|---|---|---|---|---|
| 1.1 | Name the component | 5 min | once | B1 |
| 1.2 | The three-column test | 10 min | when overwhelmed | B1 |
| 5.1 | The five-minute shutdown | 5 min × 7 | nightly, forever | B3 |
| 6.1 | The dependency audit | the day + 10 min | monthly | — |
| 7.1 | The incident log | 1 min × 14 | quarterly | B4 |
| 8.1 | The one-outcome sentence | 5 min + 90 | daily | B3 |
| 9.1 | The Monday round | 15 min | weekly | B5 |
| 11.1 | The certainty audit | 20 min | monthly | — |
| 12.1 | The first window | 20 min | as needed | B9 |
| 13.1 | The unresolved register | 10 min | monthly | B6 |
| 14.1 | The four-week installation | 10 min + 4 wk | once | B2 |
| 16.1 | Pre-decide the bad day | 10 min | once, then quarterly | A |
| 17.1 | Time the pause | 15 min | quarterly | — |
| 19.1 | The mechanism sentence | 15 min | after a failure | — |
| 22.1 | The quarter-hour audit | 30 min | quarterly | B7 |
| 25.1 | The name | 10 min | now | — |
| — | The seven-box week | 1 min | weekly | B2 |
| — | The five-signal check | 1 min | weekly | B8 |

## 29. Three worked examples

**Worked example — the shutdown, done badly and then well.** A first attempt: "Finish pricing. Reply to T. Check the deploy." That is a task list, not a shutdown; it holds the same loops it was meant to release, and it produces the 3am waking because nothing in it says *this is finished for today*. A second attempt, the same evening: "Pricing: three ventures, decided, not published — decision is X, publishing is tomorrow at 10. T: owes me a number, not the other way round, so nothing is owed tonight. Deploy: verified at 18:20, nothing to do. Tomorrow's one outcome: the pricing page no longer apologises." Then, out loud: "It is recorded. The estate can run until eight." The difference is not length. It is that every item has been given a status, and one of them has been given a time.

**Worked example — a bad month closed in four lines.** "March: zero new customers, and the one that churned had been quiet for six weeks. Mechanism: I stopped writing the Monday round in February, so the quiet was not visible until it was a churn. Next action: the Monday round at 9am, in the calendar, recurring — 12 March." Then the file is closed and read once, at the monthly review, and not at night. The value is not in the lines; it is in the closing.

**Worked example — a bad day, with the protocol.** Woke at 4am, no reason, could not get back. At 8:40 the screen said the one thing was forty minutes of copy work. Step one: ran the screen, saw the thing, decided it was not under three minutes — so nothing today. Step two: moved two calls, told one person "I am off today, back tomorrow", and set the day's outcome to "eat, walk, sleep at a reasonable hour". Step three: did not open the laptop again, including at 9pm when the thought arrived. Shutdown at 21:30, three lines, out loud, door closed. Cost: one day. The version where the forty minutes gets done at 11pm costs the week, and this is the arithmetic the protocol exists to make obvious.

## 30. What to do if you only do one thing

If everything in this book is too much — if the week is bad enough that even the installation set is impossible — then do this one thing, and nothing else, until it holds:

> End the day on purpose. Five minutes, written, out loud, laptop closed, room left.

Everything else in the method is downstream of a day that finishes. The shutdown is not the smallest rule because it is the easiest; it is the smallest because it is the one that makes the other eight possible.

---

# Appendices

## Appendix A — The card

Print this page. Cut along the rule. Put it where you work — not in a drawer, not in a notes app. The card is the book, compressed.

<div class="card-sheet">

**JACARANDA LABS · THE OPERATOR'S CARD** · *The Point of Failure*, first edition

**THE NINE** — 1 shutdown, every day, out loud · 2 one day off, fully off · 3 sleep before midnight; three short nights is an incident · 4 the first ninety minutes are the one outcome · 5 no money numbers Sunday night to Monday · 6 move, outside, no phone · 7 one non-business conversation · 8 the worry window, twenty minutes, pen · 9 no new venture while two are unresolved

**THE BAD DAY** — make it safe (2 min) · shrink the day (10 min) · leave it alone (the rest of it, no catching up)

**THE PAUSE** — disable the press workflow · stop pushing · leave the checkouts alone — or do nothing for a week and let the outbox fill

**THE THREE SENTENCES** — The machine runs; I steer, and steering has hours. · A failure is a hypothesis that was tested. · The business exists so that a person can live.

**IF IT IS MORE THAN TWO WEEKS** — this is not a scheduling problem. A doctor, a counsellor, or Friendship Bench. Tell one person by name.

</div>

## Appendix B — The instruments

Eight sheets, each a form to be filled in by hand. Print them, or copy the headings into a notebook — the format matters less than the repetition. Nothing here needs software, and that is deliberate: an instrument that requires a working laptop is an instrument that fails on the day you need it.

**Sheet B1 — Name the component.** Two columns. *Stops for a day without the business stopping* (six rows) and *cannot stop* (one row, written specifically). Below: "the thing only I can do, in the smallest true form" and a date.

**Sheet B2 — The seven-box week and the installation plan.** Nine rows, one per rule, seven columns for the days. A tick per day. At the bottom, the count. On the reverse, the installation plan: nine rules, nine start dates, starting with the shutdown. Six of nine is information; four of nine for three weeks is a finding.

**Sheet B3 — The shutdown page and the one outcome.** Two fields per night, ruled. *Open loops* (as many lines as needed) · *tomorrow's one outcome* (one line, a state of the world, a verb in it) · *the sentence said out loud* (a checkbox, not a line — the saying is the record).

**Sheet B4 — The incident log.** Fourteen rows: date · hours slept · the day's most consequential decision · would I make it again (yes/no). No commentary column, on purpose. The pattern is the output.

**Sheet B5 — The Monday round.** Five rows, weekly: cash · revenue · pipeline · what the numbers imply (one sentence) · the decision they produce (one, dated). A rule at the top: *no number is read outside this hour.*

**Sheet B6 — The unresolved register.** One row per venture: name · status (growing / steady / stalled / unknown) · what would resolve it · date. A footer line for the count of the last two categories, and a box for the next idea — *after* — with the date it arrived.

**Sheet B7 — The quarter-hour audit.** Four questions, four numeric answers, four quarters: hours worked last week · nights under six hours · non-business conversations · what I did that had no return but that I wanted. Two consecutive quarters moving the wrong way is the finding.

**Sheet B8 — The five-signal check.** Five rows, one minute, weekly: non-work life (shrunk?) · the queue (moving?) · the numbers (read?) · the tone (mine?) · sleep (three nights?). Three ticks in the *wrong* column and the week gets the protocol early.

**Sheet B9 — The worry page.** Four fields: the fear, one sentence · the worst realistic case, and would I survive it · the next physical action, small enough for today · the window closed at (time). The last field is the one that makes it a method rather than a journal.

## Appendix C — The one-page estate audit

Once a year, or before any large decision, answer these twenty questions. Each is scored 0 (no), 1 (partly), 2 (yes). The total is not a grade; it is a list of where to look.

**The business as a machine (0–10)**

1. Can the business run for a week with no input from me?
2. Does every automated act leave a record a stranger could audit?
3. Does anything tell me when a rail has gone quiet, rather than only when it errors?
4. Can I pause everything in under a minute without losing anything?
5. Is there anything I do daily that is not a decision?

**The decisions (0–10)**

6. Do I know which single decision this week matters most?
7. Is that decision scheduled rather than remembered?
8. Have I refused a good idea this month, on purpose?
9. Are fewer than two ventures unresolved?
10. Did I write down what would tell me a decision was wrong, before making it?

**The operator (0–10)**

11. Did I sleep seven hours or more on most nights this month?
12. Did I take a full day off in each of the last four weeks?
13. Did I move my body outside on most days?
14. Did I have a conversation about something other than the business on most days?
15. Have I told one person, by name, how the work is actually going?

**The life (0–10)**

16. Is there something in my week that has no return except that I want it?
17. Do the hours I work fit inside the shape of the day I chose?
18. Is the money a floor I can see, rather than a score I am chasing?
19. If a venture failed tomorrow, would I still be able to rest on Sunday?
20. Is the business arranged so that I can live, rather than the other way round?

**Reading it.** Under 20: the business has a failover problem and the operator has a load problem, and the nine rules are urgent rather than advisable. 20–30: the method is running but one of the three groups is being neglected, and the lowest group tells you which. Over 30: the estate is doing what it was built for, and the work now is to keep it that way through a busy quarter — which is when it is most likely to break.

## Appendix D — Glossary

**Activity** — an exercise in this book that a reader performs once in order to own a part of the method. Not homework.

**Bad day** — a day on which the machine is fine and the operator is not. Handled by a three-step protocol, not by rescue.

**Boundary** — a limit chosen in advance, which holds when intentions fail. Distinguished from a wish, which does not.

**Check** — the question that takes seconds and tells you whether a rule is running. Every rule in Part Two has one.

**Component** — anything in the business that can be absent for a while. The operator is a component with no replica.

**Degenerate form** — the smallest version of a rule that still counts. Scaled-down is not failed.

**Estate** — the shared machinery plus the portfolio of ventures, as distinct from any one venture. The unit of the business, not the org chart.

**Failover** — what happens when a component is absent. Everything in the estate has one except the operator.

**Ghost authority** — confidence in an automated act that no human has verified. Named in the companion volume, *Operatorship*, and the most common way an operator's knowledge falls while their confidence rises.

**Incident** — a short night logged as an event rather than absorbed as a habit. Three consecutive nights under six hours is the threshold.

**Loop** — an unfinished thing the mind holds open. Written down, it becomes a task; held, it remains a threat.

**Mechanism** — the decision or absence of a decision that produced an outcome. The alternative to a verdict about the self.

**Non-negotiables** — the nine rules. Called that because they survive a bad week, which is the only test that matters.

**One outcome** — a state of the world that will be true by lunchtime or will not. Not a task.

**Operator** — the person who owns the consequences of machine work they did not perform. One person, no replica.

**Pause switch** — the written procedure for stopping everything in under a minute. A design feature, and a test of the design.

**Shutdown** — five minutes, written, out loud, laptop closed, room left. The highest-leverage habit in the book.

**Signals** — the five leading indicators of a bad stretch, visible in artefacts rather than feelings.

**Worry window** — twenty minutes with a pen, then closed. Converts a state into a list with an end.

## Appendix E — References and further reading

**On running systems that act without you**

* The companion volume of this book: *Operatorship: What Ate Technopreneurship, and What Replaced It* — the same estate, argued as a form of business rather than a form of self-management.
* *The Mechanism Auditor* — how to review a product that runs without you; the claim ledger, the mechanism map, the evidence trail, and the six failure signatures.
* *The Mechanism Audit* (working paper 2026-04) — the formal version, with the gap classes and the incident tables.
* Garikai, C. (2026). *ContentOps* — a zero-capital field report on grounded generation, silent failure, and fail-loud operations. Jacaranda Labs, Harare.

**On sleep, attention and judgement**

* Walker, M. *Why We Sleep* — the popular account of sleep's role in judgement and emotional regulation; read it as an argument for the rule, not as a clinical reference.
* Kahneman, D. *Thinking, Fast and Slow* — for the mechanism behind "confidently wrong at 4pm".
* Newport, C. *Deep Work* — for the front-loading of attention that Rule 4 depends on; the surrounding productivity culture is not required.

**On one-person businesses and unbounded work**

* Sarasvathy, S. (2001). "Causation and Effectuation." *Academy of Management Review* — what a resource-constrained operator actually does, formalised.
* Baker, T. & Nelson, R. (2005). "Creating Something from Nothing: Resource Construction through Entrepreneurial Bricolage." *ASQ* — the academic account of making a business out of what is to hand.
* Rachleff, A. on the "unbounded surface" of early companies — the phrase is useful even where the context is venture capital.

**On failure, records and mechanism**

* Petroski, H. *To Engineer Is Human* — failure as the engine of design, which is the posture this book asks of the operator.
* Perrow, C. *Normal Accidents* — why complex systems fail in ways their designers did not anticipate; the intellectual ancestor of the operator-as-component argument.
* Reason, J. *Human Error* — the error taxonomy that makes "name the mechanism" specific rather than therapeutic.

**On the boundary between a book and a person**

* Friendship Bench (Zimbabwe) — free, evidence-based lay counselling through primary care clinics and community spaces.
* World Health Organization, *mhGAP* — the primary-care protocols that a general practitioner is likely working from.
* National mental-health lines — the right first call outside Zimbabwe; the number is local, and worth looking up before you need it.

**Notes on the references.** This book is not a clinical text, and none of the clinical material above is a substitute for a clinician. The references to sleep and attention are there to explain why an operational rule works, not to establish a treatment. Where a claim in this book is testable in your own operation within a month, Appendix C is the instrument; where it is not, the claim is an argument, and the argument is the book.

## Appendix F — Acknowledgements

A book about not being alone in a business is written by someone who was, for most of it, alone — and it is only honest to name the people and systems that made the aloneness survivable rather than total.

**The estate built the argument.** Seven ventures, a press rail that has posted through every bad week, a bank that refills itself, a monitor that says plainly when a front door has stopped answering, and an outreach sequence that now stops after three touches instead of three hundred. The machines did not write this book, but they are the specimen, and several of the failures in it are theirs. The first readers of Part Three were the rails.

**The operator's own failure is the evidence.** Every incident described in these pages happened to the author, in this estate, in ordinary operation. That is the only warrant the book claims, and it is the reason the examples are specific enough to be checked — including the ones that make the author look worse than a well-edited case study would.

**The people who noticed.** To the friends and family who asked about sleep rather than about revenue, and who kept asking when the answer was evasive. To the peers who run things of their own and who said, when it was useful, "are you sure" — which is the most valuable sentence available to a person who decides alone. To the readers of the earlier work whose questions about *how* rather than *why* produced the instruments in Appendix B.

**The clinical community in Zimbabwe.** Friendship Bench, for existing, and for building a model that a person with no money and no time can actually reach through a clinic and a community space. A general practitioner who takes a sentence like "I have not slept properly in three weeks" as the beginning of a conversation rather than the end of one. This book is not their work, and it would be irresponsible without them.

**The estate's successor readers.** To anyone who picks this up because a bad day has already happened: the book is designed to be entered from the middle. Part Three first, if that is where you are.

**Errata and correction.** This is a private-operator document published openly, and it will be wrong about something. Corrections, disagreements and better instruments are welcome through the public repository the estate is published in. A rule in this book that turns out to be unkeepable is the most useful correction of all, because it means the rule was a wish wearing a rule's clothes.

## Appendix G — About the author

Courage Garikai runs Jacaranda Labs, a one-person software estate in Harare, Zimbabwe: seven ventures, a press that publishes books like this one, and roughly three hours twenty minutes a week of human attention. He holds a first degree in entrepreneurship, in which he was taught *technopreneurship* — the subject of the companion volume in this series. He writes about what happens when the machinery that makes a small business possible also makes the person running it the only thing in the building that cannot be replaced.

## Appendix H — Colophon and rights

**Type.** Set in Iowan Old Style, Palatino and Georgia for text; the system sans-serif for labels and tables; a monospace for code and figures. No external fonts are loaded and no web font is used: the edition is designed to render identically on a phone, a laptop, an e-reader and a print run.

**Figures.** All twelve figures in this series are hand-drawn SVG — coordinates, rules and type, no charting library and no images — so that they survive A5 print and a small screen without becoming unreadable. They are generated by `tools/make_figures.py` in the public repository, in the same idiom as the covers: cream stock, black rules, one red accent.

**Edition.** First edition, November 2026. HTML and Markdown are published; the Markdown is the source of the HTML and can be copied, diffed or forked.

**Licence.** Text and figures: CC BY 4.0. Attribution to Courage Garikai, Jacaranda Labs, Harare. The instruments in Appendix B may be reproduced and modified without attribution for any use, commercial or not — a form that cannot be copied is not an instrument.

**Canonical location.** `https://jacaranda-labs.pages.dev/read/the-point-of-failure.html`

**A note on the price.** This book costs nothing to read and nothing to copy. It was written by an operator for operators, and the whole argument of it is that the person running the business is more expensive than the business. Charging for the manual would be a poor way to make that point.
