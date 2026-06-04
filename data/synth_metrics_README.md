# Synth Benchmark — Metrics Specification (Final)

This is the finalized scoring spec for the 76-question bank. It defines every
metric with its formula, a worked example grounded in real questions, what it
measures, and why it matters — plus the governance layer that makes the set safe
to optimise against:

- **Counter-metric pairing (BFF test).** Every success metric is paired with the
  metric that stops it being gamed. No success metric is reported or optimised alone.
- **Safety guardrail.** A hard rule that voids the efficiency metrics whenever the
  quality counter-metric breaches threshold — speed can never buy itself by
  degrading correctness.
- **Acted-on vs Reported.** Each metric is tagged for whether you *optimise* it or
  merely *display* it, so reported-only numbers never become vanity targets.
- **Leading vs Lagging.** Each metric is tagged for responsiveness, so you know
  which give fast iteration signal and which only confirm outcomes after volume.

Metrics apply in four layers — per-check, set-level, task-level, aggregate +
deployment — routed by the `gradability` column (Deterministic -> per-check +
set-level; Hybrid -> both + judge; Judgment -> jury).

---

## TL;DR governance table

| Metric | Role | Counter-metric | Acted-on / Reported | Leading / Lagging |
|---|---|---|---|---|
| Exact match | success | (per-check, n/a) | acted-on | leading |
| Numeric tolerance | success | (per-check, n/a) | acted-on | leading |
| Precision | quality | **Recall** | acted-on | leading |
| Recall | success | **Precision** | acted-on | leading |
| F1 / F-beta | composite | (balances the pair) | acted-on | leading |
| Partial Credit | success (lenient) | **All-Pass** | acted-on | mixed |
| All-Pass | quality (strict) | Partial Credit | reported | mixed |
| Naive accuracy | context | Class-balanced accuracy | reported | lagging |
| Class-balanced accuracy | success | Naive (spread check) | acted-on | lagging |
| Mean +/- SE | reliability | (variance guard) | reported | lagging |
| Brier score | quality | ECE (direction) | acted-on | lagging |
| ECE | quality | Brier (magnitude) | acted-on | lagging |
| **Autonomy rate** | success | **Bad-auto-post rate** [GUARDRAIL] | acted-on | lagging |
| **Time saved** | success | **Bad-auto-post rate** [GUARDRAIL] | acted-on | lagging |
| Bad-auto-post rate | quality (safety) | Over-queue rate | acted-on | lagging |
| Over-queue rate | quality | Bad-auto-post rate | reported | lagging |

[GUARDRAIL] = governed by the safety guardrail below.

---

## The safety guardrail (non-negotiable)

The efficiency metrics — **Autonomy rate** and **Time saved** — are maximised by
auto-posting everything and queuing nothing, which silently pushes wrong entries
into client books. To prevent this, they are **conditional metrics**:

```
Autonomy* = Autonomy rate      if BadAutoPost <= theta
          = void ("unsafe")    if BadAutoPost >  theta
```

with `theta` a hard ceiling (suggested start: theta = 1%). The same gate applies
to Time saved.

**Rule: neither efficiency metric is ever reported, quoted, or optimised without
its bad-auto-post rate displayed beside it.** Speed that breaches the quality
ceiling does not count as speed.

---

## Notation

| Symbol | Meaning |
|---|---|
| TP, FP, FN | true / false positives, false negatives (set matching) |
| N | items / predictions / tasks in scope |
| K | categories (K = 14) |
| w_i | severity weight of check i |
| s_i in {0,1} | pass/fail of check i |
| p_i in [0,1] | stated confidence on item i |
| o_i in {0,1} | actual correctness of item i |
| theta | bad-auto-post ceiling (guardrail threshold) |

---

## Layer 1 — Per-check metrics (Deterministic tier)

### 1. Exact match  · acted-on · leading
**Measures:** a categorical/string answer equals gold.
`s_i = 1 if predicted == gold else 0`
**Example (TXN-003):** gold TDS section `194J`; answer `194J` -> 1, `194C` -> 0.
**Counter-metric:** none needed — a single binary fact, not gameable.
**Why it matters:** cheapest, least ambiguous check; covers sections, heads, flags.

### 2. Numeric within tolerance · acted-on · leading
**Measures:** a numeric answer is within an allowed band of gold.
`s_i = 1 if |predicted - gold| <= tau else 0`
**Example (RECO-001 balance, tau=0.01):** 99,325.00 -> pass; 98,705.00 (delta=620) -> fail.
**Counter-metric:** the tolerance tau itself guards false precision — tight for tax, looser for estimates.
**Why it matters:** encodes "how close is correct" as a rule, not a whim.

