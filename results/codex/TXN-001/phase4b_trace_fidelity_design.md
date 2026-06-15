# Phase 4B Trace Fidelity Design

Task: TXN-001  
Run: `runs/codex/TXN-001/seed-0`  
Experiment ID: `exp_3697a2b14c4d`  
Run ID: `run_0d217bb566c6`

This phase designs and prototypes transcript-to-event reconstruction. TXN-001 was not rerun and grading logic was not modified.

## Objective

Raise trace tool-capture recall from `0.0556` to above `0.90` by reconstructing inner Codex CLI actions from `raw_response.txt` and `final_output.md`.

The current adapter emits only the outer subprocess:

- `tool_call`: `codex.subprocess`
- `tool_result`: `codex.subprocess`

The raw transcript contains inner Codex actions such as shell commands, Python executions, file reads, file writes, and verification checks.

## Prototype

Implemented standalone prototype:

`tools/reconstruct_codex_events.py`

Generated artifacts:

| Artifact | Location |
|---|---|
| Reconstructed events | `results/codex/TXN-001/seed-0/reconstructed_events.jsonl` |
| Comparison metrics | `results/codex/TXN-001/seed-0/reconstructed_events.comparison.json` |

The prototype reads:

- `runs/codex/TXN-001/seed-0/events.jsonl`
- `runs/codex/TXN-001/seed-0/raw_response.txt`
- `runs/codex/TXN-001/seed-0/final_output.md`
- `runs/codex/TXN-001/seed-0/manifest.json`

It writes reconstructed events separately and does not mutate the original trace.

## Extraction Design

### Input Layer

The extractor combines `raw_response.txt` and `final_output.md`, then scans for Codex transcript blocks:

```text
exec
<command>
 succeeded in <N>ms:
```

It also handles adjacent/parallel `exec` entries by queueing pending commands and assigning result lines in order.

### Tool Event Layer

For every inner `exec` command, the prototype emits:

- `tool_call`
- `tool_result`

Tool names are inferred from command shape:

| Command pattern | Reconstructed tool_name |
|---|---|
| `python3 ...` | `shell.python3` |
| `sed ...` | `shell.sed` |
| `rg ...` | `shell.rg` |
| `find ...` | `shell.find` |
| `ls ...` | `shell.ls` |
| fallback | `shell.exec` |

### Semantic Event Layer

The prototype emits additional semantic events from command heuristics:

| Event type | Extraction signal |
|---|---|
| `file_read` | `sed`, `rg --files`, `find`, `head`, `cat`, `load_workbook`, `DictReader` |
| `file_write` | explicit output artifact paths referenced in transcript |
| `verification` | `counts`, `reconcile`, `summary.txt`, `exceptions.csv`, `Self-check` |
| `retry` | retry-like command markers |
| `exception` | failed command status or exception-like markers |

The reconstructed stream includes the original `task_start` event, synthetic monotonic timestamps, and source metadata so auditors can distinguish reconstructed events from natively captured events.

## Comparison Results

| Metric | Original trace | Reconstructed trace |
|---|---:|---:|
| original_event_count | 7 | n/a |
| reconstructed_event_count | n/a | 52 |
| expected_tool_events | 36 | 36 |
| observed/reconstructed_tool_events | 2 | 36 |
| missing_original_tool_events | 34 | 0 |
| tool_capture_recall | 0.0556 | 1.0000 |
| validation_issues | n/a | 0 |

Event counts in `reconstructed_events.jsonl`:

| event_type | Count |
|---|---:|
| `task_start` | 1 |
| `tool_call` | 18 |
| `tool_result` | 18 |
| `file_read` | 7 |
| `file_write` | 5 |
| `verification` | 2 |
| `exception` | 1 |

## Interpretation

The original trace undercounts tool usage because it captures only the adapter boundary. The reconstructed trace captures every inner Codex `exec` observed in the raw transcript.

For TXN-001:

- Original `tool_capture_recall`: `2 / 36 = 0.0556`
- Reconstructed `tool_capture_recall`: `36 / 36 = 1.0000`

This exceeds the Phase 4B target of `>0.90`.

## Missing or Imperfect Coverage

The prototype is intentionally conservative and still has limitations:

- It reconstructs shell-level tool usage from transcript text, not native Codex structured telemetry.
- Python heredoc internals are not fully parsed into individual file-level operations.
- `file_write` events are inferred from final artifact references, so `summary.json` can be missed if it is not linked in the transcript.
- Latency is taken from transcript status lines where available, but synthetic timestamps are monotonic rather than exact wall-clock times.
- `exception` reconstruction is heuristic and should be interpreted as a signal, not definitive failure evidence.

## Recommended Integration Path

1. Keep `events.jsonl` as the native trace emitted during execution.
2. Add post-run reconstruction as a separate artifact:
   `reconstructed_events.jsonl`.
3. Add comparison metrics to intelligence reports:
   original tool events, reconstructed tool events, tool capture recall, missing tool events.
4. Do not use reconstructed events for official grading until the evaluator explicitly accepts transcript-derived events.
5. Prefer native structured Codex telemetry in the long term. Transcript reconstruction is a compatibility bridge.

## Grading Status

No grading logic was modified.

The existing `tool_use` operator still reads only `events.jsonl`. Therefore, current grading remains unchanged and continues to undercount Codex inner tool usage for this run. The reconstructed trace demonstrates that the failure is trace-capture related rather than evidence that the agent only used two tools.
