# TXN-001 Ground Truth Quality Audit

Scope: audits ground truth quality using existing TXN-001 ground_truth files and existing normalized outputs only. No raw invoice reprocessing was performed.

## Summary score

- ground_truth_confidence_score: 54/100

Rationale: extraction and duplicate labels are useful but incomplete/partly ambiguous; ledger labels contain a systemic contradiction for blank-ledger rows; queue labels are missing entirely.

## Category audit

| Category | Label file / source | Record count | Sample records | Consistency | Contradictions | Missing labels | Ambiguous labels | Confidence |
|---|---|---:|---|---|---|---|---|---:|
| extraction labels | ground_truth_extraction.csv | 68 | [{'invoice_number': 'AMD2-1171', 'vendor_name': 'CHERIAN ENTERPRISES', 'taxable_value': '3246.10', 'cgst': '0.00', 'sgst': '0.00', 'igst': '584.30', 'purchase_ledger': 'Manufacturing vendor'}, {'invoice_number': 'AMD2-3862', 'vendor_name': 'CHERIAN ENTERPRISES', 'taxable_value': '3758.04', 'cgst': '0.00', 'sgst': '0.00', 'igst': '676.45', 'purchase_ledger': 'Manufacturing vendor'}, {'invoice_number': 'BLR7-10525', 'vendor_name': 'CHERIAN ENTERPRISES', 'taxable_value': '3645.29', 'cgst': '0.00', 'sgst': '0.00', 'igst': '656.16', 'purchase_ledger': 'Manufacturing vendor'}, {'invoice_number': 'BLR7-8177', 'vendor_name': 'CHERIAN ENTERPRISES', 'taxable_value': '4913.94', 'cgst': '0.00', 'sgst': '0.00', 'igst': '884.52', 'purchase_ledger': 'Manufacturing vendor'}, {'invoice_number': 'BLR8-14563', 'vendor_name': 'CHERIAN ENTERPRISES', 'taxable_value': '3645.29', 'cgst': '0.00', 'sgst': '0.00', 'igst': '656.16', 'purchase_ledger': 'Manufacturing vendor'}] | Invoice number/date/vendor/GSTIN/taxable present for all 68. | Tax columns use blanks for some zero values: CGST blank 21, SGST blank 21, IGST blank 18; purchase_ledger blank 39. | {'invoice_number': 0, 'invoice_date': 0, 'vendor_name': 0, 'gstin': 0, 'taxable_value': 0, 'cgst': 21, 'sgst': 21, 'igst': 18, 'purchase_ledger': 39} | Zero-vs-blank tax labels and blank ledger labels reduce clarity. | 75% |
| duplicate labels | ground_truth_duplicates.csv | 68 | [{'invoice_number': 'AMD2-1171', 'duplicate_flag': 'TRUE', 'duplicate_reason': 'invoice_number_present_in_prior_postings'}, {'invoice_number': 'AMD2-3862', 'duplicate_flag': 'TRUE', 'duplicate_reason': 'invoice_number_present_in_prior_postings'}, {'invoice_number': 'BLR7-10525', 'duplicate_flag': 'TRUE', 'duplicate_reason': 'invoice_number_present_in_prior_postings'}, {'invoice_number': 'BLR7-8177', 'duplicate_flag': 'TRUE', 'duplicate_reason': 'invoice_number_present_in_prior_postings'}, {'invoice_number': 'BLR8-14563', 'duplicate_flag': 'TRUE', 'duplicate_reason': 'invoice_number_present_in_prior_postings'}] | duplicate_flag covers all records: {'TRUE': 52, 'FALSE': 16}. | duplicate_reason blank for 16 FALSE rows, which is acceptable but less explanatory; policy for fuzzy duplicate candidates not represented. | {'invoice_number': 0, 'duplicate_flag': 0, 'duplicate_reason': 16} | TRUE/FALSE labels exist, but duplicate policy does not encode exact vs fuzzy/candidate severity. | 82% |
| ledger labels | ground_truth_ledger_mapping.csv | 68 | [{'invoice_number': 'AMD2-1171', 'expected_ledger': 'Manufacturing vendor', 'mapping_source': 'intake_purchase_ledger_field'}, {'invoice_number': 'AMD2-3862', 'expected_ledger': 'Manufacturing vendor', 'mapping_source': 'intake_purchase_ledger_field'}, {'invoice_number': 'BLR7-10525', 'expected_ledger': 'Manufacturing vendor', 'mapping_source': 'intake_purchase_ledger_field'}, {'invoice_number': 'BLR7-8177', 'expected_ledger': 'Manufacturing vendor', 'mapping_source': 'intake_purchase_ledger_field'}, {'invoice_number': 'BLR8-14563', 'expected_ledger': 'Manufacturing vendor', 'mapping_source': 'intake_purchase_ledger_field'}] | expected_ledger has one nonblank class plus blanks: {'<blank>': 39, 'Manufacturing vendor': 29}. | 39 rows have blank expected_ledger but mapping_source=intake_purchase_ledger_field, which overstates evidence. | {'invoice_number': 0, 'expected_ledger': 39, 'mapping_source': 0} | Blank expected ledgers are not typed as missing/unknown/no-ledger; mapping_source is not granular. | 45% |
| queue labels | no dedicated queue ground truth found | 0 | none | Not evaluable as a ground truth category. | Queue labels were derived post-hoc in audits, not present as source ground truth. | 68 missing queue labels if one expected per invoice. | Hard/medium/auto-post policy absent from ground truth. | 0% |

## Detailed findings

### Extraction labels

- Complete core identifiers: invoice_number, invoice_date, vendor_name, GSTIN, taxable_value are present for all 68 rows.
- Tax component labels have blanks that likely mean zero, but the label contract does not distinguish zero from missing: CGST blanks=21, SGST blanks=21, IGST blanks=18.
- Purchase ledger is blank for 39 rows, which may be a true missing source field but is not explicitly typed.

### Duplicate labels

- Duplicate flags: {'TRUE': 52, 'FALSE': 16}.
- Duplicate labels are broadly usable for exact duplicate testing, but they do not encode fuzzy/malformed-prior candidate status.

### Ledger labels

- Ledger expected values: {'<blank>': 39, 'Manufacturing vendor': 29}.
- Contradiction: 39 rows say mapping_source=intake_purchase_ledger_field while expected_ledger is blank.

### Queue labels

- No separate queue-label ground truth file exists. Queue precision/recall studies therefore depend on derived policy judgments, not fixture-native labels.

## Ground truth improvement requirements for TXN-002

- Encode zero tax values as numeric zero, not blank.
- Add label status fields: observed, missing_in_source, inferred, not_applicable.
- Split duplicate labels into exact_duplicate, fuzzy_candidate, current_intake_repeat, no_duplicate.
- Split ledger labels into true_mapping, inferred_mapping, unknown_missing_ledger, not_applicable.
- Add queue labels with severity: Hard Queue, Medium Queue, Auto Post Candidate.