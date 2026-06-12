from __future__ import annotations

from pathlib import Path
from typing import Any

from synthbench.common import read_json
from synthbench.trace.events import parse_timestamp, read_events, validate_trace


def load_trace(cell_dir: str | Path) -> dict[str, Any]:
    root = Path(cell_dir)
    manifest = read_json(root / "manifest.json", default={}) or {}
    events = read_events(root / "events.jsonl")
    state_dir = root / "state"
    state = {
        "s0": read_json(state_dir / "S0.json", default=None),
        "s1": read_json(state_dir / "S1.json", default=None),
        "diff": read_json(state_dir / "state_diff.json", default=None),
        "side_effect_audit": read_json(state_dir / "side_effect_audit.json", default=None),
    }
    return {"cell_dir": root.as_posix(), "manifest": manifest, "events": events, "state": state}


def reconstruct_timeline(manifest: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(events, key=lambda event: parse_timestamp(event["timestamp"]))
    tool_events = [event for event in ordered if event.get("event_type") in {"tool_call", "tool_result"}]
    exceptions = [event for event in ordered if event.get("event_type") == "exception"]
    checkpoints = [event for event in ordered if event.get("event_type") == "state_checkpoint"]
    complete = next((event for event in reversed(ordered) if event.get("event_type") == "task_complete"), None)
    runtime_seconds = complete.get("runtime_seconds") if complete else None
    step_count = complete.get("step_count") if complete else len(ordered)
    return {
        "experiment_id": manifest.get("experiment_id"),
        "run_id": manifest.get("run_id"),
        "task_id": manifest.get("task_id"),
        "harness_id": manifest.get("harness_id"),
        "model_id": manifest.get("model_id"),
        "dataset_version": manifest.get("dataset_version"),
        "fixture_version": manifest.get("fixture_version"),
        "event_count": len(ordered),
        "step_count": step_count,
        "runtime_seconds": runtime_seconds,
        "tool_event_count": len(tool_events),
        "exception_count": len(exceptions),
        "checkpoint_count": len(checkpoints),
        "events": ordered,
    }


def replay_cell(cell_dir: str | Path) -> dict[str, Any]:
    trace = load_trace(cell_dir)
    issues = validate_trace(trace["events"])
    return {
        "cell_dir": trace["cell_dir"],
        "valid": not issues,
        "issues": issues,
        "timeline": reconstruct_timeline(trace["manifest"], trace["events"]),
        "state": trace["state"],
    }
