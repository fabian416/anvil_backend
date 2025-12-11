"""
Position Entity.

Represents a user's open perpetual futures position.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class Position:
    """
    User position entity.

    Represents an open position with PnL and risk data.
    """

    symbol: str
    side: str  # "long" or "short"
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal
    leverage: Decimal
    liquidation_price: Decimal
    margin_ratio: Decimal = Decimal("0")

    @property
    def pnl_pct(self) -> Decimal:
        """Calculate PnL as percentage of entry."""
        if self.entry_price == 0:
            return Decimal("0")
        if self.side == "long":
            return (self.mark_price - self.entry_price) / self.entry_price * 100
        return (self.entry_price - self.mark_price) / self.entry_price * 100

    @property
    def position_value(self) -> Decimal:
        """Calculate current position value."""
        return self.size * self.mark_price

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.unrealized_pnl > 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "size": str(self.size),
            "entry_price": str(self.entry_price),
            "mark_price": str(self.mark_price),
            "unrealized_pnl": str(self.unrealized_pnl),
            "leverage": str(self.leverage),
            "liquidation_price": str(self.liquidation_price),
            "margin_ratio": str(self.margin_ratio),
            "pnl_pct": str(self.pnl_pct),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Position":
        """Deserialize from dictionary."""
        return cls(
            symbol=data["symbol"],
            side=data["side"],
            size=Decimal(str(data.get("size", "0"))),
            entry_price=Decimal(str(data.get("entry_price", "0"))),
            mark_price=Decimal(str(data.get("mark_price", "0"))),
            unrealized_pnl=Decimal(str(data.get("unrealized_pnl", "0"))),
            leverage=Decimal(str(data.get("leverage", "1"))),
            liquidation_price=Decimal(str(data.get("liquidation_price", "0"))),
            margin_ratio=Decimal(str(data.get("margin_ratio", "0"))),
        )
