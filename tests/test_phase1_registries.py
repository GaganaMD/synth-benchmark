from pathlib import Path

from synthbench.registry.datasets import find_dataset, register_dataset
from synthbench.registry.experiments import append_experiment, experiment_record, query_experiments
from synthbench.registry.fixtures import materialize_from_blobs, register_fixture, require_fixture


def test_dataset_registry_records_checksum_and_task_count(tmp_path: Path):
    csv_path = tmp_path / "tasks.csv"
    csv_path.write_text("id,agent_prompt,rubric,time_budget_s,expert_time_mins,grading_signals,skills\nT1,p,[],1,1,,\n", encoding="utf-8")
    registry = tmp_path / "registry" / "datasets.jsonl"
    latest = tmp_path / "registry" / "latest_dataset.json"

    record = register_dataset("ds1", csv_path, registry, latest)

    assert record["dataset_version"] == "ds1"
    assert record["task_count"] == 1
    assert len(record["checksum"]) == 64
    assert find_dataset("ds1", registry)["checksum"] == record["checksum"]


def test_fixture_registry_stores_and_materializes_blobs(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "input.txt").write_text("hello", encoding="utf-8")
    registry = tmp_path / "registry" / "fixtures.jsonl"
    fixture_root = tmp_path / "immutable_inputs"

    record = register_fixture("fx1", workspace, fixture_root, registry)
    loaded = require_fixture("fx1", registry)
    out = materialize_from_blobs(loaded, tmp_path / "replay")

    assert record["fixture_version"] == "fx1"
    assert record["file_count"] == 1
    assert (out / "input.txt").read_text(encoding="utf-8") == "hello"


def test_experiment_registry_filters_records(tmp_path: Path):
    registry = tmp_path / "registry" / "experiments.jsonl"
    record = experiment_record(
        experiment_id="exp1",
        run_id="run1",
        task_id="T1",
        harness_id="codex",
        model_id="model",
        seed=0,
        dataset_version="ds1",
        fixture_version="fx1",
        environment_version="env1",
        run_dir="runs/codex/T1/seed-0",
        manifest_path="runs/codex/T1/seed-0/manifest.json",
    )
    append_experiment(record, registry)

    assert query_experiments(registry, task_id="T1")[0]["run_id"] == "run1"
    assert query_experiments(registry, harness_id="missing") == []
