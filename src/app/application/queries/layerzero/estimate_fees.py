"""
EstimateFees Query.

Application query for estimating cross-chain message fees.
"""

from dataclasses import dataclass

from app.domain.ports.layerzero_gateway import LayerZeroGateway
from app.domain.value_objects.cross_chain.message_fee import MessageFee


@dataclass
class EstimateFeesRequest:
    """Request parameters for EstimateFees query."""

    source_chain: str
    destination_chain: str
    payload_size: int = 100


class EstimateFees:
    """
    Query to estimate cross-chain message fees.

    Returns fee breakdown in native and USD.
    """

    def __init__(self, gateway: LayerZeroGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: EstimateFeesRequest) -> MessageFee:
        """Execute query to estimate fees."""
        return await self._gateway.estimate_fees(
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            payload_size=request.payload_size,
        )
