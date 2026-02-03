"""
User lending preferences domain entity.

Stores user-specific risk preferences and notification settings.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "risk_tolerance",
    "min_health_factor",
    "max_leverage",
    "preferred_protocol",
    "auto_rebalance",
    "notification_health_threshold",
    "notification_email",
    "notification_enabled",
    "created_at",
    "updated_at",
)


@dataclass(slots=True, frozen=True)
class UserLendingPreferences:
    """
    Domain entity representing user lending preferences.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users
        risk_tolerance: Risk level ('conservative', 'moderate', 'aggressive')
        min_health_factor: Minimum acceptable health factor (default: 1.5)
        max_leverage: Maximum leverage multiplier (default: 3.0)
        preferred_protocol: Preferred lending protocol ('aave' or 'morpho')
        auto_rebalance: Enable automatic rebalancing
        notification_health_threshold: Health factor threshold for notifications (default: 1.3)
        notification_email: Email for notifications
        notification_enabled: Enable/disable notifications
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID
    user_id: UUID
    risk_tolerance: str  # 'conservative', 'moderate', 'aggressive'
    min_health_factor: Decimal
    max_leverage: Decimal
    preferred_protocol: Optional[str]  # 'aave' or 'morpho'
    auto_rebalance: bool
    notification_health_threshold: Optional[Decimal]
    notification_email: Optional[str]
    notification_enabled: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if self.risk_tolerance not in ("conservative", "moderate", "aggressive"):
            raise ValueError(
                f"Invalid risk_tolerance: {self.risk_tolerance}. "
                "Must be 'conservative', 'moderate', or 'aggressive'."
            )

        if self.min_health_factor < Decimal("1.0") or self.min_health_factor > Decimal(
            "10.0"
        ):
            raise ValueError(
                f"Invalid min_health_factor: {self.min_health_factor}. "
                "Must be between 1.0 and 10.0."
            )

        if self.max_leverage < Decimal("1.0") or self.max_leverage > Decimal("10.0"):
            raise ValueError(
                f"Invalid max_leverage: {self.max_leverage}. "
                "Must be between 1.0 and 10.0."
            )

        if self.preferred_protocol and self.preferred_protocol not in (
            "aave",
            "morpho",
        ):
            raise ValueError(
                f"Invalid preferred_protocol: {self.preferred_protocol}. "
                "Must be 'aave' or 'morpho'."
            )

    @property
    def is_conservative(self) -> bool:
        """Check if user has conservative risk tolerance."""
        return self.risk_tolerance == "conservative"

    @property
    def is_moderate(self) -> bool:
        """Check if user has moderate risk tolerance."""
        return self.risk_tolerance == "moderate"

    @property
    def is_aggressive(self) -> bool:
        """Check if user has aggressive risk tolerance."""
        return self.risk_tolerance == "aggressive"

    @property
    def has_notification_email(self) -> bool:
        """Check if user has configured notification email."""
        return self.notification_email is not None and len(self.notification_email) > 0

    @property
    def should_notify_health_issues(self) -> bool:
        """Check if user should receive health factor notifications."""
        return (
            self.notification_enabled and self.notification_health_threshold is not None
        )
