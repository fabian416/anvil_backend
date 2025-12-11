"""
Curve Finance HTTP Router.

Provides REST API endpoints for Curve Finance operations.
"""

from typing import Literal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.commands.curve.get_swap_quote import GetSwapQuote, SwapQuoteRequest
from app.application.queries.curve.get_gauges import GetGauges, GetGaugesRequest
from app.application.queries.curve.get_pool_apy import GetPoolAPY, GetPoolAPYRequest
from app.application.queries.curve.get_pools import GetPools, GetPoolsRequest
from app.application.queries.curve.get_tvl import GetTVL, GetTVLRequest
from app.domain.exceptions.curve import (
    CurveAPIError,
    CurveError,
    InvalidTokenError,
    NoRouteFoundError,
    PoolNotFoundError,
)
from app.presentation.http.controllers.defi.curve_schemas import (
    GaugesResponse,
    PoolAPYResponse,
    PoolResponse,
    PoolsResponse,
    SwapQuoteRequestModel,
    SwapQuoteResponse,
    TVLResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_curve_router() -> APIRouter:
    """Create and configure the Curve Finance router."""
    router = ErrorAwareRouter(prefix="/curve", tags=["DeFi", "Curve"])

    # Common error map for Curve operations
    curve_error_map = {
        PoolNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="pool"),
            on_error=log_info,
        ),
        InvalidTokenError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        NoRouteFoundError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        CurveAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        CurveError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/pools",
        summary="Get Curve Pools",
        description="Get all Curve pools with optional sorting and filtering",
        response_model=PoolsResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_pools(
        query: FromDishka[GetPools],
        chain: str = Query(default="ethereum", description="Blockchain name"),
        sort_by: Literal["tvl", "apy", "volume"] = Query(
            default="tvl", description="Sort field"
        ),
        limit: int = Query(default=50, ge=1, le=200, description="Max results"),
        min_tvl: float | None = Query(
            default=None, description="Minimum TVL filter (USD)"
        ),
    ) -> PoolsResponse:
        """Get all Curve pools sorted by TVL, APY, or volume."""
        request = GetPoolsRequest(
            chain=chain,
            sort_by=sort_by,
            limit=limit,
            min_tvl=min_tvl,
        )
        pools = await query.execute(request)
        return PoolsResponse.from_domain(pools, chain)

    @router.get(
        "/pools/{pool_address}",
        summary="Get Pool Details",
        description="Get detailed information for a specific Curve pool",
        response_model=PoolResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_pool(
        pool_address: str,
        query: FromDishka[GetPools],
        chain: str = Query(default="ethereum", description="Blockchain name"),
    ) -> PoolResponse:
        """Get a specific pool by address."""
        # Use GetPools and filter to find the specific pool
        request = GetPoolsRequest(chain=chain, limit=1000)
        pools = await query.execute(request)

        for pool in pools:
            if pool.id.lower() == pool_address.lower():
                return PoolResponse.from_domain(pool)

        raise PoolNotFoundError(pool_address, chain)

    @router.get(
        "/pools/{pool_address}/apy",
        summary="Get Pool APY Breakdown",
        description="Get detailed APY breakdown for a Curve pool",
        response_model=PoolAPYResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_pool_apy(
        pool_address: str,
        query: FromDishka[GetPoolAPY],
        chain: str = Query(default="ethereum", description="Blockchain name"),
    ) -> PoolAPYResponse:
        """Get APY breakdown including base fees, CRV rewards, and extra rewards."""
        request = GetPoolAPYRequest(pool_address=pool_address, chain=chain)
        apy = await query.execute(request)
        return PoolAPYResponse.from_domain(apy)

    @router.post(
        "/quote",
        summary="Get Swap Quote",
        description="Get a swap quote for token exchange with risk analysis",
        response_model=SwapQuoteResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_swap_quote(
        request_body: SwapQuoteRequestModel,
        command: FromDishka[GetSwapQuote],
    ) -> SwapQuoteResponse:
        """Get swap quote with price impact and risk warnings."""
        request = SwapQuoteRequest(
            from_token=request_body.from_token,
            to_token=request_body.to_token,
            amount=request_body.amount,
            chain=request_body.chain,
        )
        quote = await command.execute(request)
        return SwapQuoteResponse.from_domain(quote)

    @router.get(
        "/gauges",
        summary="Get Curve Gauges",
        description="Get all Curve gauges with reward data",
        response_model=GaugesResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_gauges(
        query: FromDishka[GetGauges],
        chain: str = Query(default="ethereum", description="Blockchain name"),
        sort_by: Literal["apy", "weight", "emissions"] = Query(
            default="apy", description="Sort field"
        ),
        min_apy: float | None = Query(default=None, description="Minimum APY filter"),
    ) -> GaugesResponse:
        """Get all gauges sorted by APY, weight, or emissions."""
        request = GetGaugesRequest(chain=chain, sort_by=sort_by, min_apy=min_apy)
        gauges = await query.execute(request)
        return GaugesResponse.from_domain(gauges, chain)

    @router.get(
        "/tvl",
        summary="Get Curve TVL",
        description="Get total value locked data for Curve",
        response_model=TVLResponse,
        error_map=curve_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_tvl(
        query: FromDishka[GetTVL],
        chain: str = Query(default="ethereum", description="Blockchain name"),
    ) -> TVLResponse:
        """Get TVL data including total value and pool count."""
        request = GetTVLRequest(chain=chain)
        tvl = await query.execute(request)
        return TVLResponse.from_domain(tvl)

    return router
