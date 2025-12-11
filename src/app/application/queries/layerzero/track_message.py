"""
TrackMessage Query.

Application query for tracking cross-chain message status.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.entities.cross_chain.lz_message import LZMessage
from app.domain.exceptions.layerzero import MessageNotFoundError
from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.message_status import MessageStatus


@dataclass
class TrackMessageRequest:
    """Request parameters for TrackMessage query."""

    tx_hash: str


@dataclass
class MessageTrackingResponse:
    """Response for message tracking."""

    message: LZMessage
    progress_pct: int
    estimated_completion: datetime | None = None


class TrackMessage:
    """
    Query to track cross-chain message status.

    Calculates progress and estimated completion time.
    """

    # Average delivery times by chain type (seconds)
    DEFAULT_DELIVERY_TIME = 300  # 5 minutes

    def __init__(self, gateway: LayerZeroGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: TrackMessageRequest) -> MessageTrackingResponse:
        """Execute query to track message."""
        message = await self._gateway.track_message(request.tx_hash)

        if not message:
            raise MessageNotFoundError(request.tx_hash)

        # Calculate progress
        progress = self._calculate_progress(message)

        # Estimate completion for in-flight messages
        estimated = None
        if message.status == MessageStatus.INFLIGHT:
            estimated = self._estimate_completion(message)

        return MessageTrackingResponse(
            message=message,
            progress_pct=progress,
            estimated_completion=estimated,
        )

    def _calculate_progress(self, message: LZMessage) -> int:
        """Calculate progress percentage based on status."""
        status_progress = {
            MessageStatus.INFLIGHT: 50,
            MessageStatus.DELIVERED: 100,
            MessageStatus.FAILED: 0,
            MessageStatus.BLOCKED: 25,
        }
        return status_progress.get(message.status, 0)

    def _estimate_completion(self, message: LZMessage) -> datetime:
        """Estimate completion time for in-flight messages."""
        # Base estimate on creation time
        return message.created_at + timedelta(seconds=self.DEFAULT_DELIVERY_TIME)
