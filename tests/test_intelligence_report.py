from pathlib import Path

from synthbench.common import write_json
from synthbench.grading.engine import grade_cell
from synthbench.intelligence import generate_run_intelligence_report
from synthbench.normalization.output import normalize_cell
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, write_snapshot
from synthbench.trace.events import (
    append_event,
    make_event,
    make_task_complete_event,
    make_tool_call_event,
    make_tool_result_event,
)


def test_generate_run_intelligence_report(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    workspace = tmp_path / "tasks" / "T1" / "workspace"
    artifacts = cell / "artifacts"
    state = cell / "state"
    workspace.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    state.mkdir(parents=True)
    (workspace / "invoice_001.pdf").write_text("invoice INV-1 amount 100", encoding="utf-8")
    (workspace / "prior_postings.csv").write_text("invoice_no\nINV-0\n", encoding="utf-8")
    write_json(
        tmp_path / "tasks" / "T1" / "task.json",
        {
            "id": "T1",
            "service_line": "CFO",
            "category": "Transaction Processing",
            "subcategory": "Document extraction",
            "complexity": "Hard",
            "expert_time_mins": 55,
        },
    )
    manifest = {
        "schema_version": "1.0",
        "experiment_id": "exp1",
        "run_id": "run1",
        "task_id": "T1",
        "harness_id": "codex",
        "model_id": "model1",
        "seed": 0,
        "dataset_version": "ds1",
        "fixture_version": "fx1",
        "environment_version": "env1",
        "workspace_hash": {"tree_sha256": "abc"},
        "git_commit": "abc123",
        "workspace_dir": workspace.as_posix(),
        "task_dir": (tmp_path / "tasks" / "T1").as_posix(),
        "expected_tool_calls": "2+ tool calls",
    }
    write_json(cell / "manifest.json", manifest)
    append_event(cell / "events.jsonl", make_event(manifest, "task_start"))
    append_event(cell / "events.jsonl", make_event(manifest, "file_read", path=(workspace / "invoice_001.pdf").as_posix()))
    append_event(cell / "events.jsonl", make_event(manifest, "file_read", path=(workspace / "prior_postings.csv").as_posix()))
    append_event(cell / "events.jsonl", make_tool_call_event(manifest, tool_name="read", arguments={"path": "invoice_001.pdf"}, result=None, success=True, latency_ms=10))
    append_event(cell / "events.jsonl", make_tool_result_event(manifest, tool_name="read", result={"ok": True}, success=True, latency_ms=20))
    append_event(cell / "events.jsonl", make_event(manifest, "verification", status="PASS", message="counts reconcile"))
    append_event(cell / "events.jsonl", make_task_complete_event(manifest, runtime_seconds=2, step_count=7))
    s0 = capture_snapshot(snapshot_id="S0_run1", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s0, state / "S0.json")
    (artifacts / "run_summary.csv").write_text("invoice_no,amount,source\nINV-1,100,invoice_001.pdf\n", encoding="utf-8")
    s1 = capture_snapshot(snapshot_id="S1_run1", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s1, state / "S1.json")
    write_state_diff(compute_state_diff(s0, s1), state / "state_diff.json")
    write_json(
        cell / "submission.json",
        {
            "task_id": "T1",
            "status": "COMPLETED",
            "adapter": "codex",
            "answers": {"invoice_no": "INV-1", "amount": 100},
            "final_output": "Invoice INV-1 amount 100 from invoice_001.pdf",
            "deliverables": ["artifacts/run_summary.csv"],
        },
    )
    normalize_cell(cell)
    grade_cell(
        cell,
        [
            {"operator": "exact", "criteria": "invoice_no", "expected": "INV-1"},
            {"operator": "numeric", "criteria": "amount", "expected": 100, "tolerance": 0.01},
            {"operator": "tool_use", "criteria": "tools", "min_tool_calls": 2},
        ],
        validate_artifacts=False,
    )

    report = generate_run_intelligence_report(cell)

    assert (cell / "run_intelligence_report.json").exists()
    assert (cell / "run_intelligence_report.md").exists()
    assert report["benchmark_completeness"]["execution_complete"] is True
    assert report["benchmark_completeness"]["normalization_complete"] is True
    assert report["benchmark_completeness"]["grading_complete"] is True
    assert report["benchmark_completeness"]["intelligence_report_completeness_percent"] > 0
    assert any(row["metric_name"] == "runtime_seconds" and row["available"] for row in report["metric_availability_matrix"])
    assert any(row["artifact"] == "grading_result.json" and row["present"] for row in report["artifact_availability_matrix"])
    assert report["benchmark_capability_versions"]["intelligence_report_version"] == "1.0"
    assert report["run_metadata"]["experiment_id"] == "exp1"
    assert report["run_metadata"]["service_line"] == "CFO"
    assert report["execution_summary"]["status"] == "COMPLETED"
    assert report["comparison_ready_fields"]["documents_read"] == 2
    assert report["comparison_ready_fields"]["tool_calls"] == 1
    assert report["tool_analysis"]["tools_ranked_by_usage"][0]["tool_name"] == "read"
    assert report["workspace_analysis"]["workspace_file_recall"] == 1.0
    assert report["evidence_document_utilization_analysis"]["document_influence_table"]
    assert report["document_importance_ranking"][0]["document"]
    markdown = (cell / "run_intelligence_report.md").read_text(encoding="utf-8")
    assert "Run Intelligence Report" in markdown
    assert "Benchmark Completeness" in markdown


def test_intelligence_report_marks_incomplete_run(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    state = cell / "state"
    state.mkdir(parents=True)
    manifest = {
        "schema_version": "1.0",
        "experiment_id": "exp1",
        "run_id": "run1",
        "task_id": "T1",
        "harness_id": "codex",
        "model_id": "model1",
        "seed": 0,
        "dataset_version": "ds1",
        "fixture_version": "fx1",
        "environment_version": "env1",
        "workspace_hash": {"tree_sha256": "abc", "files": []},
        "git_commit": "abc123",
    }
    write_json(cell / "manifest.json", manifest)
    append_event(cell / "events.jsonl", make_event(manifest, "task_start"))
    write_json(state / "S0.json", {"schema_version": "1.0", "snapshot_id": "S0_run1", "timestamp": "2026-01-01T00:00:00Z"})
    write_json(state / "state_diff.json", {"schema_version": "1.0", "status": "NOT_CAPTURED", "changes": []})
    write_json(cell / "submission.json", {"task_id": "T1", "status": "AWAITING_AGENT_OUTPUT"})

    report = generate_run_intelligence_report(cell)

    completeness = report["benchmark_completeness"]
    assert completeness["execution_complete"] is False
    assert completeness["normalization_complete"] is False
    assert completeness["grading_complete"] is False
    assert completeness["metrics_complete"] is False
    assert completeness["infrastructure_vs_run_status"] == "infrastructure_available_but_run_incomplete"
    assert any(row["metric_name"] == "runtime_seconds" and not row["available"] for row in report["metric_availability_matrix"])
    assert any(row["artifact"] == "canonical_output.json" and not row["present"] for row in report["artifact_availability_matrix"])
