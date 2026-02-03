"""
1inch DEX Aggregator Client

Integration with 1inch API for:
- Token prices
- Swap quotes
- Liquidity sources
- Protocol analytics
"""

from typing import List, Dict, Any, Optional
import httpx
import logging
from datetime import datetime, UTC

from app.domain.ports.external_data.defi_data_provider import (
    TokenData,
)

logger = logging.getLogger(__name__)


class OneInchClient:
    """
    1inch DEX aggregator client.

    Features:
    - Token prices across chains
    - Swap quotes with best routes
    - Liquidity source analytics
    - Protocol statistics

    Supported Chains:
    - Ethereum (1)
    - BSC (56)
    - Polygon (137)
    - Arbitrum (42161)
    - Optimism (10)
    - Avalanche (43114)
    """

    BASE_URL = "https://api.1inch.dev"

    CHAIN_IDS = {
        "ethereum": 1,
        "bsc": 56,
        "polygon": 137,
        "arbitrum": 42161,
        "optimism": 10,
        "avalanche": 43114,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize 1inch client.

        Args:
            api_key: 1inch API key
            timeout: Request timeout in seconds
        """
        self._api_key = api_key
        self._timeout = timeout

        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=headers,
            timeout=timeout,
        )

    async def get_token_price(
        self,
        token_address: str,
        chain: str = "ethereum",
    ) -> float:
        """
        Get token price in USD.

        Args:
            token_address: Token contract address
            chain: Chain name

        Returns:
            Token price in USD
        """
        chain_id = self.CHAIN_IDS.get(chain, 1)

        try:
            response = await self._client.get(f"/price/v1.1/{chain_id}/{token_address}")
            response.raise_for_status()

            data = response.json()
            return float(data.get(token_address, 0))

        except httpx.HTTPError as e:
            logger.error(f"1inch price request failed: {e}")
            return 0.0

    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: int,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Get swap quote with best route.

        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in token decimals)
            chain: Chain name

        Returns:
            Swap quote with route and estimated output
        """
        chain_id = self.CHAIN_IDS.get(chain, 1)

        params = {
            "src": from_token,
            "dst": to_token,
            "amount": str(amount),
        }

        try:
            response = await self._client.get(
                f"/swap/v5.2/{chain_id}/quote",
                params=params,
            )
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"1inch quote request failed: {e}")
            return {}

    async def get_liquidity_sources(
        self,
        chain: str = "ethereum",
    ) -> List[Dict[str, Any]]:
        """
        Get available liquidity sources.

        Args:
            chain: Chain name

        Returns:
            List of liquidity sources (DEXes)
        """
        chain_id = self.CHAIN_IDS.get(chain, 1)

        try:
            response = await self._client.get(
                f"/swap/v5.2/{chain_id}/liquidity-sources"
            )
            response.raise_for_status()

            data = response.json()
            return data.get("protocols", [])

        except httpx.HTTPError as e:
            logger.error(f"1inch liquidity sources request failed: {e}")
            return []

    async def get_tokens(
        self,
        chain: str = "ethereum",
    ) -> Dict[str, TokenData]:
        """
        Get all supported tokens.

        Args:
            chain: Chain name

        Returns:
            Dictionary of token address -> TokenData
        """
        chain_id = self.CHAIN_IDS.get(chain, 1)

        try:
            response = await self._client.get(f"/swap/v5.2/{chain_id}/tokens")
            response.raise_for_status()

            data = response.json()
            tokens = data.get("tokens", {})

            result = {}
            for address, info in tokens.items():
                result[address] = TokenData(
                    address=address,
                    symbol=info.get("symbol", ""),
                    name=info.get("name", ""),
                    decimals=info.get("decimals", 18),
                    price_usd=0.0,  # Need separate price call
                    market_cap=0.0,
                    volume_24h=0.0,
                    chain=chain,
                )

            return result

        except httpx.HTTPError as e:
            logger.error(f"1inch tokens request failed: {e}")
            return {}

    async def get_protocol_analytics(
        self,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Get protocol-level analytics.

        Args:
            chain: Chain name

        Returns:
            Protocol analytics (volume, transactions, etc.)
        """
        # Get liquidity sources as proxy for analytics
        sources = await self.get_liquidity_sources(chain)

        total_volume = 0.0
        protocol_count = len(sources)

        return {
            "chain": chain,
            "protocol_count": protocol_count,
            "total_volume_24h": total_volume,  # Not in API
            "liquidity_sources": sources,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def get_best_route(
        self,
        from_token: str,
        to_token: str,
        amount: int,
        chain: str = "ethereum",
    ) -> List[Dict[str, Any]]:
        """
        Get best swap route with splits.

        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap
            chain: Chain name

        Returns:
            List of route splits
        """
        quote = await self.get_swap_quote(
            from_token,
            to_token,
            amount,
            chain,
        )

        if not quote:
            return []

        # Parse protocols used in route
        protocols = quote.get("protocols", [])

        routes = []
        for protocol_group in protocols:
            for protocol in protocol_group:
                routes.append({
                    "protocol": protocol.get("name"),
                    "from_token": protocol.get("fromTokenAddress"),
                    "to_token": protocol.get("toTokenAddress"),
                    "part": protocol.get("part", 100),  # Percentage
                })

        return routes

    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()
