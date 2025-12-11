"""
Bridge Route Value Object.

Immutable representation of a cross-chain bridge route.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BridgeRoute:
    """
    Bridge route value object.

    Contains routing information for cross-chain transfers.
    """

    source_chain: str
    destination_chain: str
    token: str
    estimated_time_seconds: int
    fee_usd: Decimal
    fee_native: Decimal
    security_score: int  # 0-100
    is_express: bool = False

    @property
    def estimated_time_minutes(self) -> int:
        """Get estimated time in minutes."""
        return self.estimated_time_seconds // 60

    @property
    def is_secure(self) -> bool:
        """Check if route has high security score (>80)."""
        return self.security_score >= 80

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "source_chain": self.source_chain,
            "destination_chain": self.destination_chain,
            "token": self.token,
            "estimated_time_seconds": self.estimated_time_seconds,
            "fee_usd": str(self.fee_usd),
            "fee_native": str(self.fee_native),
            "security_score": self.security_score,
            "is_express": self.is_express,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BridgeRoute":
        """Deserialize from dictionary."""
        return cls(
            source_chain=data["source_chain"],
            destination_chain=data["destination_chain"],
            token=data["token"],
            estimated_time_seconds=data["estimated_time_seconds"],
            fee_usd=Decimal(str(data.get("fee_usd", "0"))),
            fee_native=Decimal(str(data.get("fee_native", "0"))),
            security_score=data.get("security_score", 95),
            is_express=data.get("is_express", False),
        )
