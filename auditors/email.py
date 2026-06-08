from auditors.base import Auditor, AuditResult


class EmailAuditor(Auditor):
    name = "email"

    def audit_live(self, expected_side_effects, submission):
        # TODO: inspect connected outbox/sent mailbox.
        return AuditResult(False, "live", self.name, ["TODO: email outbox auditor not implemented"])

