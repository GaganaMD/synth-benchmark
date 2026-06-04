# Synth Benchmark — How We Score the Agent (Metrics Guide)

This guide explains, in plain English, every metric we use to grade the agent on
the 76-question bank. For each one you get: a real example prompt, a step-by-step
walk-through of how the score is worked out, and a one-line reason it's there.

The big idea in one sentence: **we don't trust a single "accuracy" number — we
score each answer from several angles, pair every "good" score with a check that
stops it being gamed, and never call something an improvement unless the numbers
prove it isn't just luck.**

---

## The metrics at a glance

We track 17 metrics, grouped by what they look at. Read this list first; the
detailed walk-throughs follow.

**A. Scoring one fact in an answer**
1. Exact match — is this word/label/category exactly right?
2. Numeric tolerance — is this number close enough to correct?

**B. Scoring a list in an answer (red flags, reconciling items, mismatches)**
3. Recall — of all the things it *should* have found, how many did it catch?
4. Precision — of all the things it flagged, how many were actually real?
5. F1 / F-beta — one balanced score combining the two (and you can tilt it toward whichever error is costlier).

**C. Scoring a whole task**
6. Partial Credit — a fair part-marks score, but zeroed if it makes a fatal error.
7. All-Pass — the strict version: full marks only if *everything* is right.

**D. Scoring the agent across many tasks**
8. Naive accuracy — simple overall pass rate.
9. Class-balanced accuracy — pass rate that gives every task type an equal vote.
10. Mean +/- error bar — the average score and how much it wobbles between runs.
11. Significance test — proof that one version is *really* better, not just lucky.

**E. Scoring whether it's safe to deploy**
12. Brier score — when it says "I'm 90% sure," is it actually right that often?
13. Calibration error (ECE) — same idea, summarised as one "how overconfident is it" number.
14. Bad-auto-post rate — how often a wrong entry slips through unreviewed (the safety alarm).
15. Over-queue rate — how often it needlessly asks a human to check something fine.
16. Autonomy rate — how much work it finishes correctly with no human touch.
17. Time saved — how many human-hours it actually frees up.

**Two rules that sit on top of all of these:**
- **Every "good" metric is paired with a "watchdog" metric** so it can't be gamed.
- **The deployment metrics (autonomy, time saved) are switched off if the safety
  alarm goes off** — speed never counts if it's posting wrong entries.

---

## A. Scoring one fact in an answer

### 1. Exact match

**Example prompt (TXN-003):** *"For this professional-fee bill, what TDS section applies?"*
Correct answer: `194J`.

**How it's scored:** the agent's answer is compared letter-for-letter to the
correct one. Says `194J` -> scores 1 (right). Says `194C` -> scores 0 (wrong).
There's no in-between — a section number is either correct or it isn't.

**Why we use it:** the simplest, most objective check. For things like tax
sections, account names, and yes/no flags, "close" doesn't exist — so we just
check exact correctness.

### 2. Numeric tolerance

**Example prompt (RECO-001):** *"What's the reconciled bank balance?"*
Correct answer: 99,325.00.

**How it's scored:** we allow a tiny wiggle room (here, 1 paisa) for rounding.
If the agent's number is within that band, it passes; if not, it fails.
- Answer 99,325.00 -> difference is 0 -> **pass**.
- Answer 98,705.00 -> difference is 620 -> **fail**.

**Why we use it:** financial figures round differently in different tools, so a
flat "exact match" would unfairly fail near-perfect answers. The tolerance says
exactly how close counts as correct — tight for tax, looser for estimates.

---

## B. Scoring a list in an answer

Many tasks ask for a *list* — every red flag, every reconciling item, every
mismatch. To score a list we line up the agent's items against the correct
("gold") list and label each: a **match** (found a real one), an **extra** (made
one up), or a **miss** (left a real one out).

We'll use one running example for all three metrics:

**Example prompt (RECO-001):** *"List all the reconciling items."*
The correct list has **4** items. The agent returns a list where it **found 3**
real items, **missed 1** (the interest credit), and **invented 1** that doesn't
exist (a phantom vendor debit). So: matches = 3, extras = 1, misses = 1.

### 3. Recall — did it catch everything?

