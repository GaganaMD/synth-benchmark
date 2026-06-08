from auditors.base import Auditor, AuditResult


class SharePointAuditor(Auditor):
    name = "sharepoint_onedrive"

    def audit_live(self, expected_side_effects, submission):
        # TODO: SharePoint/OneDrive via Microsoft Graph. Credentials/access pending.
        raise NotImplementedError("TODO: SharePoint/OneDrive live audit is intentionally not wired")

