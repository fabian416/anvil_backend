"""
TrackTransfer Query.

Application query for tracking transfer status.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.entities.bridge.axelar_transfer import AxelarTransfer
from app.domain.exceptions.axelar import TransferNotFoundError
from app.domain.ports.axelar_gateway import AxelarGateway
from app.domain.value_objects.bridge.transfer_status import TransferStatus


@dataclass
class TrackTransferRequest:
    """Request parameters for TrackTransfer query."""

    tx_hash: str


@dataclass
class TransferTrackingResponse:
    """Response for transfer tracking query."""

    transfer: AxelarTransfer
    progress_pct: int
    next_step: str
    estimated_completion: datetime | None = None


class TrackTransfer:
    """
    Query to track transfer status.

    Returns transfer with progress and next step.
    """

    # Average transfer time (seconds)
    DEFAULT_TRANSFER_TIME = 900  # 15 minutes

    def __init__(self, gateway: AxelarGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: TrackTransferRequest) -> TransferTrackingResponse:
        """Execute query to track transfer."""
        transfer = await self._gateway.track_transfer(request.tx_hash)

        if not transfer:
            raise TransferNotFoundError(request.tx_hash)

        progress = self._calculate_progress(transfer)
        next_step = self._get_next_step(transfer)

        # Estimate completion for active transfers
        estimated = None
        if transfer.status not in (TransferStatus.EXECUTED, TransferStatus.FAILED):
            estimated = self._estimate_completion(transfer)

        return TransferTrackingResponse(
            transfer=transfer,
            progress_pct=progress,
            next_step=next_step,
            estimated_completion=estimated,
        )

    def _calculate_progress(self, transfer: AxelarTransfer) -> int:
        """Calculate progress percentage based on status."""
        status_progress = {
            TransferStatus.PENDING: 10,
            TransferStatus.CONFIRMED: 30,
            TransferStatus.EXECUTING: 70,
            TransferStatus.EXECUTED: 100,
            TransferStatus.FAILED: 0,
        }
        return status_progress.get(transfer.status, 0)

    def _get_next_step(self, transfer: AxelarTransfer) -> str:
        """Get human-readable next step."""
        next_steps = {
            TransferStatus.PENDING: "Waiting for source chain confirmation",
            TransferStatus.CONFIRMED: "Relaying to destination chain",
            TransferStatus.EXECUTING: "Executing on destination chain",
            TransferStatus.EXECUTED: "Transfer complete",
            TransferStatus.FAILED: "Transfer failed - check error message",
        }
        return next_steps.get(transfer.status, "Unknown status")

    def _estimate_completion(self, transfer: AxelarTransfer) -> datetime:
        """Estimate completion time."""
        # Calculate remaining time based on progress
        progress = self._calculate_progress(transfer)
        remaining_pct = 100 - progress
        remaining_time = (remaining_pct / 100) * self.DEFAULT_TRANSFER_TIME

        return datetime.now() + timedelta(seconds=remaining_time)
