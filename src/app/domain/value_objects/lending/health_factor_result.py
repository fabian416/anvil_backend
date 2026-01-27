"""
Health Factor Validation Result Value Object.

This value object represents the result of health factor validation
for lending operations, particularly borrows that could affect position safety.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any


class HealthFactorLevel(str, Enum):
    """
    Health factor risk level classification.

    Levels:
    - SAFE: HF >= 2.0 (recommended for most users)
    - CAUTION: 1.5 <= HF < 2.0 (acceptable but monitor closely)
    - DANGER: 1.2 <= HF < 1.5 (risky, consider reducing exposure)
    - CRITICAL: 1.0 <= HF < 1.2 (very high liquidation risk)
    - LIQUIDATABLE: HF < 1.0 (position will be liquidated)
    """
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"
    CRITICAL = "critical"
    LIQUIDATABLE = "liquidatable"


@dataclass(frozen=True)
class HealthFactorResult:
    """
    Immutable result of health factor validation.

    Contains all information needed to assess the safety of a
    lending operation before execution.
    """

    current_hf: Decimal
    """Current health factor before operation"""

    projected_hf: Decimal
    """Projected health factor after operation"""

    level: HealthFactorLevel
    """Risk level classification of projected HF"""

    is_safe: bool
    """False if projected HF < 1.2 (minimum recommended)"""

    warning_message: str
    """Human-readable warning or confirmation message"""

    liquidation_price: Decimal | None
    """Asset price at which liquidation would occur (if applicable)"""

    max_safe_borrow_usd: Decimal
    """Maximum additional borrow to maintain HF >= 1.5"""

    # Context for display
    collateral_usd: Decimal
    """Total collateral value in USD"""

    current_debt_usd: Decimal
    """Current debt before operation"""

    projected_debt_usd: Decimal
    """Projected debt after operation"""

    @property
    def color(self) -> str:
        """
        Color code for UI display.

        Returns:
            Color name for frontend visualization
        """
        return {
            HealthFactorLevel.SAFE: "green",
            HealthFactorLevel.CAUTION: "yellow",
            HealthFactorLevel.DANGER: "orange",
            HealthFactorLevel.CRITICAL: "red",
            HealthFactorLevel.LIQUIDATABLE: "red",
        }[self.level]

    @property
    def emoji(self) -> str:
        """
        Emoji indicator for risk level.

        Returns:
            Emoji for visual risk indication
        """
        return {
            HealthFactorLevel.SAFE: "✅",
            HealthFactorLevel.CAUTION: "⚠️",
            HealthFactorLevel.DANGER: "🔶",
            HealthFactorLevel.CRITICAL: "🔴",
            HealthFactorLevel.LIQUIDATABLE: "❌",
        }[self.level]

    @property
    def should_block(self) -> bool:
        """
        Whether this operation should be blocked.

        Returns:
            True if operation is too risky to proceed
        """
        return not self.is_safe

    @property
    def distance_to_liquidation_pct(self) -> Decimal:
        """
        Percentage distance from liquidation.

        Returns:
            Percentage above liquidation threshold (HF - 1.0) * 100
        """
        if self.projected_hf == Decimal("inf"):
            return Decimal("100")
        return max(Decimal("0"), (self.projected_hf - Decimal("1")) * Decimal("100"))

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary for API responses.

        Returns:
            Dictionary representation
        """
        return {
            "current_hf": str(self.current_hf) if self.current_hf != Decimal("inf") else "∞",
            "projected_hf": str(self.projected_hf) if self.projected_hf != Decimal("inf") else "∞",
            "level": self.level.value,
            "is_safe": self.is_safe,
            "warning_message": self.warning_message,
            "liquidation_price": str(self.liquidation_price) if self.liquidation_price else None,
            "max_safe_borrow_usd": str(self.max_safe_borrow_usd),
            "collateral_usd": str(self.collateral_usd),
            "current_debt_usd": str(self.current_debt_usd),
            "projected_debt_usd": str(self.projected_debt_usd),
            "color": self.color,
            "emoji": self.emoji,
            "distance_to_liquidation_pct": str(self.distance_to_liquidation_pct),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthFactorResult":
        """
        Deserialize from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            HealthFactorResult instance
        """
        def parse_hf(value: str | None) -> Decimal:
            if not value or value in ("∞", "inf", "Infinity"):
                return Decimal("inf")
            return Decimal(str(value))

        return cls(
            current_hf=parse_hf(data.get("current_hf")),
            projected_hf=parse_hf(data.get("projected_hf")),
            level=HealthFactorLevel(data["level"]),
            is_safe=data["is_safe"],
            warning_message=data["warning_message"],
            liquidation_price=Decimal(str(data["liquidation_price"])) if data.get("liquidation_price") else None,
            max_safe_borrow_usd=Decimal(str(data.get("max_safe_borrow_usd", "0"))),
            collateral_usd=Decimal(str(data.get("collateral_usd", "0"))),
            current_debt_usd=Decimal(str(data.get("current_debt_usd", "0"))),
            projected_debt_usd=Decimal(str(data.get("projected_debt_usd", "0"))),
        )
