# Phase 5 Output Normalization Layer

Phase 5 converts adapter-specific run-cell outputs into `canonical_output.json`, a stable representation graders can consume without knowing whether the run came from Codex, Claude, Gemini, WildClaw, or a future adapter.

This phase does not implement grading, metrics, or leaderboards.

## Architecture

```text
Run Cell
  manifest.json
  submission.json
  raw_response.txt
  final_output.md
  artifacts/
  events.jsonl
  state/state_diff.json
  state/side_effect_audit.json
        |
        v
Output Normalizer
  synthbench.normalization.output
        |
        v
  canonical_output.json
```

The normalizer is adapter-independent. It reads the run-cell contract instead of adapter internals.

## Canonical Schema

Top-level fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Canonical output schema version |
| `normalized_at` | UTC timestamp |
| `identity` | experiment/run/task/model/dataset/fixture IDs |
| `adapter` | adapter ID and source adapter status |
| `status` | `COMPLETED`, `FAILED`, `TIMED_OUT`, or `UNKNOWN` |
| `content` | normalized benchmark content |
| `raw_sources` | raw files used with size and SHA-256 |
| `provenance` | raw-to-normalized mapping |
| `validation` | schema validation result |

`content` always contains:

| Field | Meaning |
| --- | --- |
| `structured_records` | JSON-like records, including `submission.answers` and JSON artifacts |
| `tables` | CSV files and JSON list-of-object artifacts |
| `reports` | final output and text/Markdown artifacts |
| `side_effect_summaries` | state diff, side-effect audit, and deliverable summary |
| `exception_summaries` | exception events and adapter submission errors |

## Provenance

Every transformed source records:

```json
{
  "raw_path": "artifacts/run_summary.csv",
  "raw_pointer": "",
  "raw_sha256": "...",
  "normalized_pointer": "/content/tables/0",
  "transform": "csv_to_table"
}
```

This preserves the mapping from raw adapter output to normalized grading input.

## Commands

Generate canonical output:

```bash
python3 tools/normalize_output.py --cell runs/codex/TXN-001/seed-0
```

Validate an existing canonical output:

```bash
python3 tools/normalize_output.py \
  --cell runs/codex/TXN-001/seed-0 \
  --validate-only
```

Emit machine-readable validation status:

```bash
python3 tools/normalize_output.py \
  --cell runs/codex/TXN-001/seed-0 \
  --json
```

Override adapter ID for future adapters:

```bash
python3 tools/normalize_output.py \
  --cell runs/claude/TXN-001/seed-0 \
  --adapter-id claude
```

## Migration Instructions

For every completed run cell:

1. Execute the adapter or finalize manual output.
2. Validate trace and state.
3. Run `tools/normalize_output.py`.
4. Treat `canonical_output.json` as the only input to future graders.

Future adapters only need to write the run-cell contract:

- `manifest.json`
- `submission.json`
- `raw_response.txt`
- `final_output.md`
- `artifacts/`
- `events.jsonl`
- `state/state_diff.json`

They do not need grader-specific logic.
