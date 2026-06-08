from __future__ import annotations

from pathlib import Path
from typing import Any

from synthbench.common import read_json


def metric_result(metric_id: int, value: Any, status: str, **extra: Any) -> dict[str, Any]:
    return {"metric_id": metric_id, "value": value, "status": status, **extra}


def iter_results(results_root: str | Path = "results"):
    root = Path(results_root)
    if not root.exists():
        return
    for path in root.glob("*/results.json"):
        data = read_json(path)
        if data:
            yield path, data


def is_real_value(result: dict[str, Any]) -> bool:
    return result.get("status") == "live" and result.get("value") is not None

