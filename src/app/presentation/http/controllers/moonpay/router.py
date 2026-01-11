"""
MoonPay Swap Router.

Provides crypto-to-crypto swap endpoints:
- GET /pairs: List available swap pairs
- GET /quote: Get swap quote (cotización)
- GET /requote: Get updated quote (recotización)
- POST /execute: Execute a swap (requires customer auth)
- POST /submit: Submit a signed transaction
- GET /status/{swap_id}: Get swap status

Note: Execute endpoint requires MoonPay customer authentication.
For most use cases, swap execution is handled by Privy on the frontend.

The backend proxies to MoonPay API, keeping API keys secure.
"""

import logging
from typing import Annotated
from uuid import uuid4

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.infrastructure.adapters.external.moonpay_swap_client import (
    MoonPaySwapClient,
)
from app.setup.config.moonpay import MoonPaySettings

logger = logging.getLogger(__name__)


# ========================================
# Response Schemas
# ========================================


class SwapPairResponse(BaseModel):
    """Swap pair information."""

    pair_name: str = Field(..., description="Pair name, e.g., 'eth-usdc'")
    base_currency_code: str = Field(..., description="Base currency code, e.g., 'eth'")
    quote_currency_code: str = Field(
        ..., description="Quote currency code, e.g., 'usdc'"
    )
    base_currency_name: str = Field(..., description="Base currency name")
    quote_currency_name: str = Field(..., description="Quote currency name")
    min_base_amount: float | None = Field(None, description="Minimum swap amount")
    max_base_amount: float | None = Field(None, description="Maximum swap amount")


class SwapPairsResponse(BaseModel):
    """Response containing list of swap pairs."""

    pairs: list[SwapPairResponse]
    count: int


class SwapQuoteResponse(BaseModel):
    """Swap quote information (cotización)."""

    id: str = Field(..., description="Quote ID")
    pair_name: str = Field(..., description="Pair name, e.g., 'eth-usdc'")
    base_currency_code: str = Field(..., description="Source currency code")
    quote_currency_code: str = Field(..., description="Destination currency code")
    base_currency_amount: str = Field(..., description="Amount being swapped")
    quote_currency_amount: str = Field(..., description="Amount to receive")
    exchange_rate: str = Field(..., description="Exchange rate")
    network_fee_usd: str = Field(..., description="Network fee in USD")
    extra_fee_usd: str = Field(..., description="Extra fee in USD")
    base_price_usd: str = Field(..., description="Base currency price in USD")
    quote_price_usd: str = Field(..., description="Quote currency price in USD")
    expires_at: str = Field(..., description="Quote expiration time (ISO 8601)")


# ========================================
# Execution Request/Response Schemas
# ========================================


class SwapExecuteRequest(BaseModel):
    """Request to execute a swap."""

    quote_id: str = Field(..., description="Quote ID from /quote endpoint")
    wallet_address: str = Field(..., description="Wallet address for the swap")
    signature: str = Field(..., description="Signature from the quote response")
    external_transaction_id: str | None = Field(
        None, description="Optional external transaction ID for tracking"
    )


class SwapExecuteResponse(BaseModel):
    """Response from swap execution."""

    id: str = Field(..., description="Swap transaction ID")
    status: str = Field(..., description="Swap status")
    requires_signature: bool = Field(
        False, description="Whether the swap requires additional signature"
    )
    transaction: dict | None = Field(
        None, description="Transaction data if signature required"
    )
    message: str = Field(..., description="Status message")


class SwapSubmitRequest(BaseModel):
    """Request to submit a signed transaction."""

    swap_id: str = Field(..., description="Swap transaction ID")
    signed_transaction: str = Field(..., description="Signed transaction data")


class SwapSubmitResponse(BaseModel):
    """Response from submitting a signed transaction."""

    id: str = Field(..., description="Swap transaction ID")
    status: str = Field(..., description="Swap status")
    tx_hash: str | None = Field(None, description="Transaction hash if available")
    message: str = Field(..., description="Status message")


