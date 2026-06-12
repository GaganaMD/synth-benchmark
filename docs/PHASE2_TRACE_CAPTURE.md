# Phase 2 Trace Capture Infrastructure

Phase 2 makes each benchmark run replayable and analyzable from:

```text
manifest.json + events.jsonl
```

This phase does not implement model runners, execution adapters, grading, or leaderboards.

## 1. Architecture

```text
Run Cell
  manifest.json      Phase-1 identity and replay metadata
  prompt.txt         Agent-facing prompt
  events.jsonl       Append-only canonical event stream
  submission.json    Final normalized output shell
  artifacts/         Agent-created files
  state/             State diffs and checkpoints

Trace Layer
  synthbench.trace.events
    event constructors
    crash-safe JSONL append
    event and trace validators

  synthbench.trace.replay
    load manifest + events
    validate ordering and required fields
    reconstruct execution timeline summary
```

## 2. Canonical Event Schema

Every event must include:

| Field | Required | Meaning |
| --- | --- | --- |
| `event_id` | yes | Unique event ID |
| `experiment_id` | yes | Phase-1 experiment ID |
| `run_id` | yes | Phase-1 run ID |
| `task_id` | yes | Task ID |
| `timestamp` | yes | UTC ISO timestamp |
| `event_type` | yes | One of the supported event types |

Supported event types:

- `task_start`
- `plan_created`
- `file_read`
- `file_write`
- `tool_call`
- `tool_result`
- `state_checkpoint`
- `exception`
- `retry`
- `verification`
- `side_effect`
- `task_complete`

## 3. Tool Events

`tool_call` and `tool_result` events support:

| Field | Meaning |
| --- | --- |
| `tool_name` | Tool or subsystem name |
| `arguments` | JSON-serializable arguments |
| `result` | JSON-serializable result or text |
| `success` | Boolean |
| `latency_ms` | Non-negative latency in milliseconds |

## 4. Exception Events

`exception` events support:

| Field | Meaning |
| --- | --- |
| `exception_type` | Exception class/category |
| `message` | Error message |
| `recovered` | Boolean |
| `recovery_action` | What was done to recover |

## 5. State Checkpoint Events

`state_checkpoint` events support:

| Field | Meaning |
| --- | --- |
| `checkpoint_id` | Stable checkpoint ID |
| `state_summary` | JSON summary or text summary |

These are trace checkpoints, not full S0/S1 state diffs. Full state diffing remains a later phase.

## 6. Runtime Accounting

`task_complete` events support:

| Field | Meaning |
| --- | --- |
| `runtime_seconds` | Total runtime for the run |
| `step_count` | Number of prior events/steps |
| `input_tokens` | Placeholder for future model accounting |
| `output_tokens` | Placeholder for future model accounting |
| `estimated_cost` | Placeholder for future cost accounting |

## 7. Event Store

Events are stored in:

```text
runs/<harness>/<task_id>/seed-<n>/events.jsonl
```

Properties:

- append-only
- one JSON object per line
- each append flushes and fsyncs the file
- replay uses only `manifest.json` and `events.jsonl`

## 8. Validation

Trace validation checks:

- required core fields are present
- event type is valid
- timestamps are parseable
- timestamps are monotonic
- event IDs are unique
- `task_start` is first when events exist
- no events occur after `task_complete`
- event-type-specific required fields are present

Validate a cell:

```bash
python3 tools/validate_trace.py --cell runs/codex/TXN-001/seed-0
```

Print replay JSON:

```bash
python3 tools/validate_trace.py --cell runs/codex/TXN-001/seed-0 --json
```

## 9. Manual Event Capture

Examples:

```bash
python3 tools/record_event.py \
  --cell runs/codex/TXN-001/seed-0 \
  --event-type plan_created \
  --metadata '{"summary":"initial plan captured"}'

python3 tools/record_event.py \
  --cell runs/codex/TXN-001/seed-0 \
  --event-type tool_call \
  --tool-name shell \
  --arguments '{"cmd":"ls workspace"}' \
  --success true \
  --latency-ms 120

python3 tools/record_event.py \
  --cell runs/codex/TXN-001/seed-0 \
  --event-type exception \
  --exception-type FileNotFoundError \
  --message "missing invoice.pdf" \
  --recovered true \
  --recovery-action "searched alternate intake folder"

python3 tools/record_event.py \
  --cell runs/codex/TXN-001/seed-0 \
  --event-type state_checkpoint \
  --checkpoint-id pre-final \
  --state-summary '{"files_written":2,"exceptions":1}'
```

`tools/finalize_manual_run.py` appends `task_complete` if one is not already present.

## 10. Migration Instructions

Old loose event types should be replaced:

| Old | New |
| --- | --- |
| `plan` | `plan_created` |
| `observation` | `tool_result` or `verification` |
| `self_verify` | `verification` |
| `final` | `task_complete` plus `final_output.md` |
| `error` | `exception` |
| `note` | `plan_created`, `verification`, or event `metadata` |

Existing old-format traces should be treated as exploratory and regenerated before formal benchmark claims.
