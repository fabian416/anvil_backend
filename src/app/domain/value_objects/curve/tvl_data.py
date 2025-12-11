"""
TVL Data Value Object.

Immutable representation of Curve TVL data.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TVLData:
    """
    Total Value Locked data value object.

    Represents TVL metrics for Curve on a specific chain.
    This is an immutable value object.
    """

    chain: str
    total_tvl: Decimal
    pool_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize TVL data to dictionary."""
        return {
            "chain": self.chain,
            "total_tvl": str(self.total_tvl),
            "pool_count": self.pool_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TVLData":
        """Deserialize TVL data from dictionary."""
        return cls(
            chain=data["chain"],
            total_tvl=Decimal(str(data.get("total_tvl", "0"))),
            pool_count=data.get("pool_count", 0),
        )
