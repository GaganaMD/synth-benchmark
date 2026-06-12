from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from synthbench.common import read_json, write_json
from synthbench.hashing import hash_tree
from synthbench.state.diff import compute_state_diff, write_state_diff
from synthbench.state.snapshots import capture_snapshot, load_snapshot, write_snapshot
from synthbench.trace.events import (
    append_event,
    make_event,
    make_exception_event,
    make_state_checkpoint_event,
    make_task_complete_event,
    make_tool_call_event,
    make_tool_result_event,
    read_events,
)


@dataclass(frozen=True)
class CodexAdapterConfig:
    mode: str = "dry-run"
    codex_command: tuple[str, ...] = ("codex", "exec")
    timeout_s: int | None = None
    retries: int = 0


class CodexCommandError(RuntimeError):
    def __init__(self, message: str, raw_response: str):
        super().__init__(message)
        self.raw_response = raw_response


def run_codex_adapter(cell: str | Path, config: CodexAdapterConfig | None = None) -> dict[str, Any]:
    cfg = config or CodexAdapterConfig()
    if cfg.mode not in {"dry-run", "codex"}:
        raise ValueError(f"unsupported adapter mode: {cfg.mode}")
    cell_dir = Path(cell)
    manifest = read_json(cell_dir / "manifest.json")
    if not manifest:
        raise FileNotFoundError(f"missing manifest: {cell_dir / 'manifest.json'}")

    start = time.monotonic()
    events_path = cell_dir / "events.jsonl"
    artifacts_dir = cell_dir / "artifacts"
    state_dir = cell_dir / "state"
    prompt_path = cell_dir / "prompt.txt"
    raw_response_path = cell_dir / "raw_response.txt"
    final_output_path = cell_dir / "final_output.md"
    workspace_dir = Path(manifest["workspace_dir"])
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    if not prompt_path.exists():
        prompt_path.write_text("", encoding="utf-8")
    initial_events = read_events(events_path)
    if any(event.get("event_type") == "task_complete" for event in initial_events):
        raise RuntimeError(f"run cell already completed: {cell_dir}")

    status = "COMPLETED"
    final_output = ""
    step_count = 0
    error: dict[str, Any] | None = None
    _ensure_task_start(events_path, manifest, prompt_path, workspace_dir)

    s0 = _capture_snapshot(cell_dir, manifest, "S0")
    append_event(
        events_path,
        make_state_checkpoint_event(
            manifest,
            checkpoint_id=s0["snapshot_id"],
            state_summary={
                "label": "S0",
                "workspace_hash": s0.get("workspace_hash"),
                "outputs_hash": s0.get("outputs_hash"),
            },
        ),
    )

    try:
        final_output = _execute_with_retries(cell_dir, manifest, cfg, prompt_path, raw_response_path)
        raw_response_path.write_text(final_output, encoding="utf-8")
        final_output_path.write_text(final_output, encoding="utf-8")
        append_event(
            events_path,
            make_event(
                manifest,
                "verification",
                status="PASS",
                message="Adapter completed and persisted raw_response.txt and final_output.md.",
            ),
        )
    except Exception as exc:
        status = "FAILED"
        error = {"type": type(exc).__name__, "message": str(exc), "recovered": False}
        raw_failure = getattr(exc, "raw_response", "")
        final_output = raw_failure or f"FAILED: {type(exc).__name__}: {exc}\n"
        raw_response_path.write_text(final_output, encoding="utf-8")
        final_output_path.write_text(final_output, encoding="utf-8")
        events = read_events(events_path)
        if not events or events[-1].get("event_type") != "exception":
            append_event(
                events_path,
                make_exception_event(
                    manifest,
                    exception_type=type(exc).__name__,
                    message=str(exc),
                    recovered=False,
                    recovery_action="task marked failed; task_complete emitted",
                ),
            )
    finally:
        s1 = _capture_snapshot(cell_dir, manifest, "S1")
        append_event(
            events_path,
            make_state_checkpoint_event(
                manifest,
                checkpoint_id=s1["snapshot_id"],
                state_summary={
                    "label": "S1",
                    "workspace_hash": s1.get("workspace_hash"),
                    "outputs_hash": s1.get("outputs_hash"),
                },
            ),
        )
        _write_state_diff(cell_dir)
        events = read_events(events_path)
        step_count = len(events)
        if not any(event.get("event_type") == "task_complete" for event in events):
            append_event(
                events_path,
                make_task_complete_event(
                    manifest,
                    runtime_seconds=round(time.monotonic() - start, 6),
                    step_count=step_count + 1,
                    input_tokens=None,
                    output_tokens=None,
                    estimated_cost=None,
                ),
            )
        submission = _write_submission(cell_dir, manifest, status, final_output, error)

    return {
        "status": status,
        "cell": cell_dir.as_posix(),
        "manifest": (cell_dir / "manifest.json").as_posix(),
        "events": events_path.as_posix(),
        "raw_response": raw_response_path.as_posix(),
        "final_output": final_output_path.as_posix(),
        "submission": (cell_dir / "submission.json").as_posix(),
        "state": {
            "s0": (state_dir / "S0.json").as_posix(),
            "s1": (state_dir / "S1.json").as_posix(),
            "diff": (state_dir / "state_diff.json").as_posix(),
        },
        "error": error,
        "submission_status": submission.get("status"),
    }


