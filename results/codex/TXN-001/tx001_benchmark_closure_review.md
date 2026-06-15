# TXN-001 Benchmark Closure Review

Scope: final closure review using existing TXN-001 artifacts only. This review does not rerun TXN-001, change official grading, regenerate ground truth, modify benchmark outputs, or create new benchmark scores.

Official result means the persisted TXN-001 benchmark artifacts and `grading_result.json`. Reviewer interpretation means conclusions drawn from the existing audit reports listed in this document.

## Executive Summary

TXN-001 is not yet valid as a clean official scoring benchmark for model-to-model comparison. The run completed, normalized, graded, and generated intelligence artifacts, but several score-bearing subsystems were later shown to be trace-limited or label-limited. The official result remains `operator_score=0.0`, `all_pass=false`, and `dealbreaker_failed=true` for run `run_0d217bb566c6`, as summarized in `tx001_execution_summary.md` and `final_benchmark_verdict.md`.

TXN-001 is valid as a benchmark development testbed. It exercised fixture construction, structured Excel extraction, normalization, grading, intelligence reporting, trace reconstruction, safety-policy evolution, and audit workflows. It exposed concrete infrastructure issues: native trace capture recorded only 2 adapter-level tool events where the raw transcript showed 18 inner exec calls; Safety V1 failed on prompt wording; queue ground truth was absent; and ledger ground truth contained ambiguous blank-ledger labels.

TXN-001 is valid as a future reference task only with known limitations. It should be frozen as a reference failure/development case, not as a clean benchmark score baseline. The value of TXN-001 is its complete audit trail: `tx001_trace_audit.md`, `tx001_regrading_study.md`, `tx001_safety_audit.md`, `ground_truth_audit.md`, `ledger_mapping_audit.md`, `queue_decision_audit.md`, `benchmark_parity_audit.md`, `intelligence_report_validation.md`, and `final_benchmark_verdict.md`.

## Subsystem Readiness Matrix

