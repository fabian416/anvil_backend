"""
Axelar HTTP Router.

Provides REST API endpoints for cross-chain bridging operations.
"""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.queries.axelar.estimate_transfer import (
    EstimateTransfer,
    EstimateTransferRequest,
)
from app.application.queries.axelar.get_chains import GetChains
from app.application.queries.axelar.get_routes import GetRoutes, GetRoutesRequest
from app.application.queries.axelar.get_tokens import GetTokens, GetTokensRequest
from app.application.queries.axelar.track_transfer import (
    TrackTransfer,
    TrackTransferRequest,
)
from app.domain.exceptions.axelar import (
    AxelarAPIError,
    AxelarError,
    TransferNotFoundError,
    UnsupportedChainError,
    UnsupportedTokenError,
)
from app.presentation.http.controllers.defi.axelar_schemas import (
    BridgeRouteResponse,
    ChainResponse,
    ChainsResponse,
    RoutesResponse,
    TokenResponse,
    TokensResponse,
    TransferEstimateResponse,
    TransferEstimateResponseModel,
    TransferResponse,
    TransferTrackingResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_axelar_router() -> APIRouter:
    """Create and configure the Axelar router."""
    router = ErrorAwareRouter(prefix="/axelar", tags=["DeFi", "Bridge"])

    # Common error map
    axelar_error_map = {
        TransferNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="transfer"),
            on_error=log_info,
        ),
        UnsupportedChainError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        UnsupportedTokenError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        AxelarAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        AxelarError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/routes",
        summary="Get Bridge Routes",
        description="Get available bridge routes including express options",
        response_model=RoutesResponse,
        error_map=axelar_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_routes(
        source_chain: str,
        destination_chain: str,
        query: FromDishka[GetRoutes],
        token: str = Query(default="USDC", description="Token to bridge"),
    ) -> RoutesResponse:
        """Get bridge routes."""
        request = GetRoutesRequest(
            source_chain=source_chain,
            destination_chain=destination_chain,
            token=token,
        )
        routes = await query.execute(request)

        return RoutesResponse(
            routes=[BridgeRouteResponse.from_domain(r) for r in routes],
            count=len(routes),
        )

    @router.get(
        "/estimate",
        summary="Estimate Transfer",
        description="Estimate transfer costs with standard and express options",
        response_model=TransferEstimateResponse,
        error_map=axelar_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def estimate_transfer(
        source_chain: str,
        destination_chain: str,
        token: str,
        amount: str,
        query: FromDishka[EstimateTransfer],
        include_express: bool = Query(
            default=True, description="Include express estimate"
        ),
    ) -> TransferEstimateResponse:
        """Estimate transfer costs."""
        request = EstimateTransferRequest(
            source_chain=source_chain,
            destination_chain=destination_chain,
            token=token,
            amount=amount,
            include_express=include_express,
        )
        response = await query.execute(request)

        return TransferEstimateResponse(
            standard=TransferEstimateResponseModel.from_domain(response.standard),
            express=TransferEstimateResponseModel.from_domain(response.express)
            if response.express
            else None,
            recommendation=response.recommendation,
        )

    @router.get(
        "/transfer/{tx_hash}",
        summary="Track Transfer",
        description="Track transfer status with progress and next steps",
        response_model=TransferTrackingResponse,
        error_map=axelar_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def track_transfer(
        tx_hash: str,
        query: FromDishka[TrackTransfer],
    ) -> TransferTrackingResponse:
        """Track transfer status."""
        request = TrackTransferRequest(tx_hash=tx_hash)
        response = await query.execute(request)

        return TransferTrackingResponse(
            transfer=TransferResponse.from_domain(response.transfer),
            progress_pct=response.progress_pct,
            next_step=response.next_step,
            estimated_completion=response.estimated_completion,
        )

    @router.get(
        "/chains",
        summary="Get Supported Chains",
        description="Get list of supported Axelar chains",
        response_model=ChainsResponse,
        error_map=axelar_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_chains(
        query: FromDishka[GetChains],
    ) -> ChainsResponse:
        """Get supported chains."""
        response = await query.execute()

        return ChainsResponse(
            chains=[
                ChainResponse(
                    id=c.id,
                    name=c.name,
                    chain_id=c.chain_id,
                )
                for c in response.chains
            ],
            count=response.count,
        )

    @router.get(
        "/tokens/{chain}",
        summary="Get Supported Tokens",
        description="Get supported tokens for a chain",
        response_model=TokensResponse,
        error_map=axelar_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_tokens(
        chain: str,
        query: FromDishka[GetTokens],
    ) -> TokensResponse:
        """Get supported tokens for a chain."""
        request = GetTokensRequest(chain=chain)
        response = await query.execute(request)

        return TokensResponse(
            tokens=[
                TokenResponse(
                    symbol=t.symbol,
                    name=t.name,
                    decimals=t.decimals,
                    is_axl_wrapped=t.is_axl_wrapped,
                )
                for t in response.tokens
            ],
            chain=response.chain,
            count=response.count,
        )

    return router
