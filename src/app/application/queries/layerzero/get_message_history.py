"""
GetMessageHistory Query.

Application query for retrieving message history for an address.
"""

from dataclasses import dataclass

from app.domain.entities.cross_chain.lz_message import LZMessage
from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.message_status import MessageStatus


@dataclass
class GetMessageHistoryRequest:
    """Request parameters for GetMessageHistory query."""

    address: str
    limit: int = 50
    status_filter: str | None = None  # Filter by status


@dataclass
class MessageHistoryResponse:
    """Response for message history query."""

    messages: list[LZMessage]
    total_count: int
    pending_count: int
    delivered_count: int


class GetMessageHistory:
    """
    Query to get message history for an address.

    Returns filtered and sorted message list.
    """

    def __init__(self, gateway: LayerZeroGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(
        self, request: GetMessageHistoryRequest
    ) -> MessageHistoryResponse:
        """Execute query to get message history."""
        messages = await self._gateway.get_message_history(
            address=request.address,
            limit=request.limit,
        )

        # Filter by status if specified
        if request.status_filter:
            try:
                status = MessageStatus(request.status_filter.upper())
                messages = [m for m in messages if m.status == status]
            except ValueError:
                pass  # Invalid status, skip filter

        # Sort by creation time (newest first)
        messages.sort(key=lambda m: m.created_at, reverse=True)

        # Count by status
        pending = sum(1 for m in messages if m.status == MessageStatus.INFLIGHT)
        delivered = sum(1 for m in messages if m.status == MessageStatus.DELIVERED)

        return MessageHistoryResponse(
            messages=messages,
            total_count=len(messages),
            pending_count=pending,
            delivered_count=delivered,
        )
