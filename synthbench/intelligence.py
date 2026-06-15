from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from synthbench.common import read_json, write_json
from synthbench.normalization.output import SCHEMA_VERSION as NORMALIZATION_VERSION
from synthbench.schemas.artifacts import CURRENT_VERSION as ARTIFACT_SCHEMA_VERSION
from synthbench.schemas.validation import validate_document
from synthbench.trace.events import parse_timestamp, read_events
from synthbench.trace.reconstruction import reconstruct_cell_events, trace_fidelity_metrics


REPORT_SCHEMA_VERSION = "1.0"
PLATFORM_VERSION = "1.0"
METRICS_VERSION = "1.0"
GRADING_VERSION = "1.0"


def generate_run_intelligence_report(cell: str | Path) -> dict[str, Any]:
    cell_dir = Path(cell)
    manifest = read_json(cell_dir / "manifest.json", default={}) or {}
    task = read_json(Path(manifest.get("task_dir", "")) / "task.json", default={}) if manifest.get("task_dir") else {}
    submission = read_json(cell_dir / "submission.json", default={}) or {}
    canonical = read_json(cell_dir / "canonical_output.json", default={}) or {}
    grading = read_json(cell_dir / "grading_result.json", default={}) or {}
    state_diff = read_json(cell_dir / "state" / "state_diff.json", default={}) or {}
    s0 = read_json(cell_dir / "state" / "S0.json", default={}) or {}
    s1 = read_json(cell_dir / "state" / "S1.json", default={}) or {}
    events = read_events(cell_dir / "events.jsonl")
    reconstructed_events, reconstruction_comparison = _reconstruct_trace_fidelity(cell_dir, events)
    trace_fidelity = trace_fidelity_metrics(events, reconstructed_events) if reconstructed_events else _empty_trace_fidelity(events)
    trace_fidelity["reconstruction_comparison"] = reconstruction_comparison

    workspace_files = _workspace_files(manifest, s0)
    output_text = _output_text(submission, canonical)
    file_reads = _file_events(events, "file_read")
    file_writes = _file_events(events, "file_write")
    tool_analysis = _tool_analysis(events)
    workspace_quality = _workspace_quality_assessment(manifest, task, workspace_files)
    workspace = _workspace_analysis(manifest, task, workspace_files, file_reads, file_writes, state_diff, output_text, workspace_quality)
    documents = _document_utilization(workspace_files, file_reads, state_diff, canonical, grading, output_text)
    decisions = _decision_trace(documents, grading, events)
    grounding = _grounding_report(canonical, documents, grading)
    retrieval = _retrieval_effectiveness(workspace_files, documents)
    state = _state_analysis(s0, s1, state_diff)
    output = _output_analysis(canonical, cell_dir)
    grading_analysis = _grading_analysis(grading)
    execution = _execution_summary(submission, events)
    metrics = _metric_computation(grading_analysis, grounding, retrieval, tool_analysis, state, execution)
    artifact_matrix = _artifact_availability_matrix(cell_dir)
    metric_matrix = _metric_availability_matrix(cell_dir, events, metrics)
    completeness = _benchmark_completeness(
        cell_dir,
        submission,
        events,
        canonical,
        grading,
        metrics,
        artifact_matrix,
        metric_matrix,
        workspace_quality,
        tool_analysis,
    )
    failures = _failure_analysis(execution, tool_analysis, grounding, retrieval, state, output, grading, workspace_quality, completeness)
    enterprise = _enterprise_analysis(task, execution, grounding, state, tool_analysis)
    audit_trail = _audit_trail(grounding, decisions, documents, events)
    research_notes = _research_notes(execution, tool_analysis, grounding, retrieval, grading_analysis, failures)
    reasoning = _reasoning_attribution(decisions, grading_analysis)

    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "artifact_type": "run_intelligence_report",
        "generated_at": _utc_now(),
        "cell": cell_dir.as_posix(),
        "benchmark_completeness": completeness,
        "metric_availability_matrix": metric_matrix,
        "artifact_availability_matrix": artifact_matrix,
        "benchmark_capability_versions": _benchmark_capability_versions(),
        "run_metadata": _run_metadata(manifest, task),
        "execution_summary": execution,
        "tool_analysis": tool_analysis,
        "workspace_analysis": workspace,
        "workspace_quality_assessment": workspace_quality,
        "evidence_document_utilization_analysis": documents,
        "decision_trace_analysis": decisions,
        "evidence_grounding_report": grounding,
        "retrieval_effectiveness": retrieval,
        "document_importance_ranking": _document_importance_ranking(documents),
        "trace_analysis": _trace_analysis(events),
        "trace_fidelity_analysis": trace_fidelity,
        "state_analysis": state,
        "output_analysis": output,
        "grading_analysis": grading_analysis,
        "metric_computation": metrics,
        "failure_analysis": failures,
        "enterprise_analysis": enterprise,
        "audit_trail_reconstruction": audit_trail,
        "benchmark_research_notes": research_notes,
        "reasoning_attribution": reasoning,
        "comparison_ready_fields": _comparison_ready_fields(execution, tool_analysis, documents, state, grading_analysis, metrics, retrieval),
    }
    write_json(cell_dir / "run_intelligence_report.json", report)
    (cell_dir / "run_intelligence_report.md").write_text(render_run_intelligence_markdown(report), encoding="utf-8")
    return report


