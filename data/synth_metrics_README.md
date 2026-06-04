# Synth Benchmark — Metrics Specification (Final, v2)

This is the finalized draft for scoring spec for the 76-question bank. It defines every
metric with its formula, a worked example grounded in real questions, what it
measures, and why it matters — plus the governance layer that makes the set safe
to optimise against.

**What changed in v2** (from external review of three industry sources):
- **Significance testing** added to the reliability layer — point-gap "wins" must
  now clear a permutation test, not just sit outside the error bars. [Hebbia]
- **Anchored examples** required on every judgment-tier criterion (3 good / 3 bad)
  and scored as independent calls, to improve judge consistency. [Hebbia]
- **Named judgment dimensions** (Accuracy, Citation Rate, Groundedness, Relevance,
  Structure, etc.) adopted as the standard sub-criteria for judgment-tier checks. [MSFT]
- **Audit-trail / provenance** requirement added to governance — a reviewable,
  tamper-evident record per scored task. [FAGI]

Governance principles carried from v1:
- **Counter-metric pairing (BFF test).** Every success metric is paired with the
  metric that stops it being gamed. No success metric is reported or optimised alone.
- **Safety guardrail.** Efficiency metrics are voided whenever the quality
  counter-metric breaches threshold.
- **Acted-on vs Reported.** Each metric is tagged for whether you optimise it or
  merely display it.
- **Leading vs Lagging.** Each metric is tagged for responsiveness.

Metrics apply in four layers — per-check, set-level, task-level, aggregate +
deployment — routed by the `gradability` column.

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
| **Significance test (permutation)** | reliability | (gates point-gap claims) | acted-on (gate) | lagging |
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
its bad-auto-post rate displayed beside it.**

---

## Provenance / audit-trail requirement (governance, not a metric)

Because Synth touches statutory work (GST, TDS, ROC filings) and client books,
every scored task must retain a **reviewable, tamper-evident record**: the input,
the output, the per-check scores, the rubric reason for each score, the model +
orchestration version (e.g. Codex / +Fabric / +Hermes), and any human override.
A second-line reviewer must be able to walk from "wrong entry" back to the exact
input, retrieved document, score, and reason. [FAGI]

This is the *principle* of a reviewable model-risk record; the specific US
regulations cited by the source (SR 11-7, SEC 17a-4, CFPB) do not apply to Synth's
Indian context, but the reviewable-record requirement does.

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
| alpha | significance level (0.05) |

---

## Layer 1 — Per-check metrics (Deterministic tier)

### 1. Exact match  · acted-on · leading
**Measures:** a categorical/string answer equals gold.
`s_i = 1 if predicted == gold else 0`
**Example (TXN-003):** gold TDS section `194J`; answer `194J` -> 1, `194C` -> 0.
**Counter-metric:** none needed — a single binary fact, not gameable.

### 2. Numeric within tolerance · acted-on · leading
**Measures:** a numeric answer is within an allowed band of gold.
`s_i = 1 if |predicted - gold| <= tau else 0`
**Example (RECO-001 balance, tau=0.01):** 99,325.00 -> pass; 98,705.00 (delta=620) -> fail.
**Counter-metric:** the tolerance tau itself guards false precision.

---

## Layer 2 — Set-level metrics (list-valued answers)

Items matched to gold on a key (e.g. amount + side): matched = TP, extra = FP, missed = FN.

### 3 & 4. Precision and Recall · acted-on · leading · **paired with each other**
```
P = TP / (TP + FP)        R = TP / (TP + FN)
```
**Example (RECO-001 flawed):** found 3 of 4 gold items, missed 1, fabricated 1 ->
TP=3, FP=1, FN=1  =>  P = R = 0.75 (matches the grader output).
**Why the pairing is mandatory:** recall alone is gamed by flagging everything;
precision alone by flagging only the one sure thing. Neither is reported alone.

