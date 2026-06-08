from __future__ import annotations

import re

from metrics.common import metric_result


METRIC_ID = 12


def expected_count(task: dict) -> int:
    text = task.get("expected_tool_calls", "")
    match = re.search(r"(\d+)\+", text)
    if match:
        return int(match.group(1))
    by_complexity = {"Easy": 10, "Medium": 20, "Hard": 30}
    return by_complexity.get(task.get("complexity"), 10)


def synthesize_mock_trajectory(submission: dict) -> dict:
    trajectory = submission.get("trajectory") or {}
    if trajectory:
        return trajectory
    return {
        "tool_calls": submission.get("tool_calls", []),
        "read_all_inputs": submission.get("read_all_inputs", False),
        "wrote_deliverable": submission.get("wrote_deliverable", False),
        "recovered_from_tool_error": submission.get("recovered_from_tool_error", True),
    }


def compute(task: dict, submission: dict, mode: str = "mock") -> dict:
    trajectory = synthesize_mock_trajectory(submission) if mode == "mock" else submission.get("trajectory", {})
    required = expected_count(task)
    checks = {
        "tool_call_count": len(trajectory.get("tool_calls", [])) >= required,
        "read_all_inputs": trajectory.get("read_all_inputs") is True,
        "wrote_deliverable": trajectory.get("wrote_deliverable") is True,
        "recovered_from_tool_error": trajectory.get("recovered_from_tool_error", True) is True,
    }
    value = sum(1 for ok in checks.values() if ok) / len(checks)
    return metric_result(METRIC_ID, value, "mock" if mode == "mock" else "live", checks=checks, required_tool_calls=required)

