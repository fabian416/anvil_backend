"""
Portfolio Repository Port.

Defines the abstract interface for portfolio snapshot persistence operations.
This allows storing and retrieving portfolio snapshots from the database.
"""

from datetime import datetime
from typing import Protocol

from app.domain.entities.portfolio_snapshot import (
    PortfolioSnapshot,
    PortfolioSnapshotId,
    TokenHolding,
)
from app.domain.entities.wallet import WalletId
from app.domain.enums.chain_type import ChainType


class PortfolioRepository(Protocol):
    """
    Repository interface for portfolio snapshot persistence.

    Handles CRUD operations for portfolio snapshots stored in the database.
    Portfolio snapshots capture a point-in-time view of wallet holdings.

    Use cases:
    - Storing portfolio snapshots after transaction confirmations
    - Retrieving latest portfolio for user display
    - Historical portfolio data for analytics and charts
    """

    async def get_by_id(
        self, snapshot_id: PortfolioSnapshotId
    ) -> PortfolioSnapshot | None:
        """
        Get portfolio snapshot by ID.

        Args:
            snapshot_id: The snapshot's database ID.

        Returns:
            PortfolioSnapshot if found, None otherwise.
        """
        ...

    async def get_latest_by_wallet(
        self,
        wallet_id: WalletId,
        chain: ChainType | None = None,
    ) -> PortfolioSnapshot | None:
        """
        Get the most recent portfolio snapshot for a wallet.

        Args:
            wallet_id: The wallet's database ID.
            chain: Optional chain filter.

        Returns:
            Most recent PortfolioSnapshot if found, None otherwise.
        """
        ...

    async def get_by_wallet(
        self,
        wallet_id: WalletId,
        *,
        chain: ChainType | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PortfolioSnapshot]:
        """
        Get portfolio snapshots for a wallet.

        Args:
            wallet_id: The wallet's database ID.
            chain: Optional chain filter.
            limit: Maximum number of results (default 50).
            offset: Number of results to skip (default 0).

        Returns:
            List of snapshots ordered by captured_at desc.
        """
        ...

    async def get_history(
        self,
        wallet_id: WalletId,
        start_date: datetime,
        end_date: datetime,
        *,
        chain: ChainType | None = None,
    ) -> list[PortfolioSnapshot]:
        """
        Get portfolio snapshot history for a date range.

        Args:
            wallet_id: The wallet's database ID.
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).
            chain: Optional chain filter.

        Returns:
            List of snapshots in the date range.
        """
        ...

    async def save(self, snapshot: PortfolioSnapshot) -> PortfolioSnapshot:
        """
        Save a new portfolio snapshot with its holdings.

        Args:
            snapshot: The portfolio snapshot to save.

        Returns:
            The saved snapshot with generated ID.
        """
        ...

    async def save_holding(self, holding: TokenHolding) -> TokenHolding:
        """
        Save a token holding to an existing snapshot.

        Args:
            holding: The token holding to save.

        Returns:
            The saved holding with generated ID.
        """
        ...

    async def delete(self, snapshot_id: PortfolioSnapshotId) -> bool:
        """
        Delete a portfolio snapshot and its holdings.

        Args:
            snapshot_id: The snapshot's database ID.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def delete_old_snapshots(
        self,
        wallet_id: WalletId,
        *,
        keep_count: int = 100,
    ) -> int:
        """
        Delete old snapshots for a wallet, keeping the most recent ones.

        Args:
            wallet_id: The wallet's database ID.
            keep_count: Number of recent snapshots to keep.

        Returns:
            Number of deleted snapshots.
        """
        ...

    # ============================================================
    # Analytics Methods (for Admin Metrics)
    # ============================================================

    async def count_snapshots(self, wallet_id: WalletId | None = None) -> int:
        """
        Count total portfolio snapshots.

        Args:
            wallet_id: Optional filter by wallet.

        Returns:
            Total count of snapshots.
        """
        ...

    async def get_portfolio_value_history(
        self,
        wallet_id: WalletId,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple[datetime, float]]:
        """
        Get portfolio total USD value history for charts.

        Args:
            wallet_id: The wallet's database ID.
            start_date: Start of the date range.
            end_date: End of the date range.

        Returns:
            List of (datetime, total_usd) tuples.
        """
        ...
