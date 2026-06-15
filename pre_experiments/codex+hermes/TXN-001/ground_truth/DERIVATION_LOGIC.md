# TXN-001 Ground Truth Derivation Logic

Prepared: 2026-06-15T04:57:25Z

Approved source audit artifacts used:
- /Users/basethesis/Desktop/synth-benchmark/tasks_complete/TXN-001
- Workspace source: /Users/basethesis/Desktop/synth-benchmark/tasks_complete/TXN-001/workspace
- Ground truth source: /Users/basethesis/Desktop/synth-benchmark/tasks_complete/TXN-001/ground_truth

Ground truth files:
- ground_truth_extraction.csv: normalized invoice fields copied from approved structured Excel intake derivation.
- ground_truth_duplicates.csv: duplicate labels copied from approved derivation; an invoice is duplicate when invoice_number appears in prior_postings.csv or repeats within intake.
- ground_truth_ledger_mapping.csv: expected ledger copied from approved derivation using purchase_ledger from the intake workbook.

Workspace derivations:
- chart_of_accounts.csv: approved derived output from TB April 25 March 26.xlsx; union of trial-balance candidate ledger names and distinct purchase_ledger values.
- prior_postings.csv: approved derived output from BaseThesis_Tally_Purchase_June25.xlsx.
- recurring_master.csv and reimbursement_policy.md: schema-compliant placeholders from approved workspace.

Baseline exclusion:
- Tally_Cherian_Enterprises_June25_v2.xlsx was not copied into workspace/ or fixture/workspace/.