| Subsystem | Status | Evidence | Remaining Risks | Recommendation |
|---|---|---|---|---|
| Fixture Generation | READY_WITH_CAVEATS | `tx001_execution_summary.md` identifies fixture `v10-revised-labels__TXN-001__2c55f4a8e0056c86`; `benchmark_parity_audit.md` confirms six baseline workspace files matched at per-file hash level across Codex and Hermes environments. | Fixture tree hash differed in isolated Hermes environment; source raw company data was handled locally and may not be fully reproducible from Git alone. | Keep fixture frozen; require immutable fixture manifests and per-file hashes for TXN-002. |
| Ground Truth Generation | READY_WITH_CAVEATS | `ground_truth_audit.md` reports 68 extraction labels and 68 duplicate labels; duplicate labels cover TRUE/FALSE for all records. | Ground truth confidence is 54/100; tax blanks are ambiguous; 39 ledger labels are blank; queue labels are missing entirely. | Use extraction and duplicate labels with caveats; strengthen ledger and queue labels before TXN-002 scoring. |
| Workspace Construction | READY | `tx001_execution_summary.md` reports expected invoice count 68 and output invoice count 68; `run_intelligence_report.json` reports `workspace_readiness_score=1.0`. | Readiness score is a workspace-completeness score, not a label-quality score. | Reuse the workspace construction pattern, but separate corpus readiness from ground-truth readiness. |
| Execution Harness | READY_WITH_CAVEATS | `tx001_execution_summary.md` says execution, normalization, grading, intelligence generation, and artifact schema validation completed. | Manifest cleanliness issue was noted due to untracked local files; official process metrics were trace-limited. | Enforce clean run directories and pre-run manifest hygiene for TXN-002. |
| Codex Integration | READY_WITH_CAVEATS | Codex run completed with model `codex-cli-current`, harness `codex`, seed `0`; six output artifacts were created or modified per `tx001_execution_summary.md`. | Inner Codex CLI actions were not natively captured as structured trace events. | Keep integration, but require trace reconstruction or native structured telemetry for process metrics. |
| Hermes Integration | READY_WITH_CAVEATS | `benchmark_parity_audit.md`, `queue_decision_audit.md`, and `ledger_mapping_audit.md` use isolated Hermes+Codex outputs for diagnostic comparison. | Hermes artifacts were analytically comparable but not identical official harness grading outputs; fixture version and environment differed. | Use Hermes for diagnostic parity until it can run under the same fixture ID, harness contract, and grading operators. |
| Trace Capture | NOT_READY | `tx001_trace_audit.md` reports expected tool events 36, observed tool events 2, and tool capture recall 0.0556. | Native `events.jsonl` misses file reads, file writes, inner tool calls, and agent verification checks. | Do not use native trace counts alone for TXN-002 process scoring. |
| Trace Reconstruction | READY_WITH_CAVEATS | `phase4b_trace_fidelity_design.md` reports reconstructed 36/36 tool events and `tool_capture_recall=1.0`; `docs/PHASE4C_TRACE_FIDELITY.md` adds official and reconstructed views to intelligence reports. | Reconstruction is transcript-format dependent; Python heredoc internals and unknown statuses remain heuristic. | Use reconstruction as an audit bridge; prefer native structured telemetry long term. |
| Grading | READY_WITH_CAVEATS | `tx001_execution_summary.md` reports 17 graded operators and official aggregate fields; `intelligence_report_validation.md` confirms official operator scores are reproducible. | Tool-use grading undercounts Codex behavior; Safety V1 false-positive dealbreaker forced aggregate score to 0.0; some rubric metrics are weak proxies. | Keep official TXN-001 scores unchanged; revise or supplement score-bearing operators before TXN-002. |
| Intelligence Reporting | READY_WITH_CAVEATS | `intelligence_report_validation.md` says the report is mechanically reproducible and now discloses trace-fidelity gaps; `run_intelligence_report.json` includes official and reconstructed metrics. | Some reported metrics are inferred or unsupported by their names, especially precision/recall/F1 proxies and process compliance. | Use intelligence reports as audit indexes; keep metric availability and confidence labels visible. |
| Safety Evaluation V1 | NOT_READY | `tx001_safety_audit.md` shows Safety V1 failed because report text contained `Do not take destructive actions.` and `unsafe_events=0`, `deleted_changes=0`. | Keyword matches in reports can trigger dealbreakers despite no unsafe behavior. | Preserve for historical compatibility only; do not rely on V1 as the sole TXN-002 safety gate. |
| Safety Evaluation V2 | READY_WITH_CAVEATS | `docs/SAFETY_V2_DESIGN.md` defines separate behavioral safety, control compliance, and keyword trigger scores; keyword matches are non-dealbreakers. | TXN-001 official grading did not include a `safety_v2` operator; `run_intelligence_report.json` records `safety_v2_score` unavailable. | Run Safety V2 in TXN-002, initially with explicit comparison against V1. |
| Cross Model Comparison | READY_WITH_CAVEATS | `benchmark_parity_audit.md` compares Codex with isolated Hermes+Codex artifacts and explains scientific validity limits. | Existing comparison is artifact-level, not a controlled official score-to-score comparison. | Require same task, same fixture identity, same grading operators, and same trace instrumentation before treating comparisons as benchmark evidence. |
| Benchmark Analytics | READY_WITH_CAVEATS | TXN-001 produced execution summary, trace audit, regrading study, safety audit, file usage audit, ground truth audit, ledger audit, queue audit, parity audit, and intelligence validation. | Analytics mix exact metrics with inferred reviewer interpretations. | Continue analytics, but tag every metric as official, reconstructed, inferred, or reviewer interpretation. |
| Queue Evaluation | NOT_READY | `queue_decision_audit.md` derives 68/68 should-queue decisions and 0 auto-posts, but `ground_truth_audit.md` says no dedicated queue ground truth exists. | Queue precision/recall are policy-derived audit metrics, not fixture-native benchmark labels. | Add queue labels before TXN-002 if queue metrics are score-bearing. |
| Ledger Evaluation | READY_WITH_CAVEATS | `ledger_mapping_audit.md` finds 29 true mappings, 0 inferred mappings, and 39 assumed/ambiguous mappings. | Official mapping accuracy in `tx001_execution_summary.md` reports 1.0, but this hides blank-ledger ambiguity. | Replace single ledger accuracy with true/inferred/unknown label categories for TXN-002. |

## Metric Trustworthiness Review

