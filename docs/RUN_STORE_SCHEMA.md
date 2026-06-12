# Run Store Schema

Every benchmark cell must be reconstructable from files in its run directory.

```text
runs/<harness>/<task_id>/seed-<n>/
```

## `manifest.json`

Required fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Manifest schema version |
| `cell_id` | `<harness>::<task_id>::seed-<n>` |
| `task_id` | Benchmark task ID |
| `harness` | `codex`, `codex_hermes`, or `synth_max` |
| `harness_path` | Local path or identifier for the runner |
| `model_id` | Exact dated model/runtime ID |
| `seed` | Repeat seed |
| `temperature` | Sampling temperature, usually `0` |
| `csv_path` | Source task CSV |
| `task_dir` | Generated task package |
| `workspace_dir` | Workspace visible to the agent |
| `storage_backend` | `local`, `onedrive`, or `aws` |
| `repo.commit` | Git commit at preparation time |
| `workspace_hash` | Content hash inventory of the workspace |
| `config_snapshot` | Relevant benchmark configuration |

## `events.jsonl`

One JSON object per line. Required event fields:

| Field | Meaning |
| --- | --- |
| `ts` | UTC timestamp |
| `event_type` | `plan`, `tool_call`, `observation`, `self_verify`, `final`, `error`, `note` |
| `tool` | Tool or subsystem name |
| `action` | What happened |
| `input` | Path, query, API endpoint, or other input |
| `success` | Boolean |
| `error` | Error text when applicable |
| `metadata` | Optional structured extras |

Example:

```json
{"ts":"2026-06-12T07:00:00Z","event_type":"tool_call","tool":"shell","action":"read all workspace inputs","input":"tasks_complete/TXN-001/workspace","success":true,"error":null}
```

## `submission.json`

This is the normalized record consumed by `run_suite.py`.

Required fields:

| Field | Meaning |
| --- | --- |
| `task_id` | Benchmark task ID |
| `status` | `COMPLETED`, `FAILED`, `TIMED_OUT`, or `AWAITING_AGENT_OUTPUT` |
| `final_output` | Agent's final answer |
| `answers` | Structured answer fields where available |
| `deliverables` | Paths under the run cell |
| `trajectory.tool_calls` | Tool events used for tool-use grading |
| `trajectory.read_all_inputs` | Whether the agent read all relevant inputs |
| `trajectory.wrote_deliverable` | Whether it wrote a required artifact |
| `trajectory.recovered_from_tool_error` | Whether failed calls were recovered |
| `trajectory.self_verified` | Whether it performed tie-out/self-checks |
| `control_violation` | Safety/destructive-action flag |
| `_no_contradiction` | False if final output conflicts with evidence |

## `state/state_diff.json`

For local-only runs this may remain a placeholder. For OneDrive, Zoho, Tally, or AWS-backed runs, populate it with S1-S0 changes.

Recommended fields:

| Field | Meaning |
| --- | --- |
| `status` | `NOT_CAPTURED`, `CAPTURED`, or `FAILED` |
| `backend` | `local`, `onedrive`, `zoho`, `tally`, `aws` |
| `baseline_ref` | S0 snapshot path/hash |
| `final_ref` | S1 snapshot path/hash |
| `changes` | List of created/updated/deleted objects |
| `landed_correct` | Count of correct landed side effects |
| `claimed_effects` | Count of claimed side effects |
| `control_violation` | True if unsafe/destructive action occurred |

## Artifacts

Store agent-created files under:

```text
artifacts/
```

Use stable names such as:

```text
artifacts/run_summary.csv
artifacts/exceptions.csv
artifacts/final_report.md
```

When `tools/finalize_manual_run.py --copy-to-task` is used, artifacts are also copied into:

```text
tasks_complete/<TASK_ID>/results/
```
