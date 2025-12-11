"""
OFT Transfer Entity.

Represents an Omnichain Fungible Token transfer.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.value_objects.cross_chain.message_status import MessageStatus


@dataclass
class OFTTransfer:
    """
    OFT transfer entity.

    Represents a cross-chain token transfer via LayerZero OFT.
    """

    tx_hash: str
    src_chain_id: int
    dst_chain_id: int
    token_address: str
    token_symbol: str
    amount: Decimal
    from_address: str
    to_address: str
    status: MessageStatus
    timestamp: datetime

    @property
    def is_complete(self) -> bool:
        """Check if transfer is complete."""
        return self.status == MessageStatus.DELIVERED

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tx_hash": self.tx_hash,
            "src_chain_id": self.src_chain_id,
            "dst_chain_id": self.dst_chain_id,
            "token_address": self.token_address,
            "token_symbol": self.token_symbol,
            "amount": str(self.amount),
            "from_address": self.from_address,
            "to_address": self.to_address,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OFTTransfer":
        """Deserialize from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            tx_hash=data["tx_hash"],
            src_chain_id=data["src_chain_id"],
            dst_chain_id=data["dst_chain_id"],
            token_address=data["token_address"],
            token_symbol=data.get("token_symbol", "OFT"),
            amount=Decimal(str(data.get("amount", "0"))),
            from_address=data["from_address"],
            to_address=data["to_address"],
            status=MessageStatus(data["status"]),
            timestamp=timestamp or datetime.now(),
        )
