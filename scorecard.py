from __future__ import annotations

import argparse
from collections import defaultdict

from grader.grade import mean_se
from synthbench.common import read_json


def scorecard(results_path: str) -> dict:
    data = read_json(results_path)
    buckets = defaultdict(list)
    for row in data.get("results", []):
        task = row.get("grade", {})
        score = row.get("score", 0.0)
        task_meta = row.get("task", {})
        buckets["overall"].append(score)
        for key in ("category", "service_line", "bi_band", "tool"):
            if task_meta.get(key):
                buckets[f"{key}:{task_meta[key]}"].append(score)
    categories = [vals for name, vals in buckets.items() if name.startswith("category:")]
    if categories:
        class_means = [mean_se(vals)[0] for vals in categories]
        buckets["class_balanced_accuracy"] = class_means
    return {name: {"mean": mean_se(vals)[0], "se": mean_se(vals)[1], "n": len(vals)} for name, vals in buckets.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results")
    args = parser.parse_args()
    for name, row in scorecard(args.results).items():
        print(f"{name}: mean={row['mean']:.3f} se={row['se']:.3f} n={row['n']}")


if __name__ == "__main__":
    main()
