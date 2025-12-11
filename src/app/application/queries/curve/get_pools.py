"""
GetPools Query.

Application query for retrieving and filtering Curve pools.
"""

from dataclasses import dataclass
from typing import Literal

from app.domain.entities.curve.pool import Pool
from app.domain.ports.curve_gateway import CurveGateway


@dataclass
class GetPoolsRequest:
    """Request parameters for GetPools query."""

    chain: str = "ethereum"
    sort_by: Literal["tvl", "apy", "volume"] = "tvl"
    limit: int = 50
    min_tvl: float | None = None  # Filter pools with TVL below this


class GetPools:
    """
    Query to get Curve pools with sorting and filtering.

    This interactor encapsulates the business logic for pool listing,
    including sorting by various metrics and filtering by TVL.
    """

    def __init__(self, gateway: CurveGateway):
        """
        Initialize GetPools query.

        Args:
            gateway: CurveGateway port for data access
        """
        self._gateway = gateway

    async def execute(self, request: GetPoolsRequest) -> list[Pool]:
        """
        Execute the query to get pools.

        Args:
            request: Query parameters

        Returns:
            List of Pool entities sorted and filtered
        """
        # Get all pools from gateway
        pools = await self._gateway.get_pools(chain=request.chain)

        # Filter by minimum TVL if specified
        if request.min_tvl is not None:
            pools = [p for p in pools if float(p.tvl_usd) >= request.min_tvl]

        # Sort pools
        if request.sort_by == "tvl":
            pools.sort(key=lambda p: p.tvl_usd, reverse=True)
        elif request.sort_by == "apy":
            pools.sort(key=lambda p: p.apy, reverse=True)
        elif request.sort_by == "volume":
            pools.sort(key=lambda p: p.volume_24h_usd, reverse=True)

        # Apply limit
        return pools[: request.limit]
