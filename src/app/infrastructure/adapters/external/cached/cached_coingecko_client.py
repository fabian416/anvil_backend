"""
Cached CoinGecko API Client.

Wraps the base CoinGeckoClient with Redis caching for:
- Price data (30s TTL)
- Market charts (1h TTL)
- Coin details (15min TTL)
- Trending coins (5min TTL)
- Global market data (2min TTL)
"""

from dataclasses import asdict
from typing import Any, Optional

from app.infrastructure.adapters.external.coingecko_client import (
    CoinDetails,
    CoinGeckoClient,
    MarketChart,
    Price,
    TrendingCoin,
)
from app.infrastructure.cache.external_api_cache import ExternalAPICache


class CachedCoinGeckoClient(CoinGeckoClient):
    """
    CoinGecko client with Redis caching.

    Reduces API calls significantly for frequently requested data.

    Example:
        >>> cache = ExternalAPICache(redis_client)
        >>> client = CachedCoinGeckoClient(api_key="...", cache=cache)
        >>>
        >>> # First call hits API
        >>> price = await client.get_price("ethereum")
        >>>
        >>> # Subsequent calls within TTL hit cache
        >>> price = await client.get_price("ethereum")  # From cache!
    """

    API_NAME = "coingecko"

    def __init__(
        self,
        api_key: str | None = None,
        cache: Optional[ExternalAPICache] = None,
    ):
        """
        Initialize cached CoinGecko client.

        Args:
            api_key: CoinGecko API key (optional)
            cache: External API cache instance
        """
        super().__init__(api_key)
        self._cache = cache

    async def get_price(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True,
    ) -> Price:
        """Get current price with caching (30s TTL)."""
        if self._cache:
            # Try cache first
            cached = await self._cache.get(
                self.API_NAME,
                "price",
                coin_id=coin_id,
                vs_currency=vs_currency,
            )
            if cached:
                return Price(**cached)

        # Fetch from API
        result = await super().get_price(
            coin_id,
            vs_currency,
            include_market_cap,
            include_24hr_vol,
            include_24hr_change,
        )

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "price",
                asdict(result),
                coin_id=coin_id,
                vs_currency=vs_currency,
            )

        return result

    async def get_prices_bulk(
        self,
        coin_ids: list[str],
        vs_currency: str = "usd",
    ) -> dict[str, Price]:
        """Get prices for multiple coins with caching."""
        if self._cache:
            # Try cache first
            ids_key = ",".join(sorted(coin_ids))
            cached = await self._cache.get(
                self.API_NAME,
                "prices_bulk",
                coin_ids=ids_key,
                vs_currency=vs_currency,
            )
            if cached:
                return {k: Price(**v) for k, v in cached.items()}

        # Fetch from API
        result = await super().get_prices_bulk(coin_ids, vs_currency)

        # Cache result
        if self._cache:
            cache_data = {k: asdict(v) for k, v in result.items()}
            await self._cache.set(
                self.API_NAME,
                "prices_bulk",
                cache_data,
                coin_ids=ids_key,
                vs_currency=vs_currency,
            )

        return result

    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> MarketChart:
        """Get historical price chart with caching (1h TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "market_chart",
                coin_id=coin_id,
                vs_currency=vs_currency,
                days=days,
            )
            if cached:
                return MarketChart(
                    coin_id=cached["coin_id"],
                    prices=[(int(ts), float(p)) for ts, p in cached["prices"]],
                    market_caps=[
                        (int(ts), float(mc)) for ts, mc in cached["market_caps"]
                    ],
                    total_volumes=[
                        (int(ts), float(v)) for ts, v in cached["total_volumes"]
                    ],
                )

        # Fetch from API
        result = await super().get_market_chart(coin_id, vs_currency, days)

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "market_chart",
                asdict(result),
                coin_id=coin_id,
                vs_currency=vs_currency,
                days=days,
            )

        return result

    async def get_coin_details(self, coin_id: str) -> CoinDetails:
        """Get detailed coin info with caching (15min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "coin_details",
                coin_id=coin_id,
            )
            if cached:
                return CoinDetails(**cached)

        # Fetch from API
        result = await super().get_coin_details(coin_id)

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "coin_details",
                asdict(result),
                coin_id=coin_id,
            )

        return result

    async def get_trending_coins(self) -> list[TrendingCoin]:
        """Get trending coins with caching (5min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "trending",
            )
            if cached:
                return [TrendingCoin(**c) for c in cached]

        # Fetch from API
        result = await super().get_trending_coins()

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "trending",
                [asdict(c) for c in result],
            )

        return result

    async def search_coins(self, query: str) -> list[dict]:
        """Search coins with caching (15min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "search",
                query=query,
            )
            if cached:
                return cached

        # Fetch from API
        result = await super().search_coins(query)

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "search",
                result,
                query=query,
            )

        return result

    async def get_global_data(self) -> dict[str, Any]:
        """Get global market data with caching (2min TTL)."""
        if self._cache:
            cached = await self._cache.get(
                self.API_NAME,
                "global",
            )
            if cached:
                return cached

        # Fetch from API
        result = await super().get_global_data()

        # Cache result
        if self._cache:
            await self._cache.set(
                self.API_NAME,
                "global",
                result,
            )

        return result
