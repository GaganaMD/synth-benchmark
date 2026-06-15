# TXN-001 Source Audit

Task: TXN-001  
Service line: CFO  
Category: Financial Close & Controllership Operations  
Subcategory: Document Extraction  
Source folder: `data_company/CFO Services`

This audit inspected the candidate CFO files for use in a future executable TXN-001 fixture. No benchmark task was executed and no benchmark output artifacts were generated.

## Candidate Source Assessment

| Candidate path | File type | Sheets / row counts | Best use | Suitability for TXN-001 | Confidence |
|---|---:|---|---|---|---:|
| `data_company/CFO Services/BaseThesis/BaseThesis_Tally_Purchase_June25.xlsx` | Excel workbook | `Purchase Bills`: 2,566 non-empty rows, 12 columns. Header includes supplier GSTIN, supplier name, invoice number, invoice date, invoice value, GST rate, taxable value, IGST, CGST, SGST, purchase ledger, Tally name. 1,584 non-empty invoice-number cells, 872 unique invoice numbers, 44 duplicate invoice numbers. | `prior_postings.csv` source | Strong prior postings source. It contains the same invoice fields expected for extraction and can support duplicate checks against intake invoices. It is less suitable as primary intake because it appears to be a large historical Tally purchase register with noisy rows and incomplete vendor/tax fields. | 0.90 |
| `data_company/CFO Services/Invoice Register A-to-AVA.xlsx` | Excel workbook | `Sheet1`: 40 non-empty rows, 12 columns. Same purchase-bill style header. 39 data rows, 39 unique invoice numbers, 16 unique vendors. 23 invoice numbers overlap with the BaseThesis purchase register. | Intake source, optional extraction ground truth source | Good structured intake candidate for a small multi-vendor invoice subset. It has all extraction fields needed for GST and ledger mapping. It is not a raw PDF invoice set, so it benchmarks structured document extraction rather than OCR/PDF extraction. | 0.82 |
| `data_company/CFO Services/TB April 25 March 26.xlsx` | Excel workbook | `Sheet1`: 113 non-empty rows, 5 columns. First rows contain company/address/CIN/report headers before ledger-style values. | `chart_of_accounts.csv` source | Partial chart-of-accounts source. It appears to be a trial balance export rather than a clean COA list. It can likely be parsed for ledger/account names, but would need normalization and validation before use as authoritative COA data. | 0.58 |
| `data_company/CFO Services/Other Invoices/Invoices & CN for BaseThesis/Tally_Cherian_Enterprises_June25.xlsx` | Excel workbook | `Purchase Bills`: 30 non-empty rows, 12 columns. Same purchase-bill style header. 29 data rows, 29 unique invoice numbers, one vendor: CHERIAN ENTERPRISES. | Intake source | Strong intake source for TXN-001. It has invoice fields, GST fields, purchase ledger, and vendor identity. All 29 invoice numbers overlap with the BaseThesis purchase register, making it especially useful for duplicate detection against prior postings. | 0.93 |
| `data_company/CFO Services/Other Invoices/Invoices & CN for BaseThesis/Tally_Cherian_Enterprises_June25_v2.xlsx` | Excel workbook | `Purchase Bills`: 30 non-empty rows, 12 columns. Same purchase-bill style header. 29 data rows, 29 unique invoice numbers, one vendor. Invoice-number set exactly matches the non-v2 Cherian workbook. | Duplicate intake variant or unsupported duplicate copy | Useful only if the benchmark should test duplicate handling across intake files. Otherwise it is a duplicate of the non-v2 Cherian workbook and should not be used as an independent source of new invoices. | 0.86 |
| `data_company/CFO Services/SAPA_Financials_2025 Final.xlsx` | Excel workbook | 21 sheets including `Computation`, `BS`, `P&L`, `Cash Flow`, `TB2025`, `Grouping`, `Ageing`, and tax/regulatory note sheets. `TB2025` has 423 non-empty rows; `Grouping` has 341 non-empty rows. | Unsupported for TXN-001 | Financial statement and diligence-style workbook. It may contain accounting context, but it is not an invoice extraction source for TXN-001 and should not be used unless a separate SAPA financial-statement task is created. | 0.24 |
| `data_company/CFO Services/SAPA_Financials_2026.xlsx` | Excel workbook | 3 sheets: `Sheet1` empty, `P&L` with 90 non-empty rows, `Balance Sheet` with 67 non-empty rows. | Unsupported for TXN-001 | Financial statement workbook. Not suitable for invoice extraction, duplicate detection, or GST extraction for this task. | 0.15 |

## Accepted Sources

| Fixture component | Accepted source | Reason |
|---|---|---|
| `intake/` | `Tally_Cherian_Enterprises_June25.xlsx` | Clean 29-row structured invoice subset with all extraction fields and duplicate overlap against prior postings. |
| `intake/` | `Invoice Register A-to-AVA.xlsx` | Clean 39-row structured invoice subset with all extraction fields and multi-vendor coverage. |
| duplicate test input | `Tally_Cherian_Enterprises_June25_v2.xlsx` | Exact invoice-number duplicate of the non-v2 Cherian workbook. Include only if the fixture intentionally tests intra-intake duplicate detection. |
| `prior_postings.csv` | `BaseThesis_Tally_Purchase_June25.xlsx` | Large historical purchase register with overlapping invoices. Best available evidence for prior postings. |
| `chart_of_accounts.csv` | `TB April 25 March 26.xlsx` plus purchase-ledger columns from invoice workbooks | Best available account/ledger source, but requires parsing and cleanup. |

## Rejected Sources

| Source | Rejection reason |
|---|---|
| `SAPA_Financials_2025 Final.xlsx` | Financial statement workbook, not invoice intake. It introduces unrelated diligence/accounting statement context. |
| `SAPA_Financials_2026.xlsx` | Financial statement workbook, not invoice intake. |

## Key Findings

- The available CFO data supports a structured Excel invoice extraction benchmark.
- The data does not provide raw invoice PDFs or scans for OCR-style document extraction.
- Duplicate detection is feasible because the Cherian intake invoices all overlap with the BaseThesis purchase register, and the two Cherian workbooks contain the same invoice-number set.
- Ledger mapping is partially feasible because purchase-ledger fields exist in the invoice workbooks and the trial balance can provide additional ledger names, but there is no clean chart-of-accounts export.
- No recurring master or reimbursement policy source was found in the candidate folder.
