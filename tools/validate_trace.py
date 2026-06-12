from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.trace.replay import replay_cell


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and replay a benchmark trace from manifest + events.jsonl.")
    parser.add_argument("--cell", required=True, help="Run cell directory, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--json", action="store_true", help="Print full replay object as JSON.")
    args = parser.parse_args()

    result = replay_cell(args.cell)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        timeline = result["timeline"]
        print(f"valid={result['valid']}")
        print(f"experiment_id={timeline.get('experiment_id')}")
        print(f"run_id={timeline.get('run_id')}")
        print(f"task_id={timeline.get('task_id')}")
        print(f"events={timeline.get('event_count')} tools={timeline.get('tool_event_count')} exceptions={timeline.get('exception_count')}")
        for issue in result["issues"]:
            print(f"ISSUE {issue}")
    if not result["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
