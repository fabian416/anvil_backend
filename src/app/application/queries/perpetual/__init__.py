"""Perpetual futures application queries."""

from app.application.queries.perpetual.get_funding_rates import (
    GetFundingRates,
    GetFundingRatesRequest,
)
from app.application.queries.perpetual.get_liquidations import (
    GetLiquidations,
    GetLiquidationsRequest,
)
from app.application.queries.perpetual.get_markets import GetMarkets, GetMarketsRequest
from app.application.queries.perpetual.get_order_book import GetOrderBook, GetOrderBookRequest
from app.application.queries.perpetual.get_positions import GetPositions, GetPositionsRequest

__all__ = [
    "GetMarkets",
    "GetMarketsRequest",
    "GetOrderBook",
    "GetOrderBookRequest",
    "GetFundingRates",
    "GetFundingRatesRequest",
    "GetLiquidations",
    "GetLiquidationsRequest",
    "GetPositions",
    "GetPositionsRequest",
]
