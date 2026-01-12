"""
MoonPay Swap Router.

Provides crypto-to-crypto swap endpoints:
- GET /pairs: List available swap pairs
- GET /quote: Get swap quote (cotización)
- GET /requote: Get updated quote (recotización)
- POST /sign-url: Sign widget URL for security
- POST /execute: Execute a swap (requires customer auth)
- POST /submit: Submit a signed transaction
- GET /status/{swap_id}: Get swap status

Note: Execute endpoint requires MoonPay customer authentication.
For most use cases, swap execution is handled by Privy on the frontend.

The backend proxies to MoonPay API, keeping API keys secure.
"""

import base64
import hashlib
import hmac
import logging
from typing import Annotated
from urllib.parse import urlparse
from uuid import uuid4

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.domain.ports.moonpay_token_repository import MoonPayTokenRepository
from app.infrastructure.adapters.external.moonpay_swap_client import (
    MoonPaySwapClient,
)
from app.infrastructure.auth.handlers.jwt_handler import JwtHandler
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
    # New fields for swap execution flow
    signature: str = Field("", description="Encrypted signature for execute_quote API")
    kyc_required: bool = Field(False, description="True if KYC is required (constraints include KycDataRequired)")


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
# URL Signing Request/Response Schemas
# ========================================


class SignUrlRequest(BaseModel):
    """Request to sign a MoonPay widget URL."""

    url: str = Field(
        ...,
        description="The MoonPay widget URL to sign (from SDK's generateUrlForSigning)",
    )


class SignUrlResponse(BaseModel):
    """Response with signed URL signature."""

    signature: str = Field(..., description="HMAC-SHA256 signature for the URL")
    original_url: str = Field(..., description="The original URL that was signed")


class GenerateSwapUrlRequest(BaseModel):
    """Request to generate a signed MoonPay swap widget URL."""

    base_currency_code: str = Field(
        ..., description="Token to swap from (e.g., 'eth', 'usdc')"
    )
    quote_currency_code: str = Field(
        ..., description="Token to receive (e.g., 'usdc', 'eth')"
    )
    base_currency_amount: str = Field(..., description="Amount to swap")
    wallet_address: str = Field(..., description="Wallet address to receive tokens")


