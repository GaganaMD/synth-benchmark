from __future__ import annotations

from metrics.common import metric_result


METRIC_ID = 15


def mock_pairs() -> list[tuple[float, int]]:
    return [(0.9, 1), (0.8, 1), (0.7, 0), (0.6, 1), (0.4, 0)]


def brier(pairs: list[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    return sum((p - o) ** 2 for p, o in pairs) / len(pairs)


def ece(pairs: list[tuple[float, int]], bins: int = 10) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    error = 0.0
    for i in range(bins):
        low = i / bins
        high = (i + 1) / bins
        bucket = [(p, o) for p, o in pairs if (low <= p < high) or (i == bins - 1 and p == 1.0)]
        if not bucket:
            continue
        conf = sum(p for p, _ in bucket) / len(bucket)
        acc = sum(o for _, o in bucket) / len(bucket)
        error += (len(bucket) / total) * abs(acc - conf)
    return error


def pairs_from_rows(rows: list[dict]) -> list[tuple[float, int]]:
    pairs = []
    for row in rows:
        for item in row.get("confidence_items", []):
            pairs.append((float(item["confidence"]), int(bool(item["correct"]))))
        submission = row.get("submission", {})
        for item in submission.get("confidence_items", []):
            pairs.append((float(item["confidence"]), int(bool(item["correct"]))))
    return pairs


def compute(rows: list[dict] | None = None, mode: str = "mock") -> dict:
    pairs = mock_pairs() if mode == "mock" else pairs_from_rows(rows or [])
    if mode != "mock" and not pairs:
        raise NotImplementedError("TODO: live confidence/correct pairs are not wired")
    return metric_result(METRIC_ID, {"brier": brier(pairs), "ece": ece(pairs)}, "mock" if mode == "mock" else "live", n=len(pairs))

