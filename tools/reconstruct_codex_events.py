from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


def main() -> None:
    parser = argparse.ArgumentParser(description="Prototype reconstruction of inner Codex tool events from raw transcript text.")
    parser.add_argument("--cell", required=True, help="Run cell, e.g. runs/codex/TXN-001/seed-0")
    parser.add_argument("--output", help="JSONL output path. Defaults to <cell>/reconstructed_events.jsonl")
    parser.add_argument("--comparison-output", help="JSON comparison path. Defaults to <output>.comparison.json")
    args = parser.parse_args()

    cell = Path(args.cell)
    manifest = read_json(cell / "manifest.json")
    original_events = read_events(cell / "events.jsonl")
    transcript = _read_transcript(cell)
    reconstructed = reconstruct_events(manifest, original_events, transcript)

    output_path = Path(args.output) if args.output else cell / "reconstructed_events.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n" for event in reconstructed),
        encoding="utf-8",
    )

    comparison = compare_events(original_events, reconstructed)
    comparison["validation_issues"] = validate_trace(reconstructed)
    comparison_path = Path(args.comparison_output) if args.comparison_output else output_path.with_suffix(".comparison.json")
    comparison_path.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": output_path.as_posix(), "comparison": comparison_path.as_posix(), **comparison}, indent=2, sort_keys=True))


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

        for event_type, payload in _derived_events(manifest, command, success, idx, result_ts):
            ev = make_event(manifest, event_type, **payload)
            ev["timestamp"] = (start_ts + timedelta(milliseconds=sequence * 10)).isoformat().replace("+00:00", "Z")
            sequence += 1
            events.append(ev)
    for path in _result_artifact_paths(transcript):
        ev = make_event(
            manifest,
            "file_write",
            path=path,
            source="codex_transcript_artifact_reference",
            confidence=0.8,
        )
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
        "original_tool_capture_recall": observed_tool_events / expected_tool_events if expected_tool_events else 1.0,
        "reconstructed_tool_capture_recall": len(reconstructed_tool_events) / expected_tool_events if expected_tool_events else 1.0,
        "event_type_counts": _counts(reconstructed_events),
    }


def _read_transcript(cell: Path) -> str:
    parts = []
    for name in ("raw_response.txt", "final_output.md"):
        path = cell / name
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


def _derived_events(manifest: dict[str, Any], command: str, success: bool, idx: int, timestamp: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    lowered = command.lower()
    if any(marker.lower() in lowered for marker in READ_MARKERS) or "load_workbook" in command or "DictReader" in command:
        events.append(
            (
                "file_read",
                {
                    "path": _first_path(command),
                    "source": "codex_transcript",
                    "reconstructed_from_tool_index": idx,
                    "confidence": 0.75 if "python3" in command else 0.9,
                },
            )
        )
    if any(marker.lower() in lowered for marker in WRITE_MARKERS) or "/results" in command and "open" in lowered:
        events.append(
            (
                "file_write",
                {
                    "path": _first_results_path(command),
                    "source": "codex_transcript",
                    "reconstructed_from_tool_index": idx,
                    "confidence": 0.65,
                },
            )
        )
    if any(marker.lower() in lowered for marker in VERIFY_MARKERS):
        events.append(
            (
                "verification",
                {
                    "status": "PASS" if success else "UNKNOWN",
                    "message": "Reconstructed verification-like command from Codex transcript.",
                    "source": "codex_transcript",
                    "reconstructed_from_tool_index": idx,
                },
            )
        )
    if any(marker.lower() in lowered for marker in RETRY_MARKERS):
        events.append(("retry", {"source": "codex_transcript", "reconstructed_from_tool_index": idx}))
    if (not success) or any(marker.lower() in lowered for marker in EXCEPTION_MARKERS):
        events.append(
            (
                "exception",
                {
                    "exception_type": "TranscriptCommandFailure",
                    "message": "Reconstructed failed or exception-like command from Codex transcript.",
                    "recovered": success,
                    "source": "codex_transcript",
                    "reconstructed_from_tool_index": idx,
                },
            )
        )
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


if __name__ == "__main__":
    main()
