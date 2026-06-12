from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from synthbench.common import write_json
from synthbench.run_store import hash_tree, sha256_file, utc_now


DEFAULT_FIXTURE_ROOT = Path("immutable_inputs")
DEFAULT_FIXTURE_REGISTRY = Path("registry/fixtures.jsonl")


def _version_path(root: Path, fixture_version: str) -> Path:
    return root / fixture_version


def _blob_path(root: Path, file_hash: str) -> Path:
    return root / "blobs" / file_hash[:2] / file_hash


def copy_blob(src: Path, fixture_root: Path) -> dict[str, Any]:
    file_hash = sha256_file(src)
    target = _blob_path(fixture_root, file_hash)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(src, target)
    return {"sha256": file_hash, "size": src.stat().st_size, "blob_path": target.as_posix()}


def materialize_from_blobs(record: dict[str, Any], destination: str | Path, overwrite: bool = False) -> Path:
    dest = Path(destination)
    if dest.exists() and overwrite:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for item in record.get("files", []):
        source = Path(item["blob_path"])
        target = dest / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return dest


def fixture_record(fixture_version: str, source_workspace: str | Path, fixture_root: str | Path = DEFAULT_FIXTURE_ROOT) -> dict[str, Any]:
    source = Path(source_workspace)
    if not source.exists():
        raise FileNotFoundError(source)
    root = Path(fixture_root)
    tree = hash_tree(source)
    files = []
    for item in tree.get("files", []):
        src = source / item["path"]
        blob = copy_blob(src, root)
        files.append(
            {
                "path": item["path"],
                "size": item["size"],
                "sha256": item["sha256"],
                "blob_path": blob["blob_path"],
            }
        )
    version_dir = _version_path(root, fixture_version)
    workspace_copy = version_dir / "workspace"
    if workspace_copy.exists():
        shutil.rmtree(workspace_copy)
    shutil.copytree(source, workspace_copy)
    record = {
        "schema_version": "1.0",
        "fixture_version": fixture_version,
        "created_at": utc_now(),
        "source_workspace": source.as_posix(),
        "fixture_root": root.as_posix(),
        "workspace_copy": workspace_copy.as_posix(),
        "workspace_hash": tree.get("tree_sha256"),
        "file_count": tree.get("file_count", 0),
        "files": files,
    }
    write_json(version_dir / "fixture_manifest.json", record)
    return record


def load_fixture_registry(path: str | Path = DEFAULT_FIXTURE_REGISTRY) -> list[dict[str, Any]]:
    registry_path = Path(path)
    if not registry_path.exists():
        return []
    records = []
    for line in registry_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def find_fixture(fixture_version: str, path: str | Path = DEFAULT_FIXTURE_REGISTRY) -> dict[str, Any] | None:
    for record in reversed(load_fixture_registry(path)):
        if record.get("fixture_version") == fixture_version:
            return record
    return None


def register_fixture(
    fixture_version: str,
    source_workspace: str | Path,
    fixture_root: str | Path = DEFAULT_FIXTURE_ROOT,
    registry_path: str | Path = DEFAULT_FIXTURE_REGISTRY,
) -> dict[str, Any]:
    existing = find_fixture(fixture_version, registry_path)
    if existing:
        tree = hash_tree(Path(source_workspace))
        incoming = {
            "fixture_version": fixture_version,
            "workspace_hash": tree.get("tree_sha256"),
            "file_count": tree.get("file_count", 0),
        }
        comparable = {k: existing.get(k) for k in ("fixture_version", "workspace_hash", "file_count")}
        if comparable != incoming:
            raise ValueError(f"fixture_version already exists with different content: {fixture_version}")
        return existing
    record = fixture_record(fixture_version, source_workspace, fixture_root)
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True))
        f.write("\n")
    return record


def require_fixture(fixture_version: str, registry_path: str | Path = DEFAULT_FIXTURE_REGISTRY) -> dict[str, Any]:
    record = find_fixture(fixture_version, registry_path)
    if not record:
        raise FileNotFoundError(f"fixture version is not registered: {fixture_version}")
    for item in record.get("files", []):
        blob = Path(item["blob_path"])
        if not blob.exists():
            raise FileNotFoundError(blob)
        if sha256_file(blob) != item["sha256"]:
            raise ValueError(f"fixture blob checksum mismatch: {blob}")
    return record