class GenerateSwapUrlResponse(BaseModel):
    """Response with signed swap widget URL."""

    url: str = Field(..., description="Full signed URL to open in browser")
    signature: str = Field(..., description="The signature used")
    environment: str = Field(..., description="MoonPay environment (sandbox/production)")


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
                signature=quote.signature,
                kyc_required=quote.kyc_required,
            )
        except Exception as e:
            logger.error(f"Failed to get MoonPay swap quote: {e}")
            # Extract the actual error message
            error_message = str(e)
            # Check if it's a MoonPay-specific error with a clear message
            if hasattr(e, "message"):
                error_message = e.message
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # Use 400 for validation errors
                detail={
                    "error": "MOONPAY_QUOTE_ERROR",
                    "message": error_message,
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
                signature=quote.signature,
                kyc_required=quote.kyc_required,
            )
        except Exception as e:
            logger.error(f"Failed to get MoonPay requote: {e}")
            # Extract the actual error message
            error_message = str(e)
            if hasattr(e, "message"):
                error_message = e.message
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # Use 400 for validation errors
                detail={
                    "error": "MOONPAY_REQUOTE_ERROR",
                    "message": error_message,
                },
            )
        finally:
            await client.close()

    # ========================================
    # URL Signing Endpoint
    # ========================================

    @router.post(
        "/sign-url",
        response_model=SignUrlResponse,
        summary="Sign MoonPay widget URL",
        description="""
Sign a MoonPay widget URL for secure widget integration.

MoonPay requires URL signing when using walletAddress or walletAddresses parameters.
The signature is generated using HMAC-SHA256 with your API secret key.

**Important**: This endpoint keeps your API secret secure on the backend.
The frontend should:
1. Initialize the MoonPay SDK
2. Call `generateUrlForSigning()` to get the URL
3. Send the URL to this endpoint
4. Call `updateSignature(signature)` with the returned signature
5. Show the widget with `show()`

Example flow:
```javascript
const widget = MoonPayWebSdk({ flow: 'swap', ... });
const urlForSigning = widget.generateUrlForSigning();
const { signature } = await fetch('/api/v1/moonpay/swap/sign-url', {
    method: 'POST',
    body: JSON.stringify({ url: urlForSigning })
});
widget.updateSignature(signature);
widget.show();
```
""",
    )
    @inject
    async def sign_moonpay_url(
        request: SignUrlRequest,
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> SignUrlResponse:
        """
        Sign a MoonPay widget URL.

        The signature is generated using HMAC-SHA256 with the API secret.
        This is required when using walletAddress parameter in the widget.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured. Set MOONPAY_API_KEY in config.",
                },
            )

        # Validate the URL is from MoonPay
        try:
            parsed_url = urlparse(request.url)
            if not parsed_url.netloc.endswith("moonpay.com"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "INVALID_URL",
                        "message": "URL must be from moonpay.com domain",
                    },
                )
        except Exception as e:
            logger.error(f"Invalid URL for signing: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "INVALID_URL",
                    "message": "Invalid URL format",
                },
            )

        try:
            # Get the API secret for signing
            api_secret = moonpay_settings.secret_key
            if not api_secret:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "error": "MOONPAY_SECRET_NOT_CONFIGURED",
                        "message": "MoonPay API secret is not configured.",
                    },
                )

            # MoonPay requires signing the query string part of the URL
            # The signature is HMAC-SHA256 of the query string, encoded in BASE64
            # See: https://dev.moonpay.com/docs/on-ramp-enhance-security-using-signed-urls
            query_string = parsed_url.query
            if query_string.startswith("?"):
                query_string = query_string[1:]

            # Generate HMAC-SHA256 signature and encode as BASE64 (NOT hex!)
            signature_bytes = hmac.new(
                api_secret.encode("utf-8"),
                f"?{query_string}".encode("utf-8"),
                hashlib.sha256,
            ).digest()
            signature = base64.b64encode(signature_bytes).decode("utf-8")

            logger.info(f"MoonPay URL signed successfully for domain: {parsed_url.netloc}")

            return SignUrlResponse(
                signature=signature,
                original_url=request.url,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to sign MoonPay URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "SIGNING_ERROR",
                    "message": "Failed to sign URL",
                },
            )

    # ========================================
    # Generate Signed URL Endpoint
    # ========================================

    @router.post(
        "/generate-signed-url",
        response_model=GenerateSwapUrlResponse,
        summary="Generate signed MoonPay swap widget URL",
        description="""
Generate a fully signed URL for the MoonPay swap widget.

**IMPORTANT**: MoonPay requires URL signing when pre-filling `walletAddress`.
Without a valid signature, the widget will show an infinite loading state.

This endpoint:
1. Constructs the widget URL with swap parameters
2. Signs the URL using HMAC-SHA256 with your API secret
3. Returns the complete signed URL ready to open in a browser

Frontend usage:
```javascript
const { url } = await fetch('/api/v1/moonpay/swap/generate-signed-url', {
    method: 'POST',
    body: JSON.stringify({
        base_currency_code: 'usdc',
        quote_currency_code: 'eth',
        base_currency_amount: '100',
        wallet_address: '0x...'
    })
}).then(r => r.json());

window.open(url, '_blank');
```
""",
    )
    @inject
    async def generate_signed_swap_url(
        request: GenerateSwapUrlRequest,
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> GenerateSwapUrlResponse:
        """
        Generate a fully signed URL for the MoonPay swap widget.

        MoonPay requires URL signing when walletAddress is pre-filled.
        Without a valid signature, the widget shows infinite loading.
        """
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_NOT_CONFIGURED",
                    "message": "MoonPay API is not configured. Set MOONPAY_API_KEY in config.",
                },
            )

        api_secret = moonpay_settings.secret_key
        if not api_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "MOONPAY_SECRET_NOT_CONFIGURED",
                    "message": "MoonPay API secret is not configured for URL signing.",
                },
            )

        try:
            from urllib.parse import quote, urlencode

            # Determine base URL based on environment
            # MoonPay widget URL (NOT the API URL)
            base_url = (
                "https://buy-sandbox.moonpay.com"
                if moonpay_settings.is_sandbox
                else "https://buy.moonpay.com"
            )

            # Build query parameters for swap widget
            # IMPORTANT: Parameters MUST be sorted alphabetically for signature validation
            # baseCurrencyCode = crypto to swap FROM (e.g., 'usdc')
            # currencyCode = crypto to receive (e.g., 'eth')
            #
            # MoonPay Signing Process (per official docs):
            # 1. Build query string with URL-encoded values, sorted alphabetically
            # 2. HMAC-SHA256 of "?" + query_string using secret key
            # 3. Base64 encode the HMAC result
            # 4. URL-encode the Base64 signature
            # 5. Append &signature=<encoded_signature> to URL

            # Step 1: Build params dict - will be sorted alphabetically
            params = {
                "apiKey": moonpay_settings.api_key,
                "baseCurrencyAmount": request.base_currency_amount,
                "baseCurrencyCode": request.base_currency_code.lower(),
                "currencyCode": request.quote_currency_code.lower(),
                "showWalletAddressForm": "false",
                "walletAddress": request.wallet_address,
            }

            # Sort parameters alphabetically (required by MoonPay)
            sorted_params = dict(sorted(params.items()))

            # Build query string - urlencode automatically URL-encodes values
            query_string = urlencode(sorted_params)

            # Step 2 & 3: Generate HMAC-SHA256 signature and Base64 encode
            # CRITICAL: Sign the query string WITH the "?" prefix (per MoonPay docs)
            # The value to sign is exactly: "?" + query_string
            to_sign = f"?{query_string}"
            signature_bytes = hmac.new(
                api_secret.encode("utf-8"),
                to_sign.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            signature_base64 = base64.b64encode(signature_bytes).decode("utf-8")

            # Step 4: URL-encode the Base64 signature
            # This is critical - the signature contains characters like + and /
            # that must be percent-encoded
            encoded_signature = quote(signature_base64, safe="")

            # Step 5: Build final signed URL
            signed_url = f"{base_url}?{query_string}&signature={encoded_signature}"

            # Log signing details for debugging
            logger.info(
                f"[MoonPay URL Signing] "
                f"swap: {request.base_currency_code} -> {request.quote_currency_code}, "
                f"env: {moonpay_settings.environment}"
            )
            logger.info(f"[MoonPay] String to sign: {to_sign}")
            logger.info(f"[MoonPay] Signature (base64): {signature_base64}")
            logger.info(f"[MoonPay] Signature (URL-encoded): {encoded_signature}")
            logger.info(f"[MoonPay] Final URL: {signed_url}")

            return GenerateSwapUrlResponse(
                url=signed_url,
                signature=signature_base64,
                environment=moonpay_settings.environment,
            )

        except Exception as e:
            logger.error(f"Failed to generate signed MoonPay URL: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "URL_GENERATION_ERROR",
                    "message": "Failed to generate signed URL",
                },
            )

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

    # ========================================
    # Debug Endpoint (for troubleshooting signature issues)
    # ========================================

    class DebugSignatureResponse(BaseModel):
        """Debug response showing signature generation details."""

        api_key: str = Field(..., description="API key being used")
        secret_key_prefix: str = Field(
            ..., description="First 20 chars of secret key (for verification)"
        )
        secret_key_length: int = Field(..., description="Length of secret key")
        environment: str = Field(..., description="Current environment")
        is_sandbox: bool = Field(..., description="Whether sandbox mode is active")
        string_to_sign: str = Field(..., description="Exact string being signed")
        signature_base64: str = Field(..., description="Generated signature (Base64)")
        signature_url_encoded: str = Field(
            ..., description="Generated signature (URL-encoded)"
        )
        final_url: str = Field(..., description="Final signed URL")
        expected_signature: str = Field(
            ..., description="Expected signature for test values"
        )
        signatures_match: bool = Field(
            ..., description="Whether generated matches expected"
        )

    @router.post(
        "/debug-signature",
        response_model=DebugSignatureResponse,
        summary="Debug signature generation (REMOVE IN PRODUCTION)",
        description="Shows exactly what values are being used for signature generation.",
    )
    @inject
    async def debug_signature(
        moonpay_settings: FromDishka[MoonPaySettings],
    ) -> DebugSignatureResponse:
        """
        Debug endpoint to verify signature generation.

        Uses fixed test values to verify the signature matches expected output.
        REMOVE THIS ENDPOINT IN PRODUCTION.
        """
        from urllib.parse import quote, urlencode

        # Fixed test values
        test_params = {
            "apiKey": "pk_test_zJtsRVDetOru63X98XExqNoRHaFDco",
            "baseCurrencyAmount": "100",
            "baseCurrencyCode": "eth",
            "currencyCode": "usdt",
            "showWalletAddressForm": "false",
            "walletAddress": "0x2CF83F7A02c8B75D820f9EB2eE30db9AC9758bDb",
        }

        # Sort and build query string
        sorted_params = dict(sorted(test_params.items()))
        query_string = urlencode(sorted_params)
        string_to_sign = f"?{query_string}"

        # Generate signature with ACTUAL secret key from config
        api_secret = moonpay_settings.secret_key or ""
        signature_bytes = hmac.new(
            api_secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature_base64 = base64.b64encode(signature_bytes).decode("utf-8")
        signature_url_encoded = quote(signature_base64, safe="")

        base_url = (
            "https://buy-sandbox.moonpay.com"
            if moonpay_settings.is_sandbox
            else "https://buy.moonpay.com"
        )
        final_url = f"{base_url}?{query_string}&signature={signature_url_encoded}"

        # Expected signature (calculated with sk_test_4Or6cMpvuWskCAdHopbvxl2igUu1bW3)
        expected_signature = "52LRZGBBptJ8iv4CDbkbSZ43Lnre+b/GDQTKnT47aIA="

        return DebugSignatureResponse(
            api_key=moonpay_settings.api_key or "NOT_CONFIGURED",
            secret_key_prefix=api_secret[:20] + "..." if api_secret else "NOT_CONFIGURED",
            secret_key_length=len(api_secret),
            environment=moonpay_settings.environment,
            is_sandbox=moonpay_settings.is_sandbox,
            string_to_sign=string_to_sign,
            signature_base64=signature_base64,
            signature_url_encoded=signature_url_encoded,
            final_url=final_url,
            expected_signature=expected_signature,
            signatures_match=signature_base64 == expected_signature,
        )

    # ========================================
    # NEW ENDPOINTS: Official MoonPay Swap Flow
    # These endpoints implement the official MoonPay swap flow using
    # swapsCustomerSetup for KYC and API-based execution
    # ========================================

    class CheckAuthResponse(BaseModel):
        """Response for auth check endpoint."""

        has_valid_tokens: bool = Field(..., description="Whether user has valid MoonPay tokens")

    class SaveTokensRequest(BaseModel):
        """Request to save MoonPay tokens after KYC."""

        token: str = Field(..., description="MoonPay Bearer token from onAuthToken")
        csrf_token: str = Field(..., description="MoonPay CSRF token from onAuthToken")

    class SaveTokensResponse(BaseModel):
        """Response from saving tokens."""

        success: bool = Field(..., description="Whether tokens were saved successfully")

    class ExecuteSwapRequest(BaseModel):
        """Request to execute a swap."""

        signature: str = Field(..., description="Quote signature from /quote endpoint")
        base_wallet_address: str = Field(..., description="Wallet address for base currency")
        quote_wallet_address: str = Field(..., description="Wallet address for quote currency")
        refund_wallet_address: str | None = Field(None, description="Wallet for refunds (optional)")

    class ExecuteSwapResponse(BaseModel):
        """Response from swap execution."""

        transaction_id: str = Field(..., description="MoonPay transaction ID")
        status: str = Field(..., description="Transaction status")
        deposit_wallet_address: str = Field(..., description="Address to send deposit to")
        base_currency_amount: str = Field(..., description="Amount to deposit")
        quote_currency_amount: str = Field(..., description="Amount to receive")

    class TransactionStatusResponse(BaseModel):
        """Response for transaction status query."""

        id: str = Field(..., description="Transaction ID")
        status: str = Field(..., description="Current status")
        base_currency_amount: str | None = Field(None, description="Amount sent")
        quote_currency_amount: str | None = Field(None, description="Amount received")
        created_at: str | None = Field(None, description="Creation timestamp")
        updated_at: str | None = Field(None, description="Last update timestamp")

    @router.get(
        "/check-auth",
        response_model=CheckAuthResponse,
        summary="Check if user has valid MoonPay tokens",
        description="""
Check if the current user has valid MoonPay authentication tokens.

If the user has not completed KYC via the swapsCustomerSetup flow,
this will return `has_valid_tokens: false` and the frontend should
open the MoonPayKYCWidget to complete authentication.

**Requires JWT authentication.**
""",
    )
    @inject
    async def check_moonpay_auth(
        jwt_handler: FromDishka[JwtHandler],
        moonpay_token_repo: FromDishka[MoonPayTokenRepository],
        authorization: str = Header(..., alias="Authorization"),
    ) -> CheckAuthResponse:
        """Check if user has valid MoonPay tokens."""
        # Extract user_id from JWT
        try:
            # Remove "Bearer " prefix if present
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            payload = jwt_handler.decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        from uuid import UUID
        has_valid = await moonpay_token_repo.has_valid_tokens(UUID(user_id))
        return CheckAuthResponse(has_valid_tokens=has_valid)

    @router.post(
        "/save-tokens",
        response_model=SaveTokensResponse,
        summary="Save MoonPay tokens after KYC",
        description="""
Save MoonPay authentication tokens received from the swapsCustomerSetup widget.

The frontend should call this endpoint in the `onAuthToken` handler of the
MoonPayKYCWidget to persist the tokens for future swap executions.

**Requires JWT authentication.**
""",
    )
    @inject
    async def save_moonpay_tokens(
        request: SaveTokensRequest,
        jwt_handler: FromDishka[JwtHandler],
        moonpay_token_repo: FromDishka[MoonPayTokenRepository],
        authorization: str = Header(..., alias="Authorization"),
    ) -> SaveTokensResponse:
        """Save MoonPay tokens after KYC completion."""
        # Extract user_id from JWT
        try:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            payload = jwt_handler.decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        from uuid import UUID
        await moonpay_token_repo.upsert(
            user_id=UUID(user_id),
            moonpay_token=request.token,
            moonpay_csrf_token=request.csrf_token,
        )

        logger.info(f"[MoonPay] Saved tokens for user {user_id[:8]}...")
        return SaveTokensResponse(success=True)

    @router.post(
        "/execute-swap",
        response_model=ExecuteSwapResponse,
        summary="Execute a swap using stored tokens",
        description="""
Execute a swap using the quote signature and stored MoonPay tokens.

This endpoint:
1. Retrieves the user's MoonPay tokens from the database
2. Calls MoonPay's execute_quote API with the Bearer token
3. Returns the deposit wallet address for the user to send funds to

The frontend should then use Privy's sendTransaction to send the deposit
to the returned deposit_wallet_address.

**Requires JWT authentication and completed MoonPay KYC.**
""",
    )
    @inject
    async def execute_moonpay_swap(
        request: ExecuteSwapRequest,
        jwt_handler: FromDishka[JwtHandler],
        moonpay_token_repo: FromDishka[MoonPayTokenRepository],
        moonpay_settings: FromDishka[MoonPaySettings],
        authorization: str = Header(..., alias="Authorization"),
    ) -> ExecuteSwapResponse:
        """Execute a swap using stored MoonPay tokens."""
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "MOONPAY_NOT_CONFIGURED", "message": "MoonPay is not configured"},
            )

        # Extract user_id from JWT
        try:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            payload = jwt_handler.decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Get user's MoonPay tokens
        from uuid import UUID
        token_data = await moonpay_token_repo.get_by_user_id(UUID(user_id))
        if token_data is None or token_data.is_expired():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "MOONPAY_AUTH_REQUIRED",
                    "message": "User has not completed MoonPay KYC. Open swapsCustomerSetup widget first.",
                },
            )

        # Execute the swap via MoonPay API
        client = MoonPaySwapClient(
            api_key=moonpay_settings.api_key,
            environment=moonpay_settings.environment,
        )

        try:
            result = await client.execute_quote(
                customer_token=token_data.moonpay_token,
                signature=request.signature,
                base_wallet_address=request.base_wallet_address,
                quote_wallet_address=request.quote_wallet_address,
                refund_wallet_address=request.refund_wallet_address,
            )

            # Extract deposit address from response
            deposit_address = result.get("depositWalletAddress", {})
            if isinstance(deposit_address, dict):
                deposit_address = deposit_address.get("address", "")

            return ExecuteSwapResponse(
                transaction_id=result.get("transactionId", result.get("id", "")),
                status=result.get("status", "pending"),
                deposit_wallet_address=deposit_address,
                base_currency_amount=result.get("baseCurrencyAmount", ""),
                quote_currency_amount=result.get("quoteCurrencyAmount", ""),
            )
        except Exception as e:
            logger.error(f"[MoonPay] Swap execution failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "MOONPAY_EXECUTE_ERROR", "message": str(e)},
            )
        finally:
            await client.close()

    @router.get(
        "/transaction/{transaction_id}",
        response_model=TransactionStatusResponse,
        summary="Get swap transaction status",
        description="""
Get the current status of a swap transaction.

**Requires JWT authentication and valid MoonPay tokens.**
""",
    )
    @inject
    async def get_moonpay_transaction(
        transaction_id: str,
        jwt_handler: FromDishka[JwtHandler],
        moonpay_token_repo: FromDishka[MoonPayTokenRepository],
        moonpay_settings: FromDishka[MoonPaySettings],
        authorization: str = Header(..., alias="Authorization"),
    ) -> TransactionStatusResponse:
        """Get swap transaction status."""
        if not moonpay_settings.is_configured:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error": "MOONPAY_NOT_CONFIGURED", "message": "MoonPay is not configured"},
            )

        # Extract user_id from JWT
        try:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            payload = jwt_handler.decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Get user's MoonPay tokens
        from uuid import UUID
        token_data = await moonpay_token_repo.get_by_user_id(UUID(user_id))
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "MOONPAY_AUTH_REQUIRED", "message": "No MoonPay tokens found"},
            )

        client = MoonPaySwapClient(
            api_key=moonpay_settings.api_key,
            environment=moonpay_settings.environment,
        )

        try:
            result = await client.get_transaction(
                customer_token=token_data.moonpay_token,
                transaction_id=transaction_id,
            )

            return TransactionStatusResponse(
                id=result.get("id", transaction_id),
                status=result.get("status", "unknown"),
                base_currency_amount=result.get("baseCurrencyAmount"),
                quote_currency_amount=result.get("quoteCurrencyAmount"),
                created_at=result.get("createdAt"),
                updated_at=result.get("updatedAt"),
            )
        except Exception as e:
            logger.error(f"[MoonPay] Failed to get transaction {transaction_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "MOONPAY_API_ERROR", "message": str(e)},
            )
        finally:
            await client.close()

    return router