class SwapStatusResponse(BaseModel):
    """Response for swap status query."""

    id: str = Field(..., description="Swap transaction ID")
    status: str = Field(
        ...,
        description="Swap status: pending, processing, completed, failed, waitingForDeposit, executingSwap",
    )
    tx_hash: str | None = Field(None, description="Transaction hash if available")
    from_amount: str | None = Field(None, description="Amount swapped from")
    to_amount: str | None = Field(None, description="Amount received")
    from_token: str | None = Field(None, description="Source token")
    to_token: str | None = Field(None, description="Destination token")
    created_at: str | None = Field(None, description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")


# ========================================
# Router Factory
# ========================================


def create_moonpay_router() -> APIRouter:
    """Create the MoonPay swap quote router."""

    router = APIRouter(
        prefix="/moonpay/swap",
        tags=["MoonPay Swap"],
    )

    @router.get(
        "/pairs",
        response_model=SwapPairsResponse,
        summary="Get available swap pairs",
        description="Returns list of available crypto-to-crypto swap pairs from MoonPay.",
    )
    @inject
    async def get_swap_pairs(
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> SwapPairsResponse:
        """
        Get available swap pairs.

        No authentication required - this is public data.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured. Set MOONPAY_API_KEY in config.",
                },
            )

        client = MoonPaySwapClient(
            api_key=moonpay_settings.api_key,
            environment=moonpay_settings.environment,
        )

        try:
            pairs = await client.get_pairs()
            return SwapPairsResponse(
                pairs=[
                    SwapPairResponse(
                        pair_name=p.pair_name,
                        base_currency_code=p.base_currency_code,
                        quote_currency_code=p.quote_currency_code,
                        base_currency_name=p.base_currency_name,
                        quote_currency_name=p.quote_currency_name,
                        min_base_amount=p.min_base_amount,
                        max_base_amount=p.max_base_amount,
                    )
                    for p in pairs
                ],
                count=len(pairs),
            )
        except Exception as e:
            logger.error(f"Failed to get MoonPay swap pairs: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "MOONPAY_API_ERROR",
                    "message": str(e),
                },
            )
        finally:
            await client.close()

    @router.get(
        "/quote",
        response_model=SwapQuoteResponse,
        summary="Get swap quote (cotización)",
        description="Get a quote for swapping tokens. Example: 1 ETH → USDC",
    )
    @inject
    async def get_swap_quote(
        moonpay_settings: FromDishka[MoonPaySettings],
        from_token: Annotated[
            str, Query(description="Source token symbol, e.g., 'ETH'")
        ],
        to_token: Annotated[
            str, Query(description="Destination token symbol, e.g., 'USDC'")
        ],
        amount: Annotated[str, Query(description="Amount to swap, e.g., '1'")],
    ) -> SwapQuoteResponse:
        """
        Get swap quote (cotización).

        Example: GET /api/v1/moonpay/swap/quote?from_token=ETH&to_token=USDC&amount=1

        No authentication required - quotes are read-only.
        Swap execution is handled by Privy on the frontend.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured. Set MOONPAY_API_KEY in config.",
                },
            )

        client = MoonPaySwapClient(
            api_key=moonpay_settings.api_key,
            environment=moonpay_settings.environment,
        )

        try:
            # Build pair name (e.g., "eth-usdc")
            pair_name = client.build_pair_name(from_token, to_token)

            quote = await client.get_quote(
                pair_name=pair_name,
                base_amount=amount,
            )

            return SwapQuoteResponse(
                id=quote.id,
                pair_name=quote.pair_name,
                base_currency_code=quote.base_currency_code,
                quote_currency_code=quote.quote_currency_code,
                base_currency_amount=quote.base_currency_amount,
                quote_currency_amount=quote.quote_currency_amount,
                exchange_rate=quote.exchange_rate,
                network_fee_usd=quote.network_fee_amount_usd,
                extra_fee_usd=quote.extra_fee_amount_usd,
                base_price_usd=quote.base_currency_price_usd,
                quote_price_usd=quote.quote_currency_price_usd,
                expires_at=quote.expires_at,
            )
        except Exception as e:
            logger.error(f"Failed to get MoonPay swap quote: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "MOONPAY_QUOTE_ERROR",
                    "message": str(e),
                },
            )
        finally:
            await client.close()

    @router.get(
        "/requote",
        response_model=SwapQuoteResponse,
        summary="Get updated quote (recotización)",
        description="Get fresh pricing before confirming swap in Privy.",
    )
    @inject
    async def get_swap_requote(
        moonpay_settings: FromDishka[MoonPaySettings],
        from_token: Annotated[
            str, Query(description="Source token symbol, e.g., 'ETH'")
        ],
        to_token: Annotated[
            str, Query(description="Destination token symbol, e.g., 'USDC'")
        ],
        amount: Annotated[str, Query(description="Amount to swap, e.g., '1'")],
    ) -> SwapQuoteResponse:
        """
        Get updated quote (recotización).

        Call this right before the user confirms the swap in Privy
        to ensure they see the most current price.

        Example: GET /api/v1/moonpay/swap/requote?from_token=ETH&to_token=USDC&amount=1
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured.",
                },
            )

        client = MoonPaySwapClient(
            api_key=moonpay_settings.api_key,
            environment=moonpay_settings.environment,
        )

        try:
            pair_name = client.build_pair_name(from_token, to_token)

            # Get fresh quote (recotización)
            quote = await client.get_requote(
                pair_name=pair_name,
                base_amount=amount,
            )

            return SwapQuoteResponse(
                id=quote.id,
                pair_name=quote.pair_name,
                base_currency_code=quote.base_currency_code,
                quote_currency_code=quote.quote_currency_code,
                base_currency_amount=quote.base_currency_amount,
                quote_currency_amount=quote.quote_currency_amount,
                exchange_rate=quote.exchange_rate,
                network_fee_usd=quote.network_fee_amount_usd,
                extra_fee_usd=quote.extra_fee_amount_usd,
                base_price_usd=quote.base_currency_price_usd,
                quote_price_usd=quote.quote_currency_price_usd,
                expires_at=quote.expires_at,
            )
        except Exception as e:
            logger.error(f"Failed to get MoonPay requote: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": "MOONPAY_REQUOTE_ERROR",
                    "message": str(e),
                },
            )
        finally:
            await client.close()

    # ========================================
    # Execution Endpoints
    # ========================================

    @router.post(
        "/execute",
        response_model=SwapExecuteResponse,
        summary="Execute a swap",
        description="""
