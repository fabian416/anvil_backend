"""
Risk Tier Enum.

Represents the risk level of a lending vault.
"""

from enum import Enum


class RiskTier(Enum):
    """
    Vault risk tier enumeration.

    Based on collateral quality, LLTV, and utilization.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_metrics(
        cls,
        max_lltv: float,
        avg_utilization: float,
    ) -> "RiskTier":
        """
        Calculate risk tier from metrics.

        Args:
            max_lltv: Maximum LLTV in vault allocations
            avg_utilization: Average utilization rate

        Returns:
            RiskTier based on metrics
        """
        if max_lltv >= 0.90 and avg_utilization >= 0.85:
            return cls.VERY_HIGH
        elif max_lltv >= 0.85 or avg_utilization >= 0.80:
            return cls.HIGH
        elif max_lltv >= 0.75 or avg_utilization >= 0.60:
            return cls.MEDIUM
        return cls.LOW
