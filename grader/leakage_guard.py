from __future__ import annotations

from pathlib import Path

from synthbench.common import read_json


GRADING_ASSETS = {"expected.json", "reference_answer.json", "gold.json"}


def assert_clean(workspace: str | Path) -> None:
    root = Path(workspace)
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.name in GRADING_ASSETS:
            raise RuntimeError(f"grading asset leaked into workspace: {path}")


def load_expected_after_exit(task_dir: str | Path) -> dict:
    task_dir = Path(task_dir)
    assert_clean(task_dir / "workspace")
    expected = read_json(task_dir / "expected.json")
    if expected is None:
        raise FileNotFoundError(task_dir / "expected.json")
    return expected

