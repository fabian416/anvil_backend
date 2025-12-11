"""
Message Fee Value Object.

Immutable representation of cross-chain message fees.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class MessageFee:
    """
    Message fee estimate value object.

    Contains fee breakdown for cross-chain messaging.
    """

    source_chain_id: int
    destination_chain_id: int
    native_fee: Decimal  # In wei
    native_fee_usd: Decimal
    zro_fee: Decimal | None = None  # Optional ZRO token fee

    @property
    def total_fee_usd(self) -> Decimal:
        """Get total fee in USD."""
        return self.native_fee_usd

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_chain_id": self.source_chain_id,
            "destination_chain_id": self.destination_chain_id,
            "native_fee": str(self.native_fee),
            "native_fee_usd": str(self.native_fee_usd),
            "zro_fee": str(self.zro_fee) if self.zro_fee else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageFee":
        """Deserialize from dictionary."""
        zro_fee = data.get("zro_fee")
        return cls(
            source_chain_id=data["source_chain_id"],
            destination_chain_id=data["destination_chain_id"],
            native_fee=Decimal(str(data.get("native_fee", "0"))),
            native_fee_usd=Decimal(str(data.get("native_fee_usd", "0"))),
            zro_fee=Decimal(str(zro_fee)) if zro_fee else None,
        )
