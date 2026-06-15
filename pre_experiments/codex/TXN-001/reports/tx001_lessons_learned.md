# TXN-001 Lessons Learned for TXN-002 Benchmark Engineering

Scope: benchmark-engineering lessons from existing TXN-001 artifacts only. This is not a task-performance report and does not rerun or reprocess TXN-001.

Evidence base:

- runs/codex/TXN-001/seed-0/grading_result.json
- runs/codex/TXN-001/seed-0/run_intelligence_report.md
- runs/codex/TXN-001/seed-0/results/*.csv and summary.json
- experiments/hermes_codex/TXN-001/normalized_outputs/*.csv and final_summary.md/json
- experiments/hermes_codex/TXN-001/intelligence_reports/txn001_hermes_decision_audit.md
- experiments/hermes_codex/TXN-001/intelligence_reports/txn001_queue_counterfactual_analysis.md
- experiments/hermes_codex/TXN-001/intelligence_reports/tx001_codex_vs_hermes_comparison.md
- experiments/hermes_codex/TXN-001/intelligence_reports/tx001_controllership_precision_study.md
- results/codex/TXN-001/final_benchmark_verdict.md

## Executive benchmark-engineering takeaway

TXN-001 was useful because it exposed the gap between artifact generation and controllership-grade benchmark evaluation. Codex could produce plausible finance outputs and reconcile the 68-record population, while the harness still scored the run as a dealbreaker failure. Hermes could produce safer, more auditable queue behavior, while also demonstrating that the fixture and grader need more explicit policy definitions to separate hard queues from analyst-resolvable queues.

The main TXN-002 design requirement is to make the benchmark row-level, policy-explicit, trace-observable, and safety-decomposed.

## 1. Benchmark design flaws discovered

1. The fixture did not encode enough policy distinctions.

TXN-001 required extraction, duplicate handling, ledger mapping, GST/TDS judgment, and queue decisions, but it did not sufficiently distinguish:

- exact duplicate vs fuzzy duplicate candidate;
- hard queue vs medium analyst-resolvable queue;
- missing ledger as hard blocker vs medium blocker;
- no TDS evidence as warning vs blocker;
- human analyst posting vs unattended auto-posting.

2. The benchmark rewarded or penalized final outcomes without a clean intermediate decision contract.

Codex emitted approved postings, duplicates, and exceptions. Hermes emitted extraction, duplicate, ledger, and exception reports. These are not the same artifact contract. TXN-002 should specify the exact row-level outputs expected from every agent.

3. Ground truth needs to cover decisions, not just extraction.

TXN-001 had enough data to create post-hoc ground truth for extraction and duplicates, but the intended ground truth for ledger decisions, queue severity, and auto-post eligibility was not explicit enough.

4. The fixture allowed plausible but divergent policies.

Codex used a broader duplicate heuristic for malformed prior invoice numbers. Hermes emphasized exact invoice-number evidence. Both behaviors are explainable. TXN-002 should state which policy is correct.

5. The task mixed operational completion and controllership safety.

A model can reconcile 68 rows and still be unsafe for posting. TXN-002 should score operational completeness separately from posting safety.

## 2. Grading flaws discovered

1. Numeric grading was not reliably row-level.

The official report showed numeric failures with `actual=None, expected=None`. This suggests the grader did not evaluate numeric values from the CSV detail rows where the invoice data existed.

2. Presence-style exact checks passed too easily.

Several exact checks passed because expected values were absent and the exact operator treated the check as a presence check. This can inflate extraction quality.

3. The official operator_score collapsed nuance to zero.

The official score was `operator_score: 0.0`, `all_pass: false`, `dealbreaker_failed: true`, even though 10 of 17 criteria passed and the run produced useful artifacts. Dealbreakers are appropriate, but the scorecard should still expose partial dimensions.

4. Set-match failure lacked enough row-level diagnostics.

The grader reported set precision/recall mismatch, but the useful benchmark question is which invoices were misclassified, omitted, duplicated, or assigned the wrong decision.

5. Grading did not cleanly distinguish policy disagreements from reasoning errors.

For duplicate detection and queue behavior, the grader should separate:

- policy-compliant hard failure;
- defensible alternative policy;
- missed evidence;
- unsupported inference.

## 3. Trace fidelity flaws discovered

1. Subprocess opacity hid actual work.

The run intelligence report showed `tool_call_count: 1`, `file_read_count: 0`, `workspace_file_recall: 0.0`, and all workspace files as never examined, even though Codex outputs referenced those files. The harness observed a subprocess boundary, not the internal agent workflow.

2. File-write telemetry was incomplete.

The benchmark saw final outputs, but trace-level file writes were not reconstructed as granular events.

3. Audit-trail reconstruction attached evidence to the subprocess event rather than actual reads/transforms.

This makes source provenance weaker than the final CSVs imply.

4. Trace scores can become misleading.

`files_never_examined` may reflect instrumentation gaps rather than literal non-use. TXN-002 should distinguish unobserved file access from confirmed non-access.

## 4. Safety heuristic flaws discovered

1. Safety failure was not decomposed into finance-control categories.

The official safety failure said safety violation markers were detected, but a CFO benchmark needs categories such as duplicate posted, missing ledger posted, source conflict posted, unsupported TDS fabricated, or destructive write.

2. Missing ledger handling was underspecified.

Codex approved blank-ledger records; Hermes queued them. The benchmark needs an explicit rule for whether blank ledger is a hard blocker, medium blocker, or allowed with fallback evidence.

3. Duplicate policy was underspecified.

Exact invoice-number duplicates should likely be hard blockers. Fuzzy GSTIN/date/value matches against malformed prior postings should be duplicate candidates requiring review unless the fixture states otherwise.

4. Queue conservatism was not scored separately from false-post risk.

Hermes queued all 68. That can look inefficient, but the controllership precision study shows 52 hard queues and 16 medium queues with zero clear auto-post candidates using existing Hermes outputs alone.

5. TDS absence was not policy-defined.

No TDS rule or amount was available. A good benchmark should define whether the model must queue, warn, or ignore TDS when data is absent.

## 5. Codex behavioral weaknesses

1. Codex optimized for operational throughput over posting certainty.

It approved 18 records even though ledger evidence was weak or blank.

2. Codex did not consistently surface ledger ambiguity.

Blank Purchase ledger was not always converted into an exception or review queue.

3. Codex duplicate detection was inconsistent.

It used broader duplicate heuristics for some malformed-prior cases while missing exact-prior-invoice duplicate evidence surfaced by Hermes for several approved or nonduplicate-classified records.

4. Codex outputs were less audit-friendly.

They were useful, but lacked the same explicit separation of extraction, duplicate evidence, ledger rationale, and exception reasoning found in Hermes normalized outputs.

5. Codex traceability was weak under the harness.

Whether due to subprocess opacity or actual behavior, the recorded trace did not prove file discovery and source-read compliance.

## 6. Hermes behavioral weaknesses

1. Hermes was very conservative.

It queued all 68 records. That is safe for unattended automation but may overstate queue workload relative to a human analyst workflow.

2. Hermes did not elevate medium queue vs hard queue in the original normalized outputs.

The distinction was added by later audits. TXN-002 should require this distinction in the primary output contract.

3. Hermes ledger inference was cautious but limited.

It did not infer ledgers for blank-ledger records even where a human analyst might select a reasonable ledger from the chart of accounts.

4. Hermes exception volume was high.

Logging every queued record as an exception is audit-safe, but TXN-002 should require severity tiers so exceptions are operationally actionable.

5. Hermes did not produce empirical auto-post precision because it posted nothing.

This makes safety high but limits measurement of positive posting capability.

## 7. Recommendations for TXN-002 fixture design

1. Include explicit ground-truth files for every decision layer.

Required ground truth:

- extraction rows;
- duplicate classification;
- ledger mapping;
- GST treatment;
- TDS treatment or explicit TDS-not-applicable flags;
- queue severity;
- auto-post eligibility;
- exception category.

2. Add policy labels to the fixture.

Each invoice should have a target class such as:

- hard_queue_exact_duplicate;
- hard_queue_value_conflict;
- medium_queue_missing_ledger;
- auto_post_validated_ledger;
- review_fuzzy_duplicate_candidate;
- warning_only_tds_absent.

3. Include ledger-evidence variation.

TXN-002 should contain examples where ledger can be inferred from:

- source ledger field;
- chart of accounts exact match;
- prior postings with nonblank historical ledger;
- recurring master;
- vendor policy;
- no reliable evidence.

4. Include duplicate-evidence variation.

The fixture should separate:

- exact prior invoice number;
- same GSTIN + invoice number;
- same invoice number but different GSTIN;
- malformed prior invoice number with amount/date match;
- repeated current-intake invoice;
- no duplicate.

5. Include TDS policy data.

If TDS treatment is expected, provide a machine-readable policy table with thresholds, vendor/service categories, and expected treatment.

6. Include intentional conflicts.

Add known source-value conflicts, date conflicts, GST component conflicts, and ledger conflicts with expected resolution behavior.

7. Preserve source provenance.

Every source row should have stable source_file, source_sheet, source_row, and fixture-row ID fields to support exact joins.

## 8. Recommendations for TXN-002 grading design

1. Grade row-level artifacts directly.

Do not rely only on canonical_output.json prose. Grade the required CSV/JSON reports row by row.

2. Separate score dimensions.

Recommended score families:

- extraction accuracy;
- duplicate detection precision/recall;
- ledger mapping accuracy;
- queue severity accuracy;
- auto-post precision;
- exception completeness;
- trace fidelity;
- safety.

3. Require severity-aware queue metrics.

Report:

- hard queue precision/recall;
- medium queue precision/recall;
- auto-post candidate precision;
- false-post rate;
- false-queue rate;
- critical false-post count.

4. Add finance-language safety dealbreakers.

Examples:

- exact duplicate auto-posted;
- missing ledger auto-posted when policy forbids it;
- source value/tax conflict auto-posted;
- unsupported TDS amount fabricated;
- fixture/source file modified;
- required source document silently skipped.

5. Instrument subprocess agents.

For Codex-like agents, require one of:

- internal file-access manifest emitted by the agent;
- wrapper-level filesystem tracing;
- structured event logging from the subprocess;
- mandatory source inventory and hash report.

6. Make absent expected values fail safely.

Exact and numeric operators should not pass because expected values are absent. Missing expected values should be a fixture/grader error, not an agent pass.

7. Produce both official and diagnostic scores.

Keep dealbreaker scoring, but also expose diagnostic partial credit so benchmark engineers can separate model failures from harness failures.

8. Require evidence fields in every row.

Each output row should include:

- source provenance;
- duplicate evidence;
- ledger evidence;
- exception reason;
- confidence;
- minimum evidence needed to clear queue;
- policy rule ID.

## Final recommendation

Before TXN-002, freeze a single row-level artifact contract and grading schema. The next benchmark should not ask models merely to produce finance outputs; it should measure whether each invoice-level decision is policy-compliant, evidence-grounded, trace-observable, and safe under unattended controllership automation.
