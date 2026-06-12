# Artifact Contracts

Generated from `synthbench.schemas.artifacts`. Do not edit schema tables by hand; rerun `tools/generate_schema_docs.py` after schema changes.

Phase 5.5 freezes the benchmark artifact contracts at schema version `1.0`.

## Artifacts

### `manifest`

Schema file: [`schemas/artifacts/manifest.v1.0.schema.json`](../schemas/artifacts/manifest.v1.0.schema.json)

Title: Benchmark Manifest

Required fields:

- `schema_version`: `string`
- `experiment_id`: `string`
- `run_id`: `string`
- `task_id`: `string`
- `harness_id`: `string`
- `model_id`: `string`
- `seed`: `integer`
- `dataset_version`: `string`
- `fixture_version`: `string`
- `environment_version`: `string`
- `workspace_hash`: `object`
- `git_commit`: `string`


### `canonical_output`

Schema file: [`schemas/artifacts/canonical_output.v1.0.schema.json`](../schemas/artifacts/canonical_output.v1.0.schema.json)

Title: Canonical Output

Required fields:

- `schema_version`: `string`
- `normalized_at`: `string`
- `identity`: `object`
- `adapter`: `object`
- `status`: `string`
- `content`: `object`
- `raw_sources`: `array`
- `provenance`: `array`
- `validation`: `object`


### `event`

Schema file: [`schemas/artifacts/event.v1.0.schema.json`](../schemas/artifacts/event.v1.0.schema.json)

Title: Trace Event

Required fields:

- `schema_version`: `string`
- `event_id`: `string`
- `experiment_id`: `string`
- `run_id`: `string`
- `task_id`: `string`
- `timestamp`: `string`
- `event_type`: `string`


### `snapshot`

Schema file: [`schemas/artifacts/snapshot.v1.0.schema.json`](../schemas/artifacts/snapshot.v1.0.schema.json)

Title: State Snapshot

Required fields:

- `schema_version`: `string`
- `snapshot_id`: `string`
- `timestamp`: `string`
- `workspace_hash`: `['string', 'null']`
- `workspace`: `object`
- `outputs`: `object`
- `filesystem`: `object`


### `state_diff`

Schema file: [`schemas/artifacts/state_diff.v1.0.schema.json`](../schemas/artifacts/state_diff.v1.0.schema.json)

Title: State Diff

Required fields:

- `schema_version`: `string`
- `status`: `string`
- `changes`: `array`


## Validation

Validate a full run cell:

```bash
python3 tools/validate_artifacts.py --cell runs/codex/TXN-001/seed-0 --require-canonical
```

Validate one artifact:

```bash
python3 tools/validate_artifacts.py --artifact-type manifest --path runs/codex/TXN-001/seed-0/manifest.json
```

## Compatibility

The validator checks every artifact's `schema_version` against the frozen current version. Missing versions are reported as compatibility issues. `--allow-migration` applies available in-memory migrations before validation.

## Migration Strategy

Migration hooks live in `synthbench.schemas.migrations`. Version `1.0` is the baseline. Future versions should add explicit artifact-specific transforms and keep validators able to read older benchmark records without changing graders.

Write a migrated copy without modifying the original:

```bash
python3 tools/migrate_artifact.py --artifact-type manifest --path old/manifest.json --output migrated/manifest.json
```
