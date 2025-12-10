"""
Transaction Repository Port.

Defines the abstract interface for transaction persistence operations.
This allows storing and retrieving transaction history from the database.
"""

from datetime import datetime
from typing import Protocol

from app.domain.entities.transaction import Transaction, TransactionId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.entities.wallet import WalletId
from app.domain.value_objects.user_id import UserId


class TransactionRepository(Protocol):
    """
    Repository interface for transaction persistence.

    Handles CRUD operations for transaction records stored in the database.
    Transactions represent on-chain operations initiated by users via Privy.

    Use cases:
    - Recording transaction when user sends from frontend
    - Updating transaction status after on-chain confirmation
    - Retrieving transaction history for user display
    - Auditing and analytics
    """

    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None:
        """
        Get transaction by ID.

        Args:
            transaction_id: The transaction's database ID.

        Returns:
            Transaction if found, None otherwise.
        """
        ...

    async def get_by_tx_hash(self, tx_hash: str) -> Transaction | None:
        """
        Get transaction by blockchain hash.

        Args:
            tx_hash: The blockchain transaction hash (0x...).

        Returns:
            Transaction if found, None otherwise.
        """
        ...

    async def get_by_user_id(
        self,
        user_id: UserId,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """
        Get transactions for a specific user with optional filters.

        Args:
            user_id: The user's ID.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            List of transactions matching the criteria, ordered by created_at desc.
        """
        ...

    async def get_by_wallet_id(
        self,
        wallet_id: WalletId,
        *,
        limit: int = 50,
        offset: int = 0,
        status: TransactionStatus | None = None,
    ) -> list[Transaction]:
        """
        Get transactions for a specific wallet.

        Args:
            wallet_id: The wallet's database ID.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            status: Filter by status (optional).

        Returns:
            List of transactions for the wallet, ordered by created_at desc.
        """
        ...

    async def get_pending_transactions(
        self,
        *,
        limit: int = 100,
        older_than_seconds: int | None = None,
    ) -> list[Transaction]:
        """
        Get pending transactions that need confirmation.

        Args:
            limit: Maximum number of results.
            older_than_seconds: Only get transactions older than this (for retries).

        Returns:
            List of pending transactions with tx_hash set.
        """
        ...

    async def count_by_user_id(
        self,
        user_id: UserId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """
        Count transactions for a user with optional filters.

        Args:
            user_id: The user's ID.
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            Total count of matching transactions.
        """
        ...

    async def save(self, transaction: Transaction) -> Transaction:
        """
        Save a new transaction to the database.

        Args:
            transaction: The transaction entity to save.

        Returns:
            The saved transaction with generated ID.
        """
        ...

    async def update(self, transaction: Transaction) -> Transaction:
        """
        Update an existing transaction.

        Args:
            transaction: The transaction entity with updated fields.

        Returns:
            The updated transaction.
        """
        ...

    async def update_status(
        self,
        transaction_id: TransactionId,
        status: TransactionStatus,
        *,
        block_number: int | None = None,
        confirmed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> bool:
        """
        Update transaction status and confirmation data.

        Args:
            transaction_id: The transaction's database ID.
            status: New status (SUCCESS, FAILED).
            block_number: Block where transaction was confirmed.
            confirmed_at: Timestamp of confirmation.
            error_message: Error message if failed.

        Returns:
            True if updated, False if not found.
        """
        ...
