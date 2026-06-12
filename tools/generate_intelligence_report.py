from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.intelligence import generate_run_intelligence_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate single-run experiment intelligence reports.")
    parser.add_argument("--cell", required=True, help="Run cell directory.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = generate_run_intelligence_report(args.cell)
    result = {
        "json": str(Path(args.cell) / "run_intelligence_report.json"),
        "markdown": str(Path(args.cell) / "run_intelligence_report.md"),
        "run_id": report.get("run_metadata", {}).get("run_id"),
        "task_id": report.get("run_metadata", {}).get("task_id"),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"intelligence report written: {result['json']}")
        print(f"intelligence report written: {result['markdown']}")


if __name__ == "__main__":
    main()
