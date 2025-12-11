"""
Hyperliquid HTTP Router.

Provides REST API endpoints for perpetual futures operations.
"""

from decimal import Decimal
from typing import Literal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.commands.perpetual.calculate_risk import (
    CalculateRisk,
    CalculateRiskRequest,
)
from app.application.queries.perpetual.get_funding_rates import (
    GetFundingRates,
    GetFundingRatesRequest,
    FundingOpportunity,
)
from app.application.queries.perpetual.get_liquidations import (
    GetLiquidations,
    GetLiquidationsRequest,
)
from app.application.queries.perpetual.get_markets import GetMarkets, GetMarketsRequest
from app.application.queries.perpetual.get_order_book import (
    GetOrderBook,
    GetOrderBookRequest,
)
from app.application.queries.perpetual.get_positions import (
    GetPositions,
    GetPositionsRequest,
)
from app.domain.exceptions.perpetual import (
    HyperliquidAPIError,
    InvalidAddressError,
    PerpetualError,
    SymbolNotFoundError,
)
from app.presentation.http.controllers.defi.hyperliquid_schemas import (
    CalculateRiskRequestModel,
    FundingOpportunityResponse,
    FundingRateResponse,
    FundingRatesResponse,
    LiquidationResponse,
    LiquidationsResponse,
    LiquidationSummaryResponse,
    MarketsResponse,
    OrderBookResponse,
    PositionResponse,
    PositionsResponse,
    PositionsSummaryResponse,
    RiskMetricsResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_hyperliquid_router() -> APIRouter:
    """Create and configure the Hyperliquid router."""
    router = ErrorAwareRouter(prefix="/hyperliquid", tags=["DeFi", "Perpetuals"])

    # Common error map
    perp_error_map = {
        SymbolNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="symbol"),
            on_error=log_info,
        ),
        InvalidAddressError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        HyperliquidAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        PerpetualError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/markets",
        summary="Get Perpetual Markets",
        description="Get all perpetual markets with pricing and funding data",
        response_model=MarketsResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_markets(
        query: FromDishka[GetMarkets],
        sort_by: Literal["volume", "open_interest", "funding", "price_change"] = Query(
            default="volume", description="Sort field"
        ),
        limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    ) -> MarketsResponse:
        """Get all perpetual markets."""
        request = GetMarketsRequest(sort_by=sort_by, limit=limit)
        markets = await query.execute(request)
        return MarketsResponse.from_domain(markets)

    @router.get(
        "/markets/{symbol}/orderbook",
        summary="Get Order Book",
        description="Get real-time order book with spread analysis",
        response_model=OrderBookResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_order_book(
        symbol: str,
        query: FromDishka[GetOrderBook],
        depth: int = Query(default=20, ge=1, le=100, description="Book depth"),
    ) -> OrderBookResponse:
        """Get order book for a symbol."""
        request = GetOrderBookRequest(symbol=symbol, depth=depth)
        response = await query.execute(request)
        return OrderBookResponse.from_domain(
            response.order_book, warnings=response.warnings
        )

    @router.get(
        "/funding",
        summary="Get Funding Rates",
        description="Get funding rates with arbitrage opportunities",
        response_model=FundingRatesResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_funding_rates(
        query: FromDishka[GetFundingRates],
        sort_by: Literal["absolute", "positive", "negative"] = Query(
            default="absolute", description="Sort by funding rate type"
        ),
        min_rate: float | None = Query(
            default=None, description="Minimum absolute rate filter"
        ),
    ) -> FundingRatesResponse:
        """Get all funding rates with opportunities."""
        request = GetFundingRatesRequest(sort_by=sort_by, min_rate=min_rate)
        response = await query.execute(request)

        return FundingRatesResponse(
            rates=[FundingRateResponse.from_domain(r) for r in response.rates],
            opportunities=[
                FundingOpportunityResponse(
                    symbol=o.symbol,
                    rate=str(o.rate),
                    annualized_return=str(o.annualized_return),
                    direction=o.direction,
                    strategy=o.strategy,
                )
                for o in response.opportunities
            ],
            count=len(response.rates),
        )

    @router.get(
        "/liquidations",
        summary="Get Liquidations",
        description="Get recent liquidations with market stress analysis",
        response_model=LiquidationsResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_liquidations(
        query: FromDishka[GetLiquidations],
        symbol: str | None = Query(default=None, description="Filter by symbol"),
        hours: int = Query(default=24, ge=1, le=168, description="Lookback hours"),
        sort_by: Literal["size", "time"] = Query(default="time", description="Sort by"),
    ) -> LiquidationsResponse:
        """Get recent liquidations."""
        request = GetLiquidationsRequest(symbol=symbol, hours=hours, sort_by=sort_by)
        response = await query.execute(request)

        return LiquidationsResponse(
            liquidations=[
                LiquidationResponse.from_domain(l) for l in response.liquidations
            ],
            summary=LiquidationSummaryResponse(
                total_count=response.summary.total_count,
                total_volume_usd=str(response.summary.total_volume_usd),
                long_volume_usd=str(response.summary.long_volume_usd),
                short_volume_usd=str(response.summary.short_volume_usd),
                largest_liquidation_usd=str(response.summary.largest_liquidation_usd),
                is_cascade=response.summary.is_cascade,
            ),
            warnings=response.warnings,
        )

    @router.get(
        "/positions/{address}",
        summary="Get User Positions",
        description="Get user's open positions with risk analysis",
        response_model=PositionsResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_positions(
        address: str,
        query: FromDishka[GetPositions],
    ) -> PositionsResponse:
        """Get user positions by wallet address."""
        request = GetPositionsRequest(address=address)
        response = await query.execute(request)

        return PositionsResponse(
            positions=[PositionResponse.from_domain(p) for p in response.positions],
            summary=PositionsSummaryResponse(
                total_positions=response.summary.total_positions,
                total_unrealized_pnl=str(response.summary.total_unrealized_pnl),
                total_position_value=str(response.summary.total_position_value),
                long_exposure=str(response.summary.long_exposure),
                short_exposure=str(response.summary.short_exposure),
            ),
            warnings=response.warnings,
        )

    @router.post(
        "/risk/calculate",
        summary="Calculate Position Risk",
        description="Calculate risk metrics for a potential position",
        response_model=RiskMetricsResponse,
        error_map=perp_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def calculate_risk(
        request_body: CalculateRiskRequestModel,
        command: FromDishka[CalculateRisk],
    ) -> RiskMetricsResponse:
        """Calculate liquidation price and risk metrics."""
        request = CalculateRiskRequest(
            entry_price=Decimal(request_body.entry_price),
            size=Decimal(request_body.size),
            leverage=Decimal(request_body.leverage),
            side=request_body.side,
            account_balance=(
                Decimal(request_body.account_balance)
                if request_body.account_balance
                else None
            ),
        )
        metrics = await command.execute(request)
        return RiskMetricsResponse.from_domain(metrics)

    return router
