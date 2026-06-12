from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from synthbench.common import read_json, write_json
from synthbench.hashing import sha256_file
from synthbench.trace.events import read_events


SCHEMA_VERSION = "1.0"
TOP_LEVEL_REQUIRED = {
    "schema_version",
    "normalized_at",
    "identity",
    "adapter",
    "status",
    "content",
    "provenance",
    "raw_sources",
    "validation",
}
CONTENT_REQUIRED = {"structured_records", "tables", "reports", "side_effect_summaries", "exception_summaries"}


def normalize_cell(cell: str | Path, adapter_id: str | None = None, output_path: str | Path | None = None) -> dict[str, Any]:
    cell_dir = Path(cell)
    manifest = read_json(cell_dir / "manifest.json", default={}) or {}
    submission = read_json(cell_dir / "submission.json", default={}) or {}
    events = read_events(cell_dir / "events.jsonl")
    state_diff = read_json(cell_dir / "state" / "state_diff.json", default=None)
    side_effect_audit = read_json(cell_dir / "state" / "side_effect_audit.json", default=None)
    resolved_adapter = adapter_id or submission.get("adapter") or manifest.get("harness_id") or manifest.get("harness") or "unknown"

    normalizer = _Normalizer(cell_dir)
    final_output_file = _submission_path(submission, "final_output_file", "final_output.md")
    raw_response_file = _submission_path(submission, "raw_response_file", "raw_response.txt")
    final_output = _read_optional_text(cell_dir / final_output_file)
    raw_response = _read_optional_text(cell_dir / raw_response_file)
    if final_output is None:
        final_output = str(submission.get("final_output") or "")
    if raw_response is None:
        raw_response = final_output

    structured_records = []
    answers = submission.get("answers")
    if isinstance(answers, dict) and answers:
        structured_records.append(
            {
                "record_type": "answers",
                "source_path": "submission.json",
                "data": answers,
            }
        )
        normalizer.provenance("submission.json", "/answers", "/content/structured_records/0/data", "copy")

    tables = []
    reports = []
    artifact_paths = _artifact_files(cell_dir)
    for artifact in artifact_paths:
        rel = artifact.relative_to(cell_dir).as_posix()
        suffix = artifact.suffix.lower()
        if suffix == ".csv":
            table = _read_csv_table(artifact, rel)
            normalizer.provenance(rel, "", f"/content/tables/{len(tables)}", "csv_to_table")
            tables.append(table)
        elif suffix == ".json":
            parsed = read_json(artifact, default=None)
            if isinstance(parsed, list) and all(isinstance(row, dict) for row in parsed):
                normalizer.provenance(rel, "", f"/content/tables/{len(tables)}", "json_records_to_table")
                tables.append(_json_records_table(parsed, rel))
            else:
                normalizer.provenance(rel, "", f"/content/structured_records/{len(structured_records)}", "json_to_structured_record")
                structured_records.append({"record_type": "json_artifact", "source_path": rel, "data": parsed})
        elif suffix in {".md", ".txt", ".text", ".log"}:
            normalizer.provenance(rel, "", f"/content/reports/{len(reports)}", "text_to_report")
            reports.append(_text_report(artifact, rel, role="artifact_report"))

    if final_output:
        reports.insert(
            0,
            {
                "report_type": "final_output",
                "source_path": final_output_file,
                "content": final_output,
                "content_sha256": _sha256_text(final_output),
            },
        )
        normalizer.provenance(
            final_output_file,
            "",
            "/content/reports/0/content",
            "copy_text",
        )
    if raw_response and raw_response != final_output:
        reports.append(
            {
                "report_type": "raw_response",
                "source_path": raw_response_file,
                "content": raw_response,
                "content_sha256": _sha256_text(raw_response),
            }
        )
        normalizer.provenance(
            raw_response_file,
            "",
            f"/content/reports/{len(reports) - 1}/content",
            "copy_text",
        )

    side_effect_summary = {
        "source_paths": _existing_rel_paths(cell_dir, ["state/state_diff.json", "state/side_effect_audit.json"]),
        "state_diff_summary": (state_diff or {}).get("summary") if isinstance(state_diff, dict) else None,
        "state_changes": (state_diff or {}).get("changes", []) if isinstance(state_diff, dict) else [],
        "side_effect_audit": side_effect_audit,
        "deliverables": submission.get("deliverables", []),
    }
    if state_diff:
        normalizer.provenance("state/state_diff.json", "/summary", "/content/side_effect_summaries/0/state_diff_summary", "copy")
        normalizer.provenance("state/state_diff.json", "/changes", "/content/side_effect_summaries/0/state_changes", "copy")
    if side_effect_audit:
        normalizer.provenance("state/side_effect_audit.json", "", "/content/side_effect_summaries/0/side_effect_audit", "copy")

    exception_summaries = _exception_summaries(events, submission)
    for idx, _item in enumerate(exception_summaries):
        normalizer.provenance("events.jsonl", "/event_type=exception", f"/content/exception_summaries/{idx}", "event_filter")

    canonical = {
        "schema_version": SCHEMA_VERSION,
        "normalized_at": _utc_now(),
        "identity": {
            "experiment_id": manifest.get("experiment_id"),
            "run_id": manifest.get("run_id"),
            "task_id": manifest.get("task_id") or submission.get("task_id"),
            "harness_id": manifest.get("harness_id") or manifest.get("harness"),
            "model_id": manifest.get("model_id"),
            "dataset_version": manifest.get("dataset_version"),
            "fixture_version": manifest.get("fixture_version"),
        },
        "adapter": {
            "adapter_id": resolved_adapter,
            "source_status": submission.get("status"),
        },
        "status": _canonical_status(submission.get("status")),
        "content": {
            "structured_records": structured_records,
            "tables": tables,
            "reports": reports,
            "side_effect_summaries": [side_effect_summary],
            "exception_summaries": exception_summaries,
        },
        "raw_sources": _raw_sources(cell_dir, submission, artifact_paths),
        "provenance": normalizer.entries,
        "validation": {"valid": True, "issues": []},
    }
    issues = validate_canonical_output(canonical)
    canonical["validation"] = {"valid": not issues, "issues": issues}
    if output_path is None:
        output_path = cell_dir / "canonical_output.json"
    write_json(output_path, canonical)
    return canonical


