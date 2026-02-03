"""
Aave HTTP Router.

Provides REST API endpoints for Aave V3 lending operations.
"""

from decimal import Decimal
from typing import Literal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.domain.exceptions.aave import (
    AaveAPIError,
    AaveError,
    InvalidAddressError,
    MarketNotFoundError,
    PositionNotFoundError,
    UnsupportedChainError,
)
from app.domain.ports.aave_gateway import AaveGateway
from app.domain.value_objects.lending.health_factor import HealthFactor
from app.presentation.http.controllers.defi.aave_schemas import (
    AaveMarketResponse,
    AaveMarketsResponse,
    AavePositionResponse,
    AvailableToBorrowResponse,
    CalculateHealthFactorRequest,
    HealthFactorResponse,
    ProtocolStatsResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
    ValidationErrorTranslator,
)


def create_aave_router() -> APIRouter:
    """Create and configure the Aave router."""
    router = ErrorAwareRouter(prefix="/aave", tags=["DeFi", "Lending"])

    # Common error map
    aave_error_map = {
        MarketNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="market"),
            on_error=log_info,
        ),
        PositionNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="position"),
            on_error=log_info,
        ),
        InvalidAddressError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=ValidationErrorTranslator(),
            on_error=log_info,
        ),
        UnsupportedChainError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        AaveAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        AaveError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/markets",
        summary="Get Aave V3 Markets",
        description="Get lending markets with supply/borrow rates and utilization",
        response_model=AaveMarketsResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_markets(
        gateway: FromDishka[AaveGateway],
        asset: str | None = Query(default=None, description="Filter by asset symbol"),
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
        sort_by: Literal["supply_apy", "borrow_apy", "tvl", "utilization"] = Query(
            default="supply_apy", description="Sort field"
        ),
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    ) -> AaveMarketsResponse:
        """Get Aave V3 markets."""
        markets = await gateway.get_markets(asset=asset, chain=chain)

        # Sort markets
        if sort_by == "supply_apy":
            markets.sort(key=lambda m: m.supply_apy, reverse=True)
        elif sort_by == "borrow_apy":
            markets.sort(key=lambda m: m.borrow_apy_variable, reverse=True)
        elif sort_by == "tvl":
            markets.sort(key=lambda m: m.total_supplied_usd, reverse=True)
        elif sort_by == "utilization":
            markets.sort(key=lambda m: m.utilization_rate, reverse=True)

        # Apply limit
        markets = markets[:limit]

        # Calculate totals
        total_supplied = sum(m.total_supplied_usd for m in markets)
        total_borrowed = sum(m.total_borrowed_usd for m in markets)

        return AaveMarketsResponse(
            markets=[AaveMarketResponse.from_domain(m) for m in markets],
            count=len(markets),
            chain=chain,
            total_supplied_usd=str(total_supplied),
            total_borrowed_usd=str(total_borrowed),
        )

    @router.get(
        "/markets/{asset}",
        summary="Get Market Details",
        description="Get detailed market information for a specific asset",
        response_model=AaveMarketResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_market_details(
        asset: str,
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> AaveMarketResponse:
        """Get market details for an asset."""
        market = await gateway.get_market_details(asset=asset, chain=chain)
        return AaveMarketResponse.from_domain(market)

    @router.get(
        "/positions/{user_address}",
        summary="Get User Position",
        description="Get user's complete lending/borrowing position with health metrics",
        response_model=AavePositionResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_user_position(
        user_address: str,
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> AavePositionResponse:
        """Get user's Aave position."""
        position = await gateway.get_user_position(address=user_address, chain=chain)
        return AavePositionResponse.from_domain(position)

    @router.get(
        "/positions/{user_address}/health",
        summary="Get Health Factor",
        description="Get user's health factor with risk analysis",
        response_model=HealthFactorResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_health_factor(
        user_address: str,
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> HealthFactorResponse:
        """Get user's health factor."""
        health_factor = await gateway.get_health_factor(
            address=user_address, chain=chain
        )
        return HealthFactorResponse.from_domain(health_factor)

    @router.get(
        "/positions/{user_address}/borrow-capacity/{asset}",
        summary="Get Available to Borrow",
        description="Get maximum amount user can borrow of an asset",
        response_model=AvailableToBorrowResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_available_to_borrow(
        user_address: str,
        asset: str,
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> AvailableToBorrowResponse:
        """Get maximum borrowable amount for an asset."""
        max_borrow = await gateway.get_available_to_borrow(
            address=user_address, asset=asset, chain=chain
        )

        # Get additional context
        position = await gateway.get_user_position(address=user_address, chain=chain)
        market = await gateway.get_market_details(asset=asset, chain=chain)

        max_borrow_usd = max_borrow * market.price_usd

        # Calculate HF after max borrow
        new_debt = position.total_debt_usd + max_borrow_usd
        if new_debt > 0:
            new_hf = (position.total_collateral_usd * Decimal("0.825")) / new_debt
        else:
            new_hf = Decimal("inf")

        hf_str = str(new_hf)
        if "inf" in hf_str.lower():
            hf_str = "∞"

        return AvailableToBorrowResponse(
            asset=asset,
            chain=chain,
            max_borrowable=str(max_borrow),
            max_borrowable_usd=str(max_borrow_usd),
            current_debt=str(position.total_debt_usd),
            collateral_usd=str(position.total_collateral_usd),
            health_factor_after_max_borrow=hf_str,
        )

    @router.get(
        "/stats",
        summary="Get Protocol Stats",
        description="Get protocol-wide statistics for Aave V3",
        response_model=ProtocolStatsResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_protocol_stats(
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> ProtocolStatsResponse:
        """Get protocol statistics."""
        stats = await gateway.get_protocol_stats(chain=chain)
        return ProtocolStatsResponse(
            chain=stats.get("chain", chain),
            total_tvl_usd=str(stats.get("total_tvl_usd", 0)),
            total_supplied_usd=str(stats.get("total_supplied_usd", 0)),
            total_borrowed_usd=str(stats.get("total_borrowed_usd", 0)),
            num_markets=stats.get("num_markets", 0),
        )

    @router.post(
        "/calculate/health-factor",
        summary="Calculate Health Factor",
        description="Calculate health factor from collateral and debt amounts",
        response_model=HealthFactorResponse,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def calculate_health_factor(
        request: CalculateHealthFactorRequest,
        gateway: FromDishka[AaveGateway],
    ) -> HealthFactorResponse:
        """Calculate health factor."""
        health_factor = await gateway.calculate_health_factor(
            collateral_usd=Decimal(str(request.collateral_usd)),
            debt_usd=Decimal(str(request.debt_usd)),
            liquidation_threshold=Decimal(str(request.liquidation_threshold)),
        )
        return HealthFactorResponse.from_domain(health_factor)

    @router.get(
        "/rates/{asset}",
        summary="Get Asset Rates",
        description="Get supply and borrow rates for an asset",
        response_model=dict,
        error_map=aave_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_asset_rates(
        asset: str,
        gateway: FromDishka[AaveGateway],
        chain: Literal[
            "ethereum", "polygon", "arbitrum", "optimism", "avalanche", "base"
        ] = Query(default="ethereum", description="Blockchain"),
    ) -> dict:
        """Get supply and borrow rates for an asset."""
        supply_apy = await gateway.get_supply_apy(asset=asset, chain=chain)
        borrow_apy_variable = await gateway.get_borrow_apy(
            asset=asset, chain=chain, rate_type="variable"
        )
        borrow_apy_stable = await gateway.get_borrow_apy(
            asset=asset, chain=chain, rate_type="stable"
        )
        liquidation_threshold = await gateway.get_liquidation_threshold(
            asset=asset, chain=chain
        )

        return {
            "asset": asset,
            "chain": chain,
            "supply_apy": str(supply_apy),
            "borrow_apy_variable": str(borrow_apy_variable),
            "borrow_apy_stable": str(borrow_apy_stable),
            "liquidation_threshold": str(liquidation_threshold),
        }

    return router