**How it's scored:** of the 4 items it should have found, it caught 3.
`Recall = found / should-have-found = 3 / 4 = 0.75` (75%).

**Why we use it:** this is the "did anything slip through?" score. In due
diligence, a missed red flag can sink a deal — so we need to know how much the
agent overlooks.

### 4. Precision — was everything it flagged real?

**How it's scored:** it flagged 4 items in total, but only 3 were real.
`Precision = real / total-flagged = 3 / 4 = 0.75` (75%).

**Why we use it:** this is the "did it cry wolf?" score. An agent that flags
everything would never miss anything (great recall) but would drown the team in
false alarms (terrible precision). Precision keeps it honest.

### 5. F1 / F-beta — one balanced number

**How it's scored:** F1 blends precision and recall into a single score.
`F1 = 2 x (P x R) / (P + R) = 2 x (0.75 x 0.75) / 1.5 = 0.75`.
When one error is worse than the other, we tilt the blend with F-beta:
- *DD red flags* — missing one is worse, so we weight recall more (beta = 2).
  With recall 1.0 and precision 0.6, F1 = 0.75 but **F2 = 0.88** (forgives the
  false alarms, rewards catching everything).
- *CFO auto-posting* — a wrong posted entry is worse, so we weight precision more (beta = 0.5).

**Why we use it:** sometimes you want a single number to rank on, and F-beta lets
that number reflect *which mistake actually costs you more* in that task.

---

## C. Scoring a whole task

### 6. Partial Credit (the main task score)

**Example prompt (RECO-001):** the full reconciliation — balance + all items.

**How it's scored:** the task has several checks (the balance, each item, "no
fabrications"). Partial Credit is the share of checks passed — **but** if the
agent makes a *fatal* error (a "dealbreaker," like inventing an item or breaking
the books), the whole score drops to 0 no matter what else it got right.
- *Flawed answer:* invents a phantom item -> dealbreaker tripped -> **PC = 0%**,
  even though 3 items were correct.
- *Near-miss answer:* balance right, all 4 items found, just one mislabeled, no
  fatal error -> 6 of 7 checks pass -> **PC = 86%**.

**Why we use it:** all-or-nothing scoring is too harsh for multi-part finance
work, but pure part-marks would reward a confident, dangerous wrong answer. This
gives fair credit for partial work while still punishing the unforgivable mistakes.

### 7. All-Pass (the strict score)

**How it's scored:** 100% only if *every single* check passes; otherwise 0%.
The near-miss above (one mislabel) scores **0% on All-Pass** even though it got
86% on Partial Credit.

**Why we use it:** it answers a different question — "is this good enough to ship
with zero edits?" The gap between Partial Credit and All-Pass tells you how much
human cleanup is still needed.

---

## D. Scoring the agent across many tasks

### 8. Naive accuracy — the simple average

**How it's scored:** just the overall pass rate.
Example: Transaction Processing passes 8 of 10, Payroll passes 1 of 3 ->
`(8 + 1) / (10 + 3) = 9/13 = 69%`.

**Why we use it:** it's the easy headline number — but it's misleading on its own
(see the next one), so we only *report* it, we don't optimise it.

### 9. Class-balanced accuracy — the fair average

**How it's scored:** average the pass rate *per category*, giving each category
equal weight regardless of how many questions it has.
Same example: `(0.80 for TXN + 0.33 for Payroll) / 2 = 57%`.
Notice it's lower than the naive 69% — because the small, weak Payroll category
now gets an equal say instead of being drowned out by the big TXN category.

**Why we use it:** our categories have very different sizes. Without this, a big
easy category could hide a small category the agent is failing. This is our real
headline number.

### 10. Mean +/- error bar — the average and its wobble

**How it's scored:** run the same tasks a few times (the agent isn't perfectly
consistent), then report the average and how much it varied.
Example (3 runs: 0.82, 0.78, 0.86): average = 0.82, wobble (standard error) = 0.023.
So we report **0.82 +/- 0.023**.

**Why we use it:** one run is like flipping a coin once. The error bar tells you
how much to trust the number — and whether a difference between two versions is
real or just run-to-run noise.

### 11. Significance test — is the improvement real or luck?

