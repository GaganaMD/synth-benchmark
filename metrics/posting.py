from __future__ import annotations

from metrics.common import metric_result


BAD_AUTO_POST_ID = 16
OVER_QUEUE_ID = 17


def compute_bad_auto_post(audit_rows: list[dict] | None = None, mode: str = "mock") -> dict:
    if mode == "mock":
        return metric_result(BAD_AUTO_POST_ID, None, "mock", wrong_posted=None, posted=None)
    wrong = sum(int(row.get("wrong_posted", 0)) for row in (audit_rows or []))
    posted = sum(int(row.get("posted", 0)) for row in (audit_rows or []))
    if posted == 0 and not audit_rows:
        raise NotImplementedError("TODO: live posting audit counts are not wired")
    return metric_result(BAD_AUTO_POST_ID, None if posted == 0 else wrong / posted, "live", wrong_posted=wrong, posted=posted)


def compute_over_queue(audit_rows: list[dict] | None = None, mode: str = "mock") -> dict:
    if mode == "mock":
        return metric_result(OVER_QUEUE_ID, None, "mock", unnecessarily_queued=None, queued=None)
    unnecessary = sum(int(row.get("unnecessarily_queued", 0)) for row in (audit_rows or []))
    queued = sum(int(row.get("queued", 0)) for row in (audit_rows or []))
    if queued == 0 and not audit_rows:
        raise NotImplementedError("TODO: live queue audit counts are not wired")
    return metric_result(OVER_QUEUE_ID, None if queued == 0 else unnecessary / queued, "live", unnecessarily_queued=unnecessary, queued=queued)