### 5 & 6. F1 / F-beta · acted-on · leading
```
F1    = 2PR / (P + R)
Fbeta = (1 + beta^2) * P * R / (beta^2 * P + R)
```
**Example (DD-RF, recall=1.0, precision=0.6):** F1 = 0.75; F2 = 0.88.
**Why it matters:** beta=2 (recall-weighted) for DD red flags; beta=0.5
(precision-weighted) for CFO auto-posting.

---

## Layer 3 — Task-level scoring

### 7. Dealbreaker-gated Partial Credit · acted-on · paired with All-Pass
```
PC = 0                                   if any dealbreaker check fails
PC = sum(w_i * s_i) / sum(w_i)           otherwise
```
**Example A (RECO-001 flawed):** phantom item -> dealbreaker fails -> PC = 0%.
**Example B (RECO-001 near-miss):** balance right, all 4 items found, one category
mislabeled, dealbreaker intact -> PC = 6/7 = 85.7%.

### 8. All-Pass · reported · paired with Partial Credit
```
AllPass = 1 only if every check passes, else 0
```
**Example (RECO-001 near-miss):** one mislabel -> AllPass = 0 though PC = 85.7%.
The **gap between PC and All-Pass** measures human cleanup remaining.

### Judgment-tier rules (Hybrid + Judgment rows)

Judgment-tier checks are graded by a 3-model LLM jury. Two requirements make them
reliable:

**(a) Named sub-criteria.** Judgment checks use these standard dimensions rather
than a generic "judgment" label [MSFT]:

| Dimension | What it scores | Most relevant to |
|---|---|---|
| Accuracy | factually correct vs ground truth | all |
| Groundedness | supported by referenced sources, no hallucination | DD findings, MIS |
| Citation Rate | claims properly reference their source | DD report rows |
| Relevance | directly answers the task, stays on scope | client emails, commentary |
| Depth | explores beyond surface level | QoE, risk commentary |
| Clarity | concise, readable | client-facing emails |
| Structure | logical flow, key insights prioritised | DD deck, MIS pack |
| Recency | time-sensitive info is current, dated | financial-performance tasks |

For a DD report row (DD-RPT-*), Groundedness and Citation Rate are the load-bearing
dimensions — "is this finding backed by a document in the data room."

**(b) Anchored examples.** Every judgment criterion ships with **3 positive and 3
negative example answers** that anchor what "good" and "bad" look like, and each
criterion is scored as an **independent LLM call** (so scoring one criterion does
not bias another). This materially improves judge consistency. [Hebbia]

---

## Layer 4a — Aggregate + reliability metrics

### 9 & 10. Naive vs Class-balanced accuracy · paired
```
Naive = (1/N) * sum(s_j)
CBA   = (1/K) * sum_over_categories(acc_k)
```
**Example (TXN 8/10=0.80, Payroll 1/3=0.33):** Naive = 0.692; CBA = 0.567.
**Acted-on:** CBA (headline). **Reported:** Naive (spread check). Use per service
line in later parts.

### 11. Multi-run reliability: mean +/- SE AND significance testing · reliability

**Step 1 — mean +/- SE (reported).** Run each setting n times:
```
mean = (1/n) * sum(x_r)
sd   = sqrt( sum((x_r - mean)^2) / (n - 1) )
SE   = sd / sqrt(n)
```
**Example (n=3: 0.82, 0.78, 0.86):** mean = 0.82, sd = 0.04, SE = 0.023.

**Step 2 — significance test (acted-on gate).** Before declaring one config better
than another (e.g. orchestration A vs B, or +Hermes vs not), run a **two-sided
permutation test at alpha = 0.05 over 10,000 iterations** on the pooled
per-question scores. Report **significant win / tie / significant loss**, never a
raw point gap. [Hebbia]

```
observed_diff = mean(A) - mean(B)
repeat 10,000x: shuffle labels A/B across pooled scores, recompute diff
p = fraction of shuffled |diff| >= |observed_diff|
significant if p < alpha
```

**Example.** A scores 0.82, B scores 0.80 across N=50, 3 runs each.
- permutation p = 0.31  ->  **TIE** (the 2-point gap is noise; do NOT claim a win).
- permutation p = 0.02  ->  **significant win for A**.

