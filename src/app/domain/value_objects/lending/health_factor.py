"""
Health Factor Value Object.

Immutable representation of Aave health factor with risk analysis.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    """Risk level classification."""

    SAFE = "safe"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    LIQUIDATABLE = "liquidatable"


@dataclass(frozen=True)
class HealthFactor:
    """
    Health Factor value object.

    Represents the health factor of an Aave position
    with risk analysis and recommendations.
    """

    value: Decimal
    collateral_usd: Decimal
    debt_usd: Decimal
    liquidation_threshold: Decimal

    @property
    def risk_level(self) -> RiskLevel:
        """Classify risk level based on health factor."""
        if self.value < 1:
            return RiskLevel.LIQUIDATABLE
        elif self.value < Decimal("1.1"):
            return RiskLevel.CRITICAL
        elif self.value < Decimal("1.5"):
            return RiskLevel.HIGH
        elif self.value < Decimal("2.0"):
            return RiskLevel.MODERATE
        else:
            return RiskLevel.SAFE

    @property
    def is_liquidatable(self) -> bool:
        """Check if position can be liquidated."""
        return self.value < 1

    @property
    def distance_to_liquidation(self) -> Decimal:
        """Calculate how far from liquidation (in percentage)."""
        if self.value == Decimal("inf"):
            return Decimal("100")
        return max(Decimal("0"), (self.value - 1) * 100)

    @property
    def max_withdrawable_pct(self) -> Decimal:
        """Calculate max collateral withdrawal percentage to stay above HF=1."""
        if self.value == Decimal("inf") or self.debt_usd == 0:
            return Decimal("100")
        # Safe withdrawal keeps HF at 1.05
        target_hf = Decimal("1.05")
        required_collateral = (self.debt_usd * target_hf) / self.liquidation_threshold
        max_withdraw = self.collateral_usd - required_collateral
        if max_withdraw <= 0:
            return Decimal("0")
        return (max_withdraw / self.collateral_usd) * 100

    @property
    def max_borrowable_pct(self) -> Decimal:
        """Calculate max additional borrow percentage to stay above HF=1."""
        if self.debt_usd == 0:
            return Decimal("100")
        # Safe borrow keeps HF at 1.05
        target_hf = Decimal("1.05")
        max_debt = (self.collateral_usd * self.liquidation_threshold) / target_hf
        additional_borrow = max_debt - self.debt_usd
        if additional_borrow <= 0:
            return Decimal("0")
        return (additional_borrow / self.debt_usd) * 100

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "value": str(self.value) if self.value != Decimal("inf") else "∞",
            "collateral_usd": str(self.collateral_usd),
            "debt_usd": str(self.debt_usd),
            "liquidation_threshold": str(self.liquidation_threshold),
            "risk_level": self.risk_level.value,
            "is_liquidatable": self.is_liquidatable,
            "distance_to_liquidation": str(self.distance_to_liquidation),
            "max_withdrawable_pct": str(self.max_withdrawable_pct),
            "max_borrowable_pct": str(self.max_borrowable_pct),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthFactor":
        """Deserialize from dictionary."""
        value_str = data.get("value", "inf")
        if value_str in ("∞", "inf", "Infinity"):
            value = Decimal("inf")
        else:
            value = Decimal(str(value_str))

        return cls(
            value=value,
            collateral_usd=Decimal(str(data.get("collateral_usd", "0"))),
            debt_usd=Decimal(str(data.get("debt_usd", "0"))),
            liquidation_threshold=Decimal(
                str(data.get("liquidation_threshold", "0.825"))
            ),
        )

    @classmethod
    def calculate(
        cls,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal = Decimal("0.825"),
    ) -> "HealthFactor":
        """
        Calculate health factor from collateral and debt.

        Args:
            collateral_usd: Total collateral value in USD
            debt_usd: Total debt value in USD
            liquidation_threshold: Average liquidation threshold

        Returns:
            HealthFactor value object
        """
        if debt_usd <= 0:
            value = Decimal("inf")
        else:
            value = (collateral_usd * liquidation_threshold) / debt_usd

        return cls(
            value=value,
            collateral_usd=collateral_usd,
            debt_usd=debt_usd,
            liquidation_threshold=liquidation_threshold,
        )
