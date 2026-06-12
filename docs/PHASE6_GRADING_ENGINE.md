# Phase 6 Rubric-Based Grading Engine

Phase 6 grades one completed run cell at a time using rubric operators over frozen artifacts.

This phase does not implement leaderboard aggregation or benchmark-wide metrics.

## Architecture

```text
Run Cell
  manifest.json
  canonical_output.json
  events.jsonl
  state/state_diff.json
        +
  rubric from task.json or JSON file
        |
        v
Grading Engine
  synthbench.grading.engine
  synthbench.grading.operators
        |
        v
  grading_result.json
```

## Interface

Inputs:

- `manifest.json`
- `canonical_output.json`
- `events.jsonl`
- `state/state_diff.json`
- rubric list

Output:

- `grading_result.json`

## Operators

| Operator | Behavior |
| --- | --- |
| `exact` | Normalized scalar equality. If expected is omitted, falls back to presence. |
| `numeric` | Numeric equality within `tolerance`. |
| `presence` | Checks that a value or report content exists. |
| `set_match` | Computes precision, recall, and F1. |
| `contradiction` | Detects conflicting structured values, conflicting state changes, and conflict markers in reports. |
| `state` | Evaluates `state_diff.json` against expected outputs/changes when supplied. |
| `tool_use` | Evaluates `events.jsonl` against expected tool behavior and failed tool results. |
| `safety` | Checks destructive deletes and unauthorized/destructive/policy markers. |

Every operator returns:

- `score`
- `pass_fail`
- `evidence.reason`
- `evidence.supporting_artifact`
- `evidence.supporting_fields`

## Commands

Grade using a task JSON rubric:

```bash
python3 tools/grade_run.py \
  --cell runs/codex/TXN-001/seed-0 \
  --task-json tasks_complete/TXN-001/task.json
```

Grade using a standalone rubric file:

```bash
python3 tools/grade_run.py \
  --cell runs/codex/TXN-001/seed-0 \
  --rubric rubric.json
```

Use inline rubric JSON:

```bash
python3 tools/grade_run.py \
  --cell runs/codex/TXN-001/seed-0 \
  --rubric-json '[{"operator":"presence","criteria":"final_output"}]'
```

Skip frozen artifact validation only for debugging:

```bash
python3 tools/grade_run.py \
  --cell runs/codex/TXN-001/seed-0 \
  --task-json tasks_complete/TXN-001/task.json \
  --skip-artifact-validation
```

## Output Shape

`grading_result.json` contains:

- run identity
- input artifact paths
- artifact validation results
- rubric count and graded count
- per-operator results
- `operator_score`
- `all_pass`
- `dealbreaker_failed`

`operator_score` is a per-run rubric score only. It is not a benchmark-wide metric or leaderboard score.

## Migration Instructions

For each completed run cell:

1. Validate artifacts with `tools/validate_artifacts.py`.
2. Ensure `canonical_output.json` exists with `tools/normalize_output.py`.
3. Run `tools/grade_run.py`.
4. Treat `grading_result.json` as the input to future benchmark-wide metric aggregation.
