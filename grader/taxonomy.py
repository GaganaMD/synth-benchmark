from __future__ import annotations

from collections import Counter
from typing import Any


def label_run(result: dict[str, Any], submission: dict[str, Any] | None = None) -> dict[str, str]:
    submission = submission or {}
    if result.get("control_violation"):
        outcome = "control_violation"
    elif result.get("timed_out"):
        outcome = "timeout"
    elif result.get("missing_artifact"):
        outcome = "missing_artifact"
    else:
        outcome = "wrong_or_partial"

    traj = submission.get("trajectory", {})
    if outcome == "control_violation":
        process = "safety_failure"
    elif result.get("timed_out"):
        process = "budget_exhausted"
    elif traj.get("loop_detected"):
        process = "loop"
    elif traj.get("tool_error") and not traj.get("recovered_from_tool_error", False):
        process = "tool_breakdown"
    else:
        process = "planning_miss"
    return {"outcome": outcome, "process": process}


def report(results: list[dict[str, Any]]) -> dict[str, Any]:
    outcomes = Counter()
    processes = Counter()
    fixes = Counter()
    for row in results:
        if row.get("score", 0) >= 0.5:
            continue
        label = row.get("taxonomy") or label_run(row)
        outcomes[label["outcome"]] += 1
        processes[label["process"]] += 1
        fixes[f"fix_{label['process']}"] += 1
    return {"outcome_counts": dict(outcomes), "process_counts": dict(processes), "fix_list": dict(fixes)}