**Notes:** for larger samples consider Mann-Whitney U (two-sided); when running
many comparisons (models x criteria x questions), consider False Discovery Rate
control (Benjamini-Hochberg) before claiming a proportion of true wins. [Hebbia]

**Why it matters:** this is the rigorous form of "vibes need standard errors" —
it stops the orchestration ladder (Codex / +Fabric / +Hermes) from chasing gains
that are within noise. A 2-point gain that fails the permutation test is not a gain.

---

## Layer 4b — Deployment metrics (Synth-specific)

### 12. Brier score · acted-on · lagging · calibration
```
Brier = (1/N) * sum( (p_i - o_i)^2 )      (0 = perfect, lower better)
```
**Example (TXN-005, p=[.99,.95,.90,.70,.55], o=[1,1,0,1,0]):** Brier = 1.2051/5 = 0.241.
**Counter-metric:** read with ECE — Brier gives magnitude, ECE gives direction.

### 13. Expected Calibration Error (ECE) · acted-on · lagging
```
ECE = sum_over_bins( (N_b / N) * |acc(b) - conf(b)| )
```
**Example (bin [0.90,1.0]: 0.99 correct, 0.95 correct, 0.90 wrong):**
conf = 0.947, acc = 0.667, gap = 0.28 -> overconfident; the >95% auto-post threshold is unsafe as set.
**Plain-language wrapper:** *"when the agent says it's sure, how often is it actually right."*

### 14. Bad-auto-post rate · acted-on · lagging · **the safety counter-metric**
```
BadAutoPost = #{posted AND wrong} / #{posted}
```
**Example:** 80 auto-posted, 3 wrong -> 3.75% (above a 1% ceiling -> autonomy voided).
**Counter-metric:** Over-queue rate.

### 15. Over-queue rate · reported · lagging
```
OverQueue = #{queued AND actually fine} / #{queued}
```
**Example:** 20 queued, 8 were fine -> 40% wasted human review.

### 16. Autonomy rate · acted-on · lagging · [GUARDRAILED]
```
Autonomy = #{no human touch AND correct} / N      (reported only if BadAutoPost <= theta)
```
**Example:** 50/76 = 65.8% — valid only if bad-auto-post <= theta.

### 17. Time saved / ROI · acted-on · lagging · [GUARDRAILED]
```
TimeSaved = sum(expert_time on auto tasks) - sum(agent_time on auto tasks)   (only if BadAutoPost <= theta)
```
**Example:** 180 expert-min - 12 agent-min = 168 min saved (only if safe).
**Caveat:** `expert_time_mins` is placeholder until real Kayess/Eldaas times land.

---

## How the layers compose

```
per-check (exact / numeric)
      |
      +-- set-level: Precision <-> Recall -> F-beta
      v
task: Partial Credit <-> All-Pass     (judgment via 3-model jury, named dims, anchored examples)
      |  x 3 runs -> mean +/- SE -> permutation significance test (win / tie / loss)
      v
category acc -> Class-Balanced Acc   (x service line x BI band x tool)
      v
deployment: Brier <-> ECE | Autonomy [GR] <-> Bad-auto-post <-> Over-queue | Time saved [GR]
      |
      +-- every scored task logged to the provenance / audit trail
```

### Metric-to-tier routing

| Gradability | Per-check | Set-level | Task | Deployment |
|---|---|---|---|---|
| Deterministic | exact, numeric | P <-> R, F-beta | PC + All-Pass (code) | calibration, autonomy[GR], time[GR] |
| Hybrid | exact, numeric (spine) | P <-> R (spine) | PC: spine code, judgment via jury (named dims + anchors) | autonomy[GR], time[GR] |
| Judgment | — | — | PC + All-Pass via 3-model jury (named dims + anchors) | autonomy[GR], time[GR] |

---

## How to use this set (the four-test summary)

- **Actionable:** optimise the *acted-on* metrics; the *reported* ones are context,
  never targets.
- **Responsive:** per-check and set-level metrics are *leading* — run on a small
  dev subset for fast iteration. Deployment metrics are *lagging*; measure over
  real volume (accuracy of the safety signal beats speed of it).
