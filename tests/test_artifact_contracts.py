from pathlib import Path

from synthbench.common import write_json
from synthbench.normalization.output import normalize_cell
from synthbench.schemas.artifacts import all_schemas
from synthbench.schemas.migrations import compatibility_issues, migrate_artifact
from synthbench.schemas.validation import contract_is_valid, validate_cell_contract, validate_document
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, write_snapshot
from synthbench.trace.events import append_event, make_event


def test_schema_specs_are_available():
    schemas = all_schemas()
    assert set(schemas) == {"manifest", "canonical_output", "event", "snapshot", "state_diff"}
    assert schemas["manifest"]["properties"]["schema_version"]["const"] == "1.0"


def test_validate_full_artifact_contract(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    workspace = tmp_path / "tasks" / "T1" / "workspace"
    artifacts = cell / "artifacts"
    state = cell / "state"
    workspace.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    state.mkdir(parents=True)
    (workspace / "input.txt").write_text("fixture", encoding="utf-8")
    (artifacts / "run_summary.csv").write_text("invoice_no,amount\nINV-1,10\n", encoding="utf-8")
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
    }
    write_json(cell / "manifest.json", manifest)
    append_event(cell / "events.jsonl", make_event(manifest, "task_start"))
    s0 = capture_snapshot(snapshot_id="S0_run1", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s0, state / "S0.json")
    (artifacts / "exceptions.csv").write_text("item,reason\n", encoding="utf-8")
    s1 = capture_snapshot(snapshot_id="S1_run1", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s1, state / "S1.json")
    write_state_diff(compute_state_diff(s0, s1), state / "state_diff.json")
    write_json(
        cell / "submission.json",
        {
            "task_id": "T1",
            "status": "COMPLETED",
            "adapter": "codex",
            "final_output": "done",
            "deliverables": ["artifacts/run_summary.csv"],
        },
    )
    normalize_cell(cell)

    results = validate_cell_contract(cell, require_canonical=True)

    assert contract_is_valid(results), results


def test_compatibility_and_migration_for_missing_version():
    document = {"event_id": "evt1"}
    assert compatibility_issues("event", document) == ["event: missing schema_version; can be migrated to 1.0"]
    migrated = migrate_artifact("event", document)
    assert migrated["schema_version"] == "1.0"
    assert "schema_version" not in document


def test_validate_document_reports_required_fields():
    issues = validate_document("manifest", {"schema_version": "1.0"})
    assert any("missing required field run_id" in issue for issue in issues)
