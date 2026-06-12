from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from synthbench.run_store import git_value, utc_now


DEFAULT_EXPERIMENT_REGISTRY = Path("registry/experiments.jsonl")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def experiment_record(
    *,
    experiment_id: str | None,
    run_id: str | None,
    task_id: str,
    harness_id: str,
    model_id: str,
    seed: int,
    dataset_version: str,
    fixture_version: str,
    environment_version: str,
    run_dir: str | Path,
    manifest_path: str | Path,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "experiment_id": experiment_id or new_id("exp"),
        "run_id": run_id or new_id("run"),
        "task_id": task_id,
        "harness_id": harness_id,
        "model_id": model_id,
        "seed": seed,
        "dataset_version": dataset_version,
        "fixture_version": fixture_version,
        "environment_version": environment_version,
        "git_commit": git_value(["rev-parse", "HEAD"]),
        "timestamp": utc_now(),
        "run_dir": Path(run_dir).as_posix(),
        "manifest_path": Path(manifest_path).as_posix(),
        "status": "PREPARED",
    }


def append_experiment(record: dict[str, Any], registry_path: str | Path = DEFAULT_EXPERIMENT_REGISTRY) -> dict[str, Any]:
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True))
        f.write("\n")
    return record


def load_experiments(registry_path: str | Path = DEFAULT_EXPERIMENT_REGISTRY) -> list[dict[str, Any]]:
    path = Path(registry_path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def query_experiments(registry_path: str | Path = DEFAULT_EXPERIMENT_REGISTRY, **filters: Any) -> list[dict[str, Any]]:
    records = load_experiments(registry_path)
    active_filters = {k: v for k, v in filters.items() if v not in (None, "")}
    if not active_filters:
        return records
    result = []
    for record in records:
        if all(str(record.get(key)) == str(value) for key, value in active_filters.items()):
            result.append(record)
    return result
