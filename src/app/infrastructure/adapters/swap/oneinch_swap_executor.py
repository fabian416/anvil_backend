"""
1inch Swap Executor Adapter.

Implements ISwapExecutor port using 1inch MCP server for token swaps.
Provides swap quotes and execute_data for leverage loop operations.
"""

import logging
from decimal import Decimal
from typing import Any

from app.domain.ports.swap_executor import ISwapExecutor
from app.infrastructure.mcp.mcp_client import MCPClient

logger = logging.getLogger(__name__)


class OneInchSwapExecutor(ISwapExecutor):
    """
    Swap executor adapter using 1inch MCP server (port 8082).

    Implements ISwapExecutor port for token swaps via 1inch DEX aggregator.
    1inch provides best swap routes across multiple DEXes with optimal pricing.

    Features:
    - Best swap rates via DEX aggregation
    - Automatic route optimization
    - Slippage protection
    - Gas estimation
    - Multi-chain support

    Supported chains:
    - Ethereum (1)
    - Base (8453)
    - Arbitrum (42161)
    - Polygon (137)
    - Optimism (10)
    """

    # 1inch MCP server configuration
    MCP_BASE_URL = "http://localhost:8082"

    # Chain ID mapping
    CHAIN_IDS = {
        "ethereum": 1,
        "base": 8453,
        "arbitrum": 42161,
        "polygon": 137,
        "optimism": 10,
        "avalanche": 43114,
    }

    # Common token addresses by chain
    TOKEN_ADDRESSES = {
        "ethereum": {
            "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # Native ETH
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        },
        "base": {
            "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "WETH": "0x4200000000000000000000000000000000000006",
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        },
        "arbitrum": {
            "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
            "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        },
    }

    # Token decimals
    TOKEN_DECIMALS = {
        "ETH": 18,
        "WETH": 18,
        "USDC": 6,
        "USDT": 6,
        "DAI": 18,
        "WBTC": 8,
    }

    __slots__ = ("_mcp_client",)

    def __init__(self, mcp_client: MCPClient):
        """
        Initialize 1inch swap executor.

        Args:
            mcp_client: MCP client for calling 1inch server
        """
        self._mcp_client = mcp_client

    async def get_swap_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        chain: str = "ethereum",
        slippage: Decimal = Decimal("0.01"),
    ) -> dict:
        """
        Get swap quote from 1inch.

        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            chain: Blockchain network
            slippage: Slippage tolerance (0.01 = 1%)

        Returns:
            Quote dictionary with swap details

        Raises:
            ValueError: If swap not available or quote fails
        """
        logger.info(
            f"Getting 1inch swap quote: {amount_in} {token_in} → {token_out} "
            f"on {chain} (slippage: {slippage})"
        )

        try:
            # Get token addresses
            token_in_address = self._get_token_address(token_in, chain)
            token_out_address = self._get_token_address(token_out, chain)

            # Get chain ID
            chain_id = self.CHAIN_IDS.get(chain.lower())
            if not chain_id:
                raise ValueError(f"Unsupported chain: {chain}")

            # Convert amount to smallest units (wei)
            token_in_decimals = self.TOKEN_DECIMALS.get(token_in.upper(), 18)
            amount_in_wei = int(amount_in * Decimal(10 ** token_in_decimals))

            # Call 1inch MCP quote tool
            quote_response = await self._mcp_client.call_tool(
                server_url=self.MCP_BASE_URL,
                tool_name="get_swap_quote",
                arguments={
                    "chain_id": chain_id,
                    "src": token_in_address,
                    "dst": token_out_address,
                    "amount": str(amount_in_wei),
                    "slippage": float(slippage * 100),  # Convert to percentage
                },
            )

            # Parse response
            token_out_decimals = self.TOKEN_DECIMALS.get(token_out.upper(), 18)
            amount_out = Decimal(quote_response["dst_amount"]) / Decimal(
                10 ** token_out_decimals
            )

            # Calculate rate
            rate = amount_out / amount_in if amount_in > 0 else Decimal("0")

            # Calculate price impact
            price_impact = Decimal(quote_response.get("price_impact", "0"))

            # Calculate minimum output with slippage
            min_amount_out = amount_out * (Decimal("1") - slippage)

            # Estimate gas cost
            gas_estimate = Decimal(quote_response.get("gas", "0"))
            gas_estimate_eth = gas_estimate / Decimal(10**18)  # Convert to ETH

            logger.info(
                f"1inch quote: {amount_in} {token_in} → {amount_out} {token_out} "
                f"(rate: {rate}, impact: {price_impact}%)"
            )

            return {
                "amount_out": amount_out,
                "rate": rate,
                "price_impact": price_impact,
                "min_amount_out": min_amount_out,
                "gas_estimate": gas_estimate_eth,
                "gas_estimate_usd": Decimal("0"),  # TODO: Calculate from price
                "route": quote_response.get("protocols", []),
                "raw_quote": quote_response,
            }

        except Exception as e:
            logger.error(f"Failed to get 1inch quote: {type(e).__name__}: {e}")
            raise ValueError(f"Failed to get swap quote: {e}") from e

    async def build_swap_execute_data(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        min_amount_out: Decimal,
        chain: str = "ethereum",
    ) -> dict:
        """
        Build execute_data for Privy swap execution.

        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            min_amount_out: Minimum output with slippage
            chain: Blockchain network

        Returns:
            Execute data dictionary for Privy

        Raises:
            ValueError: If swap cannot be built
        """
        logger.info(
            f"Building 1inch swap execute_data: {amount_in} {token_in} → "
            f"{token_out} (min: {min_amount_out}) on {chain}"
        )

        try:
            # Get token addresses
            token_in_address = self._get_token_address(token_in, chain)
            token_out_address = self._get_token_address(token_out, chain)

            # Get chain ID
            chain_id = self.CHAIN_IDS.get(chain.lower())
            if not chain_id:
                raise ValueError(f"Unsupported chain: {chain}")

            # Convert amounts to wei
            token_in_decimals = self.TOKEN_DECIMALS.get(token_in.upper(), 18)
            token_out_decimals = self.TOKEN_DECIMALS.get(token_out.upper(), 18)

            amount_in_wei = int(amount_in * Decimal(10 ** token_in_decimals))
            min_amount_out_wei = int(min_amount_out * Decimal(10 ** token_out_decimals))

            # Build execute_data following SwapHandlerV2 pattern
            execute_data = {
                "action_type": "swap",
                "provider": "1inch",
                "protocol": "1inch_v5",
                "chain": chain,
                "chain_id": chain_id,
                "from_token": token_in,
                "to_token": token_out,
                "from_token_address": token_in_address,
                "to_token_address": token_out_address,
                "from_amount": str(amount_in),
                "from_amount_wei": str(amount_in_wei),
                "to_amount_min": str(min_amount_out),
                "to_amount_min_wei": str(min_amount_out_wei),
                # Note: Actual calldata and contract address would be fetched from 1inch API
                # For MVP, we provide the structure that Privy needs
                "requires_approval": True,
            }

            logger.info(f"Built 1inch execute_data for {token_in} → {token_out}")

            return execute_data

        except Exception as e:
            logger.error(f"Failed to build swap execute_data: {type(e).__name__}: {e}")
            raise ValueError(f"Failed to build swap execute_data: {e}") from e

    async def get_supported_tokens(
        self,
        chain: str = "ethereum",
    ) -> set[str]:
        """
        Get supported tokens for swaps on chain.

        Args:
            chain: Blockchain network

        Returns:
            Set of supported token symbols
        """
        chain_tokens = self.TOKEN_ADDRESSES.get(chain.lower(), {})
        return set(chain_tokens.keys())

    async def validate_swap_route(
        self,
        token_in: str,
        token_out: str,
        chain: str = "ethereum",
    ) -> bool:
        """
        Validate if swap route exists.

        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            chain: Blockchain network

        Returns:
            True if swap route exists
        """
        try:
            # Check if both tokens are supported
            supported_tokens = await self.get_supported_tokens(chain)
            return (
                token_in.upper() in supported_tokens
                and token_out.upper() in supported_tokens
            )
        except Exception as e:
            logger.error(f"Failed to validate swap route: {e}")
            return False

    def _get_token_address(self, token_symbol: str, chain: str) -> str:
        """
        Get token contract address for symbol.

        Args:
            token_symbol: Token symbol (ETH, USDC, etc.)
            chain: Blockchain network

        Returns:
            Token contract address

        Raises:
            ValueError: If token not found
        """
        chain_tokens = self.TOKEN_ADDRESSES.get(chain.lower(), {})
        token_address = chain_tokens.get(token_symbol.upper())

        if not token_address:
            raise ValueError(
                f"Token {token_symbol} not supported on {chain}. "
                f"Supported: {list(chain_tokens.keys())}"
            )

        return token_address
