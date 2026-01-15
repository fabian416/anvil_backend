"""
Audit Log Entry domain entity.

Enterprise-grade audit logging for compliance and security tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from app.domain.enums.audit_event_type import AuditEventType


@dataclass
class AuditLogEntry:
    """
    Audit log entry entity.

    Represents a single auditable event in the system for compliance and security.
    Immutable after creation with indexed timestamp for efficient querying.
    """

    id: UUID = field(default_factory=uuid4)
    event_type: AuditEventType = None  # type: ignore
    action: str = None  # type: ignore
    outcome: str = "success"  # "success", "failure", "pending"

    # Context
    user_id: Optional[UUID] = None
    resource_id: Optional[UUID] = None
    resource_type: Optional[str] = None

    # Additional Data
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Error details (for failed events)
    error_message: Optional[str] = None
    error_code: Optional[str] = None

    # Timestamps (immutable)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Validate required fields."""
        if self.event_type is None:
            raise ValueError("event_type is required")
        if self.action is None:
            raise ValueError("action is required")

        # Ensure created_at is set and immutable
        if not isinstance(self.created_at, datetime):
            object.__setattr__(self, "created_at", datetime.now(UTC))

    def is_success(self) -> bool:
        """Check if event was successful."""
        return self.outcome == "success"

    def is_failure(self) -> bool:
        """Check if event failed."""
        return self.outcome == "failure"

    def is_pending(self) -> bool:
        """Check if event is pending completion."""
        return self.outcome == "pending"

    def is_security_event(self) -> bool:
        """Check if this is a security-related event."""
        return self.event_type.is_security_event

    def is_data_access_event(self) -> bool:
        """Check if this is a data access event."""
        return self.event_type.is_data_access_event

    def is_admin_action(self) -> bool:
        """Check if this is an administrative action."""
        return self.event_type.is_admin_action

    def requires_retention(self) -> bool:
        """
        Check if this event requires long-term retention.

        Security events, data access, and admin actions typically require
        longer retention periods for regulatory compliance.
        """
        return self.event_type.requires_retention

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the audit log entry.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def with_error(self, error_message: str, error_code: Optional[str] = None) -> None:
        """
        Mark event as failed with error details.

        Args:
            error_message: Error description
            error_code: Optional error code
        """
        object.__setattr__(self, "outcome", "failure")
        object.__setattr__(self, "error_message", error_message)
        if error_code:
            object.__setattr__(self, "error_code", error_code)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "action": self.action,
            "outcome": self.outcome,
            "user_id": str(self.user_id) if self.user_id else None,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "resource_type": self.resource_type,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AuditLogEntry("
            f"id={self.id}, "
            f"event_type={self.event_type.value}, "
            f"action={self.action}, "
            f"outcome={self.outcome}, "
            f"user_id={self.user_id}, "
            f"created_at={self.created_at.isoformat()}"
            f")"
        )
