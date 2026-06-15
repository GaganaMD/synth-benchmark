from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.comparison import generate_comparison_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate same-task cross-run comparison reports without creating a leaderboard.")
    parser.add_argument("--run", action="append", required=True, help="Completed run cell. Provide at least two.")
    parser.add_argument("--output-dir", required=True, help="Directory for comparison_report.json and comparison_report.md.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = generate_comparison_report(args.run, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(Path(args.output_dir) / "comparison_report.json")
        print(Path(args.output_dir) / "comparison_report.md")


if __name__ == "__main__":
    main()
