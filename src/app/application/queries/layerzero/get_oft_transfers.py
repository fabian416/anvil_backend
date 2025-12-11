"""
GetOFTTransfers Query.

Application query for retrieving OFT transfer history.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.cross_chain.oft_transfer import OFTTransfer
from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.message_status import MessageStatus


@dataclass
class GetOFTTransfersRequest:
    """Request parameters for GetOFTTransfers query."""

    address: str
    limit: int = 50


@dataclass
class OFTTransfersSummary:
    """Summary of OFT transfers."""

    total_transfers: int
    pending_count: int
    completed_count: int
    total_volume: Decimal


@dataclass
class OFTTransfersResponse:
    """Response for OFT transfers query."""

    transfers: list[OFTTransfer]
    summary: OFTTransfersSummary


class GetOFTTransfers:
    """
    Query to get OFT transfers for an address.

    Returns transfers with volume summary.
    """

    def __init__(self, gateway: LayerZeroGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetOFTTransfersRequest) -> OFTTransfersResponse:
        """Execute query to get OFT transfers."""
        transfers = await self._gateway.get_oft_transfers(
            address=request.address,
            limit=request.limit,
        )

        # Sort by timestamp (newest first)
        transfers.sort(key=lambda t: t.timestamp, reverse=True)

        # Calculate summary
        summary = self._calculate_summary(transfers)

        return OFTTransfersResponse(
            transfers=transfers,
            summary=summary,
        )

    def _calculate_summary(self, transfers: list[OFTTransfer]) -> OFTTransfersSummary:
        """Calculate transfer summary."""
        if not transfers:
            return OFTTransfersSummary(
                total_transfers=0,
                pending_count=0,
                completed_count=0,
                total_volume=Decimal("0"),
            )

        pending = sum(1 for t in transfers if t.status == MessageStatus.INFLIGHT)
        completed = sum(1 for t in transfers if t.status == MessageStatus.DELIVERED)
        volume = sum(t.amount for t in transfers)

        return OFTTransfersSummary(
            total_transfers=len(transfers),
            pending_count=pending,
            completed_count=completed,
            total_volume=volume,
        )
