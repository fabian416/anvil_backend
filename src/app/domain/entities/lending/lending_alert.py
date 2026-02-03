"""
Lending alert domain entity.

Stores alerts for liquidation risk, health factor drops, and position changes.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "position_id",
    "alert_type",
    "severity",
    "title",
    "message",
    "health_factor",
    "threshold_value",
    "current_value",
    "is_read",
    "sent_at",
    "metadata",
    "created_at",
)


@dataclass(slots=True, frozen=True)
class LendingAlert:
    """
    Domain entity representing a lending alert notification.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users
        position_id: Reference to lending_positions (nullable)
        alert_type: Type of alert ('health_factor_low', 'liquidation_risk', etc.)
        severity: Alert severity ('info', 'warning', 'critical')
        title: Alert title
        message: Alert message
        health_factor: Current health factor (if applicable)
        threshold_value: Threshold value that triggered alert
        current_value: Current value that crossed threshold
        is_read: Whether alert has been read
        sent_at: Timestamp when alert was sent
        metadata: Additional alert metadata
        created_at: Creation timestamp
    """

    id: UUID
    user_id: UUID
    position_id: Optional[UUID]
    alert_type: str  # 'health_factor_low', 'liquidation_risk', 'position_closed', etc.
    severity: str  # 'info', 'warning', 'critical'
    title: str
    message: str
    health_factor: Optional[Decimal]
    threshold_value: Optional[Decimal]
    current_value: Optional[Decimal]
    is_read: bool
    sent_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        valid_types = (
            "health_factor_low",
            "liquidation_risk",
            "position_closed",
            "loop_completed",
            "loop_failed",
            "rate_change",
        )
        if self.alert_type not in valid_types:
            raise ValueError(
                f"Invalid alert_type: {self.alert_type}. "
                f"Must be one of {valid_types}."
            )

        valid_severities = ("info", "warning", "critical")
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity: {self.severity}. "
                f"Must be one of {valid_severities}."
            )

        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Alert title cannot be empty.")

        if not self.message or len(self.message.strip()) == 0:
            raise ValueError("Alert message cannot be empty.")

    @property
    def is_info(self) -> bool:
        """Check if alert is informational."""
        return self.severity == "info"

    @property
    def is_warning(self) -> bool:
        """Check if alert is a warning."""
        return self.severity == "warning"

    @property
    def is_critical(self) -> bool:
        """Check if alert is critical."""
        return self.severity == "critical"

    @property
    def is_unread(self) -> bool:
        """Check if alert is unread."""
        return not self.is_read

    @property
    def was_sent(self) -> bool:
        """Check if alert was sent."""
        return self.sent_at is not None

    @property
    def is_health_related(self) -> bool:
        """Check if alert is related to health factor."""
        return self.alert_type in ("health_factor_low", "liquidation_risk")

    @property
    def is_position_related(self) -> bool:
        """Check if alert is related to a specific position."""
        return self.position_id is not None

    @property
    def is_loop_related(self) -> bool:
        """Check if alert is related to leverage loop execution."""
        return self.alert_type in ("loop_completed", "loop_failed")
