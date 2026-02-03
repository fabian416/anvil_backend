"""
Admin Metrics Query Handlers.

Handlers for fetching admin analytics and metrics data.
These handlers aggregate data from wallet and transaction repositories.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.common.ports.user_query_gateway import UserQueryGateway
from app.domain.enums.chain_type import ChainType
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.transaction_type import TransactionType
from app.domain.enums.wallet_provider import WalletProvider
from app.domain.transactions.ports.transaction.transaction_repository import (
    TransactionRepository,
)
from app.domain.ports.wallet.wallet_repository import WalletRepository

logger = logging.getLogger(__name__)


# ============================================================
# Response Data Classes
# ============================================================


@dataclass
class WalletOverview:
    """Wallet overview metrics."""

    total_wallets: int
    active_wallets: int
    privy_wallets: int
    imported_wallets: int
    external_wallets: int


@dataclass
class TransactionOverview:
    """Transaction overview metrics."""

    total_transactions: int
    pending_transactions: int
    successful_transactions: int
    failed_transactions: int


@dataclass
class UserActivityOverview:
    """User activity overview metrics."""

    total_users: int
    total_users_with_transactions: int
    active_users_today: int
    active_users_7d: int
    active_users_30d: int


@dataclass
class MetricsOverview:
    """Combined admin metrics overview."""

    wallets: WalletOverview
    transactions: TransactionOverview
    users: UserActivityOverview
    generated_at: datetime


@dataclass
class TimeSeriesPoint:
    """Single point in a time series."""

    date: datetime
    value: int


@dataclass
class DistributionItem:
    """Item in a distribution."""

    name: str
    count: int
    percentage: float


# ============================================================
# Query Handlers
# ============================================================


class GetAdminMetricsOverviewHandler:
    """
    Handler to get admin metrics overview.

    Aggregates data from both wallet and transaction repositories
    to provide a high-level view of system activity.
    """

    def __init__(
        self,
        wallet_repository: WalletRepository,
        transaction_repository: TransactionRepository,
        user_query_gateway: UserQueryGateway,
    ):
        self._wallet_repository = wallet_repository
        self._transaction_repository = transaction_repository
        self._user_query_gateway = user_query_gateway

    async def execute(self) -> MetricsOverview:
        """
        Get admin metrics overview.

        Returns:
            MetricsOverview with wallet, transaction, and user activity data.
        """
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = today_start - timedelta(days=7)
        thirty_days_ago = today_start - timedelta(days=30)

        # Fetch wallet metrics
        try:
            total_wallets = await self._wallet_repository.count_all()
            active_wallets = await self._wallet_repository.count_active_wallets()
            privy_wallets = await self._wallet_repository.count_by_provider(
                WalletProvider.PRIVY
            )
            imported_wallets = await self._wallet_repository.count_by_provider(
                WalletProvider.IMPORTED
            )
            external_wallets = await self._wallet_repository.count_by_provider(
                WalletProvider.EXTERNAL
            )
        except Exception as e:
            logger.error(f"Error fetching wallet metrics: {e}")
            total_wallets = 0
            active_wallets = 0
            privy_wallets = 0
            imported_wallets = 0
            external_wallets = 0

        wallet_overview = WalletOverview(
            total_wallets=total_wallets,
            active_wallets=active_wallets,
            privy_wallets=privy_wallets,
            imported_wallets=imported_wallets,
            external_wallets=external_wallets,
        )

        # Fetch transaction metrics
        try:
            total_transactions = await self._transaction_repository.count_all()
            pending_transactions = await self._transaction_repository.count_by_status(
                TransactionStatus.PENDING
            )
            successful_transactions = (
                await self._transaction_repository.count_by_status(
                    TransactionStatus.SUCCESS
                )
            )
            failed_transactions = await self._transaction_repository.count_by_status(
                TransactionStatus.FAILED
            )
        except Exception as e:
            logger.error(f"Error fetching transaction metrics: {e}")
            total_transactions = 0
            pending_transactions = 0
            successful_transactions = 0
            failed_transactions = 0

        transaction_overview = TransactionOverview(
            total_transactions=total_transactions,
            pending_transactions=pending_transactions,
            successful_transactions=successful_transactions,
            failed_transactions=failed_transactions,
        )

        # Fetch user activity metrics
        try:
            # Total registered users in the system
            total_users = await self._user_query_gateway.count_all()
        except Exception as e:
            logger.error(f"Error fetching total users count: {e}")
            total_users = 0

        try:
            users_with_transactions = (
                await self._transaction_repository.get_unique_user_count()
            )
            active_today = await self._transaction_repository.get_unique_user_count(
                start_date=today_start, end_date=now
            )
            active_7d = await self._transaction_repository.get_unique_user_count(
                start_date=seven_days_ago, end_date=now
            )
            active_30d = await self._transaction_repository.get_unique_user_count(
                start_date=thirty_days_ago, end_date=now
            )
        except Exception as e:
            logger.error(f"Error fetching user activity metrics: {e}")
            users_with_transactions = 0
            active_today = 0
            active_7d = 0
            active_30d = 0

        user_activity = UserActivityOverview(
            total_users=total_users,
            total_users_with_transactions=users_with_transactions,
            active_users_today=active_today,
            active_users_7d=active_7d,
            active_users_30d=active_30d,
        )

        return MetricsOverview(
            wallets=wallet_overview,
            transactions=transaction_overview,
            users=user_activity,
            generated_at=now,
        )


class GetTransactionTimeSeriesHandler:
    """Handler to get transaction time series data."""

    def __init__(self, transaction_repository: TransactionRepository):
        self._transaction_repository = transaction_repository

    async def execute(
        self,
        from_date: datetime,
        to_date: datetime,
        chain: str | None = None,
        tx_type: str | None = None,
    ) -> tuple[list[TimeSeriesPoint], int]:
        """
        Get transaction time series data.

        Args:
            from_date: Start of the date range.
            to_date: End of the date range.
            chain: Optional chain filter.
            tx_type: Optional transaction type filter.

        Returns:
            Tuple of (list of TimeSeriesPoint, total count).
        """
        # Parse chain if provided
        chain_enum: ChainType | None = None
        if chain:
            try:
                chain_enum = ChainType(chain)
            except ValueError:
                logger.warning(f"Invalid chain filter: {chain}")

        # Parse tx_type if provided
        tx_type_enum: TransactionType | None = None
        if tx_type:
            try:
                tx_type_enum = TransactionType[tx_type.upper()]
            except (KeyError, ValueError):
                logger.warning(f"Invalid tx_type filter: {tx_type}")

        try:
            daily_counts = (
                await self._transaction_repository.get_daily_transaction_counts(
                    start_date=from_date,
                    end_date=to_date,
                    chain=chain_enum,
                    tx_type=tx_type_enum,
                )
            )

            total_count = (
                await self._transaction_repository.count_transactions_in_range(
                    start_date=from_date,
                    end_date=to_date,
                    chain=chain_enum,
                    tx_type=tx_type_enum,
                )
            )

            data_points = [
                TimeSeriesPoint(date=date, value=count) for date, count in daily_counts
            ]

            return data_points, total_count

        except Exception as e:
            logger.error(f"Error fetching transaction time series: {e}")
            return [], 0


class GetWalletTimeSeriesHandler:
    """Handler to get wallet creation time series data."""

    def __init__(self, wallet_repository: WalletRepository):
        self._wallet_repository = wallet_repository

    async def execute(
        self,
        from_date: datetime,
        to_date: datetime,
    ) -> tuple[list[TimeSeriesPoint], int]:
        """
        Get wallet creation time series data.

        Args:
            from_date: Start of the date range.
            to_date: End of the date range.

        Returns:
            Tuple of (list of TimeSeriesPoint, total count).
        """
        try:
            daily_counts = await self._wallet_repository.get_daily_wallet_counts(
                start_date=from_date,
                end_date=to_date,
            )

            total_count = await self._wallet_repository.count_wallets_created_in_range(
                start_date=from_date,
                end_date=to_date,
            )

            data_points = [
                TimeSeriesPoint(date=date, value=count) for date, count in daily_counts
            ]

            return data_points, total_count

        except Exception as e:
            logger.error(f"Error fetching wallet time series: {e}")
            return [], 0


class GetUserActivityTimeSeriesHandler:
    """Handler to get user activity time series data."""

    def __init__(self, transaction_repository: TransactionRepository):
        self._transaction_repository = transaction_repository

    async def execute(
        self,
        from_date: datetime,
        to_date: datetime,
    ) -> list[TimeSeriesPoint]:
        """
        Get user activity time series data.

        Returns unique users per day within the date range.

        Args:
            from_date: Start of the date range.
            to_date: End of the date range.

        Returns:
            List of TimeSeriesPoint with unique user counts.
        """
        try:
            daily_counts = await self._transaction_repository.get_active_users_per_day(
                start_date=from_date,
                end_date=to_date,
            )

            return [
                TimeSeriesPoint(date=date, value=count) for date, count in daily_counts
            ]

        except Exception as e:
            logger.error(f"Error fetching user activity time series: {e}")
            return []


class GetWalletDistributionHandler:
    """Handler to get wallet distribution by provider."""

    def __init__(self, wallet_repository: WalletRepository):
        self._wallet_repository = wallet_repository

    async def execute(self) -> tuple[list[DistributionItem], int]:
        """
        Get wallet distribution by provider.

        Returns:
            Tuple of (list of DistributionItem, total count).
        """
        try:
            counts_by_provider = (
                await self._wallet_repository.get_wallet_counts_by_provider()
            )
            total = sum(counts_by_provider.values())

            distribution = []
            for provider, count in counts_by_provider.items():
                percentage = (count / total * 100) if total > 0 else 0.0
                distribution.append(
                    DistributionItem(
                        name=provider,
                        count=count,
                        percentage=round(percentage, 2),
                    )
                )

            return distribution, total

        except Exception as e:
            logger.error(f"Error fetching wallet distribution: {e}")
            return [], 0


class GetTransactionDistributionHandler:
    """Handler to get transaction distribution by various dimensions."""

    def __init__(self, transaction_repository: TransactionRepository):
        self._transaction_repository = transaction_repository

    async def execute(
        self,
    ) -> tuple[
        list[DistributionItem], list[DistributionItem], list[DistributionItem], int
    ]:
        """
        Get transaction distribution by chain, status, and type.

        Returns:
            Tuple of (by_chain, by_status, by_type, total).
        """
        try:
            total = await self._transaction_repository.count_all()

            # Get by chain
            counts_by_chain = (
                await self._transaction_repository.get_transaction_counts_by_chain()
            )
            by_chain = [
                DistributionItem(
                    name=chain,
                    count=count,
                    percentage=round((count / total * 100) if total > 0 else 0.0, 2),
                )
                for chain, count in counts_by_chain.items()
            ]

            # Get by status
            counts_by_status = (
                await self._transaction_repository.get_transaction_counts_by_status()
            )
            by_status = [
                DistributionItem(
                    name=status,
                    count=count,
                    percentage=round((count / total * 100) if total > 0 else 0.0, 2),
                )
                for status, count in counts_by_status.items()
            ]

            # Get by type
            counts_by_type = (
                await self._transaction_repository.get_transaction_counts_by_type()
            )
            by_type = [
                DistributionItem(
                    name=tx_type,
                    count=count,
                    percentage=round((count / total * 100) if total > 0 else 0.0, 2),
                )
                for tx_type, count in counts_by_type.items()
            ]

            return by_chain, by_status, by_type, total

        except Exception as e:
            logger.error(f"Error fetching transaction distribution: {e}")
            return [], [], [], 0
