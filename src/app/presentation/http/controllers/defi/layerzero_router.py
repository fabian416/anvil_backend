"""
LayerZero HTTP Router.

Provides REST API endpoints for cross-chain message tracking.
"""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from app.application.queries.layerzero.estimate_fees import (
    EstimateFees,
    EstimateFeesRequest,
)
from app.application.queries.layerzero.get_chains import GetChains
from app.application.queries.layerzero.get_message_history import (
    GetMessageHistory,
    GetMessageHistoryRequest,
)
from app.application.queries.layerzero.get_oft_transfers import (
    GetOFTTransfers,
    GetOFTTransfersRequest,
)
from app.application.queries.layerzero.track_message import (
    TrackMessage,
    TrackMessageRequest,
)
from app.domain.exceptions.layerzero import (
    InvalidTxHashError,
    LayerZeroAPIError,
    LayerZeroError,
    MessageNotFoundError,
)
from app.presentation.http.controllers.defi.layerzero_schemas import (
    ChainsResponse,
    FeeEstimateResponse,
    LZChainResponse,
    LZMessageResponse,
    MessageHistoryResponse,
    MessageTrackingResponse,
    OFTTransferResponse,
    OFTTransfersResponse,
    OFTTransfersSummaryResponse,
)
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    NotFoundErrorTranslator,
    ServiceUnavailableTranslator,
    StandardizedErrorTranslator,
)


def create_layerzero_router() -> APIRouter:
    """Create and configure the LayerZero router."""
    router = ErrorAwareRouter(prefix="/layerzero", tags=["DeFi", "Cross-Chain"])

    # Common error map
    lz_error_map = {
        MessageNotFoundError: rule(
            status=status.HTTP_404_NOT_FOUND,
            translator=NotFoundErrorTranslator(resource_type="message"),
            on_error=log_info,
        ),
        InvalidTxHashError: rule(
            status=status.HTTP_400_BAD_REQUEST,
            translator=StandardizedErrorTranslator(),
            on_error=log_info,
        ),
        LayerZeroAPIError: rule(
            status=status.HTTP_502_BAD_GATEWAY,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        LayerZeroError: rule(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            translator=StandardizedErrorTranslator(),
            on_error=log_error,
        ),
    }

    @router.get(
        "/message/{tx_hash}",
        summary="Track Message",
        description="Track cross-chain message status by source transaction hash",
        response_model=MessageTrackingResponse,
        error_map=lz_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def track_message(
        tx_hash: str,
        query: FromDishka[TrackMessage],
    ) -> MessageTrackingResponse:
        """Track message status."""
        request = TrackMessageRequest(tx_hash=tx_hash)
        response = await query.execute(request)

        return MessageTrackingResponse(
            message=LZMessageResponse.from_domain(response.message),
            progress_pct=response.progress_pct,
            estimated_completion=response.estimated_completion,
        )

    @router.get(
        "/messages/{address}",
        summary="Get Message History",
        description="Get cross-chain message history for an address",
        response_model=MessageHistoryResponse,
        error_map=lz_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_message_history(
        address: str,
        query: FromDishka[GetMessageHistory],
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
        status_filter: str | None = Query(
            default=None, description="Filter by status (INFLIGHT, DELIVERED, FAILED)"
        ),
    ) -> MessageHistoryResponse:
        """Get message history."""
        request = GetMessageHistoryRequest(
            address=address,
            limit=limit,
            status_filter=status_filter,
        )
        response = await query.execute(request)

        return MessageHistoryResponse(
            messages=[LZMessageResponse.from_domain(m) for m in response.messages],
            total_count=response.total_count,
            pending_count=response.pending_count,
            delivered_count=response.delivered_count,
        )

    @router.get(
        "/chains",
        summary="Get Supported Chains",
        description="Get list of supported LayerZero chains",
        response_model=ChainsResponse,
        error_map=lz_error_map,
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
            chains=[LZChainResponse.from_domain(c) for c in response.chains],
            evm_chains=[LZChainResponse.from_domain(c) for c in response.evm_chains],
            non_evm_chains=[
                LZChainResponse.from_domain(c) for c in response.non_evm_chains
            ],
        )

    @router.get(
        "/fees/estimate",
        summary="Estimate Fees",
        description="Estimate cross-chain message fees",
        response_model=FeeEstimateResponse,
        error_map=lz_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def estimate_fees(
        source_chain: str,
        destination_chain: str,
        query: FromDishka[EstimateFees],
        payload_size: int = Query(
            default=100, ge=1, le=10000, description="Payload size"
        ),
    ) -> FeeEstimateResponse:
        """Estimate message fees."""
        request = EstimateFeesRequest(
            source_chain=source_chain,
            destination_chain=destination_chain,
            payload_size=payload_size,
        )
        fee = await query.execute(request)
        return FeeEstimateResponse.from_domain(fee)

    @router.get(
        "/oft/{address}",
        summary="Get OFT Transfers",
        description="Get OFT transfer history for an address",
        response_model=OFTTransfersResponse,
        error_map=lz_error_map,
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
    )
    @inject
    async def get_oft_transfers(
        address: str,
        query: FromDishka[GetOFTTransfers],
        limit: int = Query(default=50, ge=1, le=100, description="Max results"),
    ) -> OFTTransfersResponse:
        """Get OFT transfers."""
        request = GetOFTTransfersRequest(address=address, limit=limit)
        response = await query.execute(request)

        return OFTTransfersResponse(
            transfers=[OFTTransferResponse.from_domain(t) for t in response.transfers],
            summary=OFTTransfersSummaryResponse(
                total_transfers=response.summary.total_transfers,
                pending_count=response.summary.pending_count,
                completed_count=response.summary.completed_count,
                total_volume=str(response.summary.total_volume),
            ),
        )

    return router
