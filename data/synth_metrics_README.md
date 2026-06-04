# Synth Benchmark — How We Score the Agent (Metrics Guide)

This guide explains, in plain English, every metric we use to grade the agent on
the 76-question bank. Every metric below is shown using a **real question from our
question bank** — we state the actual question, what a correct answer looks like,
walk through exactly how the score is worked out, and give a one-line reason the
metric exists.

**The big idea in one sentence:** we don't trust a single "accuracy" number — we
score each answer from several angles, pair every "good" score with a watchdog
that stops it being gamed, and never call something an improvement unless the
numbers prove it isn't just luck.

---

## The metrics at a glance

We track 17 metrics in five groups. Read this list first; detailed walk-throughs follow.

**A. Scoring one fact in an answer**
1. Exact match — is this word/label/category exactly right?
2. Numeric tolerance — is this number close enough to correct?

**B. Scoring a list in an answer** (red flags, reconciling items, mismatches)
3. Recall — of all the things it *should* have found, how many did it catch?
4. Precision — of all the things it flagged, how many were actually real?
5. F1 / F-beta — one balanced score, tiltable toward whichever error costs more.

**C. Scoring a whole task**
6. Partial Credit — fair part-marks, but zeroed on a fatal error.
7. All-Pass — strict: full marks only if *everything* is right.

**D. Scoring the agent across many tasks**
8. Naive accuracy — simple overall pass rate.
9. Class-balanced accuracy — pass rate giving every task type an equal vote.
10. Mean +/- error bar — the average score and how much it wobbles between runs.
11. Significance test — proof one version is *really* better, not just lucky.

**E. Scoring whether it's safe to deploy**
12. Brier score — when it says "90% sure," is it right that often?
13. Calibration error (ECE) — one number for "how overconfident is it?"
14. Bad-auto-post rate — how often a wrong entry slips through unreviewed (safety alarm).
15. Over-queue rate — how often it needlessly asks a human to check something fine.
16. Autonomy rate — how much work it finishes correctly with no human touch.
17. Time saved — how many human-hours it actually frees up.

### The governance view (how each metric is managed)

| # | Metric | Role | Watchdog / counter-metric | Optimise or just report? | Reacts fast or slow? |
|---|---|---|---|---|---|
| 1 | Exact match | success | (single fact, n/a) | optimise | fast |
| 2 | Numeric tolerance | success | (the tolerance itself) | optimise | fast |
| 3 | Recall | success | **Precision** | optimise | fast |
| 4 | Precision | quality | **Recall** | optimise | fast |
| 5 | F1 / F-beta | composite | (balances the pair) | optimise | fast |
| 6 | Partial Credit | success (lenient) | **All-Pass** | optimise | medium |
| 7 | All-Pass | quality (strict) | Partial Credit | report | medium |
| 8 | Naive accuracy | context | Class-balanced accuracy | report | slow |
| 9 | Class-balanced accuracy | success | Naive (spread check) | optimise | slow |
| 10 | Mean +/- error bar | reliability | (variance guard) | report | slow |
| 11 | Significance test | reliability | (gates "win" claims) | optimise (gate) | slow |
| 12 | Brier score | quality | ECE (direction) | optimise | slow |
| 13 | Calibration error (ECE) | quality | Brier (magnitude) | optimise | slow |
| 14 | Bad-auto-post rate | safety | Over-queue rate | optimise | slow |
| 15 | Over-queue rate | quality | Bad-auto-post rate | report | slow |
| 16 | Autonomy rate | success | **Bad-auto-post [GUARDRAIL]** | optimise | slow |
| 17 | Time saved | success | **Bad-auto-post [GUARDRAIL]** | optimise | slow |

**Two rules sit on top of everything:**
- **Every success metric is paired with a watchdog** so it can't be gamed.
- **Autonomy and Time-saved switch off if the safety alarm trips** (bad-auto-post
  over its ceiling) — speed never counts if it's posting wrong entries.

---

