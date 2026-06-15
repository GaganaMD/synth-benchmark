# TXN-001 Ground Truth Report

Task: TXN-001  
Fixture modality: structured Excel  
Optional Cherian v2 workbook included: no

## Sources

| Role | Source |
|---|---|
| Intake | `data_company/CFO Services/Other Invoices/Invoices & CN for BaseThesis/Tally_Cherian_Enterprises_June25.xlsx` |
| Intake | `data_company/CFO Services/Invoice Register A-to-AVA.xlsx` |
| Prior postings | `data_company/CFO Services/BaseThesis/BaseThesis_Tally_Purchase_June25.xlsx` |
| Chart of accounts | `data_company/CFO Services/TB April 25 March 26.xlsx` plus distinct purchase-ledger values |

## Generated Ground Truth

| Artifact | Rows | Derivation |
|---|---:|---|
| `ground_truth_extraction.csv` | 68 | Normalized invoice fields copied from approved intake workbooks. |
| `ground_truth_duplicates.csv` | 68 | `duplicate_flag=TRUE` when invoice number appears in prior postings or repeats within intake. |
| `ground_truth_ledger_mapping.csv` | 68 | `expected_ledger` copied from intake `Purchase ledger`. |

## Coverage

| Metric | Value |
|---|---:|
| Intake workbooks | 2 |
| Intake invoice rows | 68 |
| Unique intake invoice numbers | 68 |
| Prior posting rows | 1584 |
| Duplicate rows flagged | 52 |
| Chart-of-account candidate rows | 110 |

## Notes

- The fixture intentionally uses structured Excel workbooks, not invoice PDFs/scans.
- The optional Cherian v2 duplicate-stress workbook was not included in this canonical run to keep intake scope to the two approved primary workbooks.
- The reimbursement policy and recurring master are schema-compatible placeholders because no source documents were available for those components and they are not material to supplier invoice extraction.
