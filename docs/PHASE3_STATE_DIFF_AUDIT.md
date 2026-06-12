# Phase 3 State Diff and Side Effect Auditing

Phase 3 determines what changed during a benchmark run and whether observed side effects match expectations.

This phase does not implement model runners, grading, or leaderboards.

## 1. Architecture

```text
Run Cell
  state/S0.json                pre-run state snapshot
  state/S1.json                post-run state snapshot
  state/state_diff.json        reproducible S1-S0 diff
  state/side_effect_audit.json file/side-effect audit report

State Layer
  synthbench.state.snapshots   captures filesystem, workspace, outputs, mock state
  synthbench.state.diff        computes created/modified/deleted/content changes
  synthbench.state.audit       side-effect records and duplicate detection
  synthbench.state.validation  validates S0/S1/diff consistency
```

## 2. Snapshot Schema

Every snapshot contains:

| Field | Meaning |
| --- | --- |
| `snapshot_id` | Stable S0/S1 snapshot ID |
| `timestamp` | UTC timestamp |
| `workspace_hash` | Tree hash of workspace files |
| `workspace` | Full workspace hash inventory |
| `outputs_hash` | Tree hash of generated outputs |
| `outputs` | Full generated-output inventory |
| `filesystem.workspace_files` | File list with path, size, sha256 |
| `filesystem.output_files` | Output file list with path, size, sha256 |
| `mock_state` | Optional mock system state JSON/text |

## 3. Diff Schema

`state/state_diff.json` contains:

| Field | Meaning |
| --- | --- |
| `s0_snapshot_id` | Source S0 snapshot |
| `s1_snapshot_id` | Source S1 snapshot |
| `workspace_hash_before` | S0 workspace hash |
| `workspace_hash_after` | S1 workspace hash |
| `changes` | Created, modified, deleted, and mock-state changes |
| `summary` | Counts by change type/scope |

Each change contains:

```json
{
  "scope": "workspace | outputs | mock_state",
  "change_type": "created | modified | deleted",
  "path": "relative/path",
  "before": {"sha256": "...", "size": 123},
  "after": {"sha256": "...", "size": 456}
}
```

## 4. Side Effect Audit Schema

Each effect contains:

| Field | Meaning |
| --- | --- |
| `effect_id` | Unique effect ID |
| `effect_type` | e.g. `file_output`, `posting`, `email`, `onedrive_file` |
| `target` | File path, posting ID, email ID, etc. |
| `expected` | Expected value/state |
| `observed` | Observed value/state |
| `status` | `PASS`, `FAIL`, or `PARTIAL` |

## 5. Filesystem Auditing

Filesystem auditing detects:

- output files generated
- missing expected outputs
- unexpected outputs
- duplicate output names

## 6. Duplicate Detection

Supported duplicate checks:

- duplicate outputs by basename
- duplicate postings by date/vendor/invoice/amount/ledger
- repeated side effects by effect type, target, and observed value

## 7. Commands

Capture S0 manually:

```bash
python3 tools/capture_state.py --cell runs/codex/TXN-001/seed-0 --label S0
```

Capture S1 and compute diff:

```bash
python3 tools/capture_state.py --cell runs/codex/TXN-001/seed-0 --label S1 --compute-diff
```

Audit expected outputs:

```bash
python3 tools/audit_side_effects.py \
  --cell runs/codex/TXN-001/seed-0 \
  --expected-output run_summary.csv
```

Validate state:

```bash
python3 tools/validate_state.py --cell runs/codex/TXN-001/seed-0
```

## 8. Replay Integration

`synthbench.trace.replay.replay_cell()` now includes:

- `state.s0`
- `state.s1`
- `state.diff`
- `state.side_effect_audit`

This allows reconstruction of:

- before state
- after state
- change set
- observed file side effects

## 9. Migration Instructions

For every prepared cell:

1. Ensure `state/S0.json` exists before execution.
2. After manual/model output is written to `artifacts/`, capture `state/S1.json`.
3. Compute `state/state_diff.json`.
4. Run side-effect audit with expected output paths.
5. Run `tools/validate_state.py`.

`tools/finalize_manual_run.py` now captures S1 and computes the diff automatically when S0 exists.
