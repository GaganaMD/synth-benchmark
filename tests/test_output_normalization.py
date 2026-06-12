from pathlib import Path

from synthbench.common import write_json
from synthbench.normalization.output import normalize_cell, validate_canonical_output


def test_normalize_cell_outputs_canonical_schema(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    artifacts = cell / "artifacts"
    state = cell / "state"
    artifacts.mkdir(parents=True)
    state.mkdir(parents=True)
    write_json(
        cell / "manifest.json",
        {
            "experiment_id": "exp1",
            "run_id": "run1",
            "task_id": "T1",
            "harness_id": "codex",
            "model_id": "model1",
            "dataset_version": "ds1",
            "fixture_version": "fx1",
        },
    )
    write_json(
        cell / "submission.json",
        {
            "task_id": "T1",
            "status": "COMPLETED",
            "adapter": "codex",
            "answers": {"invoice_no": "INV-1"},
            "deliverables": ["artifacts/run_summary.csv", "artifacts/report.md"],
            "raw_response_file": "raw_response.txt",
            "final_output_file": "final_output.md",
        },
    )
    (cell / "raw_response.txt").write_text("raw response", encoding="utf-8")
    (cell / "final_output.md").write_text("final response", encoding="utf-8")
    (cell / "events.jsonl").write_text("", encoding="utf-8")
    (artifacts / "run_summary.csv").write_text("invoice_no,amount\nINV-1,10\n", encoding="utf-8")
    (artifacts / "report.md").write_text("# Report\nDone\n", encoding="utf-8")
    write_json(state / "state_diff.json", {"summary": {"files_created": 2}, "changes": [{"path": "run_summary.csv"}]})

    canonical = normalize_cell(cell)

    assert (cell / "canonical_output.json").exists()
    assert validate_canonical_output(canonical) == []
    assert canonical["validation"]["valid"] is True
    assert canonical["identity"]["run_id"] == "run1"
    assert canonical["adapter"]["adapter_id"] == "codex"
    assert canonical["content"]["structured_records"][0]["data"]["invoice_no"] == "INV-1"
    assert canonical["content"]["tables"][0]["rows"][0]["invoice_no"] == "INV-1"
    assert canonical["content"]["reports"][0]["content"] == "final response"
    assert canonical["content"]["side_effect_summaries"][0]["state_diff_summary"]["files_created"] == 2
    assert any(entry["raw_path"] == "artifacts/run_summary.csv" for entry in canonical["provenance"])


def test_validate_canonical_output_rejects_bad_types():
    output = {
        "schema_version": "1.0",
        "normalized_at": "2026-01-01T00:00:00Z",
        "identity": {"run_id": "run1", "task_id": "T1"},
        "adapter": {"adapter_id": "codex"},
        "status": "COMPLETED",
        "content": {
            "structured_records": [],
            "tables": [{"columns": "not-a-list", "rows": []}],
            "reports": [],
            "side_effect_summaries": [],
            "exception_summaries": [],
        },
        "provenance": [],
        "raw_sources": [],
        "validation": {"valid": True, "issues": []},
    }

    issues = validate_canonical_output(output)

    assert any("columns must be a list" in issue for issue in issues)
