"""
Admin Transactions Router.

Provides admin-only access to transaction history scoped by wallet address or user id.

Endpoints:
- GET /admin/transactions - List transactions for any wallet/user (admin)
"""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, Field

from app.application.common.exceptions.authorization import AuthorizationError
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.auth.handlers.transaction_log import (
    GetAdminTransactionHistoryHandler,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class AdminTransactionHistoryItemResponse(BaseModel):
    """Single transaction in history (admin view)."""

    id: int = Field(..., description="Transaction database ID")
    tx_hash: str | None = Field(None, description="Transaction hash")
    type: str = Field(..., description="Transaction type")
    chain: str = Field(..., description="Blockchain name")
    status: str = Field(..., description="Transaction status")
    to_address: str | None = Field(None, description="Recipient address")
    asset_in: str | None = Field(None, description="Input asset symbol")
    amount_in: str | None = Field(None, description="Input amount")
    asset_out: str | None = Field(None, description="Output asset symbol")
    amount_out: str | None = Field(None, description="Output amount")
    fee_usd: str | None = Field(None, description="Fee in USD")
    block_number: int | None = Field(None, description="Confirmation block")
    confirmed_at: str | None = Field(None, description="Confirmation timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    explorer_url: str | None = Field(None, description="Block explorer URL")
    gas_used: int | None = Field(None, description="Gas units consumed")
    gas_price: int | None = Field(None, description="Gas price in wei")
    is_incoming: bool = Field(False, description="True if this is receiver-view record")
    from_address: str | None = Field(None, description="Sender address (incoming tx)")


class AdminTransactionHistoryResponse(BaseModel):
    """Response with transaction history (admin)."""

    wallet_address: str | None = Field(
        None, description="Optional wallet address used to scope the query"
    )
    user_id: int | None = Field(
        None, description="Optional user id used to scope the query"
    )
    transactions: list[AdminTransactionHistoryItemResponse] = Field(
        ..., description="List of transactions"
    )
    total: int = Field(..., description="Total matching transactions")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


def create_admin_transactions_router() -> APIRouter:
    router = ErrorAwareRouter(prefix="/admin/transactions", tags=["Admin - Transactions"])

    @router.get(
        "",
        response_model=AdminTransactionHistoryResponse,
        status_code=status.HTTP_200_OK,
        summary="Get transaction history (admin)",
        description=(
            "Admin-only endpoint to retrieve transaction history for any wallet address "
            "or user id. Supports filtering by chain, status, and transaction type."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_403_FORBIDDEN,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_admin_transaction_history(
        handler: FromDishka[GetAdminTransactionHistoryHandler],
        wallet_address: str | None = Query(
            default=None, description="Filter by wallet address (recommended)"
        ),
        user_id: int | None = Query(
            default=None, ge=1, description="Filter by user id (aggregates across wallets)"
        ),
        limit: int = Query(default=50, ge=1, le=100, description="Maximum number of results"),
        offset: int = Query(default=0, ge=0, description="Number of results to skip"),
        chain: str | None = Query(default=None, description="Filter by chain (ethereum, base, ...)"),
        status_: str | None = Query(
            default=None,
            alias="status",
            description="Filter by status: pending, success, failed",
        ),
        tx_type: str | None = Query(
            default=None,
            description="Filter by type: send, swap, approve, fund, etc.",
        ),
    ) -> AdminTransactionHistoryResponse:
        result = await handler.execute(
            wallet_address=wallet_address,
            user_id=user_id,
            limit=limit,
            offset=offset,
            chain=chain,
            status=status_,
            tx_type=tx_type,
        )

        return AdminTransactionHistoryResponse(
            wallet_address=result.wallet_address,
            user_id=result.user_id,
            transactions=[
                AdminTransactionHistoryItemResponse(
                    id=tx.id,
                    tx_hash=tx.tx_hash,
                    type=tx.type,
                    chain=tx.chain,
                    status=tx.status,
                    to_address=tx.to_address,
                    asset_in=tx.asset_in,
                    amount_in=tx.amount_in,
                    asset_out=tx.asset_out,
                    amount_out=tx.amount_out,
                    fee_usd=tx.fee_usd,
                    block_number=tx.block_number,
                    confirmed_at=tx.confirmed_at,
                    created_at=tx.created_at,
                    explorer_url=tx.explorer_url,
                    gas_used=tx.gas_used,
                    gas_price=tx.gas_price,
                    is_incoming=tx.is_incoming,
                    from_address=tx.from_address,
                )
                for tx in result.transactions
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    return router

