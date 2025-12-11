"""
GetFundingRates Query.

Application query for retrieving funding rates with opportunity analysis.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.domain.ports.perpetual_gateway import PerpetualGateway
from app.domain.value_objects.perpetual.funding_rate import FundingRate


# Threshold for funding arbitrage opportunity (50% annualized)
OPPORTUNITY_THRESHOLD = Decimal("50")


@dataclass
class FundingOpportunity:
    """Identified funding rate opportunity."""

    symbol: str
    rate: Decimal
    annualized_return: Decimal
    direction: str  # "short" (collect positive funding) or "long" (collect negative)
    strategy: str


@dataclass
class GetFundingRatesRequest:
    """Request parameters for GetFundingRates query."""

    sort_by: Literal["absolute", "positive", "negative"] = "absolute"
    min_rate: float | None = None


@dataclass
class FundingRatesResponse:
    """Response for funding rates query with opportunities."""

    rates: list[FundingRate]
    opportunities: list[FundingOpportunity] = field(default_factory=list)


class GetFundingRates:
    """
    Query to get funding rates with arbitrage opportunity identification.

    Identifies markets where funding rate is high enough for arbitrage.
    """

    def __init__(self, gateway: PerpetualGateway):
        """Initialize query."""
        self._gateway = gateway

    async def execute(self, request: GetFundingRatesRequest) -> FundingRatesResponse:
        """Execute query to get funding rates."""
        rates = await self._gateway.get_funding_rates()

        # Filter by minimum rate
        if request.min_rate is not None:
            min_rate = Decimal(str(request.min_rate))
            rates = [r for r in rates if abs(r.rate) >= min_rate]

        # Sort
        if request.sort_by == "absolute":
            rates.sort(key=lambda r: abs(r.rate), reverse=True)
        elif request.sort_by == "positive":
            rates = [r for r in rates if r.rate > 0]
            rates.sort(key=lambda r: r.rate, reverse=True)
        elif request.sort_by == "negative":
            rates = [r for r in rates if r.rate < 0]
            rates.sort(key=lambda r: r.rate)

        # Identify opportunities
        opportunities = self._identify_opportunities(rates)

        return FundingRatesResponse(
            rates=rates,
            opportunities=opportunities,
        )

    def _identify_opportunities(
        self, rates: list[FundingRate]
    ) -> list[FundingOpportunity]:
        """Identify funding rate arbitrage opportunities."""
        opportunities = []

        for rate in rates:
            abs_annualized = abs(rate.annualized_rate)

            if abs_annualized >= OPPORTUNITY_THRESHOLD:
                if rate.rate > 0:
                    # Positive funding: shorts collect from longs
                    direction = "short"
                    strategy = (
                        f"Short {rate.symbol} perp + Long spot to collect "
                        f"{abs_annualized:.1f}% APR funding"
                    )
                else:
                    # Negative funding: longs collect from shorts
                    direction = "long"
                    strategy = (
                        f"Long {rate.symbol} perp + Short spot to collect "
                        f"{abs_annualized:.1f}% APR funding"
                    )

                opportunities.append(
                    FundingOpportunity(
                        symbol=rate.symbol,
                        rate=rate.rate,
                        annualized_return=abs_annualized,
                        direction=direction,
                        strategy=strategy,
                    )
                )

        # Sort by annualized return
        opportunities.sort(key=lambda o: o.annualized_return, reverse=True)

        return opportunities
