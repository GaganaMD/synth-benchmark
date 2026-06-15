# TXN-001 Benchmark Parity Audit

Scope: compares the original Codex TXN-001 run against the isolated Hermes+Codex TXN-001 environment. This audit uses manifests, fixture hashes, grading reports, and generated output artifacts only.

## Identity checks

| Dimension | Codex TXN-001 | Hermes+Codex TXN-001 | Parity finding |
|---|---|---|---|
| task identity | TXN-001 | TXN-001 | MATCH: both are TXN-001. |
| dataset identity | v10-revised-labels | v10-revised-labels | MATCH: both use v10-revised-labels. |
| seed identity | 0 | 0 | MATCH: both seed 0. |
| fixture identity / version | v10-revised-labels__TXN-001__2c55f4a8e0056c86 | hermes-codex-v10-revised-labels__TXN-001__01f2b75398112df4 | VERSION MISMATCH: isolated environment rematerialized fixture under a new fixture_version. |
| workspace hash | 2c55f4a8e0056c860fb10de8c292bcd2eda69b333dfd375df1b84a822786f5ea | 01f2b75398112df4863f9dfc9154c2b554afe9ddaaf2d2721558a8ba82230f01 | HASH MISMATCH in tree hash, but per-file hashes match for the six baseline files; likely path/root hashing difference. |
| workspace file count | 6 | 6 | MATCH: both list 6 workspace files. |
| environment identity | env_12ff104b9e61dd7f | env_hermes_codex_525d0d8047304246 | MISMATCH: environments are intentionally isolated/different. |
| git commit identity | 3caeb64725dc5642b765177394d9010d26d65845 | 19100900934176c329754ea166d6a17fe9d7a6d7 | MISMATCH: runs were prepared at different commits. |
| harness/model identity | codex / codex-cli-current | Hermes manifest model_id=hermes; paired Codex manifest model_id=codex-cli-current | MISMATCH by design: this is a cross-agent comparison, not same-harness replay. |
| grading identity | Original Codex grading_result.json / run_intelligence_report.md | Isolated manifests specify shared fixture/dataset/seed, but Hermes processing outputs were not official harness grading outputs | PARTIAL: comparable for artifact analysis, not fully parity-equivalent official scoring. |
| safety identity | Official safety operator score=0.0 for Codex; subprocess trace | Hermes safety inferred from normalized outputs/audits, not same official safety operator | MISMATCH: safety conclusions use different evidence layers. |
| metric identity | operator_score, exact/numeric/set/state/tool/safety scores | agreement/disagreement, queue precision, controllership metrics | MISMATCH: metrics are analytically useful but not identical official metrics. |

## Scientific-validity assessment

The Codex-vs-Hermes comparison is scientifically valid only for artifact-level, post-hoc qualitative/diagnostic comparison, not as a fully controlled head-to-head benchmark score.

Reasons it is partially valid:

- Task ID, dataset_version, seed, and six baseline workspace file hashes match at the per-file level.
- Both analyses cover the same 68-invoice population.
- The isolated Hermes+Codex environment intentionally excluded the optional v2 workbook, preserving baseline scope.

Reasons it is not fully scientifically controlled:

- Fixture_version and workspace tree hash differ because the Hermes+Codex environment was rematerialized under a new isolated root.
- Codex has official grading_result/run_intelligence artifacts; Hermes outputs here are normalized analytical outputs, not an official identical harness grading run.
- Trace fidelity differs: Codex subprocess trace is opaque; Hermes file usage is supported by generated artifacts but not identical low-level tracing.
- Safety and metric identities differ, so direct score-to-score comparison is invalid.

Final parity conclusion: scientifically valid for identifying likely decision-quality and infrastructure issues; not scientifically valid as a definitive model leaderboard comparison until TXN-002 uses identical fixture IDs, identical grading operators, identical trace instrumentation, and identical metric definitions.