---

## Layer 2 — Set-level metrics (list-valued answers)

Items matched to gold on a key (e.g. amount + side): matched = TP, extra = FP, missed = FN.

### 3 & 4. Precision and Recall · acted-on · leading · **paired with each other**
```
P = TP / (TP + FP)        R = TP / (TP + FN)
```
**Example (RECO-001 flawed):** found 3 of 4 gold items, missed 1, fabricated 1 ->
TP=3, FP=1, FN=1  =>  P = R = 0.75 (matches the grader output).
**Why the pairing is mandatory:** recall alone is gamed by flagging everything
(perfect recall, terrible precision); precision alone is gamed by flagging only
the one sure thing. **Neither is ever reported without the other.** Recall catches
misses; precision catches fabrications.

### 5 & 6. F1 / F-beta · acted-on · leading
```
F1    = 2PR / (P + R)
Fbeta = (1 + beta^2) * P * R / (beta^2 * P + R)
```
**Example (DD-RF, recall=1.0, precision=0.6):** F1 = 0.75;
recall-weighted F2 = 5*0.6*1.0 / (4*0.6 + 1.0) = 0.88.
**Role:** F-beta is the single number that resolves the precision/recall pair, with
beta encoding which error is worse.
**Why it matters:** beta=2 (recall-weighted) for DD red flags — a missed flag can
sink a deal; beta=0.5 (precision-weighted) for CFO auto-posting — a wrong posted
entry is the expensive error.

---

## Layer 3 — Task-level scoring

### 7. Dealbreaker-gated Partial Credit · acted-on · paired with All-Pass
```
PC = 0                                   if any dealbreaker check fails
PC = sum(w_i * s_i) / sum(w_i)           otherwise
```
**Example A (RECO-001 flawed):** phantom item -> `contradiction` dealbreaker fails
-> PC = 0% despite 3 correct items.
**Example B (RECO-001 near-miss):** balance right, all 4 items found, one category
mislabeled, dealbreaker intact -> PC = 6/7 = 85.7%.
**Counter-metric:** All-Pass — PC is the lenient view, read against the strict view.
**Why it matters:** rewards partial work but zeroes confidently-wrong answers.

### 8. All-Pass · reported · paired with Partial Credit
```
AllPass = 1 only if every check passes, else 0
```
**Example (RECO-001 near-miss):** one mislabel -> AllPass = 0 though PC = 85.7%.
**Role:** the strict counter to PC. The **gap between PC and All-Pass** measures how
much human cleanup remains.
**Why reported-only:** optimising All-Pass directly drives over-conservatism;
optimise PC, watch All-Pass.

---

## Layer 4a — Aggregate metrics

### 9 & 10. Naive vs Class-balanced accuracy · paired
```
Naive = (1/N) * sum(s_j)
CBA   = (1/K) * sum_over_categories(acc_k)
```
**Example (TXN 8/10=0.80, Payroll 1/3=0.33):** Naive = 9/13 = 0.692;
CBA = (0.80 + 0.33)/2 = 0.567.
**Role:** Naive is the context/counter number — a big CBA-vs-Naive gap warns that a
few large categories are masking weak small ones.
**Acted-on:** CBA (headline). **Reported:** Naive (spread check).
**Why it matters:** category counts are uneven (TXN 10, Payroll 3); CBA gives each
category an equal vote. Use per service line in later parts.

### 11. Multi-run mean +/- standard error · reported · reliability
```
mean = (1/n) * sum(x_r)
sd   = sqrt( sum((x_r - mean)^2) / (n - 1) )
SE   = sd / sqrt(n)
```
**Example (n=3: 0.82, 0.78, 0.86):** mean = 0.82, sd = 0.04, SE = 0.023 ->
report **0.82 +/- 0.023**.
**Role:** the variance guard on every other metric — a 2-point orchestration gap
inside the error bars is noise.
**Why it matters:** judgment-tier scores vary run to run; never compare point
estimates without the bars.

---

## Layer 4b — Deployment metrics (Synth-specific)

### 12. Brier score · acted-on · lagging · calibration
```
Brier = (1/N) * sum( (p_i - o_i)^2 )      (0 = perfect, lower better)
```
**Example (TXN-005, p=[.99,.95,.90,.70,.55], o=[1,1,0,1,0]):** Brier = 1.2051/5 = 0.241.
**Counter-metric:** read with ECE — Brier gives magnitude, ECE gives direction.
**Why it matters:** precondition for the >95% auto-post rule to be safe.

