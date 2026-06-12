from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.grading.engine import grade_cell, load_rubric


def main() -> None:
    parser = argparse.ArgumentParser(description="Grade one run cell using rubric operators over normalized artifacts.")
    parser.add_argument("--cell", required=True, help="Run cell directory.")
    parser.add_argument("--rubric", help="JSON file containing a rubric list or object with rubric field.")
    parser.add_argument("--task-json", help="Task JSON containing rubric and optional expected_tool_calls.")
    parser.add_argument("--rubric-json", help="Inline rubric JSON list.")
    parser.add_argument("--output", help="Output path. Defaults to <cell>/grading_result.json")
    parser.add_argument("--skip-artifact-validation", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    provided = [bool(args.rubric), bool(args.task_json), bool(args.rubric_json)]
    if sum(provided) != 1:
        raise SystemExit("provide exactly one of --rubric, --task-json, or --rubric-json")
    rubric, task = load_rubric(args.rubric, task_path=args.task_json, inline_json=args.rubric_json)
    result = grade_cell(
        args.cell,
        rubric,
        output_path=args.output,
        task=task,
        validate_artifacts=not args.skip_artifact_validation,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"graded {result['task_id']}: score={result['operator_score']:.3f} all_pass={result['all_pass']}")
        print(args.output or str(Path(args.cell) / "grading_result.json"))


if __name__ == "__main__":
    main()
