from __future__ import annotations

from pathlib import Path
from typing import Any

from metrics.common import iter_results, is_real_value


METRICS = {
    11: "metrics.state_audit",
    12: "metrics.tool_use",
    14: "metrics.timeout",
    15: "metrics.calibration",
    16: "metrics.posting.bad_auto_post",
    17: "metrics.posting.over_queue",
    18: "metrics.deployment.autonomy",
    19: "metrics.deployment.time_saved",
}


def _walk_metric_results(obj: Any):
    if isinstance(obj, dict):
        if "metric_id" in obj and "status" in obj:
            yield obj
        for value in obj.values():
            yield from _walk_metric_results(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_metric_results(item)


def is_live(metric_id: int, results_root: str | Path = "results") -> bool:
    for _, data in iter_results(results_root) or []:
        for result in _walk_metric_results(data):
            if result.get("metric_id") == metric_id and is_real_value(result):
                return True
    return False

