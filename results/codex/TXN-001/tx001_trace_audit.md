# TXN-001 Trace Fidelity Audit

Task: TXN-001  
Run: `runs/codex/TXN-001/seed-0`  
Experiment ID: `exp_3697a2b14c4d`  
Run ID: `run_0d217bb566c6`

This audit reviews trace fidelity only. TXN-001 was not rerun, grading logic was not modified, and no benchmark scores were recomputed.

## Summary

The benchmark trace captures the outer Codex adapter invocation, but it does not capture the inner Codex CLI tool actions as first-class benchmark events.

| Metric | Value |
|---|---:|
| expected_tool_events | 36 |
| observed_tool_events | 2 |
| missing_tool_events | 34 |
| tool_capture_recall | 0.0556 |
| inner_codex_exec_calls_observed_in_raw_output | 18 |
| rubric_min_tool_events | 30 |

`expected_tool_events` is computed as 18 inner `exec` actions times 2 event records per action (`tool_call` + `tool_result`). The benchmark trace contains only one outer `codex.subprocess` call and one outer `codex.subprocess` result.

## 1. Codex Actions Executed But Not Recorded

The following inner Codex CLI actions appear in `final_output.md` / `raw_response.txt` but are not represented as individual events in `events.jsonl`:

| # | Action observed in raw Codex transcript | Missing benchmark event types |
|---:|---|---|
| 1 | `find .../tasks_complete/TXN-001/workspace -maxdepth 3 -type d -print` | `tool_call`, `tool_result` |
| 2 | `pwd && rg --files .../workspace` | `tool_call`, `tool_result`, `file_read` |
| 3 | `sed -n '1,160p' .../chart_of_accounts.csv` | `tool_call`, `tool_result`, `file_read` |
| 4 | `sed -n '1,220p' .../recurring_master.csv` | `tool_call`, `tool_result`, `file_read` |
| 5 | `sed -n '1,220p' .../prior_postings.csv` | `tool_call`, `tool_result`, `file_read` |
| 6 | `sed -n '1,220p' .../reimbursement_policy.md` | `tool_call`, `tool_result`, `file_read` |
| 7 | `python3 - <<'PY' ...` workbook/sheet inspection | `tool_call`, `tool_result`, `file_read` |
| 8 | `python3 - <<'PY' ...` intake parsing / extraction work | `tool_call`, `tool_result`, `file_read` |
| 9 | `python3 - <<'PY' ...` duplicate detection work | `tool_call`, `tool_result`, `file_read` |
| 10 | `python3 - <<'PY' ...` ledger / control processing | `tool_call`, `tool_result`, `file_read` |
| 11 | `python3 - <<'PY' ...` artifact generation or validation | `tool_call`, `tool_result`, `file_write`, `verification` |
| 12 | `python3 - <<'PY' ...` artifact generation or validation | `tool_call`, `tool_result`, `file_write`, `verification` |
| 13 | `python3 - <<'PY' ...` artifact generation or validation | `tool_call`, `tool_result`, `file_write`, `verification` |
| 14 | `python3 - <<'PY' ...` artifact generation or validation | `tool_call`, `tool_result`, `file_write`, `verification` |
| 15 | `python3 - <<'PY' ...` artifact generation or validation | `tool_call`, `tool_result`, `file_write`, `verification` |
| 16 | `sed -n '1,80p' .../runs/codex/TXN-001/seed-0/results/summary.txt` | `tool_call`, `tool_result`, `file_read` |
| 17 | `ls -l .../runs/codex/TXN-001/seed-0/results` | `tool_call`, `tool_result` |
| 18 | `python3 - <<'PY' ...` final count/tie-out verification | `tool_call`, `tool_result`, `verification` |

The raw transcript also shows that the agent wrote six result artifacts under `runs/codex/TXN-001/seed-0/results`, but the benchmark trace did not record those individual file writes as `file_write` or `side_effect` events.

## 2. Trace Events Currently Emitted

`events.jsonl` contains 7 events:

| event_type | Count | What it represents |
|---|---:|---|
| `task_start` | 1 | Prepared run cell start event. |
| `state_checkpoint` | 2 | Adapter-level S0 and S1 snapshots. |
| `tool_call` | 1 | Outer `codex.subprocess` invocation only. |
| `tool_result` | 1 | Outer `codex.subprocess` completion only. |
| `verification` | 1 | Adapter persisted `raw_response.txt` and `final_output.md`. |
| `task_complete` | 1 | Adapter-level run completion and runtime. |

