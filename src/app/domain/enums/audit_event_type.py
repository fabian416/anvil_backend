"""
Audit event type enum for compliance and security logging.

Categorizes events into user actions, system events, security events, and data access.
"""

from enum import StrEnum


class AuditEventType(StrEnum):
    """
    Enum defining types of auditable events.

    Organized by category: user actions, system events, security, and data access.
    """

    # User Actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTRATION = "user_registration"
    USER_PROFILE_UPDATE = "user_profile_update"
    USER_PREFERENCE_CHANGE = "user_preference_change"
    USER_PASSWORD_CHANGE = "user_password_change"
    USER_EMAIL_CHANGE = "user_email_change"
    USER_ROLE_CHANGE = "user_role_change"

    # Export Actions
    EXPORT_REQUEST = "export_request"
    EXPORT_DOWNLOAD = "export_download"
    EXPORT_DELETION = "export_deletion"

    # Conversation Actions
    CONVERSATION_CREATE = "conversation_create"
    CONVERSATION_DELETE = "conversation_delete"
    CONVERSATION_SHARE = "conversation_share"
    MESSAGE_CREATE = "message_create"
    MESSAGE_UPDATE = "message_update"
    MESSAGE_DELETE = "message_delete"

    # Template Actions
    TEMPLATE_CREATE = "template_create"
    TEMPLATE_UPDATE = "template_update"
    TEMPLATE_DELETE = "template_delete"
    TEMPLATE_EXECUTE = "template_execute"

    # Agent Actions
    AGENT_EXECUTION_START = "agent_execution_start"
    AGENT_EXECUTION_COMPLETE = "agent_execution_complete"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    VOTING_ROUND_START = "voting_round_start"
    VOTING_ROUND_COMPLETE = "voting_round_complete"

    # Security Events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    AUTH_TOKEN_REVOKE = "auth_token_revoke"
    UNAUTHORIZED_ACCESS_ATTEMPT = "unauthorized_access_attempt"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data Access Events
    PII_VIEW = "pii_view"
    PII_EXPORT = "pii_export"
    PII_MODIFICATION = "pii_modification"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"

    # System Events
    SYSTEM_CONFIGURATION_CHANGE = "system_configuration_change"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    BACKGROUND_JOB_START = "background_job_start"
    BACKGROUND_JOB_COMPLETE = "background_job_complete"
    BACKGROUND_JOB_FAILED = "background_job_failed"

    # Administrative Actions
    ADMIN_USER_SUSPENSION = "admin_user_suspension"
    ADMIN_USER_ACTIVATION = "admin_user_activation"
    ADMIN_USER_DELETION = "admin_user_deletion"
    ADMIN_ROLE_ASSIGNMENT = "admin_role_assignment"
    ADMIN_PERMISSION_GRANT = "admin_permission_grant"
    ADMIN_PERMISSION_REVOKE = "admin_permission_revoke"

    @property
    def is_security_event(self) -> bool:
        """Check if event is security-related."""
        security_events = {
            self.AUTH_SUCCESS,
            self.AUTH_FAILURE,
            self.AUTH_TOKEN_REFRESH,
            self.AUTH_TOKEN_REVOKE,
            self.UNAUTHORIZED_ACCESS_ATTEMPT,
            self.PERMISSION_DENIED,
            self.RATE_LIMIT_EXCEEDED,
            self.SUSPICIOUS_ACTIVITY,
        }
        return self in security_events

    @property
    def is_data_access_event(self) -> bool:
        """Check if event involves data access."""
        data_access_events = {
            self.PII_VIEW,
            self.PII_EXPORT,
            self.PII_MODIFICATION,
            self.SENSITIVE_DATA_ACCESS,
            self.BULK_DATA_EXPORT,
        }
        return self in data_access_events

    @property
    def is_admin_action(self) -> bool:
        """Check if event is an administrative action."""
        admin_actions = {
            self.ADMIN_USER_SUSPENSION,
            self.ADMIN_USER_ACTIVATION,
            self.ADMIN_USER_DELETION,
            self.ADMIN_ROLE_ASSIGNMENT,
            self.ADMIN_PERMISSION_GRANT,
            self.ADMIN_PERMISSION_REVOKE,
        }
        return self in admin_actions

    @property
    def requires_retention(self) -> bool:
        """
        Check if event requires long-term retention for compliance.

        Security events, data access, and admin actions typically require
        longer retention periods for regulatory compliance.
        """
        return (
            self.is_security_event or self.is_data_access_event or self.is_admin_action
        )
