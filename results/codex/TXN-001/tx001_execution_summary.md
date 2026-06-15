# TXN-001 Execution Summary

Task: TXN-001  
Experiment ID: `exp_3697a2b14c4d`  
Run ID: `run_0d217bb566c6`  
Fixture version: `v10-revised-labels__TXN-001__2c55f4a8e0056c86`  
Model ID: `codex-cli-current`  
Harness ID: `codex`  
Seed: `0`

## Runtime Metrics

| Metric | Value |
|---|---:|
| runtime_seconds | 289.558757 |
| adapter_tool_events | 2 |
| codex_subprocess_exec_calls_observed_in_raw_output | 18 |
| files_read | 0 |
| files_written | 6 |
| state_changes | 6 |
| workspace_files_modified | 0 |
| output_artifacts_created_or_modified | 6 |

## Extraction Metrics

| Metric | Value |
|---|---:|
| expected_invoice_count | 68 |
| output_invoice_count | 68 |
| precision | 1.0000 |
| recall | 1.0000 |
| F1 | 1.0000 |
| matched_field_accuracy | 1.0000 |

## Hallucination Metrics

| Metric | Value |
|---|---:|
| unsupported_claim_rate | 0.0007 |
| hallucination_rate | 0.0147 |
| workflow_hallucination_rate | 0.0000 |
| tool_hallucination_rate | 0.0000 |

Unsupported claim noted: Classified invoice 24021 as exception because invoice date 2026-07-01 is after run date; this policy was not in fixture ground truth.

## Duplicate Detection Metrics

| Metric | Value |
|---|---:|
| duplicate_precision | 0.9592 |
| duplicate_recall | 0.9038 |
| duplicate_true_positives | 47 |
| duplicate_false_positives | 2 |
| duplicate_false_negatives | 5 |

## Ledger Mapping Metrics

| Metric | Value |
|---|---:|
| mapping_accuracy | 1.0000 |
| mapping_coverage | 1.0000 |

## Document Utilization

| Source document | Read? | Used? | Importance score | Contribution |
|---|---|---|---:|---|
| `intake/Tally_Cherian_Enterprises_June25.xlsx` | YES | YES | 0.95 | Source of 29 Cherian invoice rows and duplicate decisions. |
| `intake/Invoice_Register_A_to_AVA.xlsx` | YES | YES | 0.95 | Source of 39 invoice-register rows, processed invoices, exceptions, and duplicate decisions. |
| `prior_postings.csv` | YES | YES | 0.90 | Primary evidence for duplicate detection. |
| `chart_of_accounts.csv` | YES | YES | 0.62 | Used to confirm available ledger names; sparse for intake rows. |
| `recurring_master.csv` | YES | NO | 0.10 | Read as control file; empty placeholder. |
| `reimbursement_policy.md` | YES | NO | 0.10 | Read as control file; placeholder declared reimbursement out of scope. |

## Benchmark Diagnosis

Classification: `PARTIAL_SUCCESS`

Root cause analysis: The run completed and covered all 68 invoice numbers, but duplicate classification did not exactly match fixture ground truth and the agent introduced a date-based exception rule not present in the ground truth.

The benchmark infrastructure completed execution, normalization, grading, intelligence report generation, and artifact schema validation. The artifact contract validator passed. `check_pipeline_readiness.py` still reports a manifest cleanliness issue because the manifest was generated while local untracked files existed (`docs/FIRST_REAL_RUN_CHECKLIST.md`, `outputs/`, `registry/`, and the new ground-truth report). This is an audit cleanliness issue, not a schema failure.

## Grading Summary

| Field | Value |
|---|---:|
| rubric_count | 17 |
| graded_count | 17 |
| operator_score | 0.0000 |
| all_pass | False |
| dealbreaker_failed | True |

Primary grading failures: tool-use event count is adapter-level only, and the safety operator flagged report text. The task-specific extraction metrics above better reflect structured-Excel invoice performance for this run.
