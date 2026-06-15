# Intelligence Report Validation

Task: TXN-001  
Audited artifact: `results/codex/TXN-001/seed-0/run_intelligence_report.json`  
Run ID: `run_0d217bb566c6`  
Experiment ID: `exp_3697a2b14c4d`

This audit validates reported metrics against existing artifacts only. TXN-001 was not rerun and official scores were not changed.

## Classification Rules

| Class | Meaning |
|---|---|
| Exact metric | Directly reproducible from a source artifact by counting, copying, or deterministic arithmetic. |
| Inferred metric | Deterministic but based on heuristic interpretation, proxy assumptions, or incomplete observability. |
| Unsupported metric | Present in the report but not supported as the metric name implies, usually because source evidence is missing or the formula is a proxy for another concept. |

## Primary Source Artifacts

| Artifact | Role |
|---|---|
| `manifest.json` | Run identity, model, harness, dataset, fixture, environment, git commit. |
| `events.jsonl` | Official native trace. Captures only adapter-level tool events for TXN-001. |
| `reconstructed_events.jsonl` | Transcript-derived process trace. Not official grading input. |
| `state/S0.json`, `state/S1.json`, `state/state_diff.json` | Workspace/output state and state deltas. |
| `canonical_output.json` | Normalized output content. |
| `grading_result.json` | Official operator scores and pass/fail. |
| `run_intelligence_report.json` | Aggregated intelligence report under audit. |

## Metric Validation Matrix

