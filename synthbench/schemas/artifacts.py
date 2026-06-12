from __future__ import annotations

from copy import deepcopy
from typing import Any


CURRENT_VERSION = "1.0"
ARTIFACT_ORDER = ("manifest", "canonical_output", "event", "snapshot", "state_diff")


def _base_schema(title: str, required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://synthbench.local/schemas/{title.lower().replace(' ', '-')}-v1.0.json",
        "title": title,
        "type": "object",
        "additionalProperties": True,
        "required": ["schema_version", *required],
        "properties": {
            "schema_version": {"type": "string", "const": CURRENT_VERSION},
            **properties,
        },
    }


SCHEMAS: dict[str, dict[str, Any]] = {
    "manifest": _base_schema(
        "Benchmark Manifest",
        [
            "experiment_id",
            "run_id",
            "task_id",
            "harness_id",
            "model_id",
            "seed",
            "dataset_version",
            "fixture_version",
            "environment_version",
            "workspace_hash",
            "git_commit",
        ],
        {
            "experiment_id": {"type": "string"},
            "run_id": {"type": "string"},
            "task_id": {"type": "string"},
            "harness_id": {"type": "string"},
            "model_id": {"type": "string"},
            "seed": {"type": "integer"},
            "dataset_version": {"type": "string"},
            "fixture_version": {"type": "string"},
            "environment_version": {"type": "string"},
            "workspace_hash": {"type": "object"},
            "git_commit": {"type": "string"},
            "replay": {"type": "object"},
        },
    ),
    "canonical_output": _base_schema(
        "Canonical Output",
        ["normalized_at", "identity", "adapter", "status", "content", "raw_sources", "provenance", "validation"],
        {
            "normalized_at": {"type": "string"},
            "identity": {"type": "object", "required": ["run_id", "task_id"]},
            "adapter": {"type": "object", "required": ["adapter_id"]},
            "status": {"type": "string", "enum": ["COMPLETED", "FAILED", "TIMED_OUT", "UNKNOWN"]},
            "content": {
                "type": "object",
                "required": ["structured_records", "tables", "reports", "side_effect_summaries", "exception_summaries"],
            },
            "raw_sources": {"type": "array"},
            "provenance": {"type": "array"},
            "validation": {"type": "object"},
        },
    ),
    "event": _base_schema(
        "Trace Event",
        ["event_id", "experiment_id", "run_id", "task_id", "timestamp", "event_type"],
        {
            "event_id": {"type": "string"},
            "experiment_id": {"type": "string"},
            "run_id": {"type": "string"},
            "task_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "event_type": {
                "type": "string",
                "enum": [
                    "task_start",
                    "plan_created",
                    "file_read",
                    "file_write",
                    "tool_call",
                    "tool_result",
                    "state_checkpoint",
                    "exception",
                    "retry",
                    "verification",
                    "side_effect",
                    "task_complete",
                ],
            },
        },
    ),
    "snapshot": _base_schema(
        "State Snapshot",
        ["snapshot_id", "timestamp", "workspace_hash", "workspace", "outputs", "filesystem"],
        {
            "snapshot_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "workspace_hash": {"type": ["string", "null"]},
            "workspace": {"type": "object"},
            "outputs_hash": {"type": ["string", "null"]},
            "outputs": {"type": "object"},
            "filesystem": {"type": "object", "required": ["workspace_files", "output_files"]},
            "mock_state": {},
        },
    ),
    "state_diff": _base_schema(
        "State Diff",
        ["status", "changes"],
        {
            "created_at": {"type": "string"},
            "status": {"type": "string", "enum": ["NOT_CAPTURED", "CAPTURED", "FAILED"]},
            "s0_snapshot_id": {"type": ["string", "null"]},
            "s1_snapshot_id": {"type": ["string", "null"]},
            "workspace_hash_before": {"type": ["string", "null"]},
            "workspace_hash_after": {"type": ["string", "null"]},
            "changes": {"type": "array"},
            "summary": {"type": "object"},
        },
    ),
}


def schema_for(artifact_type: str) -> dict[str, Any]:
    if artifact_type not in SCHEMAS:
        raise KeyError(f"unknown artifact type: {artifact_type}")
    return deepcopy(SCHEMAS[artifact_type])


def all_schemas() -> dict[str, dict[str, Any]]:
    return {name: schema_for(name) for name in ARTIFACT_ORDER}


def schema_filename(artifact_type: str) -> str:
    return f"{artifact_type}.v{CURRENT_VERSION}.schema.json"
