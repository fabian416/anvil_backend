"""
Risk Metrics Value Object.

Immutable representation of position risk calculations.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal


RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "EXTREME"]


@dataclass(frozen=True)
class RiskMetrics:
    """
    Position risk metrics value object.

    Contains calculated risk values for a perpetual position.
    """

    liquidation_price: Decimal
    margin_required: Decimal
    max_loss: Decimal
    distance_to_liquidation_pct: Decimal
    risk_level: RiskLevel

    @property
    def is_high_risk(self) -> bool:
        """Check if position is high risk."""
        return self.risk_level in ("HIGH", "EXTREME")

    @property
    def is_safe(self) -> bool:
        """Check if position has safe margin."""
        return self.distance_to_liquidation_pct > Decimal("20")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "liquidation_price": str(self.liquidation_price),
            "margin_required": str(self.margin_required),
            "max_loss": str(self.max_loss),
            "distance_to_liquidation_pct": str(self.distance_to_liquidation_pct),
            "risk_level": self.risk_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskMetrics":
        """Deserialize from dictionary."""
        return cls(
            liquidation_price=Decimal(str(data.get("liquidation_price", "0"))),
            margin_required=Decimal(str(data.get("margin_required", "0"))),
            max_loss=Decimal(str(data.get("max_loss", "0"))),
            distance_to_liquidation_pct=Decimal(
                str(data.get("distance_to_liquidation_pct", "0"))
            ),
            risk_level=data.get("risk_level", "MEDIUM"),
        )


def assess_risk_level(distance_pct: Decimal) -> RiskLevel:
    """
    Assess risk level based on distance to liquidation.

    Args:
        distance_pct: Distance to liquidation as percentage

    Returns:
        Risk level classification
    """
    if distance_pct < Decimal("5"):
        return "EXTREME"
    elif distance_pct < Decimal("10"):
        return "HIGH"
    elif distance_pct < Decimal("20"):
        return "MEDIUM"
    return "LOW"
