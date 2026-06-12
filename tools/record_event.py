from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json
from synthbench.trace.events import (
    EVENT_TYPES,
    append_event,
    make_event,
    make_exception_event,
    make_state_checkpoint_event,
    make_task_complete_event,
    make_tool_call_event,
    make_tool_result_event,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append one event to a benchmark cell events.jsonl.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--event-type", required=True, choices=sorted(EVENT_TYPES - {"task_start"}))
    parser.add_argument("--tool-name")
    parser.add_argument("--arguments", help="JSON value for tool arguments.")
    parser.add_argument("--result", help="JSON value or plain text result.")
    parser.add_argument("--success", choices=["true", "false"])
    parser.add_argument("--latency-ms", type=float)
    parser.add_argument("--exception-type")
    parser.add_argument("--message")
    parser.add_argument("--recovered", choices=["true", "false"])
    parser.add_argument("--recovery-action")
    parser.add_argument("--checkpoint-id")
    parser.add_argument("--state-summary", help="JSON value or plain text checkpoint summary.")
    parser.add_argument("--runtime-seconds", type=float)
    parser.add_argument("--step-count", type=int)
    parser.add_argument("--input-tokens", type=int)
    parser.add_argument("--output-tokens", type=int)
    parser.add_argument("--estimated-cost", type=float)
    parser.add_argument("--metadata", help="JSON object with extra fields.")
    args = parser.parse_args()

    cell = Path(args.cell)
    manifest = read_json(cell / "manifest.json")
    if not manifest:
        raise SystemExit(f"missing manifest: {cell / 'manifest.json'}")

    def parse_value(value):
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    payload = {
        "tool_name": args.tool_name,
        "arguments": parse_value(args.arguments),
        "result": parse_value(args.result),
        "success": None if args.success is None else args.success == "true",
        "latency_ms": args.latency_ms,
        "exception_type": args.exception_type,
        "message": args.message,
        "recovered": None if args.recovered is None else args.recovered == "true",
        "recovery_action": args.recovery_action,
        "checkpoint_id": args.checkpoint_id,
        "state_summary": parse_value(args.state_summary),
        "runtime_seconds": args.runtime_seconds,
        "step_count": args.step_count,
        "input_tokens": args.input_tokens,
        "output_tokens": args.output_tokens,
        "estimated_cost": args.estimated_cost,
    }
    if args.metadata:
        extra = json.loads(args.metadata)
        if not isinstance(extra, dict):
            raise SystemExit("--metadata must be a JSON object")
        payload["metadata"] = extra
    if args.event_type == "tool_call":
        event = make_tool_call_event(
            manifest,
            tool_name=args.tool_name or "",
            arguments=payload["arguments"],
            result=payload["result"],
            success=payload["success"],
            latency_ms=payload["latency_ms"],
        )
        if payload.get("metadata"):
            event["metadata"] = payload["metadata"]
    elif args.event_type == "tool_result":
        event = make_tool_result_event(
            manifest,
            tool_name=args.tool_name or "",
            result=payload["result"],
            success=payload["success"],
            latency_ms=payload["latency_ms"],
        )
        if payload.get("metadata"):
            event["metadata"] = payload["metadata"]
    elif args.event_type == "exception":
        event = make_exception_event(
            manifest,
            exception_type=args.exception_type or "",
            message=args.message or "",
            recovered=payload["recovered"],
            recovery_action=args.recovery_action,
        )
        if payload.get("metadata"):
            event["metadata"] = payload["metadata"]
    elif args.event_type == "state_checkpoint":
        event = make_state_checkpoint_event(
            manifest,
            checkpoint_id=args.checkpoint_id or "",
            state_summary=payload["state_summary"],
        )
        if payload.get("metadata"):
            event["metadata"] = payload["metadata"]
    elif args.event_type == "task_complete":
        event = make_task_complete_event(
            manifest,
            runtime_seconds=args.runtime_seconds,
            step_count=args.step_count,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            estimated_cost=args.estimated_cost,
        )
        if payload.get("metadata"):
            event["metadata"] = payload["metadata"]
    else:
        event = make_event(manifest, args.event_type, **payload)
    append_event(cell / "events.jsonl", event)
    print(f"Appended {args.event_type} event to {args.cell}/events.jsonl")


if __name__ == "__main__":
    main()
