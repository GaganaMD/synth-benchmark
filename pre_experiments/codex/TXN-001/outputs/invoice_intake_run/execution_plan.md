# Vendor Invoice Intake Execution Plan

## Scope discovery result

Expected current-workspace inputs from user prompt:
- intake/
- chart_of_accounts.csv
- recurring_master.csv
- reimbursement_policy.md
- prior_postings.csv

Discovery in current working directory `/Users/basethesis/Desktop/synth-benchmark` found that none of those expected paths exist as current-workspace files/directories.

A search of repository contents found only placeholder benchmark workspaces under `tasks_complete/TXN-*` and `immutable_inputs/v10-revised-labels__TXN-001__2f601427ad6d1822/workspace`; each contains README.md placeholder files stating that BI must drop task-specific input assets before live runs. These are not invoice/supporting source records.

## Processing controls

1. Treat only the user-specified workspace paths as in-scope if present in the live working directory.
2. Do not process unrelated repository files or historical completed-task artifacts as invoices.
3. If expected inputs are absent, surface a blocking exception rather than fabricate invoice records.
4. Maintain a file manifest with existence/status for every expected source.
5. Parse every in-scope invoice/supporting record if any are present.
6. Extract invoice number, date, vendor, GSTIN, taxable value, CGST, SGST, IGST, purchase ledger, confidence, action.
7. Determine GST/TDS treatment from extracted data and reference files where available.
8. Map ledgers using chart_of_accounts and supporting references where available.
9. Detect duplicates against current intake and prior_postings where available.
10. Queue exceptions for review; auto-post only complete, internally consistent, non-duplicate records with adequate confidence.
11. Reconcile document counts and extracted totals before finalization.

## Run decision

Because no live in-scope source files are available, processing proceeds in controlled zero-record mode:
- no invoices extracted
- no auto-postings created
- missing-source exceptions reported for each mandatory workspace input
- reconciliation confirms zero processed invoices and zero posted invoices