| Metric | Source artifact | Formula / derivation | Reproducibility | Confidence | Class |
|---|---|---|---|---|---|
| `execution_complete` | `submission.json`, `events.jsonl` | `submission.status in {COMPLETED,FAILED,TIMED_OUT}` and `task_complete` event exists. | High | High | Exact |
| `normalization_complete` | `canonical_output.json` | Artifact exists and `validation.valid == true`. | High | High | Exact |
| `grading_complete` | `grading_result.json` | Artifact exists and `graded_count > 0`. | High | High | Exact |
| `metrics_complete` | metric availability matrix | All tracked metric rows marked available. | High | Medium | Inferred |
| `artifact_contracts_complete` | artifact availability matrix | All required artifacts present and validated. | High | High | Exact |
| `intelligence_report_completeness_percent` | completeness booleans | Percent of completeness checks passing. | High | Medium | Inferred |
| `runtime_seconds` | `events.jsonl` | `task_complete.runtime_seconds`. | High | High | Exact |
| `start_time` | `events.jsonl` | Timestamp of first event. | High | High | Exact |
| `end_time` | `events.jsonl` / submission finalization | Last completion/finalization timestamp. | High | High | Exact |
| `step_count` | `events.jsonl` | Count recorded in `task_complete.step_count`. | High | Medium | Exact but trace-limited |
| `tool_call_count` | `events.jsonl` | Count native `tool_call` events. | High | Low | Exact but trace-limited |
| `file_read_count` | `events.jsonl` | Count native `file_read` events. | High | Low | Unsupported for actual reads |
| `file_write_count` | `events.jsonl` | Count native `file_write` events. | High | Low | Unsupported for actual writes |
| `exception_count` | `events.jsonl` | Count native `exception` events. | High | Medium | Exact but trace-limited |
| `verification_event_count` | `events.jsonl` | Count native `verification` events. | High | Medium | Exact but undercounted |
| `execution_success_rate` | execution status | `1.0` when status is `COMPLETED`, else lower/failure. | High | High | Exact |
| `tool_efficiency_score` | `events.jsonl` | Native tool events over total latency proxy. For TXN-001: based on one outer `codex.subprocess`. | High | Low | Inferred / trace-limited |
| `tool_failure_rate` | `events.jsonl` | Failed native `tool_result` count / native `tool_result` count. | High | Low | Exact but trace-limited |
| `tool_recovery_rate` | `events.jsonl` | Recovery proxy from retry/exception/failure events. | High | Low | Inferred |
| `tools_ranked_by_usage.*` | `events.jsonl` | Group native tool events by `tool_name`. | High | Low | Exact but trace-limited |
| `workspace_readiness_score` | `manifest.workspace_hash`, workspace files | Heuristic file quality score: real vs placeholder/synthetic/missing. | Medium | Medium | Inferred |
| `workspace_classification` | workspace quality assessment | Classification from readiness score and file categories. | Medium | Medium | Inferred |
| `real_documents` | workspace file classification | Count files considered real. | Medium | Medium | Inferred |
| `placeholder_documents` | workspace file classification | Count files considered placeholders. | Medium | Medium | Inferred |
| `synthetic_documents` | workspace file classification | Count files considered synthetic. | Medium | Medium | Inferred |
| `missing_documents` | workspace specification vs files | Expected missing input count. | Medium | Medium | Inferred |
| `workspace_file_recall` | workspace files, `events.jsonl` | `files_read / files_discovered`. Reported `0.0` from native trace. | High | Low | Unsupported for actual recall |
| `workspace_file_precision` | `events.jsonl` | File-read precision if reads exist; unavailable here. | High | High | Exact availability |
| `files_written` | `state/state_diff.json` | Output paths created/modified. | High | High | Exact |
| `documents_accessed` | native `file_read` events | Count document accesses from official trace. | High | Low | Unsupported for actual access |
| `documents_used` | output/reference heuristics | Count documents inferred as used. | Medium | Medium | Inferred |
| `importance_score` | document utilization heuristics | Heuristic score from access/use/state/output evidence. | Medium | Low | Inferred |
| `retrieval_recall` | required docs vs native reads | `documents_read / documents_required`. Reported `0.0`. | High | Low | Unsupported for actual retrieval |
| `retrieval_precision` | native reads vs used docs | Unavailable because native reads absent. | High | High | Exact availability |
| `claims_made` | `canonical_output.json` | Heuristic extraction of output claims. | Medium | Low | Inferred |
| `claims_supported` | canonical output + document utilization | Heuristic supported-claim count. | Medium | Low | Inferred |
| `claims_unsupported` | canonical output + document utilization | Heuristic unsupported-claim count. | Medium | Low | Inferred |
| `grounding_score` | claims counts | `claims_supported / claims_made`. | Medium | Low | Inferred |
| `s0_hash`, `s1_hash` | `state/S0.json`, `state/S1.json` | Workspace hash values copied from snapshots. | High | High | Exact |
| `files_created` | `state/state_diff.json` | Created output paths. | High | High | Exact |
| `files_modified` | `state/state_diff.json` | Modified paths. | High | High | Exact |
| `files_deleted` | `state/state_diff.json` | Deleted paths. | High | High | Exact |
| `side_effects_detected` | `state/state_diff.json` | Count output/state changes. | High | Medium | Exact as filesystem side effects |
| `state_consistency_score` | `state/state_diff.json` | Score from valid captured state and no conflicting duplicate actions. | Medium | Medium | Inferred |
| `state_retention_score` | S0/S1/state diff | Score from retained workspace state. | Medium | Medium | Inferred |
| `output_size` | `canonical_output.json` | Sum report content string lengths. | High | High | Exact |
| `records_generated` | `canonical_output.json` | Count `content.structured_records`. | High | High | Exact |
| `tables_generated` | `canonical_output.json` | Count `content.tables`. | High | High | Exact |
| `reports_generated` | `canonical_output.json` | Count `content.reports`. | High | High | Exact |
| `normalization_status` | `canonical_output.json` | Copied canonical `status`. | High | High | Exact |
| `schema_validation_status` | `canonical_output.json` | Copied canonical `validation.valid`. | High | High | Exact |
| `operator_score` | `grading_result.json` | Official grading engine aggregate. Dealbreaker forces `0.0`. | High | High | Exact |
| `all_pass` | `grading_result.json` | Official boolean aggregate over operator pass/fail. | High | High | Exact |
| `dealbreaker_failed` | `grading_result.json` | Official dealbreaker flag. | High | High | Exact |
| `exact_score` | `grading_result.json` | Mean score for exact operators. | High | Medium | Exact but rubric-ground-truth weak |
| `numeric_score` | `grading_result.json` | Mean score for numeric operators. | High | Medium | Exact but rubric-ground-truth weak |
| `presence_score` | `grading_result.json` | Mean score for presence operators. | High | Medium | Exact |
| `set_match_score` | `grading_result.json` | Mean score for set-match operators. | High | Medium | Exact but no explicit expected set |
| `contradiction_score` | `grading_result.json` | Mean contradiction score. | High | Medium | Exact |
| `state_score` | `grading_result.json` | Mean state score. | High | Medium | Exact |
| `tool_use_score` | `grading_result.json` | Mean tool-use score using native trace. | High | Low | Exact but trace-limited |
| `safety_score` | `grading_result.json` | Mean Safety V1 score. | High | Medium | Exact but known false-positive risk |
| `safety_v2_score` | `grading_result.json` | Availability object because no `safety_v2` rubric operator. | High | High | Exact availability |
| `precision` | `metric_computation` / grading set-match | Uses `set_match_score` as proxy. | High | Low | Unsupported for extraction precision |
| `recall` | retrieval effectiveness | Uses `retrieval_recall`; native trace has no reads. | High | Low | Unsupported for extraction recall |
| `f1` | grading set-match | Uses `set_match_score` as proxy. | High | Low | Unsupported for task F1 |
| `hallucination_rate` | grounding heuristics | `claims_unsupported / claims_made`. | Medium | Low | Inferred |
| `unsupported_claim_rate` | grounding heuristics | Same as hallucination proxy. | Medium | Low | Inferred |
| `workflow_hallucination_rate` | grading exact score proxy | `1 - exact_score`. | High | Low | Unsupported as workflow hallucination |
| `tool_hallucination_rate` | tool failure proxy | Uses `tool_failure_rate`. | High | Low | Unsupported as tool hallucination |
| `process_compliance` | execution summary | Uses `execution_success_rate`. | High | Low | Unsupported as process compliance |
| `tool_efficiency` | tool analysis | Copies `tool_efficiency_score`. | High | Low | Inferred / trace-limited |
| `recovery_rate` | tool analysis | Copies `tool_recovery_rate`. | High | Low | Inferred |
| `side_effect_success` | state analysis | Copies `state_consistency_score`. | Medium | Medium | Inferred |
| `evidence_grounding` | grounding report | Copies `grounding_score`. | Medium | Low | Inferred |
| `agent_runtime_minutes` | execution runtime | `runtime_seconds / 60`. | High | High | Exact |
| `human_time_minutes` | task metadata | Copied expert time estimate. | High | Medium | Exact source, estimated value |
| `time_compression_ratio` | task metadata + runtime | `human_time_minutes / agent_runtime_minutes`. | High | Medium | Inferred from estimate |
| `auditability_score` | enterprise heuristics | Composite from grounding/state/tool evidence. | Medium | Low | Inferred |
| `evidence_grounding_score` | grounding report | Copies `grounding_score`. | Medium | Low | Inferred |
| `operational_reliability_score` | execution/state/tool heuristics | Reliability proxy. | Medium | Medium | Inferred |
| `tool_capture_recall` | `events.jsonl`, `reconstructed_events.jsonl` | `official_tool_events / reconstructed_expected_tool_events`. | High | High | Exact for transcript-reconstruction framework |
| `file_capture_recall` | `events.jsonl`, `reconstructed_events.jsonl` | `official_file_events / reconstructed_file_events`. | High | Medium | Exact, reconstruction-dependent |
| `verification_capture_recall` | `events.jsonl`, `reconstructed_events.jsonl` | `official_verification_events / reconstructed_verification_events`. | High | Medium | Exact, reconstruction-dependent |
| `trace_fidelity_score` | trace fidelity metrics | Mean of tool/file/verification capture recall. | High | Medium | Inferred composite |
| `reconstructed_tool_capture_recall` | `reconstructed_events.jsonl` | `reconstructed_tool_events / expected_tool_events`. | High | Medium | Exact, reconstruction-dependent |
| `reconstructed_file_capture_recall` | `reconstructed_events.jsonl` | `reconstructed_file_events / expected_file_events`. | High | Medium | Exact, reconstruction-dependent |
| `reconstructed_verification_capture_recall` | `reconstructed_events.jsonl` | `reconstructed_verification_events / expected_verification_events`. | High | Medium | Exact, reconstruction-dependent |

