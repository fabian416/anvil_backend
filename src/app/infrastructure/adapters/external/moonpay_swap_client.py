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

import logging
from dataclasses import dataclass

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
        environment: str = "sandbox",
    ):
        """
        Initialize MoonPay Swap client.

        Args:
            api_key: MoonPay publishable API key (pk_test_... or pk_live_...)
            environment: "sandbox" or "production"
        """
        self._api_key = api_key
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
        """
        try:
            response = await self._client.get(
                f"/swap/{pair_name}/quote",
                params={
                    "apiKey": self._api_key,
                    "baseCurrencyAmount": base_amount,
                },
            )
            response.raise_for_status()
            data = response.json()

            quote = MoonPaySwapQuote(
                id=data.get("id", ""),
                pair_name=data.get("pairName", pair_name),
                base_currency_code=data.get("baseCurrency", {}).get("code", ""),
                quote_currency_code=data.get("quoteCurrency", {}).get("code", ""),
                base_currency_amount=data.get("baseCurrencyAmount", base_amount),
                quote_currency_amount=data.get("quoteCurrencyAmount", "0"),
                exchange_rate=data.get("exchangeRate", "0"),
                network_fee_amount=data.get("networkFeeAmount", "0"),
                network_fee_amount_usd=data.get("networkFeeAmountInUSD", "0"),
                extra_fee_amount=data.get("extraFeeAmount", "0"),
                extra_fee_amount_usd=data.get("extraFeeAmountInUSD", "0"),
                base_currency_price_usd=data.get("baseCurrencyPriceInUsd", "0"),
                quote_currency_price_usd=data.get("quoteCurrencyPriceInUsd", "0"),
                expires_at=data.get("expiresAt", ""),
            )

            logger.info(
                f"MoonPay quote: {base_amount} {quote.base_currency_code} → "
                f"{quote.quote_currency_amount} {quote.quote_currency_code}"
            )
            return quote

        except httpx.HTTPStatusError as e:
            logger.error(
                f"MoonPay API error getting quote: {e.response.status_code} - {e.response.text}"
            )
            raise
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
