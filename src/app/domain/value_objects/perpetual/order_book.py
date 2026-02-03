"""
Order Book Value Object.

Immutable representation of perpetual order book.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class OrderBook:
    """
    Order book value object.

    Represents the current order book state with bids and asks.
    """

    symbol: str
    bids: tuple[tuple[Decimal, Decimal], ...]  # (price, size) tuples
    asks: tuple[tuple[Decimal, Decimal], ...]
    timestamp: datetime

    @property
    def best_bid(self) -> Decimal:
        """Get best bid price."""
        return self.bids[0][0] if self.bids else Decimal("0")

    @property
    def best_ask(self) -> Decimal:
        """Get best ask price."""
        return self.asks[0][0] if self.asks else Decimal("0")

    @property
    def spread(self) -> Decimal:
        """Calculate bid-ask spread."""
        if self.bids and self.asks:
            return self.best_ask - self.best_bid
        return Decimal("0")

    @property
    def spread_pct(self) -> Decimal:
        """Calculate spread as percentage of mid price."""
        if self.bids and self.asks:
            mid = (self.best_ask + self.best_bid) / 2
            if mid > 0:
                return self.spread / mid * 100
        return Decimal("0")

    @property
    def mid_price(self) -> Decimal:
        """Calculate mid price."""
        if self.bids and self.asks:
            return (self.best_ask + self.best_bid) / 2
        return Decimal("0")

    @property
    def bid_depth(self) -> Decimal:
        """Calculate total bid depth (volume)."""
        return sum(size for _, size in self.bids)

    @property
    def ask_depth(self) -> Decimal:
        """Calculate total ask depth (volume)."""
        return sum(size for _, size in self.asks)

    @property
    def imbalance(self) -> Decimal:
        """
        Calculate order book imbalance.

        Positive = more bids (bullish), Negative = more asks (bearish).
        """
        total = self.bid_depth + self.ask_depth
        if total == 0:
            return Decimal("0")
        return (self.bid_depth - self.ask_depth) / total

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "bids": [[str(p), str(s)] for p, s in self.bids],
            "asks": [[str(p), str(s)] for p, s in self.asks],
            "timestamp": self.timestamp.isoformat(),
            "spread": str(self.spread),
            "spread_pct": str(self.spread_pct),
            "mid_price": str(self.mid_price),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrderBook":
        """Deserialize from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000)
        else:
            timestamp = datetime.now(UTC)

        bids = tuple(
            (Decimal(str(b[0])), Decimal(str(b[1]))) for b in data.get("bids", [])
        )
        asks = tuple(
            (Decimal(str(a[0])), Decimal(str(a[1]))) for a in data.get("asks", [])
        )

        return cls(
            symbol=data["symbol"],
            bids=bids,
            asks=asks,
            timestamp=timestamp,
        )
