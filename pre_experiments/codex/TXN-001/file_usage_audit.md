# TXN-001 File Usage Audit

Scope: audits observed and inferred use of each TXN-001 workspace file across the Codex run and the Hermes+Codex isolated outputs. This audit distinguishes direct evidence of opening/reading from downstream output references.

Classification definitions:

- READ_AND_USED: there is artifact evidence the file was read/opened and separate evidence it affected output rows or decisions.
- READ_NOT_USED: there is artifact evidence the file was read/opened but no material decision/output dependency was found.
- USED_WITHOUT_EVIDENCE: output rows or decisions depend on the file, but trace/read evidence is absent or only inferred.
- NOT_READ: no observed read/open evidence and no observed output dependency.

Important: the Codex subprocess trace is opaque. For Codex, output rows cite some files, but the outer run intelligence report recorded `file_read_count: 0`. Those cases are classified as USED_WITHOUT_EVIDENCE, not READ_AND_USED.

## Per-file audit

| Workspace file | Hermes classification | Codex classification | Exact evidence opened/read | Exact evidence file influenced a decision | Exact output rows derived | Confidence |
|---|---|---|---|---|---|---:|
| intake/Tally_Cherian_Enterprises_June25.xlsx | READ_AND_USED | USED_WITHOUT_EVIDENCE | Hermes final_summary.md lines 11-13 state workbook/sheet row counts were read; fixture manifests list exact file hash. Codex run_intelligence_report.md lines 215-248 records tool_use_score 0 and file_read_count/workspace recall failure; output rows cite file but no observed read event. | Hermes invoice_extraction_report contains 29 rows with source_file=intake/Tally_Cherian_Enterprises_June25.xlsx; duplicate/exception reports use same source provenance. Codex output CSVs contain 29 rows citing source_file=Tally_Cherian_Enterprises_June25.xlsx. | Hermes invoice rows: 29; sample invoices: AMD2-1171, AMD2-3862, BLR7-10525, BLR7-8177, BLR8-14563; +24 more. Codex cited rows: 29. | 95% for Hermes; 60% for Codex inferred use due to subprocess opacity |
| intake/Invoice_Register_A_to_AVA.xlsx | READ_AND_USED | USED_WITHOUT_EVIDENCE | Hermes final_summary.md lines 11-13 state workbook/sheet row counts were read; fixture manifests list exact file hash. Codex run_intelligence_report.md lines 215-248 records tool_use_score 0 and file_read_count/workspace recall failure; output rows cite file but no observed read event. | Hermes invoice_extraction_report contains 39 rows with source_file=intake/Invoice_Register_A_to_AVA.xlsx; duplicate/exception reports use same source provenance. Codex output CSVs contain 57 rows citing source_file=Invoice_Register_A_to_AVA.xlsx. | Hermes invoice rows: 39; sample invoices: H1253, H0468, ARKB2B-04, ARKB2B-09, FM/0017/25-26; +34 more. Codex cited rows: 57. | 95% for Hermes; 60% for Codex inferred use due to subprocess opacity |
| chart_of_accounts.csv | READ_AND_USED | NOT_READ | Hermes final_summary.md lines 14 and 41-45 state chart_of_accounts.csv was read with 110 rows. Fixture manifests list exact hash. Codex trace has no observed read event. | Hermes ledger_mapping_report rationale says `Purchase ledger supplied in intake and exists in chart_of_accounts.csv` for 68 rows. | Ledger mapping rows influenced: 68; sample invoices: AMD2-1171, AMD2-3862, BLR7-10525, BLR7-8177, BLR8-14563; +63 more. | 90% for Hermes; 85% Codex non-use as no output rationale cites COA |
| prior_postings.csv | READ_AND_USED | USED_WITHOUT_EVIDENCE | Hermes final_summary.md lines 15 and 41-45 state prior_postings.csv was read with 1584 rows and no nonblank purchase_ledger values. Codex output duplicate reasons cite prior_postings, but run trace records no observed file reads. | Hermes duplicate_detection_report uses exact prior-posting evidence for 52 rows. Codex duplicates_skipped.csv uses prior_postings duplicate_reason for 49 rows. | Hermes duplicate rows: 52; sample invoices: AMD2-1171, AMD2-3862, BLR7-10525, BLR7-8177, BLR8-14563; +47 more. Codex duplicate rows: 49. | 95% for Hermes; 65% for Codex inferred use |
| recurring_master.csv | READ_NOT_USED | NOT_READ | Hermes final_summary.md line 16 states recurring_master.csv had 0 rows; method notes say it contains only headers and no usable recurring rules. No Codex read evidence. | No invoice-level decision depends on recurring rules; file is only noted as empty/no usable rules. | No output rows derived from recurring_master.csv. | 90% |
| reimbursement_policy.md | READ_NOT_USED | NOT_READ | Hermes final_summary.md line 17 states reimbursement_policy.md was read; method notes state reimbursement rules were not applicable. No Codex read evidence. | No invoice-level booking, duplicate, ledger, or queue decision depends materially on reimbursement_policy.md. | No output rows derived from reimbursement_policy.md. | 90% |

## Conclusions depending on inferred rather than observed usage

- Any claim that Codex opened/read intake workbooks is inferred from Codex CSV source_file/source_row outputs, not observed in trace.
- Any claim that Codex opened/read prior_postings.csv is inferred from duplicate_reason text, not observed in trace.
- Codex-vs-Hermes comparison conclusions about Codex source usage are therefore scientifically weaker than conclusions about Codex final artifacts.
- Hermes file usage is better supported by generated final_summary/report provenance, but still not an independent low-level file-access trace; it is artifact-level evidence from the Hermes processing run.