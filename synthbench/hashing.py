from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_tree(root: Path) -> dict[str, Any]:
    if not root.exists():
        return {"root": str(root), "exists": False, "files": [], "tree_sha256": None}
    files = []
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        file_hash = sha256_file(path)
        size = path.stat().st_size
        files.append({"path": rel, "size": size, "sha256": file_hash})
        digest.update(rel.encode("utf-8"))
        digest.update(file_hash.encode("ascii"))
    return {
        "root": str(root),
        "exists": True,
        "file_count": len(files),
        "files": files,
        "tree_sha256": digest.hexdigest(),
    }
