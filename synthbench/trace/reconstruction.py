from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

from synthbench.common import read_json
from synthbench.trace.events import (
    base_event,
    make_event,
    make_tool_call_event,
    make_tool_result_event,
    parse_timestamp,
    read_events,
    validate_trace,
)


READ_MARKERS = ("sed -n", "rg --files", "find ", "head ", "cat ")
WRITE_MARKERS = ("write_text", "DictWriter", ".open('w'", '.open("w"', "mkdir", "cp -R")
VERIFY_MARKERS = ("counts", "reconcile", "Self-check", "summary.txt", "exceptions.csv")
EXCEPTION_MARKERS = ("Traceback", "Error:", "Exception", "exited with code")
RETRY_MARKERS = ("retry", "again", "rerun")


def reconstruct_cell_events(cell: str | Path, output_path: str | Path | None = None, comparison_path: str | Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cell_dir = Path(cell)
    manifest = read_json(cell_dir / "manifest.json")
    original_events = read_events(cell_dir / "events.jsonl")
    transcript = read_transcript(cell_dir)
    reconstructed = reconstruct_events(manifest, original_events, transcript)
    comparison = compare_events(original_events, reconstructed)
    comparison["validation_issues"] = validate_trace(reconstructed)
    if output_path:
        write_events_jsonl(output_path, reconstructed)
    if comparison_path:
        Path(comparison_path).parent.mkdir(parents=True, exist_ok=True)
        Path(comparison_path).write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return reconstructed, comparison


def write_events_jsonl(path: str | Path, events: list[dict[str, Any]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in events), encoding="utf-8")


def reconstruct_events(manifest: dict[str, Any], original_events: list[dict[str, Any]], transcript: str) -> list[dict[str, Any]]:
    start_ts = _start_timestamp(original_events)
    events: list[dict[str, Any]] = [_copy_task_start(manifest, original_events, start_ts)]
    commands = _extract_exec_commands(transcript)
    sequence = 1
    for idx, item in enumerate(commands, start=1):
        command = item["command"]
        latency_ms = item["latency_ms"]
        success = item["success"]
        call_ts = (start_ts + timedelta(milliseconds=sequence * 10)).isoformat().replace("+00:00", "Z")
        sequence += 1
        result_ts = (start_ts + timedelta(milliseconds=sequence * 10)).isoformat().replace("+00:00", "Z")
        sequence += 1
        tool_name = _tool_name(command)
        call = make_tool_call_event(
            manifest,
            tool_name=tool_name,
            arguments={"command": command, "source": "codex_transcript", "reconstructed_index": idx},
            success=True,
            latency_ms=0,
        )
        call["timestamp"] = call_ts
        events.append(call)
        result = make_tool_result_event(
            manifest,
            tool_name=tool_name,
            result={"status": item["status"], "reconstructed_index": idx},
            success=success,
            latency_ms=latency_ms,
        )
        result["timestamp"] = result_ts
        events.append(result)
        for event_type, payload in _derived_events(manifest, command, success, idx):
            ev = make_event(manifest, event_type, **payload)
            ev["timestamp"] = (start_ts + timedelta(milliseconds=sequence * 10)).isoformat().replace("+00:00", "Z")
            sequence += 1
            events.append(ev)
    for path in _result_artifact_paths(transcript):
        ev = make_event(manifest, "file_write", path=path, source="codex_transcript_artifact_reference", confidence=0.8)
        ev["timestamp"] = (start_ts + timedelta(milliseconds=sequence * 10)).isoformat().replace("+00:00", "Z")
        sequence += 1
        events.append(ev)
    return events


def compare_events(original_events: list[dict[str, Any]], reconstructed_events: list[dict[str, Any]]) -> dict[str, Any]:
    original_tool_events = [event for event in original_events if event.get("event_type") in {"tool_call", "tool_result"}]
    reconstructed_tool_events = [event for event in reconstructed_events if event.get("event_type") in {"tool_call", "tool_result"}]
    expected_tool_events = len(reconstructed_tool_events)
    observed_tool_events = len(original_tool_events)
    return {
        "original_event_count": len(original_events),
        "original_tool_events": observed_tool_events,
        "reconstructed_event_count": len(reconstructed_events),
        "reconstructed_tool_events": len(reconstructed_tool_events),
        "expected_tool_events": expected_tool_events,
        "missing_original_tool_events": max(0, expected_tool_events - observed_tool_events),
        "original_tool_capture_recall": _ratio(observed_tool_events, expected_tool_events),
        "reconstructed_tool_capture_recall": _ratio(len(reconstructed_tool_events), expected_tool_events),
        "event_type_counts": _counts(reconstructed_events),
    }


def trace_fidelity_metrics(original_events: list[dict[str, Any]], reconstructed_events: list[dict[str, Any]]) -> dict[str, Any]:
    original_counts = _counts(original_events)
    reconstructed_counts = _counts(reconstructed_events)
    expected_tool = reconstructed_counts.get("tool_call", 0) + reconstructed_counts.get("tool_result", 0)
    official_tool = original_counts.get("tool_call", 0) + original_counts.get("tool_result", 0)
    expected_files = reconstructed_counts.get("file_read", 0) + reconstructed_counts.get("file_write", 0)
    official_files = original_counts.get("file_read", 0) + original_counts.get("file_write", 0)
    expected_verifications = reconstructed_counts.get("verification", 0)
    official_verifications = original_counts.get("verification", 0)
    tool_capture = _ratio(official_tool, expected_tool)
    file_capture = _ratio(official_files, expected_files)
    verification_capture = _ratio(official_verifications, expected_verifications)
    reconstructed_tool_capture = _ratio(expected_tool, expected_tool)
    reconstructed_file_capture = _ratio(expected_files, expected_files)
    reconstructed_verification_capture = _ratio(expected_verifications, expected_verifications)
    return {
        "official_metrics": {
            "event_count": len(original_events),
            "tool_events": official_tool,
            "file_events": official_files,
            "verification_events": official_verifications,
            "tool_capture_recall": tool_capture,
            "file_capture_recall": file_capture,
            "verification_capture_recall": verification_capture,
            "trace_fidelity_score": _mean_available([tool_capture, file_capture, verification_capture]),
        },
        "reconstructed_metrics": {
            "event_count": len(reconstructed_events),
            "tool_events": expected_tool,
            "file_events": expected_files,
            "verification_events": expected_verifications,
            "tool_capture_recall": reconstructed_tool_capture,
            "file_capture_recall": reconstructed_file_capture,
            "verification_capture_recall": reconstructed_verification_capture,
            "trace_fidelity_score": _mean_available([reconstructed_tool_capture, reconstructed_file_capture, reconstructed_verification_capture]),
            "event_type_counts": reconstructed_counts,
        },
        "expected_tool_events": expected_tool,
        "expected_file_events": expected_files,
        "expected_verification_events": expected_verifications,
        "missing_tool_events": max(0, expected_tool - official_tool),
        "missing_file_events": max(0, expected_files - official_files),
        "missing_verification_events": max(0, expected_verifications - official_verifications),
    }


def read_transcript(cell_dir: Path) -> str:
    parts = []
    for name in ("raw_response.txt", "final_output.md"):
        path = cell_dir / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text not in parts:
                parts.append(text)
    return "\n".join(parts)


def _start_timestamp(original_events: list[dict[str, Any]]):
    for event in original_events:
        if event.get("timestamp"):
            return parse_timestamp(event["timestamp"])
    raise ValueError("cannot reconstruct timestamps without at least one original event timestamp")


def _copy_task_start(manifest: dict[str, Any], original_events: list[dict[str, Any]], start_ts) -> dict[str, Any]:
    for event in original_events:
        if event.get("event_type") == "task_start":
            copied = dict(event)
            copied["event_id"] = f"{event.get('event_id')}_reconstructed"
            copied["source"] = "original_events"
            return copied
    event = base_event(manifest, "task_start", timestamp=start_ts.isoformat().replace("+00:00", "Z"))
    event["source"] = "synthetic"
    return event


def _extract_exec_commands(transcript: str) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    pending: list[int] = []
    lines = transcript.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line == "exec" and idx + 1 < len(lines):
            commands.append({"command": _clean_command(lines[idx + 1]), "status": "unknown", "success": False, "latency_ms": 0})
            pending.append(len(commands) - 1)
            idx += 2
            continue
        status = _parse_status_line(line)
        if status and pending:
            command_idx = pending.pop(0)
            commands[command_idx].update(status)
        idx += 1
    return commands


def _parse_status_line(line: str) -> dict[str, Any] | None:
    match = re.match(r" (succeeded|exited with code \d+) in (\d+)ms:", line)
    if not match:
        return None
    status = match.group(1)
    return {"status": status, "success": status == "succeeded", "latency_ms": int(match.group(2))}


def _clean_command(command: str) -> str:
    return " ".join(line.rstrip() for line in command.strip().splitlines()).strip()


def _tool_name(command: str) -> str:
    if "python3" in command:
        return "shell.python3"
    if "sed " in command:
        return "shell.sed"
    if "rg " in command:
        return "shell.rg"
    if "find " in command:
        return "shell.find"
    if "ls " in command:
        return "shell.ls"
    return "shell.exec"


def _derived_events(manifest: dict[str, Any], command: str, success: bool, idx: int) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    lowered = command.lower()
    if any(marker.lower() in lowered for marker in READ_MARKERS) or "load_workbook" in command or "DictReader" in command:
        events.append(("file_read", {"path": _first_path(command), "source": "codex_transcript", "reconstructed_from_tool_index": idx, "confidence": 0.75 if "python3" in command else 0.9}))
    if any(marker.lower() in lowered for marker in WRITE_MARKERS) or "/results" in command and "open" in lowered:
        events.append(("file_write", {"path": _first_results_path(command), "source": "codex_transcript", "reconstructed_from_tool_index": idx, "confidence": 0.65}))
    if any(marker.lower() in lowered for marker in VERIFY_MARKERS):
        events.append(("verification", {"status": "PASS" if success else "UNKNOWN", "message": "Reconstructed verification-like command from Codex transcript.", "source": "codex_transcript", "reconstructed_from_tool_index": idx}))
    if any(marker.lower() in lowered for marker in RETRY_MARKERS):
        events.append(("retry", {"source": "codex_transcript", "reconstructed_from_tool_index": idx}))
    if (not success) or any(marker.lower() in lowered for marker in EXCEPTION_MARKERS):
        events.append(("exception", {"exception_type": "TranscriptCommandFailure", "message": "Reconstructed failed or exception-like command from Codex transcript.", "recovered": success, "source": "codex_transcript", "reconstructed_from_tool_index": idx}))
    return events


def _first_path(command: str) -> str | None:
    match = re.search(r"(/Users/[^\s'\";]+)", command)
    return match.group(1) if match else None


def _first_results_path(command: str) -> str | None:
    match = re.search(r"(/Users/[^\s'\";]*results[^\s'\";]*)", command)
    return match.group(1) if match else _first_path(command)


def _result_artifact_paths(transcript: str) -> list[str]:
    seen = set()
    paths = []
    for match in re.finditer(r"(/Users/[^\s\]\)'\";]+/results/[^\s\]\)'\";]+\.(?:csv|json|txt|md))", transcript):
        path = match.group(1)
        if path not in seen:
            seen.add(path)
            paths.append(path)
    return paths


def _counts(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        counts[event["event_type"]] = counts.get(event["event_type"], 0) + 1
    return counts


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 1.0
    return round(float(numerator) / float(denominator), 6)


def _mean_available(values: list[float]) -> float:
    present = [value for value in values if value is not None]
    if not present:
        return 1.0
    return round(sum(present) / len(present), 6)