def _ensure_task_start(events_path: Path, manifest: dict[str, Any], prompt_path: Path, workspace_dir: Path) -> None:
    events = read_events(events_path)
    if events:
        return
    append_event(
        events_path,
        make_event(
            manifest,
            "task_start",
            prompt_path=prompt_path.as_posix(),
            workspace_dir=workspace_dir.as_posix(),
        ),
    )


def _capture_snapshot(cell_dir: Path, manifest: dict[str, Any], label: str) -> dict[str, Any]:
    snapshot = capture_snapshot(
        snapshot_id=f"{label}_{manifest.get('run_id') or manifest.get('task_id')}",
        workspace_dir=manifest["workspace_dir"],
        outputs_dir=cell_dir / "artifacts",
        mock_state_path=cell_dir / "state" / "mock_state.json",
    )
    write_snapshot(snapshot, cell_dir / "state" / f"{label}.json")
    return snapshot


def _write_state_diff(cell_dir: Path) -> None:
    s0_path = cell_dir / "state" / "S0.json"
    s1_path = cell_dir / "state" / "S1.json"
    diff = compute_state_diff(load_snapshot(s0_path), load_snapshot(s1_path))
    diff["s0_snapshot_path"] = s0_path.as_posix()
    diff["s1_snapshot_path"] = s1_path.as_posix()
    write_state_diff(diff, cell_dir / "state" / "state_diff.json")


def _execute_with_retries(
    cell_dir: Path,
    manifest: dict[str, Any],
    config: CodexAdapterConfig,
    prompt_path: Path,
    raw_response_path: Path,
) -> str:
    attempts = max(1, config.retries + 1)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        if attempt > 1:
            append_event(
                cell_dir / "events.jsonl",
                make_event(
                    manifest,
                    "retry",
                    attempt=attempt,
                    max_attempts=attempts,
                    previous_error=type(last_error).__name__ if last_error else None,
                ),
            )
        try:
            if config.mode == "dry-run":
                return _run_dry(cell_dir, manifest, prompt_path, raw_response_path, attempt)
            return _run_codex_subprocess(cell_dir, manifest, config, prompt_path, attempt)
        except Exception as exc:
            last_error = exc
            recovered = attempt < attempts
            append_event(
                cell_dir / "events.jsonl",
                make_exception_event(
                    manifest,
                    exception_type=type(exc).__name__,
                    message=str(exc),
                    recovered=recovered,
                    recovery_action="retry" if recovered else None,
                ),
            )
            if not recovered:
                raise
    raise RuntimeError("adapter retry loop exited without result")


