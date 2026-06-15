from pathlib import Path

from synthbench.trace.events import (
    append_event,
    make_event,
    make_exception_event,
    make_state_checkpoint_event,
    make_task_complete_event,
    make_tool_call_event,
    read_events,
    validate_trace,
)
from synthbench.trace.replay import replay_cell
from synthbench.trace.reconstruction import reconstruct_cell_events, trace_fidelity_metrics
from synthbench.common import write_json


def manifest() -> dict:
    return {
        "experiment_id": "exp1",
        "run_id": "run1",
        "task_id": "T1",
        "harness_id": "codex",
        "model_id": "model",
        "dataset_version": "ds1",
        "fixture_version": "fx1",
    }


def test_trace_events_append_validate_and_replay(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    cell.mkdir(parents=True)
    write_json(cell / "manifest.json", manifest())
    events_path = cell / "events.jsonl"

    append_event(events_path, make_event(manifest(), "task_start", timestamp="2026-01-01T00:00:00Z"))
    append_event(
        events_path,
        make_tool_call_event(
            manifest(),
            tool_name="shell",
            arguments={"cmd": "ls"},
            success=True,
            latency_ms=5,
        )
        | {"timestamp": "2026-01-01T00:00:01Z"},
    )
    append_event(
        events_path,
        make_state_checkpoint_event(manifest(), checkpoint_id="cp1", state_summary={"files": 1})
        | {"timestamp": "2026-01-01T00:00:02Z"},
    )
    append_event(
        events_path,
        make_task_complete_event(manifest(), runtime_seconds=3, step_count=3, input_tokens=None, output_tokens=None, estimated_cost=None)
        | {"timestamp": "2026-01-01T00:00:03Z"},
    )

    events = read_events(events_path)
    assert validate_trace(events) == []
    replay = replay_cell(cell)
    assert replay["valid"] is True
    assert replay["timeline"]["event_count"] == 4
    assert replay["timeline"]["tool_event_count"] == 1
    assert replay["timeline"]["checkpoint_count"] == 1
    assert replay["timeline"]["runtime_seconds"] == 3


def test_trace_validator_catches_ordering_and_required_fields():
    bad = [
        make_tool_call_event(manifest(), tool_name="shell", success=True) | {"timestamp": "2026-01-01T00:00:02Z"},
        make_event(manifest(), "task_start", timestamp="2026-01-01T00:00:01Z"),
        make_exception_event(manifest(), exception_type="ValueError", message="bad", recovered=False) | {"timestamp": "2026-01-01T00:00:00Z"},
    ]
    issues = validate_trace(bad)
    assert any("missing task_start" in issue or "task_start must be first" in issue for issue in issues)
    assert any("timestamp decreased" in issue for issue in issues)


def test_exception_event_schema_requires_recovery_fields():
    event = make_exception_event(manifest(), exception_type="RuntimeError", message="boom", recovered=True, recovery_action="retry")
    assert event["event_type"] == "exception"
    assert event["recovered"] is True
    assert event["recovery_action"] == "retry"


def test_reconstruct_codex_events_from_transcript(tmp_path: Path):
    cell = tmp_path / "runs" / "codex" / "T1" / "seed-0"
    cell.mkdir(parents=True)
    write_json(cell / "manifest.json", manifest())
    append_event(cell / "events.jsonl", make_event(manifest(), "task_start", timestamp="2026-01-01T00:00:00Z"))
    append_event(
        cell / "events.jsonl",
        make_tool_call_event(manifest(), tool_name="codex.subprocess", arguments={}, result=None, success=True, latency_ms=0)
        | {"timestamp": "2026-01-01T00:00:01Z"},
    )
    append_event(
        cell / "events.jsonl",
        make_tool_call_event(manifest(), tool_name="codex.subprocess", arguments={}, result=None, success=True, latency_ms=2)
        | {"event_type": "tool_result", "timestamp": "2026-01-01T00:00:02Z"},
    )
    (cell / "raw_response.txt").write_text(
        "exec\n/bin/zsh -lc 'rg --files workspace' in /tmp/cell\n succeeded in 3ms:\nworkspace/input.txt\n",
        encoding="utf-8",
    )

    reconstructed, comparison = reconstruct_cell_events(cell)
    metrics = trace_fidelity_metrics(read_events(cell / "events.jsonl"), reconstructed)

    assert comparison["reconstructed_tool_events"] == 2
    assert metrics["official_metrics"]["tool_capture_recall"] == 1.0
    assert metrics["reconstructed_metrics"]["file_events"] == 1
