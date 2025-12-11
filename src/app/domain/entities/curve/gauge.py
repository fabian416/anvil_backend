"""
Curve Gauge Entity.

Represents a Curve gauge for liquidity mining rewards.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class Gauge:
    """
    Curve gauge entity for liquidity mining.

    Gauges distribute CRV rewards to liquidity providers
    based on their staked LP tokens.
    """

    address: str  # Gauge contract address
    pool_address: str  # Associated pool address
    crv_emissions_per_day: Decimal = Decimal("0")
    relative_weight: Decimal = Decimal("0")  # Gauge weight for emissions
    total_staked: Decimal = Decimal("0")
    apy: Decimal = Decimal("0")

    def to_dict(self) -> dict[str, Any]:
        """Serialize gauge to dictionary for caching."""
        return {
            "address": self.address,
            "pool_address": self.pool_address,
            "crv_emissions_per_day": str(self.crv_emissions_per_day),
            "relative_weight": str(self.relative_weight),
            "total_staked": str(self.total_staked),
            "apy": str(self.apy),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Gauge":
        """Deserialize gauge from dictionary."""
        return cls(
            address=data["address"],
            pool_address=data["pool_address"],
            crv_emissions_per_day=Decimal(str(data.get("crv_emissions_per_day", "0"))),
            relative_weight=Decimal(str(data.get("relative_weight", "0"))),
            total_staked=Decimal(str(data.get("total_staked", "0"))),
            apy=Decimal(str(data.get("apy", "0"))),
        )