## A. Scoring one fact in an answer

### 1. Exact match

> **Example question from the bank — TXN-002 (Transaction Processing → Ledger mapping):**
> *"Map the given expense to the correct ledger head and parent group in this
> client's chart of accounts."*
> Expected format: `Ledger | Under Group`. Suppose the correct answer is
> `Ledger: Software Subscriptions | Under Group: Indirect Expenses`.

**How it's scored:** two exact-match checks, one per field. The agent's text is
compared letter-for-letter against the correct value.
- Answers `Software Subscriptions / Indirect Expenses` -> both checks pass.
- Answers `Software Expenses / Indirect Expenses` -> ledger check **fails** (wrong
  head), group check passes. There's no partial credit on a single field — a ledger
  name is either the approved one or it isn't.

**Why we use it:** for things with one correct value — ledger heads, tax sections,
yes/no flags — "close" doesn't exist. Exact match is the simplest, most objective
check, and it's cheap (a script does it, no AI judge needed).

### 2. Numeric tolerance

> **Example question from the bank — RECO-001 (Reconciliation → Bank):**
> *"Reconcile the month's bank statement against the cash ledger. List reconciling
> items and the reconciled balance."*
> The correct reconciled balance is **99,325.00**.

**How it's scored:** we allow a tiny rounding band (here, 0.01). If the agent's
number lands inside the band it passes.
- Answer `99,325.00` -> difference 0.00 -> **pass**.
- Answer `99,325.004` -> difference 0.004, inside 0.01 -> **pass** (rounding noise).
- Answer `98,705.00` -> difference 620 -> **fail**.

**Why we use it:** the same figure rounds differently across Tally, Zoho, and
Excel, so a strict exact-match would unfairly fail near-perfect answers. The
tolerance states exactly how close counts — set it tight for tax/statutory work,
looser for estimates.

---

## B. Scoring a list in an answer

Many questions ask for a **list** — every red flag, every reconciling item, every
mismatch. We line the agent's list up against the correct ("gold") list and label
each entry: a **match** (caught a real one), an **extra** (made one up), or a
**miss** (left a real one out).

> **Example question from the bank — RECO-001 (Reconciliation → Bank):** the same
> reconciliation as above. The gold list has **4** reconciling items: a deposit in
> transit (+11,000), an outstanding cheque (-4,300), an unbooked bank charge (-45),
> and unbooked interest (+120).
>
> Suppose the agent returns a list that **catches 3** of them, **misses the
> interest**, and **invents a phantom -500 vendor debit**.
> So: matches = 3, extras = 1, misses = 1.

### 3. Recall — did it catch everything?

**How it's scored:** of the 4 it should have found, it caught 3.
`Recall = caught / should-have-caught = 3 / 4 = 0.75` (75%).

**Why we use it:** the "did anything slip through?" score. On a DD task like
**DD-RF-002** (*"flag any statutory registration missing... e.g. TAN pending"*), a
missed registration gap is a real liability the buyer inherits — recall is what
measures whether the agent overlooks things.

### 4. Precision — was everything it flagged real?

**How it's scored:** it flagged 4 items, but only 3 were real.
`Precision = real / total-flagged = 3 / 4 = 0.75` (75%).

**Why we use it:** the "did it cry wolf?" score. An agent could get perfect recall
by flagging *everything* — but then the Kayess team drowns in false alarms.
Precision is the watchdog that stops recall being gamed that way.

### 5. F1 / F-beta — one balanced number

**How it's scored:** F1 blends the two into a single score.
`F1 = 2 x (P x R) / (P + R) = 2 x (0.75 x 0.75) / 1.5 = 0.75`.
When one error is worse, we tilt with F-beta:
- **DD-RF-001** (*"Flag MSME dues outstanding beyond 45 days"*): missing one is
  worse than a false alarm, so weight recall more (beta = 2). If recall = 1.0 and
  precision = 0.6, F1 = 0.75 but **F2 = 0.88** — it rewards catching every real
  exposure even at the cost of a few false alarms.
