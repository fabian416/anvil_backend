"""
Portfolio Balance Checker Adapter.

Implements IBalanceChecker port using PortfolioService to check on-chain balances.
Uses direct RPC calls for real-time balance verification.
"""

import logging
from decimal import Decimal

from app.domain.ports.balance_checker import IBalanceChecker
from app.domain.enums.chain_type import ChainType
from app.application.portfolio.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)


class PortfolioBalanceChecker(IBalanceChecker):
    """
    Balance checker adapter using PortfolioService.

    This adapter leverages the existing PortfolioService infrastructure
    to check wallet balances via RPC calls. It provides real-time balance
    verification before transaction execution.

    Features:
    - Direct RPC calls (no database dependency)
    - Supports ERC20 tokens and native tokens (ETH)
    - Handles token decimals correctly (USDC: 6, ETH: 18)
    - Chain-aware balance checking

    Example:
        >>> checker = PortfolioBalanceChecker(portfolio_service)
        >>> has_balance = await checker.check_balance(
        ...     wallet_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        ...     token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
        ...     required_amount=Decimal("1000.0"),
        ...     chain="ethereum",
        ... )
    """

    # Common token addresses by chain
    TOKEN_ADDRESSES = {
        "ethereum": {
            "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "DAI": "0x6b175474e89094c44da98b954eedeac495271d0f",
            "WETH": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "WBTC": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        },
        "base": {
            "USDC": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
            "WETH": "0x4200000000000000000000000000000000000006",
        },
    }

    # Token decimals configuration
    TOKEN_DECIMALS = {
        "USDC": 6,
        "USDT": 6,
        "DAI": 18,
        "ETH": 18,
        "WETH": 18,
        "WBTC": 8,
    }

    # Minimum gas amounts by chain (in native token units)
    MIN_GAS_AMOUNTS = {
        ChainType.ETHEREUM: Decimal("0.01"),  # 0.01 ETH
        ChainType.BASE: Decimal("0.001"),  # 0.001 ETH (cheaper L2)
        ChainType.ARBITRUM: Decimal("0.001"),  # 0.001 ETH
        ChainType.POLYGON: Decimal("0.1"),  # 0.1 MATIC
        ChainType.OPTIMISM: Decimal("0.001"),  # 0.001 ETH
    }

    __slots__ = ("_portfolio_service",)

    def __init__(self, portfolio_service: PortfolioService):
        """
        Initialize balance checker.

        Args:
            portfolio_service: Service for fetching on-chain balances via RPC
        """
        self._portfolio_service = portfolio_service

    async def check_balance(
        self,
        wallet_address: str,
        token_address: str,
        required_amount: Decimal,
        chain: str = "ethereum",
    ) -> bool:
        """
        Check if wallet has sufficient token balance.

        Args:
            wallet_address: Wallet address (0x...)
            token_address: Token contract address or "native" for ETH
            required_amount: Required amount in token units
            chain: Blockchain name

        Returns:
            True if sufficient balance exists, False otherwise
        """
        try:
            current_balance = await self.get_balance(
                wallet_address=wallet_address,
                token_address=token_address,
                chain=chain,
            )

            has_sufficient = current_balance >= required_amount

            if not has_sufficient:
                logger.warning(
                    f"Insufficient balance for {wallet_address} on {chain}: "
                    f"has {current_balance}, needs {required_amount}"
                )

            return has_sufficient

        except Exception as e:
            logger.error(
                f"Error checking balance for {wallet_address} on {chain}: {type(e).__name__}: {e}"
            )
            # Conservative approach: return False if we can't check balance
            return False

    async def get_balance(
        self,
        wallet_address: str,
        token_address: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get current token balance for a wallet.

        Args:
            wallet_address: Wallet address (0x...)
            token_address: Token contract address or "native" for ETH
            chain: Blockchain name

        Returns:
            Current balance in token units
        """
        try:
            # Convert chain string to ChainType enum
            chain_type = self._parse_chain(chain)

            # Get RPC URL for the chain
            rpc_url = self._portfolio_service._get_rpc_url(chain_type)
            if not rpc_url:
                logger.error(f"No RPC URL configured for chain: {chain}")
                return Decimal("0")

            # Check if native token or ERC20
            if token_address.lower() == "native" or token_address.lower() == "eth":
                # Fetch native token balance (ETH, MATIC, etc.)
                balance = await self._portfolio_service._fetch_native_balance(
                    rpc_url=rpc_url,
                    address=wallet_address,
                )
                logger.debug(
                    f"Native balance for {wallet_address} on {chain}: {balance}"
                )
                return balance
            else:
                # Fetch ERC20 token balance
                decimals = self._get_token_decimals(token_address, chain)
                balance = await self._portfolio_service._fetch_token_balance(
                    rpc_url=rpc_url,
                    wallet_address=wallet_address,
                    token_address=token_address,
                    decimals=decimals,
                )
                logger.debug(
                    f"Token balance for {wallet_address} on {chain} ({token_address}): {balance}"
                )
                return balance

        except Exception as e:
            logger.error(
                f"Error fetching balance for {wallet_address} on {chain}: {type(e).__name__}: {e}"
            )
            return Decimal("0")

    async def check_gas_balance(
        self,
        wallet_address: str,
        chain: str = "ethereum",
        min_gas_amount: Decimal | None = None,
    ) -> bool:
        """
        Check if wallet has sufficient native token for gas fees.

        Args:
            wallet_address: Wallet address (0x...)
            chain: Blockchain name
            min_gas_amount: Minimum required gas amount (default varies by chain)

        Returns:
            True if sufficient gas exists, False otherwise
        """
        try:
            chain_type = self._parse_chain(chain)

            # Get minimum gas requirement for chain
            if min_gas_amount is None:
                min_gas_amount = self.MIN_GAS_AMOUNTS.get(
                    chain_type, Decimal("0.01")
                )

            # Get native token balance
            native_balance = await self.get_balance(
                wallet_address=wallet_address,
                token_address="native",
                chain=chain,
            )

            has_sufficient_gas = native_balance >= min_gas_amount

            if not has_sufficient_gas:
                logger.warning(
                    f"Insufficient gas for {wallet_address} on {chain}: "
                    f"has {native_balance}, needs {min_gas_amount}"
                )

            return has_sufficient_gas

        except Exception as e:
            logger.error(
                f"Error checking gas balance for {wallet_address} on {chain}: {type(e).__name__}: {e}"
            )
            # Conservative approach: return False if we can't check
            return False

    def _parse_chain(self, chain: str) -> ChainType:
        """
        Parse chain string to ChainType enum.

        Args:
            chain: Chain name (ethereum, base, arbitrum, etc.)

        Returns:
            ChainType enum value

        Raises:
            ValueError: If chain is not supported
        """
        chain_lower = chain.lower()

        if chain_lower in ("ethereum", "eth", "mainnet"):
            return ChainType.ETHEREUM
        elif chain_lower == "base":
            return ChainType.BASE
        elif chain_lower in ("arbitrum", "arb"):
            return ChainType.ARBITRUM
        elif chain_lower in ("polygon", "matic"):
            return ChainType.POLYGON
        elif chain_lower in ("optimism", "op"):
            return ChainType.OPTIMISM
        else:
            raise ValueError(f"Unsupported chain: {chain}")

    def _get_token_decimals(self, token_address: str, chain: str) -> int:
        """
        Get token decimals for a token address.

        Args:
            token_address: Token contract address
            chain: Blockchain name

        Returns:
            Token decimals (default: 18 for unknown tokens)
        """
        # Try to match token address against known tokens
        chain_lower = chain.lower()
        chain_tokens = self.TOKEN_ADDRESSES.get(chain_lower, {})

        for symbol, addr in chain_tokens.items():
            if addr.lower() == token_address.lower():
                return self.TOKEN_DECIMALS.get(symbol, 18)

        # Default to 18 decimals (ERC20 standard default)
        return 18

    def get_token_symbol(self, token_address: str, chain: str) -> str | None:
        """
        Get token symbol for a token address.

        Args:
            token_address: Token contract address
            chain: Blockchain name

        Returns:
            Token symbol if known, None otherwise
        """
        chain_lower = chain.lower()
        chain_tokens = self.TOKEN_ADDRESSES.get(chain_lower, {})

        for symbol, addr in chain_tokens.items():
            if addr.lower() == token_address.lower():
                return symbol

        return None
