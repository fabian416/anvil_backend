"""
Transaction Router
FastAPI router for transaction endpoints.

Endpoints:
- POST /transactions - Log a transaction from the frontend
- GET /transactions - Get transaction history for the current user
"""

from typing import Optional

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, Field

from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.auth.handlers.transaction_log import (
    GetTransactionHistoryHandler,
    LogTransactionHandler,
    LogTransactionInput,
    TransactionLogError,
    WalletNotFoundForTransactionError,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    BadRequestTranslator,
    NotFoundTranslator,
    ServiceUnavailableTranslator,
)


# ============================================================
# Pydantic Request/Response Models
# ============================================================


class LogTransactionRequest(BaseModel):
    """Request to log a transaction from the frontend."""

    tx_hash: str = Field(
        ...,
        description="Transaction hash from the blockchain",
        examples=["0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"],
        min_length=66,
        max_length=66,
    )
    from_address: str = Field(
        ...,
        description="Sender wallet address",
        examples=["0x1234567890abcdef1234567890abcdef12345678"],
        min_length=42,
        max_length=42,
    )
    to_address: Optional[str] = Field(
        None,
        description="Recipient address (null for contract creation)",
        examples=["0xabcdef1234567890abcdef1234567890abcdef12"],
    )
    value: str = Field(
        ...,
        description="Transaction value in wei",
        examples=["1000000000000000000"],
    )
    chain_id: int = Field(
        ...,
        description="Blockchain chain ID",
        examples=[1, 8453, 42161],
    )
    tx_type: str = Field(
        default="send",
        description="Transaction type: send, swap, approve, fund, etc.",
        examples=["send", "swap", "approve"],
    )
    asset_symbol: Optional[str] = Field(
        None,
        description="Asset symbol being transferred",
        examples=["ETH", "USDC", "WETH"],
    )
    data: Optional[str] = Field(
        None,
        description="Transaction data (for contract calls)",
        examples=["0x"],
    )


class LogTransactionResponse(BaseModel):
    """Response after logging a transaction."""

    id: int = Field(..., description="Transaction database ID")
    tx_hash: str = Field(..., description="Transaction hash")
    status: str = Field(..., description="Transaction status: pending, success, failed")
    chain: str = Field(..., description="Blockchain name")
    tx_type: str = Field(..., description="Transaction type")
    from_address: str = Field(..., description="Sender address")
    to_address: Optional[str] = Field(None, description="Recipient address")
    created_at: str = Field(..., description="ISO timestamp when logged")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "tx_hash": "0x1234567890abcdef...",
                "status": "pending",
                "chain": "ethereum",
                "tx_type": "send",
                "from_address": "0x1234...",
                "to_address": "0xabcd...",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }


class TransactionHistoryItemResponse(BaseModel):
    """Single transaction in history."""

    id: int = Field(..., description="Transaction database ID")
    tx_hash: Optional[str] = Field(None, description="Transaction hash")
    type: str = Field(..., description="Transaction type")
    chain: str = Field(..., description="Blockchain name")
    status: str = Field(..., description="Transaction status")
    asset_in: Optional[str] = Field(None, description="Input asset symbol")
    amount_in: Optional[str] = Field(None, description="Input amount")
    asset_out: Optional[str] = Field(None, description="Output asset symbol")
    amount_out: Optional[str] = Field(None, description="Output amount")
    fee_usd: Optional[str] = Field(None, description="Fee in USD")
    block_number: Optional[int] = Field(None, description="Confirmation block")
    confirmed_at: Optional[str] = Field(None, description="Confirmation timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    explorer_url: Optional[str] = Field(None, description="Block explorer URL")


class TransactionHistoryResponse(BaseModel):
    """Response with transaction history."""

    user_id: int = Field(..., description="User ID")
    transactions: list[TransactionHistoryItemResponse] = Field(
        ..., description="List of transactions"
    )
    total: int = Field(..., description="Total matching transactions")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "transactions": [
                    {
                        "id": 1,
                        "tx_hash": "0x1234...",
                        "type": "send",
                        "chain": "ethereum",
                        "status": "success",
                        "asset_in": "ETH",
                        "amount_in": "1000000000000000000",
                        "asset_out": None,
                        "amount_out": None,
                        "fee_usd": "2.50",
                        "block_number": 18500000,
                        "confirmed_at": "2024-01-15T10:30:30Z",
                        "created_at": "2024-01-15T10:30:00Z",
                        "explorer_url": "https://etherscan.io/tx/0x1234...",
                    }
                ],
                "total": 42,
                "limit": 50,
                "offset": 0,
            }
        }


