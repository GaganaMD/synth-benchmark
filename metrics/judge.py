from __future__ import annotations

from grader.judge import DIMENSIONS, anchors_for_dimension
from synthbench.config import load_config


def call_model(model_id: str, prompt: str) -> float:
    # TODO: wire real jury model API call once model credentials are available.
    if model_id.startswith("TODO_"):
        raise NotImplementedError("TODO: real jury model IDs/API keys are not wired")
    raise NotImplementedError("TODO: implement live model client")


def validate_anchors(dimensions: list[str] | None = None) -> None:
    for dim in dimensions or DIMENSIONS:
        anchors = anchors_for_dimension(dim)
        if len(anchors.get("good", [])) != 3 or len(anchors.get("bad", [])) != 3:
            raise ValueError(f"{dim} requires exactly 3 good and 3 bad anchors")


def live_jury(answer: str, criterion: str, config_path: str = "config.yaml") -> dict:
    validate_anchors()
    cfg = load_config(config_path)
    model_ids = cfg.get("judge_model_ids", [])
    if len(model_ids) != 3:
        raise ValueError("judge_model_ids must contain exactly 3 models")
    scores = []
    for dim in DIMENSIONS:
        prompt = f"Dimension={dim}\nCriterion={criterion}\nAnswer={answer}"
        dim_scores = [call_model(model_id, prompt) for model_id in model_ids]
        scores.extend(dim_scores)
    mean = sum(scores) / len(scores)
    return {"mean": mean, "scores": scores, "status": "live"}

