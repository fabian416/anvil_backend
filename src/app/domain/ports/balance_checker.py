"""
Balance Checker Port.

Defines the domain interface for checking wallet balances before transaction execution.
This is critical for UX - prevents showing approval UI for transactions user can't afford.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Protocol


class IBalanceChecker(Protocol):
    """
    Port interface for checking wallet token balances.

    This protocol defines the contract for validating that a wallet
    has sufficient balance before generating execute_data for transactions.

    Critical for UX:
    - Prevents showing approval UI for unaffordable transactions
    - Provides clear error messages when balance is insufficient
    - Checks both token balance and gas (native token) availability
    """

    async def check_balance(
        self,
        wallet_address: str,
        token_address: str,
        required_amount: Decimal,
        chain: str = "ethereum",
    ) -> bool:
        """
        Check if wallet has sufficient token balance for a transaction.

        Args:
            wallet_address: Wallet address to check (0x...)
            token_address: Token contract address (0x...) or "native" for ETH/native token
            required_amount: Required amount in token units (e.g., 1000.0 for 1000 USDC)
            chain: Blockchain name (ethereum, base, arbitrum, polygon, optimism)

        Returns:
            True if wallet has sufficient balance, False otherwise

        Example:
            >>> checker = PortfolioBalanceChecker(portfolio_service)
            >>> has_balance = await checker.check_balance(
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            ...     required_amount=Decimal("1000.0"),
            ...     chain="ethereum",
            ... )
            >>> if not has_balance:
            ...     return ErrorResponse("Insufficient USDC balance")
        """
        ...

    async def get_balance(
        self,
        wallet_address: str,
        token_address: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get current token balance for a wallet.

        Args:
            wallet_address: Wallet address to check (0x...)
            token_address: Token contract address (0x...) or "native" for ETH/native token
            chain: Blockchain name (ethereum, base, arbitrum, polygon, optimism)

        Returns:
            Current balance in token units (e.g., 1000.0 for 1000 USDC)

        Example:
            >>> balance = await checker.get_balance(
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
            ...     chain="ethereum",
            ... )
            >>> print(f"Current balance: {balance} USDC")
        """
        ...

    async def check_gas_balance(
        self,
        wallet_address: str,
        chain: str = "ethereum",
        min_gas_amount: Decimal | None = None,
    ) -> bool:
        """
        Check if wallet has sufficient native token for gas fees.

        Args:
            wallet_address: Wallet address to check (0x...)
            chain: Blockchain name (ethereum, base, arbitrum, polygon, optimism)
            min_gas_amount: Minimum required gas amount (default: 0.01 ETH or chain equivalent)

        Returns:
            True if wallet has sufficient gas, False otherwise

        Example:
            >>> has_gas = await checker.check_gas_balance(
            ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            ...     chain="ethereum",
            ... )
            >>> if not has_gas:
            ...     return ErrorResponse("Insufficient ETH for gas fees")
        """
        ...