# ============================================================
# Router Factory
# ============================================================


def create_transaction_router() -> APIRouter:
    """Create and configure the transaction router."""

    router = ErrorAwareRouter(prefix="/transactions", tags=["transactions"])

    @router.post(
        "",
        response_model=LogTransactionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Log a transaction",
        description=(
            "Log a transaction that was sent from the frontend via Privy. "
            "This creates a record in the database for history and auditing. "
            "The transaction status starts as 'pending' and is updated when confirmed."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            WalletNotFoundForTransactionError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=BadRequestTranslator(),
                on_error=log_info,
            ),
            TransactionLogError: rule(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
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
    async def log_transaction(
        request: LogTransactionRequest,
        handler: FromDishka[LogTransactionHandler],
    ) -> LogTransactionResponse:
        """
        Log a transaction sent from the frontend.

        After a successful Privy sendTransaction, the frontend should call
        this endpoint to persist the transaction for history and auditing.
        """
        input_data = LogTransactionInput(
            tx_hash=request.tx_hash,
            from_address=request.from_address,
            to_address=request.to_address,
            value=request.value,
            chain_id=request.chain_id,
            tx_type=request.tx_type,
            asset_symbol=request.asset_symbol,
            data=request.data,
        )

        result = await handler.execute(input_data)

        return LogTransactionResponse(
            id=result.id,
            tx_hash=result.tx_hash,
            status=result.status,
            chain=result.chain,
            tx_type=result.tx_type,
            from_address=result.from_address,
            to_address=result.to_address,
            created_at=result.created_at,
        )

    @router.get(
        "",
        response_model=TransactionHistoryResponse,
        status_code=status.HTTP_200_OK,
        summary="Get transaction history",
        description=(
            "Get the transaction history for the current authenticated user. "
            "Supports filtering by chain, status, and transaction type. "
            "Results are paginated and ordered by creation date (newest first)."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
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
    async def get_transaction_history(
        handler: FromDishka[GetTransactionHistoryHandler],
        limit: int = Query(
            default=50,
            ge=1,
            le=100,
            description="Maximum number of results",
        ),
        offset: int = Query(
            default=0,
            ge=0,
            description="Number of results to skip",
        ),
        chain: Optional[str] = Query(
            default=None,
            description="Filter by chain: ethereum, base, arbitrum, etc.",
        ),
        status: Optional[str] = Query(
            default=None,
            description="Filter by status: pending, success, failed",
        ),
        tx_type: Optional[str] = Query(
            default=None,
            description="Filter by type: send, swap, approve, etc.",
        ),
    ) -> TransactionHistoryResponse:
        """
        Get transaction history for the authenticated user.

        Returns transactions from the database with optional filtering.
        """
        result = await handler.execute(
            limit=limit,
            offset=offset,
            chain=chain,
            status=status,
            tx_type=tx_type,
        )

        return TransactionHistoryResponse(
            user_id=result.user_id,
            transactions=[
                TransactionHistoryItemResponse(
                    id=tx.id,
                    tx_hash=tx.tx_hash,
                    type=tx.type,
                    chain=tx.chain,
                    status=tx.status,
                    asset_in=tx.asset_in,
                    amount_in=tx.amount_in,
                    asset_out=tx.asset_out,
                    amount_out=tx.amount_out,
                    fee_usd=tx.fee_usd,
                    block_number=tx.block_number,
                    confirmed_at=tx.confirmed_at,
                    created_at=tx.created_at,
                    explorer_url=tx.explorer_url,
                )
                for tx in result.transactions
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    return router