def validate_canonical_output(output: dict[str, Any]) -> list[str]:
    issues = []
    missing = sorted(field for field in TOP_LEVEL_REQUIRED if field not in output)
    if missing:
        issues.append(f"missing top-level fields: {', '.join(missing)}")
        return issues
    if output.get("schema_version") != SCHEMA_VERSION:
        issues.append(f"unsupported schema_version: {output.get('schema_version')}")
    if not isinstance(output.get("identity"), dict):
        issues.append("identity must be an object")
    else:
        for field in ("run_id", "task_id"):
            if not output["identity"].get(field):
                issues.append(f"identity.{field} is required")
    if not isinstance(output.get("adapter"), dict):
        issues.append("adapter must be an object")
    elif not output["adapter"].get("adapter_id"):
        issues.append("adapter.adapter_id is required")
    if output.get("status") not in {"COMPLETED", "FAILED", "TIMED_OUT", "UNKNOWN"}:
        issues.append(f"invalid status: {output.get('status')}")
    content = output.get("content")
    if not isinstance(content, dict):
        issues.append("content must be an object")
    else:
        missing_content = sorted(field for field in CONTENT_REQUIRED if field not in content)
        if missing_content:
            issues.append(f"content missing fields: {', '.join(missing_content)}")
        for field in CONTENT_REQUIRED:
            if field in content and not isinstance(content[field], list):
                issues.append(f"content.{field} must be a list")
        for idx, table in enumerate(content.get("tables", []) if isinstance(content.get("tables"), list) else []):
            _validate_table(table, idx, issues)
        for idx, report in enumerate(content.get("reports", []) if isinstance(content.get("reports"), list) else []):
            if not isinstance(report, dict):
                issues.append(f"content.reports[{idx}] must be an object")
            elif not isinstance(report.get("content", ""), str):
                issues.append(f"content.reports[{idx}].content must be a string")
    if not isinstance(output.get("raw_sources"), list):
        issues.append("raw_sources must be a list")
    if not isinstance(output.get("provenance"), list):
        issues.append("provenance must be a list")
    else:
        for idx, entry in enumerate(output["provenance"]):
            if not isinstance(entry, dict):
                issues.append(f"provenance[{idx}] must be an object")
                continue
            for field in ("raw_path", "normalized_pointer", "transform"):
                if field not in entry:
                    issues.append(f"provenance[{idx}] missing {field}")
    return issues


