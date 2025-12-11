"""
Axelar Transfer Entity.

Represents a cross-chain transfer via Axelar.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.domain.value_objects.bridge.transfer_status import TransferStatus


@dataclass
class AxelarTransfer:
    """
    Axelar transfer entity.

    Represents a cross-chain bridge transfer with tracking.
    """

    tx_hash: str
    source_chain: str
    destination_chain: str
    token: str
    amount: Decimal
    status: TransferStatus
    source_tx_hash: str | None
    destination_tx_hash: str | None
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    is_express: bool = False

    @property
    def is_complete(self) -> bool:
        """Check if transfer is complete."""
        return self.status == TransferStatus.EXECUTED

    @property
    def is_failed(self) -> bool:
        """Check if transfer failed."""
        return self.status == TransferStatus.FAILED

    @property
    def duration_seconds(self) -> int | None:
        """Get transfer duration in seconds."""
        if self.completed_at and self.created_at:
            return int((self.completed_at - self.created_at).total_seconds())
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tx_hash": self.tx_hash,
            "source_chain": self.source_chain,
            "destination_chain": self.destination_chain,
            "token": self.token,
            "amount": str(self.amount),
            "status": self.status.value,
            "source_tx_hash": self.source_tx_hash,
            "destination_tx_hash": self.destination_tx_hash,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "is_express": self.is_express,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AxelarTransfer":
        """Deserialize from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            tx_hash=data["tx_hash"],
            source_chain=data["source_chain"],
            destination_chain=data["destination_chain"],
            token=data["token"],
            amount=Decimal(str(data.get("amount", "0"))),
            status=TransferStatus(data["status"]),
            source_tx_hash=data.get("source_tx_hash"),
            destination_tx_hash=data.get("destination_tx_hash"),
            created_at=created_at or datetime.now(),
            completed_at=completed_at,
            error_message=data.get("error_message"),
            is_express=data.get("is_express", False),
        )
