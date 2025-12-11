"""
Funding Rate Value Object.

Immutable representation of perpetual funding rate.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class FundingRate:
    """
    Funding rate value object.

    Represents the 8-hour funding rate for a perpetual market.
    Positive rate means longs pay shorts, negative means shorts pay longs.
    """

    symbol: str
    rate: Decimal  # 8-hour rate (e.g., 0.0001 = 0.01%)
    annualized_rate: Decimal  # Annual rate
    next_funding_time: datetime
    timestamp: datetime

    @property
    def direction_bias(self) -> str:
        """
        Determine market bias based on funding rate.

        Positive funding indicates bullish sentiment (longs paying).
        Negative funding indicates bearish sentiment (shorts paying).
        """
        if self.rate > Decimal("0.0001"):
            return "BULLISH"
        elif self.rate < Decimal("-0.0001"):
            return "BEARISH"
        return "NEUTRAL"

    @property
    def rate_8h_pct(self) -> Decimal:
        """Get 8-hour rate as percentage."""
        return self.rate * 100

    @property
    def is_high_funding(self) -> bool:
        """Check if funding rate is considered high (>0.05% / 8h)."""
        return abs(self.rate) > Decimal("0.0005")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "rate": str(self.rate),
            "annualized_rate": str(self.annualized_rate),
            "next_funding_time": self.next_funding_time.isoformat(),
            "timestamp": self.timestamp.isoformat(),
            "direction_bias": self.direction_bias,
            "rate_8h_pct": str(self.rate_8h_pct),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FundingRate":
        """Deserialize from dictionary."""
        next_funding = data.get("next_funding_time")
        if isinstance(next_funding, str):
            next_funding = datetime.fromisoformat(next_funding)
        elif isinstance(next_funding, (int, float)):
            next_funding = datetime.fromtimestamp(next_funding / 1000)
        else:
            next_funding = datetime.utcnow()

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000)
        else:
            timestamp = datetime.utcnow()

        return cls(
            symbol=data["symbol"],
            rate=Decimal(str(data.get("rate", "0"))),
            annualized_rate=Decimal(str(data.get("annualized_rate", "0"))),
            next_funding_time=next_funding,
            timestamp=timestamp,
        )
