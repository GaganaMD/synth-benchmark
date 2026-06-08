from __future__ import annotations

from metrics.common import metric_result


METRIC_ID = 14


def compute(run_rows: list[dict], mode: str = "mock") -> dict:
    total = len(run_rows)
    timed_out = sum(1 for row in run_rows if row.get("timed_out"))
    points = [
        {
            "task_id": row.get("task_id"),
            "score": row.get("score"),
            "budget": row.get("task", {}).get("time_budget_s") or row.get("time_budget_s"),
        }
        for row in run_rows
    ]
    value = None if total == 0 else timed_out / total
    return metric_result(METRIC_ID, value, "mock" if mode == "mock" else "live", timed_out=timed_out, total=total, score_vs_budget=points)

