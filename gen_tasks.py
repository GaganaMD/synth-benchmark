from __future__ import annotations

import argparse
from pathlib import Path

from synthbench.common import CANONICAL_CSV, criterion_key, read_task_bank, write_json


def workspace_dirs(workspace: str) -> list[str]:
    raw_parts = [part.strip() for part in workspace.split(",") if part.strip()]
    if not raw_parts:
        return ["inputs"]
    dirs: list[str] = []
    for part in raw_parts:
        folder = part.split(":", 1)[0].strip()
        folder = folder.replace("...", "").strip()
        if "/" in folder:
            folder = folder.split("/", 1)[0]
        folder = folder.strip(" ./") or "inputs"
        if folder not in dirs:
            dirs.append(folder)
    return dirs


def expected_fields(rubric: list[dict]) -> list[dict]:
    fields = []
    for item in rubric:
        fields.append(
            {
                "key": criterion_key(item),
                "operator": item.get("operator"),
                "criteria": item.get("criteria"),
                "expected": item.get("value"),
                "tolerance": item.get("tolerance"),
                "status": "AWAITING_BI_GROUND_TRUTH" if "value" not in item else "SEE_RUBRIC_VALUE",
            }
        )
    return fields


def parse_side_effects(text: str) -> dict:
    if not text:
        return {"mode": "none", "requirements": []}
    requirements = [part.strip() for part in text.split(";") if part.strip()]
    return {"mode": "mock_shape_only", "requirements": requirements or [text.strip()]}


def generate(csv_path: str | Path = CANONICAL_CSV, tasks_dir: str | Path = "tasks") -> list[Path]:
    rows = read_task_bank(csv_path)
    root = Path(tasks_dir)
    root.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for row in rows:
        task_dir = root / row["id"]
        workspace_root = task_dir / "workspace"
        workspace_root.mkdir(parents=True, exist_ok=True)
        for folder in workspace_dirs(row.get("workspace", "")):
            folder_path = workspace_root / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            readme = folder_path / "README.md"
            if not readme.exists():
                readme.write_text(
                    "# Placeholder Input Folder\n\n"
                    "BI must drop the task-specific input assets here before live runs.\n"
                    f"Source workspace spec: `{row.get('workspace', '')}`\n",
                    encoding="utf-8",
                )
        write_json(task_dir / "task.json", row)
        write_json(
            task_dir / "expected.json",
            {
                "task_id": row["id"],
                "status": "AWAITING_BI_GROUND_TRUTH",
                "expected_fields": expected_fields(row["rubric"]),
                "expected_side_effects": parse_side_effects(row.get("side_effect_checks", "")),
                "notes": "Manual BI-authored ground truth goes here. The harness never exposes this file to the workspace.",
            },
        )
        submission_path = task_dir / "submission.json"
        if not submission_path.exists():
            write_json(
                submission_path,
                {
                    "task_id": row["id"],
                    "status": "AWAITING_AGENT_OUTPUT",
                    "answers": {},
                    "trajectory": {"tool_calls": []},
                },
            )
        created.append(task_dir)
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=str(CANONICAL_CSV))
    parser.add_argument("--out", default="tasks")
    args = parser.parse_args()
    created = generate(args.csv, args.out)
    print(f"Generated {len(created)} tasks in {args.out}")


if __name__ == "__main__":
    main()