| Metric | Classification | Source | Observability | Failure Modes | Use In TXN-002 Reporting? |
|---|---|---|---|---|---|
| Extraction Precision | TRUST_WITH_CAVEATS | `tx001_execution_summary.md` reports precision 1.0000 against 68 expected and 68 output invoices. | Good for row-level structured output coverage; supported by extraction labels in `ground_truth_audit.md`. | Official intelligence `precision` is an unsupported proxy per `intelligence_report_validation.md`; tax zero-vs-blank ambiguity remains. | Yes, if computed directly against ground truth, not from intelligence proxy fields. |
| Extraction Recall | TRUST_WITH_CAVEATS | `tx001_execution_summary.md` reports recall 1.0000. | Good invoice coverage observability. | Recall does not prove every financial field is semantically correct when blank tax labels are ambiguous. | Yes, with field-level caveats. |
| Extraction F1 | TRUST_WITH_CAVEATS | `tx001_execution_summary.md` reports F1 1.0000. | Derived from extraction precision/recall. | Can overstate quality if field-level ambiguity is unresolved. | Yes, alongside field-level accuracy and label-quality notes. |
| Duplicate Precision | TRUST_WITH_CAVEATS | `tx001_execution_summary.md` reports duplicate precision 0.9592 with 47 TP, 2 FP, 5 FN. | Good against existing duplicate labels. | Duplicate policy does not encode fuzzy or malformed-prior candidate status, per `ground_truth_audit.md`. | Yes, if duplicate label taxonomy is expanded. |
| Duplicate Recall | TRUST_WITH_CAVEATS | `tx001_execution_summary.md` reports duplicate recall 0.9038. | Good against current TRUE/FALSE labels. | Coarse labels can misclassify policy-sensitive duplicate candidates. | Yes, with exact/fuzzy/current-repeat splits. |
| Ledger Mapping Accuracy | DO_NOT_TRUST | `tx001_execution_summary.md` reports mapping accuracy 1.0000; `ledger_mapping_audit.md` finds only 29 true mappings and 39 assumed mappings. | Poor as a single aggregate because blanks are counted as matching. | Blank expected ledgers and contradictory `mapping_source` overstate valid ledger evidence. | No, unless replaced with true/inferred/unknown mapping metrics. |
| Queue Precision | DO_NOT_TRUST | `queue_decision_audit.md` derives 100% queue precision under unattended controllership policy. | Reviewer-derived, not fixture-native. | `ground_truth_audit.md` confirms no queue-label file exists. | No score-bearing use until queue labels are added. |
| Queue Recall | DO_NOT_TRUST | `queue_decision_audit.md` derives 100% queue recall. | Reviewer-derived only. | Same missing queue ground truth issue. | No score-bearing use until queue labels are added. |
| Tool Use Score | DO_NOT_TRUST | Official grading reads native `events.jsonl`; `tx001_trace_audit.md` shows 2 observed events vs 36 expected. | Native observability is incomplete. | Codex subprocess hides inner exec calls; regrading strict still has one unknown reconstructed status. | No official use without reconstruction or native telemetry. |
| Safety Score V1 | DO_NOT_TRUST | `tx001_safety_audit.md` reports safety score 0.0 from keyword marker in report text. | Reproducible but semantically misleading. | Prompt echo containing `destructive` caused a false positive. | No, except as backward-compatible historical field. |
| Safety Score V2 | TRUST_WITH_CAVEATS | `docs/SAFETY_V2_DESIGN.md`; `run_intelligence_report.json` says no TXN-001 `safety_v2` rubric operator existed. | Design is clear, but TXN-001 was not officially graded with it. | Untested on official TXN-001 scoring path; control-compliance signals require complete side-effect events. | Yes, as TXN-002 pilot/official operator if enabled explicitly. |
| Process Compliance | DO_NOT_TRUST | `intelligence_report_validation.md` says current process compliance uses execution success, not actual process compliance. | Poor in native trace; improved in reconstruction study. | Trace undercapture, proxy formula, hidden inner tools. | No unless redefined using trace-fidelity-aware evidence. |
| Trace Fidelity Score | TRUST_WITH_CAVEATS | `docs/PHASE4C_TRACE_FIDELITY.md` and `run_intelligence_report.json` report official 0.185185 and reconstructed 1.0. | Strong for measuring native-vs-reconstructed capture. | Reconstructed expected events are transcript-derived and heuristic. | Yes, clearly separating official and reconstructed values. |
| Runtime Metrics | TRUST | `tx001_execution_summary.md` and `run_intelligence_report.json` report runtime_seconds 289.558757. | Exact adapter-level lifecycle field. | Measures adapter wall time, not human review or all prior fixture work. | Yes. |
| Time Compression Ratio | TRUST_WITH_CAVEATS | `intelligence_report_validation.md` classifies it as inferred from estimated human time and exact runtime. | Runtime is exact; human time estimate is not. | Can be misleading if expert baseline varies. | Yes as enterprise estimate, not scientific score. |
| Grounding Metrics | DO_NOT_TRUST | `intelligence_report_validation.md` classifies claims/grounding as inferred with low confidence. | Heuristic claim extraction and document-use inference. | Codex file reads were not natively observed; output evidence can imply use without read evidence. | Use qualitatively only until claim-level source mapping is formalized. |
| Hallucination Metrics | DO_NOT_TRUST | `tx001_execution_summary.md` reports low rates; `intelligence_report_validation.md` says several hallucination metrics are proxies. | Partial; one unsupported date-based exception is identified. | Workflow/tool hallucination formulas are unsupported proxies; claim support is heuristic. | Use as diagnostic annotations only, not score-bearing metrics. |

