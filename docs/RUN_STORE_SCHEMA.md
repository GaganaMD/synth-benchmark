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
| `experiment_id` | Matrix-level experiment identifier |
| `run_id` | Unique prepared run-cell identifier |
| `cell_id` | `<harness>::<task_id>::seed-<n>` |
| `task_id` | Benchmark task ID |
| `harness` | `codex`, `codex_hermes`, or `synth_max` |
| `harness_id` | Stable harness ID used by registries |
| `harness_path` | Local path or identifier for the runner |
| `model_id` | Exact dated model/runtime ID |
| `seed` | Repeat seed |
| `dataset_version` | Registered dataset version |
| `fixture_version` | Registered immutable fixture version |
| `environment_version` | Deterministic environment fingerprint |
| `temperature` | Sampling temperature, usually `0` |
| `csv_path` | Source task CSV |
| `task_dir` | Generated task package |
| `workspace_dir` | Workspace visible to the agent |
| `storage_backend` | `local`, `onedrive`, or `aws` |
| `repo.commit` | Git commit at preparation time |
| `git_commit` | Top-level git commit shortcut |
| `workspace_hash` | Content hash inventory of the workspace |
| `config_snapshot` | Relevant benchmark configuration |

The manifest also embeds the full `dataset` and `fixture` records so a future replay can validate registry drift.

## `events.jsonl`

One canonical JSON object per line. Required event fields:

| Field | Meaning |
| --- | --- |
| `event_id` | Unique event ID |
| `experiment_id` | Experiment registry ID |
| `run_id` | Run registry ID |
| `task_id` | Benchmark task ID |
| `timestamp` | UTC timestamp |
| `event_type` | Canonical event type |

Supported event types are documented in [Phase 2 Trace Capture](PHASE2_TRACE_CAPTURE.md).

Example:

```json
{"event_id":"evt_...","experiment_id":"exp_...","run_id":"run_...","task_id":"TXN-001","timestamp":"2026-06-12T07:00:00Z","event_type":"tool_call","tool_name":"shell","arguments":{"cmd":"ls workspace"},"success":true,"latency_ms":120}
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

For local-only runs this records the filesystem/mock-state S1-S0 diff. For OneDrive, Zoho, Tally, or AWS-backed runs, extend the same schema with live system objects.

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

Phase 3 details are documented in [Phase 3 State Diff and Side Effect Auditing](PHASE3_STATE_DIFF_AUDIT.md).

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

## `canonical_output.json`

Phase 5 writes adapter-independent normalized output here. Future graders should consume this file instead of adapter-specific raw response files.

See [Phase 5 Output Normalization](PHASE5_OUTPUT_NORMALIZATION.md).