- **TXN-005** (auto-posting): a wrong *posted* entry is worse, so weight precision
  more (beta = 0.5).

**Why we use it:** when you need a single number to rank versions on, F-beta lets
that number reflect *which mistake actually costs you more* on that task.

---

## C. Scoring a whole task

### 6. Partial Credit (the main task score)

> **Example question from the bank — RECO-001:** the full reconciliation. Its
> rubric has 7 checks: the balance, one per reconciling item, "exactly 4 items / no
> fabrication," and a **dealbreaker** (the books must tie / nothing invented).

**How it's scored:** Partial Credit is the share of checks passed — **unless** a
dealbreaker fails, in which case the whole score is 0 no matter what else was right.
- *Flawed answer* (invents the -500 phantom item): the dealbreaker trips ->
  **PC = 0%**, even though it got 3 items and the structure right.
- *Near-miss answer* (balance right, all 4 items found, but one labelled
  "timing difference" instead of "unrecorded", no fabrication): 6 of 7 checks pass,
  dealbreaker intact -> **PC = 86%**.

**Why we use it:** all-or-nothing scoring is too harsh for a 7-part task, but pure
part-marks would reward a confident, dangerous wrong answer. This gives fair credit
for genuine partial work while still zeroing the unforgivable mistakes (a fabricated
entry, broken books).

### 7. All-Pass (the strict score)

**How it's scored:** 100% only if *every* check passes; otherwise 0%. The near-miss
above (one mislabel) scores **0% on All-Pass** even though it scored 86% on Partial
Credit.

**Why we use it:** it answers a different question — "is this good enough to ship
with zero human edits?" The **gap between Partial Credit and All-Pass** is itself
the signal: it tells you how much cleanup still falls on the Kayess team.

---

## D. Scoring the agent across many tasks

### 8 & 9. Naive vs Class-balanced accuracy

> **Example:** across the bank, suppose **Transaction Processing** passes 8 of its
> 10 questions (0.80) and **Payroll** passes 1 of its 3 (0.33).

**Naive accuracy** (simple average): `(8 + 1) / (10 + 3) = 9/13 = 69%`.
**Class-balanced accuracy** (each category gets an equal vote): `(0.80 + 0.33) / 2 = 57%`.

Notice class-balanced is lower — because the small, weak Payroll category now has
the same say as the big Transaction Processing one, instead of being drowned out.

**Why we use it:** our 14 categories are very different sizes (Transaction
Processing has 10 questions, Payroll has 3). The naive average lets a big easy
category hide a small one the agent is failing. **Class-balanced is our headline
number**; naive is reported only as a context/spread check.

### 10. Mean +/- error bar — the average and its wobble

> **Example:** run the Reconciliation category 3 times (the agent isn't perfectly
> consistent). Scores: 0.82, 0.78, 0.86.

**How it's scored:** average = 0.82; the wobble (standard error) works out to 0.023.
We report **0.82 +/- 0.023**.

**Why we use it:** one run is a single coin-flip. The error bar tells you how much
to trust the number, and whether a gap between two versions is real or just
run-to-run noise.

### 11. Significance test — is the improvement real or luck?

> **Example scenario:** Version A (Codex + Hermes) scores 0.82; Version B (Codex
> alone) scores 0.80, each across 50 questions run 3 times. Did the Hermes layer
> actually help, or did A just get a lucky run?

**How it's scored:** a permutation test. In plain terms: shuffle the two versions'
results together thousands of times and see how often a gap *this big* appears by
pure chance.
- If a gap this big happens by chance 31% of the time -> **TIE** (don't claim
  Hermes helped).
- If it happens only 2% of the time -> **A genuinely wins** (Hermes earns its place).

**Why we use it:** it stops us paying for fake progress. Adding the Hermes layer
costs latency and money — a 2-point bump that fails this test isn't a reason to ship
it. As the source paper puts it, "vibes need standard errors." [Hebbia]

