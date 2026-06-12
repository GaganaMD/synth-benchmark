from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EVENT_TYPES = {
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
}

CORE_FIELDS = {"event_id", "experiment_id", "run_id", "task_id", "timestamp", "event_type"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def new_event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def base_event(manifest: dict[str, Any], event_type: str, timestamp: str | None = None, event_id: str | None = None) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event_type}")
    return {
        "event_id": event_id or new_event_id(),
        "experiment_id": manifest.get("experiment_id"),
        "run_id": manifest.get("run_id"),
        "task_id": manifest.get("task_id"),
        "timestamp": timestamp or utc_now(),
        "event_type": event_type,
    }


def make_event(manifest: dict[str, Any], event_type: str, **payload: Any) -> dict[str, Any]:
    event = base_event(manifest, event_type)
    event.update({k: v for k, v in payload.items() if v is not None})
    return event


def make_tool_call_event(
    manifest: dict[str, Any],
    *,
    tool_name: str,
    arguments: dict[str, Any] | list[Any] | str | None = None,
    success: bool | None = None,
    latency_ms: int | float | None = None,
    result: Any = None,
) -> dict[str, Any]:
    event = base_event(manifest, "tool_call")
    event.update({"tool_name": tool_name, "arguments": arguments, "result": result, "success": success, "latency_ms": latency_ms})
    return event


def make_tool_result_event(
    manifest: dict[str, Any],
    *,
    tool_name: str,
    result: Any = None,
    success: bool,
    latency_ms: int | float | None = None,
) -> dict[str, Any]:
    event = base_event(manifest, "tool_result")
    event.update({"tool_name": tool_name, "arguments": None, "result": result, "success": success, "latency_ms": latency_ms})
    return event


def make_exception_event(
    manifest: dict[str, Any],
    *,
    exception_type: str,
    message: str,
    recovered: bool = False,
    recovery_action: str | None = None,
) -> dict[str, Any]:
    return make_event(
        manifest,
        "exception",
        exception_type=exception_type,
        message=message,
        recovered=recovered,
        recovery_action=recovery_action,
    )


def make_state_checkpoint_event(
    manifest: dict[str, Any],
    *,
    checkpoint_id: str,
    state_summary: dict[str, Any] | str,
) -> dict[str, Any]:
    return make_event(manifest, "state_checkpoint", checkpoint_id=checkpoint_id, state_summary=state_summary)


def make_task_complete_event(
    manifest: dict[str, Any],
    *,
    runtime_seconds: int | float,
    step_count: int,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    estimated_cost: float | None = None,
) -> dict[str, Any]:
    event = base_event(manifest, "task_complete")
    event.update(
        {
            "runtime_seconds": runtime_seconds,
            "step_count": step_count,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": estimated_cost,
        }
    )
    return event


def append_jsonl(path: str | Path, event: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(encoded)
        f.flush()
        os.fsync(f.fileno())


def read_events(path: str | Path) -> list[dict[str, Any]]:
    events_path = Path(path)
    if not events_path.exists():
        return []
    events = []
    for line_no, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at {events_path}:{line_no}: {exc}") from exc
    return events


def append_event(path: str | Path, event: dict[str, Any]) -> None:
    issues = validate_event(event)
    if issues:
        raise ValueError("; ".join(issues))
    append_jsonl(path, event)


def validate_event(event: dict[str, Any]) -> list[str]:
    issues = []
    missing = sorted(field for field in CORE_FIELDS if event.get(field) in (None, ""))
    if missing:
        issues.append(f"missing core fields: {', '.join(missing)}")
    if event.get("event_type") not in EVENT_TYPES:
        issues.append(f"invalid event_type: {event.get('event_type')}")
    try:
        parse_timestamp(str(event.get("timestamp", "")))
    except ValueError:
        issues.append(f"invalid timestamp: {event.get('timestamp')}")

    event_type = event.get("event_type")
    if event_type in {"tool_call", "tool_result"}:
        for field in ("tool_name", "arguments", "result", "success", "latency_ms"):
            if field not in event:
                issues.append(f"{event_type} missing {field}")
        if not event.get("tool_name"):
            issues.append(f"{event_type} tool_name is required")
        if event.get("success") is None:
            issues.append(f"{event_type} success is required")
        elif not isinstance(event.get("success"), bool):
            issues.append(f"{event_type} success must be boolean")
        if event.get("latency_ms") is not None and float(event["latency_ms"]) < 0:
            issues.append(f"{event_type} latency_ms must be non-negative")
    if event_type == "exception":
        for field in ("exception_type", "message", "recovered"):
            if field not in event:
                issues.append(f"exception missing {field}")
        if not event.get("exception_type"):
            issues.append("exception exception_type is required")
        if not event.get("message"):
            issues.append("exception message is required")
        if event.get("recovered") is None:
            issues.append("exception recovered is required")
        elif not isinstance(event.get("recovered"), bool):
            issues.append("exception recovered must be boolean")
    if event_type == "state_checkpoint":
        for field in ("checkpoint_id", "state_summary"):
            if field not in event:
                issues.append(f"state_checkpoint missing {field}")
        if not event.get("checkpoint_id"):
            issues.append("state_checkpoint checkpoint_id is required")
        if event.get("state_summary") is None:
            issues.append("state_checkpoint state_summary is required")
    if event_type == "task_complete":
        for field in ("runtime_seconds", "step_count"):
            if field not in event:
                issues.append(f"task_complete missing {field}")
        if event.get("runtime_seconds") is None:
            issues.append("task_complete runtime_seconds is required")
        elif float(event["runtime_seconds"]) < 0:
            issues.append("task_complete runtime_seconds must be non-negative")
        if event.get("step_count") is None:
            issues.append("task_complete step_count is required")
        elif int(event["step_count"]) < 0:
            issues.append("task_complete step_count must be non-negative")

    return issues


def validate_trace(events: list[dict[str, Any]]) -> list[str]:
    issues = []
    previous_ts: datetime | None = None
    seen_start = False
    seen_complete = False
    ids = set()
    for idx, event in enumerate(events):
        for issue in validate_event(event):
            issues.append(f"event[{idx}] {issue}")
        event_id = event.get("event_id")
        if event_id in ids:
            issues.append(f"event[{idx}] duplicate event_id: {event_id}")
        ids.add(event_id)
        try:
            ts = parse_timestamp(str(event.get("timestamp", "")))
        except ValueError:
            continue
        if previous_ts and ts < previous_ts:
            issues.append(f"event[{idx}] timestamp decreased")
        previous_ts = ts

        event_type = event.get("event_type")
        if event_type == "task_start":
            if idx != 0:
                issues.append("task_start must be first event")
            seen_start = True
        if event_type == "task_complete":
            seen_complete = True
        elif seen_complete:
            issues.append(f"event[{idx}] occurs after task_complete")

    if events and not seen_start:
        issues.append("missing task_start event")
    return issues
