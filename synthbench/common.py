from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


CANONICAL_CSV = Path("data/v7.csv")


def read_task_bank(csv_path: str | Path = CANONICAL_CSV) -> list[dict[str, Any]]:
    path = Path(csv_path)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["rubric"] = parse_json_array(row.get("rubric", ""))
        row["time_budget_s"] = int(float(row.get("time_budget_s") or 0))
        row["expert_time_mins"] = int(float(row.get("expert_time_mins") or 0))
        row["grading_signals"] = split_csvish(row.get("grading_signals", ""))
        row["skills"] = split_csvish(row.get("skills", ""))
    return rows


def parse_json_array(value: str) -> list[dict[str, Any]]:
    if not value:
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("rubric must parse to a JSON array")
    return parsed


def split_csvish(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def slugify(value: str, fallback: str = "workspace") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value or fallback


def normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).lower()


def as_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {normalize_scalar(v) for v in value if normalize_scalar(v)}
    text = str(value)
    parts = re.split(r"[|,\n;]+", text)
    return {normalize_scalar(p) for p in parts if normalize_scalar(p)}


def criterion_key(criterion: dict[str, Any]) -> str:
    return slugify(str(criterion.get("criteria") or criterion.get("operator") or "criterion"))


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

