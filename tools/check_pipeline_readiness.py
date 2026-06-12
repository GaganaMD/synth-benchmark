from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json


REQUIRED_CELL_FILES = [
    "manifest.json",
    "prompt.txt",
    "events.jsonl",
    "submission.json",
    "state/state_diff.json",
]


def check_cell(cell: Path) -> list[str]:
    issues = []
    for rel in REQUIRED_CELL_FILES:
        if not (cell / rel).exists():
            issues.append(f"missing {cell / rel}")
    manifest = read_json(cell / "manifest.json", default={}) or {}
    if manifest.get("model_id", "").startswith("TODO"):
        issues.append(f"model_id not pinned in {cell / 'manifest.json'}")
    if manifest.get("repo", {}).get("status_short"):
        issues.append("repo had uncommitted changes when manifest was created")
    submission = read_json(cell / "submission.json", default={}) or {}
    if submission.get("status") == "AWAITING_AGENT_OUTPUT":
        issues.append("submission still awaiting agent output")
    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Check benchmark pipeline readiness.")
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument("--cell", help="Specific cell directory to check.")
    args = parser.parse_args()

    cells = [Path(args.cell)] if args.cell else [p for p in Path(args.runs_root).glob("*/*/seed-*") if p.is_dir()]
    if not cells:
        raise SystemExit("No run cells found. Run tools/prepare_benchmark_run.py first.")

    failed = 0
    for cell in sorted(cells):
        issues = check_cell(cell)
        if issues:
            failed += 1
            print(f"FAIL {cell}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"OK   {cell}")
    if failed:
        raise SystemExit(f"{failed} cell(s) are not ready")


if __name__ == "__main__":
    main()
