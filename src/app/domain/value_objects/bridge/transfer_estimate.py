"""
Transfer Estimate Value Object.

Immutable representation of a transfer cost estimate.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class TransferEstimate:
    """
    Transfer estimate value object.

    Contains cost breakdown for cross-chain transfers.
    """

    source_chain: str
    destination_chain: str
    token: str
    amount: Decimal
    fee_usd: Decimal
    gas_estimate_usd: Decimal
    total_cost_usd: Decimal
    estimated_time_seconds: int
    is_express: bool = False

    @property
    def fee_percentage(self) -> Decimal:
        """Calculate fee as percentage of amount."""
        if self.amount == 0:
            return Decimal("0")
        return (self.total_cost_usd / self.amount) * 100

    @property
    def estimated_time_minutes(self) -> int:
        """Get estimated time in minutes."""
        return self.estimated_time_seconds // 60

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_chain": self.source_chain,
            "destination_chain": self.destination_chain,
            "token": self.token,
            "amount": str(self.amount),
            "fee_usd": str(self.fee_usd),
            "gas_estimate_usd": str(self.gas_estimate_usd),
            "total_cost_usd": str(self.total_cost_usd),
            "estimated_time_seconds": self.estimated_time_seconds,
            "is_express": self.is_express,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransferEstimate":
        """Deserialize from dictionary."""
        return cls(
            source_chain=data["source_chain"],
            destination_chain=data["destination_chain"],
            token=data["token"],
            amount=Decimal(str(data.get("amount", "0"))),
            fee_usd=Decimal(str(data.get("fee_usd", "0"))),
            gas_estimate_usd=Decimal(str(data.get("gas_estimate_usd", "0"))),
            total_cost_usd=Decimal(str(data.get("total_cost_usd", "0"))),
            estimated_time_seconds=data.get("estimated_time_seconds", 900),
            is_express=data.get("is_express", False),
        )
