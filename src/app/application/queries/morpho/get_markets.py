"""
GetMarkets Query.

Application query for retrieving Morpho Blue markets.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.domain.entities.lending.morpho_market import MorphoMarket
from app.domain.ports.morpho_gateway import MorphoGateway


@dataclass
class GetMarketsRequest:
    """Request parameters for GetMarkets query."""

    collateral_asset: str | None = None
    loan_asset: str | None = None
    sort_by: Literal["supply_apy", "tvl", "utilization"] = "supply_apy"
    chain: str = "ethereum"
    limit: int = 50


class GetMarkets:
    """
    Query to get Morpho Blue markets.

    Returns markets sorted by various metrics with optional filtering.
    """

    def __init__(self, gateway: MorphoGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetMarketsRequest) -> list[MorphoMarket]:
        """Execute query to get markets."""
        markets = await self._gateway.get_markets(chain=request.chain)

        # Filter by collateral asset
        if request.collateral_asset:
            markets = [
                m for m in markets
                if m.collateral_asset.upper() == request.collateral_asset.upper()
            ]

        # Filter by loan asset
        if request.loan_asset:
            markets = [
                m for m in markets
                if m.loan_asset.upper() == request.loan_asset.upper()
            ]

        # Sort
        if request.sort_by == "supply_apy":
            markets.sort(key=lambda m: m.supply_apy, reverse=True)
        elif request.sort_by == "tvl":
            markets.sort(key=lambda m: m.total_supply, reverse=True)
        elif request.sort_by == "utilization":
            markets.sort(key=lambda m: m.utilization, reverse=True)

        return markets[: request.limit]
