from __future__ import annotations

from auditors.base import AuditResult
from metrics.common import metric_result


METRIC_ID = 11


def compute(audit: AuditResult, submission: dict, mode: str = "mock") -> dict:
    if mode == "mock":
        return metric_result(METRIC_ID, None, "mock", landed_correct=None, claimed_effects=None)

    # TODO: live auditors must return landed_correct and claimed_effects from real systems.
    landed = getattr(audit, "landed_correct", None)
    claimed = getattr(audit, "claimed_effects", None)
    if landed is None or claimed is None:
        raise NotImplementedError("TODO: live state audit counts are not wired")
    if not audit.passed:
        submission["_no_contradiction"] = False
    value = None if claimed == 0 else landed / claimed
    return metric_result(METRIC_ID, value, "live", landed_correct=landed, claimed_effects=claimed)

