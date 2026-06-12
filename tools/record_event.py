from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.run_store import append_event


def main() -> None:
    parser = argparse.ArgumentParser(description="Append one event to a benchmark cell events.jsonl.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--event-type", required=True, choices=["plan", "tool_call", "observation", "self_verify", "final", "error", "note"])
    parser.add_argument("--tool")
    parser.add_argument("--action", required=True)
    parser.add_argument("--input")
    parser.add_argument("--success", choices=["true", "false"], default="true")
    parser.add_argument("--error")
    parser.add_argument("--metadata", help="JSON object with extra fields.")
    args = parser.parse_args()

    event = {
        "event_type": args.event_type,
        "tool": args.tool,
        "action": args.action,
        "input": args.input,
        "success": args.success == "true",
        "error": args.error,
    }
    if args.metadata:
        extra = json.loads(args.metadata)
        if not isinstance(extra, dict):
            raise SystemExit("--metadata must be a JSON object")
        event["metadata"] = extra
    append_event(Path(args.cell) / "events.jsonl", event)
    print(f"Appended {args.event_type} event to {args.cell}/events.jsonl")


if __name__ == "__main__":
    main()
