"""
Compound V3 Gateway Port.

Defines the interface for Compound V3 (Comet) lending protocol operations.
"""

from typing import Optional, Protocol
from dataclasses import dataclass


@dataclass
class CompoundMarketData:
    """Compound V3 market data."""

    chain: str
    base_asset: str
    comet_address: str
    supply_apy: float
    borrow_apy: float
    utilization: float
    total_supply_usd: float
    total_borrow_usd: float


@dataclass
class CompoundUserPosition:
    """User position in Compound V3."""

    chain: str
    base_asset: str
    user_address: str
    supplied: float
    borrowed: float
    health_factor: float


class CompoundGateway(Protocol):
    """
    Gateway for Compound V3 lending protocol operations.

    Provides access to:
    - Market rates (supply/borrow APY)
    - User positions
    - Protocol statistics
    """

    async def get_market_details(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> Optional[CompoundMarketData]:
        """
        Get market details for a specific asset.

        Args:
            asset: Base asset symbol (USDC, WETH)
            chain: Blockchain (ethereum, base, arbitrum, polygon)

        Returns:
            CompoundMarketData with current rates and stats
        """
        ...

    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[CompoundMarketData]:
        """
        Get all markets on a specific chain.

        Args:
            chain: Blockchain

        Returns:
            List of CompoundMarketData objects
        """
        ...

    async def get_supply_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> float:
        """
        Get current supply APY for an asset.

        Args:
            asset: Base asset symbol
            chain: Blockchain

        Returns:
            Supply APY as percentage (e.g., 4.5 for 4.5%)
        """
        ...

    async def get_borrow_apy(
        self,
        asset: str,
        chain: str = "ethereum",
    ) -> float:
        """
        Get current borrow APY for an asset.

        Args:
            asset: Base asset symbol
            chain: Blockchain

        Returns:
            Borrow APY as percentage
        """
        ...

    async def get_user_position(
        self,
        user_address: str,
        asset: str = "USDC",
        chain: str = "ethereum",
    ) -> Optional[CompoundUserPosition]:
        """
        Get user's position in a Compound V3 market.

        Args:
            user_address: User's wallet address
            asset: Base asset
            chain: Blockchain

        Returns:
            CompoundUserPosition or None if no position
        """
        ...