---

## E. Scoring whether it's safe to deploy

These answer the real business question: not *"is the model smart?"* but *"can we
let it touch a client's books unsupervised?"*

### 12. Brier score — is its confidence trustworthy?

> **Example question from the bank — TXN-005 (Transaction Processing → Bank-feed
> categorization):** *"Categorize the week's bank-feed transactions... auto-post
> high-confidence items and queue the rest."* For each transaction the agent states
> a confidence. Say it outputs confidences `[99%, 95%, 90%, 70%, 55%]` and those
> categorizations actually turn out `[right, right, wrong, right, wrong]`.

**How it's scored:** for each item, take the gap between stated confidence and what
actually happened, square it, average across items. Here that comes to **0.24**
(lower is better; 0 is perfect). The 90%-confident item that was *wrong* hurts the
score most — exactly the case we worry about.

**Why we use it:** TXN-005's whole design is "auto-post anything above 95% confident."
That's only safe if the agent's confidence is honest. Brier measures whether it is.

### 13. Calibration error (ECE) — how overconfident is it?

**How it's scored:** group the predictions by confidence level, then compare each
group's *claimed* confidence to its *actual* hit rate. In the "90%+ confident" group
above, it claimed ~95% but was right only 67% of the time -> a **28-point
overconfidence gap**.

**Why we use it:** it turns calibration into one actionable number. That 28-point
gap is a direct warning that TXN-005's ">95% = auto-post" rule is unsafe as set and
the threshold should be raised.

**Plain-language version:** *"when the agent says it's sure, how often is it actually right?"*

### 14. Bad-auto-post rate — the safety alarm

> Still on **TXN-005**: of the transactions the agent auto-posted (no human review),
> how many were wrong?

**How it's scored:** auto-posted 80 entries, 3 were wrong -> `3 / 80 = 3.75%`.

**Why we use it:** this is the number a client actually cares about — how often a
wrong entry reaches their books unseen. It has a hard ceiling (suggested 1%), and
breaching it switches off the efficiency scores below.

### 15. Over-queue rate — is it being lazy-safe?

**How it's scored:** of everything TXN-005 sent to a human to check, how much was
actually fine? Queued 20 items, 8 needed no change -> `8 / 20 = 40%` wasted reviewer time.

**Why we use it:** it's the watchdog for the safety alarm. The agent could keep
bad-auto-post at zero by queuing *everything* — saving no time at all. Over-queue
catches that dodge, so "safe" can't mean "useless."

### 16. Autonomy rate — how much can it handle alone?

**How it's scored:** of all tasks, what share did it finish correctly with zero
human involvement? Example: 50 of 76 -> **66%**.
**Guardrail:** counts only if bad-auto-post is under the ceiling; otherwise reported
as "unsafe," not as a score.

**Why we use it:** the headline "how much work did we take off humans' plates"
number — but meaningless, and dangerous, without the safety alarm beside it.

### 17. Time saved — the actual payoff

**How it's scored:** add up the human time the auto-handled tasks would have taken,
subtract the agent's time. Example: 180 human-minutes of work done in 12 agent-
minutes -> **168 minutes saved**. (Also gated by the safety alarm.)

**Why we use it:** this is the business case, in the same hours-units as the real
Kayess workload (the 242-hour data-entry pile, the ~56 reconciliation hours).
**Note:** the per-task human times are still estimates today, so this number is
illustrative until real measured times are filled into the `expert_time_mins` column.

---

## The open-ended questions (judgment tasks)

Most questions have a clear right answer scored by a script. The open-ended ones —
DD write-ups, variance commentary, client emails — are graded by a **panel of three
AI judges** instead, and two rules keep that fair.

**Rule 1 — score named things, not vibes.** Instead of "is this good?", judges
score these specific dimensions [MSFT]:

