from pathlib import Path

import pytest

from synthbench.common import write_json
from synthbench.comparison import generate_comparison_report


def _run_cell(root: Path, task_id: str, run_id: str, model_id: str) -> Path:
    cell = root / run_id
    cell.mkdir(parents=True)
    write_json(
        cell / "manifest.json",
        {
            "task_id": task_id,
            "run_id": run_id,
            "experiment_id": f"exp_{run_id}",
            "model_id": model_id,
            "harness_id": "codex",
            "seed": 0,
        },
    )
    write_json(
        cell / "canonical_output.json",
        {
            "content": {
                "tables": [{"source_path": "processed_invoices.csv", "rows": [{"Invoice No": "INV-1"}]}],
                "reports": [],
            }
        },
    )
    write_json(cell / "grading_result.json", {"operator_score": 1.0})
    write_json(cell / "submission.json", {"status": "COMPLETED"})
    write_json(
        cell / "run_intelligence_report.json",
        {
            "execution_summary": {"status": "COMPLETED", "runtime_seconds": 1, "tool_call_count": 2},
            "metric_computation": {"f1": 1.0, "hallucination_rate": 0.0},
            "grading_analysis": {"safety_score": 1.0},
            "enterprise_analysis": {"auditability_score": 1.0},
        },
    )
    return cell


def test_generate_same_task_comparison_report(tmp_path: Path):
    a = _run_cell(tmp_path, "TXN-001", "run_a", "model-a")
    b = _run_cell(tmp_path, "TXN-001", "run_b", "model-b")

    report = generate_comparison_report([a, b], output_dir=tmp_path / "comparison")

    assert report["task_id"] == "TXN-001"
    assert report["run_count"] == 2
    assert report["pairwise_comparisons"][0]["agreement_rate"] == 1.0
    assert (tmp_path / "comparison" / "comparison_report.json").exists()
    assert (tmp_path / "comparison" / "comparison_report.md").exists()


def test_comparison_rejects_mixed_tasks(tmp_path: Path):
    a = _run_cell(tmp_path, "TXN-001", "run_a", "model-a")
    b = _run_cell(tmp_path, "TXN-002", "run_b", "model-b")

    with pytest.raises(ValueError, match="same task_id"):
        generate_comparison_report([a, b])
