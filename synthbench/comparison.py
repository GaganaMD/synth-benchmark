from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from synthbench.common import read_json, write_json


COMPARISON_SCHEMA_VERSION = "1.0"


def generate_comparison_report(run_dirs: list[str | Path], output_dir: str | Path | None = None) -> dict[str, Any]:
    runs = [_load_run(Path(run_dir)) for run_dir in run_dirs]
    if len(runs) < 2:
        raise ValueError("at least two completed runs are required for comparison")
    task_ids = {run["task_id"] for run in runs}
    if len(task_ids) != 1:
        raise ValueError(f"all runs must have the same task_id; found {sorted(task_ids)}")
    task_id = next(iter(task_ids))
    report = {
        "schema_version": COMPARISON_SCHEMA_VERSION,
        "artifact_type": "comparison_report",
        "task_id": task_id,
        "run_count": len(runs),
        "runs": [_run_summary(run) for run in runs],
        "pairwise_comparisons": [_compare_pair(a, b) for a, b in combinations(runs, 2)],
        "notes": "Pairwise same-task comparison only. This is not a leaderboard.",
    }
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        write_json(out / "comparison_report.json", report)
        (out / "comparison_report.md").write_text(render_comparison_markdown(report), encoding="utf-8")
    return report


def render_comparison_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Comparison Report: {report.get('task_id')}",
        "",
        "This report compares completed runs for the same task. It is not a leaderboard.",
        "",
        "## Runs",
        _table(
            ["Run ID", "Model", "Harness", "Seed", "Status", "Runtime", "Safety"],
            [
                [
                    run.get("run_id"),
                    run.get("model_id"),
                    run.get("harness_id"),
                    run.get("seed"),
                    run.get("status"),
                    run.get("runtime_seconds"),
                    run.get("safety_score"),
                ]
                for run in report.get("runs", [])
            ],
        ),
        "",
    ]
    for item in report.get("pairwise_comparisons", []):
        lines.extend(
            [
                f"## {item.get('model_a')} vs {item.get('model_b')}",
                "",
                "### Metrics",
                _table(
                    ["Metric", "Model A", "Model B", "Delta"],
                    [[k, v.get("model_a"), v.get("model_b"), v.get("delta")] for k, v in item.get("metric_comparison", {}).items()],
                ),
                "",
                f"- `agreement_rate`: {item.get('agreement_rate')}",
                f"- `disagreement_rate`: {item.get('disagreement_rate')}",
                "",
                "### Disagreements",
                _table(
                    ["Decision Key", "Model A Decision", "Model B Decision", "Supporting Evidence"],
                    [
                        [
                            disagreement.get("decision_key"),
                            disagreement.get("model_a_decision"),
                            disagreement.get("model_b_decision"),
                            disagreement.get("supporting_evidence"),
                        ]
                        for disagreement in item.get("disagreements", [])
                    ],
                ),
                "",
            ]
        )
    return "\n".join(lines)


def _load_run(run_dir: Path) -> dict[str, Any]:
    manifest = read_json(run_dir / "manifest.json", default={}) or {}
    canonical = read_json(run_dir / "canonical_output.json", default={}) or {}
    grading = read_json(run_dir / "grading_result.json", default={}) or {}
    intelligence = read_json(run_dir / "run_intelligence_report.json", default={}) or {}
    submission = read_json(run_dir / "submission.json", default={}) or {}
    return {
        "run_dir": run_dir,
        "manifest": manifest,
        "canonical": canonical,
        "grading": grading,
        "intelligence": intelligence,
        "submission": submission,
        "task_id": manifest.get("task_id") or canonical.get("identity", {}).get("task_id") or grading.get("task_id"),
    }


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    manifest = run["manifest"]
    execution = run["intelligence"].get("execution_summary", {})
    grading = run["intelligence"].get("grading_analysis", {})
    return {
        "run_id": manifest.get("run_id"),
        "experiment_id": manifest.get("experiment_id"),
        "model_id": manifest.get("model_id"),
        "harness_id": manifest.get("harness_id"),
        "seed": manifest.get("seed"),
        "status": execution.get("status") or run["submission"].get("status"),
        "runtime_seconds": execution.get("runtime_seconds"),
        "safety_score": grading.get("safety_score") or grading.get("safety_v2_score"),
    }


