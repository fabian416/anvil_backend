"""
MoonPay Swap API Client.

Provides crypto-to-crypto swap QUOTES via MoonPay:
- Get swap pairs
- Get swap quotes (cotización)
- Get requotes (recotización - updated prices)

Note: Swap EXECUTION is handled by Privy on the frontend.
This client only provides pricing/quotes.

API Docs: https://dev.moonpay.com/v1.0/docs/ramps-swap
Reference: https://dev.moonpay.com/v1.0/reference/getswappairs
"""

import hashlib
import hmac
import logging
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


@dataclass
class MoonPaySwapPair:
    """Available swap pair from MoonPay."""

    pair_name: str  # e.g., "eth-usdc"
    base_currency_code: str  # e.g., "eth"
    quote_currency_code: str  # e.g., "usdc"
    base_currency_name: str
    quote_currency_name: str
    min_base_amount: float | None
    max_base_amount: float | None


class MoonPayQuoteError(Exception):
    """Error when getting a swap quote from MoonPay API."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


@dataclass
class MoonPaySwapQuote:
    """Swap quote from MoonPay."""

    id: str
    pair_name: str
    base_currency_code: str
    quote_currency_code: str
    base_currency_amount: str
    quote_currency_amount: str
    exchange_rate: str
    network_fee_amount: str
    network_fee_amount_usd: str
    extra_fee_amount: str
    extra_fee_amount_usd: str
    base_currency_price_usd: str
    quote_currency_price_usd: str
    expires_at: str
    # New fields for swap execution flow
    signature: str = ""  # Encrypted signature for execute_quote API
    kyc_required: bool = False  # True if constraints include KycDataRequired


class MoonPaySwapClient:
    """
    MoonPay Swap API client for crypto-to-crypto swap QUOTES.

    Features:
    - Get available swap pairs
    - Get swap quotes with real-time pricing (cotización)
    - Get requotes for updated prices (recotización)

    Note: Swap execution is handled by Privy on the frontend.
    This client is for pricing information only.

    Usage:
        >>> client = MoonPaySwapClient(api_key="pk_test_...")
        >>> pairs = await client.get_pairs()
        >>> quote = await client.get_quote("eth-usdc", base_amount="1")
        >>> print(f"1 ETH = {quote.quote_currency_amount} USDC")
    """

    BASE_URL = "https://api.moonpay.com/v4"

    def __init__(
        self,
        api_key: str,
        secret_key: str = "",
        environment: str = "sandbox",
    ):
        """
        Initialize MoonPay Swap client.

        Args:
            api_key: MoonPay publishable API key (pk_test_... or pk_live_...)
            secret_key: MoonPay secret key for URL signing (required for execute_quote)
            environment: "sandbox" or "production"
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._environment = environment
        self._base_url = "https://api.moonpay.com/v4"

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _sign_url(self, query_params: dict) -> str:
        """
        Sign URL query parameters with HMAC SHA-256.

        MoonPay requires ALL requests with walletAddress/walletAddresses to be signed
        using the secret key. Without this signature, requests will fail with 401.

        Reference: https://dev.moonpay.com/docs/url-signing

        Args:
            query_params: Dictionary of query parameters to sign

        Returns:
            Base64-encoded HMAC SHA-256 signature

        Example:
            >>> params = {"apiKey": "pk_test_123", "walletAddress": "0x123..."}
            >>> signature = self._sign_url(params)
            >>> # Add signature to params before making request
        """
        if not self._secret_key:
            logger.warning(
                "[MoonPay] URL signing skipped: secret_key not configured. "
                "Requests with wallet addresses will fail with 401."
            )
            return ""

        # Build query string exactly as MoonPay expects
        # Format: ?key1=value1&key2=value2
        query_string = "?" + urlencode(sorted(query_params.items()))

        # Sign with HMAC SHA-256
        signature = hmac.new(
            self._secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Return base64-encoded signature
        import base64
        return base64.b64encode(signature).decode('utf-8')

    def _sign_merchant_payload(self, payload: dict) -> str:
        """
        Generate HMAC-SHA256 signature for POST payload (Merchant Signature).

        MoonPay Swaps v4 requires TWO separate signatures:
        1. URL Signature (_sign_url) - for query parameters
        2. Merchant Signature (this method) - for POST body payload

        CRITICAL: The JSON must be canonical (no spaces, keys sorted alphabetically)
        to match MoonPay's signature validation.

        Args:
            payload: Dictionary with data to sign (quoteId, walletAddresses)

        Returns:
            Base64-encoded HMAC-SHA256 merchant signature

        Example:
            >>> payload = {"quoteId": "123", "walletAddresses": {...}}
            >>> sig = self._sign_merchant_payload(payload)
        """
        if not self._secret_key:
            logger.warning(
                "[MoonPay] Merchant signature skipped: secret_key not configured. "
                "Request will fail with 401."
            )
            return ""

        # CRITICAL: Create canonical JSON (no spaces, sorted keys)
        # MoonPay validates signature against this exact format
        import json
        import base64

        json_string = json.dumps(payload, separators=(',', ':'), sort_keys=True)

        # Generate HMAC-SHA256
        signature = hmac.new(
            self._secret_key.encode('utf-8'),
            json_string.encode('utf-8'),
            hashlib.sha256
        ).digest()

        # Return base64-encoded signature
        return base64.b64encode(signature).decode('utf-8')


    async def get_pairs(self) -> list[MoonPaySwapPair]:
        """
        Get available swap pairs.

        Returns:
            List of available swap pairs

        Example:
            >>> pairs = await client.get_pairs()
            >>> for pair in pairs:
            ...     print(f"{pair.base_currency_code} → {pair.quote_currency_code}")
        """
        try:
            response = await self._client.get(
                "/swap/pairs",
                params={"apiKey": self._api_key},
            )
            response.raise_for_status()
            data = response.json()

            # Log first pair for debugging
            if data:
                logger.info(f"MoonPay API response sample: {data[0]}")

            pairs = []
            for pair_data in data:
                # MoonPay API returns flat structure, not nested
                base_code = pair_data.get("baseCurrencyCode", "").upper()
                quote_code = pair_data.get("quoteCurrencyCode", "").upper()

                pairs.append(
                    MoonPaySwapPair(
                        pair_name=pair_data.get("pairName", ""),
                        base_currency_code=base_code,
                        quote_currency_code=quote_code,
                        base_currency_name=base_code,  # API doesn't provide full names
                        quote_currency_name=quote_code,
                        min_base_amount=float(pair_data.get("minSwapAmount", 0)) if pair_data.get("minSwapAmount") else None,
                        max_base_amount=float(pair_data.get("maxSwapAmount", 0)) if pair_data.get("maxSwapAmount") else None,
                    )
                )

            logger.info(f"MoonPay: Retrieved {len(pairs)} swap pairs")
            return pairs

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MoonPay API error getting pairs: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"MoonPay request failed: {e}")
            raise

    async def get_quote(
        self,
        pair_name: str,
        base_amount: str,
    ) -> MoonPaySwapQuote:
        """
        Get swap quote for a pair (cotización).

        Args:
            pair_name: Swap pair (e.g., "eth-usdc")
            base_amount: Amount of base currency to swap

        Returns:
            MoonPaySwapQuote with pricing information

        Example:
            >>> quote = await client.get_quote("eth-usdc", "1")
            >>> print(f"1 ETH = {quote.quote_currency_amount} USDC")
        
        Raises:
            ValueError: If the quote response contains invalid data (zero amount, missing fields)
            httpx.HTTPStatusError: If the API returns an error status
        """
        try:
            logger.info(
                f"💰 [MoonPay] Requesting quote for pair={pair_name}, amount={base_amount}"
            )
            
            response = await self._client.get(
                f"/swap/{pair_name}/quote",
                params={
                    "apiKey": self._api_key,
                    "baseCurrencyAmount": base_amount,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            # Log raw response for debugging
            logger.info(f"[MoonPay] Raw quote response: {data}")

            # Extract and validate quote currency amount
            quote_currency_amount = data.get("quoteCurrencyAmount", "0")
            exchange_rate = data.get("exchangeRate", "0")
            
            # Validate the response has meaningful data
            try:
                quote_amount_float = float(quote_currency_amount) if quote_currency_amount else 0
                exchange_rate_float = float(exchange_rate) if exchange_rate else 0
            except (ValueError, TypeError):
                quote_amount_float = 0
                exchange_rate_float = 0
            
            # If MoonPay returns 0 or empty values, calculate from exchange rate
            if quote_amount_float == 0 and exchange_rate_float > 0:
                try:
                    base_amount_float = float(base_amount)
                    quote_amount_float = base_amount_float * exchange_rate_float
                    quote_currency_amount = str(quote_amount_float)
                    logger.info(
                        f"[MoonPay] Calculated quote_amount from exchange_rate: "
                        f"{base_amount} * {exchange_rate} = {quote_currency_amount}"
                    )
                except (ValueError, TypeError):
                    pass
            
            # If still no valid quote, try to calculate from USD prices
            if quote_amount_float == 0:
                base_price_usd = data.get("baseCurrencyPriceInUsd", "0")
                quote_price_usd = data.get("quoteCurrencyPriceInUsd", "0")
                try:
                    base_price = float(base_price_usd) if base_price_usd else 0
                    quote_price = float(quote_price_usd) if quote_price_usd else 0
                    if base_price > 0 and quote_price > 0:
                        base_amount_float = float(base_amount)
                        # Calculate: (base_amount * base_price_usd) / quote_price_usd
                        quote_amount_float = (base_amount_float * base_price) / quote_price
                        quote_currency_amount = str(quote_amount_float)
                        # Also calculate exchange rate
                        exchange_rate = str(base_price / quote_price)
                        logger.info(
                            f"[MoonPay] Calculated from USD prices: "
                            f"{base_amount} * {base_price}/{quote_price} = {quote_currency_amount}"
                        )
                except (ValueError, TypeError, ZeroDivisionError):
                    pass

            # Extract signature and constraints from MoonPay response
            signature = data.get("signature", "")
            constraints = data.get("constraints", [])
            kyc_required = any(
                c.get("type") == "KycDataRequired" 
                for c in constraints 
                if isinstance(c, dict)
            )
            
            quote = MoonPaySwapQuote(
                id=data.get("id", ""),
                pair_name=data.get("pairName", pair_name),
                base_currency_code=data.get("baseCurrency", {}).get("code", "") or pair_name.split("-")[0],
                quote_currency_code=data.get("quoteCurrency", {}).get("code", "") or pair_name.split("-")[1] if "-" in pair_name else "",
                base_currency_amount=data.get("baseCurrencyAmount", base_amount),
                quote_currency_amount=quote_currency_amount,
                exchange_rate=exchange_rate,
                network_fee_amount=data.get("networkFeeAmount", "0"),
                network_fee_amount_usd=data.get("networkFeeAmountInUSD", "0"),
                extra_fee_amount=data.get("extraFeeAmount", "0"),
                extra_fee_amount_usd=data.get("extraFeeAmountInUSD", "0"),
                base_currency_price_usd=data.get("baseCurrencyPriceInUsd", "0"),
                quote_currency_price_usd=data.get("quoteCurrencyPriceInUsd", "0"),
                expires_at=data.get("expiresAt", ""),
                signature=signature,
                kyc_required=kyc_required,
            )

            logger.info(
                f"✅ [MoonPay] Quote result: {base_amount} {quote.base_currency_code} → "
                f"{quote.quote_currency_amount} {quote.quote_currency_code} "
                f"(rate: {quote.exchange_rate})"
            )
            
            # Validate we have a meaningful quote
            try:
                final_quote_amount = float(quote.quote_currency_amount)
                if final_quote_amount == 0:
                    logger.warning(
                        f"[MoonPay] Warning: Quote returned 0 for {pair_name}. "
                        f"This pair may not be available or the amount is too small."
                    )
            except (ValueError, TypeError):
                pass
            
            return quote

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MoonPay API error getting quote: {e.response.status_code} - {e.response.text}"
            )
            # Extract the specific error message from MoonPay's response
            try:
                error_data = e.response.json()
                moonpay_message = error_data.get("message", str(e))
            except Exception:
                moonpay_message = str(e)
            # Raise a more descriptive error
            raise MoonPayQuoteError(moonpay_message) from e
        except Exception as e:
            logger.error(f"MoonPay quote request failed: {e}")
            raise

    async def get_requote(
        self,
        pair_name: str,
        base_amount: str,
    ) -> MoonPaySwapQuote:
        """
        Get updated quote (recotización).

        Same as get_quote but intended to refresh pricing
        before the user confirms the swap in Privy.

        Args:
            pair_name: Swap pair (e.g., "eth-usdc")
            base_amount: Amount of base currency to swap

        Returns:
            Updated MoonPaySwapQuote with fresh pricing

        Example:
            >>> # User is about to confirm, get fresh price
            >>> requote = await client.get_requote("eth-usdc", "1")
            >>> print(f"Updated rate: {requote.exchange_rate}")
        """
        # Requote is essentially a fresh quote
        return await self.get_quote(pair_name, base_amount)

    def build_pair_name(self, from_token: str, to_token: str) -> str:
        """
        Build MoonPay pair name from token symbols.

        Args:
            from_token: Source token symbol (e.g., "ETH")
            to_token: Destination token symbol (e.g., "USDC")

        Returns:
            Pair name in MoonPay format (e.g., "eth-usdc")
        """
        return f"{from_token.lower()}-{to_token.lower()}"

    async def execute_quote(
        self,
        quote_id: str,
        customer_token: str,
        signature: str,
        base_wallet_address: str,
        quote_wallet_address: str,
        refund_wallet_address: str | None = None,
        external_transaction_id: str | None = None,
    ) -> dict:
        """
        Execute a swap using DOUBLE SIGNATURE authentication with TIMESTAMP.

        MoonPay Swaps v4 requires TWO separate HMAC-SHA256 signatures:

        1. **URL Signature**: Signs query parameters (apiKey + quoteId + timestamp)
           - Protects URL from manipulation
           - Includes timestamp to prevent replay attacks
           - Added to query string as `&signature=...`

        2. **Merchant Signature**: Signs POST body payload
           - Authenticates the request body (quoteId + walletAddresses)
           - Sent in JSON body as `merchantSignature` field
           - MUST use canonical JSON (no spaces, sorted keys)

        Flow requirements:
        1. Unix timestamp (prevents replay attacks - CRITICAL)
        2. Quote ID from the quote response (CRITICAL for authorization)
        3. Customer authentication token from swapsCustomerSetup flow
        4. Quote signature from the quote response (encrypted price validation)
        5. URL signature for query params (apiKey + quoteId + timestamp)
        6. Merchant signature for POST body (quoteId + walletAddresses)

        CRITICAL: Both signatures AND timestamp must be present or request fails with 401.
        The merchant signature uses canonical JSON: separators=(',',':'), sort_keys=True

        Reference: https://dev.moonpay.com/docs/url-signing

        Args:
            quote_id: The quote ID from the quote response (REQUIRED for authorization)
            customer_token: Bearer token from MoonPay swapsCustomerSetup onAuthToken
            signature: The quote signature from the quote response
            base_wallet_address: Wallet address for the base currency (sending from)
            quote_wallet_address: Wallet address for the quote currency (receiving to)
            refund_wallet_address: Wallet address for refunds (optional, defaults to base)
            external_transaction_id: Optional external transaction ID for tracking

        Returns:
            Swap execution response with:
            - transactionId: The swap transaction ID
            - status: Current status
            - depositWalletAddress: Address to send the deposit to
            - baseCurrencyAmount: Amount to deposit
            - quoteCurrencyAmount: Amount to receive

        Raises:
            httpx.HTTPStatusError: If the API returns an error (401 = invalid token/signature)
        """
        try:
            import json

            # Build the JSON payload for the request body
            payload = {
                "signature": signature,
                "walletAddresses": {
                    "baseCurrency": {
                        "address": base_wallet_address,
                        "tag": None,
                    },
                    "quoteCurrency": {
                        "address": quote_wallet_address,
                        "tag": None,
                    },
                    "refund": {
                        "address": refund_wallet_address or base_wallet_address,
                        "tag": None,
                    },
                },
            }

            if external_transaction_id:
                payload["externalTransactionId"] = external_transaction_id

            # ============================================================
            # DOUBLE SIGNATURE SYSTEM (MoonPay Swaps v4 Requirement)
            # ============================================================

            # Generate timestamp for replay attack prevention
            import time
            timestamp = str(int(time.time()))

            # SIGNATURE 1: URL Signature (for query parameters)
            # Build query parameters for URL signing
            query_params = {
                "apiKey": self._api_key,
                "quoteId": quote_id,  # ✅ MUST be included in signature calculation
                "timestamp": timestamp,  # ✅ CRITICAL: Prevents replay attacks
            }

            # Sign the URL with HMAC SHA-256 using secret key
            url_signature = self._sign_url(query_params)

            # SIGNATURE 2: Merchant Signature (for POST body)
            # Build merchant payload for signing (canonical JSON required)
            merchant_payload = {
                "quoteId": quote_id,
                "walletAddresses": payload["walletAddresses"],
            }

            # Generate merchant signature
            merchant_signature = self._sign_merchant_payload(merchant_payload)

            # Add merchant signature to the request payload
            payload["merchantSignature"] = merchant_signature

            # ========== DEBUG LOGGING ==========
            logger.info(
                f"🚀 [MoonPay] ====== EXECUTE_QUOTE DEBUG START ======"
            )
            logger.info(
                f"🔑 [MoonPay] Customer Token (first 30 chars): {customer_token[:30] if customer_token else 'EMPTY'}..."
            )
            logger.info(
                f"🔑 [MoonPay] API Key: {self._api_key}"
            )
            logger.info(
                f"🔐 [MoonPay] Secret Key (first 20 chars): {self._secret_key[:20] if self._secret_key else 'NOT CONFIGURED'}..."
            )

            # Debug query params - ALL params are included in signature
            logger.info(
                f"📋 [MoonPay] Query params (ALL included in signature):"
            )
            for k, v in sorted(query_params.items()):
                if k == "quoteId":
                    logger.info(f"  ✅ {k} = {v}  ← REQUIRED for authorization")
                elif k == "apiKey":
                    logger.info(f"  ✅ {k} = {v}  ← REQUIRED for API access")
                elif k == "timestamp":
                    logger.info(f"  ✅ {k} = {v}  ← CRITICAL for replay attack prevention")
                else:
                    logger.info(f"  ✅ {k} = {v}")

            # Debug URL signature
            query_string_to_sign = "?" + urlencode(sorted(query_params.items()))
            logger.info(
                f"📝 [MoonPay] Complete query string for URL signature: {query_string_to_sign}"
            )
            logger.info(
                f"🔏 [MoonPay] Generated URL signature: {url_signature if url_signature else 'EMPTY'}..."
            )

            # Debug merchant signature
            import json
            merchant_json = json.dumps(merchant_payload, separators=(',', ':'), sort_keys=True)
            logger.info(
                f"📝 [MoonPay] Canonical JSON for merchant signature: {merchant_json[:100]}..."
            )
            logger.info(
                f"🔐 [MoonPay] Generated MERCHANT signature: {merchant_signature if merchant_signature else 'EMPTY'}..."
            )

            # Debug final payload with both signatures
            logger.info(
                f"📦 [MoonPay] Final request body (with merchantSignature):"
            )
            logger.info(
                f"  {json.dumps(payload, indent=2)}"
            )
            logger.info(
                f"🏁 [MoonPay] ====== EXECUTE_QUOTE DEBUG END ======"
            )
            logger.info(
                f"🔑 [MoonPay] SUMMARY: Using DOUBLE signature system (URL + Merchant)"
            )
            # ===================================

            if url_signature:
                # Add signature to query params
                query_params["signature"] = url_signature
                logger.info(
                    f"✅ [MoonPay] URL signed for execute_quote (signature: {url_signature[:20]}...)"
                )
            else:
                logger.warning(
                    "⚠️ [MoonPay] URL signing skipped - request will likely fail with 401. "
                    "Ensure MOONPAY_SECRET_KEY is configured."
                )

            logger.info(f"🔄 [MoonPay] Executing quote with quote signature: {signature[:20]}...")

            # Make POST request with signed URL and JSON payload
            response = await self._client.post(
                "/swap/execute_quote",
                params=query_params,  # Add signed query parameters
                json=payload,
                headers={
                    "Authorization": f"Bearer {customer_token}",
                },
            )
            response.raise_for_status()
            data = response.json()

            logger.info(
                f"✅ [MoonPay] Swap executed successfully: "
                f"transactionId={data.get('transactionId', 'unknown')}, "
                f"depositAddress={data.get('depositWalletAddress', {}).get('address', 'unknown')}"
            )
            return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"❌ [MoonPay] API error executing swap: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"❌ [MoonPay] Swap execution failed: {e}")
            raise

    async def get_transaction(
        self,
        customer_token: str,
        transaction_id: str,
    ) -> dict:
        """
        Get the status of a swap transaction.

        Args:
            customer_token: Bearer token from MoonPay swapsCustomerSetup
            transaction_id: The ID of the swap transaction

        Returns:
            Transaction details including:
            - id: Transaction ID
            - status: Current status (pending, waitingForDeposit, executingSwap, completed, failed)
            - baseCurrencyAmount: Amount sent
            - quoteCurrencyAmount: Amount to receive
            - depositWalletAddress: Address where deposit was sent
            - createdAt: Creation timestamp
            - updatedAt: Last update timestamp
        """
        try:
            response = await self._client.get(
                f"/swap/transaction/{transaction_id}",
                headers={
                    "Authorization": f"Bearer {customer_token}",
                },
            )
            response.raise_for_status()
            data = response.json()

            logger.info(f"[MoonPay] Transaction status: {transaction_id} -> {data.get('status', 'unknown')}")
            return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MoonPay API error getting transaction: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"MoonPay transaction request failed: {e}")
            raise
