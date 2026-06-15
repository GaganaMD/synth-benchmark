# TXN-001 Queue Counterfactual Analysis

Scope: independent counterfactual review of the 68 queued invoices using existing normalized outputs only. This analysis did not rerun the benchmark, did not reread source invoice workbooks, and did not modify normalized_outputs/.

Evidence files used:
- experiments/hermes_codex/TXN-001/normalized_outputs/invoice_extraction_report.csv
- experiments/hermes_codex/TXN-001/normalized_outputs/duplicate_detection_report.csv
- experiments/hermes_codex/TXN-001/normalized_outputs/ledger_mapping_report.csv
- experiments/hermes_codex/TXN-001/normalized_outputs/exception_report.csv

## Counterfactual method

This is not a restatement of the prior queue decision. I classified each queued record based on whether a reasonable finance analyst, seeing only the existing normalized outputs, could still post the invoice after applying professional judgment.

Severity definitions:
- hard: duplicate evidence, source value/tax conflict, or missing required non-ledger invoice fields; posting would be inappropriate without resolution.
- medium: missing or ambiguous purchase ledger only; a finance analyst could potentially post after manually selecting/confirming a ledger, but it is not a safe unattended auto-post.
- low: warning-only / low-confidence-only issue; generally postable if core fields are complete. No low-severity-only records were found here.

Counterfactual confidence is the audit confidence in the classification, not the original extraction confidence.

## Required metrics

- total queued invoices reviewed: 68
- auto_post_candidates: 16
- queue_candidates: 52
- high_confidence_posts: 0
- high_confidence_queues: 52

## Severity counts

- hard: 52
- medium: 16
- low: 0

## Interpretation

Counterfactually, 16 records are auto-post candidates in the sense that a reasonable finance analyst could still post them after selecting/confirming a ledger. They are not high-confidence unattended auto-posts because the existing outputs show missing or ambiguous Purchase Ledger evidence.

The remaining 52 records are queue candidates because the existing outputs show duplicate evidence and/or a source-value conflict. One duplicate record also has an internal invoice-value/tax conflict.

## Record-level counterfactual review

| # | Invoice | Source row | Vendor | Original confidence | Exact blocker | Severity | Could analyst still post? | Counterfactual classification | Counterfactual confidence |
|---:|---|---:|---|---:|---|---|---|---|---:|
| 1 | AMD2-1171 | 2 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 2 | AMD2-3862 | 3 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 3 | BLR7-10525 | 4 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 4 | BLR7-8177 | 5 | CHERIAN ENTERPRISES | 0.45 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (2 prior row(s)) \| source value/tax conflict: invoice_value 4301.46 differs from taxable+tax components 5798.46 | hard | No | queue_candidate | 95% |
| 5 | BLR8-14563 | 6 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 6 | BLR8-390 | 7 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 7 | BLR8-391 | 8 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 8 | BLR8-6425 | 9 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 9 | BOM5-13884 | 10 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 10 | BOM5-5782 | 11 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 11 | BOM7-8226 | 12 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 12 | CCX1-1638 | 13 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 13 | CJB1-10077 | 14 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 14 | CJB1-2466 | 15 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 15 | CJB1-3280 | 16 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 16 | CJB1-8340 | 17 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 17 | DED4-3178 | 18 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 18 | DED4-3179 | 19 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 19 | GAX1-506 | 20 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 20 | GAX1-507 | 21 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 21 | HYD8-1937 | 22 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 22 | HYD8-441 | 23 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 23 | HYD8-442 | 24 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 24 | LKO1-1270 | 25 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 25 | MAA4-7121 | 26 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 26 | MAA4-7123 | 27 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 27 | MAA4-8550 | 28 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 28 | TWCX-1454 | 29 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 29 | TWCX-5755 | 30 | CHERIAN ENTERPRISES | 0.65 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) | hard | No | queue_candidate | 88% |
| 30 | H1253 | 2 | A & A LED LIGHTING CORPORATION | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 31 | H0468 | 3 | A & A LED LIGHTING CORPORATION | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 32 | ARKB2B-04 | 4 | ARKIDAM DEVELOPERS PRIVATE LIMITED | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 33 | ARKB2B-09 | 5 | ARKIDAM DEVELOPERS PRIVATE LIMITED | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 34 | FM/0017/25-26 | 6 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 35 | FM/0125/25-26 | 7 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 36 | FM/0244/25-26 | 8 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 37 | FM/0361/25-26 | 9 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 38 | FM/0479/25-26 | 10 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 39 | FM/0606/25-26 | 11 | ABAD PROPERTY MANAGEMENT SERVICES PVT LTD | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 40 | 17991 | 12 | Actartly Technology Private Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 41 | 20188 | 13 | Actartly Technology Private Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 42 | 21770 | 14 | Actartly Technology Private Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 43 | 24021 | 15 | Actartly Technology Private Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 44 | 25802 | 16 | Actartly Technology Private Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 45 | ACT/25-26/05/653 | 17 | Advantage Club Technologies Private Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 46 | IN-719 | 18 | AERIAL INFOTECH | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 47 | 31 | 19 | AHAANA KRISHNA | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 48 | 46 | 20 | AHAANA KRISHNA | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 49 | IN-1717 | 21 | Akaay Enterprises | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 50 | XHRC-122091 | 22 | ALPINO HEALTH FOODS PRIVATE LIMITED | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 51 | XHRC-153772 | 23 | ALPINO HEALTH FOODS PRIVATE LIMITED | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 52 | AC/2025-2026/316 | 24 | Analytics Cloud | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 53 | AC/2025-2026/383 | 25 | Analytics Cloud | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 54 | AC/2025-2026/444 | 26 | Analytics Cloud | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 55 | AC/2025-2026/516 | 27 | Analytics Cloud | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 56 | LIN/28/25-26 | 28 | Amyka Healthcare Private Limited (Anvka) | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 57 | CJB1-2115 | 29 | ARAVIND BROADVIEW CONSTRUCTIONS AND HOLDINGS PVT LTD | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 58 | AC/197 | 30 | ARIHANT CREATIONS | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 59 | AC/216 | 31 | ARIHANT CREATIONS | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 60 | AC/222 | 32 | ARIHANT CREATIONS | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 61 | 3212500001380880 | 33 | Asianet Satellite Communications Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 62 | 3212500002379690 | 34 | Asianet Satellite Communications Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 63 | 3212500002803520 | 35 | Asianet Satellite Communications Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 64 | 3212500003145990 | 36 | Asianet Satellite Communications Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 65 | 3212500003445710 | 37 | Asianet Satellite Communications Limited | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (1 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 66 | 3212500003746450 | 38 | Asianet Satellite Communications Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |
| 67 | HYD8-8218 | 39 | Radiant Consumer Appliances Pvt Ltd | 0.15 | prior-posting duplicate: exact invoice_number match in prior_postings.csv (2 prior row(s)) \| missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | hard | No | queue_candidate | 90% |
| 68 | HYD8-2174 | 40 | AVA International Private Limited | 0.50 | missing/ambiguous purchase ledger: source Purchase Ledger is blank/ambiguous and existing ledger report says no reliable historical ledger inference was available | medium | Yes, but only after analyst ledger selection/confirmation; not safe as unattended auto-post | auto_post_candidate | 62% |

## Bottom line

Independent counterfactual view: not all queued records are equally severe. 52 are true queue candidates due to hard duplicate/conflict blockers. 16 are medium-severity ledger-only cases where a reasonable finance analyst could still post after manual ledger selection, but they should not be counted as high-confidence unattended auto-posts from the existing outputs alone.
