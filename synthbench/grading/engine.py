from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from synthbench.common import read_json, write_json
from synthbench.grading.operators import SUPPORTED_OPERATORS, grade_operator
from synthbench.schemas.validation import contract_is_valid, validate_cell_contract
from synthbench.trace.events import read_events


DEALBREAKER_OPERATORS = {"contradiction", "state", "safety"}


def grade_cell(
    cell: str | Path,
    rubric: list[dict[str, Any]],
    *,
    output_path: str | Path | None = None,
    task: dict[str, Any] | None = None,
    validate_artifacts: bool = True,
) -> dict[str, Any]:
    cell_dir = Path(cell)
    manifest = read_json(cell_dir / "manifest.json", default={}) or {}
    canonical = read_json(cell_dir / "canonical_output.json", default={}) or {}
    state_diff = read_json(cell_dir / "state" / "state_diff.json", default={}) or {}
    events = read_events(cell_dir / "events.jsonl")
    if task is None:
        task = _load_task(manifest)
    artifact_validation = validate_cell_contract(cell_dir, require_canonical=True) if validate_artifacts else {}

    context = {
        "cell_dir": cell_dir,
        "manifest": manifest,
        "canonical_output": canonical,
        "state_diff": state_diff,
        "events": events,
        "task": task or {},
    }
    criteria = []
    for idx, criterion in enumerate(rubric):
        result = grade_operator(criterion, context)
        result["criterion_index"] = idx
        if criterion.get("operator") not in SUPPORTED_OPERATORS:
            result["status"] = "unsupported"
        else:
            result["status"] = "graded"
        criteria.append(result)

    graded = [item for item in criteria if item.get("status") == "graded"]
    dealbreaker_failed = any(item["operator"] in DEALBREAKER_OPERATORS and item.get("pass_fail") is False for item in graded)
    if dealbreaker_failed:
        operator_score = 0.0
    elif graded:
        operator_score = sum(float(item.get("score") or 0.0) for item in graded) / len(graded)
    else:
        operator_score = 0.0
    result = {
        "schema_version": "1.0",
        "artifact_type": "grading_result",
        "task_id": manifest.get("task_id") or (task or {}).get("id"),
        "run_id": manifest.get("run_id"),
        "experiment_id": manifest.get("experiment_id"),
        "harness_id": manifest.get("harness_id"),
        "model_id": manifest.get("model_id"),
        "inputs": {
            "manifest": "manifest.json",
            "canonical_output": "canonical_output.json",
            "events": "events.jsonl",
            "state_diff": "state/state_diff.json",
        },
        "artifact_validation": {
            "enabled": validate_artifacts,
            "valid": contract_is_valid(artifact_validation) if validate_artifacts else None,
            "results": artifact_validation,
        },
        "rubric_count": len(rubric),
        "graded_count": len(graded),
        "operator_score": operator_score,
        "all_pass": bool(graded) and all(item.get("pass_fail") is True for item in graded),
        "dealbreaker_failed": dealbreaker_failed,
        "operator_results": criteria,
    }
    if output_path is None:
        output_path = cell_dir / "grading_result.json"
    write_json(output_path, result)
    return result


def load_rubric(path: str | Path | None = None, *, task_path: str | Path | None = None, inline_json: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    task = None
    if inline_json:
        parsed = json.loads(inline_json)
        return _rubric_list(parsed), task
    if path:
        parsed = read_json(path, default=None)
        return _rubric_list(parsed), task
    if task_path:
        task = read_json(task_path, default={}) or {}
        return _rubric_list(task.get("rubric", [])), task
    raise ValueError("provide rubric path, task path, or inline rubric JSON")


def _rubric_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and "rubric" in value:
        value = value["rubric"]
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("rubric must be a list of objects")
    return value


def _load_task(manifest: dict[str, Any]) -> dict[str, Any] | None:
    task_dir = manifest.get("task_dir")
    if not task_dir:
        return None
    task_path = Path(task_dir) / "task.json"
    if not task_path.exists():
        return None
    task = read_json(task_path, default=None)
    return task if isinstance(task, dict) else None
