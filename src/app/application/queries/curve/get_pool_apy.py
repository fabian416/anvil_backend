"""
GetPoolAPY Query.

Application query for retrieving detailed APY breakdown for a pool.
"""

from dataclasses import dataclass

from app.domain.ports.curve_gateway import CurveGateway
from app.domain.value_objects.curve.pool_apy import PoolAPY


@dataclass
class GetPoolAPYRequest:
    """Request parameters for GetPoolAPY query."""

    pool_address: str
    chain: str = "ethereum"


class GetPoolAPY:
    """
    Query to get detailed APY breakdown for a Curve pool.

    Returns the APY components including base fees, CRV rewards,
    and additional reward tokens.
    """

    def __init__(self, gateway: CurveGateway):
        """
        Initialize GetPoolAPY query.

        Args:
            gateway: CurveGateway port for data access
        """
        self._gateway = gateway

    async def execute(self, request: GetPoolAPYRequest) -> PoolAPY:
        """
        Execute the query to get pool APY.

        Args:
            request: Query parameters

        Returns:
            PoolAPY value object with APY breakdown

        Raises:
            PoolNotFoundError: If the pool doesn't exist
        """
        return await self._gateway.get_pool_apy(
            pool_address=request.pool_address,
            chain=request.chain,
        )
