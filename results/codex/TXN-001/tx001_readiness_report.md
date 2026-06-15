# TXN-001 Readiness Report

Task: TXN-001  
Status: Preparation complete; benchmark execution not started.

## Ground Truth Readiness

| Ground truth artifact | Readiness | Reason |
|---|---|---|
| `ground_truth_extraction.csv` | READY for structured Excel extraction; PARTIAL for PDF/OCR extraction | The proposed intake workbooks contain supplier GSTIN, supplier name, invoice number, invoice date, invoice value, GST rate, taxable value, IGST, CGST, SGST, purchase ledger, and Tally name. This is enough for row-level structured extraction ground truth. It is not enough to validate extraction from raw invoice PDFs or scans. |
| `ground_truth_duplicates.csv` | READY | Duplicate evidence is strong. The Cherian intake invoice numbers all overlap with the BaseThesis prior postings register. The two Cherian workbooks also have identical invoice-number sets, enabling intra-intake duplicate testing if both are included. `Invoice Register A-to-AVA.xlsx` has 23 invoice-number overlaps with the BaseThesis prior postings register. |
| `ground_truth_ledger_mapping.csv` | PARTIAL | Purchase-ledger fields exist in the intake and prior-postings workbooks, and `TB April 25 March 26.xlsx` can provide ledger context. However, no clean chart-of-accounts export was found, and the trial balance requires parsing and normalization. |

## Benchmark Readiness

| Metric | Value |
|---|---|
| workspace_readiness_score | 0.72 |
| readiness classification | PARTIAL |
| expected primary intake document count | 2 structured Excel workbooks |
| optional duplicate-stress document count | 1 additional duplicate Excel workbook |
| expected raw invoice count, primary intake only | 68 |
| expected raw invoice count, with duplicate-stress workbook | 97 |
| expected unique invoice-number count, with duplicate-stress workbook | 68 |
| duplicate detection feasibility | HIGH |
| ledger mapping feasibility | MEDIUM / PARTIAL |
| GST extraction feasibility | HIGH for structured Excel fields |

## Score Rationale

The score is partial rather than ready because the core transaction data exists, but two benchmark fixture components are missing and one is only partially available.

| Component | Availability | Contribution |
|---|---|---|
| Intake documents | Available | Strong structured invoice sources exist. |
| Prior postings | Available | Strong duplicate-detection reference exists. |
| Chart of accounts | Partial | Trial balance exists but needs parsing and may not represent a clean COA. |
| Recurring master | Missing | Not material for basic invoice extraction, but required if the benchmark schema expects it. |
| Reimbursement policy | Missing | Not material for supplier invoice extraction, but required if the benchmark schema expects it. |
| Raw invoice PDFs/scans | Missing | Material only if TXN-001 is intended to benchmark OCR or visual document extraction. |

## Execution Recommendation

Do not execute TXN-001 until the operator confirms the fixture modality:

- If structured Excel extraction is acceptable, the fixture can be constructed from the accepted sources with documented fallbacks.
- If PDF/OCR invoice extraction is required, the current data is insufficient and additional invoice documents are needed.

Operator approval is required before creating the executable workspace or running the benchmark.
