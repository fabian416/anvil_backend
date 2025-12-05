"""
CoinGecko API Client.

Provides access to cryptocurrency market data:
- Current prices
- Market charts (historical)
- Coin details
- Trending coins
- Global market data

API Docs: https://www.coingecko.com/en/api/documentation
Rate Limit: 10-50 calls/min (free tier)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass
class Price:
    """Current price data."""
    coin_id: str
    symbol: str
    usd: float
    usd_24h_change: float | None = None
    market_cap: float | None = None
    volume_24h: float | None = None


@dataclass
class MarketChart:
    """Historical price chart data."""
    coin_id: str
    prices: list[tuple[int, float]]  # (timestamp_ms, price)
    market_caps: list[tuple[int, float]]  # (timestamp_ms, market_cap)
    total_volumes: list[tuple[int, float]]  # (timestamp_ms, volume)


@dataclass
class CoinDetails:
    """Detailed coin information."""
    id: str
    symbol: str
    name: str
    description: str
    market_cap_rank: int | None
    current_price: float
    market_cap: float
    total_volume: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    ath: float  # All-time high
    ath_date: str
    atl: float  # All-time low
    atl_date: str


@dataclass
class TrendingCoin:
    """Trending coin data."""
    id: str
    symbol: str
    name: str
    market_cap_rank: int
    price_btc: float


class CoinGeckoClient:
    """
    CoinGecko API client for cryptocurrency market data.
    
    Features:
    - Real-time price data
    - Historical charts
    - Market statistics
    - Trending coins
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: str | None = None):
        """
        Initialize CoinGecko client.
        
        Args:
            api_key: CoinGecko API key (optional, for higher rate limits)
        """
        self._api_key = api_key
        headers = {}
        if api_key:
            headers["x-cg-pro-api-key"] = api_key
        
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers=headers,
        )
    
    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()
    
    async def get_price(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True,
    ) -> Price:
        """
        Get current price for a coin.
        
        Args:
            coin_id: Coin ID (e.g., "bitcoin", "ethereum")
            vs_currency: Quote currency (default: "usd")
            include_market_cap: Include market cap (default: True)
            include_24hr_vol: Include 24h volume (default: True)
            include_24hr_change: Include 24h change (default: True)
            
        Returns:
            Price with current data
            
        Example:
            >>> price = await client.get_price("ethereum")
            >>> print(f"ETH: ${price.usd:.2f}")
            >>> print(f"24h change: {price.usd_24h_change:.2f}%")
        """
        response = await self._client.get(
            "/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": vs_currency,
                "include_market_cap": str(include_market_cap).lower(),
                "include_24hr_vol": str(include_24hr_vol).lower(),
                "include_24hr_change": str(include_24hr_change).lower(),
            }
        )
        response.raise_for_status()
        data = response.json()
        
        coin_data = data.get(coin_id, {})
        
        return Price(
            coin_id=coin_id,
            symbol=coin_id,  # Symbol not provided in simple/price
            usd=float(coin_data.get(vs_currency, 0)),
            usd_24h_change=coin_data.get(f"{vs_currency}_24h_change"),
            market_cap=coin_data.get(f"{vs_currency}_market_cap"),
            volume_24h=coin_data.get(f"{vs_currency}_24h_vol"),
        )
    
    async def get_prices_bulk(
        self,
        coin_ids: list[str],
        vs_currency: str = "usd",
    ) -> dict[str, Price]:
        """
        Get prices for multiple coins at once.
        
        Args:
            coin_ids: List of coin IDs
            vs_currency: Quote currency (default: "usd")
            
        Returns:
            Dict mapping coin ID to Price
            
        Example:
            >>> prices = await client.get_prices_bulk(["bitcoin", "ethereum", "solana"])
            >>> for coin_id, price in prices.items():
            ...     print(f"{coin_id}: ${price.usd:.2f}")
        """
        ids_str = ",".join(coin_ids)
        response = await self._client.get(
            "/simple/price",
            params={
                "ids": ids_str,
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            }
        )
        response.raise_for_status()
        data = response.json()
        
        prices = {}
        for coin_id, coin_data in data.items():
            prices[coin_id] = Price(
                coin_id=coin_id,
                symbol=coin_id,
                usd=float(coin_data.get(vs_currency, 0)),
                usd_24h_change=coin_data.get(f"{vs_currency}_24h_change"),
                market_cap=coin_data.get(f"{vs_currency}_market_cap"),
                volume_24h=coin_data.get(f"{vs_currency}_24h_vol"),
            )
        
        return prices
    
    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> MarketChart:
        """
        Get historical price chart data.
        
        Args:
            coin_id: Coin ID
            vs_currency: Quote currency (default: "usd")
            days: Number of days (1, 7, 14, 30, 90, 180, 365, max)
            
        Returns:
            MarketChart with historical data
            
        Example:
            >>> chart = await client.get_market_chart("ethereum", days=7)
            >>> prices = [p[1] for p in chart.prices]
            >>> print(f"7-day high: ${max(prices):.2f}")
            >>> print(f"7-day low: ${min(prices):.2f}")
        """
        response = await self._client.get(
            f"/coins/{coin_id}/market_chart",
            params={
                "vs_currency": vs_currency,
                "days": days,
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return MarketChart(
            coin_id=coin_id,
            prices=[(int(ts), float(price)) for ts, price in data.get("prices", [])],
            market_caps=[(int(ts), float(mc)) for ts, mc in data.get("market_caps", [])],
            total_volumes=[(int(ts), float(vol)) for ts, vol in data.get("total_volumes", [])],
        )
    
    async def get_coin_details(self, coin_id: str) -> CoinDetails:
        """
        Get detailed information about a coin.
        
        Args:
            coin_id: Coin ID
            
        Returns:
            CoinDetails with comprehensive data
            
        Example:
            >>> details = await client.get_coin_details("ethereum")
            >>> print(f"{details.name} (#{details.market_cap_rank})")
            >>> print(f"Price: ${details.current_price:.2f}")
            >>> print(f"ATH: ${details.ath:.2f} on {details.ath_date}")
        """
        response = await self._client.get(
            f"/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "false",
                "developer_data": "false",
            }
        )
        response.raise_for_status()
        data = response.json()
        
        market_data = data.get("market_data", {})
        
        return CoinDetails(
            id=data["id"],
            symbol=data["symbol"],
            name=data["name"],
            description=data.get("description", {}).get("en", ""),
            market_cap_rank=data.get("market_cap_rank"),
            current_price=float(market_data.get("current_price", {}).get("usd", 0)),
            market_cap=float(market_data.get("market_cap", {}).get("usd", 0)),
            total_volume=float(market_data.get("total_volume", {}).get("usd", 0)),
            high_24h=float(market_data.get("high_24h", {}).get("usd", 0)),
            low_24h=float(market_data.get("low_24h", {}).get("usd", 0)),
            price_change_24h=float(market_data.get("price_change_24h", 0)),
            price_change_percentage_24h=float(market_data.get("price_change_percentage_24h", 0)),
            ath=float(market_data.get("ath", {}).get("usd", 0)),
            ath_date=market_data.get("ath_date", {}).get("usd", ""),
            atl=float(market_data.get("atl", {}).get("usd", 0)),
            atl_date=market_data.get("atl_date", {}).get("usd", ""),
        )
    
    async def get_trending_coins(self) -> list[TrendingCoin]:
        """
        Get trending coins (top 7).
        
        Returns:
            List of trending coins
            
        Example:
            >>> trending = await client.get_trending_coins()
            >>> for coin in trending:
            ...     print(f"#{coin.market_cap_rank}: {coin.name} ({coin.symbol})")
        """
        response = await self._client.get("/search/trending")
        response.raise_for_status()
        data = response.json()
        
        trending = []
        for item in data.get("coins", []):
            coin_data = item.get("item", {})
            trending.append(
                TrendingCoin(
                    id=coin_data["id"],
                    symbol=coin_data["symbol"],
                    name=coin_data["name"],
                    market_cap_rank=coin_data.get("market_cap_rank", 0),
                    price_btc=float(coin_data.get("price_btc", 0)),
                )
            )
        
        return trending
    
    async def search_coins(self, query: str) -> list[dict]:
        """
        Search for coins by name or symbol.
        
        Args:
            query: Search query
            
        Returns:
            List of matching coins
            
        Example:
            >>> results = await client.search_coins("uni")
            >>> for coin in results[:5]:
            ...     print(f"{coin['name']} ({coin['symbol']})")
        """
        response = await self._client.get(
            "/search",
            params={"query": query}
        )
        response.raise_for_status()
        data = response.json()
        
        return data.get("coins", [])
    
    async def get_global_data(self) -> dict[str, Any]:
        """
        Get global cryptocurrency market data.
        
        Returns:
            Dict with global market statistics
            
        Example:
            >>> global_data = await client.get_global_data()
            >>> print(f"Total market cap: ${global_data['total_market_cap'] / 1e12:.2f}T")
            >>> print(f"BTC dominance: {global_data['btc_dominance']:.1f}%")
        """
        response = await self._client.get("/global")
        response.raise_for_status()
        data = response.json()
        
        market_data = data.get("data", {})
        
        return {
            "total_market_cap": float(market_data.get("total_market_cap", {}).get("usd", 0)),
            "total_volume": float(market_data.get("total_volume", {}).get("usd", 0)),
            "btc_dominance": float(market_data.get("market_cap_percentage", {}).get("btc", 0)),
            "eth_dominance": float(market_data.get("market_cap_percentage", {}).get("eth", 0)),
            "active_cryptocurrencies": market_data.get("active_cryptocurrencies", 0),
            "markets": market_data.get("markets", 0),
        }
