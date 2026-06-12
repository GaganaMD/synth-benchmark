from __future__ import annotations

from pathlib import Path
from typing import Any

from synthbench.common import read_json
from synthbench.schemas.artifacts import CURRENT_VERSION, schema_for
from synthbench.schemas.migrations import compatibility_issues, migrate_artifact
from synthbench.trace.events import read_events, validate_trace


ARTIFACT_PATHS = {
    "manifest": "manifest.json",
    "canonical_output": "canonical_output.json",
    "events": "events.jsonl",
    "S0": "state/S0.json",
    "S1": "state/S1.json",
    "state_diff": "state/state_diff.json",
}


def validate_document(artifact_type: str, document: dict[str, Any], *, allow_migration: bool = False) -> list[str]:
    schema_type = "event" if artifact_type == "events" else "snapshot" if artifact_type in {"S0", "S1"} else artifact_type
    if allow_migration:
        try:
            document = migrate_artifact(schema_type, document)
        except Exception as exc:
            return [str(exc)]
    issues = compatibility_issues(schema_type, document, CURRENT_VERSION)
    issues.extend(_validate_against_schema(document, schema_for(schema_type), path="$"))
    return issues


def validate_cell_contract(cell: str | Path, *, require_canonical: bool = False, allow_migration: bool = False) -> dict[str, list[str]]:
    root = Path(cell)
    results: dict[str, list[str]] = {}
    for artifact, rel in ARTIFACT_PATHS.items():
        path = root / rel
        if artifact == "canonical_output" and not require_canonical and not path.exists():
            continue
        if not path.exists():
            results[artifact] = [f"missing artifact: {rel}"]
            continue
        if artifact == "events":
            event_issues = []
            events = read_events(path)
            for idx, event in enumerate(events):
                for issue in validate_document("events", event, allow_migration=allow_migration):
                    event_issues.append(f"event[{idx}] {issue}")
            event_issues.extend(validate_trace(events))
            results[artifact] = event_issues
            continue
        document = read_json(path, default=None)
        if not isinstance(document, dict):
            results[artifact] = [f"{rel} must contain a JSON object"]
            continue
        results[artifact] = validate_document(artifact, document, allow_migration=allow_migration)
    _add_cross_artifact_issues(root, results)
    return results


def contract_is_valid(results: dict[str, list[str]]) -> bool:
    return all(not issues for issues in results.values())


def _validate_against_schema(value: Any, schema: dict[str, Any], *, path: str) -> list[str]:
    issues = []
    expected_type = schema.get("type")
    if expected_type and not _matches_type(value, expected_type):
        issues.append(f"{path}: expected {expected_type}, got {type(value).__name__}")
        return issues
    if "const" in schema and value != schema["const"]:
        issues.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        issues.append(f"{path}: expected one of {schema['enum']}, got {value!r}")
    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value or value[field] is None:
                issues.append(f"{path}: missing required field {field}")
        properties = schema.get("properties", {})
        for field, child_schema in properties.items():
            if field in value:
                issues.extend(_validate_against_schema(value[field], child_schema, path=f"{path}.{field}"))
    if isinstance(value, list) and "items" in schema:
        for idx, item in enumerate(value):
            issues.extend(_validate_against_schema(item, schema["items"], path=f"{path}[{idx}]"))
    return issues


def _matches_type(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(value, item) for item in expected)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def _add_cross_artifact_issues(root: Path, results: dict[str, list[str]]) -> None:
    manifest = read_json(root / "manifest.json", default={}) or {}
    canonical = read_json(root / "canonical_output.json", default={}) or {}
    s0 = read_json(root / "state" / "S0.json", default={}) or {}
    s1 = read_json(root / "state" / "S1.json", default={}) or {}
    diff = read_json(root / "state" / "state_diff.json", default={}) or {}
    if canonical:
        identity = canonical.get("identity", {})
        for field in ("run_id", "task_id", "dataset_version", "fixture_version"):
            if manifest.get(field) and identity.get(field) and manifest.get(field) != identity.get(field):
                results.setdefault("canonical_output", []).append(f"identity.{field} does not match manifest.{field}")
    if diff:
        if diff.get("s0_snapshot_id") and s0.get("snapshot_id") and diff.get("s0_snapshot_id") != s0.get("snapshot_id"):
            results.setdefault("state_diff", []).append("s0_snapshot_id does not match S0.snapshot_id")
        if diff.get("s1_snapshot_id") and s1.get("snapshot_id") and diff.get("s1_snapshot_id") != s1.get("snapshot_id"):
            results.setdefault("state_diff", []).append("s1_snapshot_id does not match S1.snapshot_id")