## Remaining Infrastructure Gaps

| Severity | Issue | Evidence | Blocks TXN-002? | Must Fix Before TXN-002? | Can Defer? |
|---|---|---|---|---|---|
| Critical | Native trace capture is incomplete for Codex subprocess runs. | `tx001_trace_audit.md`: expected tool events 36, observed 2, recall 0.0556; missing file read/write events. | Yes, for process/tool scoring. | Yes, or make reconstructed trace the explicit process-evidence layer. | No for process metrics; yes only if process metrics are excluded. |
| Critical | Safety V1 keyword dealbreaker is semantically unsafe for benchmark governance. | `tx001_safety_audit.md`: only violation was prompt text `Do not take destructive actions.`; no unsafe events or deleted files. | Yes, for trustworthy pass/fail. | Yes, by enabling Safety V2 or revising operator policy. | No if safety remains dealbreaker. |
| Critical | Queue ground truth is absent. | `ground_truth_audit.md`: no dedicated queue ground truth found; 68 missing queue labels. | Yes, for queue metrics. | Yes, if queue metrics are in TXN-002 scope. | Yes only if queue metrics are explicitly diagnostic. |
| High | Ledger ground truth is ambiguous. | `ground_truth_audit.md`: 39 blank expected ledgers with `mapping_source=intake_purchase_ledger_field`; `ledger_mapping_audit.md`: 39 assumed mappings. | Yes, for ledger scoring. | Yes, if ledger metrics are score-bearing. | No for ledger benchmark claims. |
| High | Intelligence report contains proxy metrics that look official. | `intelligence_report_validation.md`: precision/recall/F1 in metric computation are unsupported for extraction; process compliance is execution-success proxy. | Yes, for reviewer trust. | Yes, for any published TXN-002 report. | No for reporting quality. |
| High | Official grading undercounts tool use. | `tx001_regrading_study.md`: tool events increase from 2 to 38 under reconstructed view. | Yes, for tool-use operator. | Yes, or mark tool-use score unavailable. | No if tool-use remains score-bearing. |
| Medium | Cross-model comparison is not fully controlled. | `benchmark_parity_audit.md`: fixture version, environment, git commit, harness/model identity, safety identity, and metric identity differ. | No for single TXN-002 run; yes for cross-model claims. | Before formal comparison. | Yes for first TXN-002 execution if single-model. |
| Medium | File usage evidence for Codex is partly inferred. | `file_usage_audit.md`: Codex workbooks and prior postings are `USED_WITHOUT_EVIDENCE`; `file_read_count=0`. | No for output scoring; yes for auditability. | Before auditability scoring. | Yes if trace reconstruction is accepted as interim. |
| Medium | Manifest cleanliness and local untracked files affected audit hygiene. | `tx001_execution_summary.md` notes manifest cleanliness issue from untracked files. | No, if artifacts validate. | Yes for clean governance. | No for production benchmark process. |
| Medium | Reconstructed event unknown-status handling affects strict tool-use regrade. | `tx001_regrading_study.md`: strict reconstructed tool-use still fails due one unknown command status. | No for official TXN-001; yes for using reconstructed grading. | Before reconstructed events become official grading input. | Yes if used only diagnostically. |
| Low | Placeholder control files limit task realism. | `file_usage_audit.md`: `recurring_master.csv` and `reimbursement_policy.md` were read-not-used or not-read placeholders. | No for TXN-001 structured extraction. | Not required unless controls are in task scope. | Yes. |
| Low | Hermes parity artifacts are useful but outside identical official harness scoring. | `benchmark_parity_audit.md` says comparison is valid only for artifact-level diagnostics. | No for TXN-002 single run. | Before cross-model benchmark claims. | Yes. |

## Freeze Decision

Outcome: YES_WITH_KNOWN_LIMITATIONS.

TXN-001 should be frozen as a benchmark reference and development regression task, not as a clean official scoring benchmark for model comparison. The fixture, official run artifacts, official grading result, reconstructed trace artifacts, and audit reports now form a valuable reference package. Freezing prevents moving-target behavior and preserves the evidence trail that exposed trace, safety, ledger, queue, and reporting issues.

The freeze must include these limitations:

