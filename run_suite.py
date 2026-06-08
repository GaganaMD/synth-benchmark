from __future__ import annotations

import argparse
import time
from pathlib import Path

from auditors import get_auditor
from grader.grade import grade_task
from grader.leakage_guard import assert_clean, load_expected_after_exit
from grader.taxonomy import label_run, report as taxonomy_report
from synthbench.common import read_json, write_json


def run_task(task_dir: Path, mode: str) -> dict:
    task = read_json(task_dir / "task.json")
    start = time.time()
    assert_clean(task_dir / "workspace")
    submission = read_json(task_dir / "submission.json", default={}) or {}
    timed_out = False
    elapsed = time.time() - start
    if task.get("time_budget_s") and elapsed > task["time_budget_s"]:
        timed_out = True
        submission["timed_out"] = True
    expected = load_expected_after_exit(task_dir)
    auditor = get_auditor(task.get("tool", ""))
    try:
        audit = auditor.audit(expected.get("expected_side_effects", {}), submission, mode=mode)
    except NotImplementedError as exc:
        audit = auditor.audit_mock(expected.get("expected_side_effects", {}), submission)
        audit.passed = False
        audit.details.append(str(exc))
    if mode == "live" and not audit.passed:
        submission["_no_contradiction"] = False
    grade = grade_task(task, expected, submission, audit)
    row = {
        "task_id": task["id"],
        "score": grade["partial_credit"],
        "all_pass": grade["all_pass"],
        "elapsed_s": elapsed,
        "cost_usd": submission.get("cost_usd", 0.0),
        "timed_out": timed_out,
        "control_violation": grade["control_violation"],
        "audit": audit.__dict__,
        "grade": grade,
    }
    if row["score"] < 0.5:
        row["taxonomy"] = label_run(row, submission)
    return row


def run_suite(harness: str, mode: str = "mock", tasks_root: str = "tasks") -> dict:
    root = Path(tasks_root)
    results = []
    for task_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        results.append(run_task(task_dir, mode))
    output = {"harness": harness, "mode": mode, "results": results, "taxonomy": taxonomy_report(results)}
    write_json(Path("results") / harness / "results.json", output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--mode", default="mock", choices=["mock", "live"])
    parser.add_argument("--tasks", default="tasks")
    args = parser.parse_args()
    output = run_suite(args.harness, args.mode, args.tasks)
    print(f"Ran {len(output['results'])} tasks; wrote results/{args.harness}/results.json")


if __name__ == "__main__":
    main()