Execute a swap using a quote ID.

**Note**: This endpoint is for demonstration and testing purposes.
In production, swap execution typically requires MoonPay customer authentication
and is handled directly from the frontend via Privy SDK.

This endpoint simulates the execution flow and returns a mock response.
""",
    )
    @inject
    async def execute_swap(
        request: SwapExecuteRequest,
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> SwapExecuteResponse:
        """
        Execute a swap.

        In a real implementation, this would:
        1. Validate the quote is still valid
        2. Call MoonPay's execute_quote endpoint with customer auth
        3. Return the transaction details

        For now, this returns a simulated response for testing the flow.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured.",
                },
            )

        logger.info(
            f"Swap execute request: quote_id={request.quote_id}, "
            f"wallet={request.wallet_address[:10]}..."
        )

        # Generate a mock swap ID for testing
        swap_id = str(uuid4())

        # In production, this would call MoonPay's execute_quote endpoint
        # which requires customer authentication (Bearer token from MoonPay login)
        #
        # Example of what the real call would look like:
        # client = MoonPaySwapClient(api_key=moonpay_settings.api_key)
        # result = await client.execute_swap(
        #     quote_id=request.quote_id,
        #     wallet_address=request.wallet_address,
        #     signature=request.signature,
        #     external_transaction_id=request.external_transaction_id,
        # )

        return SwapExecuteResponse(
            id=swap_id,
            status="pending",
            requires_signature=False,
            transaction=None,
            message="Swap initiated successfully. In production, this would execute via MoonPay.",
        )

    @router.post(
        "/submit",
        response_model=SwapSubmitResponse,
        summary="Submit a signed transaction",
        description="""
Submit a signed transaction for a swap.

**Note**: This endpoint is for demonstration and testing purposes.
In production, transaction signing and submission is handled by Privy SDK.
""",
    )
    @inject
    async def submit_signed_swap(
        request: SwapSubmitRequest,
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> SwapSubmitResponse:
        """
        Submit a signed transaction.

        In a real implementation, this would:
        1. Validate the swap exists and is pending
        2. Submit the signed transaction to the blockchain
        3. Return the transaction hash
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured.",
                },
            )

        logger.info(f"Swap submit request: swap_id={request.swap_id}")

        # Generate a mock transaction hash
        mock_tx_hash = f"0x{uuid4().hex}"

        return SwapSubmitResponse(
            id=request.swap_id,
            status="processing",
            tx_hash=mock_tx_hash,
            message="Transaction submitted. In production, this would be broadcast to the blockchain.",
        )

    @router.get(
        "/status/{swap_id}",
        response_model=SwapStatusResponse,
        summary="Get swap status",
        description="Get the current status of a swap transaction.",
    )
    @inject
    async def get_swap_status(
        swap_id: str,
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> SwapStatusResponse:
        """
        Get swap status.

        Returns the current status of a swap transaction.
        In production, this would query MoonPay's transaction status API.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured.",
                },
            )

        logger.info(f"Swap status request: swap_id={swap_id}")

        # In production, this would call MoonPay's transaction status API
        # client = MoonPaySwapClient(api_key=moonpay_settings.api_key)
        # result = await client.get_swap_status(swap_id)

        # For now, return a mock response
        return SwapStatusResponse(
            id=swap_id,
            status="completed",
            tx_hash=f"0x{uuid4().hex}",
            from_amount="1.0",
            to_amount="3014.24",
            from_token="ETH",
            to_token="USDC",
            created_at="2026-01-11T12:00:00Z",
            updated_at="2026-01-11T12:01:00Z",
        )

    return router
