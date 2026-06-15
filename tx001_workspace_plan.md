# TXN-001 Workspace Plan

Task: TXN-001  
Status: Proposed only. No benchmark workspace was created.

## Proposed Workspace Layout

```text
tasks_complete/TXN-001/workspace/
  intake/
    Tally_Cherian_Enterprises_June25.xlsx
    Invoice_Register_A_to_AVA.xlsx
    Tally_Cherian_Enterprises_June25_v2.xlsx        # optional duplicate-stress input
  chart_of_accounts.csv
  prior_postings.csv
  recurring_master.csv
  reimbursement_policy.md
```

## Source Mapping

| Workspace artifact | Proposed source | Transformation required | Status |
|---|---|---|---|
| `intake/Tally_Cherian_Enterprises_June25.xlsx` | `data_company/CFO Services/Other Invoices/Invoices & CN for BaseThesis/Tally_Cherian_Enterprises_June25.xlsx` | Copy into fixture intake folder. | Available |
| `intake/Invoice_Register_A_to_AVA.xlsx` | `data_company/CFO Services/Invoice Register A-to-AVA.xlsx` | Copy into fixture intake folder, preferably with filesystem-safe normalized name. | Available |
| `intake/Tally_Cherian_Enterprises_June25_v2.xlsx` | `data_company/CFO Services/Other Invoices/Invoices & CN for BaseThesis/Tally_Cherian_Enterprises_June25_v2.xlsx` | Optional. Copy only if the task should test duplicate detection across repeated intake workbooks. | Optional |
| `prior_postings.csv` | `data_company/CFO Services/BaseThesis/BaseThesis_Tally_Purchase_June25.xlsx` | Convert `Purchase Bills` sheet to CSV, normalize headers, preserve invoice number, supplier, date, value, GST, tax, and ledger fields. | Available |
| `chart_of_accounts.csv` | `data_company/CFO Services/TB April 25 March 26.xlsx` | Parse trial balance ledger rows into account code/name/type where possible. Supplement with distinct `Purchase ledger` values from invoice and purchase-register workbooks. | Partial |
| `recurring_master.csv` | No candidate source found | Create an empty fixture file with benchmark-required headers only, or mark this component as not applicable for TXN-001. | Missing |
| `reimbursement_policy.md` | No candidate source found | Create a minimal non-operative policy stating that employee reimbursement rules are out of scope for this invoice extraction task, or omit if schema permits. | Missing |

## Proposed Intake Scope

Recommended primary intake:

| Source | Invoice rows | Unique invoice numbers | Role |
|---|---:|---:|---|
| `Tally_Cherian_Enterprises_June25.xlsx` | 29 | 29 | Single-vendor intake with full prior-postings overlap. |
| `Invoice Register A-to-AVA.xlsx` | 39 | 39 | Multi-vendor intake with partial prior-postings overlap. |

Optional duplicate-stress intake:

| Source | Invoice rows | Unique invoice numbers | Role |
|---|---:|---:|---|
| `Tally_Cherian_Enterprises_June25_v2.xlsx` | 29 | 29 | Duplicate of Cherian v1 by invoice-number set. |

If all three intake workbooks are included, the expected raw intake row count is 97 and the expected unique invoice-number count is 68.

## Missing Components and Fallbacks

| Missing or partial component | Impact | Proposed fallback |
|---|---|---|
| Clean `chart_of_accounts.csv` | Ledger mapping can be tested, but account classification may be incomplete or dependent on purchase-ledger labels rather than an authoritative COA. | Derive account names from `TB April 25 March 26.xlsx` and supplement with distinct `Purchase ledger` values from the intake and prior-postings files. Mark ledger mapping ground truth as partial. |
| `recurring_master.csv` | Low impact for TXN-001 if the task remains invoice extraction, duplicate detection, and ledger mapping. Higher impact only if recurring transaction recognition is added. | Provide an empty recurring master with required headers and document it as not applicable. |
| `reimbursement_policy.md` | Low impact because the candidate sources are supplier purchase invoices, not employee reimbursement claims. | Provide a minimal policy file stating that reimbursement rules are out of scope, or exclude if the harness permits missing policy files. |
| Raw PDF or scanned invoices | Limits the task modality. The fixture would evaluate extraction from structured Excel registers, not OCR or visual document parsing. | Proceed only if TXN-001 is intended to accept structured workbook intake. If PDF extraction is required, additional source documents are needed. |

## Construction Recommendation

Use `Tally_Cherian_Enterprises_June25.xlsx` and `Invoice Register A-to-AVA.xlsx` as primary intake. Use `BaseThesis_Tally_Purchase_June25.xlsx` as prior postings. Use `TB April 25 March 26.xlsx` as a partial chart-of-accounts source with ledger-name supplementation from purchase data.

Do not include SAPA financial statement workbooks in the TXN-001 fixture.