### 13. Expected Calibration Error (ECE) · acted-on · lagging
```
ECE = sum_over_bins( (N_b / N) * |acc(b) - conf(b)| )
```
**Example (bin [0.90,1.0]: 0.99 correct, 0.95 correct, 0.90 wrong):**
conf = 0.947, acc = 0.667, gap = 0.28 -> overconfident; the >95% threshold is unsafe as set.
**Plain-language wrapper (for non-technical stakeholders):** *"when the agent says
it's sure, how often is it actually right."*
**Why it matters:** tells you exactly where to set the auto-post threshold.

### 14. Bad-auto-post rate · acted-on · lagging · **the safety counter-metric**
```
BadAutoPost = #{posted AND wrong} / #{posted}
```
**Example:** 80 auto-posted, 3 wrong -> 3/80 = 3.75% (above a 1% ceiling -> autonomy
voided by the guardrail).
**Counter-metric:** Over-queue rate — stops the agent dodging this by queuing everything.
**Why it matters:** the number a client actually cares about; it gates autonomy and
time-saved via the guardrail.

### 15. Over-queue rate · reported · lagging
```
OverQueue = #{queued AND actually fine} / #{queued}
```
**Example:** 20 queued, 8 were fine -> 8/20 = 40% wasted human review.
**Role:** the counter to bad-auto-post — together they catch both unsafe
over-automation and useless over-caution.
**Why it matters:** an agent with 0% bad-auto-post but 90% over-queue saves no human
time; this keeps the safety push honest.

### 16. Autonomy rate · acted-on · lagging · [GUARDRAILED]
```
Autonomy = #{no human touch AND correct} / N      (reported only if BadAutoPost <= theta)
```
**Example:** 50/76 = 65.8% — **valid only if** bad-auto-post <= theta; else reported as unsafe.
**Why it matters:** the headline deployment number, meaningless without its gate.

### 17. Time saved / ROI · acted-on · lagging · [GUARDRAILED]
```
TimeSaved = sum(expert_time on auto tasks) - sum(agent_time on auto tasks)   (counted only if BadAutoPost <= theta)
```
**Example:** 180 expert-min - 12 agent-min = **168 min saved** (only if safe).
**Caveat:** `expert_time_mins` is placeholder until real Kayess/Eldaas times land.
**Why it matters:** the business case, in the same units as the 242.78 hours.

---

## How the layers compose

```
per-check (exact / numeric)
      |
      +-- set-level: Precision <-> Recall -> F-beta
      v
task: Partial Credit <-> All-Pass        (gap = cleanup remaining)
      |  x 3 runs -> mean +/- SE
      v
category acc -> Class-Balanced Acc   (x service line x BI band x tool)
      v
deployment: Brier <-> ECE | Autonomy [GR] <-> Bad-auto-post <-> Over-queue | Time saved [GR]
```

### Metric-to-tier routing

| Gradability | Per-check | Set-level | Task | Deployment |
|---|---|---|---|---|
| Deterministic | exact, numeric | P <-> R, F-beta | PC + All-Pass (code) | calibration, autonomy[GR], time[GR] |
| Hybrid | exact, numeric (spine) | P <-> R (spine) | PC: spine code, judgment via jury | autonomy[GR], time[GR] |
| Judgment | — | — | PC + All-Pass via 3-model jury | autonomy[GR], time[GR] |

---

## How to use this set (the four-test summary)

- **Actionable:** optimise the *acted-on* metrics; the *reported* ones (All-Pass,
  Naive accuracy, Over-queue, Mean+/-SE) are context, never targets — this keeps
  them from becoming vanity numbers.
- **Responsive:** per-check and set-level metrics are *leading* — run them on a
  small dev subset for fast iteration. Deployment metrics are *lagging* by nature;
  do not wait on them to iterate, but measure them carefully over real volume
  (accuracy of the safety signal beats speed of it).
- **BFF / counter-metrics:** every success metric names its pair. The critical one
  is the guardrail: **Autonomy and Time-saved are void when Bad-auto-post breaches theta.**
- **Clear & comparable:** Brier/ECE ship with the plain-language wrapper for
  non-technical readers; every aggregate is comparative (over time, across the
  three axes, across the orchestration ladder).

---

## Caveats

- **Weights and thresholds are business calls.** beta, the severity weights w_i,
  the auto-post confidence cutoff, and theta encode *your* risk tolerance — set
  them explicitly, do not default to equal weight.
- **`expert_time_mins` is placeholder.** Metric 17 is illustrative until real
  measured times replace the estimates.
- **Judge calibration precedes judge use.** Validate the jury against human grades
  (percent agreement / Cohen's kappa) before trusting it on Judgment-tier tasks.
