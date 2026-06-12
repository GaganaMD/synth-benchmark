from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.registry.experiments import query_experiments


def main() -> None:
    parser = argparse.ArgumentParser(description="Query prepared benchmark experiment records.")
    parser.add_argument("--registry", default="registry/experiments.jsonl")
    parser.add_argument("--experiment-id")
    parser.add_argument("--run-id")
    parser.add_argument("--task-id")
    parser.add_argument("--harness-id")
    parser.add_argument("--model-id")
    parser.add_argument("--dataset-version")
    parser.add_argument("--fixture-version")
    parser.add_argument("--seed")
    args = parser.parse_args()

    rows = query_experiments(
        args.registry,
        experiment_id=args.experiment_id,
        run_id=args.run_id,
        task_id=args.task_id,
        harness_id=args.harness_id,
        model_id=args.model_id,
        dataset_version=args.dataset_version,
        fixture_version=args.fixture_version,
        seed=args.seed,
    )
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
