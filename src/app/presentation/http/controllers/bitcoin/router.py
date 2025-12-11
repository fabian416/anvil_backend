"""
Bitcoin Transaction Router.

FastAPI router for Bitcoin-specific transaction endpoints.
Supports logging BTC transactions sent via Privy.

Endpoints:
- POST /bitcoin/transactions - Log a Bitcoin transaction
- GET /bitcoin/transactions - Get Bitcoin transaction history
"""

import re
from typing import Literal

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, Field, field_validator

from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.auth.handlers.bitcoin_transaction import (
    GetBitcoinTransactionHistoryHandler,
    LogBitcoinTransactionHandler,
    LogBitcoinTransactionInput,
)
from app.infrastructure.auth.handlers.bitcoin_wallet import (
    CreateBitcoinWalletHandler,
    GetBitcoinWalletHandler,
)
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import (
    BadRequestTranslator,
    ServiceUnavailableTranslator,
)

# ============================================================
# Bitcoin Address Validation
# ============================================================

# Bitcoin address patterns
BTC_P2PKH_PATTERN = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")  # Legacy
BTC_P2SH_PATTERN = re.compile(r"^3[a-km-zA-HJ-NP-Z1-9]{25,34}$")  # SegWit compatible
BTC_BECH32_PATTERN = re.compile(r"^bc1[a-z0-9]{39,59}$")  # Native SegWit
BTC_BECH32M_PATTERN = re.compile(r"^bc1p[a-z0-9]{58}$")  # Taproot
# Testnet patterns
BTC_TESTNET_P2PKH_PATTERN = re.compile(r"^[mn][a-km-zA-HJ-NP-Z1-9]{25,34}$")
BTC_TESTNET_P2SH_PATTERN = re.compile(r"^2[a-km-zA-HJ-NP-Z1-9]{25,34}$")
BTC_TESTNET_BECH32_PATTERN = re.compile(r"^tb1[a-z0-9]{39,59}$")


def is_valid_bitcoin_address(address: str) -> bool:
    """Validate Bitcoin address format (mainnet or testnet)."""
    patterns = [
        BTC_P2PKH_PATTERN,
        BTC_P2SH_PATTERN,
        BTC_BECH32_PATTERN,
        BTC_BECH32M_PATTERN,
        BTC_TESTNET_P2PKH_PATTERN,
        BTC_TESTNET_P2SH_PATTERN,
        BTC_TESTNET_BECH32_PATTERN,
    ]
    return any(pattern.match(address) for pattern in patterns)


def is_testnet_address(address: str) -> bool:
    """Check if address is a testnet address."""
    testnet_patterns = [
        BTC_TESTNET_P2PKH_PATTERN,
        BTC_TESTNET_P2SH_PATTERN,
        BTC_TESTNET_BECH32_PATTERN,
    ]
    return any(pattern.match(address) for pattern in testnet_patterns)


# ============================================================
# Pydantic Request/Response Models
# ============================================================


class LogBitcoinTransactionRequest(BaseModel):
    """Request to log a Bitcoin transaction."""

    tx_hash: str = Field(
        ...,
        description="Bitcoin transaction hash (txid)",
        examples=["a1075db55d416d3ca199f55b6084e2115b9345e16c5cf302fc80e9d5fbf5d48d"],
        min_length=64,
        max_length=64,
    )
    from_address: str = Field(
        ...,
        description="Sender Bitcoin address",
        examples=["bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh"],
    )
    to_address: str = Field(
        ...,
        description="Recipient Bitcoin address",
        examples=["bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"],
    )
    amount_btc: str = Field(
        ...,
        description="Amount in BTC (as string for precision)",
        examples=["0.001", "1.5"],
    )
    fee_btc: str | None = Field(
        None,
        description="Transaction fee in BTC",
        examples=["0.00001"],
    )
    network: Literal["bitcoin", "bitcoin_testnet"] = Field(
        default="bitcoin",
        description="Bitcoin network: mainnet or testnet",
    )

    @field_validator("from_address", "to_address")
    @classmethod
    def validate_btc_address(cls, v: str) -> str:
        """Validate Bitcoin address format."""
        if not is_valid_bitcoin_address(v):
            raise ValueError(f"Invalid Bitcoin address format: {v[:10]}...")
        return v

    @field_validator("tx_hash")
    @classmethod
    def validate_tx_hash(cls, v: str) -> str:
        """Validate Bitcoin transaction hash format."""
        if not re.match(r"^[a-fA-F0-9]{64}$", v):
            raise ValueError("Invalid Bitcoin transaction hash format")
        return v.lower()


