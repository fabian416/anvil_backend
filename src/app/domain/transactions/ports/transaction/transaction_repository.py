"""
Transaction Repository Port.

Defines the abstract interface for transaction persistence operations.
This allows storing and retrieving transaction history from the database.
"""

from datetime import datetime
from typing import Protocol

from app.domain.transactions.entities.transaction import Transaction, TransactionId
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
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

        Note: This returns the first match. For checking per-user duplicates,
        use get_by_user_and_tx_hash instead.

        Args:
            tx_hash: The blockchain transaction hash (0x...).

        Returns:
            Transaction if found, None otherwise.
        """
        ...

    async def get_by_user_and_tx_hash(
        self,
        user_id: UserId,
        tx_hash: str,
    ) -> Transaction | None:
        """
        Get transaction by user ID and blockchain hash combination.

        This is used to check for duplicate records per user, since the same
        on-chain transaction can appear in both sender's and receiver's history.

        Args:
            user_id: The user's ID.
            tx_hash: The blockchain transaction hash (0x...).

        Returns:
            Transaction if found for this user, None otherwise.
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
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """
        Get transactions for a specific wallet.

        Args:
            wallet_id: The wallet's database ID.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            List of transactions for the wallet, ordered by created_at desc.
        """
        ...

    async def count_by_wallet_id(
        self,
        wallet_id: WalletId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """
        Count transactions for a wallet with optional filters.

        Args:
            wallet_id: The wallet's database ID.
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            Total count of matching transactions.
        """
        ...

    async def get_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]:
        """
        Get transactions across all users (admin usage).

        Args:
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            List of transactions matching the criteria, ordered by created_at desc.
        """
        ...

    async def count_all_filtered(
        self,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """
        Count all transactions with optional filters (admin usage).

        Args:
            chain: Filter by blockchain (optional).
            status: Filter by status (optional).
            tx_type: Filter by transaction type (optional).

        Returns:
            Total count of matching transactions.
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

    # ============================================================
    # Analytics Methods (for Admin Metrics)
    # ============================================================

    async def count_all(self) -> int:
        """
        Count total number of transactions in the system.

        Returns:
            Total count of all transactions.
        """
        ...

    async def count_by_status(self, status: TransactionStatus) -> int:
        """
        Count transactions by status.

        Args:
            status: The transaction status to filter by.

        Returns:
            Count of transactions with the specified status.
        """
        ...

    async def count_by_chain(self, chain: ChainType) -> int:
        """
        Count transactions by chain.

        Args:
            chain: The chain to filter by.

        Returns:
            Count of transactions on the specified chain.
        """
        ...

    async def get_transaction_counts_by_status(self) -> dict[str, int]:
        """
        Get transaction counts grouped by status.

        Returns:
            Dictionary mapping status name to count.
        """
        ...

    async def get_transaction_counts_by_chain(self) -> dict[str, int]:
        """
        Get transaction counts grouped by chain.

        Returns:
            Dictionary mapping chain name to count.
        """
        ...

    async def get_transaction_counts_by_type(self) -> dict[str, int]:
        """
        Get transaction counts grouped by transaction type.

        Returns:
            Dictionary mapping type name to count.
        """
        ...

    async def count_transactions_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int:
        """
        Count transactions within a date range with optional filters.

        Args:
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).
            chain: Optional chain filter.
            status: Optional status filter.
            tx_type: Optional transaction type filter.

        Returns:
            Count of transactions matching the criteria.
        """
        ...

    async def get_daily_transaction_counts(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, int]]:
        """
        Get daily transaction counts for a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
            chain: Optional chain filter.
            tx_type: Optional transaction type filter.

        Returns:
            List of (date, count) tuples for each day.
        """
        ...

    async def get_unique_user_count(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> int:
        """
        Count unique users with transactions.

        Args:
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Count of unique users.
        """
        ...

    async def get_active_users_per_day(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, int]]:
        """
        Get count of unique active users per day.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.

        Returns:
            List of (date, unique_user_count) tuples.
        """
        ...

    # ============================================================
    # Volume Analytics Methods
    # ============================================================

    async def get_total_volume(
        self,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[float, float]:
        """
        Get total transaction volume (sum of amount_in) with optional filters.

        Args:
            chain: Optional chain filter.
            tx_type: Optional transaction type filter.
            status: Optional status filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Tuple of (total_volume, total_volume_count) where volume is in ETH.
        """
        ...

    async def get_volume_by_user(
        self,
        user_id: UserId,
        *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float:
        """
        Get total transaction volume for a specific user.

        Args:
            user_id: The user's ID.
            chain: Optional chain filter.
            status: Optional status filter.
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            Total volume in ETH.
        """
        ...

    async def get_daily_volume(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, float]]:
        """
        Get daily transaction volume for a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.
            chain: Optional chain filter.
            tx_type: Optional transaction type filter.

        Returns:
            List of (date, volume) tuples for each day.
        """
        ...

    async def get_top_senders(
        self,
        *,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[tuple[int, int, float]]:
        """
        Get top senders by transaction count and volume.

        Args:
            limit: Maximum number of results (default 10).
            start_date: Optional start date filter.
            end_date: Optional end date filter.

        Returns:
            List of (user_id, tx_count, total_volume) tuples.
        """
        ...