def _compare_pair(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    decisions_a = _decision_map(a)
    decisions_b = _decision_map(b)
    keys = sorted(set(decisions_a) | set(decisions_b))
    agreements = [key for key in keys if decisions_a.get(key) == decisions_b.get(key)]
    disagreements = [
        {
            "decision_key": key,
            "model_a_decision": decisions_a.get(key),
            "model_b_decision": decisions_b.get(key),
            "supporting_evidence": _supporting_evidence(a, b, key),
        }
        for key in keys
        if decisions_a.get(key) != decisions_b.get(key)
    ]
    agreement_rate = len(agreements) / len(keys) if keys else 1.0
    return {
        "run_a": a["manifest"].get("run_id"),
        "run_b": b["manifest"].get("run_id"),
        "model_a": a["manifest"].get("model_id"),
        "model_b": b["manifest"].get("model_id"),
        "metric_comparison": _metric_comparison(a, b),
        "agreement_rate": round(agreement_rate, 6),
        "disagreement_rate": round(1.0 - agreement_rate, 6),
        "disagreements": disagreements,
    }


def _metric_comparison(a: dict[str, Any], b: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics = {}
    for name, getter in {
        "extraction_accuracy": lambda run: _metric(run, "f1"),
        "duplicate_detection": lambda run: _metric(run, "duplicate_f1"),
        "ledger_mapping": lambda run: _metric(run, "mapping_accuracy"),
        "queue_rate": _queue_rate,
        "auto_post_rate": _auto_post_rate,
        "hallucination_rate": lambda run: _metric(run, "hallucination_rate"),
        "runtime": lambda run: run["intelligence"].get("execution_summary", {}).get("runtime_seconds"),
        "tool_usage": lambda run: run["intelligence"].get("execution_summary", {}).get("tool_call_count"),
        "safety": lambda run: run["intelligence"].get("grading_analysis", {}).get("safety_score") or run["intelligence"].get("grading_analysis", {}).get("safety_v2_score"),
        "auditability": lambda run: run["intelligence"].get("enterprise_analysis", {}).get("auditability_score"),
    }.items():
        av = getter(a)
        bv = getter(b)
        metrics[name] = {"model_a": av, "model_b": bv, "delta": _delta(av, bv)}
    return metrics


def _decision_map(run: dict[str, Any]) -> dict[str, str]:
    decisions = {}
    for table in run["canonical"].get("content", {}).get("tables", []):
        if not isinstance(table, dict):
            continue
        source = table.get("source_path") or "table"
        for row in table.get("rows", []):
            if not isinstance(row, dict):
                continue
            key = row.get("Invoice No") or row.get("invoice_number") or row.get("invoice_no") or row.get("id")
            if key:
                decisions[str(key)] = f"{source}:{_decision_label(row)}"
    if decisions:
        return decisions
    final_output = ""
    for report in run["canonical"].get("content", {}).get("reports", []):
        if report.get("report_type") == "final_output":
            final_output = report.get("content", "")
            break
    return {"final_output": final_output[:500]}


def _decision_label(row: dict[str, Any]) -> str:
    if row.get("duplicate_reason"):
        return "duplicate"
    if row.get("exception_reason"):
        return "exception"
    if row.get("queue_reason"):
        return "queued"
    return "processed"


def _supporting_evidence(a: dict[str, Any], b: dict[str, Any], key: str) -> str:
    return f"Compared canonical_output tables for decision key {key}; run_a={a['manifest'].get('run_id')}, run_b={b['manifest'].get('run_id')}"


def _metric(run: dict[str, Any], name: str) -> Any:
    return run["intelligence"].get("metric_computation", {}).get(name)


def _queue_rate(run: dict[str, Any]) -> Any:
    counts = _output_counts(run)
    total = sum(counts.values())
    return round(counts.get("queued", 0) / total, 6) if total else None


def _auto_post_rate(run: dict[str, Any]) -> Any:
    counts = _output_counts(run)
    total = sum(counts.values())
    return round(counts.get("processed", 0) / total, 6) if total else None


def _output_counts(run: dict[str, Any]) -> dict[str, int]:
    counts = {"processed": 0, "queued": 0, "duplicate": 0, "exception": 0}
    for table in run["canonical"].get("content", {}).get("tables", []):
        source = str(table.get("source_path") or "").lower()
        row_count = len(table.get("rows", []) if isinstance(table.get("rows"), list) else [])
        if "duplicate" in source:
            counts["duplicate"] += row_count
        elif "exception" in source:
            counts["exception"] += row_count
        elif "queue" in source:
            counts["queued"] += row_count
        elif "processed" in source or "approved_postings" in source:
            counts["processed"] += row_count
    return counts


def _delta(a: Any, b: Any) -> Any:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return round(float(a) - float(b), 6)
    return None


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_No rows._"
    header = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(value).replace("|", "\\|") if value is not None else "" for value in row) + " |" for row in rows]
    return "\n".join([header, sep, *body])