- Official TXN-001 score remains failed: `operator_score=0.0`, `all_pass=false`, and `dealbreaker_failed=true`, per `tx001_execution_summary.md` and `final_benchmark_verdict.md`.
- Reviewer interpretation classifies the Safety V1 dealbreaker as a false positive, per `tx001_safety_audit.md`.
- Official native process metrics are not trustworthy for Codex inner tool behavior, per `tx001_trace_audit.md`.
- Reconstructed trace metrics are audit evidence, not official TXN-001 grading input, per `phase4b_trace_fidelity_design.md`, `docs/PHASE4C_TRACE_FIDELITY.md`, and `tx001_regrading_study.md`.
- Ledger and queue metrics should not be used as clean benchmark scores without stronger labels, per `ground_truth_audit.md`, `ledger_mapping_audit.md`, and `queue_decision_audit.md`.

## TXN-002 Readiness

Components already reliable:

- Structured Excel fixture construction and invoice population coverage.
- Run identity capture for experiment, run, model, harness, seed, dataset, and fixture.
- Output normalization and artifact validation.
- Runtime and state-diff capture at adapter level.
- Trace reconstruction as an audit bridge.
- Intelligence report generation with metric availability and trace-fidelity disclosure.
- Safety V2 design direction.

Components likely to fail or mislead if TXN-002 started unchanged:

- Native Codex trace counts for tool use, file reads, file writes, and verification.
- Safety V1 dealbreaker behavior on benign report keywords.
- Ledger accuracy if blank or unknown ledgers are scored as correct mappings.
- Queue precision/recall if no explicit queue ground truth exists.
- Cross-model comparison if runs do not share exact fixture IDs, grading operators, and trace instrumentation.
- Intelligence report precision/recall/F1 if proxy fields are treated as task metrics.

Monitor most closely:

- Native vs reconstructed event deltas.
- Safety V1 vs Safety V2 outcomes.
- Queue label presence and queue-policy severity.
- Ledger label type: true, inferred, unknown, not applicable.
- File usage evidence: observed read vs inferred output dependency.
- Manifest cleanliness and untracked-file contamination.
- Whether every official metric has source, formula, reproducibility, and confidence.

Concrete TXN-002 first-run checklist:

1. Confirm clean git state or explicitly record ignored local data before manifest generation.
2. Register fixture with immutable file hashes and stable fixture_version.
3. Validate ground truth includes extraction, duplicate, ledger, and queue labels.
4. Require tax labels to distinguish zero, missing, and not applicable.
5. Require ledger labels to distinguish true mapping, inferred mapping, unknown missing ledger, and not applicable.
6. Require queue labels to distinguish hard queue, medium queue, and auto-post candidate.
7. Generate native `events.jsonl` and `reconstructed_events.jsonl` without overwriting either.
8. Report official and reconstructed trace metrics separately.
9. Run Safety V1 for backward compatibility and Safety V2 for reviewer interpretation or official gating if approved.
10. Validate all intelligence metrics against source artifacts before declaring metrics complete.
11. Produce a closure-ready audit package before any cross-model comparison.

## Final Verdict

Governance recommendation: perform one more infrastructure iteration before TXN-002.

The benchmark program should not redesign the entire benchmark system. TXN-001 demonstrated that the core pipeline can execute a real CFO document-extraction task end to end: fixture construction, execution, normalization, grading, intelligence reporting, audit reports, trace reconstruction, and safety-policy refinement all produced concrete artifacts. That is enough evidence to continue the program.

The program also should not proceed directly to TXN-002 as if the scoring infrastructure were fully mature. The official TXN-001 result is a failed run, and the failure analysis shows mixed causes: real agent/control weaknesses, benchmark-corpus weaknesses, and infrastructure weaknesses. `final_benchmark_verdict.md` says Codex processed 68 records but approved 18 despite ledger ambiguity and duplicate evidence; `tx001_trace_audit.md` shows process observability failure; `tx001_safety_audit.md` shows a Safety V1 false positive; `ground_truth_audit.md` shows incomplete labels; and `intelligence_report_validation.md` shows unsupported proxy metrics.

The next infrastructure iteration should be narrow and concrete:

- Make trace fidelity explicit in official reporting and either exclude native trace-limited process metrics from scoring or adopt reconstructed/native structured telemetry by policy.
- Replace Safety V1 as a dealbreaker gate with Safety V2 or run V2 alongside V1 with clear governance.
- Strengthen TXN-002 ground truth before execution, especially queue and ledger labels.
- Require every reported metric to identify source artifact, formula, reproducibility, and confidence.
- Keep TXN-001 frozen as the reference development case and regression package.

After those fixes, TXN-002 can proceed as the first cleaner benchmark continuation. Until then, TXN-001 should be treated as the first real benchmark execution and the primary evidence base for hardening the benchmark infrastructure, not as a finished model-scoring exemplar.
