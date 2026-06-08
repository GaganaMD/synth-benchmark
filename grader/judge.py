from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


DIMENSIONS = ["Accuracy", "Groundedness", "Citation Rate", "Relevance", "Depth", "Clarity", "Structure"]
JURY_MODELS = ["mock_jury_a", "mock_jury_b", "mock_jury_c"]


@dataclass
class JudgeResult:
    dimension: str
    mean: float
    se: float
    scores: list[float]


def call_model(model: str, prompt: str) -> float:
    # TODO: wire live jury model IDs and API calls.
    return 75.0


def anchors_for_dimension(dimension: str) -> dict[str, list[str]]:
    # TODO: replace placeholders with BI-authored 3 good / 3 bad anchor examples per dimension.
    return {
        "good": [f"{dimension} good anchor {i}" for i in range(1, 4)],
        "bad": [f"{dimension} bad anchor {i}" for i in range(1, 4)],
    }


def score_dimension(dimension: str, answer: str, criterion: str, models: list[str] | None = None) -> JudgeResult:
    models = models or JURY_MODELS
    anchors = anchors_for_dimension(dimension)
    prompt = f"Dimension: {dimension}\nCriterion: {criterion}\nAnchors: {anchors}\nAnswer: {answer}"
    scores = [call_model(model, prompt) for model in models]
    mean = sum(scores) / len(scores)
    if len(scores) == 1:
        se = 0.0
    else:
        var = sum((s - mean) ** 2 for s in scores) / (len(scores) - 1)
        se = sqrt(var / len(scores))
    return JudgeResult(dimension, mean, se, scores)


def judge(answer: str, criterion: str, dimensions: list[str] | None = None) -> dict:
    results = [score_dimension(dim, answer, criterion) for dim in (dimensions or DIMENSIONS)]
    means = [r.mean for r in results]
    overall = sum(means) / len(means) if means else 0.0
    return {
        "overall_mean": overall,
        "dimensions": [r.__dict__ for r in results],
        "mock": True,
    }

