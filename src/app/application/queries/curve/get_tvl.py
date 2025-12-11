"""
GetTVL Query.

Application query for retrieving Curve TVL data.
"""

from dataclasses import dataclass

from app.domain.ports.curve_gateway import CurveGateway
from app.domain.value_objects.curve.tvl_data import TVLData


@dataclass
class GetTVLRequest:
    """Request parameters for GetTVL query."""

    chain: str = "ethereum"


class GetTVL:
    """
    Query to get Curve TVL data for a chain.

    Returns total value locked and pool count metrics.
    """

    def __init__(self, gateway: CurveGateway):
        """
        Initialize GetTVL query.

        Args:
            gateway: CurveGateway port for data access
        """
        self._gateway = gateway

    async def execute(self, request: GetTVLRequest) -> TVLData:
        """
        Execute the query to get TVL data.

        Args:
            request: Query parameters

        Returns:
            TVLData value object with TVL metrics
        """
        return await self._gateway.get_tvl(chain=request.chain)
