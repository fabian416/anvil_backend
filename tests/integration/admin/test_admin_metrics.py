"""
Integration tests for admin metrics handlers.

Tests the analytics handlers that aggregate data from
wallet and transaction repositories.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.queries.admin.get_metrics import (
    GetAdminMetricsOverviewHandler,
    GetTransactionDistributionHandler,
    GetTransactionTimeSeriesHandler,
    GetUserActivityTimeSeriesHandler,
    GetWalletDistributionHandler,
    GetWalletTimeSeriesHandler,
)
from app.domain.enums.transaction_status import TransactionStatus
from app.domain.enums.wallet_provider import WalletProvider


class TestGetAdminMetricsOverviewHandler:
    """Tests for GetAdminMetricsOverviewHandler."""

    @pytest.fixture
    def mock_wallet_repository(self) -> MagicMock:
        """Create a mock wallet repository."""
        repo = MagicMock()
        repo.count_all = AsyncMock(return_value=100)
        repo.count_active_wallets = AsyncMock(return_value=80)
        repo.count_by_provider = AsyncMock(side_effect=lambda p: {
            WalletProvider.PRIVY: 50,
            WalletProvider.IMPORTED: 30,
            WalletProvider.EXTERNAL: 20,
        }.get(p, 0))
        return repo

    @pytest.fixture
    def mock_transaction_repository(self) -> MagicMock:
        """Create a mock transaction repository."""
        repo = MagicMock()
        repo.count_all = AsyncMock(return_value=500)
        repo.count_by_status = AsyncMock(side_effect=lambda s: {
            TransactionStatus.PENDING: 10,
            TransactionStatus.SUCCESS: 450,
            TransactionStatus.FAILED: 40,
        }.get(s, 0))
        repo.get_unique_user_count = AsyncMock(return_value=50)
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_wallet_repository: MagicMock,
        mock_transaction_repository: MagicMock,
    ) -> GetAdminMetricsOverviewHandler:
        """Create handler with mocked repositories."""
        return GetAdminMetricsOverviewHandler(
            wallet_repository=mock_wallet_repository,
            transaction_repository=mock_transaction_repository,
        )

    @pytest.mark.asyncio
    async def test_get_overview_returns_all_metrics(
        self,
        handler: GetAdminMetricsOverviewHandler,
    ):
        """Test that overview returns all metric categories."""
        result = await handler.execute()

        # Verify wallet metrics
        assert result.wallets.total_wallets == 100
        assert result.wallets.active_wallets == 80
        assert result.wallets.privy_wallets == 50
        assert result.wallets.imported_wallets == 30
        assert result.wallets.external_wallets == 20

        # Verify transaction metrics
        assert result.transactions.total_transactions == 500
        assert result.transactions.pending_transactions == 10
        assert result.transactions.successful_transactions == 450
        assert result.transactions.failed_transactions == 40

        # Verify user activity metrics
        assert result.users.total_users_with_transactions == 50

        # Verify timestamp is present
        assert result.generated_at is not None

    @pytest.mark.asyncio
    async def test_get_overview_handles_wallet_repo_error(
        self,
        handler: GetAdminMetricsOverviewHandler,
        mock_wallet_repository: MagicMock,
    ):
        """Test graceful handling of wallet repository errors."""
        mock_wallet_repository.count_all = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await handler.execute()

        # Should return zero for wallet metrics
        assert result.wallets.total_wallets == 0

        # Transaction metrics should still work
        assert result.transactions.total_transactions == 500

    @pytest.mark.asyncio
    async def test_get_overview_handles_transaction_repo_error(
        self,
        handler: GetAdminMetricsOverviewHandler,
        mock_transaction_repository: MagicMock,
    ):
        """Test graceful handling of transaction repository errors."""
        mock_transaction_repository.count_all = AsyncMock(
            side_effect=Exception("Database error")
        )

        result = await handler.execute()

        # Should return zero for transaction metrics
        assert result.transactions.total_transactions == 0

        # Wallet metrics should still work
        assert result.wallets.total_wallets == 100


class TestGetTransactionTimeSeriesHandler:
    """Tests for GetTransactionTimeSeriesHandler."""

    @pytest.fixture
    def mock_transaction_repository(self) -> MagicMock:
        """Create a mock transaction repository."""
        repo = MagicMock()
        now = datetime.now(UTC)
        repo.get_daily_transaction_counts = AsyncMock(return_value=[
            (now - timedelta(days=2), 10),
            (now - timedelta(days=1), 25),
            (now, 30),
        ])
        repo.count_transactions_in_range = AsyncMock(return_value=65)
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_transaction_repository: MagicMock,
    ) -> GetTransactionTimeSeriesHandler:
        """Create handler with mocked repository."""
        return GetTransactionTimeSeriesHandler(
            transaction_repository=mock_transaction_repository,
        )

    @pytest.mark.asyncio
    async def test_get_time_series_returns_data_points(
        self,
        handler: GetTransactionTimeSeriesHandler,
    ):
        """Test that time series returns data points."""
        now = datetime.now(UTC)
        from_date = now - timedelta(days=7)

        data_points, total = await handler.execute(
            from_date=from_date,
            to_date=now,
        )

        assert len(data_points) == 3
        assert total == 65
        assert data_points[0].value == 10
        assert data_points[1].value == 25
        assert data_points[2].value == 30

    @pytest.mark.asyncio
    async def test_get_time_series_with_chain_filter(
        self,
        handler: GetTransactionTimeSeriesHandler,
        mock_transaction_repository: MagicMock,
    ):
        """Test time series with chain filter."""
        now = datetime.now(UTC)
        from_date = now - timedelta(days=7)

        await handler.execute(
            from_date=from_date,
            to_date=now,
            chain="ethereum",
        )

        # Verify the repository was called with chain filter
        mock_transaction_repository.get_daily_transaction_counts.assert_called()

    @pytest.mark.asyncio
    async def test_get_time_series_handles_error(
        self,
        handler: GetTransactionTimeSeriesHandler,
        mock_transaction_repository: MagicMock,
    ):
        """Test graceful handling of errors."""
        mock_transaction_repository.get_daily_transaction_counts = AsyncMock(
            side_effect=Exception("Database error")
        )

        now = datetime.now(UTC)
        data_points, total = await handler.execute(
            from_date=now - timedelta(days=7),
            to_date=now,
        )

        assert data_points == []
        assert total == 0


class TestGetWalletTimeSeriesHandler:
    """Tests for GetWalletTimeSeriesHandler."""

    @pytest.fixture
    def mock_wallet_repository(self) -> MagicMock:
        """Create a mock wallet repository."""
        repo = MagicMock()
        now = datetime.now(UTC)
        repo.get_daily_wallet_counts = AsyncMock(return_value=[
            (now - timedelta(days=2), 5),
            (now - timedelta(days=1), 8),
            (now, 12),
        ])
        repo.count_wallets_created_in_range = AsyncMock(return_value=25)
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_wallet_repository: MagicMock,
    ) -> GetWalletTimeSeriesHandler:
        """Create handler with mocked repository."""
        return GetWalletTimeSeriesHandler(
            wallet_repository=mock_wallet_repository,
        )

    @pytest.mark.asyncio
    async def test_get_wallet_time_series(
        self,
        handler: GetWalletTimeSeriesHandler,
    ):
        """Test wallet time series data."""
        now = datetime.now(UTC)
        from_date = now - timedelta(days=7)

        data_points, total = await handler.execute(
            from_date=from_date,
            to_date=now,
        )

        assert len(data_points) == 3
        assert total == 25


class TestGetUserActivityTimeSeriesHandler:
    """Tests for GetUserActivityTimeSeriesHandler."""

    @pytest.fixture
    def mock_transaction_repository(self) -> MagicMock:
        """Create a mock transaction repository."""
        repo = MagicMock()
        now = datetime.now(UTC)
        repo.get_active_users_per_day = AsyncMock(return_value=[
            (now - timedelta(days=2), 15),
            (now - timedelta(days=1), 20),
            (now, 25),
        ])
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_transaction_repository: MagicMock,
    ) -> GetUserActivityTimeSeriesHandler:
        """Create handler with mocked repository."""
        return GetUserActivityTimeSeriesHandler(
            transaction_repository=mock_transaction_repository,
        )

    @pytest.mark.asyncio
    async def test_get_user_activity_time_series(
        self,
        handler: GetUserActivityTimeSeriesHandler,
    ):
        """Test user activity time series data."""
        now = datetime.now(UTC)
        from_date = now - timedelta(days=7)

        data_points = await handler.execute(
            from_date=from_date,
            to_date=now,
        )

        assert len(data_points) == 3
        assert data_points[0].value == 15
        assert data_points[1].value == 20
        assert data_points[2].value == 25


class TestGetWalletDistributionHandler:
    """Tests for GetWalletDistributionHandler."""

    @pytest.fixture
    def mock_wallet_repository(self) -> MagicMock:
        """Create a mock wallet repository."""
        repo = MagicMock()
        repo.get_wallet_counts_by_provider = AsyncMock(return_value={
            "privy": 50,
            "imported": 30,
            "external": 20,
        })
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_wallet_repository: MagicMock,
    ) -> GetWalletDistributionHandler:
        """Create handler with mocked repository."""
        return GetWalletDistributionHandler(
            wallet_repository=mock_wallet_repository,
        )

    @pytest.mark.asyncio
    async def test_get_wallet_distribution(
        self,
        handler: GetWalletDistributionHandler,
    ):
        """Test wallet distribution data."""
        distribution, total = await handler.execute()

        assert total == 100
        assert len(distribution) == 3

        # Find privy distribution
        privy_dist = next(d for d in distribution if d.name == "privy")
        assert privy_dist.count == 50
        assert privy_dist.percentage == 50.0


class TestGetTransactionDistributionHandler:
    """Tests for GetTransactionDistributionHandler."""

    @pytest.fixture
    def mock_transaction_repository(self) -> MagicMock:
        """Create a mock transaction repository."""
        repo = MagicMock()
        repo.count_all = AsyncMock(return_value=100)
        repo.get_transaction_counts_by_chain = AsyncMock(return_value={
            "ethereum": 60,
            "polygon": 40,
        })
        repo.get_transaction_counts_by_status = AsyncMock(return_value={
            "SUCCESS": 80,
            "PENDING": 15,
            "FAILED": 5,
        })
        repo.get_transaction_counts_by_type = AsyncMock(return_value={
            "SEND": 70,
            "SWAP": 30,
        })
        return repo

    @pytest.fixture
    def handler(
        self,
        mock_transaction_repository: MagicMock,
    ) -> GetTransactionDistributionHandler:
        """Create handler with mocked repository."""
        return GetTransactionDistributionHandler(
            transaction_repository=mock_transaction_repository,
        )

    @pytest.mark.asyncio
    async def test_get_transaction_distribution(
        self,
        handler: GetTransactionDistributionHandler,
    ):
        """Test transaction distribution data."""
        by_chain, by_status, by_type, total = await handler.execute()

        assert total == 100
        assert len(by_chain) == 2
        assert len(by_status) == 3
        assert len(by_type) == 2

        # Verify chain distribution
        eth_dist = next(d for d in by_chain if d.name == "ethereum")
        assert eth_dist.count == 60
        assert eth_dist.percentage == 60.0
