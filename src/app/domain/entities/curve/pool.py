"""
Curve Pool Entity.

Represents a Curve liquidity pool with its current state.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class Pool:
    """
    Curve liquidity pool entity.

    Represents a pool's current state including TVL, APY, and composition.
    This is a mutable entity as pool state changes over time.
    """

    id: str  # Pool contract address
    name: str
    symbol: str
    chain: str
    coins: list[str] = field(default_factory=list)  # Token addresses
    coin_names: list[str] = field(default_factory=list)  # Token symbols
    tvl_usd: Decimal = Decimal("0")
    apy: Decimal = Decimal("0")  # Total APY
    volume_24h_usd: Decimal = Decimal("0")
    fee_percentage: Decimal = Decimal("0.04")
    is_factory: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize pool to dictionary for caching."""
        return {
            "id": self.id,
            "name": self.name,
            "symbol": self.symbol,
            "chain": self.chain,
            "coins": self.coins,
            "coin_names": self.coin_names,
            "tvl_usd": str(self.tvl_usd),
            "apy": str(self.apy),
            "volume_24h_usd": str(self.volume_24h_usd),
            "fee_percentage": str(self.fee_percentage),
            "is_factory": self.is_factory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pool":
        """Deserialize pool from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            symbol=data["symbol"],
            chain=data["chain"],
            coins=data.get("coins", []),
            coin_names=data.get("coin_names", []),
            tvl_usd=Decimal(str(data.get("tvl_usd", "0"))),
            apy=Decimal(str(data.get("apy", "0"))),
            volume_24h_usd=Decimal(str(data.get("volume_24h_usd", "0"))),
            fee_percentage=Decimal(str(data.get("fee_percentage", "0.04"))),
            is_factory=data.get("is_factory", False),
        )
