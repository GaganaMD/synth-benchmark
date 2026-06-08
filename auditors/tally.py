from auditors.base import Auditor, AuditResult


class TallyAuditor(Auditor):
    name = "tally"

    def audit_live(self, expected_side_effects, submission):
        # TODO: real Tally XML/ODBC verification over EC2 tunnel.
        return AuditResult(False, "live", self.name, ["TODO: Tally live auditor not implemented"])

