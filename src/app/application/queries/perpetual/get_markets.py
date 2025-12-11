"""
GetMarkets Query.

Application query for retrieving perpetual markets.
"""

from dataclasses import dataclass
from typing import Literal

from app.domain.entities.perpetual.market import PerpMarket
from app.domain.ports.perpetual_gateway import PerpetualGateway


@dataclass
class GetMarketsRequest:
    """Request parameters for GetMarkets query."""

    sort_by: Literal["volume", "open_interest", "funding", "price_change"] = "volume"
    limit: int = 50


class GetMarkets:
    """
    Query to get perpetual markets.

    Returns markets sorted by various metrics.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetMarketsRequest) -> list[PerpMarket]:
        """Execute query to get markets."""
        markets = await self._gateway.get_markets()

        # Sort markets
        if request.sort_by == "volume":
            markets.sort(key=lambda m: m.volume_24h, reverse=True)
        elif request.sort_by == "open_interest":
            markets.sort(key=lambda m: m.open_interest, reverse=True)
        elif request.sort_by == "funding":
            markets.sort(key=lambda m: abs(m.funding_rate), reverse=True)
        elif request.sort_by == "price_change":
            markets.sort(key=lambda m: abs(m.price_change_24h), reverse=True)

        return markets[: request.limit]
