# Metrics Wiring

This repo supports all pending live-exec metrics in offline mock mode. Live paths are explicit TODOs and raise `NotImplementedError` until credentials or model APIs are wired.

## Metric Status Rules

`metrics/registry.py` marks a metric live only after `results/**/results.json` contains at least one result object with:

- matching `metric_id`
- `status: "live"`
- non-null `value`

`tools/update_metric_status.py` only flips `docs/metrics_v2.md` from `pending live exec` to `live`. It never flips a metric back.

## Metric Wiring

- **11 State-audit pass rate**: mock validates audit shape and returns null. Live requires real auditor counts: `landed_correct` and `claimed_effects`. TODO: Zoho/Tally/SharePoint/OneDrive/email auditors must populate those counts.
- **12 Tool-use compliance**: computes from trajectory logs. Mock can synthesize from submission metadata. Live uses the real captured trajectory.
- **14 Timeout rate**: computes from `run_suite.py` task logs and CSV `time_budget_s`.
- **15 Calibration**: mock uses deterministic placeholder confidence/correct pairs. Live requires real per-item confidence/correct emissions from tasks.
- **16 Bad-auto-post rate**: mock returns null. Live requires state-audit posting counts: `wrong_posted` and `posted`.
- **17 Over-queue rate**: mock returns null. Live requires queue audit counts: `unnecessarily_queued` and `queued`.
- **18 Autonomy rate** and **19 Time saved**: compute only if the deployment guardrail passes. They return `VOID (unsafe)` when `bad_auto_post > theta_bad_auto_post` or any safety violation occurs.

## Config

All shared thresholds and model IDs live in `config.yaml`:

- `theta_bad_auto_post`
- `f_beta_default`
- `f_beta`
- `judge_model_ids`
- `time_budget_source`

The harness still reads task time budgets from `data/76LH_wildclaw_synth_benchmark.csv`.

## Manual / Not Wired

Leave these manual until access exists:

1. Live Zoho/Tally credentials.
2. SharePoint/OneDrive via Microsoft Graph.
3. Real jury model IDs and anchor authoring.
4. BI human-score CSV for judge validation.
5. Real agent wall-clock and cost capture.

