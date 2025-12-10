"""
Aave Protocol Gateway Port.

Defines the domain interface for Aave V3 lending operations.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.lending.aave_market import AaveMarket
from app.domain.entities.lending.aave_position import AavePosition
from app.domain.value_objects.lending.health_factor import HealthFactor


class AaveGateway(Protocol):
    """
    Port interface for Aave V3 Protocol operations.

    This protocol defines the contract for accessing Aave V3
    lending markets, user positions, and health calculations.
    """

    async def get_markets(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[AaveMarket]:
        """
        Get Aave V3 markets.

        Args:
            asset: Filter by asset symbol (e.g., "USDC", "WETH")
            chain: Blockchain (default: ethereum)

        Returns:
            List of AaveMarket entities

        Raises:
            AaveAPIError: If API is unavailable
            UnsupportedChainError: If chain is not supported
        """
        ...

    async def get_market_details(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> AaveMarket:
        """
        Get detailed market information for an asset.

        Args:
            asset: Asset symbol or address
            chain: Blockchain

        Returns:
            AaveMarket with full details

        Raises:
            MarketNotFoundError: If market doesn't exist
        """
        ...

    async def get_user_position(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> AavePosition:
        """
        Get user's complete Aave position.

        Args:
            address: User wallet address
            chain: Blockchain

        Returns:
            AavePosition with supplies, borrows, and health metrics

        Raises:
            InvalidAddressError: If address format invalid
            PositionNotFoundError: If user has no position
        """
        ...

    async def get_health_factor(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> HealthFactor:
        """
        Get user's health factor with risk analysis.

        Args:
            address: User wallet address
            chain: Blockchain

        Returns:
            HealthFactor value object

        Raises:
            InvalidAddressError: If address format invalid
        """
        ...

    async def calculate_health_factor(
        self,
        collateral_usd: Decimal,
        debt_usd: Decimal,
        liquidation_threshold: Decimal = Decimal("0.825"),
    ) -> HealthFactor:
        """
        Calculate health factor from collateral and debt.

        Args:
            collateral_usd: Total collateral value in USD
            debt_usd: Total debt value in USD
            liquidation_threshold: Average liquidation threshold

        Returns:
            HealthFactor value object
        """
        ...

    async def get_available_to_borrow(
        self,
        address: str,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get maximum amount user can borrow of an asset.

        Args:
            address: User wallet address
            asset: Asset symbol to borrow
            chain: Blockchain

        Returns:
            Maximum borrowable amount in asset units

        Raises:
            InvalidAddressError: If address format invalid
            MarketNotFoundError: If market doesn't exist
        """
        ...

    async def get_liquidation_threshold(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get liquidation threshold for an asset.

        Args:
            asset: Asset symbol
            chain: Blockchain

        Returns:
            Liquidation threshold as decimal (e.g., 0.825 = 82.5%)
        """
        ...

    async def get_protocol_stats(
        self,
        chain: str = "ethereum",
    ) -> dict:
        """
        Get protocol-wide statistics.

        Args:
            chain: Blockchain

        Returns:
            Dict with TVL, total supplied, total borrowed, etc.
        """
        ...

    async def get_supply_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Decimal:
        """
        Get current supply APY for an asset.

        Args:
            asset: Asset symbol
            chain: Blockchain

        Returns:
            Supply APY as decimal (e.g., 0.05 = 5%)

        Raises:
            MarketNotFoundError: If market doesn't exist
        """
        ...

    async def get_borrow_apy(
        self,
        asset: str,
        chain: str = "ethereum",
        rate_type: str = "variable",
    ) -> Decimal:
        """
        Get current borrow APY for an asset.

        Args:
            asset: Asset symbol
            chain: Blockchain
            rate_type: "variable" or "stable"

        Returns:
            Borrow APY as decimal

        Raises:
            MarketNotFoundError: If market doesn't exist
        """
        ...
