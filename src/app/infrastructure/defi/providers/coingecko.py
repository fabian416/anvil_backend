"""
CoinGecko API client for price feeds and market data.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """
    Client for CoinGecko API.

    Provides real-time price data and market information.
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    # Common token ID mappings
    TOKEN_IDS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDC": "usd-coin",
        "USDT": "tether",
        "DAI": "dai",
        "WBTC": "wrapped-bitcoin",
        "UNI": "uniswap",
        "LINK": "chainlink",
        "AAVE": "aave",
        "MATIC": "matic-network",
        "ARB": "arbitrum",
        "OP": "optimism",
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize CoinGecko client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self.api_key = api_key

        headers = {}
        if api_key:
            headers["x-cg-pro-api-key"] = api_key

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=30.0,
        )

    async def get_price(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        include_24h_change: bool = True,
    ) -> Dict[str, Any]:
        """
        Get current price for a coin.

        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin", "ethereum")
            vs_currency: Currency to price in (default "usd")
            include_24h_change: Include 24h price change

        Returns:
            Price data including current price and 24h change
        """
        try:
            params = {
                "ids": coin_id,
                "vs_currencies": vs_currency,
            }

            if include_24h_change:
                params["include_24hr_change"] = "true"

            response = await self._client.get(
                "/simple/price",
                params=params,
            )
            response.raise_for_status()

            data = response.json()

            if coin_id not in data:
                raise ValueError(f"Coin {coin_id} not found")

            coin_data = data[coin_id]

            return {
                "coin_id": coin_id,
                "price": coin_data.get(vs_currency, 0),
                "currency": vs_currency,
                "change_24h": coin_data.get(f"{vs_currency}_24h_change", 0),
            }

        except httpx.HTTPError as e:
            logger.error(f"CoinGecko price error: {e}")
            raise

    async def get_multiple_prices(
        self,
        coin_ids: List[str],
        vs_currency: str = "usd",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get prices for multiple coins at once.

        Args:
            coin_ids: List of CoinGecko coin IDs
            vs_currency: Currency to price in

        Returns:
            Dictionary mapping coin_id -> price data
        """
        try:
            response = await self._client.get(
                "/simple/price",
                params={
                    "ids": ",".join(coin_ids),
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                },
            )
            response.raise_for_status()

            data = response.json()

            result = {}
            for coin_id, coin_data in data.items():
                result[coin_id] = {
                    "price": coin_data.get(vs_currency, 0),
                    "change_24h": coin_data.get(f"{vs_currency}_24h_change", 0),
                    "market_cap": coin_data.get(f"{vs_currency}_market_cap", 0),
                }

            return result

        except httpx.HTTPError as e:
            logger.error(f"CoinGecko multiple prices error: {e}")
            raise

    async def get_coin_info(self, coin_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a coin.

        Args:
            coin_id: CoinGecko coin ID

        Returns:
            Detailed coin information
        """
        try:
            response = await self._client.get(
                f"/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "community_data": "false",
                    "developer_data": "false",
                },
            )
            response.raise_for_status()

            data = response.json()

            market_data = data.get("market_data", {})

            return {
                "coin_id": coin_id,
                "name": data.get("name", ""),
                "symbol": data.get("symbol", "").upper(),
                "current_price": market_data.get("current_price", {}).get("usd", 0),
                "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                "total_volume": market_data.get("total_volume", {}).get("usd", 0),
                "high_24h": market_data.get("high_24h", {}).get("usd", 0),
                "low_24h": market_data.get("low_24h", {}).get("usd", 0),
                "price_change_24h": market_data.get("price_change_24h", 0),
                "price_change_percentage_24h": market_data.get(
                    "price_change_percentage_24h", 0
                ),
            }

        except httpx.HTTPError as e:
            logger.error(f"CoinGecko coin info error: {e}")
            raise

    async def search_coins(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for coins by name or symbol.

        Args:
            query: Search query

        Returns:
            List of matching coins
        """
        try:
            response = await self._client.get(
                "/search",
                params={"query": query},
            )
            response.raise_for_status()

            data = response.json()
            coins = data.get("coins", [])

            return [
                {
                    "id": coin.get("id"),
                    "name": coin.get("name"),
                    "symbol": coin.get("symbol"),
                    "market_cap_rank": coin.get("market_cap_rank"),
                }
                for coin in coins[:10]  # Top 10 results
            ]

        except httpx.HTTPError as e:
            logger.error(f"CoinGecko search error: {e}")
            raise

    def resolve_token_symbol(self, symbol: str) -> Optional[str]:
        """
        Resolve token symbol to CoinGecko coin ID.

        Args:
            symbol: Token symbol (e.g., "BTC", "ETH")

        Returns:
            CoinGecko coin ID or None
        """
        return self.TOKEN_IDS.get(symbol.upper())

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class CoinGeckoError(Exception):
    """CoinGecko API error."""

    pass
