from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gen_tasks import generate
from synthbench.common import read_json, read_task_bank
from synthbench.config import load_config
from synthbench.registry.datasets import require_dataset
from synthbench.registry.experiments import append_experiment, experiment_record
from synthbench.registry.fixtures import register_fixture
from synthbench.run_store import DEFAULT_HARNESSES, build_manifest, cell_dir, environment_version, hash_tree, initialize_cell


def copy_local_inputs(input_root: Path, task_dir: Path, task_id: str) -> None:
    src = input_root / task_id
    if not src.exists():
        return
    dst = task_dir / "workspace"
    for item in src.iterdir():
        target = dst / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def parse_harnesses(value: str) -> list[str]:
    if value == "all":
        return list(DEFAULT_HARNESSES)
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare replayable benchmark run cells.")
    parser.add_argument("--csv", default="data/v7.csv")
    parser.add_argument("--dataset-version", required=True, help="Registered dataset version every run must reference.")
    parser.add_argument("--tasks-out", default="tasks_complete")
    parser.add_argument("--runs-root", default="runs")
    parser.add_argument("--experiment-registry", default="registry/experiments.jsonl")
    parser.add_argument("--fixture-registry", default="registry/fixtures.jsonl")
    parser.add_argument("--fixture-root", default="immutable_inputs")
    parser.add_argument("--experiment-id", help="Reuse an experiment_id across a matrix; generated if omitted.")
    parser.add_argument("--harnesses", default="codex", help="Comma list or 'all'. Known: codex,codex_hermes,synth_max")
    parser.add_argument("--task-id", action="append", help="Restrict to one or more task IDs.")
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--local-input-root", help="Optional folder containing one subfolder per task id to copy into workspace.")
    parser.add_argument("--storage-backend", default="local", choices=["local", "onedrive", "aws"])
    parser.add_argument("--model-id", help="Exact model/runtime ID to pin in manifest.json for this batch.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    dataset = require_dataset(args.dataset_version)
    if Path(dataset["canonical_csv"]) != csv_path:
        raise SystemExit(f"--csv must match registered canonical_csv for {args.dataset_version}: {dataset['canonical_csv']}")
    tasks_root = Path(args.tasks_out)
    runs_root = Path(args.runs_root)
    config = load_config()

    generate(csv_path, tasks_root)
    rows = {row["id"]: row for row in read_task_bank(csv_path)}
    selected = set(args.task_id or rows.keys())
    harnesses = parse_harnesses(args.harnesses)
    input_root = Path(args.local_input_root) if args.local_input_root else None

    created = []
    for task_id in sorted(selected):
        if task_id not in rows:
            raise SystemExit(f"Unknown task id in {csv_path}: {task_id}")
        task_dir = tasks_root / task_id
        if input_root:
            copy_local_inputs(input_root, task_dir, task_id)
        task = read_json(task_dir / "task.json")
        workspace_hash = hash_tree(task_dir / "workspace").get("tree_sha256") or "empty"
        fixture_version = f"{args.dataset_version}__{task_id}__{workspace_hash[:16]}"
        fixture = register_fixture(
            fixture_version,
            task_dir / "workspace",
            fixture_root=args.fixture_root,
            registry_path=args.fixture_registry,
        )
        for harness in harnesses:
            for seed in range(args.seeds):
                run_dir = cell_dir(runs_root, harness, task_id, seed)
                manifest_path = run_dir / "manifest.json"
                env_version = environment_version()
                model_id = args.model_id or f"TODO_PIN_EXACT_MODEL_FOR_{harness}"
                exp_record = experiment_record(
                    experiment_id=args.experiment_id,
                    run_id=None,
                    task_id=task_id,
                    harness_id=harness,
                    model_id=model_id,
                    seed=seed,
                    dataset_version=args.dataset_version,
                    fixture_version=fixture["fixture_version"],
                    environment_version=env_version,
                    run_dir=run_dir,
                    manifest_path=manifest_path,
                )
                append_experiment(exp_record, args.experiment_registry)
                manifest = build_manifest(
                    task=task,
                    harness=harness,
                    seed=seed,
                    task_dir=task_dir,
                    csv_path=csv_path,
                    config=config,
                    storage_backend=args.storage_backend,
                    model_id=model_id,
                    experiment_record=exp_record,
                    dataset_record=dataset,
                    fixture_record=fixture,
                    environment_version_id=env_version,
                )
                initialize_cell(run_dir=run_dir, task=task, task_dir=task_dir, manifest=manifest, overwrite=args.overwrite)
                created.append(run_dir)

    print(f"Prepared {len(created)} run cells")
    for run_dir in created[:20]:
        print(run_dir)
    if len(created) > 20:
        print(f"... {len(created) - 20} more")


if __name__ == "__main__":
    main()