- **BFF / counter-metrics:** every success metric names its pair; the critical one
  is the guardrail (Autonomy/Time void when Bad-auto-post breaches theta).
- **Significance before claims:** never report an orchestration "win" without the
  permutation test. A point gap inside noise is a tie.
- **Judge discipline:** judgment checks use the named dimensions, ship 3-good/3-bad
  anchors, and are scored as independent calls.
- **Clear & comparable:** Brier/ECE ship with the plain-language wrapper; every
  aggregate is comparative.

---

## Caveats

- **Weights and thresholds are business calls.** beta, the severity weights w_i,
  the auto-post confidence cutoff, and theta encode *your* risk tolerance.
- **`expert_time_mins` is placeholder.** Metric 17 is illustrative until real
  measured times replace the estimates.
- **Judge calibration precedes judge use.** Validate the jury against human grades
  (percent agreement / Cohen's kappa) before trusting it on Judgment-tier tasks.
  Hebbia validated their automated scores against former hedge-fund/PE analysts and
  found strong alignment; do the equivalent with your BIs. [Hebbia]

---

## References

1. **[FAB]** Bigeard, Krishnan, Wu, et al. *Finance Agent Benchmark: Benchmarking
   LLMs on Real-world Financial Research Tasks.* Vals AI / Stanford, 2025.
   arXiv:2508.00828 — https://arxiv.org/abs/2508.00828 .
   Live v2 leaderboard & methodology (dealbreaker-gated Partial Credit, All-Pass,
   3-judge jury, 3-run aggregation): https://www.vals.ai/benchmarks/fabv2 .
   Supports: Partial Credit, All-Pass, jury, multi-run aggregation, class-balanced accuracy.

2. **[Hebbia]** Skinner, Li, Ramanathan (Hebbia Research & Product). *Who Evaluates
   the Evaluator: Reaching Autonomous Consensus on Agentic Outputs.* 2025.
   Related public benchmark: https://www.hebbia.com/blog/which-model-will-give-me-the-edge .
   Supports: permutation significance testing, independent per-criterion scoring,
   3-good/3-bad anchored examples, human-expert validation of automated scores.
   Builds on foundational LLM-as-judge work cataloged therein — G-Eval, GPTScore,
   BooookScore, and MT-Bench / Chatbot Arena.

3. **[MSFT]** Microsoft 365 Copilot Blog. *Finance Agent Benchmark: evaluating and
   improving AI for Finance.* May 2026.
   https://techcommunity.microsoft.com/blog/microsoft365copilotblog/finance-agent-benchmark-evaluating-and-improving-ai-for-finance/4522978 .
   Code: https://github.com/microsoft/FinanceBenchmark .
   Supports: named judgment dimensions (Accuracy, Citation Rate, Clarity, Depth,
   Groundedness, Recency, Relevance, Structure), equal-weighted task-area
   composite, LLM-as-judge against rubric assertions, latency-constrained eval,
   MCP tool-parity setup. Closest published peer to Synth's CFO (AP/AR) domain.

4. **[FAGI]** Future AGI. *Best Fintech AI Evaluation Platforms in 2026.* May 2026.
   https://futureagi.com/blog/best-fintech-ai-evaluation-platforms-2026/ .
   Supports: the provenance / audit-trail principle only (reviewable, tamper-evident
   per-decision record with score, reason, model version, and override). Note: this
   is a vendor comparison piece; only the audit-trail principle is adopted, and the
   US-specific regulations it cites do not apply to Synth's Indian context.

### Further domain references (context, not directly cited above)

5. DualEntry. *Accounting AI Benchmark 2026* — bookkeeping/accounting model accuracy.
   https://www.dualentry.com/accounting-ai-benchmark . Closest to Synth's CFO domain.
6. FinGAIA: *A Chinese Benchmark for AI Agents in Real-World Financial Domain.*
   arXiv:2507.17186 — https://arxiv.org/abs/2507.17186 . Multi-step, multi-tool agent
   failure taxonomy.
