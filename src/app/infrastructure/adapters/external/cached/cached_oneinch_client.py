"""
Cached 1inch DEX Aggregator API Client.

Wraps the base OneInchClient with Redis caching for:
- Swap quotes (30s TTL - prices change fast)
- Token list (15min TTL - changes rarely)
- Protocols (15min TTL - changes rarely)

Note: Swap transaction data is NOT cached as it's
unique per user address and time-sensitive.
"""

from dataclasses import asdict
from typing import Optional

from app.infrastructure.adapters.external.oneinch_client import (
    OneInchClient,
    SwapQuote,
    SwapTransaction,
    Token,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class CachedOneInchClient(OneInchClient):
    """
    1inch client with Redis caching.

    Important: This client is rate-limited (1 req/sec free tier).
    Caching significantly reduces the number of API calls.

    Example:
        >>> cache = ExternalAPICache(redis_client)
        >>> client = CachedOneInchClient(api_key="...", cache=cache)
        >>>
        >>> # First call hits API
        >>> quote = await client.get_swap_quote(eth, usdc, amount)
        >>>
        >>> # Same quote within 30s hits cache
        >>> quote = await client.get_swap_quote(eth, usdc, amount)  # From cache!
    """

    API_NAME = "oneinch"

    def __init__(
        self,
        api_key: str,
        chain: str = "ethereum",
        cache: Optional[ExternalAPICache] = None,
    ):
        """
        Initialize cached 1inch client.

        Args:
            api_key: 1inch API key
            chain: Blockchain name (default: "ethereum")
            cache: External API cache instance
        """
        super().__init__(api_key, chain)
        self._cache = cache

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 1.0,
    ) -> SwapQuote:
        """Get swap quote with caching (30s TTL)."""
        if self._cache:
            # Cache key includes all params that affect the quote
            cached = await self._cache.get(
                self.API_NAME,
                "quote",
                chain=self._chain,
                from_token=from_token.lower(),
                to_token=to_token.lower(),
                amount=amount,
            )
            if cached:
                return SwapQuote(**cached)

        # Fetch from API
        result = await super().get_swap_quote(
            from_token,
            to_token,
            amount,
            slippage,
        )

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "quote",
                asdict(result),
                chain=self._chain,
                from_token=from_token.lower(),
                to_token=to_token.lower(),
                amount=amount,
            )

        return result

    async def get_swap_data(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
        disable_estimate: bool = False,
    ) -> SwapTransaction:
        """
        Get swap transaction data (NOT cached).

        Transaction data is unique per user address and
        time-sensitive, so it should not be cached.
        """
        # No caching for swap data - it's user-specific and time-sensitive
        return await super().get_swap_data(
            from_token,
            to_token,
            amount,
            from_address,
            slippage,
            disable_estimate,
        )

    async def get_tokens(self) -> list[Token]:
        """Get supported tokens with caching (15min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "tokens",
                chain=self._chain,
            )
            if cached:
                return [Token(**t) for t in cached]

        # Fetch from API
        result = await super().get_tokens()

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "tokens",
                [asdict(t) for t in result],
                chain=self._chain,
            )

        return result

    async def get_token_price(
        self,
        token_address: str,
        vs_currency: str = "USD",
    ) -> float:
        """Get token price with caching (30s TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "token_price",
                chain=self._chain,
                token=token_address.lower(),
            )
            if cached is not None:
                return cached

        # Fetch from API
        result = await super().get_token_price(token_address, vs_currency)

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "token_price",
                result,
                chain=self._chain,
                token=token_address.lower(),
            )

        return result

    async def get_protocols(self) -> list[dict]:
        """Get DEX protocols with caching (15min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "protocols",
                chain=self._chain,
            )
            if cached:
                return cached

        # Fetch from API
        result = await super().get_protocols()

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "protocols",
                result,
                chain=self._chain,
            )

        return result
