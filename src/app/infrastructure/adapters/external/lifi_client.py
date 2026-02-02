"""
LiFi Cross-Chain Swap API Client.

Provides access to LiFi bridge/swap aggregator:
- Cross-chain swaps and bridges
- Best route finding across 20+ chains
- Multi-protocol aggregation (bridges + DEXes)

API Docs: https://docs.li.fi/
Rate Limit: 100 requests/minute (free)
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LiFiQuote:
    """Cross-chain swap quote from LiFi."""

    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    to_amount_min: str  # Minimum with slippage
    estimated_gas: str
    bridge_name: str | None  # Bridge used (e.g., "stargate", "hop")
    execution_duration: int  # Estimated seconds
    fee_costs: list[dict]


@dataclass
class LiFiRoute:
    """Complete route for cross-chain swap."""

    id: str
    from_chain_id: int
    to_chain_id: int
    from_token: dict
    to_token: dict
    from_amount: str
    to_amount: str
    steps: list[dict]  # Swap/bridge steps
    gas_cost_usd: float
    bridge: str | None


# Chain IDs supported by LiFi
LIFI_CHAINS = {
    "ethereum": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "optimism": 10,
    "base": 8453,
    "bsc": 56,
    "avalanche": 43114,
    "fantom": 250,
    "gnosis": 100,
    "zksync": 324,
    # Hyperliquid chains
    "hyperliquid": 1337,  # HyperCore (perps/spot)
    "hpl": 1337,          # Alias for hyperliquid
    "hyperevm": 999,      # HyperEVM (smart contracts)
    "hyp": 999,           # Alias for hyperevm
}

# Common token addresses
# LiFi uses 0xEeee...eE for native ETH (not zero address)
NATIVE_ETH_ADDRESS = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

LIFI_TOKENS = {
    "ethereum": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    },
    "polygon": {
        "MATIC": NATIVE_ETH_ADDRESS,
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    },
    "arbitrum": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
    },
    "base": {
        "ETH": NATIVE_ETH_ADDRESS,
        "WETH": "0x4200000000000000000000000000000000000006",
        "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    },
    # Hyperliquid tokens (chain 1337 - HyperCore)
    "hyperliquid": {
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",       # USDC (Perps)
        "USDC_PERPS": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", # USDC (Perps) alias
        "USDC_SPOT": "0x6d1e7cde53bA9467B783Cb7c530CE05400000000",  # USDC (Spot)
    },
    "hpl": {
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDC_PERPS": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDC_SPOT": "0x6d1e7cde53bA9467B783Cb7c530CE05400000000",
    },
}


class LiFiClient:
    """
    LiFi API client for cross-chain swaps and bridges.

    Features:
    - Cross-chain token swaps
    - Bridge aggregation (Stargate, Hop, Across, etc.)
    - Best route finding
    - Multi-chain support (20+ chains)
    """

    BASE_URL = "https://li.quest/v1"

    def __init__(self, api_key: str | None = None):
        """
        Initialize LiFi client.

        Args:
            api_key: Optional API key for higher rate limits
        """
        self._api_key = api_key
        headers = {"Accept": "application/json"}
        if api_key:
            headers["x-lifi-api-key"] = api_key

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers=headers,
        )

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def get_quote(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str | None = None,
        slippage: float = 0.5,
    ) -> LiFiQuote:
        """
        Get cross-chain swap quote.

        Args:
            from_chain: Source chain (e.g., "ethereum", "base")
            to_chain: Destination chain
            from_token: Source token address or symbol
            to_token: Destination token address or symbol
            from_amount: Amount in wei/smallest unit
            from_address: User address (for more accurate quotes)
            slippage: Slippage tolerance (percent, default: 0.5)

        Returns:
            LiFiQuote with route details

        Example:
            >>> quote = await client.get_quote(
            ...     from_chain="ethereum",
            ...     to_chain="base",
            ...     from_token="USDC",
            ...     to_token="USDC",
            ...     from_amount="1000000000",  # 1000 USDC
            ... )
        """
        # Resolve chain IDs
        from_chain_id = LIFI_CHAINS.get(from_chain.lower(), 1)
        to_chain_id = LIFI_CHAINS.get(to_chain.lower(), 8453)

        # Resolve token addresses
        from_token_addr = self._resolve_token(from_token, from_chain)
        to_token_addr = self._resolve_token(to_token, to_chain)

        params = {
            "fromChain": from_chain_id,
            "toChain": to_chain_id,
            "fromToken": from_token_addr,
            "toToken": to_token_addr,
            "fromAmount": from_amount,
            "slippage": slippage / 100,  # LiFi expects decimal
        }

        if from_address:
            params["fromAddress"] = from_address

        try:
            response = await self._client.get("/quote", params=params)
            response.raise_for_status()
            data = response.json()

            # Extract bridge name if cross-chain
            bridge_name = None
            if data.get("includedSteps"):
                for step in data["includedSteps"]:
                    if step.get("type") == "cross":
                        bridge_name = step.get("tool")
                        break

            return LiFiQuote(
                from_chain=from_chain,
                to_chain=to_chain,
                from_token=from_token,
                to_token=to_token,
                from_amount=from_amount,
                to_amount=data.get("estimate", {}).get("toAmount", "0"),
                to_amount_min=data.get("estimate", {}).get("toAmountMin", "0"),
                estimated_gas=data.get("estimate", {}).get("gasCosts", [{}])[0].get(
                    "amount", "0"
                ),
                bridge_name=bridge_name,
                execution_duration=data.get("estimate", {}).get(
                    "executionDuration", 0
                ),
                fee_costs=data.get("estimate", {}).get("feeCosts", []),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"LiFi API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LiFi request failed: {e}")
            raise

    async def get_routes(
        self,
        from_chain: str,
        to_chain: str,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str | None = None,
    ) -> list[LiFiRoute]:
        """
        Get multiple route options for cross-chain swap.

        Args:
            from_chain: Source chain
            to_chain: Destination chain
            from_token: Source token
            to_token: Destination token
            from_amount: Amount in smallest unit
            from_address: User address

        Returns:
            List of LiFiRoute options sorted by output amount
        """
        from_chain_id = LIFI_CHAINS.get(from_chain.lower(), 1)
        to_chain_id = LIFI_CHAINS.get(to_chain.lower(), 8453)
        from_token_addr = self._resolve_token(from_token, from_chain)
        to_token_addr = self._resolve_token(to_token, to_chain)

        payload = {
            "fromChainId": from_chain_id,
            "toChainId": to_chain_id,
            "fromTokenAddress": from_token_addr,
            "toTokenAddress": to_token_addr,
            "fromAmount": from_amount,
        }

        if from_address:
            payload["fromAddress"] = from_address

        try:
            response = await self._client.post("/advanced/routes", json=payload)
            response.raise_for_status()
            data = response.json()

            routes = []
            for route in data.get("routes", []):
                # Get bridge name from steps
                bridge = None
                for step in route.get("steps", []):
                    if step.get("type") == "cross":
                        bridge = step.get("tool")
                        break

                routes.append(
                    LiFiRoute(
                        id=route.get("id", ""),
                        from_chain_id=from_chain_id,
                        to_chain_id=to_chain_id,
                        from_token=route.get("fromToken", {}),
                        to_token=route.get("toToken", {}),
                        from_amount=from_amount,
                        to_amount=route.get("toAmount", "0"),
                        steps=route.get("steps", []),
                        gas_cost_usd=float(route.get("gasCostUSD", 0)),
                        bridge=bridge,
                    )
                )

            return routes

        except Exception as e:
            logger.error(f"LiFi routes request failed: {e}")
            return []

    async def get_chains(self) -> list[dict]:
        """Get list of supported chains."""
        try:
            response = await self._client.get("/chains")
            response.raise_for_status()
            return response.json().get("chains", [])
        except Exception as e:
            logger.error(f"Failed to get LiFi chains: {e}")
            return []

    async def get_tokens(self, chain: str | None = None) -> list[dict]:
        """
        Get supported tokens.

        Args:
            chain: Filter by chain (optional)
        """
        try:
            params = {}
            if chain:
                chain_id = LIFI_CHAINS.get(chain.lower())
                if chain_id:
                    params["chains"] = str(chain_id)

            response = await self._client.get("/tokens", params=params)
            response.raise_for_status()
            return response.json().get("tokens", {})
        except Exception as e:
            logger.error(f"Failed to get LiFi tokens: {e}")
            return []

    def _resolve_token(self, token: str, chain: str) -> str:
        """Resolve token symbol to address."""
        if token.startswith("0x"):
            return token

        chain_tokens = LIFI_TOKENS.get(chain.lower(), {})
        return chain_tokens.get(token.upper(), token)
