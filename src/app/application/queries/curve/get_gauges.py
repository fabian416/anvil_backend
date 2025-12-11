"""
GetGauges Query.

Application query for retrieving Curve gauge data.
"""

from dataclasses import dataclass
from typing import Literal

from app.domain.entities.curve.gauge import Gauge
from app.domain.ports.curve_gateway import CurveGateway


@dataclass
class GetGaugesRequest:
    """Request parameters for GetGauges query."""

    chain: str = "ethereum"
    sort_by: Literal["apy", "weight", "emissions"] = "apy"
    min_apy: float | None = None  # Filter gauges with APY below this


class GetGauges:
    """
    Query to get Curve gauges with sorting and filtering.

    Gauges control CRV emissions to liquidity providers.
    This interactor retrieves gauge data sorted by various metrics.
    """

    def __init__(self, gateway: CurveGateway):
        """
        Initialize GetGauges query.

        Args:
            gateway: CurveGateway port for data access
        """
        self._gateway = gateway

    async def execute(self, request: GetGaugesRequest) -> list[Gauge]:
        """
        Execute the query to get gauges.

        Args:
            request: Query parameters

        Returns:
            List of Gauge entities sorted and filtered
        """
        # Get all gauges from gateway
        gauges = await self._gateway.get_gauges(chain=request.chain)

        # Filter by minimum APY if specified
        if request.min_apy is not None:
            gauges = [g for g in gauges if float(g.apy) >= request.min_apy]

        # Sort gauges
        if request.sort_by == "apy":
            gauges.sort(key=lambda g: g.apy, reverse=True)
        elif request.sort_by == "weight":
            gauges.sort(key=lambda g: g.relative_weight, reverse=True)
        elif request.sort_by == "emissions":
            gauges.sort(key=lambda g: g.crv_emissions_per_day, reverse=True)

        return gauges