def _reconstruct_trace_fidelity(cell_dir: Path, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    transcript_present = (cell_dir / "raw_response.txt").exists() or (cell_dir / "final_output.md").exists()
    if not events or not transcript_present:
        return [], {"status": "unavailable", "reason": "events or transcript missing"}
    output_path = cell_dir / "reconstructed_events.jsonl"
    comparison_path = cell_dir / "reconstructed_events.comparison.json"
    try:
        reconstructed, comparison = reconstruct_cell_events(cell_dir, output_path=output_path, comparison_path=comparison_path)
    except Exception as exc:
        return [], {"status": "failed", "reason": f"{type(exc).__name__}: {exc}"}
    comparison["status"] = "generated"
    comparison["reconstructed_events_path"] = output_path.as_posix()
    comparison["comparison_path"] = comparison_path.as_posix()
    return reconstructed, comparison


def _empty_trace_fidelity(events: list[dict[str, Any]]) -> dict[str, Any]:
    tool_events = sum(1 for event in events if event.get("event_type") in {"tool_call", "tool_result"})
    file_events = sum(1 for event in events if event.get("event_type") in {"file_read", "file_write"})
    verification_events = sum(1 for event in events if event.get("event_type") == "verification")
    return {
        "official_metrics": {
            "event_count": len(events),
            "tool_events": tool_events,
            "file_events": file_events,
            "verification_events": verification_events,
            "tool_capture_recall": 1.0,
            "file_capture_recall": 1.0,
            "verification_capture_recall": 1.0,
            "trace_fidelity_score": 1.0,
        },
        "reconstructed_metrics": {
            "event_count": 0,
            "tool_events": 0,
            "file_events": 0,
            "verification_events": 0,
            "tool_capture_recall": 0.0,
            "file_capture_recall": 0.0,
            "verification_capture_recall": 0.0,
            "trace_fidelity_score": 0.0,
            "event_type_counts": {},
        },
        "expected_tool_events": tool_events,
        "expected_file_events": file_events,
        "expected_verification_events": verification_events,
        "missing_tool_events": 0,
        "missing_file_events": 0,
        "missing_verification_events": 0,
    }


def render_run_intelligence_markdown(report: dict[str, Any]) -> str:
    meta = report.get("run_metadata", {})
    execution = report.get("execution_summary", {})
    retrieval = report.get("retrieval_effectiveness", {})
    grounding = report.get("evidence_grounding_report", {})
    grading = report.get("grading_analysis", {})
    lines = [
        f"# Run Intelligence Report: {meta.get('task_id', 'unknown')}",
        "",
        "## Benchmark Completeness",
        _kv(report.get("benchmark_completeness", {})),
        "",
        "## Metric Availability Matrix",
        _table(
            ["Metric", "Available", "Reason"],
            [
                [item.get("metric_name"), "YES" if item.get("available") else "NO", item.get("reason")]
                for item in report.get("metric_availability_matrix", [])
            ],
        ),
        "",
        "## Artifact Availability Matrix",
        _table(
            ["Artifact", "Present", "Validated", "Schema Version", "Reason"],
            [
                [
                    item.get("artifact"),
                    "YES" if item.get("present") else "NO",
                    "YES" if item.get("validated") else "NO",
                    item.get("schema_version"),
                    item.get("reason"),
                ]
                for item in report.get("artifact_availability_matrix", [])
            ],
        ),
        "",
        "## Benchmark Capability Versions",
        _kv(report.get("benchmark_capability_versions", {})),
        "",
        "## Run Metadata",
        _kv(meta),
        "",
        "## Execution Summary",
        _kv(execution),
        "",
        "## Tool Analysis",
        _table(
            ["Tool", "Calls", "Success", "Failures", "Retries", "Avg ms", "Failure Rate"],
            [
                [
                    item.get("tool_name"),
                    item.get("call_count"),
                    item.get("success_count"),
                    item.get("failure_count"),
                    item.get("retry_count"),
                    item.get("avg_latency_ms"),
                    item.get("tool_failure_rate"),
                ]
                for item in report.get("tool_analysis", {}).get("tools_ranked_by_usage", [])
            ],
        ),
        "",
        "## Workspace Analysis",
        _kv(report.get("workspace_analysis", {})),
        "",
        "## Workspace Quality Assessment",
        _kv(report.get("workspace_quality_assessment", {})),
        "",
        "## Document Influence Table",
        _table(
            ["Document", "Read?", "Used?", "Importance Score", "Why Used?"],
            [
                [
                    item.get("document_path"),
                    "YES" if item.get("read") else "NO",
                    "YES" if item.get("used") else "NO",
                    item.get("importance_score"),
                    item.get("why_used"),
                ]
                for item in report.get("evidence_document_utilization_analysis", {}).get("document_influence_table", [])
            ],
        ),
        "",
        "## Decision Trace",
        _table(
            ["Decision", "Type", "Confidence", "Supporting Documents"],
            [
                [
                    item.get("decision_description"),
                    item.get("decision_type"),
                    item.get("confidence"),
                    ", ".join(item.get("supporting_documents", [])),
                ]
                for item in report.get("decision_trace_analysis", {}).get("decisions", [])
            ],
        ),
        "",
        "## Evidence Grounding",
        _kv(grounding),
        "",
        "## Retrieval Effectiveness",
        _kv(retrieval),
        "",
        "## Trace Fidelity",
        _kv({f"official_{k}": v for k, v in report.get("trace_fidelity_analysis", {}).get("official_metrics", {}).items()}),
        _kv({f"reconstructed_{k}": v for k, v in report.get("trace_fidelity_analysis", {}).get("reconstructed_metrics", {}).items()}),
        _kv({k: v for k, v in report.get("trace_fidelity_analysis", {}).items() if k not in {"official_metrics", "reconstructed_metrics", "reconstruction_comparison"}}),
        "",
        "## State Analysis",
        _kv(report.get("state_analysis", {})),
        "",
        "## Output Analysis",
        _kv(report.get("output_analysis", {})),
        "",
        "## Grading Analysis",
        _kv({k: v for k, v in grading.items() if k != "operator_results"}),
        _table(
            ["Operator", "Score", "Pass/Fail", "Reason", "Artifact"],
            [
                [
                    item.get("operator"),
                    item.get("score"),
                    item.get("pass_fail"),
                    item.get("reason"),
                    item.get("supporting_artifact"),
                ]
                for item in grading.get("operator_results", [])
            ],
        ),
        "",
        "## Failure Analysis",
        _table(
            ["Type", "Severity", "Root Cause", "Affected Artifacts", "Recommended Fix"],
            [
                [
                    item.get("failure_type"),
                    item.get("severity"),
                    item.get("root_cause"),
                    ", ".join(item.get("affected_artifacts", [])),
                    item.get("recommended_fix"),
                ]
                for item in report.get("failure_analysis", {}).get("failures", [])
            ],
        ),
        "",
        "## Enterprise Analysis",
        _kv(report.get("enterprise_analysis", {})),
        "",
        "## Audit Trail Reconstruction",
        _table(
            ["Output", "Decision", "Evidence", "Source Document", "Trace Event", "Tool Call"],
            [
                [
                    item.get("output"),
                    item.get("decision"),
                    item.get("evidence"),
                    item.get("source_document"),
                    item.get("trace_event"),
                    item.get("tool_call"),
                ]
                for item in report.get("audit_trail_reconstruction", [])
            ],
        ),
        "",
        "## Benchmark Research Notes",
        _kv(report.get("benchmark_research_notes", {})),
        "",
        "## Reasoning Attribution",
        _kv(report.get("reasoning_attribution", {})),
        "",
        "## Comparison Ready Fields",
        _kv(report.get("comparison_ready_fields", {})),
        "",
    ]
    return "\n".join(lines)


def _benchmark_completeness(
    cell_dir: Path,
    submission: dict[str, Any],
    events: list[dict[str, Any]],
    canonical: dict[str, Any],
    grading: dict[str, Any],
    metrics: dict[str, Any],
    artifact_matrix: list[dict[str, Any]],
    metric_matrix: list[dict[str, Any]],
    workspace_quality: dict[str, Any],
    tool_analysis: dict[str, Any],
) -> dict[str, Any]:
    execution_complete = submission.get("status") in {"COMPLETED", "FAILED", "TIMED_OUT"} and any(
        event.get("event_type") == "task_complete" for event in events
    )
    normalization_complete = bool(canonical) and (cell_dir / "canonical_output.json").exists() and canonical.get("validation", {}).get("valid") is True
    grading_complete = bool(grading) and (cell_dir / "grading_result.json").exists() and int(grading.get("graded_count") or 0) > 0
    metrics_complete = bool(metric_matrix) and all(item.get("available") is True for item in metric_matrix)
    artifact_complete = all(item.get("present") and item.get("validated") for item in artifact_matrix)
    checks = [execution_complete, normalization_complete, grading_complete, metrics_complete, artifact_complete]
    lifecycle = _lifecycle_diagnostics(
        submission=submission,
        events=events,
        execution_complete=execution_complete,
        normalization_complete=normalization_complete,
        grading_complete=grading_complete,
        metrics_complete=metrics_complete,
        artifact_complete=artifact_complete,
        workspace_quality=workspace_quality,
        tool_analysis=tool_analysis,
    )
    return {
        "execution_complete": execution_complete,
        "normalization_complete": normalization_complete,
        "grading_complete": grading_complete,
        "metrics_complete": metrics_complete,
        "artifact_contracts_complete": artifact_complete,
        "intelligence_report_completeness_percent": _round(100 * sum(1 for item in checks if item) / len(checks)),
        "infrastructure_vs_run_status": "run_exercised" if all(checks) else "infrastructure_available_but_run_incomplete",
        **lifecycle,
    }


def _lifecycle_diagnostics(
    *,
    submission: dict[str, Any],
    events: list[dict[str, Any]],
    execution_complete: bool,
    normalization_complete: bool,
    grading_complete: bool,
    metrics_complete: bool,
    artifact_complete: bool,
    workspace_quality: dict[str, Any],
    tool_analysis: dict[str, Any],
) -> dict[str, Any]:
    status = submission.get("status") or "UNKNOWN"
    event_types = {event.get("event_type") for event in events}
    has_task_start = "task_start" in event_types
    has_task_complete = "task_complete" in event_types
    has_tool_events = bool(tool_analysis.get("tools_ranked_by_usage"))
    exception_events = [event for event in events if event.get("event_type") == "exception"]
    tool_failure_rate = _numeric_or_none(tool_analysis.get("tool_failure_rate")) or 0.0
    workspace_class = workspace_quality.get("workspace_classification")

    if not has_task_start:
        termination_stage = "preparation"
        termination_reason = "infrastructure_failure_missing_trace_start"
        execution_status = "NOT_STARTED"
        operator_action_required = "repair run cell trace artifacts before execution"
        lifecycle_stage = "PREPARED_INCOMPLETE"
    elif workspace_class in {"PLACEHOLDER_ONLY", "MISSING"} and not has_tool_events:
        termination_stage = "workspace_discovery"
        termination_reason = "benchmark_corpus_failure"
        execution_status = "BLOCKED"
        operator_action_required = "provide real benchmark input documents or confirm placeholder-only dry run"
        lifecycle_stage = "CORPUS_NOT_READY"
    elif status == "AWAITING_AGENT_OUTPUT" and not has_tool_events and not has_task_complete:
        termination_stage = "pre_execution"
        termination_reason = "operator_cancellation_or_execution_not_started"
        execution_status = "WAITING_FOR_OPERATOR"
        operator_action_required = "confirm workspace selection and start benchmark execution"
        lifecycle_stage = "AWAITING_EXECUTION"
    elif exception_events and "permission" in " ".join(str(e.get("message", "")).lower() for e in exception_events):
        termination_stage = "adapter_execution"
        termination_reason = "infrastructure_failure"
        execution_status = "FAILED"
        operator_action_required = "fix adapter permissions/environment and rerun"
        lifecycle_stage = "EXECUTION_FAILED"
    elif status == "FAILED" or tool_failure_rate > 0:
        termination_stage = "agent_execution"
        termination_reason = "agent_or_tool_failure"
        execution_status = "FAILED"
        operator_action_required = "inspect failed tool calls, agent output, and retry policy"
        lifecycle_stage = "EXECUTION_FAILED"
    elif execution_complete and not normalization_complete:
        termination_stage = "normalization"
        termination_reason = "normalization_pending_or_failed"
        execution_status = "EXECUTED"
        operator_action_required = "run output normalization"
        lifecycle_stage = "EXECUTION_COMPLETE_NORMALIZATION_PENDING"
    elif normalization_complete and not grading_complete:
        termination_stage = "grading"
        termination_reason = "grading_pending_or_failed"
        execution_status = "NORMALIZED"
        operator_action_required = "run grading"
        lifecycle_stage = "NORMALIZED_GRADING_PENDING"
    elif grading_complete and not metrics_complete:
        termination_stage = "metrics"
        termination_reason = "metrics_partially_unavailable"
        execution_status = "GRADED"
        operator_action_required = "review metric availability matrix and missing upstream evidence"
        lifecycle_stage = "GRADED_METRICS_PARTIAL"
    elif execution_complete and normalization_complete and grading_complete and artifact_complete:
        termination_stage = "complete"
        termination_reason = "completed"
        execution_status = "COMPLETED"
        operator_action_required = "none"
        lifecycle_stage = "READY_FOR_REVIEW"
    else:
        termination_stage = "unknown"
        termination_reason = "incomplete_artifacts"
        execution_status = "INCOMPLETE"
        operator_action_required = "review artifact availability matrix"
        lifecycle_stage = "INCOMPLETE"

    if workspace_class in {"PLACEHOLDER_ONLY", "MISSING"} and termination_reason not in {
        "operator_cancellation_or_execution_not_started",
        "infrastructure_failure_missing_trace_start",
    }:
        termination_reason = "benchmark_corpus_failure"
        operator_action_required = "provide real benchmark input documents before interpreting agent metrics"
        lifecycle_stage = "CORPUS_NOT_READY"

    return {
        "execution_status": execution_status,
        "termination_reason": termination_reason,
        "termination_stage": termination_stage,
        "operator_action_required": operator_action_required,
        "benchmark_lifecycle_stage": lifecycle_stage,
    }


def _metric_availability_matrix(cell_dir: Path, events: list[dict[str, Any]], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    artifact_presence = {
        "canonical_output.json": (cell_dir / "canonical_output.json").exists(),
        "grading_result.json": (cell_dir / "grading_result.json").exists(),
        "events.jsonl": (cell_dir / "events.jsonl").exists(),
        "state_diff.json": (cell_dir / "state" / "state_diff.json").exists(),
    }
    task_complete = any(event.get("event_type") == "task_complete" for event in events)
    tool_events = any(event.get("event_type") in {"tool_call", "tool_result"} for event in events)
    metric_requirements = {
        "precision": ["grading_result.json"],
        "recall": ["grading_result.json", "events.jsonl"],
        "f1": ["grading_result.json"],
        "hallucination_rate": ["canonical_output.json"],
        "unsupported_claim_rate": ["canonical_output.json"],
        "workflow_hallucination_rate": ["grading_result.json"],
        "tool_hallucination_rate": ["events.jsonl"],
        "process_compliance": ["events.jsonl"],
        "state_retention": ["state_diff.json"],
        "tool_efficiency": ["events.jsonl"],
        "recovery_rate": ["events.jsonl"],
        "side_effect_success": ["state_diff.json"],
        "runtime_seconds": ["events.jsonl"],
    }
    rows = []
    for metric_name, required in metric_requirements.items():
        missing = [name for name in required if not artifact_presence.get(name)]
        value = metrics.get(metric_name)
        if metric_name == "runtime_seconds":
            available = task_complete
            reason = "task_complete event present" if available else "task_complete event missing"
        elif metric_name in {"tool_hallucination_rate", "tool_efficiency", "recovery_rate"} and not tool_events:
            available = False
            reason = "tool events missing"
        elif missing:
            available = False
            reason = f"{', '.join(missing)} missing"
        elif isinstance(value, dict) and value.get("available") is False:
            available = False
            reason = value.get("reason") or "metric unavailable"
        elif value is None:
            available = False
            reason = "metric value not computed"
        else:
            available = True
            reason = "computed from run artifacts"
        rows.append({"metric_name": metric_name, "available": available, "reason": reason})
    return rows


def _artifact_availability_matrix(cell_dir: Path) -> list[dict[str, Any]]:
    artifacts = [
        ("manifest.json", "manifest", cell_dir / "manifest.json"),
        ("events.jsonl", "events", cell_dir / "events.jsonl"),
        ("S0.json", "S0", cell_dir / "state" / "S0.json"),
        ("S1.json", "S1", cell_dir / "state" / "S1.json"),
        ("state_diff.json", "state_diff", cell_dir / "state" / "state_diff.json"),
        ("canonical_output.json", "canonical_output", cell_dir / "canonical_output.json"),
        ("grading_result.json", "grading_result", cell_dir / "grading_result.json"),
    ]
    rows = []
    for display, artifact_type, path in artifacts:
        if not path.exists():
            rows.append({"artifact": display, "present": False, "validated": False, "schema_version": None, "reason": "missing"})
            continue
        schema_version: str | None = None
        issues: list[str] = []
        if artifact_type == "events":
            try:
                events = read_events(path)
                versions = sorted({str(event.get("schema_version")) for event in events if event.get("schema_version")})
                schema_version = ",".join(versions) if versions else None
                for idx, event in enumerate(events):
                    for issue in validate_document("events", event):
                        issues.append(f"event[{idx}] {issue}")
            except Exception as exc:
                issues.append(str(exc))
        elif artifact_type == "grading_result":
            document = read_json(path, default=None)
            if isinstance(document, dict):
                schema_version = document.get("schema_version")
                for field in ("schema_version", "artifact_type", "operator_results"):
                    if field not in document:
                        issues.append(f"missing structural field {field}")
            else:
                issues.append("grading_result.json must contain a JSON object")
        else:
            document = read_json(path, default=None)
            if isinstance(document, dict):
                schema_version = document.get("schema_version")
                issues.extend(validate_document(artifact_type, document))
            else:
                issues.append(f"{display} must contain a JSON object")
        rows.append(
            {
                "artifact": display,
                "present": True,
                "validated": not issues,
                "schema_version": schema_version,
                "reason": "validated" if not issues else "; ".join(issues[:3]),
            }
        )
    return rows


def _benchmark_capability_versions() -> dict[str, Any]:
    return {
        "platform_version": PLATFORM_VERSION,
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "grading_version": GRADING_VERSION,
        "intelligence_report_version": REPORT_SCHEMA_VERSION,
        "metrics_version": METRICS_VERSION,
    }


def _run_metadata(manifest: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": manifest.get("experiment_id"),
        "run_id": manifest.get("run_id"),
        "task_id": manifest.get("task_id") or task.get("id"),
        "service_line": task.get("service_line"),
        "category": task.get("category"),
        "subcategory": task.get("subcategory"),
        "complexity": task.get("complexity"),
        "model_id": manifest.get("model_id"),
        "harness_id": manifest.get("harness_id") or manifest.get("harness"),
        "seed": manifest.get("seed"),
        "dataset_version": manifest.get("dataset_version"),
        "fixture_version": manifest.get("fixture_version"),
        "environment_version": manifest.get("environment_version"),
        "git_commit": manifest.get("git_commit"),
        "manifest_version": manifest.get("schema_version"),
    }


def _execution_summary(submission: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(event.get("event_type") for event in events)
    start = events[0].get("timestamp") if events else None
    end = events[-1].get("timestamp") if events else None
    runtime = _task_complete(events, "runtime_seconds")
    if runtime is None:
        runtime = _seconds_between(start, end)
    step_count = _task_complete(events, "step_count") or len(events)
    tool_events = [event for event in events if event.get("event_type") in {"tool_call", "tool_result"}]
    failures = [event for event in tool_events if event.get("success") is False]
    status = submission.get("status") or "UNKNOWN"
    success_rate = None if not tool_events else _round((len(tool_events) - len(failures)) / len(tool_events))
    return {
        "status": status,
        "start_time": start,
        "end_time": end,
        "runtime_seconds": runtime,
        "step_count": step_count,
        "tool_call_count": counts.get("tool_call", 0),
        "file_read_count": counts.get("file_read", 0),
        "file_write_count": counts.get("file_write", 0),
        "exception_count": counts.get("exception", 0),
        "recovery_count": sum(1 for e in events if e.get("event_type") in {"retry", "exception"} and e.get("recovered") is True),
        "verification_event_count": counts.get("verification", 0),
        "completion_status": "completed" if status == "COMPLETED" else "failed" if status == "FAILED" else "incomplete_or_unknown",
        "execution_success_rate": success_rate if success_rate is not None else _availability("no tool events recorded"),
    }


def _tool_analysis(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_tool: dict[str, list[dict[str, Any]]] = defaultdict(list)
    retry_count = Counter()
    for event in events:
        if event.get("event_type") in {"tool_call", "tool_result"}:
            by_tool[str(event.get("tool_name") or "unknown")].append(event)
        elif event.get("event_type") == "retry":
            retry_count[str(event.get("tool_name") or event.get("previous_error") or "unknown")] += 1
    tools = []
    for name, tool_events in by_tool.items():
        latencies = [float(e.get("latency_ms") or 0) for e in tool_events if e.get("latency_ms") is not None]
        failures = [e for e in tool_events if e.get("success") is False]
        successes = [e for e in tool_events if e.get("success") is True]
        total = sum(latencies)
        tools.append(
            {
                "tool_name": name,
                "call_count": len([e for e in tool_events if e.get("event_type") == "tool_call"]),
                "event_count": len(tool_events),
                "success_count": len(successes),
                "failure_count": len(failures),
                "retry_count": retry_count.get(name, 0),
                "avg_latency_ms": _round(total / len(latencies)) if latencies else 0.0,
                "max_latency_ms": _round(max(latencies)) if latencies else 0.0,
                "total_latency_ms": _round(total),
                "tool_efficiency_score": _round(len(successes) / max(1, len(tool_events)) / max(1.0, (total / 1000) or 1.0)),
                "tool_failure_rate": _round(len(failures) / max(1, len(tool_events))),
                "tool_recovery_rate": _round(retry_count.get(name, 0) / max(1, len(failures))) if failures else 1.0,
            }
        )
    ranked = sorted(tools, key=lambda item: (item["call_count"], item["event_count"]), reverse=True)
    total_failures = sum(item["failure_count"] for item in ranked)
    total_events = sum(item["event_count"] for item in ranked)
    return {
        "tools_ranked_by_usage": ranked,
        "tool_efficiency_score": _round(sum(item["tool_efficiency_score"] for item in ranked) / len(ranked)) if ranked else _availability("no tool events recorded"),
        "tool_failure_rate": _round(total_failures / total_events) if total_events else _availability("no tool events recorded"),
        "tool_recovery_rate": _round(sum(item["retry_count"] for item in ranked) / total_failures) if total_failures else (1.0 if total_events else _availability("no failures recorded")),
    }


def _workspace_quality_assessment(manifest: dict[str, Any], task: dict[str, Any], workspace_files: list[str]) -> dict[str, Any]:
    workspace_dir = Path(manifest.get("workspace_dir", ""))
    expected = _expected_workspace_items(task.get("workspace") or "")
    real_documents = 0
    placeholder_documents = 0
    synthetic_documents = 0
    classified_files = []
    for rel in sorted(workspace_files):
        full_path = workspace_dir / rel if workspace_dir else Path(rel)
        classification, reason = _classify_workspace_file(rel, full_path)
        if classification == "real":
            real_documents += 1
        elif classification == "placeholder":
            placeholder_documents += 1
        elif classification == "synthetic":
            synthetic_documents += 1
        classified_files.append({"path": rel, "classification": classification, "reason": reason})

    satisfied_expected = set()
    for item in expected:
        for entry in classified_files:
            if entry["classification"] != "real":
                continue
            path = entry["path"]
            if path == item or path.startswith(f"{item}/") or Path(path).name == item:
                satisfied_expected.add(item)
    missing_expected = [item for item in expected if item not in satisfied_expected]
    missing_documents = len(missing_expected)
    total_signals = real_documents + placeholder_documents + synthetic_documents + missing_documents
    readiness_score = _round(real_documents / total_signals) if total_signals else 0.0
    if not workspace_files and missing_documents:
        classification = "MISSING"
    elif real_documents == 0 and placeholder_documents > 0:
        classification = "PLACEHOLDER_ONLY"
    elif real_documents > 0 and (placeholder_documents or synthetic_documents or missing_documents):
        classification = "PARTIAL"
    elif real_documents > 0 and missing_documents == 0:
        classification = "READY"
    else:
        classification = "MISSING"
    return {
        "real_documents": real_documents,
        "placeholder_documents": placeholder_documents,
        "synthetic_documents": synthetic_documents,
        "missing_documents": missing_documents,
        "missing_expected_items": missing_expected,
        "workspace_readiness_score": readiness_score,
        "workspace_classification": classification,
        "classified_files": classified_files,
    }


def _workspace_analysis(
    manifest: dict[str, Any],
    task: dict[str, Any],
    workspace_files: list[str],
    file_reads: list[dict[str, Any]],
    file_writes: list[dict[str, Any]],
    state_diff: dict[str, Any],
    output_text: str,
    workspace_quality: dict[str, Any],
) -> dict[str, Any]:
    read_paths = _paths_from_events(file_reads)
    write_paths = _paths_from_events(file_writes)
    changes = state_diff.get("changes", []) if isinstance(state_diff, dict) else []
    modified = [c.get("path") for c in changes if c.get("change_type") == "modified"]
    available = set(workspace_files)
    read = set(_match_workspace_paths(read_paths, available))
    written = set(write_paths) | {str(c.get("path")) for c in changes if c.get("change_type") == "created"}
    referenced = sorted(path for path in available if Path(path).name and Path(path).name in output_text)
    return {
        "files_discovered": sorted(workspace_files),
        "files_read": sorted(read),
        "files_ignored": sorted(available - read),
        "files_written": sorted(written),
        "files_modified": sorted(str(p) for p in modified if p),
        "workspace_file_recall": _round(len(read) / len(available)) if available else _availability("no workspace files discovered"),
        "workspace_file_precision": _round(len(read & available) / len(read)) if read else _availability("no file_read events recorded"),
        "unused_but_available_files": sorted(available - read),
        "files_never_examined": sorted(available - read),
        "files_referenced_in_output": referenced,
        "real_documents": workspace_quality.get("real_documents"),
        "placeholder_documents": workspace_quality.get("placeholder_documents"),
        "synthetic_documents": workspace_quality.get("synthetic_documents"),
        "missing_documents": workspace_quality.get("missing_documents"),
        "workspace_readiness_score": workspace_quality.get("workspace_readiness_score"),
        "workspace_classification": workspace_quality.get("workspace_classification"),
    }


def _document_utilization(
    workspace_files: list[str],
    file_reads: list[dict[str, Any]],
    state_diff: dict[str, Any],
    canonical: dict[str, Any],
    grading: dict[str, Any],
    output_text: str,
) -> dict[str, Any]:
    read_paths = _paths_from_events(file_reads)
    read_counter = Counter(_match_workspace_paths(read_paths, set(workspace_files)))
    event_by_path = defaultdict(list)
    for event in file_reads:
        for path in _match_workspace_paths(_paths_from_event(event), set(workspace_files)):
            event_by_path[path].append(event)
    grading_text = str(grading)
    state_text = str(state_diff)
    rows = []
    for path in sorted(workspace_files):
        used_final = Path(path).name in output_text or path in output_text
        used_grading = Path(path).name in grading_text or path in grading_text
        used_state = Path(path).name in state_text or path in state_text
        accessed = event_by_path.get(path, [])
        importance = _round(
            min(
                1.0,
                (0.35 if read_counter[path] else 0)
                + (0.3 if used_final else 0)
                + (0.2 if used_grading else 0)
                + (0.15 if used_state else 0),
            )
        )
        rows.append(
            {
                "document_path": path,
                "document_type": _document_type(path),
                "times_accessed": read_counter[path],
                "first_access_timestamp": accessed[0].get("timestamp") if accessed else None,
                "last_access_timestamp": accessed[-1].get("timestamp") if accessed else None,
                "read": read_counter[path] > 0,
                "used": used_final or used_grading or used_state,
                "used_in_final_answer": used_final,
                "used_in_grading_evidence": used_grading,
                "used_in_state_change": used_state,
                "importance_score": importance,
                "why_used": _why_used(path, read_counter[path], used_final, used_grading, used_state),
            }
        )
    return {
        "documents": rows,
        "document_influence_table": rows,
        "documents_accessed": [row for row in rows if row["read"]],
        "documents_used": [row for row in rows if row["used"]],
    }


def _decision_trace(documents: dict[str, Any], grading: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = []
    doc_names = [row["document_path"] for row in documents.get("documents", []) if row.get("used") or row.get("read")]
    tool_event_ids = [e.get("event_id") for e in events if e.get("event_type") in {"tool_call", "tool_result"}]
    for idx, item in enumerate(grading.get("operator_results", []) if isinstance(grading, dict) else [], start=1):
        ev = item.get("evidence", {}) if isinstance(item.get("evidence"), dict) else {}
        op = item.get("operator") or "unknown"
        decisions.append(
            {
                "decision_id": f"decision_{idx:03d}",
                "decision_type": _decision_type(op),
                "decision_description": item.get("criteria") or f"{op} criterion",
                "confidence": _round(float(item.get("score") or 0)),
                "supporting_documents": _documents_from_text(str(item), doc_names),
                "supporting_trace_events": [e.get("event_id") for e in events if e.get("event_type") in {"verification", "side_effect", "exception"}][:5],
                "supporting_tool_calls": tool_event_ids[:5],
                "reason": ev.get("reason"),
            }
        )
    return {"decisions": decisions, "decision_count": len(decisions)}


def _grounding_report(canonical: dict[str, Any], documents: dict[str, Any], grading: dict[str, Any]) -> dict[str, Any]:
    doc_paths = [row["document_path"] for row in documents.get("documents", [])]
    claims = _extract_claims(canonical)
    supported = []
    weak = []
    unsupported = []
    outputs = []
    for claim in claims:
        matched = _documents_from_text(claim, doc_paths)
        score = 1.0 if matched else 0.0
        entry = {"output_item": claim, "source_document": matched[0] if matched else None, "source_location": None, "confidence": score}
        outputs.append(entry)
        if score == 1.0:
            supported.append(claim)
        elif _has_positive_grading(grading):
            weak.append(claim)
        else:
            unsupported.append(claim)
    claims_supported = len(supported) + len(weak)
    return {
        "major_outputs": outputs,
        "claims_made": len(claims),
        "claims_supported": claims_supported,
        "claims_unsupported": len(unsupported),
        "grounding_score": _round(claims_supported / len(claims)) if claims else _availability("no output claims found"),
        "unsupported_claims": unsupported,
        "weakly_supported_claims": weak,
        "fully_supported_claims": supported,
    }


def _retrieval_effectiveness(workspace_files: list[str], documents: dict[str, Any]) -> dict[str, Any]:
    rows = documents.get("documents", [])
    read = [row for row in rows if row.get("read")]
    used = [row for row in rows if row.get("used")]
    required = _required_documents(workspace_files)
    read_paths = {row["document_path"] for row in read}
    used_paths = {row["document_path"] for row in used}
    return {
        "documents_available": len(workspace_files),
        "documents_read": len(read),
        "documents_used": len(used),
        "documents_required": len(required),
        "retrieval_recall": _round(len(read_paths & set(required)) / len(required)) if required else _availability("required documents cannot be inferred"),
        "retrieval_precision": _round(len(used_paths) / len(read_paths)) if read_paths else _availability("no documents read"),
        "critical_documents_missed": sorted(set(required) - read_paths),
        "documents_read_but_unused": sorted(read_paths - used_paths),
    }


def _document_importance_ranking(documents: dict[str, Any]) -> list[dict[str, Any]]:
    ranked = sorted(documents.get("documents", []), key=lambda row: (row.get("importance_score") or 0, row.get("times_accessed") or 0), reverse=True)
    return [
        {
            "rank": idx,
            "document": row.get("document_path"),
            "influence_score": row.get("importance_score"),
            "usage_count": row.get("times_accessed"),
            "decision_count": 1 if row.get("used") else 0,
        }
        for idx, row in enumerate(ranked, start=1)
    ]


def _trace_analysis(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(event.get("event_type") for event in events)
    timeline = [
        {
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
            "event_type": event.get("event_type"),
            "summary": _event_summary(event),
        }
        for event in events
    ]
    idle = []
    for before, after in zip(events, events[1:]):
        delta = _seconds_between(before.get("timestamp"), after.get("timestamp"))
        if delta is not None and delta > 30:
            idle.append({"from_event": before.get("event_id"), "to_event": after.get("event_id"), "seconds": delta})
    return {
        "event_counts_by_type": {event_type: counts.get(event_type, 0) for event_type in sorted(counts)},
        "timeline_reconstruction": timeline,
        "idle_periods": idle,
        "retry_chains": _chains(events, "retry"),
        "failure_cascades": _chains(events, "exception"),
    }


def _state_analysis(s0: dict[str, Any], s1: dict[str, Any], state_diff: dict[str, Any]) -> dict[str, Any]:
    changes = state_diff.get("changes", []) if isinstance(state_diff, dict) else []
    created = [c for c in changes if c.get("change_type") == "created"]
    modified = [c for c in changes if c.get("change_type") == "modified"]
    deleted = [c for c in changes if c.get("change_type") == "deleted"]
    duplicate_paths = [path for path, count in Counter(c.get("path") for c in changes).items() if path and count > 1]
    consistency = 0.0 if duplicate_paths else 1.0
    retention = 0.0 if deleted else 1.0
    return {
        "s0_hash": s0.get("workspace_hash") or state_diff.get("workspace_hash_before"),
        "s1_hash": s1.get("workspace_hash") or state_diff.get("workspace_hash_after"),
        "files_created": [c.get("path") for c in created],
        "files_modified": [c.get("path") for c in modified],
        "files_deleted": [c.get("path") for c in deleted],
        "side_effects_detected": len(changes),
        "duplicate_actions_detected": duplicate_paths,
        "state_consistency_score": consistency,
        "state_retention_score": retention,
    }


def _output_analysis(canonical: dict[str, Any], cell_dir: Path) -> dict[str, Any]:
    content = canonical.get("content", {}) if isinstance(canonical, dict) else {}
    reports = content.get("reports", []) if isinstance(content, dict) else []
    tables = content.get("tables", []) if isinstance(content, dict) else []
    records = content.get("structured_records", []) if isinstance(content, dict) else []
    output_size = sum(len(str(report.get("content", ""))) for report in reports if isinstance(report, dict))
    canonical_path = cell_dir / "canonical_output.json"
    return {
        "output_type": "canonical_output" if canonical else "unavailable",
        "output_size": output_size,
        "records_generated": len(records),
        "tables_generated": len(tables),
        "reports_generated": len(reports),
        "normalization_status": canonical.get("status") if canonical else _availability("canonical_output.json missing"),
        "schema_validation_status": canonical.get("validation", {}).get("valid") if canonical else _availability("canonical_output.json missing"),
        "canonical_output_path": canonical_path.as_posix() if canonical_path.exists() else None,
    }


def _grading_analysis(grading: dict[str, Any]) -> dict[str, Any]:
    results = []
    aggregates = defaultdict(list)
    for item in grading.get("operator_results", []) if isinstance(grading, dict) else []:
        ev = item.get("evidence", {}) if isinstance(item.get("evidence"), dict) else {}
        results.append(
            {
                "operator": item.get("operator"),
                "criteria": item.get("criteria"),
                "score": item.get("score"),
                "pass_fail": item.get("pass_fail"),
                "reason": ev.get("reason"),
                "supporting_artifact": ev.get("supporting_artifact"),
                "supporting_fields": ev.get("supporting_fields", []),
            }
        )
        aggregates[str(item.get("operator"))].append(float(item.get("score") or 0))
    summary = {
        "operator_score": grading.get("operator_score"),
        "all_pass": grading.get("all_pass"),
        "dealbreaker_failed": grading.get("dealbreaker_failed"),
        "rubric_count": grading.get("rubric_count"),
        "graded_count": grading.get("graded_count"),
        "operator_results": results,
    }
    for op in ("exact", "numeric", "presence", "set_match", "contradiction", "state", "tool_use", "safety", "safety_v2"):
        values = aggregates.get(op, [])
        summary[f"{op}_score"] = _round(sum(values) / len(values)) if values else _availability(f"no {op} rubric operator")
    return summary


def _metric_computation(
    grading: dict[str, Any],
    grounding: dict[str, Any],
    retrieval: dict[str, Any],
    tool_analysis: dict[str, Any],
    state: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    exact = _numeric_or_none(grading.get("exact_score"))
    set_match = _numeric_or_none(grading.get("set_match_score"))
    grounding_score = _numeric_or_none(grounding.get("grounding_score"))
    retrieval_recall = _numeric_or_none(retrieval.get("retrieval_recall"))
    claims = grounding.get("claims_made") or 0
    unsupported = grounding.get("claims_unsupported") or 0
    return {
        "precision": set_match if set_match is not None else _availability("set_match score unavailable"),
        "recall": retrieval_recall if retrieval_recall is not None else _availability("retrieval recall unavailable"),
        "f1": set_match if set_match is not None else _availability("set_match score unavailable"),
        "hallucination_rate": _round(unsupported / claims) if claims else _availability("no output claims found"),
        "unsupported_claim_rate": _round(unsupported / claims) if claims else _availability("no output claims found"),
        "workflow_hallucination_rate": 1.0 - exact if exact is not None else _availability("exact score unavailable"),
        "tool_hallucination_rate": tool_analysis.get("tool_failure_rate"),
        "process_compliance": execution.get("execution_success_rate"),
        "state_retention": state.get("state_retention_score"),
        "tool_efficiency": tool_analysis.get("tool_efficiency_score"),
        "recovery_rate": tool_analysis.get("tool_recovery_rate"),
        "side_effect_success": state.get("state_consistency_score"),
        "evidence_grounding": grounding_score if grounding_score is not None else _availability("grounding unavailable"),
    }


def _failure_analysis(
    execution: dict[str, Any],
    tool_analysis: dict[str, Any],
    grounding: dict[str, Any],
    retrieval: dict[str, Any],
    state: dict[str, Any],
    output: dict[str, Any],
    grading: dict[str, Any],
    workspace_quality: dict[str, Any],
    completeness: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    termination_reason = completeness.get("termination_reason")
    if workspace_quality.get("workspace_classification") in {"PLACEHOLDER_ONLY", "MISSING"}:
        failures.append(
            _failure(
                "benchmark_corpus_failure",
                "high",
                f"workspace classified as {workspace_quality.get('workspace_classification')}",
                ["manifest.json", "state/S0.json", "workspace"],
                "Provide real benchmark documents matching the task workspace specification.",
            )
        )
    if termination_reason == "operator_cancellation_or_execution_not_started":
        failures.append(
            _failure(
                "operator_cancellation",
                "medium",
                "run was prepared but execution did not start or was cancelled before tool use",
                ["events.jsonl", "submission.json"],
                "Confirm workspace selection and intentionally start execution.",
            )
        )
    if termination_reason in {"infrastructure_failure", "infrastructure_failure_missing_trace_start"}:
        failures.append(
            _failure(
                "infrastructure_failure",
                "high",
                "run artifacts or adapter environment prevented benchmark execution",
                ["events.jsonl", "manifest.json"],
                "Repair the run cell or adapter environment, then rerun.",
            )
        )
    if execution.get("status") != "COMPLETED" and termination_reason not in {
        "benchmark_corpus_failure",
        "operator_cancellation_or_execution_not_started",
        "infrastructure_failure",
        "infrastructure_failure_missing_trace_start",
    }:
        failures.append(_failure("tool_failure", "high", "run did not complete successfully", ["submission.json", "events.jsonl"], "Inspect adapter/tool errors and rerun once environment access is fixed."))
    if _numeric_or_none(tool_analysis.get("tool_failure_rate")) not in (None, 0.0):
        failures.append(_failure("tool_failure", "medium", "one or more tool events failed", ["events.jsonl"], "Review failed tool_result events and retry/recovery behavior."))
    if retrieval.get("critical_documents_missed"):
        failures.append(_failure("retrieval_failure", "high", "required workspace files were not read", ["events.jsonl", "state/S0.json"], "Ensure the agent enumerates and reads all required workspace inputs."))
    if grounding.get("unsupported_claims"):
        failures.append(_failure("reasoning_failure", "medium", "outputs include claims without direct source linkage", ["canonical_output.json"], "Require outputs to cite source documents or emit structured evidence fields."))
    if state.get("duplicate_actions_detected"):
        failures.append(_failure("state_failure", "medium", "duplicate state actions detected for the same path", ["state/state_diff.json"], "Review side-effect deduplication and idempotency handling."))
    if output.get("schema_validation_status") is not True:
        failures.append(_failure("normalization_failure", "medium", "canonical output is missing or invalid", ["canonical_output.json"], "Run normalization and inspect validation issues."))
    if not grading or grading.get("graded_count") in (None, 0):
        failures.append(_failure("grading_failure", "medium", "grading result is missing or contains no graded operators", ["grading_result.json"], "Run grading after normalization."))
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    failures.sort(key=lambda item: severity_order.get(item["severity"], 9))
    return {"failures": failures, "failure_count": len(failures)}


def _enterprise_analysis(task: dict[str, Any], execution: dict[str, Any], grounding: dict[str, Any], state: dict[str, Any], tool_analysis: dict[str, Any]) -> dict[str, Any]:
    human = task.get("expert_time_mins")
    runtime_s = execution.get("runtime_seconds") if isinstance(execution.get("runtime_seconds"), (int, float)) else None
    agent_mins = _round(runtime_s / 60) if runtime_s is not None else None
    return {
        "human_time_minutes": human if human is not None else _availability("task expert_time_mins unavailable"),
        "agent_runtime_minutes": agent_mins if agent_mins is not None else _availability("runtime unavailable"),
        "time_compression_ratio": _round(float(human) / agent_mins) if human and agent_mins else _availability("requires human time and agent runtime"),
        "task_completion_status": execution.get("completion_status"),
        "auditability_score": _round(_mean_numeric([grounding.get("grounding_score"), state.get("state_consistency_score"), tool_analysis.get("tool_recovery_rate")])),
        "evidence_grounding_score": grounding.get("grounding_score"),
        "operational_reliability_score": _round(_mean_numeric([execution.get("execution_success_rate"), state.get("state_retention_score"), 1 - (_numeric_or_none(tool_analysis.get("tool_failure_rate")) or 0)])),
    }


def _audit_trail(grounding: dict[str, Any], decisions: dict[str, Any], documents: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_rows = decisions.get("decisions", [])
    event = next((e for e in events if e.get("event_type") in {"tool_call", "tool_result", "verification"}), {})
    rows = []
    for idx, output in enumerate(grounding.get("major_outputs", []), start=0):
        decision = decision_rows[idx] if idx < len(decision_rows) else {}
        rows.append(
            {
                "output": output.get("output_item"),
                "decision": decision.get("decision_id"),
                "evidence": decision.get("reason"),
                "source_document": output.get("source_document"),
                "trace_event": event.get("event_id"),
                "tool_call": event.get("tool_name"),
            }
        )
    return rows


def _research_notes(execution: dict[str, Any], tool_analysis: dict[str, Any], grounding: dict[str, Any], retrieval: dict[str, Any], grading: dict[str, Any], failures: dict[str, Any]) -> dict[str, Any]:
    return {
        "strongest_behavior": _strongest_behavior(execution, grounding, grading),
        "weakest_behavior": failures.get("failures", [{}])[0].get("root_cause") if failures.get("failures") else "No material failure detected in derived artifacts.",
        "surprising_behavior": "Unavailable; requires cross-run or evaluator annotation." if not failures.get("failures") else "Failure surfaced in single-run artifact checks.",
        "recommended_follow_up_experiments": _followups(retrieval, grounding, tool_analysis),
        "research_observations": [
            "Report is single-run only and does not create leaderboards.",
            "Evidence metrics depend on trace richness; unavailable fields are explicitly marked.",
        ],
    }


def _reasoning_attribution(decisions: dict[str, Any], grading: dict[str, Any]) -> dict[str, Any]:
    labels = Counter()
    for decision in decisions.get("decisions", []):
        labels[_attribution_for(decision.get("decision_type"))] += 1
    if not labels:
        for item in grading.get("operator_results", []):
            labels[_attribution_for(_decision_type(item.get("operator")))] += 1
    total = sum(labels.values())
    return {
        "counts": dict(labels),
        "percentages": {key: _round(value / total) for key, value in labels.items()} if total else {},
    }


def _comparison_ready_fields(
    execution: dict[str, Any],
    tool_analysis: dict[str, Any],
    documents: dict[str, Any],
    state: dict[str, Any],
    grading: dict[str, Any],
    metrics: dict[str, Any],
    retrieval: dict[str, Any],
) -> dict[str, Any]:
    tool_rows = tool_analysis.get("tools_ranked_by_usage", [])
    return {
        "documents_read": len(documents.get("documents_accessed", [])),
        "documents_used": len(documents.get("documents_used", [])),
        "tool_calls": execution.get("tool_call_count"),
        "tool_failures": sum(row.get("failure_count", 0) for row in tool_rows),
        "tool_retries": sum(row.get("retry_count", 0) for row in tool_rows),
        "reasoning_steps": grading.get("graded_count"),
        "verification_events": execution.get("verification_event_count"),
        "state_changes": len(state.get("files_created", [])) + len(state.get("files_modified", [])) + len(state.get("files_deleted", [])),
        "runtime_seconds": execution.get("runtime_seconds"),
        "grading_scores": {key: value for key, value in grading.items() if key.endswith("_score")},
        "hallucination_metrics": {
            "hallucination_rate": metrics.get("hallucination_rate"),
            "unsupported_claim_rate": metrics.get("unsupported_claim_rate"),
            "workflow_hallucination_rate": metrics.get("workflow_hallucination_rate"),
            "tool_hallucination_rate": metrics.get("tool_hallucination_rate"),
        },
        "retrieval_metrics": {
            "retrieval_recall": retrieval.get("retrieval_recall"),
            "retrieval_precision": retrieval.get("retrieval_precision"),
        },
    }


def _workspace_files(manifest: dict[str, Any], s0: dict[str, Any]) -> list[str]:
    files = s0.get("filesystem", {}).get("workspace_files")
    if isinstance(files, list):
        return sorted(str(item.get("path")) for item in files if item.get("path"))
    workspace_hash = manifest.get("workspace_hash", {})
    if isinstance(workspace_hash, dict):
        return sorted(str(item.get("path")) for item in workspace_hash.get("files", []) if item.get("path"))
    return []


def _output_text(submission: dict[str, Any], canonical: dict[str, Any]) -> str:
    chunks = [str(submission.get("final_output") or "")]
    content = canonical.get("content", {}) if isinstance(canonical, dict) else {}
    for report in content.get("reports", []) if isinstance(content, dict) else []:
        chunks.append(str(report.get("content") or ""))
    return "\n".join(chunks)


def _file_events(events: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    return [event for event in events if event.get("event_type") == event_type]


def _paths_from_events(events: list[dict[str, Any]]) -> list[str]:
    paths = []
    for event in events:
        paths.extend(_paths_from_event(event))
    return paths


def _paths_from_event(event: dict[str, Any]) -> list[str]:
    paths = []
    for key in ("path", "file", "filepath", "document_path", "output_path"):
        value = event.get(key)
        if value:
            paths.append(str(value))
    args = event.get("arguments")
    if isinstance(args, dict):
        for key in ("path", "file", "filepath", "document_path", "output_path", "input"):
            if args.get(key):
                paths.append(str(args[key]))
    return paths


def _match_workspace_paths(paths: list[str], available: set[str]) -> list[str]:
    matched = []
    for path in paths:
        clean = path.replace("\\", "/")
        for candidate in available:
            if clean.endswith(candidate) or clean.endswith(Path(candidate).name) or candidate in clean:
                matched.append(candidate)
    return matched


def _document_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        return "image"
    if suffix in {".csv"}:
        return "csv"
    if suffix in {".md", ".txt"}:
        return "text"
    return suffix.strip(".") or "unknown"


def _expected_workspace_items(workspace_spec: str) -> list[str]:
    items = []
    for raw in str(workspace_spec or "").split(","):
        item = raw.strip()
        if not item:
            continue
        item = item.split("(", 1)[0].strip()
        item = item.split(":", 1)[0].strip()
        item = item.replace("...", "").strip().strip("./")
        if item and item not in items:
            items.append(item)
    return items


def _classify_workspace_file(rel_path: str, full_path: Path) -> tuple[str, str]:
    lower_path = rel_path.lower()
    text = ""
    if full_path.exists() and full_path.is_file() and full_path.stat().st_size <= 1024 * 1024:
        try:
            text = full_path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            text = ""
    placeholder_markers = (
        "placeholder input folder",
        "bi must drop",
        "task-specific input assets here",
        "source workspace spec:",
    )
    synthetic_markers = ("synthetic", "sample", "dummy", "mock", "fixture-only", "generated test")
    if Path(rel_path).name.lower() == "readme.md" and any(marker in text for marker in placeholder_markers):
        return "placeholder", "generated placeholder README; real source document not present"
    if any(marker in lower_path for marker in synthetic_markers) or any(marker in text for marker in synthetic_markers):
        return "synthetic", "file name or content indicates synthetic/sample fixture"
    if not full_path.exists():
        return "missing", "file listed in snapshot but not present on disk"
    return "real", "non-placeholder workspace file"


def _why_used(path: str, reads: int, final: bool, grading: bool, state: bool) -> str:
    reasons = []
    if reads:
        reasons.append(f"accessed {reads} time(s)")
    if final:
        reasons.append("referenced in final answer")
    if grading:
        reasons.append("referenced in grading evidence")
    if state:
        reasons.append("referenced in state changes")
    if not reasons:
        return "Available but no trace evidence of use."
    return "; ".join(reasons)


def _required_documents(workspace_files: list[str]) -> list[str]:
    required_names = {"intake", "chart_of_accounts", "recurring_master", "reimbursement_policy", "prior_postings"}
    return [path for path in workspace_files if any(name in path for name in required_names)]


def _extract_claims(canonical: dict[str, Any]) -> list[str]:
    content = canonical.get("content", {}) if isinstance(canonical, dict) else {}
    claims = []
    for record in content.get("structured_records", []) if isinstance(content, dict) else []:
        if isinstance(record, dict):
            claims.extend(f"{k}: {v}" for k, v in _flat_scalars(record.get("data", record)).items())
    for table in content.get("tables", []) if isinstance(content, dict) else []:
        rows = table.get("rows", []) if isinstance(table, dict) else []
        for row in rows[:50]:
            claims.append(str(row))
    for report in content.get("reports", []) if isinstance(content, dict) else []:
        text = str(report.get("content", ""))
        claims.extend([line.strip() for line in text.splitlines() if line.strip()][:50])
    return claims[:200]


def _flat_scalars(obj: Any, prefix: str = "") -> dict[str, Any]:
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flat_scalars(value, new_key))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            out.update(_flat_scalars(value, f"{prefix}[{idx}]"))
    elif obj not in (None, ""):
        out[prefix] = obj
    return out


def _has_positive_grading(grading: dict[str, Any]) -> bool:
    return bool(grading) and float(grading.get("operator_score") or 0) > 0


def _documents_from_text(text: str, doc_paths: list[str]) -> list[str]:
    return sorted({path for path in doc_paths if path in text or Path(path).name in text})


def _decision_type(operator: Any) -> str:
    return {
        "exact": "Retrieval Driven",
        "numeric": "Calculation Driven",
        "presence": "Retrieval Driven",
        "set_match": "Retrieval Driven",
        "contradiction": "Judgment Driven",
        "state": "Tool Driven",
        "tool_use": "Tool Driven",
        "safety": "Rule Driven",
    }.get(str(operator), "Judgment Driven")


def _attribution_for(decision_type: Any) -> str:
    allowed = {"Retrieval Driven", "Rule Driven", "Calculation Driven", "Judgment Driven", "Tool Driven"}
    return str(decision_type) if decision_type in allowed else "Judgment Driven"


def _task_complete(events: list[dict[str, Any]], field: str) -> Any:
    for event in reversed(events):
        if event.get("event_type") == "task_complete" and field in event:
            return event.get(field)
    return None


def _event_summary(event: dict[str, Any]) -> str:
    event_type = event.get("event_type")
    if event_type in {"tool_call", "tool_result"}:
        return f"{event_type}: {event.get('tool_name')} success={event.get('success')}"
    if event_type == "exception":
        return f"{event.get('exception_type')}: {event.get('message')}"
    return str(event_type)


def _chains(events: list[dict[str, Any]], event_type: str) -> list[dict[str, Any]]:
    return [
        {"event_id": e.get("event_id"), "timestamp": e.get("timestamp"), "summary": _event_summary(e)}
        for e in events
        if e.get("event_type") == event_type
    ]


def _failure(failure_type: str, severity: str, root_cause: str, affected: list[str], fix: str) -> dict[str, Any]:
    return {
        "failure_type": failure_type,
        "severity": severity,
        "root_cause": root_cause,
        "affected_artifacts": affected,
        "recommended_fix": fix,
    }


def _strongest_behavior(execution: dict[str, Any], grounding: dict[str, Any], grading: dict[str, Any]) -> str:
    if execution.get("status") == "COMPLETED" and grading.get("all_pass") is True:
        return "Completed run with all graded rubric operators passing."
    if _numeric_or_none(grounding.get("grounding_score")) == 1.0:
        return "All extracted claims have direct source linkage in available artifacts."
    return "Trace and artifact capture completed enough to support single-run analysis."


def _followups(retrieval: dict[str, Any], grounding: dict[str, Any], tool_analysis: dict[str, Any]) -> list[str]:
    items = []
    if retrieval.get("critical_documents_missed"):
        items.append("Repeat with explicit workspace discovery and required-document read checks.")
    if grounding.get("unsupported_claims"):
        items.append("Require source-citation fields for every output row.")
    if _numeric_or_none(tool_analysis.get("tool_failure_rate")) not in (None, 0.0):
        items.append("Rerun after fixing failing tool/environment dependency.")
    return items or ["Run a second seed/model only after this single-run report is reviewed."]


def _mean_numeric(values: list[Any]) -> float:
    nums = [_numeric_or_none(value) for value in values]
    nums = [value for value in nums if value is not None]
    return sum(nums) / len(nums) if nums else 0.0


def _numeric_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _availability(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def _seconds_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        return _round((parse_timestamp(end) - parse_timestamp(start)).total_seconds())
    except ValueError:
        return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _round(value: float | int, ndigits: int = 6) -> float:
    return round(float(value), ndigits)


def _kv(obj: dict[str, Any]) -> str:
    lines = []
    for key, value in obj.items():
        if isinstance(value, (dict, list)):
            value = _compact(value)
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "_No rows._"
    header = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(_cell(value) for value in row) + " |" for row in rows]
    return "\n".join([header, sep, *body])


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ") if value is not None else ""


def _compact(value: Any) -> str:
    text = str(value)
    return text if len(text) <= 400 else text[:397] + "..."
