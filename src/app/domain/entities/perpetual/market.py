"""
Perpetual Market Entity.

Represents a perpetual futures market with its current state.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PerpMarket:
    """
    Perpetual futures market entity.

    Represents a trading market with current prices,
    funding rate, and volume data.
    """

    symbol: str  # e.g., "ETH", "BTC"
    mark_price: Decimal
    index_price: Decimal
    funding_rate: Decimal  # 8-hour rate
    open_interest: Decimal
    volume_24h: Decimal
    price_change_24h: Decimal  # Percentage
    max_leverage: int = 50

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "mark_price": str(self.mark_price),
            "index_price": str(self.index_price),
            "funding_rate": str(self.funding_rate),
            "open_interest": str(self.open_interest),
            "volume_24h": str(self.volume_24h),
            "price_change_24h": str(self.price_change_24h),
            "max_leverage": self.max_leverage,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PerpMarket":
        """Deserialize from dictionary."""
        return cls(
            symbol=data["symbol"],
            mark_price=Decimal(str(data.get("mark_price", "0"))),
            index_price=Decimal(str(data.get("index_price", "0"))),
            funding_rate=Decimal(str(data.get("funding_rate", "0"))),
            open_interest=Decimal(str(data.get("open_interest", "0"))),
            volume_24h=Decimal(str(data.get("volume_24h", "0"))),
            price_change_24h=Decimal(str(data.get("price_change_24h", "0"))),
            max_leverage=data.get("max_leverage", 50),
        )