class LogBitcoinTransactionResponse(BaseModel):
    """Response after logging a Bitcoin transaction."""

    id: int = Field(..., description="Transaction database ID")
    tx_hash: str = Field(..., description="Bitcoin transaction hash")
    status: str = Field(..., description="Transaction status: pending, success, failed")
    chain: str = Field(..., description="Network: bitcoin or bitcoin_testnet")
    from_address: str = Field(..., description="Sender address")
    to_address: str = Field(..., description="Recipient address")
    amount_btc: str = Field(..., description="Amount in BTC")
    created_at: str = Field(..., description="ISO timestamp when logged")
    explorer_url: str | None = Field(None, description="Mempool.space explorer URL")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 123,
                "tx_hash": "a1075db55d416d3...f5d48d",
                "status": "pending",
                "chain": "bitcoin",
                "from_address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "to_address": "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
                "amount_btc": "0.001",
                "created_at": "2024-01-15T10:30:00Z",
                "explorer_url": "https://mempool.space/tx/a1075db55d416d3...",
            }
        }
    }


class BitcoinTransactionHistoryItemResponse(BaseModel):
    """Single Bitcoin transaction in history."""

    id: int = Field(..., description="Transaction database ID")
    tx_hash: str | None = Field(None, description="Transaction hash")
    chain: str = Field(..., description="Network: bitcoin or bitcoin_testnet")
    status: str = Field(..., description="Transaction status")
    from_address: str | None = Field(None, description="Sender address")
    to_address: str | None = Field(None, description="Recipient address")
    amount_btc: str | None = Field(None, description="Amount in BTC")
    fee_btc: str | None = Field(None, description="Fee in BTC")
    confirmed_at: str | None = Field(None, description="Confirmation timestamp")
    created_at: str = Field(..., description="Creation timestamp")
    explorer_url: str | None = Field(None, description="Block explorer URL")
    is_incoming: bool = Field(
        False, description="True if user is the receiver of this transaction"
    )


class BitcoinTransactionHistoryResponse(BaseModel):
    """Response with Bitcoin transaction history."""

    user_id: int = Field(..., description="User ID")
    transactions: list[BitcoinTransactionHistoryItemResponse] = Field(
        ..., description="List of Bitcoin transactions"
    )
    total: int = Field(..., description="Total matching transactions")
    limit: int = Field(..., description="Page size")
    offset: int = Field(..., description="Page offset")


# ============================================================
# Bitcoin Wallet Models
# ============================================================


