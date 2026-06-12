# Phase 4A Codex Execution Adapter

Phase 4A executes a prepared benchmark run cell through a Codex-compatible adapter while preserving the existing registry, manifest, trace, and state-audit contracts.

This phase does not implement grading, metrics, or leaderboards.

## Architecture

```text
Prepared Run Cell
  manifest.json
  prompt.txt
  workspace_dir from manifest
        |
        v
Codex Adapter
  synthbench.adapters.codex
        |
        v
Run Cell Outputs
  raw_response.txt
  final_output.md
  artifacts/
  events.jsonl
  state/S0.json
  state/S1.json
  state/state_diff.json
  submission.json
```

The adapter has two modes:

| Mode | Purpose |
| --- | --- |
| `dry-run` | Validation mode. Simulates execution and does not invoke Codex. |
| `codex` | Subprocess mode. Sends `prompt.txt` to the configured Codex command over stdin. |

## Adapter Interface

Input:

- `manifest.json`
- `prompt.txt`
- workspace path from `manifest.workspace_dir`
- task metadata already embedded in the manifest/run cell

Output:

- execution artifacts inside the run directory
- canonical trace events in `events.jsonl`
- S0/S1 snapshots and `state_diff.json`
- updated `submission.json`

## Trace Integration

The adapter emits or ensures:

- `task_start`
- `tool_call`
- `tool_result`
- `exception`
- `retry`
- `state_checkpoint`
- `verification`
- `task_complete`

`task_start` is only appended when the run cell does not already contain events. Prepared cells usually already contain it from `initialize_cell`, and duplicate `task_start` events would fail trace validation.

`task_complete` is emitted in a `finally` path so failed runs still close the trace.

## State Integration

The adapter captures:

- `state/S0.json` before execution
- `state/S1.json` after execution
- `state/state_diff.json` from S1-S0

Snapshots cover workspace files, generated artifacts, and optional `state/mock_state.json`.

## Commands

Validate adapter infrastructure without invoking Codex:

```bash
python3 tools/run_codex_adapter.py \
  --cell runs/codex/TXN-001/seed-0 \
  --mode dry-run
```

Run through a real Codex command:

```bash
python3 tools/run_codex_adapter.py \
  --cell runs/codex/TXN-001/seed-0 \
  --mode codex \
  --codex-command codex exec \
  --timeout-s 1200
```

Use retries for transient command failures:

```bash
python3 tools/run_codex_adapter.py \
  --cell runs/codex/TXN-001/seed-0 \
  --mode codex \
  --codex-command codex exec \
  --timeout-s 1200 \
  --retries 1
```

## Failure Handling

On failure, the adapter:

1. writes `raw_response.txt` and `final_output.md` with the failure summary
2. emits an `exception` event with type, message, recovered status, and recovery action
3. captures S1 and computes `state_diff.json`
4. emits `task_complete`
5. marks `submission.json.status` as `FAILED`

## Migration Instructions

Existing prepared cells can move from manual execution to adapter execution directly:

1. Prepare the cell with `tools/prepare_benchmark_run.py`.
2. Run `tools/run_codex_adapter.py --mode dry-run` to validate infrastructure.
3. Validate trace and state:

```bash
python3 tools/validate_trace.py --cell runs/codex/TXN-001/seed-0
python3 tools/validate_state.py --cell runs/codex/TXN-001/seed-0
```

4. Switch to `--mode codex` when ready to invoke Codex.

For large-scale scheduling, Stage 3 should call this adapter per run cell and treat nonzero adapter status as an execution failure, not a grading failure.
