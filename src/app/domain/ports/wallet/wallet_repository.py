"""
Wallet Repository Port.

Defines the abstract interface for wallet persistence operations.
This allows storing and retrieving wallets from the database,
independent of any external wallet provider.
"""

from typing import Protocol

from app.domain.entities.wallet import Wallet, WalletId
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.value_objects.user_id import UserId


class WalletRepository(Protocol):
    """
    Repository interface for wallet persistence.

    Handles CRUD operations for wallets stored locally in the database.
    This is separate from the EmbeddedWalletProviderPort which communicates
    with external providers like Privy.

    Use cases:
    - Storing imported wallets (not managed by Privy)
    - Caching wallet data locally
    - Tracking user's primary wallet
    """

    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None:
        """
        Get wallet by ID.

        Args:
            wallet_id: The wallet's database ID.

        Returns:
            Wallet if found, None otherwise.
        """
        ...

    async def get_by_address(self, address: str) -> Wallet | None:
        """
        Get wallet by blockchain address.

        Args:
            address: Blockchain wallet address (0x...).

        Returns:
            Wallet if found, None otherwise.
        """
        ...

    async def get_by_privy_wallet_id(self, privy_wallet_id: str) -> Wallet | None:
        """
        Get wallet by Privy wallet ID.

        Args:
            privy_wallet_id: The Privy wallet ID.

        Returns:
            Wallet if found, None otherwise.
        """
        ...

    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]:
        """
        Get all wallets for a specific user.

        Args:
            user_id: The user's ID.

        Returns:
            List of wallets belonging to the user.
        """
        ...

    async def get_by_user_and_address(
        self,
        user_id: UserId,
        address: str,
    ) -> Wallet | None:
        """
        Get wallet by user ID and address combination.

        Args:
            user_id: The user's ID.
            address: Blockchain wallet address (0x...).

        Returns:
            Wallet if found, None otherwise.
        """
        ...

    async def get_by_user_and_provider(
        self,
        user_id: UserId,
        provider: WalletProvider,
    ) -> list[Wallet]:
        """
        Get all wallets for a user with a specific provider.

        Args:
            user_id: The user's ID.
            provider: The wallet provider (PRIVY, EXTERNAL, IMPORTED).

        Returns:
            List of wallets matching the criteria.
        """
        ...

    async def save(self, wallet: Wallet) -> Wallet:
        """
        Save a new wallet to the database.

        Args:
            wallet: The wallet entity to save.

        Returns:
            The saved wallet with generated ID.
        """
        ...

    async def update(self, wallet: Wallet) -> Wallet:
        """
        Update an existing wallet.

        Args:
            wallet: The wallet entity with updated fields.

        Returns:
            The updated wallet.
        """
        ...

    async def upsert(
        self,
        user_id: UserId,
        address: str,
        provider: WalletProvider,
        privy_wallet_id: str | None = None,
        chain_type: str | None = None,
    ) -> Wallet:
        """
        Insert or update a wallet by user_id + address.

        If a wallet with the same user_id and address exists, update it.
        Otherwise, create a new wallet.

        Args:
            user_id: The user's ID.
            address: Blockchain wallet address.
            provider: The wallet provider (PRIVY, EXTERNAL, IMPORTED).
            privy_wallet_id: Optional Privy wallet ID (can be None for imported).
            chain_type: Optional chain type string.

        Returns:
            The upserted wallet.
        """
        ...

    async def delete(self, wallet_id: WalletId) -> bool:
        """
        Delete a wallet by ID.

        Args:
            wallet_id: The wallet's database ID.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def delete_by_user_and_address(
        self,
        user_id: UserId,
        address: str,
    ) -> bool:
        """
        Delete a wallet by user ID and address.

        Args:
            user_id: The user's ID.
            address: Blockchain wallet address.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def mark_exported(self, privy_wallet_id: str) -> bool:
        """
        Mark a wallet as exported by setting exported_at timestamp.

        This is used for audit purposes to track when a wallet's private key
        was exported. The actual private key is never stored.

        Args:
            privy_wallet_id: The Privy wallet ID.

        Returns:
            True if updated, False if wallet not found in local DB.
        """
        ...
