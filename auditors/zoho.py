from auditors.base import Auditor, AuditResult


class ZohoAuditor(Auditor):
    name = "zoho"

    def audit_live(self, expected_side_effects, submission):
        # TODO: real Zoho Books API side-effect verification.
        return AuditResult(False, "live", self.name, ["TODO: Zoho Books API auditor not implemented"])

