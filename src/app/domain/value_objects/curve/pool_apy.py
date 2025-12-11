"""
Pool APY Value Object.

Immutable representation of a pool's APY breakdown.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class PoolAPY:
    """
    Pool APY breakdown value object.

    Represents the different components of a pool's yield:
    - base_apy: Yield from trading fees
    - crv_apy: Yield from CRV token rewards
    - reward_apy: Yield from additional reward tokens
    - total_apy: Combined yield

    This is an immutable value object as APY data represents
    a point-in-time snapshot.
    """

    pool_address: str
    base_apy: Decimal  # From trading fees
    crv_apy: Decimal  # CRV rewards
    reward_apy: Decimal  # Extra rewards (e.g., CVX, LDO)
    total_apy: Decimal  # Combined
    boost_min: Decimal = Decimal("1.0")  # Minimum boost (1x)
    boost_max: Decimal = Decimal("2.5")  # Maximum boost with veCRV

    def to_dict(self) -> dict[str, Any]:
        """Serialize APY to dictionary for caching."""
        return {
            "pool_address": self.pool_address,
            "base_apy": str(self.base_apy),
            "crv_apy": str(self.crv_apy),
            "reward_apy": str(self.reward_apy),
            "total_apy": str(self.total_apy),
            "boost_min": str(self.boost_min),
            "boost_max": str(self.boost_max),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PoolAPY":
        """Deserialize APY from dictionary."""
        return cls(
            pool_address=data["pool_address"],
            base_apy=Decimal(str(data.get("base_apy", "0"))),
            crv_apy=Decimal(str(data.get("crv_apy", "0"))),
            reward_apy=Decimal(str(data.get("reward_apy", "0"))),
            total_apy=Decimal(str(data.get("total_apy", "0"))),
            boost_min=Decimal(str(data.get("boost_min", "1.0"))),
            boost_max=Decimal(str(data.get("boost_max", "2.5"))),
        )
