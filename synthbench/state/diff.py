from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from synthbench.common import write_json
from synthbench.trace.events import utc_now


def _index(files: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["path"]: item for item in files}


def _diff_files(before: list[dict[str, Any]], after: list[dict[str, Any]], scope: str) -> list[dict[str, Any]]:
    b = _index(before)
    a = _index(after)
    changes = []
    for path in sorted(set(a) - set(b)):
        changes.append({"scope": scope, "change_type": "created", "path": path, "before": None, "after": a[path]})
    for path in sorted(set(b) - set(a)):
        changes.append({"scope": scope, "change_type": "deleted", "path": path, "before": b[path], "after": None})
    for path in sorted(set(a) & set(b)):
        if a[path].get("sha256") != b[path].get("sha256") or a[path].get("size") != b[path].get("size"):
            changes.append({"scope": scope, "change_type": "modified", "path": path, "before": b[path], "after": a[path]})
    return changes


def _stable_hash(obj: Any) -> str | None:
    if obj is None:
        return None
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def compute_state_diff(s0: dict[str, Any], s1: dict[str, Any]) -> dict[str, Any]:
    workspace_changes = _diff_files(
        s0.get("filesystem", {}).get("workspace_files", []),
        s1.get("filesystem", {}).get("workspace_files", []),
        "workspace",
    )
    output_changes = _diff_files(
        s0.get("filesystem", {}).get("output_files", []),
        s1.get("filesystem", {}).get("output_files", []),
        "outputs",
    )
    mock_before_hash = _stable_hash(s0.get("mock_state"))
    mock_after_hash = _stable_hash(s1.get("mock_state"))
    mock_changes = []
    if mock_before_hash != mock_after_hash:
        mock_changes.append(
            {
                "scope": "mock_state",
                "change_type": "modified" if mock_before_hash and mock_after_hash else "created" if mock_after_hash else "deleted",
                "path": s1.get("mock_state_path") or s0.get("mock_state_path"),
                "before": {"sha256": mock_before_hash},
                "after": {"sha256": mock_after_hash},
            }
        )
    changes = workspace_changes + output_changes + mock_changes
    return {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "status": "CAPTURED",
        "s0_snapshot_id": s0.get("snapshot_id"),
        "s1_snapshot_id": s1.get("snapshot_id"),
        "workspace_hash_before": s0.get("workspace_hash"),
        "workspace_hash_after": s1.get("workspace_hash"),
        "changes": changes,
        "summary": {
            "files_created": sum(1 for c in changes if c["change_type"] == "created"),
            "files_modified": sum(1 for c in changes if c["change_type"] == "modified"),
            "files_deleted": sum(1 for c in changes if c["change_type"] == "deleted"),
            "workspace_changes": len(workspace_changes),
            "output_changes": len(output_changes),
            "mock_state_changes": len(mock_changes),
        },
    }


def write_state_diff(diff: dict[str, Any], path: str | Path) -> dict[str, Any]:
    write_json(path, diff)
    return diff