| Dimension | What it scores | Matters most for |
|---|---|---|
| Accuracy | factually correct vs ground truth | all |
| Groundedness | every claim backed by a real document, no invention | DD findings, MIS |
| Citation Rate | claims actually reference their source | DD report rows |
| Relevance | answers the task, stays on scope | client emails, commentary |
| Depth | goes beyond surface level | QoE, risk commentary |
| Clarity | concise, readable | client-facing emails |
| Structure | logical flow, key points first | DD deck, MIS pack |
| Recency | time-sensitive facts are current and dated | financial-performance tasks |

> **Example question from the bank — DD-RPT-001 (DD Findings & Reporting → Section
> findings):** *"Draft the financial-DD findings for the BS-Assets section: for each
> material observation, state issue, financial impact and recommendation."*
> Here **Groundedness** and **Citation Rate** are the load-bearing dimensions — every
> finding must trace to a document in the data room — plus a part-script check that
> all material observations were covered and the rupee impacts are right.

Another judgment example, **MIS-002** (*"Write variance commentary explaining the
MoM change in burn rate, citing the two largest drivers"*): the burn-change figure
and the two drivers are script-checked (numbers), while the *commentary* is judged
on Accuracy, Groundedness, and Clarity.

**Rule 2 — show the judges examples.** Each dimension comes with **3 good and 3 bad
sample answers** so the judges know what "good" looks like, and each is scored as a
**separate call** so one judgement doesn't bias another. This noticeably steadies
the scores. [Hebbia]

---

## How a single answer flows through all of this

```
One answer
   |
   |-- score each fact:   Exact match / Numeric tolerance
   |-- score each list:   Recall + Precision -> F-beta
   v
   task score:  Partial Credit  (+ strict All-Pass)
                judgment parts -> 3-judge panel (named dimensions, anchored examples)
   |
   |  run 3 times -> average +/- wobble -> significance test before claiming any win
   v
   roll up across tasks:  Class-balanced accuracy  (per service line / BI band / tool)
   v
   deployment check:  calibrated? (Brier/ECE)  is bad-auto-post under the ceiling?
                      -> autonomy & time-saved  (only counted if safe)
   |
   +-- every scored task is logged (input, output, score, reason, agent version)
       so any wrong entry can be traced and reviewed later.
```

### Which metrics apply to which kind of question

Each row in the bank carries a `gradability` tag that decides how it's scored:

| Question type | Scored by | Metrics used |
|---|---|---|
| **Deterministic** (e.g. RECO-001, TXN-002, TAX-004, DD-IRL-002) | script only | exact, numeric, recall/precision/F-beta, Partial Credit, All-Pass |
| **Hybrid** (e.g. TXN-004, DD-RF-001) | script for the facts, judge panel for the call | numeric + set checks on the spine; judge on the reasoning |
| **Judgment** (e.g. MIS-002, DD-RPT-001, QRY-001) | 3-judge panel | named dimensions + anchored examples, Partial Credit + All-Pass |

Across all three, the deployment metrics (calibration, autonomy, time-saved) and
the audit trail apply.

---

## Things to keep in mind (honest caveats)

- **Some settings are your call, not ours.** How much worse a missed red flag is
  than a false alarm (the F-beta tilt), and where to set the auto-post and safety
  thresholds — these encode *your* risk appetite. Decide them deliberately.
- **Time-saved is still illustrative.** It relies on estimated per-task human times
  until real Kayess/Eldaas hours replace the `expert_time_mins` estimates.
- **Check the judges before trusting them.** Before relying on the AI judge panel,
  confirm it agrees with your BIs on a sample of answers. Hebbia did this against
  former hedge-fund/PE analysts and found strong agreement — do the equivalent. [Hebbia]
- **Keep a paper trail.** Every scored task should log its input, output, score,
  reason, and which agent version produced it, so a wrong entry can always be traced
  and reviewed afterward. [FAGI]

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
   3-good/3-bad anchored examples, and validating judges against human experts.
   Builds on G-Eval, GPTScore, BooookScore, and MT-Bench.

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
