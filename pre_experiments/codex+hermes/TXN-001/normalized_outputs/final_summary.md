# TXN-001 Vendor Invoice Intake Final Summary

## Workspace inventory
- chart_of_accounts.csv (10076 bytes, sha256=faa5d546dcae498f0aeaf5b0bc3a5d077f55fd1e74378e987e736e55798acf31)
- intake/Invoice_Register_A_to_AVA.xlsx (10114 bytes, sha256=86bf4b8c6dd32b5dd4b101dabd1dfc93305b51cf65e49d94a73ac4dfc91d2d5f)
- intake/Tally_Cherian_Enterprises_June25.xlsx (8743 bytes, sha256=7aae9f40724a0105b2ff2f74b5a1cb9a467441bd0e25b1c48b005498d9039cb9)
- prior_postings.csv (86408 bytes, sha256=77ba69d76e9d55c3674f60c988105aa32dbf1578b631090b6f0d6b9130606084)
- recurring_master.csv (67 bytes, sha256=8559c43c546cec0bcf70390a60e22787734fae26dcaf62b1951b7ba0cd192b4f)
- reimbursement_policy.md (262 bytes, sha256=d5884fce36c00fe01884a861330fc11b69db0f773ad3d113e3e85484433fd2c3)

## Files and sheets read
- intake/Tally_Cherian_Enterprises_June25.xlsx / Purchase Bills: 29 rows, columns=GSTIN of supplier, Trade/Legal name, Invoice number, Invoice Date, Invoice Value (₹), GST Rate, Taxable Value (₹), Integrated Tax (₹), Central Tax (₹), State/UT Tax (₹), Purchase ledger, Name as per Tally
- intake/Invoice_Register_A_to_AVA.xlsx / Sheet1: 39 rows, columns=GSTIN of supplier, Trade/Legal name, Invoice number, Invoice Date, Invoice Value (₹), GST Rate, Taxable Value (₹), Integrated Tax (₹), Central Tax (₹), State/UT Tax (₹), Purchase ledger, Name as per Tally
- chart_of_accounts.csv: 110 rows
- prior_postings.csv: 1584 rows
- recurring_master.csv: 0 rows
- reimbursement_policy.md: read

## Final Summary
- invoices processed: 68
- duplicates detected: 52
- exceptions identified: 68
- records queued for review: 68
- records approved for posting: 0

## Totals
- invoice_value_total: 3257156.21
- taxable_value_total: 2863664.75
- cgst_total: 109747.60
- sgst_total: 109747.60
- igst_total: 175495.14

## Reconciliation
- input_invoice_rows: 68
- report_invoice_rows: 68
- row_count_reconciled: True
- decision_count_reconciled: True
- duplicate_report_rows_reconciled: True
- ledger_report_rows_reconciled: True

## Method notes
- recurring_master.csv contains only headers and no usable recurring rules.
- reimbursement_policy.md states reimbursement rules are not applicable to this fixture.
- prior_postings.csv contains prior invoice numbers but no nonblank purchase_ledger values; ledger inference from history is therefore limited.
- No TDS amount/rule exists in the workspace; TDS is not fabricated and remains a review checkpoint where applicable.

## Output files
- invoice_extraction_report: experiments/hermes_codex/TXN-001/normalized_outputs/invoice_extraction_report.csv
- duplicate_detection_report: experiments/hermes_codex/TXN-001/normalized_outputs/duplicate_detection_report.csv
- ledger_mapping_report: experiments/hermes_codex/TXN-001/normalized_outputs/ledger_mapping_report.csv
- exception_report: experiments/hermes_codex/TXN-001/normalized_outputs/exception_report.csv
- final_summary.json: experiments/hermes_codex/TXN-001/normalized_outputs/final_summary.json
