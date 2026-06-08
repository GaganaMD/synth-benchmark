from __future__ import annotations

import csv
from pathlib import Path

from metrics.common import metric_result


def validate_from_csv(path: str | Path, jury_scores: dict[str, float]) -> dict:
    diffs = []
    with Path(path).open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            task_id = row["task_id"]
            if task_id not in jury_scores:
                continue
            diffs.append(abs(float(jury_scores[task_id]) - float(row["human_score"])))
    mad = sum(diffs) / len(diffs) if diffs else None
    return metric_result("judge_validation", mad, "live" if mad is not None and mad < 3 else "pending", passed=mad is not None and mad < 3)

