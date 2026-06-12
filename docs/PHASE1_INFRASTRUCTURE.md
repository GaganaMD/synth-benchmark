# Phase 1 Benchmark Infrastructure

Phase 1 prepares the repository for benchmark execution without implementing model runners, execution adapters, or grading changes.

## 1. Architecture Proposal

Phase 1 introduces four infrastructure layers before any benchmark run:

```text
Dataset Registry
  canonical CSV -> dataset_version -> task_count + checksum + git commit

Immutable Fixture Store
  task workspace -> fixture_version -> content-addressed blobs + workspace manifest

Experiment Registry
  experiment_id/run_id -> task + harness + model + seed + dataset + fixture + environment

Hardened Manifest
  run cell manifest references dataset_version, fixture_version, environment_version,
  workspace hash, git commit, seed, model_id, harness_id, experiment_id, run_id
```

The key rule is: **no run should depend only on mutable files**. A run may use files in `tasks_complete/<TASK_ID>/workspace/` during manual operation, but its manifest must point to an immutable fixture version that can be materialized later.

## 2. Schema Design

### Dataset Registry

Storage:

```text
registry/datasets.jsonl
registry/latest_dataset.json
```

Record:

```json
{
  "schema_version": "1.0",
  "dataset_version": "v10-revised-labels",
  "canonical_csv": "data/v10.csv",
  "created_at": "2026-06-12T00:00:00Z",
  "git_commit": "...",
  "task_count": 76,
  "checksum": "sha256..."
}
```

### Fixture Registry

Storage:

```text
registry/fixtures.jsonl
immutable_inputs/<fixture_version>/fixture_manifest.json
immutable_inputs/<fixture_version>/workspace/
immutable_inputs/blobs/<first-two-sha-chars>/<sha256>
```

Record:

```json
{
  "schema_version": "1.0",
  "fixture_version": "v10-revised-labels__TXN-001__2f601427ad6d1822",
  "created_at": "2026-06-12T00:00:00Z",
  "source_workspace": "tasks_complete/TXN-001/workspace",
  "fixture_root": "immutable_inputs",
  "workspace_copy": "immutable_inputs/v10-revised-labels__TXN-001__.../workspace",
  "workspace_hash": "sha256 tree hash",
  "file_count": 5,
  "files": [
    {
      "path": "intake/invoice.pdf",
      "size": 12345,
      "sha256": "sha256...",
      "blob_path": "immutable_inputs/blobs/ab/ab..."
    }
  ]
}
```

### Experiment Registry

Storage:

```text
registry/experiments.jsonl
```

Record:

```json
{
  "schema_version": "1.0",
  "experiment_id": "exp_...",
  "run_id": "run_...",
  "task_id": "TXN-001",
  "harness_id": "codex",
  "model_id": "exact-model-or-runtime-id",
  "seed": 0,
  "dataset_version": "v10-revised-labels",
  "fixture_version": "v10-revised-labels__TXN-001__...",
  "environment_version": "env_...",
  "git_commit": "...",
  "timestamp": "2026-06-12T00:00:00Z",
  "run_dir": "runs/codex/TXN-001/seed-0",
  "manifest_path": "runs/codex/TXN-001/seed-0/manifest.json",
  "status": "PREPARED"
}
```

### Hardened Manifest

Each run cell manifest now contains:

- `experiment_id`
- `run_id`
- `task_id`
- `harness_id`
- `model_id`
- `seed`
- `dataset_version`
- `dataset`
- `fixture_version`
- `fixture`
- `environment_version`
- `workspace_hash`
- `git_commit`
- `repo`
- `environment`
- `replay`

## 3. Implementation Plan

Implemented in Phase 1:

1. Register canonical datasets before run preparation.
2. Hash and register task workspaces into content-addressed immutable fixtures.
3. Append one experiment registry record per prepared run cell.
4. Harden run manifests to reference dataset, fixture, environment, git, harness, model, task, and seed identifiers.
5. Add query/retrieval tools for registries and fixtures.
6. Keep generated run artifacts out of source control.

Explicitly not implemented in Phase 1:

- model execution adapters
- Codex/Hermes/Synth-Max runners
- grading changes
- live OneDrive/Zoho/Tally/AWS state diffing
- scheduler queues or distributed execution

## 4. Commands

Register a dataset:

```bash
python3 tools/register_dataset.py \
  --dataset-version v10-revised-labels \
  --csv data/v10.csv
```

Prepare run cells. This does not execute a model:

```bash
python3 tools/prepare_benchmark_run.py \
  --csv data/v10.csv \
  --dataset-version v10-revised-labels \
  --tasks-out tasks_complete \
  --runs-root runs \
  --harnesses codex \
  --model-id "PIN_EXACT_CODEX_MODEL_OR_RUNTIME" \
  --task-id TXN-001 \
  --seeds 1 \
  --storage-backend local \
  --overwrite
```

Register or retrieve a fixture manually:

```bash
python3 tools/register_fixture.py register \
  --fixture-version manual-fixture-v1 \
  --workspace tasks_complete/TXN-001/workspace

python3 tools/register_fixture.py materialize \
  --fixture-version manual-fixture-v1 \
  --out /tmp/replay-workspace \
  --overwrite
```

Query experiment records:

```bash
python3 tools/query_experiments.py --task-id TXN-001
python3 tools/query_experiments.py --dataset-version v10-revised-labels --harness-id codex
```

Check cell readiness:

```bash
python3 tools/check_pipeline_readiness.py --cell runs/codex/TXN-001/seed-0
```

## 5. Migration Instructions

1. Pick one canonical CSV and assign a stable `dataset_version`.
2. Register it with `tools/register_dataset.py`.
3. Prepare tasks and run cells with `tools/prepare_benchmark_run.py`.
4. Confirm each manifest contains non-empty:
   - `experiment_id`
   - `run_id`
   - `dataset_version`
   - `fixture_version`
   - `environment_version`
   - `workspace_hash`
   - `git_commit`
   - `seed`
   - `model_id`
   - `harness_id`
5. For replay, materialize the fixture by `fixture_version` into a clean workspace.
6. Do not start Stage 4 execution until readiness checks pass for every scheduled cell.

## 6. Storage Notes

`registry/*.jsonl` and `immutable_inputs/` are generated benchmark infrastructure artifacts. For local pilots they can remain local. For formal benchmark runs, archive them with the run store or move them to S3 with versioning and KMS encryption.
