# TXN-001 Run Tabulations

Source run: `runs/codex/TXN-001/seed-0`  
Run ID: `run_cc6ddb1d6abe`  
Experiment ID: `exp_0bad1e5186af`

## Benchmark Completeness

| Field | Value |
| --- | --- |
| execution_complete | false |
| normalization_complete | false |
| grading_complete | false |
| metrics_complete | false |
| artifact_contracts_complete | false |
| intelligence_report_completeness_percent | 0.0 |
| infrastructure_vs_run_status | infrastructure_available_but_run_incomplete |

## Metric Availability Matrix

| Metric | Available | Reason |
| --- | --- | --- |
| precision | NO | grading_result.json missing |
| recall | NO | grading_result.json missing |
| f1 | NO | grading_result.json missing |
| hallucination_rate | NO | canonical_output.json missing |
| unsupported_claim_rate | NO | canonical_output.json missing |
| workflow_hallucination_rate | NO | grading_result.json missing |
| tool_hallucination_rate | NO | tool events missing |
| process_compliance | NO | no tool events recorded |
| state_retention | YES | computed from run artifacts |
| tool_efficiency | NO | tool events missing |
| recovery_rate | NO | tool events missing |
| side_effect_success | YES | computed from run artifacts |
| runtime_seconds | NO | task_complete event missing |

## Artifact Availability Matrix

| Artifact | Present | Validated | Schema Version | Reason |
| --- | --- | --- | --- | --- |
| manifest.json | YES | YES | 1.0 | validated |
| events.jsonl | YES | YES | 1.0 | validated |
| S0.json | YES | YES | 1.0 | validated |
| S1.json | NO | NO |  | missing |
| state_diff.json | YES | YES | 1.0 | validated |
| canonical_output.json | NO | NO |  | missing |
| grading_result.json | NO | NO |  | missing |

## Run Metadata

| Field | Value |
| --- | --- |
| task_id | TXN-001 |
| service_line | CFO |
| category | Transaction Processing |
| subcategory | Document extraction |
| complexity | Hard |
| model_id | codex-cli-current |
| harness_id | codex |
| seed | 0 |
| dataset_version | v10-revised-labels |
| fixture_version | v10-revised-labels__TXN-001__2f601427ad6d1822 |
| environment_version | env_12ff104b9e61dd7f |
| git_commit | 189928559f0009ab5c867d96ad7022c209465a47 |

## Workspace Coverage

| Field | Value |
| --- | --- |
| files_discovered | 5 |
| files_read | 0 |
| files_ignored | 5 |
| files_written | 0 |
| workspace_file_recall | 0.0 |
| workspace_file_precision | unavailable: no file_read events recorded |

## Document Influence Table

| Document | Read? | Used? | Importance Score | Why Used? |
| --- | --- | --- | --- | --- |
| chart_of_accounts.csv/README.md | NO | NO | 0.0 | Available but no trace evidence of use. |
| intake/README.md | NO | NO | 0.0 | Available but no trace evidence of use. |
| prior_postings.csv/README.md | NO | NO | 0.0 | Available but no trace evidence of use. |
| recurring_master.csv/README.md | NO | NO | 0.0 | Available but no trace evidence of use. |
| reimbursement_policy.md/README.md | NO | NO | 0.0 | Available but no trace evidence of use. |

## Comparison Ready Fields

| Field | Value |
| --- | --- |
| documents_read | 0 |
| documents_used | 0 |
| tool_calls | 0 |
| tool_failures | 0 |
| tool_retries | 0 |
| reasoning_steps | unavailable |
| verification_events | 0 |
| state_changes | 0 |
| runtime_seconds | 0.0 |
