from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from synthbench.common import write_json
from synthbench.run_store import git_value, sha256_file, utc_now


DEFAULT_DATASET_REGISTRY = Path("registry/datasets.jsonl")
LATEST_DATASET_POINTER = Path("registry/latest_dataset.json")


def count_tasks(csv_path: Path) -> int:
    with csv_path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def dataset_record(dataset_version: str, canonical_csv: str | Path) -> dict[str, Any]:
    csv_path = Path(canonical_csv)
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    return {
        "schema_version": "1.0",
        "dataset_version": dataset_version,
        "canonical_csv": csv_path.as_posix(),
        "created_at": utc_now(),
        "git_commit": git_value(["rev-parse", "HEAD"]),
        "task_count": count_tasks(csv_path),
        "checksum": sha256_file(csv_path),
    }


def load_dataset_registry(path: str | Path = DEFAULT_DATASET_REGISTRY) -> list[dict[str, Any]]:
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    records = []
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def find_dataset(dataset_version: str, path: str | Path = DEFAULT_DATASET_REGISTRY) -> dict[str, Any] | None:
    for record in reversed(load_dataset_registry(path)):
        if record.get("dataset_version") == dataset_version:
            return record
    return None


def register_dataset(
    dataset_version: str,
    canonical_csv: str | Path,
    registry_path: str | Path = DEFAULT_DATASET_REGISTRY,
    latest_path: str | Path = LATEST_DATASET_POINTER,
) -> dict[str, Any]:
    existing = find_dataset(dataset_version, registry_path)
    record = dataset_record(dataset_version, canonical_csv)
    if existing:
        comparable = {k: existing.get(k) for k in ("dataset_version", "canonical_csv", "task_count", "checksum")}
        incoming = {k: record.get(k) for k in ("dataset_version", "canonical_csv", "task_count", "checksum")}
        if comparable != incoming:
            raise ValueError(f"dataset_version already exists with different content: {dataset_version}")
        write_json(latest_path, existing)
        return existing

    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True))
        f.write("\n")
    write_json(latest_path, record)
    return record


def require_dataset(dataset_version: str, registry_path: str | Path = DEFAULT_DATASET_REGISTRY) -> dict[str, Any]:
    record = find_dataset(dataset_version, registry_path)
    if not record:
        raise FileNotFoundError(f"dataset version is not registered: {dataset_version}")
    csv_path = Path(record["canonical_csv"])
    if not csv_path.exists():
        raise FileNotFoundError(csv_path)
    checksum = sha256_file(csv_path)
    if checksum != record["checksum"]:
        raise ValueError(f"dataset checksum mismatch for {dataset_version}: {checksum} != {record['checksum']}")
    return record
