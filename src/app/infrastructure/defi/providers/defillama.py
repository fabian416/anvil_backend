"""
DeFiLlama API client for protocol analytics.
"""

import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

import httpx

logger = logging.getLogger(__name__)


class DeFiLlamaClient:
    """
    Client for DeFiLlama API.

    Provides protocol TVL, yields, and analytics.
    """

    BASE_URL = "https://api.llama.fi"
    YIELDS_URL = "https://yields.llama.fi"

    def __init__(self):
        """Initialize DeFiLlama client."""
        self._client = httpx.AsyncClient(
            timeout=30.0,
        )

    async def get_protocol_tvl(self, protocol: str) -> Dict[str, Any]:
        """
        Get TVL data for a specific protocol.

        Args:
            protocol: Protocol slug (e.g., "aave", "uniswap")

        Returns:
            Protocol TVL data including current TVL and history
        """
        try:
            response = await self._client.get(f"{self.BASE_URL}/protocol/{protocol}")
            response.raise_for_status()

            data = response.json()

            # Extract current TVL
            current_tvl = data.get("tvl", [])
            if current_tvl and isinstance(current_tvl, list):
                latest = current_tvl[-1]
                current_tvl_usd = latest.get("totalLiquidityUSD", 0)
            else:
                current_tvl_usd = data.get("currentChainTvls", {}).get("All", 0)

            return {
                "protocol": data.get("name", protocol),
                "slug": data.get("slug", protocol),
                "current_tvl_usd": current_tvl_usd,
                "category": data.get("category", "Unknown"),
                "chains": data.get("chains", []),
                "url": data.get("url", ""),
                "description": data.get("description", ""),
            }

        except httpx.HTTPError as e:
            logger.error(f"DeFiLlama protocol TVL error: {e}")
            raise

    async def get_all_protocols(self) -> List[Dict[str, Any]]:
        """
        Get list of all protocols with TVL.

        Returns:
            List of protocols with basic info and TVL
        """
        try:
            response = await self._client.get(f"{self.BASE_URL}/protocols")
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"DeFiLlama protocols list error: {e}")
            raise

    async def get_top_protocols(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top protocols by TVL.

        Args:
            limit: Number of protocols to return

        Returns:
            List of top protocols sorted by TVL
        """
        try:
            all_protocols = await self.get_all_protocols()

            # Sort by TVL
            sorted_protocols = sorted(
                all_protocols, key=lambda x: x.get("tvl", 0), reverse=True
            )

            return sorted_protocols[:limit]

        except Exception as e:
            logger.error(f"Error getting top protocols: {e}")
            raise

    async def get_protocol_yields(
        self,
        protocol: Optional[str] = None,
        chain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get yield opportunities.

        Args:
            protocol: Filter by protocol slug
            chain: Filter by chain name

        Returns:
            List of yield pools
        """
        try:
            response = await self._client.get(f"{self.YIELDS_URL}/pools")
            response.raise_for_status()

            data = response.json()
            pools = data.get("data", [])

            # Filter if needed
            if protocol:
                pools = [p for p in pools if p.get("project") == protocol]

            if chain:
                pools = [p for p in pools if p.get("chain") == chain]

            # Sort by APY
            pools = sorted(pools, key=lambda x: x.get("apy", 0), reverse=True)

            return pools[:50]  # Limit to top 50

        except httpx.HTTPError as e:
            logger.error(f"DeFiLlama yields error: {e}")
            raise

    async def get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """
        Get TVL for a specific chain.

        Args:
            chain: Chain name (e.g., "Ethereum", "Polygon")

        Returns:
            Chain TVL data
        """
        try:
            response = await self._client.get(f"{self.BASE_URL}/charts/{chain}")
            response.raise_for_status()

            data = response.json()

            # Get latest TVL
            if data and isinstance(data, list) and len(data) > 0:
                latest = data[-1]
                return {
                    "chain": chain,
                    "tvl_usd": latest.get("totalLiquidityUSD", 0),
                    "timestamp": latest.get("date", 0),
                }

            return {
                "chain": chain,
                "tvl_usd": 0,
                "timestamp": 0,
            }

        except httpx.HTTPError as e:
            logger.error(f"DeFiLlama chain TVL error: {e}")
            raise

    async def search_protocol(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for protocols by name.

        Args:
            query: Search query

        Returns:
            List of matching protocols
        """
        try:
            all_protocols = await self.get_all_protocols()

            # Simple search by name
            query_lower = query.lower()
            matches = [
                p
                for p in all_protocols
                if query_lower in p.get("name", "").lower()
                or query_lower in p.get("slug", "").lower()
            ]

            return matches[:10]  # Top 10 matches

        except Exception as e:
            logger.error(f"Error searching protocols: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class DeFiLlamaError(Exception):
    """DeFiLlama API error."""

    pass
