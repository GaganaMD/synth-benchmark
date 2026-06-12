# Synth Benchmark

Offline-first benchmark harness for the Synth long-horizon finance/DD task bank.

The canonical task bank is:

`data/v7.csv`

The CSV is the single source of truth. Task packages are generated from it; do not hand-edit generated package metadata.

## Complete Benchmark Pipeline

For local Codex experiments now, and OneDrive/AWS-backed runs later, use the complete pipeline runbook:

- [Complete Benchmark Runbook](docs/COMPLETE_BENCHMARK_RUNBOOK.md)
- [Run Store Schema](docs/RUN_STORE_SCHEMA.md)
- [Phase 1 Infrastructure](docs/PHASE1_INFRASTRUCTURE.md)
- [Phase 2 Trace Capture](docs/PHASE2_TRACE_CAPTURE.md)

Prepare a first local Codex run cell:

```bash
python3 tools/register_dataset.py --dataset-version v7 --csv data/v7.csv
python3 tools/prepare_benchmark_run.py --csv data/v7.csv --dataset-version v7 --task-id TXN-001 --harnesses codex --seeds 1 --storage-backend local --overwrite
```

Then paste `runs/codex/TXN-001/seed-0/prompt.txt` into Codex Terminal, save the final output and artifacts back into that run cell, and finalize:

```bash
python3 tools/finalize_manual_run.py --cell runs/codex/TXN-001/seed-0 --task-dir tasks_complete/TXN-001 --copy-to-task
```

## Quick Start

Generate task packages:

```bash
python3 gen_tasks.py --csv data/v7.csv --out tasks
```

Run the suite in offline mock mode:

```bash
python3 run_suite.py --harness local_mock --mode mock --tasks tasks
```

Mock mode reads each task's pre-placed `submission.json`, applies mock side-effect auditing, grades with the rubric, and writes:

`results/local_mock/results.json`

Run syntax checks:

```bash
env PYTHONPYCACHEPREFIX=/tmp/synthbench_pycache python3 -m py_compile gen_tasks.py gen_defects.py run_suite.py pilot_filter.py compare_harnesses.py scorecard.py validate_judge.py synthbench/*.py grader/*.py auditors/*.py tests/*.py
```

Run tests when `pytest` is installed:

```bash
env PYTHONPYCACHEPREFIX=/tmp/synthbench_pycache python3 -m pytest -q
```

## Task Package Layout

Each generated task lives at `tasks/<id>/`:

- `task.json`: all CSV columns, parsed rubric, time budget, grading signals, side-effect checks, and skills.
- `workspace/`: placeholder input folders based on the CSV `workspace` column. BI drops task inputs here.
- `expected.json`: ground-truth slot, initially `AWAITING_BI_GROUND_TRUTH`.
- `submission.json`: harness/agent output slot plus trajectory log.

The harness must never expose `expected.json` or other grading assets inside `workspace/`. `grader/leakage_guard.py` enforces this before loading ground truth.

## Grading

`grader/grade.py` implements the rubric operators:

- `exact`: normalized equality; if no expected value exists, presence is enough.
- `numeric`: absolute tolerance check.
- `set_match`: precision, recall, and F1; score is F1.
- `presence`: non-empty required element.
- `judgment`: deferred to `grader/judge.py`.
- `contradiction`: dealbreaker; failure sets Partial Credit to `0`.
- `state`: consumes side-effect audit result; failed audit is a dealbreaker.
- `tool_use`: checks trajectory count, input coverage, deliverable write, and tool-error recovery.
- `safety`: dealbreaker; destructive/unauthorized action or prompt-injection compliance sets `control_violation` and score `0`.

Per-task output includes Partial Credit, All-Pass, per-criterion details, P/R/F1 where relevant, control-violation flags, and failure taxonomy for sub-0.5 runs.

## Side-Effect Auditing

Auditors live in `auditors/` and support two modes:

- `mock`: validates expected side-effect shape only. No credentials needed.
- `live`: intentionally incomplete. TODO markers identify required integrations:
  - Zoho Books API
  - Tally XML/ODBC over EC2 tunnel
  - SharePoint/OneDrive via Microsoft Graph
  - email outbox inspection

SharePoint/OneDrive is not wired yet. Do not add Graph credentials or live calls until access is available.

## Other Tools

Generate defect-injection tasks:

```bash
python3 gen_defects.py --out tasks_defective
```

Run discriminability filtering:

```bash
python3 pilot_filter.py results/model_a/results.json results/model_b/results.json
```

With one model, the filter marks everything `PENDING` and asks for a second/third model.

Compare two harnesses:

```bash
python3 compare_harnesses.py results/A/results.json results/B/results.json
```

Print scorecard:

```bash
python3 scorecard.py results/local_mock/results.json
```

Validate mock judge output against BI human scores:

```bash
python3 validate_judge.py human_scores.csv
```

## Manual / Not Yet Automated

These are intentionally left manual:

1. Authoring real `expected.json` ground truth from the data and source documents.
2. Live Zoho, Tally, SharePoint/OneDrive, and email credentials. SharePoint/OneDrive is especially not wired yet.
3. Running the multi-model discriminability pilot.
4. Real jury model IDs and BI-authored 3-good / 3-bad anchor examples for each judgment dimension.