def _run_dry(cell_dir: Path, manifest: dict[str, Any], prompt_path: Path, raw_response_path: Path, attempt: int) -> str:
    started = time.monotonic()
    events_path = cell_dir / "events.jsonl"
    append_event(
        events_path,
        make_tool_call_event(
            manifest,
            tool_name="codex.dry_run",
            arguments={"prompt_path": prompt_path.as_posix(), "attempt": attempt},
            result=None,
            success=True,
            latency_ms=0,
        ),
    )
    output = (
        f"Dry run completed for task {manifest.get('task_id')}.\n"
        f"Prompt: {prompt_path.as_posix()}\n"
        "No Codex model was invoked.\n"
    )
    (cell_dir / "artifacts" / "dry_run_output.txt").write_text(output, encoding="utf-8")
    latency_ms = round((time.monotonic() - started) * 1000, 3)
    append_event(
        events_path,
        make_tool_result_event(
            manifest,
            tool_name="codex.dry_run",
            result={"raw_response_path": raw_response_path.as_posix(), "artifact": "artifacts/dry_run_output.txt"},
            success=True,
            latency_ms=latency_ms,
        ),
    )
    return output


def _run_codex_subprocess(
    cell_dir: Path,
    manifest: dict[str, Any],
    config: CodexAdapterConfig,
    prompt_path: Path,
    attempt: int,
) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    command = list(config.codex_command)
    started = time.monotonic()
    append_event(
        cell_dir / "events.jsonl",
        make_tool_call_event(
            manifest,
            tool_name="codex.subprocess",
            arguments={"command": command, "attempt": attempt, "timeout_s": config.timeout_s},
            result=None,
            success=True,
            latency_ms=0,
        ),
    )
    result = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        cwd=cell_dir,
        timeout=config.timeout_s,
        check=False,
    )
    latency_ms = round((time.monotonic() - started) * 1000, 3)
    payload = {
        "returncode": result.returncode,
        "stdout_chars": len(result.stdout or ""),
        "stderr_chars": len(result.stderr or ""),
    }
    append_event(
        cell_dir / "events.jsonl",
        make_tool_result_event(
            manifest,
            tool_name="codex.subprocess",
            result=payload,
            success=result.returncode == 0,
            latency_ms=latency_ms,
        ),
    )
    raw = result.stdout
    if result.stderr:
        raw = f"{raw}\n[stderr]\n{result.stderr}" if raw else f"[stderr]\n{result.stderr}"
    if result.returncode != 0:
        raise CodexCommandError(f"Codex command failed with exit code {result.returncode}", raw)
    return raw


def _write_submission(
    cell_dir: Path,
    manifest: dict[str, Any],
    status: str,
    final_output: str,
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    events = read_events(cell_dir / "events.jsonl")
    artifacts_dir = cell_dir / "artifacts"
    submission = read_json(cell_dir / "submission.json", default={}) or {}
    submission.update(
        {
            "task_id": manifest.get("task_id") or submission.get("task_id"),
            "status": status,
            "final_output": final_output,
            "raw_response_file": "raw_response.txt",
            "final_output_file": "final_output.md",
            "deliverables": [p.relative_to(cell_dir).as_posix() for p in sorted(artifacts_dir.rglob("*")) if p.is_file()],
            "trajectory": {
                "tool_calls": [event for event in events if event.get("event_type") in {"tool_call", "tool_result"}],
                "read_all_inputs": any(event.get("event_type") == "file_read" for event in events),
                "wrote_deliverable": bool(list(artifacts_dir.rglob("*"))),
                "recovered_from_tool_error": not error,
                "self_verified": any(event.get("event_type") == "verification" for event in events),
            },
            "run_manifest": "manifest.json",
            "events_file": "events.jsonl",
            "artifact_hash": hash_tree(artifacts_dir),
            "control_violation": False,
            "_no_contradiction": status == "COMPLETED",
            "adapter": "codex",
            "adapter_status": status,
        }
    )
    if error:
        submission["error"] = error
    write_json(cell_dir / "submission.json", submission)
    return submission