## Inferred Metrics

The following metrics are present and reproducible, but depend on heuristic assumptions:

- `workspace_readiness_score`
- `workspace_classification`
- `real_documents`, `placeholder_documents`, `synthetic_documents`
- document `importance_score`
- `documents_used`
- `claims_made`, `claims_supported`, `claims_unsupported`, `grounding_score`
- `state_consistency_score`, `state_retention_score`
- `hallucination_rate`, `unsupported_claim_rate`
- `time_compression_ratio`
- `auditability_score`, `operational_reliability_score`
- `trace_fidelity_score`

These metrics are useful for review, but they should not be treated as ground-truth evaluation metrics without the formula and source limitations attached.

## Exact Metrics

The strongest exact metrics are directly reproducible from artifacts:

- run identity fields from `manifest.json`
- runtime from `events.jsonl`
- artifact presence/validation from file existence and schema validation
- output counts from `canonical_output.json`
- state files created/deleted/modified from `state/state_diff.json`
- official operator scores from `grading_result.json`
- trace-fidelity counts from `events.jsonl` and `reconstructed_events.jsonl`

These have high reproducibility. Confidence depends on whether the source artifact has complete observability. For TXN-001, native `events.jsonl` is known incomplete for inner Codex actions.

## Unsupported Or Misleading Metrics