class CreateBitcoinWalletResponse(BaseModel):
    """Response after creating a Bitcoin wallet."""

    wallet_id: int = Field(..., description="Wallet database ID")
    address: str = Field(..., description="Bitcoin address (SegWit)")
    chain: str = Field(..., description="Chain type: bitcoin or bitcoin_testnet")
    privy_wallet_id: str = Field(..., description="Privy wallet ID")
    created_at: str = Field(..., description="ISO timestamp when created")

    model_config = {
        "json_schema_extra": {
            "example": {
                "wallet_id": 42,
                "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                "chain": "bitcoin",
                "privy_wallet_id": "wallet_abc123",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
    }


class GetBitcoinWalletResponse(BaseModel):
    """Response for getting Bitcoin wallet info."""

    exists: bool = Field(..., description="Whether user has a Bitcoin wallet")
    wallet: CreateBitcoinWalletResponse | None = Field(
        None, description="Wallet info if exists"
    )


# ============================================================
# Router Factory
# ============================================================


def create_bitcoin_router() -> APIRouter:
    """Create and configure the Bitcoin transaction router."""

    router = ErrorAwareRouter(prefix="/bitcoin", tags=["bitcoin"])

    @router.post(
        "/transactions",
        response_model=LogBitcoinTransactionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Log a Bitcoin transaction",
        description=(
            "Log a Bitcoin transaction that was sent from the frontend via Privy. "
            "This creates a record in the database for history and auditing. "
            "The transaction status starts as 'pending' and is updated when confirmed."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ValueError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=BadRequestTranslator(),
                on_error=log_info,
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
    async def log_bitcoin_transaction(
        request: LogBitcoinTransactionRequest,
        handler: FromDishka[LogBitcoinTransactionHandler],
    ) -> LogBitcoinTransactionResponse:
        """
        Log a Bitcoin transaction sent from the frontend.

        After a successful Privy Bitcoin transaction, the frontend should call
        this endpoint to persist the transaction for history and auditing.
        """
        input_data = LogBitcoinTransactionInput(
            tx_hash=request.tx_hash,
            from_address=request.from_address,
            to_address=request.to_address,
            amount_btc=request.amount_btc,
            fee_btc=request.fee_btc,
            network=request.network,
        )

        result = await handler.execute(input_data)

        return LogBitcoinTransactionResponse(
            id=result.id,
            tx_hash=result.tx_hash,
            status=result.status,
            chain=result.chain,
            from_address=result.from_address,
            to_address=result.to_address,
            amount_btc=result.amount_btc,
            created_at=result.created_at,
            explorer_url=result.explorer_url,
        )

    @router.get(
        "/transactions",
        response_model=BitcoinTransactionHistoryResponse,
        status_code=status.HTTP_200_OK,
        summary="Get Bitcoin transaction history",
        description=(
            "Get the Bitcoin transaction history for the current authenticated user. "
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
    async def get_bitcoin_transaction_history(
        handler: FromDishka[GetBitcoinTransactionHistoryHandler],
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
        network: str | None = Query(
            default=None,
            description="Filter by network: bitcoin, bitcoin_testnet",
        ),
        status: str | None = Query(
            default=None,
            description="Filter by status: pending, success, failed",
        ),
    ) -> BitcoinTransactionHistoryResponse:
        """
        Get Bitcoin transaction history for the authenticated user.

        Returns Bitcoin transactions from the database with optional filtering.
        """
        result = await handler.execute(
            limit=limit,
            offset=offset,
            network=network,
            status=status,
        )

        return BitcoinTransactionHistoryResponse(
            user_id=result.user_id,
            transactions=[
                BitcoinTransactionHistoryItemResponse(
                    id=tx.id,
                    tx_hash=tx.tx_hash,
                    chain=tx.chain,
                    status=tx.status,
                    from_address=tx.from_address,
                    to_address=tx.to_address,
                    amount_btc=tx.amount_btc,
                    fee_btc=tx.fee_btc,
                    confirmed_at=tx.confirmed_at,
                    created_at=tx.created_at,
                    explorer_url=tx.explorer_url,
                    is_incoming=tx.is_incoming,
                )
                for tx in result.transactions
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    # ============================================================
    # Wallet Endpoints
    # ============================================================

    @router.post(
        "/wallets/create",
        response_model=CreateBitcoinWalletResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create a Bitcoin wallet",
        description=(
            "Create a Bitcoin SegWit wallet for the current user via Privy. "
            "Bitcoin wallets must be created server-side using Privy's API. "
            "If user already has a Bitcoin wallet, returns the existing one."
        ),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            ValueError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=BadRequestTranslator(),
                on_error=log_info,
            ),
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_error,
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def create_bitcoin_wallet(
        handler: FromDishka[CreateBitcoinWalletHandler],
    ) -> CreateBitcoinWalletResponse:
        """
        Create a Bitcoin wallet for the authenticated user.

        Bitcoin wallets in Privy must be created server-side.
        This endpoint calls Privy's API to create a SegWit wallet
        and saves it to the database.
        """
        result = await handler.execute()

        return CreateBitcoinWalletResponse(
            wallet_id=result.wallet_id,
            address=result.address,
            chain=result.chain,
            privy_wallet_id=result.privy_wallet_id,
            created_at=result.created_at,
        )

    @router.get(
        "/wallets/me",
        response_model=GetBitcoinWalletResponse,
        status_code=status.HTTP_200_OK,
        summary="Get my Bitcoin wallet",
        description=(
            "Get the current user's Bitcoin wallet if it exists. "
            "Returns exists=false if user hasn't created a Bitcoin wallet yet."
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
    async def get_my_bitcoin_wallet(
        handler: FromDishka[GetBitcoinWalletHandler],
    ) -> GetBitcoinWalletResponse:
        """
        Get the authenticated user's Bitcoin wallet.

        Returns the wallet info if it exists, or exists=false otherwise.
        """
        result = await handler.execute()

        if result is None:
            return GetBitcoinWalletResponse(exists=False, wallet=None)

        return GetBitcoinWalletResponse(
            exists=True,
            wallet=CreateBitcoinWalletResponse(
                wallet_id=result.wallet_id,
                address=result.address,
                chain=result.chain,
                privy_wallet_id=result.privy_wallet_id,
                created_at=result.created_at,
            ),
        )

    return router
