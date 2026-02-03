"""
Swap Executor Port.

Defines the domain interface for executing token swaps during leverage loops.
This port abstracts swap execution from specific DEX aggregators (1inch, Hyperliquid, etc.).
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class ISwapExecutor(Protocol):
    """
    Port interface for executing token swaps during leverage loops.

    This protocol defines the contract for getting swap quotes and building
    execute_data for token swaps. Implementations may use different DEX
    aggregators (1inch, Hyperliquid, Uniswap, etc.).

    Critical for leverage loops:
    - Must support swaps between stablecoins (USDC/USDT/DAI) and collateral (ETH/WETH)
    - Must calculate accurate slippage protection
    - Must generate valid execute_data for Privy SDK execution
    """

    async def get_swap_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        chain: str = "ethereum",
        slippage: Decimal = Decimal("0.01"),
    ) -> dict:
        """
        Get swap quote with expected output and price impact.

        Args:
            token_in: Input token symbol (e.g., "USDC")
            token_out: Output token symbol (e.g., "ETH")
            amount_in: Input amount in token units
            chain: Blockchain network (ethereum, base, arbitrum, etc.)
            slippage: Acceptable slippage tolerance (0.01 = 1%)

        Returns:
            Dictionary containing:
                - amount_out: Expected output amount
                - rate: Exchange rate (1 token_in = X token_out)
                - price_impact: Price impact percentage
                - min_amount_out: Minimum output with slippage protection
                - gas_estimate: Estimated gas cost in native token
                - route: Swap route (for multi-hop swaps)

        Raises:
            ValueError: If swap route not available or liquidity insufficient

        Example:
            >>> quote = await executor.get_swap_quote(
            ...     token_in="USDC",
            ...     token_out="ETH",
            ...     amount_in=Decimal("2000.0"),
            ...     chain="ethereum",
            ...     slippage=Decimal("0.01"),
            ... )
            >>> print(f"Expected output: {quote['amount_out']} ETH")
            >>> print(f"Price impact: {quote['price_impact']}%")
        """
        ...

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

        This method generates the transaction data needed for the Privy SDK
        to execute the swap. The execute_data format follows the established
        pattern used in SwapHandlerV2.

        Args:
            token_in: Input token symbol (e.g., "USDC")
            token_out: Output token symbol (e.g., "ETH")
            amount_in: Input amount in token units
            min_amount_out: Minimum acceptable output amount (slippage protected)
            chain: Blockchain network

        Returns:
            Dictionary containing execute_data for Privy:
                {
                    "action_type": "swap",
                    "provider": "1inch",  # or "hyperliquid", "uniswap", etc.
                    "from_token": "USDC",
                    "to_token": "ETH",
                    "from_amount": "2000.0",
                    "to_amount_min": "0.54",
                    "chain": "ethereum",
                    "dex_contract": "0x...",
                    "calldata": "0x...",
                    "value": "0",  # Native token value
                }

        Raises:
            ValueError: If swap cannot be built

        Example:
            >>> execute_data = await executor.build_swap_execute_data(
            ...     token_in="USDC",
            ...     token_out="ETH",
            ...     amount_in=Decimal("2000.0"),
            ...     min_amount_out=Decimal("0.54"),
            ...     chain="ethereum",
            ... )
            >>> # Frontend uses this to execute swap via Privy
        """
        ...

    async def get_supported_tokens(
        self,
        chain: str = "ethereum",
    ) -> set[str]:
        """
        Get list of supported tokens for swaps on a given chain.

        Args:
            chain: Blockchain network

        Returns:
            Set of supported token symbols

        Example:
            >>> tokens = await executor.get_supported_tokens("ethereum")
            >>> print(tokens)
            {'ETH', 'USDC', 'USDT', 'DAI', 'WETH', 'WBTC', ...}
        """
        ...

    async def validate_swap_route(
        self,
        token_in: str,
        token_out: str,
        chain: str = "ethereum",
    ) -> bool:
        """
        Validate if a swap route exists between two tokens.

        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            chain: Blockchain network

        Returns:
            True if swap route exists with sufficient liquidity

        Example:
            >>> is_valid = await executor.validate_swap_route(
            ...     token_in="USDC",
            ...     token_out="ETH",
            ...     chain="ethereum",
            ... )
            >>> if not is_valid:
            ...     raise ValueError("No swap route available for USDC → ETH")
        """
        ...