class _Normalizer:
    def __init__(self, cell_dir: Path):
        self.cell_dir = cell_dir
        self.entries: list[dict[str, Any]] = []

    def provenance(self, raw_path: str, raw_pointer: str, normalized_pointer: str, transform: str) -> None:
        source = self.cell_dir / raw_path
        self.entries.append(
            {
                "raw_path": raw_path,
                "raw_pointer": raw_pointer,
                "raw_sha256": sha256_file(source) if source.exists() and source.is_file() else None,
                "normalized_pointer": normalized_pointer,
                "transform": transform,
            }
        )


def _validate_table(table: Any, idx: int, issues: list[str]) -> None:
    if not isinstance(table, dict):
        issues.append(f"content.tables[{idx}] must be an object")
        return
    columns = table.get("columns")
    rows = table.get("rows")
    if not isinstance(columns, list) or not all(isinstance(col, str) for col in columns):
        issues.append(f"content.tables[{idx}].columns must be a list of strings")
    if not isinstance(rows, list):
        issues.append(f"content.tables[{idx}].rows must be a list")
        return
    for row_idx, row in enumerate(rows):
        if not isinstance(row, dict):
            issues.append(f"content.tables[{idx}].rows[{row_idx}] must be an object")


def _artifact_files(cell_dir: Path) -> list[Path]:
    artifacts = cell_dir / "artifacts"
    if not artifacts.exists():
        return []
    return sorted(p for p in artifacts.rglob("*") if p.is_file() and p.name != "canonical_output.json")


def _read_csv_table(path: Path, rel: str) -> dict[str, Any]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        columns = list(reader.fieldnames or [])
    return {
        "table_type": "csv",
        "source_path": rel,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
    }


def _json_records_table(records: list[dict[str, Any]], rel: str) -> dict[str, Any]:
    columns = sorted({key for row in records for key in row})
    return {
        "table_type": "json_records",
        "source_path": rel,
        "columns": columns,
        "rows": records,
        "row_count": len(records),
    }


def _text_report(path: Path, rel: str, role: str) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    return {
        "report_type": role,
        "source_path": rel,
        "content": content,
        "content_sha256": _sha256_text(content),
    }


def _exception_summaries(events: list[dict[str, Any]], submission: dict[str, Any]) -> list[dict[str, Any]]:
    summaries = [
        {
            "source": "events.jsonl",
            "exception_type": event.get("exception_type"),
            "message": event.get("message"),
            "recovered": event.get("recovered"),
            "recovery_action": event.get("recovery_action"),
            "event_id": event.get("event_id"),
            "timestamp": event.get("timestamp"),
        }
        for event in events
        if event.get("event_type") == "exception"
    ]
    error = submission.get("error")
    if isinstance(error, dict):
        summaries.append(
            {
                "source": "submission.json",
                "exception_type": error.get("type"),
                "message": error.get("message"),
                "recovered": error.get("recovered"),
                "recovery_action": None,
                "event_id": None,
                "timestamp": None,
            }
        )
    return summaries


def _raw_sources(cell_dir: Path, submission: dict[str, Any], artifacts: list[Path]) -> list[dict[str, Any]]:
    candidates = [
        "manifest.json",
        "submission.json",
        "events.jsonl",
        _submission_path(submission, "raw_response_file", "raw_response.txt"),
        _submission_path(submission, "final_output_file", "final_output.md"),
        "state/state_diff.json",
        "state/side_effect_audit.json",
    ]
    candidates.extend(path.relative_to(cell_dir).as_posix() for path in artifacts)
    seen = set()
    sources = []
    for rel in candidates:
        if not rel or rel in seen:
            continue
        seen.add(rel)
        path = cell_dir / rel
        if path.exists() and path.is_file():
            sources.append({"path": rel, "sha256": sha256_file(path), "size": path.stat().st_size})
    return sources


def _existing_rel_paths(cell_dir: Path, rels: list[str]) -> list[str]:
    return [rel for rel in rels if (cell_dir / rel).exists()]


def _read_optional_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _submission_path(submission: dict[str, Any], field: str, default: str) -> str:
    value = submission.get(field)
    return str(value) if value else default


def _canonical_status(status: Any) -> str:
    value = str(status or "UNKNOWN").upper()
    if value in {"COMPLETED", "FAILED", "TIMED_OUT"}:
        return value
    return "UNKNOWN"


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
