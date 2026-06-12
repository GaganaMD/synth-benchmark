from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthbench.registry.datasets import register_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Register a canonical benchmark dataset CSV.")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--registry", default="registry/datasets.jsonl")
    parser.add_argument("--latest", default="registry/latest_dataset.json")
    args = parser.parse_args()

    record = register_dataset(args.dataset_version, args.csv, args.registry, args.latest)
    print(f"registered dataset {record['dataset_version']} tasks={record['task_count']} checksum={record['checksum']}")


if __name__ == "__main__":
    main()
