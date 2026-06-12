from __future__ import annotations

import argparse
import time
from pathlib import Path

from auditors import get_auditor
from grader.grade import grade_task
from grader.leakage_guard import assert_clean, load_expected_after_exit
from grader.taxonomy import label_run, report as taxonomy_report
from metrics import state_audit, tool_use
from metrics.calibration import compute as compute_calibration
from metrics.deployment import compute_autonomy, compute_time_saved
from metrics.posting import compute_bad_auto_post, compute_over_queue
from metrics.timeout import compute as compute_timeout
from synthbench.common import read_json, write_json


def pending_metric(metric_id, message):
    return {"metric_id": metric_id, "value": None, "status": "pending live exec", "error": str(message)}


def compute_state_metric(audit, submission, mode):
    try:
        return state_audit.compute(audit, submission, mode=mode)
    except NotImplementedError as exc:
        return pending_metric(11, exc)


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
        "task": {
            "category": task.get("category"),
            "service_line": task.get("service_line"),
            "bi_band": task.get("bi_band"),
            "tool": task.get("tool"),
            "time_budget_s": task.get("time_budget_s"),
        },
        "score": grade["partial_credit"],
        "all_pass": grade["all_pass"],
        "elapsed_s": elapsed,
        "cost_usd": submission.get("cost_usd", 0.0),
        "timed_out": timed_out,
        "control_violation": grade["control_violation"],
        "audit": audit.__dict__,
        "grade": grade,
        "metrics": {
            "state_audit": compute_state_metric(audit, submission, mode),
            "tool_use": tool_use.compute(task, submission, mode=mode),
        },
    }
    if row["score"] < 0.5:
        row["taxonomy"] = label_run(row, submission)
    return row


def run_suite(harness: str, mode: str = "mock", tasks_root: str = "tasks", task_ids: set[str] | None = None) -> dict:
    root = Path(tasks_root)
    results = []
    for task_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if task_ids and task_dir.name not in task_ids:
            continue
        results.append(run_task(task_dir, mode))
    try:
        bad_auto_post = compute_bad_auto_post([], mode="mock" if mode == "mock" else "live")
    except NotImplementedError as exc:
        bad_auto_post = pending_metric(16, exc)
    try:
        over_queue = compute_over_queue([], mode="mock" if mode == "mock" else "live")
    except NotImplementedError as exc:
        over_queue = pending_metric(17, exc)
    safety_violations = sum(1 for row in results if row.get("control_violation"))
    deployment_rows = [
        {
            "no_human_touch": row.get("all_pass"),
            "correct": row.get("all_pass"),
            "auto_handled": row.get("all_pass"),
            "expert_time_mins": 0,
            "agent_minutes": row.get("elapsed_s", 0) / 60,
        }
        for row in results
    ]
    suite_metrics = {
        "timeout": compute_timeout(results, mode=mode),
        "calibration": (
            compute_calibration(results, mode="mock")
            if mode == "mock"
            else pending_metric(15, "TODO: live confidence/correct pairs are not wired")
        ),
        "bad_auto_post": bad_auto_post,
        "over_queue": over_queue,
        "autonomy": compute_autonomy(deployment_rows, bad_auto_post.get("value"), safety_violations, mode=mode),
        "time_saved": compute_time_saved(deployment_rows, bad_auto_post.get("value"), safety_violations, mode=mode),
    }
    output = {"harness": harness, "mode": mode, "results": results, "suite_metrics": suite_metrics, "taxonomy": taxonomy_report(results)}
    write_json(Path("results") / harness / "results.json", output)
    if mode == "live":
        from tools.update_metric_status import update_metric_status

        update_metric_status("docs/metrics_v2.md", "results")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness", required=True)
    parser.add_argument("--mode", default="mock", choices=["mock", "live"])
    parser.add_argument("--tasks", default="tasks")
    parser.add_argument("--task-id", action="append", help="Restrict grading to one or more task IDs.")
    args = parser.parse_args()
    output = run_suite(args.harness, args.mode, args.tasks, set(args.task_id) if args.task_id else None)
    print(f"Ran {len(output['results'])} tasks; wrote results/{args.harness}/results.json")


if __name__ == "__main__":
    main()