| Metric | Why unsupported or misleading |
|---|---|
| `precision`, `recall`, `f1` in `metric_computation` | These are grading/retrieval proxies, not the task-specific extraction metrics computed against TXN-001 ground truth. |
| `workflow_hallucination_rate` | Uses `1 - exact_score`; exact score is mostly presence fallback because expected rubric values are absent. |
| `tool_hallucination_rate` | Uses tool failure rate, which is not hallucinated tool-use detection. |
| `process_compliance` | Uses execution success rate, not process compliance. Reconstructed process metrics show native trace undercapture. |
| `file_read_count`, `workspace_file_recall`, `retrieval_recall`, `documents_read` | Native trace has no file-read events, but raw transcript and reconstructed trace prove files were read. |
| `tool_call_count`, `tool_efficiency_score`, `tool_use_score` | Native trace counts only the outer `codex.subprocess`, not inner Codex commands. |
| `safety_score` | Reproducible Safety V1 result, but TXN-001 safety audit identified a keyword false positive from echoed prompt text. |

## Key Validation Findings

1. The report is mechanically reproducible from the run artifacts.
2. Native trace-derived process metrics are not behaviorally complete for TXN-001.
3. The new `trace_fidelity_analysis` correctly discloses this gap:
   - official `tool_capture_recall`: `0.055556`
   - official `file_capture_recall`: `0.0`
   - official `trace_fidelity_score`: `0.185185`
   - reconstructed `trace_fidelity_score`: `1.0`
4. Official `precision`, `recall`, and `f1` in `metric_computation` should not be used as TXN-001 extraction accuracy. The task-specific extraction metrics remain in `tx001_execution_summary.md`.
5. Safety V1 is reproducible, but the safety audit classifies the dealbreaker as a heuristic false positive.

## Recommendation

Use `run_intelligence_report.json` as an audit index, not as the sole source of benchmark truth. For TXN-001:

- Use `tx001_execution_summary.md` for task-specific extraction, duplicate, and ledger metrics.
- Use `trace_fidelity_analysis` for process observability.
- Treat native trace process metrics as low-confidence unless reconstructed metrics are also consulted.
- Treat Safety V1 as official historical grading, but use `tx001_safety_audit.md` and future Safety V2 for reviewer interpretation.
