# Phase 5.5 Artifact Contract Freeze

Phase 5.5 freezes the versioned contracts for benchmark artifacts required before grading and metrics.

This phase does not implement grading, metrics, or leaderboards.

## Frozen Artifacts

- `manifest.json`
- `canonical_output.json`
- `events.jsonl`
- `state/S0.json`
- `state/S1.json`
- `state/state_diff.json`

All frozen artifacts use `schema_version: "1.0"`.

## Schema Specifications

JSON schema files are generated under:

```text
schemas/artifacts/
```

The generated schema documentation is:

```text
docs/ARTIFACT_CONTRACTS.md
```

Regenerate both after schema changes:

```bash
python3 tools/generate_schema_docs.py
```

## Validation

Validate a full run cell:

```bash
python3 tools/validate_artifacts.py \
  --cell runs/codex/TXN-001/seed-0 \
  --require-canonical
```

Validate one artifact:

```bash
python3 tools/validate_artifacts.py \
  --artifact-type state_diff \
  --path runs/codex/TXN-001/seed-0/state/state_diff.json
```

## Compatibility Checks

The validator checks:

- required fields
- field types
- allowed enum values
- `schema_version`
- trace event ordering
- cross-artifact ID consistency where available
- S0/S1 IDs referenced by `state_diff.json`

Use `--allow-migration` to validate after applying available in-memory migrations.

## Migration Strategy

Migration hooks live in:

```text
synthbench/schemas/migrations.py
```

Version `1.0` is the baseline. Future versions should add explicit transforms from each older version to the current target version.

Write a migrated copy without changing the original:

```bash
python3 tools/migrate_artifact.py \
  --artifact-type manifest \
  --path old/manifest.json \
  --output migrated/manifest.json
```
