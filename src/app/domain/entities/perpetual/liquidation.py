"""
Liquidation Entity.

Represents a liquidation event in perpetual futures.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class Liquidation:
    """
    Liquidation event entity.

    Represents a forced position closure due to
    insufficient margin.
    """

    symbol: str
    side: str  # "long" or "short"
    size: Decimal
    price: Decimal
    timestamp: datetime

    @property
    def value_usd(self) -> Decimal:
        """Calculate USD value of liquidation."""
        return self.size * self.price

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": str(self.size),
            "price": str(self.price),
            "timestamp": self.timestamp.isoformat(),
            "value_usd": str(self.value_usd),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Liquidation":
        """Deserialize from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000)
        else:
            timestamp = datetime.utcnow()

        return cls(
            symbol=data["symbol"],
            side=data["side"],
            size=Decimal(str(data.get("size", "0"))),
            price=Decimal(str(data.get("price", "0"))),
            timestamp=timestamp,
        )
