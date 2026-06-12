from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.common import read_json
from synthbench.state.validation import validate_state_cell
from synthbench.trace.events import read_events, validate_trace


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
    for key in (
        "experiment_id",
        "run_id",
        "dataset_version",
        "fixture_version",
        "environment_version",
        "workspace_hash",
        "git_commit",
        "seed",
        "model_id",
        "harness_id",
    ):
        if manifest.get(key) in (None, "", {}):
            issues.append(f"manifest missing {key}")
    if manifest.get("model_id", "").startswith("TODO"):
        issues.append(f"model_id not pinned in {cell / 'manifest.json'}")
    if manifest.get("repo", {}).get("status_short"):
        issues.append("repo had uncommitted changes when manifest was created")
    submission = read_json(cell / "submission.json", default={}) or {}
    if submission.get("status") == "AWAITING_AGENT_OUTPUT":
        issues.append("submission still awaiting agent output")
    else:
        for issue in validate_state_cell(cell):
            issues.append(f"state invalid: {issue}")
    try:
        trace_issues = validate_trace(read_events(cell / "events.jsonl"))
    except ValueError as exc:
        trace_issues = [str(exc)]
    for issue in trace_issues:
        issues.append(f"trace invalid: {issue}")
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
