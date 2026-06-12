from __future__ import annotations

from copy import deepcopy
from typing import Any

from synthbench.schemas.artifacts import CURRENT_VERSION


class MigrationError(ValueError):
    pass


def artifact_version(document: dict[str, Any]) -> str | None:
    version = document.get("schema_version")
    return str(version) if version is not None else None


def migrate_artifact(artifact_type: str, document: dict[str, Any], target_version: str = CURRENT_VERSION) -> dict[str, Any]:
    """Return a migrated copy of an artifact.

    Phase 5.5 freezes v1.0 and installs the migration entry point. Future
    versions should register explicit artifact_type/from/to transforms here.
    """
    source_version = artifact_version(document)
    if source_version == target_version:
        return deepcopy(document)
    if source_version is None and target_version == CURRENT_VERSION:
        migrated = deepcopy(document)
        migrated["schema_version"] = CURRENT_VERSION
        return migrated
    raise MigrationError(f"no migration for {artifact_type} from {source_version!r} to {target_version!r}")


def compatibility_issues(artifact_type: str, document: dict[str, Any], expected_version: str = CURRENT_VERSION) -> list[str]:
    version = artifact_version(document)
    if version == expected_version:
        return []
    if version is None:
        return [f"{artifact_type}: missing schema_version; can be migrated to {expected_version}"]
    return [f"{artifact_type}: unsupported schema_version {version}; expected {expected_version}"]