The only recorded tool events are:

| event_type | tool_name | Scope |
|---|---|---|
| `tool_call` | `codex.subprocess` | Outer adapter subprocess |
| `tool_result` | `codex.subprocess` | Outer adapter subprocess |

## 3. Missing Event Categories

The following event categories are missing or materially incomplete for this run:

| Category | Status | Impact |
|---|---|---|
| Inner `tool_call` events | Missing | Shell/Python commands executed by Codex are not counted. |
| Inner `tool_result` events | Missing | Success/failure, latency, and outputs of inner tools are not structured. |
| `file_read` events | Missing | Document utilization cannot be measured from trace alone. |
| `file_write` events | Missing | Deliverable creation cannot be reconstructed from trace alone. |
| `verification` events for agent checks | Missing | Only adapter persistence verification is captured, not the agent's count/tie-out checks. |
| `side_effect` events | Missing | Approved postings are file artifacts only; no structured posting/queue event was emitted. |
| Per-tool latency | Missing | Inner command latency is visible only as transcript prose, not structured metrics. |
| Retry/recovery chains | Not applicable in this run | No inner retry structure is available if it occurred. |

## 4. Is Grading Undercounting Tool Usage?

Yes.

The `tool_use` operator reads only `events.jsonl` and counts events where `event_type` is `tool_call` or `tool_result`. For this run, that count is 2.

The same run's raw Codex transcript shows 18 inner `exec` tool calls. If represented in the benchmark trace as call/result pairs, that would be 36 tool events, exceeding the rubric minimum of 30.

Current grading result:

| Field | Value |
|---|---:|
| rubric minimum tool events | 30 |
| counted tool events in grading | 2 |
| inner Codex exec calls in raw output | 18 |
| inferred inner call/result events | 36 |
| tool_use pass_fail | `false` |

Conclusion: grading is undercounting tool usage for Codex subprocess runs because the adapter does not translate inner Codex transcript actions into structured benchmark trace events.

## 5. Are Process-Compliance Metrics Invalid?

Process-compliance metrics that depend on `events.jsonl` tool counts are invalid or low-confidence for this run.

| Metric family | Validity | Reason |
|---|---|---|
| Tool-use count | Invalid | Counts outer adapter events, not inner Codex actions. |
| Tool efficiency | Invalid | Inner command latencies and outcomes are not structured. |
| Tool failure rate | Invalid | Inner tool failures would be hidden inside raw transcript text. |
| File-read count | Invalid | No `file_read` events emitted, despite multiple reads in raw transcript. |
| File-write count | Invalid from trace alone | Output files exist, but writes were not represented as events. |
| Verification count | Undercounted | Agent performed count/tie-out checks, but only adapter persistence verification is structured. |
| Runtime | Valid | Adapter-level `task_complete.runtime_seconds` is present. |
| State diff | Valid for filesystem state | S0/S1 and `state_diff.json` validate, though trace attribution is incomplete. |
| Output and grading artifacts | Valid | `canonical_output.json`, `grading_result.json`, and intelligence reports were generated and schema validation passed. |

## Root Cause

The current Codex adapter treats `codex exec` as a single subprocess. `synthbench/adapters/codex.py` emits:

- one `tool_call` before `subprocess.run(...)`
- one `tool_result` after `subprocess.run(...)`

It does not parse the Codex raw transcript and does not receive structured inner tool events from the Codex CLI. Therefore, inner shell commands, file reads, file writes, and verification checks remain embedded in text rather than normalized into `events.jsonl`.

## Audit Conclusion

TXN-001 execution completed, but trace fidelity is incomplete for process analytics.

The run's output artifacts can still be evaluated for extraction, duplicate detection, ledger mapping, and state/output validation. However, benchmark claims about process compliance, tool-use efficiency, tool failure rate, file-read/file-write behavior, and detailed workflow reconstruction should not rely on `events.jsonl` alone for this run.

Recommended future infrastructure work, without changing current grading logic: add a Codex transcript-to-event extraction step or native structured event ingestion from the Codex CLI so inner tool calls become first-class benchmark trace events.
