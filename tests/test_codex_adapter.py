from pathlib import Path

from synthbench.adapters.codex import CodexAdapterConfig, run_codex_adapter
from synthbench.common import write_json
from synthbench.state.validation import validate_state_cell
from synthbench.trace.events import read_events, validate_trace
from synthbench.trace.replay import replay_cell


def test_codex_adapter_dry_run_generates_trace_state_and_artifacts(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    workspace = tmp_path / "tasks" / "T1" / "workspace"
    workspace.mkdir(parents=True)
    cell.mkdir(parents=True)
    (cell / "artifacts").mkdir()
    (cell / "state").mkdir()
    (workspace / "input.txt").write_text("fixture", encoding="utf-8")
    (cell / "prompt.txt").write_text("Do the dummy task.", encoding="utf-8")
    write_json(
        cell / "manifest.json",
        {
            "experiment_id": "exp1",
            "run_id": "run1",
            "task_id": "T1",
            "harness_id": "codex",
            "model_id": "codex-dry-run",
            "dataset_version": "ds1",
            "fixture_version": "fx1",
            "workspace_dir": workspace.as_posix(),
        },
    )
    write_json(cell / "submission.json", {"task_id": "T1", "status": "AWAITING_AGENT_OUTPUT"})

    result = run_codex_adapter(cell, CodexAdapterConfig(mode="dry-run"))

    assert result["status"] == "COMPLETED"
    assert (cell / "raw_response.txt").exists()
    assert (cell / "final_output.md").exists()
    assert (cell / "artifacts" / "dry_run_output.txt").exists()
    assert (cell / "state" / "S0.json").exists()
    assert (cell / "state" / "S1.json").exists()
    assert (cell / "state" / "state_diff.json").exists()

    events = read_events(cell / "events.jsonl")
    assert validate_trace(events) == []
    assert events[0]["event_type"] == "task_start"
    assert events[-1]["event_type"] == "task_complete"
    assert {event["event_type"] for event in events} >= {
        "task_start",
        "tool_call",
        "tool_result",
        "state_checkpoint",
        "verification",
        "task_complete",
    }
    assert validate_state_cell(cell) == []
    replay = replay_cell(cell)
    assert replay["valid"] is True
    assert replay["state"]["diff"]["summary"]["files_created"] >= 1
    submission = result["submission_status"]
    assert submission == "COMPLETED"


def test_codex_adapter_refuses_completed_cell(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    workspace = tmp_path / "tasks" / "T1" / "workspace"
    workspace.mkdir(parents=True)
    cell.mkdir(parents=True)
    (cell / "artifacts").mkdir()
    (cell / "state").mkdir()
    (workspace / "input.txt").write_text("fixture", encoding="utf-8")
    (cell / "prompt.txt").write_text("Do the dummy task.", encoding="utf-8")
    write_json(
        cell / "manifest.json",
        {
            "experiment_id": "exp1",
            "run_id": "run1",
            "task_id": "T1",
            "harness_id": "codex",
            "model_id": "codex-dry-run",
            "dataset_version": "ds1",
            "fixture_version": "fx1",
            "workspace_dir": workspace.as_posix(),
        },
    )
    write_json(cell / "submission.json", {"task_id": "T1", "status": "AWAITING_AGENT_OUTPUT"})

    run_codex_adapter(cell, CodexAdapterConfig(mode="dry-run"))
    try:
        run_codex_adapter(cell, CodexAdapterConfig(mode="dry-run"))
    except RuntimeError as exc:
        assert "already completed" in str(exc)
    else:
        raise AssertionError("adapter should reject completed cells")
