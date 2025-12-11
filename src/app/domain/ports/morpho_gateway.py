"""
Morpho Protocol Gateway Port.

Defines the domain interface for Morpho lending vault operations.
"""

from decimal import Decimal
from typing import Protocol

from app.domain.entities.lending.morpho_market import MorphoMarket
from app.domain.entities.lending.morpho_position import MorphoPosition
from app.domain.entities.lending.morpho_vault import MorphoVault
from app.domain.value_objects.lending.vault_apy import VaultAPY


class MorphoGateway(Protocol):
    """
    Port interface for Morpho Protocol operations.

    This protocol defines the contract for accessing Morpho
    MetaMorpho vaults and Morpho Blue markets.
    """

    async def get_vaults(
        self,
        asset: str | None = None,
        chain: str = "ethereum",
    ) -> list[MorphoVault]:
        """
        Get MetaMorpho vaults.

        Args:
            asset: Filter by underlying asset symbol (e.g., "USDC")
            chain: Blockchain (default: ethereum)

        Returns:
            List of MorphoVault entities

        Raises:
            MorphoAPIError: If API is unavailable
        """
        ...

    async def get_vault_details(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> MorphoVault:
        """
        Get detailed vault information.

        Args:
            vault_address: Vault contract address
            chain: Blockchain

        Returns:
            MorphoVault with full details

        Raises:
            VaultNotFoundError: If vault doesn't exist
        """
        ...

    async def get_vault_apy(
        self,
        vault_address: str,
        chain: str = "ethereum",
    ) -> VaultAPY:
        """
        Get vault APY with historical data.

        Args:
            vault_address: Vault contract address
            chain: Blockchain

        Returns:
            VaultAPY value object

        Raises:
            VaultNotFoundError: If vault doesn't exist
        """
        ...

    async def get_markets(
        self,
        chain: str = "ethereum",
    ) -> list[MorphoMarket]:
        """
        Get Morpho Blue markets.

        Args:
            chain: Blockchain

        Returns:
            List of MorphoMarket entities
        """
        ...

    async def get_user_positions(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> list[MorphoPosition]:
        """
        Get user's vault positions.

        Args:
            address: User wallet address
            chain: Blockchain

        Returns:
            List of MorphoPosition entities

        Raises:
            InvalidVaultAddressError: If address format invalid
        """
        ...

    async def get_user_deposits(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> list[MorphoPosition]:
        """
        Get user's deposit history.

        Alias for get_user_positions for API clarity.
        """
        ...
