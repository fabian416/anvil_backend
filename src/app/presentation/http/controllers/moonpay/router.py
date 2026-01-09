"""
MoonPay Swap Quote Router.

Provides crypto-to-crypto swap QUOTE endpoints:
- GET /pairs: List available swap pairs
- GET /quote: Get swap quote (cotización)
- GET /requote: Get updated quote (recotización)

Note: Swap EXECUTION is handled by Privy on the frontend.
These endpoints only provide pricing information.

The backend proxies to MoonPay API, keeping API keys secure.
"""

import logging
from typing import Annotated

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

    return router
