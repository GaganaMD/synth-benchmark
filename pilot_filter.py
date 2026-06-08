from __future__ import annotations

import argparse
from pathlib import Path

from synthbench.common import read_json, write_json


def load_scores(model_paths: list[str]) -> dict[str, dict[str, float]]:
    scores = {}
    for path in model_paths:
        data = read_json(path)
        name = data.get("harness") or Path(path).parent.name
        scores[name] = {row["task_id"]: row["score"] for row in data.get("results", [])}
    return scores


def filter_tasks(model_paths: list[str]) -> dict:
    if len(model_paths) < 2:
        data = {"status": "PENDING", "reminder": "Add a 2nd/3rd model before applying discriminability filtering.", "tasks": {}}
        write_json("results/discriminability.json", data)
        print(data["reminder"])
        return data
    scores = load_scores(model_paths)
    task_ids = sorted({tid for model in scores.values() for tid in model})
    kept = {}
    for tid in task_ids:
        vals = [model[tid] for model in scores.values() if tid in model]
        gap = max(vals) - min(vals) if vals else 0.0
        kept[tid] = {"max_gap": gap, "keep": gap >= 0.2}
    data = {"status": "COMPLETE", "tasks": kept}
    write_json("results/discriminability.json", data)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="*")
    args = parser.parse_args()
    filter_tasks(args.models)


if __name__ == "__main__":
    main()

