# Complete Benchmark Runbook

This runbook turns the repository into the full eight-stage pipeline described in `complete_pipeline/`.

The repo is ready for a small initial set of experiments with local files. OneDrive and AWS are explicit extension points: the run layout, manifests, state-diff slots, and event logs already exist, while live adapters can be wired later without changing the benchmark record format.

## Pipeline Coverage

| Stage | Status in repo | Main files |
| --- | --- | --- |
| 1 Dataset & questionnaire | Ready | `data/*.csv`, `gen_tasks.py` |
| 2 Provisioning & determinism | Ready for local, scaffolded for live | `config.yaml`, `tools/prepare_benchmark_run.py`, `manifest.json` |
| 3 Run matrix & scheduling | Ready for small manual batches | `tools/prepare_benchmark_run.py` |
| 4 Agent execution | Manual capture now, adapter-ready later | `prompt.txt`, `events.jsonl`, `artifacts/` |
| 5 Capture & normalize | Ready for manual finalization | `tools/finalize_manual_run.py`, `submission.json`, `state/state_diff.json` |
| 6 Grading | Ready for rule/state/mock, judge pending | `run_suite.py`, `grader/` |
| 7 Metrics | Partial live metrics, enough for first runs | `metrics/`, `scorecard.py` |
| 8 Benchmark & decision | Smoke support now, deeper leaderboard later | `compare_harnesses.py`, `pilot_filter.py` |

## Directory Layout

Generated task packages:

```text
tasks_complete/<TASK_ID>/
  task.json
  workspace/
  expected.json
  submission.json
  results/
```

Run cells:

```text
runs/<HARNESS>/<TASK_ID>/seed-<N>/
  manifest.json
  prompt.txt
  events.jsonl
  final_output.md
  submission.json
  artifacts/
  logs/
  state/state_diff.json
```

The task package is what `run_suite.py` grades. The run cell is the immutable audit record.

## Harness Names

Use these harness IDs consistently:

| Harness | Intended use | Config |
| --- | --- | --- |
| `codex` | Codex Terminal only | manual local run |
| `codex_hermes` | Codex + Hermes orchestration | `/Users/basethesis/Desktop/hermes-agent` |
| `synth_max` | Synth-Max harness | `/Users/basethesis/Desktop/synth-max-kayyess` |

Exact model IDs still need to be pinned in each `manifest.json` before final benchmark claims. For exploratory runs, leave the TODO but mark results as exploratory.

## Local-File Experiment

Prepare one task for Codex:

```bash
python3 tools/prepare_benchmark_run.py \
  --csv revised_benchmark.csv \
  --tasks-out tasks_complete \
  --runs-root runs \
  --harnesses codex \
  --model-id "PIN_EXACT_CODEX_MODEL_OR_RUNTIME" \
  --task-id TXN-001 \
  --seeds 1 \
  --storage-backend local \
  --overwrite
```

If your local fixtures are already organized by task ID, use:

```bash
python3 tools/prepare_benchmark_run.py \
  --csv revised_benchmark.csv \
  --tasks-out tasks_complete \
  --runs-root runs \
  --harnesses codex \
  --model-id "PIN_EXACT_CODEX_MODEL_OR_RUNTIME" \
  --task-id TXN-001 \
  --local-input-root local_fixtures \
  --seeds 1 \
  --storage-backend local \
  --overwrite
```

Expected local fixture layout:

```text
local_fixtures/TXN-001/
  intake/
  chart_of_accounts.csv
  recurring_master.csv
  reimbursement_policy.md
  prior_postings.csv
```

Then open the prompt:

```bash
sed -n '1,220p' runs/codex/TXN-001/seed-0/prompt.txt
```

Paste that prompt into Codex Terminal. Do not paste rubric, `expected.json`, `reference_answer`, or scoring metadata into the agent.

## Capturing A Manual Run

While the agent runs, append notable events:

```bash
python3 tools/record_event.py \
  --cell runs/codex/TXN-001/seed-0 \
  --event-type tool_call \
  --tool shell \
  --action "read all workspace inputs" \
  --input "tasks_complete/TXN-001/workspace" \
  --success true
```

Use these event types:

- `plan`: planning step
- `tool_call`: file/tool/API command
- `observation`: important result from a tool call
- `self_verify`: tie-out, count check, duplicate check, schema check
- `final`: final answer emitted
- `error`: failed call or blocked operation
- `note`: manual operator note

Save the final Codex answer:

```text
runs/codex/TXN-001/seed-0/final_output.md
```

Save any output files under:

