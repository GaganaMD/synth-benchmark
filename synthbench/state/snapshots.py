from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from synthbench.common import write_json
from synthbench.hashing import hash_tree, sha256_file
from synthbench.trace.events import utc_now


def new_snapshot_id(label: str) -> str:
    return f"{label}_{uuid.uuid4().hex[:12]}"


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    files = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        files.append({"path": rel, "size": path.stat().st_size, "sha256": sha256_file(path)})
    return files


def _load_mock_state(path: Path | None) -> Any:
    if not path or not path.exists():
        return None
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def capture_snapshot(
    *,
    snapshot_id: str,
    workspace_dir: str | Path,
    outputs_dir: str | Path | None = None,
    mock_state_path: str | Path | None = None,
) -> dict[str, Any]:
    workspace = Path(workspace_dir)
    outputs = Path(outputs_dir) if outputs_dir else None
    mock_state = Path(mock_state_path) if mock_state_path else None
    workspace_hash = hash_tree(workspace)
    output_hash = hash_tree(outputs) if outputs else {"exists": False, "files": [], "tree_sha256": None}
    return {
        "schema_version": "1.0",
        "snapshot_id": snapshot_id,
        "timestamp": utc_now(),
        "workspace_dir": workspace.as_posix(),
        "outputs_dir": outputs.as_posix() if outputs else None,
        "mock_state_path": mock_state.as_posix() if mock_state else None,
        "workspace_hash": workspace_hash.get("tree_sha256"),
        "workspace": workspace_hash,
        "outputs_hash": output_hash.get("tree_sha256"),
        "outputs": output_hash,
        "filesystem": {
            "workspace_files": _file_inventory(workspace),
            "output_files": _file_inventory(outputs) if outputs else [],
        },
        "mock_state": _load_mock_state(mock_state),
    }


def write_snapshot(snapshot: dict[str, Any], path: str | Path) -> dict[str, Any]:
    write_json(path, snapshot)
    return snapshot


def load_snapshot(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as f:
        return json.load(f)