**Example scenario:** Version A scores 0.82, Version B scores 0.80. Did A really
win, or did it just get a lucky run?

**How it's scored:** we run a permutation test. In plain terms: we shuffle the two
versions' results together thousands of times to see how often a gap *this big*
shows up by pure chance. If a gap this big almost never happens by chance
(probability < 5%), we call it a real win; otherwise we call it a tie.
- gap probability = 31% -> happens by chance often -> **TIE** (don't claim A won).
- gap probability = 2% -> rarely happens by chance -> **A genuinely wins**.

**Why we use it:** this stops us from chasing fake progress. When comparing the
orchestration stack (e.g. Codex vs Codex+Hermes), a 2-point bump that fails this
test is noise, not a reason to add a whole layer. As the source paper puts it,
"vibes need standard errors." [Hebbia]

---

## E. Scoring whether it's safe to deploy

These answer the real business question: *not "is the model smart?" but "can we
let it touch a client's books?"*

### 12. Brier score — is its confidence trustworthy?

**Example prompt (TXN-005):** the agent auto-categorizes transactions and states a
confidence for each, e.g. [99%, 95%, 90%, 70%, 55%]; actual correctness turned out
to be [right, right, wrong, right, wrong].

**How it's scored:** for each item we measure the gap between its stated
confidence and what actually happened, square it, and average. Here that works out
to **0.24** (lower is better; 0 is perfect). The 90%-confident item that was
*wrong* hurts the score the most.

**Why we use it:** our whole auto-post design rests on confidence ("post anything
above 95%"). That's only safe if the agent's confidence is honest — Brier checks it.

### 13. Calibration error (ECE) — how overconfident is it?

**How it's scored:** group predictions by confidence level, then compare each
group's *claimed* confidence to its *actual* hit rate.
Example: in the "90%+ confident" group, it claimed ~95% but was actually right
only 67% of the time -> a **28-point overconfidence gap**.

**Why we use it:** it turns calibration into one actionable number. That 28-point
gap is a direct warning: the ">95% = auto-post" threshold is unsafe as set, and
should be raised.

**Plain-language version:** *"when the agent says it's sure, how often is it actually right?"*

### 14. Bad-auto-post rate — the safety alarm

**How it's scored:** of everything the agent auto-posted (no human review), what
fraction was wrong?
Example: auto-posted 80 entries, 3 were wrong -> `3 / 80 = 3.75%`.

**Why we use it:** this is the number a client actually cares about — how often a
wrong entry reaches their books unseen. It has a hard ceiling (suggested 1%), and
if it's breached, the agent's efficiency scores below are switched off.

### 15. Over-queue rate — is it being lazy-safe?

**How it's scored:** of everything it sent to a human to check, what fraction was
actually fine and didn't need checking?
Example: queued 20 items, 8 were fine -> `8 / 20 = 40%` wasted reviewer time.

**Why we use it:** it's the watchdog for the safety alarm. An agent could keep its
bad-auto-post rate at zero by sending *everything* to humans — which saves no time
at all. This catches that dodge.

### 16. Autonomy rate — how much can it handle alone?

**How it's scored:** of all tasks, what fraction did it finish correctly with zero
human involvement? Example: 50 of 76 -> `66%`.
**Guardrail:** this only counts if the bad-auto-post rate is under the ceiling;
otherwise it's reported as "unsafe," not as a score.

**Why we use it:** it's the headline "how much work did we take off humans' plates"
number — but it's meaningless (and dangerous) without the safety alarm beside it.

### 17. Time saved — the actual payoff

**How it's scored:** add up the human time the auto-handled tasks would have taken,
subtract the agent's time. Example: 180 human-minutes of work done in 12 agent-
minutes -> **168 minutes saved**. (Also gated by the safety alarm.)

**Why we use it:** this is the business case, in the same hours-units as the real
Kayess workload (e.g. the 242-hour data-entry pile). **Note:** the per-task human
times are still estimates today, so this number is illustrative until real
measured times are filled in.

---

## How a single answer flows through all of this

```
One answer
   |
   |-- score each fact:  Exact match / Numeric tolerance
   |-- score each list:  Recall + Precision -> F-beta
   v
   task score:  Partial Credit  (+ strict All-Pass)
   |
   |  run it 3 times -> average +/- wobble -> significance test before claiming a win
   v
   roll up across tasks:  Class-balanced accuracy (per service line / BI band / tool)
   v
   deployment check:  is it calibrated? is bad-auto-post under the ceiling?
                      -> autonomy & time-saved (only if safe)
   |
   +-- and the whole thing is logged for review (who/what/why), so any wrong
       entry can be traced back later.
```

---

## The two judgment-task rules (for the open-ended questions)

Most tasks have a clear right answer. The open-ended ones (DD write-ups, variance
commentary, client emails) are graded by a panel of three AI judges instead of a
script, and two rules keep that fair:

1. **Score named things, not vibes.** Instead of grading "is this good?", judges
   score specific dimensions: Accuracy, Groundedness (is each claim backed by a
   real document?), Citation Rate, Relevance, Depth, Clarity, Structure, Recency.
   For a DD report, Groundedness and Citation Rate matter most. [MSFT]
2. **Show the judge examples.** Each thing being scored comes with 3 good and 3 bad
   sample answers so the judge knows what "good" looks like, and each is scored
   separately so one judgement doesn't bias another. This noticeably steadies the
   scores. [Hebbia]

---

## Things to keep in mind (honest caveats)

- **Some settings are your call, not ours.** How much worse a missed red flag is
  than a false alarm (the F-beta tilt), and where to set the auto-post and safety
  thresholds — these encode *your* risk appetite. Decide them deliberately.
- **Time-saved is still illustrative.** It relies on estimated human times until
  real Kayess/Eldaas hours are filled in.
- **Check the judges before trusting them.** Before relying on the AI judge panel,
  confirm it agrees with your BIs on a sample. Hebbia did this against former
  hedge-fund/PE analysts and found strong agreement — do the equivalent. [Hebbia]
- **Keep a paper trail.** Every scored task should log its input, output, score,
  reason, and which agent version produced it — so a wrong entry can always be
  traced and reviewed afterward. [FAGI]

---

## References

1. **[FAB]** Bigeard, Krishnan, Wu et al. *Finance Agent Benchmark: Benchmarking
   LLMs on Real-world Financial Research Tasks.* Vals AI / Stanford, 2025.
   https://arxiv.org/abs/2508.00828 · leaderboard https://www.vals.ai/benchmarks/fabv2 .
   Basis for Partial Credit, All-Pass, the judge panel, multi-run aggregation, and
   class-balanced accuracy.

2. **[Hebbia]** Skinner, Li, Ramanathan (Hebbia Research & Product). *Who Evaluates
   the Evaluator: Reaching Autonomous Consensus on Agentic Outputs.* 2025.
   Related public benchmark: https://www.hebbia.com/blog/which-model-will-give-me-the-edge .
   Basis for the significance test, scoring each criterion independently, the
   3-good/3-bad examples, and validating judges against human experts. Builds on
   G-Eval, GPTScore, BooookScore, and MT-Bench.

3. **[MSFT]** Microsoft 365 Copilot Blog. *Finance Agent Benchmark: evaluating and
   improving AI for Finance.* May 2026.
   https://techcommunity.microsoft.com/blog/microsoft365copilotblog/finance-agent-benchmark-evaluating-and-improving-ai-for-finance/4522978
   · code https://github.com/microsoft/FinanceBenchmark .
   Basis for the named judgment dimensions and equal-weighting across task areas;
   closest published peer to Synth's CFO (AP/AR) work.

4. **[FAGI]** Future AGI. *Best Fintech AI Evaluation Platforms in 2026.* May 2026.
   https://futureagi.com/blog/best-fintech-ai-evaluation-platforms-2026/ .
   Basis for the audit-trail / paper-trail principle only. (Vendor comparison; the
   US regulations it cites don't apply to Synth's Indian context — only the
   reviewable-record idea is borrowed.)

### Further reading (context)
5. DualEntry. *Accounting AI Benchmark 2026.* https://www.dualentry.com/accounting-ai-benchmark — closest to Synth's bookkeeping domain.
6. *FinGAIA: A Chinese Benchmark for AI Agents in Real-World Financial Domain.* https://arxiv.org/abs/2507.17186 — multi-step agent failure patterns.
