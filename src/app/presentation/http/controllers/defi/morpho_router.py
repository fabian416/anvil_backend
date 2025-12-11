"""
Morpho HTTP Router.

Provides REST API endpoints for Morpho lending vault operations.
"""

from typing import Literal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.queries.morpho.compare_yields import (
    CompareYields,
    CompareYieldsRequest,
)
from app.application.queries.morpho.get_markets import GetMarkets, GetMarketsRequest
from app.application.queries.morpho.get_user_positions import (
    GetUserPositions,
    GetUserPositionsRequest,
)
from app.application.queries.morpho.get_vault_apy import GetVaultAPY, GetVaultAPYRequest
from app.application.queries.morpho.get_vault_details import (
    GetVaultDetails,
    GetVaultDetailsRequest,
)
from app.application.queries.morpho.get_vaults import GetVaults, GetVaultsRequest
from app.domain.exceptions.morpho import (
    InvalidVaultAddressError,
    MorphoAPIError,
    MorphoError,
    VaultNotFoundError,
)
from app.presentation.http.controllers.defi.morpho_schemas import (
    MarketResponse,
    MarketsResponse,
    PositionResponse,
    PositionsSummaryResponse,
    UserPositionsResponse,
    VaultAPYResponse,
    VaultOpportunityResponse,
    VaultResponse,
    VaultsResponse,
    YieldComparisonListResponse,
    YieldComparisonResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_morpho_router() -> APIRouter:
    """Create and configure the Morpho router."""
    router = ErrorAwareRouter(prefix="/morpho", tags=["DeFi", "Lending"])

    # Common error map
    morpho_error_map = {
        VaultNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="vault"),
            on_error=log_info,
        ),
        InvalidVaultAddressError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        MorphoAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        MorphoError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/vaults",
        summary="Get MetaMorpho Vaults",
        description="Get available lending vaults with APY and risk data",
        response_model=VaultsResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_vaults(
        query: FromDishka[GetVaults],
        asset: str | None = Query(default=None, description="Filter by asset"),
        risk_tier: str | None = Query(
            default=None, description="Filter by risk tier (low, medium, high, very_high)"
        ),
        min_apy: float | None = Query(default=None, description="Minimum APY filter"),
        sort_by: Literal["apy", "tvl", "risk"] = Query(
            default="apy", description="Sort field"
        ),
        chain: str = Query(default="ethereum", description="Blockchain"),
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    ) -> VaultsResponse:
        """Get MetaMorpho vaults."""
        request = GetVaultsRequest(
            asset=asset,
            risk_tier=risk_tier,
            min_apy=min_apy,
            sort_by=sort_by,
            chain=chain,
            limit=limit,
        )
        response = await query.execute(request)

        return VaultsResponse(
            vaults=[VaultResponse.from_domain(v) for v in response.vaults],
            top_opportunities=[
                VaultOpportunityResponse(
                    vault_address=o.vault_address,
                    vault_name=o.vault_name,
                    asset=o.asset,
                    apy=str(o.apy),
                    risk_tier=o.risk_tier.value,
                )
                for o in response.top_opportunities
            ],
            total_count=response.total_count,
        )

    @router.get(
        "/vaults/{vault_address}",
        summary="Get Vault Details",
        description="Get detailed vault information with market allocations",
        response_model=VaultResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_vault_details(
        vault_address: str,
        query: FromDishka[GetVaultDetails],
        chain: str = Query(default="ethereum", description="Blockchain"),
    ) -> VaultResponse:
        """Get vault details."""
        request = GetVaultDetailsRequest(vault_address=vault_address, chain=chain)
        vault = await query.execute(request)
        return VaultResponse.from_domain(vault)

    @router.get(
        "/vaults/{vault_address}/apy",
        summary="Get Vault APY",
        description="Get detailed APY breakdown with historical data",
        response_model=VaultAPYResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_vault_apy(
        vault_address: str,
        query: FromDishka[GetVaultAPY],
        chain: str = Query(default="ethereum", description="Blockchain"),
    ) -> VaultAPYResponse:
        """Get vault APY breakdown."""
        request = GetVaultAPYRequest(vault_address=vault_address, chain=chain)
        response = await query.execute(request)
        return VaultAPYResponse.from_domain(
            response.apy, fee_impact=str(response.fee_impact)
        )

    @router.get(
        "/markets",
        summary="Get Morpho Blue Markets",
        description="Get lending markets with rates and utilization",
        response_model=MarketsResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_markets(
        query: FromDishka[GetMarkets],
        collateral_asset: str | None = Query(
            default=None, description="Filter by collateral asset"
        ),
        loan_asset: str | None = Query(default=None, description="Filter by loan asset"),
        sort_by: Literal["supply_apy", "tvl", "utilization"] = Query(
            default="supply_apy", description="Sort field"
        ),
        chain: str = Query(default="ethereum", description="Blockchain"),
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    ) -> MarketsResponse:
        """Get Morpho Blue markets."""
        request = GetMarketsRequest(
            collateral_asset=collateral_asset,
            loan_asset=loan_asset,
            sort_by=sort_by,
            chain=chain,
            limit=limit,
        )
        markets = await query.execute(request)

        return MarketsResponse(
            markets=[MarketResponse.from_domain(m) for m in markets],
            count=len(markets),
        )

    @router.get(
        "/positions/{user_address}",
        summary="Get User Positions",
        description="Get user's vault positions with earnings",
        response_model=UserPositionsResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_positions(
        user_address: str,
        query: FromDishka[GetUserPositions],
        chain: str = Query(default="ethereum", description="Blockchain"),
    ) -> UserPositionsResponse:
        """Get user positions."""
        request = GetUserPositionsRequest(user_address=user_address, chain=chain)
        response = await query.execute(request)

        return UserPositionsResponse(
            positions=[PositionResponse.from_domain(p) for p in response.positions],
            summary=PositionsSummaryResponse(
                total_positions=response.summary.total_positions,
                total_deposited=str(response.summary.total_deposited),
                total_current_value=str(response.summary.total_current_value),
                total_earnings=str(response.summary.total_earnings),
                average_apy=str(response.summary.average_apy),
            ),
        )

    @router.get(
        "/compare",
        summary="Compare Yields",
        description="Compare yields across protocols for an asset",
        response_model=YieldComparisonListResponse,
        error_map=morpho_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def compare_yields(
        asset: str,
        query: FromDishka[CompareYields],
        chain: str = Query(default="ethereum", description="Blockchain"),
    ) -> YieldComparisonListResponse:
        """Compare yields across protocols."""
        request = CompareYieldsRequest(
            asset=asset,
            protocols=["morpho"],
            chain=chain,
        )
        response = await query.execute(request)

        comparisons = [
            YieldComparisonResponse(
                protocol=c.protocol,
                vault_name=c.vault_name,
                apy=str(c.apy),
                risk_tier=c.risk_tier.value,
                apy_advantage=str(c.apy_advantage),
            )
            for c in response.comparisons
        ]

        best = None
        if response.best_option:
            best = YieldComparisonResponse(
                protocol=response.best_option.protocol,
                vault_name=response.best_option.vault_name,
                apy=str(response.best_option.apy),
                risk_tier=response.best_option.risk_tier.value,
                apy_advantage=str(response.best_option.apy_advantage),
            )

        return YieldComparisonListResponse(
            asset=response.asset,
            comparisons=comparisons,
            best_option=best,
        )

    return router
