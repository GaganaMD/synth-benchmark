# Hermes/Codex TXN-001 Isolated Environment Validation

Prepared: 2026-06-15T04:57:25Z

## IDs

- experiment_id: exp_hermes_codex_txn001_6985e348ef02
- fixture_version: hermes-codex-v10-revised-labels__TXN-001__01f2b75398112df4
- environment_version: env_hermes_codex_525d0d8047304246
- hermes_run_id: run_hermes_60290a436ff8
- codex_run_id: run_codex_c5220b7a5f53
- dataset_version: v10-revised-labels
- seed: 0

## Counts

- invoice count: 68
- vendor count: 17
- duplicate count: 52
- ledger count: 1
- chart of accounts ledger rows: 110
- prior postings rows: 1584

## Validation checks

| Check | Status |
|---|---|
| workspace completeness | PASS |
| fixture completeness | PASS |
| dataset linkage | PASS |
| artifact contracts | PASS |
| fixture registration | PASS |
| optional v2 excluded | PASS |
| isolated output dirs | PASS |

## Missing artifacts

None

## Workspace inventory

- chart_of_accounts.csv (10076 bytes, sha256=faa5d546dcae498f0aeaf5b0bc3a5d077f55fd1e74378e987e736e55798acf31)
- intake/Invoice_Register_A_to_AVA.xlsx (10114 bytes, sha256=86bf4b8c6dd32b5dd4b101dabd1dfc93305b51cf65e49d94a73ac4dfc91d2d5f)
- intake/Tally_Cherian_Enterprises_June25.xlsx (8743 bytes, sha256=7aae9f40724a0105b2ff2f74b5a1cb9a467441bd0e25b1c48b005498d9039cb9)
- prior_postings.csv (86408 bytes, sha256=77ba69d76e9d55c3674f60c988105aa32dbf1578b631090b6f0d6b9130606084)
- recurring_master.csv (67 bytes, sha256=8559c43c546cec0bcf70390a60e22787734fae26dcaf62b1951b7ba0cd192b4f)
- reimbursement_policy.md (262 bytes, sha256=d5884fce36c00fe01884a861330fc11b69db0f773ad3d113e3e85484433fd2c3)

## Ground truth inventory

- ground_truth_duplicates.csv (3350 bytes, sha256=fda4a1ff3978c1df55643156becc214805f9f8230fa344538bd6415b52ae0930)
- ground_truth_extraction.csv (6796 bytes, sha256=03849e9fd566342041ea14c1df0858a93ed18d4960cfd272707f9f66a7aff103)
- ground_truth_ledger_mapping.csv (3465 bytes, sha256=1c6808ae482036461009cf9eb9f5e8e67c3e4ab499261ad3d72e360dd99c321a)

## Readiness

- workspace readiness score: 100/100
- executable now: YES

Executable means the isolated inputs, fixture copy, ground truth, prompts, manifests, baseline state placeholder, output directories, and isolated registration records exist. Hermes and Codex have not been run.
