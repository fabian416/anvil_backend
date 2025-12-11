"""
GetRoutes Query.

Application query for discovering bridge routes.
"""

from dataclasses import dataclass

from app.domain.ports.axelar_gateway import AxelarGateway
from app.domain.value_objects.bridge.bridge_route import BridgeRoute


@dataclass
class GetRoutesRequest:
    """Request parameters for GetRoutes query."""

    source_chain: str
    destination_chain: str
    token: str = "USDC"


class GetRoutes:
    """
    Query to get available bridge routes.

    Returns both standard and express route options.
    """

    def __init__(self, gateway: AxelarGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetRoutesRequest) -> list[BridgeRoute]:
        """Execute query to get routes."""
        routes = await self._gateway.get_routes(
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            token=request.token,
        )

        # Sort by fee (cheapest first)
        routes.sort(key=lambda r: r.fee_usd)

        return routes
