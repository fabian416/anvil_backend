"""
LayerZero Message Entity.

Represents a cross-chain message tracked by LayerZero.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.value_objects.cross_chain.message_status import MessageStatus


@dataclass
class LZMessage:
    """
    LayerZero message entity.

    Represents a cross-chain message with tracking information.
    """

    src_tx_hash: str
    src_chain_id: int
    dst_chain_id: int
    status: MessageStatus
    src_address: str
    dst_address: str
    dst_tx_hash: str | None
    message_type: str  # "oft", "onft", "generic"
    created_at: datetime
    completed_at: datetime | None = None
    nonce: int | None = None

    @property
    def is_delivered(self) -> bool:
        """Check if message is delivered."""
        return self.status == MessageStatus.DELIVERED

    @property
    def is_pending(self) -> bool:
        """Check if message is in transit."""
        return self.status == MessageStatus.INFLIGHT

    @property
    def duration_seconds(self) -> int | None:
        """Get delivery duration in seconds."""
        if self.completed_at and self.created_at:
            return int((self.completed_at - self.created_at).total_seconds())
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "src_tx_hash": self.src_tx_hash,
            "src_chain_id": self.src_chain_id,
            "dst_chain_id": self.dst_chain_id,
            "status": self.status.value,
            "src_address": self.src_address,
            "dst_address": self.dst_address,
            "dst_tx_hash": self.dst_tx_hash,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "nonce": self.nonce,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LZMessage":
        """Deserialize from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            src_tx_hash=data["src_tx_hash"],
            src_chain_id=data["src_chain_id"],
            dst_chain_id=data["dst_chain_id"],
            status=MessageStatus(data["status"]),
            src_address=data["src_address"],
            dst_address=data["dst_address"],
            dst_tx_hash=data.get("dst_tx_hash"),
            message_type=data.get("message_type", "generic"),
            created_at=created_at or datetime.now(),
            completed_at=completed_at,
            nonce=data.get("nonce"),
        )