```text
runs/codex/TXN-001/seed-0/artifacts/
```

Finalize the run:

```bash
python3 tools/finalize_manual_run.py \
  --cell runs/codex/TXN-001/seed-0 \
  --task-dir tasks_complete/TXN-001 \
  --copy-to-task
```

Then grade:

```bash
python3 run_suite.py --harness codex --mode mock --tasks tasks_complete --task-id TXN-001
python3 scorecard.py results/codex/results.json
```

## Running All Three Harnesses

Prepare the same task for all three:

```bash
python3 tools/prepare_benchmark_run.py \
  --csv revised_benchmark.csv \
  --tasks-out tasks_complete \
  --runs-root runs \
  --harnesses all \
  --task-id TXN-001 \
  --seeds 1 \
  --storage-backend local \
  --overwrite
```

Run directories created:

```text
runs/codex/TXN-001/seed-0/
runs/codex_hermes/TXN-001/seed-0/
runs/synth_max/TXN-001/seed-0/
```

For `codex_hermes` and `synth_max`, use the same `prompt.txt` and write outputs back into the matching run cell. If their CLIs produce native logs, copy those logs into the cell's `logs/` directory and record a `note` event pointing to the file.

## Values To Extract Per Run

Always capture:

- `task_id`
- `harness`
- exact model ID
- seed
- temperature
- git commit
- start/end time
- elapsed seconds
- final status: `COMPLETED`, `FAILED`, or `TIMED_OUT`
- final answer
- deliverable file paths
- every material tool call
- errors and recovery attempts
- whether all inputs were read
- whether a deliverable was written
- whether self-verification happened
- token/cost values when available
- confidence if the harness emits one
- control violations
- state changes or state-diff placeholder

For finance/CFO tasks, also capture:

- document count
- processed count
- duplicate count
- exception count
- posting/queue decision
- ledger/GST/TDS mapping evidence
- tie-out totals
- unresolved items

## OneDrive Integration Plan

Do not change the task/run format when OneDrive is added. Add a connector that populates `workspace/` and writes state snapshots.

Recommended flow:

1. Register an Azure app with Microsoft Graph permissions for the benchmark tenant.
2. Store credentials outside git, for example in `.env` or a local secret manager.
3. Fill these placeholders in local config only:
   - `onedrive.tenant_id`
   - `onedrive.client_id`
   - `onedrive.drive_id`
   - `onedrive.root_path`
4. Build a sync step that copies OneDrive task assets into:
   - `tasks_complete/<TASK_ID>/workspace/`
5. Before agent execution, write S0 metadata:
   - file IDs
   - paths
   - sizes
   - hashes
   - modified timestamps
6. After execution, write S1 metadata and a diff to:
   - `runs/<HARNESS>/<TASK_ID>/seed-<N>/state/state_diff.json`
7. Keep `mode=mock` until the SharePoint/OneDrive auditor is wired.
8. Switch selected tasks to `mode=live` only after the auditor can prove landed side effects.

The existing `auditors/sharepoint.py` is intentionally not live yet. It should become the Microsoft Graph state-audit adapter.

## AWS Migration Plan

AWS should host the run store and optionally execute cells, but it should not change the benchmark schema.

Recommended mapping:

| Local concept | AWS equivalent |
| --- | --- |
| `runs/` | S3 prefix, e.g. `s3://bucket/runs/` |
| `immutable_inputs/` | S3 content-addressed input store |
| `manifest.json` | S3 object + DynamoDB row |
| `events.jsonl` | S3 object or CloudWatch stream exported to S3 |
| task execution | ECS/Fargate, Batch, or EC2 |
| secrets | AWS Secrets Manager |
| state snapshots | S3 JSON objects |
| dashboards | Athena/Glue/QuickSight or local parquet later |

For AWS, require:

- S3 bucket with versioning
- KMS encryption
- immutable run object naming
- IAM role per harness
- no credentials in repo
- exact container image digest in manifest

## Readiness Check

Check prepared cells:

```bash
python3 tools/check_pipeline_readiness.py --runs-root runs
```

This verifies the core run files exist and warns if `model_id` is not pinned.

## Current Limits

The repo is now ready for disciplined local experiments and audit-log capture. These pieces are still intentionally future work:

- launching Codex/Hermes/Synth-Max automatically
- live OneDrive/SharePoint state auditing
- live Zoho/Tally state auditing
- real LLM judge routing for judgment criteria
- confidence intervals over large seed batches
- AWS-backed scheduler and immutable S3 run store

Those can be added incrementally without changing the run-cell format above.
