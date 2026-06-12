from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json, write_json
from synthbench.run_store import hash_tree, utc_now
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, load_snapshot, write_snapshot
from synthbench.trace.events import append_event, make_task_complete_event, parse_timestamp, read_events


def infer_trajectory(events: list[dict], final_output: str, artifacts_dir: Path) -> dict:
    tool_calls = [event for event in events if event.get("event_type") in {"tool_call", "tool_result"}]
    errors = [event for event in events if event.get("event_type") == "exception" or event.get("success") is False]
    return {
        "tool_calls": tool_calls,
        "read_all_inputs": any(event.get("event_type") == "file_read" and event.get("metadata", {}).get("read_all_inputs") is True for event in events),
        "wrote_deliverable": bool(list(artifacts_dir.glob("*"))) or "results/" in final_output,
        "recovered_from_tool_error": not errors or any(event.get("recovered") is True or event.get("recovery_action") for event in errors),
        "self_verified": any(event.get("event_type") == "verification" for event in events),
    }


def runtime_from_events(events: list[dict], completed_at: str) -> float:
    if not events:
        return 0.0
    start = parse_timestamp(events[0]["timestamp"])
    end = parse_timestamp(completed_at)
    return max(0.0, (end - start).total_seconds())


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize a manual Codex/Hermes/Synth-Max cell into submission.json.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--task-dir", required=True, help="Generated task dir, e.g. tasks_complete/TXN-001")
    parser.add_argument("--final-output-file", help="Markdown/text file containing the final agent response.")
    parser.add_argument("--status", default="COMPLETED", choices=["COMPLETED", "FAILED", "TIMED_OUT"])
    parser.add_argument("--control-violation", action="store_true")
    parser.add_argument("--contradiction", action="store_true")
    parser.add_argument("--input-tokens", type=int)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--estimated-cost", type=float)
    parser.add_argument("--copy-to-task", action="store_true", help="Also overwrite task_dir/submission.json for run_suite.py.")
    args = parser.parse_args()

    cell = Path(args.cell)
    task_dir = Path(args.task_dir)
    manifest = read_json(cell / "manifest.json", default={}) or {}
    final_output = ""
    if args.final_output_file:
        final_output = Path(args.final_output_file).read_text(encoding="utf-8")
    elif (cell / "final_output.md").exists():
        final_output = (cell / "final_output.md").read_text(encoding="utf-8")

    events = read_events(cell / "events.jsonl")
    completed_at = utc_now()
    if not any(event.get("event_type") == "task_complete" for event in events):
        append_event(
            cell / "events.jsonl",
            make_task_complete_event(
                manifest,
                runtime_seconds=runtime_from_events(events, completed_at),
                step_count=len(events),
                input_tokens=args.input_tokens,
                output_tokens=args.output_tokens,
                estimated_cost=args.estimated_cost,
            ),
        )
        events = read_events(cell / "events.jsonl")
    artifacts_dir = cell / "artifacts"
    s1_path = cell / "state" / "S1.json"
    s1 = capture_snapshot(
        snapshot_id=f"S1_{manifest.get('run_id') or manifest.get('task_id')}",
        workspace_dir=manifest.get("workspace_dir"),
        outputs_dir=artifacts_dir,
        mock_state_path=cell / "state" / "mock_state.json",
    )
    write_snapshot(s1, s1_path)
    s0_path = cell / "state" / "S0.json"
    if s0_path.exists():
        diff = compute_state_diff(load_snapshot(s0_path), s1)
        diff["s0_snapshot_path"] = s0_path.as_posix()
        diff["s1_snapshot_path"] = s1_path.as_posix()
        write_state_diff(diff, cell / "state" / "state_diff.json")
    submission = read_json(cell / "submission.json", default={}) or {}
    submission.update(
        {
            "task_id": manifest.get("task_id") or submission.get("task_id"),
            "status": args.status,
            "completed_at": completed_at,
            "final_output": final_output,
            "deliverables": [p.relative_to(cell).as_posix() for p in sorted(artifacts_dir.rglob("*")) if p.is_file()],
            "trajectory": infer_trajectory(events, final_output, artifacts_dir),
            "run_manifest": "manifest.json",
            "events_file": "events.jsonl",
            "artifact_hash": hash_tree(artifacts_dir),
            "control_violation": args.control_violation,
            "_no_contradiction": not args.contradiction,
            "input_tokens": args.input_tokens,
            "output_tokens": args.output_tokens,
            "estimated_cost": args.estimated_cost,
        }
    )
    if args.status == "TIMED_OUT":
        submission["timed_out"] = True
    write_json(cell / "submission.json", submission)
    if args.copy_to_task:
        write_json(task_dir / "submission.json", submission)
        results_dir = task_dir / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        for path in artifacts_dir.rglob("*"):
            if path.is_file():
                target = results_dir / path.relative_to(artifacts_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    print(f"Finalized {cell / 'submission.json'}")
    if args.copy_to_task:
        print(f"Updated {task_dir / 'submission.json'}")


if __name__ == "__main__":
    main()
