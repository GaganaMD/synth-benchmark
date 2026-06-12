from pathlib import Path

from synthbench.common import write_json
from synthbench.state.audit import audit_files, duplicate_outputs, duplicate_postings, duplicate_side_effects
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, write_snapshot
from synthbench.state.validation import validate_state_cell
from synthbench.trace.replay import replay_cell


def test_snapshot_diff_and_validation(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    workspace = tmp_path / "workspace"
    artifacts = cell / "artifacts"
    state = cell / "state"
    workspace.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    state.mkdir(parents=True)
    (workspace / "input.txt").write_text("before", encoding="utf-8")
    write_json(cell / "manifest.json", {"experiment_id": "exp", "run_id": "run", "task_id": "T1"})
    (cell / "events.jsonl").write_text("", encoding="utf-8")

    s0 = capture_snapshot(snapshot_id="S0_run", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s0, state / "S0.json")
    (workspace / "input.txt").write_text("after", encoding="utf-8")
    (artifacts / "run_summary.csv").write_text("ok", encoding="utf-8")
    s1 = capture_snapshot(snapshot_id="S1_run", workspace_dir=workspace, outputs_dir=artifacts)
    write_snapshot(s1, state / "S1.json")
    diff = compute_state_diff(s0, s1)
    write_state_diff(diff, state / "state_diff.json")

    assert diff["summary"]["files_modified"] == 1
    assert diff["summary"]["files_created"] == 1
    assert validate_state_cell(cell) == []
    replay = replay_cell(cell)
    assert replay["state"]["diff"]["summary"]["files_created"] == 1


def test_side_effect_audit_and_duplicates():
    diff = {
        "changes": [
            {"scope": "outputs", "change_type": "created", "path": "run_summary.csv"},
            {"scope": "outputs", "change_type": "created", "path": "extra.csv"},
        ]
    }
    audit = audit_files(["run_summary.csv", "exceptions.csv"], diff)
    assert audit["status"] == "FAIL"
    assert audit["missing_outputs"] == ["exceptions.csv"]
    assert audit["unexpected_outputs"] == ["extra.csv"]
    assert duplicate_outputs(["a/out.csv", "b/out.csv"]) == [{"name": "out.csv", "count": 2}]
    postings = [
        {"date": "2026-01-01", "vendor": "A", "invoice_no": "1", "amount": 10, "ledger": "L"},
        {"date": "2026-01-01", "vendor": "A", "invoice_no": "1", "amount": 10, "ledger": "L"},
    ]
    assert duplicate_postings(postings)[0]["count"] == 2
    assert duplicate_side_effects(audit["effects"]) == []
