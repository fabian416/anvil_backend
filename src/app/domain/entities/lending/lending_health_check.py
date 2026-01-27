"""
Lending health check domain entity.

Tracks health factor checks over time for monitoring.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

__slots__ = (
    "id",
    "user_id",
    "protocol",
    "chain",
    "health_factor",
    "health_factor_level",
    "total_collateral_usd",
    "total_debt_usd",
    "available_to_borrow_usd",
    "liquidation_price",
    "checked_at",
)


@dataclass(slots=True, frozen=True)
class LendingHealthCheck:
    """
    Domain entity representing a health factor check snapshot.

    Attributes:
        id: Unique identifier
        user_id: Reference to chat_users
        protocol: Lending protocol ('aave' or 'morpho')
        chain: Blockchain network
        health_factor: Current health factor value
        health_factor_level: Risk level ('safe', 'caution', 'danger', 'critical', 'liquidatable')
        total_collateral_usd: Total collateral in USD
        total_debt_usd: Total debt in USD
        available_to_borrow_usd: Available borrowing capacity in USD
        liquidation_price: Estimated liquidation price
        checked_at: Timestamp of health check
    """

    id: UUID
    user_id: UUID
    protocol: str  # 'aave' or 'morpho'
    chain: str
    health_factor: Decimal
    health_factor_level: str  # 'safe', 'caution', 'danger', 'critical', 'liquidatable'
    total_collateral_usd: Decimal
    total_debt_usd: Decimal
    available_to_borrow_usd: Optional[Decimal]
    liquidation_price: Optional[Decimal]
    checked_at: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        valid_levels = ("safe", "caution", "danger", "critical", "liquidatable")
        if self.health_factor_level not in valid_levels:
            raise ValueError(
                f"Invalid health_factor_level: {self.health_factor_level}. "
                f"Must be one of {valid_levels}."
            )

        if self.total_collateral_usd < Decimal("0"):
            raise ValueError(
                f"Invalid total_collateral_usd: {self.total_collateral_usd}. "
                "Must be >= 0."
            )

        if self.total_debt_usd < Decimal("0"):
            raise ValueError(
                f"Invalid total_debt_usd: {self.total_debt_usd}. "
                "Must be >= 0."
            )

    @property
    def is_safe(self) -> bool:
        """Check if health factor is in safe range (>= 2.0)."""
        return self.health_factor_level == "safe"

    @property
    def is_at_risk(self) -> bool:
        """Check if health factor indicates risk (danger, critical, or liquidatable)."""
        return self.health_factor_level in ("danger", "critical", "liquidatable")

    @property
    def requires_immediate_action(self) -> bool:
        """Check if position requires immediate action (critical or liquidatable)."""
        return self.health_factor_level in ("critical", "liquidatable")

    @property
    def ltv_ratio(self) -> Optional[Decimal]:
        """Calculate LTV (Loan-to-Value) ratio."""
        if self.total_collateral_usd == Decimal("0"):
            return None
        return self.total_debt_usd / self.total_collateral_usd

    @property
    def collateralization_ratio(self) -> Optional[Decimal]:
        """Calculate collateralization ratio (inverse of LTV)."""
        if self.total_debt_usd == Decimal("0"):
            return None
        return self.total_collateral_usd / self.total_debt_usd
