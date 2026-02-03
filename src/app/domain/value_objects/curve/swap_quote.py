"""
Swap Quote Value Object.

Immutable representation of a Curve swap quote.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class SwapQuote:
    """
    Swap quote value object.

    Represents a quote for exchanging tokens through Curve.
    Includes price impact and fee information for user awareness.

    This is an immutable value object as quotes are point-in-time
    and should not be modified.
    """

    from_token: str
    to_token: str
    amount_in: Decimal
    amount_out: Decimal
    price_impact: Decimal  # Percentage (e.g., 0.05 = 0.05%)
    fee_amount: Decimal
    exchange_rate: Decimal
    pool_address: str = ""
    warnings: tuple[str, ...] = field(
        default_factory=tuple
    )  # Immutable tuple for frozen dataclass

    def to_dict(self) -> dict[str, Any]:
        """Serialize quote to dictionary."""
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "amount_in": str(self.amount_in),
            "amount_out": str(self.amount_out),
            "price_impact": str(self.price_impact),
            "fee_amount": str(self.fee_amount),
            "exchange_rate": str(self.exchange_rate),
            "pool_address": self.pool_address,
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SwapQuote":
        """Deserialize quote from dictionary."""
        warnings = data.get("warnings", [])
        return cls(
            from_token=data["from_token"],
            to_token=data["to_token"],
            amount_in=Decimal(str(data.get("amount_in", "0"))),
            amount_out=Decimal(str(data.get("amount_out", "0"))),
            price_impact=Decimal(str(data.get("price_impact", "0"))),
            fee_amount=Decimal(str(data.get("fee_amount", "0"))),
            exchange_rate=Decimal(str(data.get("exchange_rate", "0"))),
            pool_address=data.get("pool_address", ""),
            warnings=tuple(warnings) if isinstance(warnings, list) else warnings,
        )

    def with_warnings(self, warnings: list[str]) -> "SwapQuote":
        """Create a new SwapQuote with additional warnings."""
        return SwapQuote(
            from_token=self.from_token,
            to_token=self.to_token,
            amount_in=self.amount_in,
            amount_out=self.amount_out,
            price_impact=self.price_impact,
            fee_amount=self.fee_amount,
            exchange_rate=self.exchange_rate,
            pool_address=self.pool_address,
            warnings=tuple(list(self.warnings) + warnings),
        )
