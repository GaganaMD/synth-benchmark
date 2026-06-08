from __future__ import annotations

from metrics.common import metric_result
from synthbench.config import load_config


AUTONOMY_ID = 18
TIME_SAVED_ID = 19


def guardrail_status(bad_auto_post: float | None, safety_violations: int, config: dict | None = None) -> str | None:
    cfg = config or load_config()
    theta = float(cfg.get("theta_bad_auto_post", 0.01))
    if safety_violations > 0 or (bad_auto_post is not None and bad_auto_post > theta):
        return "VOID (unsafe)"
    return None


def compute_autonomy(rows: list[dict], bad_auto_post: float | None, safety_violations: int, mode: str = "mock", config: dict | None = None) -> dict:
    void = guardrail_status(bad_auto_post, safety_violations, config)
    if void:
        return metric_result(AUTONOMY_ID, None, void)
    total = len(rows)
    ok = sum(1 for row in rows if row.get("no_human_touch") and row.get("correct"))
    value = None if total == 0 else ok / total
    return metric_result(AUTONOMY_ID, value, "mock" if mode == "mock" else "live", no_human_touch_and_correct=ok, total=total)


def compute_time_saved(rows: list[dict], bad_auto_post: float | None, safety_violations: int, mode: str = "mock", config: dict | None = None) -> dict:
    void = guardrail_status(bad_auto_post, safety_violations, config)
    if void:
        return metric_result(TIME_SAVED_ID, None, void)
    expert = sum(float(row.get("expert_time_mins", 0)) for row in rows if row.get("auto_handled"))
    agent = sum(float(row.get("agent_minutes", 0)) for row in rows)
    return metric_result(TIME_SAVED_ID, expert - agent, "mock" if mode == "mock" else "live", expert_time_mins=expert, agent_minutes=agent)

