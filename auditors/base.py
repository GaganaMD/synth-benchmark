from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AuditResult:
    passed: bool
    mode: str
    auditor: str
    details: list[str] = field(default_factory=list)
    control_violation: bool = False


class Auditor:
    name = "base"

    def audit(self, expected_side_effects: dict[str, Any], submission: dict[str, Any], mode: str = "mock") -> AuditResult:
        if mode == "mock":
            return self.audit_mock(expected_side_effects, submission)
        return self.audit_live(expected_side_effects, submission)

    def audit_mock(self, expected_side_effects: dict[str, Any], submission: dict[str, Any]) -> AuditResult:
        if not isinstance(expected_side_effects, dict):
            return AuditResult(False, "mock", self.name, ["expected_side_effects must be an object"])
        requirements = expected_side_effects.get("requirements", [])
        if requirements is None:
            return AuditResult(False, "mock", self.name, ["requirements must not be null"])
        if not isinstance(requirements, list):
            return AuditResult(False, "mock", self.name, ["requirements must be a list"])
        return AuditResult(True, "mock", self.name, [f"mock validated {len(requirements)} side-effect requirements"])

    def audit_live(self, expected_side_effects: dict[str, Any], submission: dict[str, Any]) -> AuditResult:
        raise NotImplementedError("TODO: implement live side-effect audit")


def get_auditor(tool: str) -> Auditor:
    text = (tool or "").lower()
    if "zoho" in text:
        from auditors.zoho import ZohoAuditor

        return ZohoAuditor()
    if "tally" in text:
        from auditors.tally import TallyAuditor

        return TallyAuditor()
    if "email" in text:
        from auditors.email import EmailAuditor

        return EmailAuditor()
    if "onedrive" in text or "sharepoint" in text:
        from auditors.sharepoint import SharePointAuditor

        return SharePointAuditor()
    return Auditor()

