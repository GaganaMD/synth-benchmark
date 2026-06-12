from __future__ import annotations

import uuid
from collections import Counter
from pathlib import Path
from typing import Any


STATUSES = {"PASS", "FAIL", "PARTIAL"}


def new_effect_id() -> str:
    return f"effect_{uuid.uuid4().hex[:12]}"


def audit_effect(effect_type: str, target: str, expected: Any, observed: Any, effect_id: str | None = None) -> dict[str, Any]:
    if expected == observed:
        status = "PASS"
    elif observed in (None, "", [], {}):
        status = "FAIL"
    else:
        status = "PARTIAL"
    return {
        "effect_id": effect_id or new_effect_id(),
        "effect_type": effect_type,
        "target": target,
        "expected": expected,
        "observed": observed,
        "status": status,
    }


def audit_files(expected_outputs: list[str], diff: dict[str, Any]) -> dict[str, Any]:
    output_changes = [c for c in diff.get("changes", []) if c.get("scope") == "outputs"]
    created = sorted(c["path"] for c in output_changes if c.get("change_type") == "created")
    modified = sorted(c["path"] for c in output_changes if c.get("change_type") == "modified")
    observed = sorted(set(created + modified))
    expected_set = set(expected_outputs)
    observed_set = set(observed)
    missing = sorted(expected_set - observed_set)
    unexpected = sorted(observed_set - expected_set) if expected_set else []
    effects = [audit_effect("file_output", path, "present", "present" if path in observed_set else None) for path in sorted(expected_set)]
    return {
        "schema_version": "1.0",
        "expected_outputs": expected_outputs,
        "observed_outputs": observed,
        "missing_outputs": missing,
        "unexpected_outputs": unexpected,
        "effects": effects,
        "status": "PASS" if not missing and not unexpected else "FAIL" if missing else "PARTIAL",
    }


def duplicate_outputs(paths: list[str]) -> list[dict[str, Any]]:
    names = [Path(path).name for path in paths]
    counts = Counter(names)
    return [{"name": name, "count": count} for name, count in sorted(counts.items()) if count > 1]


def duplicate_side_effects(effects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [(e.get("effect_type"), e.get("target"), _stable(e.get("observed"))) for e in effects]
    counts = Counter(keys)
    duplicates = []
    for key, count in sorted(counts.items()):
        if count > 1:
            effect_type, target, observed = key
            duplicates.append({"effect_type": effect_type, "target": target, "observed": observed, "count": count})
    return duplicates


def duplicate_postings(postings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        (
            posting.get("date"),
            posting.get("vendor"),
            posting.get("invoice_no"),
            str(posting.get("amount")),
            posting.get("ledger"),
        )
        for posting in postings
    ]
    counts = Counter(keys)
    duplicates = []
    for key, count in sorted(counts.items()):
        if count > 1:
            date, vendor, invoice_no, amount, ledger = key
            duplicates.append(
                {
                    "date": date,
                    "vendor": vendor,
                    "invoice_no": invoice_no,
                    "amount": amount,
                    "ledger": ledger,
                    "count": count,
                }
            )
    return duplicates


def _stable(value: Any) -> str:
    return repr(value)
