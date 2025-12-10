"""
Admin Metrics Router.

FastAPI router for admin analytics/metrics endpoints.
All endpoints require admin authentication.

Endpoints:
- GET /admin/metrics/overview - High-level stats overview
- GET /admin/metrics/transactions/timeseries - Transaction counts over time
- GET /admin/metrics/wallets/timeseries - Wallet creation over time
- GET /admin/metrics/users/activity - User activity over time
- GET /admin/metrics/wallets/distribution - Wallet distribution by provider
- GET /admin/metrics/transactions/distribution - Transaction distribution
"""

from datetime import UTC, datetime, timedelta

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query, Security, status

from app.application.queries.admin.get_metrics import (
    GetAdminMetricsOverviewHandler,
    GetTransactionDistributionHandler,
    GetTransactionTimeSeriesHandler,
    GetUserActivityTimeSeriesHandler,
    GetWalletDistributionHandler,
    GetWalletTimeSeriesHandler,
)
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme
from app.presentation.http.schemas.admin.metrics import (
    AdminMetricsOverview,
    DistributionItem,
    TimeSeriesDataPoint,
    TransactionDistributionResponse,
    TransactionOverviewMetrics,
    TransactionTimeSeriesResponse,
    UserActivityTimeSeriesResponse,
    UserOverviewMetrics,
    WalletDistributionResponse,
    WalletOverviewMetrics,
    WalletTimeSeriesResponse,
)


def create_admin_metrics_router() -> APIRouter:
    """Create and configure the admin metrics router."""

    router = APIRouter(prefix="/admin/metrics", tags=["Admin - Metrics"])

    @router.get(
        "/overview",
        response_model=AdminMetricsOverview,
        status_code=status.HTTP_200_OK,
        summary="Get metrics overview",
        description=(
            "Get high-level overview of system metrics including wallet counts, "
            "transaction counts, and user activity. Requires admin authentication."
        ),
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_metrics_overview(
        handler: FromDishka[GetAdminMetricsOverviewHandler],
    ) -> AdminMetricsOverview:
        """
        Get admin metrics overview.

        Returns high-level statistics for wallets, transactions, and user activity.
        """
        result = await handler.execute()

        return AdminMetricsOverview(
            wallets=WalletOverviewMetrics(
                total_wallets=result.wallets.total_wallets,
                active_wallets=result.wallets.active_wallets,
                privy_wallets=result.wallets.privy_wallets,
                imported_wallets=result.wallets.imported_wallets,
                external_wallets=result.wallets.external_wallets,
            ),
            transactions=TransactionOverviewMetrics(
                total_transactions=result.transactions.total_transactions,
                pending_transactions=result.transactions.pending_transactions,
                successful_transactions=result.transactions.successful_transactions,
                failed_transactions=result.transactions.failed_transactions,
            ),
            users=UserOverviewMetrics(
                total_users_with_transactions=result.users.total_users_with_transactions,
                active_users_today=result.users.active_users_today,
                active_users_7d=result.users.active_users_7d,
                active_users_30d=result.users.active_users_30d,
            ),
            generated_at=result.generated_at,
        )

    @router.get(
        "/transactions/timeseries",
        response_model=TransactionTimeSeriesResponse,
        status_code=status.HTTP_200_OK,
        summary="Get transaction time series",
        description=(
            "Get transaction counts over time. Supports filtering by chain and "
            "transaction type. Data is grouped by day by default."
        ),
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_transaction_timeseries(
        handler: FromDishka[GetTransactionTimeSeriesHandler],
        from_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC) - timedelta(days=30),
            description="Start date (defaults to 30 days ago)",
        ),
        to_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC),
            description="End date (defaults to now)",
        ),
        chain: str | None = Query(None, description="Filter by chain (e.g., ethereum, polygon)"),
        tx_type: str | None = Query(None, description="Filter by transaction type (e.g., SEND, SWAP)"),
        group_by: str = Query("day", description="Grouping interval: day, week, month"),
    ) -> TransactionTimeSeriesResponse:
        """
        Get transaction time series data.

        Returns transaction counts grouped by day (or specified interval)
        within the date range.
        """
        data_points, total_count = await handler.execute(
            from_date=from_date,
            to_date=to_date,
            chain=chain,
            tx_type=tx_type,
        )

        return TransactionTimeSeriesResponse(
            data=[
                TimeSeriesDataPoint(date=point.date, value=point.value)
                for point in data_points
            ],
            from_date=from_date,
            to_date=to_date,
            group_by=group_by,
            chain=chain,
            tx_type=tx_type,
            total_count=total_count,
        )

    @router.get(
        "/wallets/timeseries",
        response_model=WalletTimeSeriesResponse,
        status_code=status.HTTP_200_OK,
        summary="Get wallet creation time series",
        description=(
            "Get wallet creation counts over time. "
            "Data is grouped by day by default."
        ),
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_wallet_timeseries(
        handler: FromDishka[GetWalletTimeSeriesHandler],
        from_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC) - timedelta(days=30),
            description="Start date (defaults to 30 days ago)",
        ),
        to_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC),
            description="End date (defaults to now)",
        ),
        group_by: str = Query("day", description="Grouping interval: day, week, month"),
    ) -> WalletTimeSeriesResponse:
        """
        Get wallet creation time series data.

        Returns wallet creation counts grouped by day within the date range.
        """
        data_points, total_count = await handler.execute(
            from_date=from_date,
            to_date=to_date,
        )

        return WalletTimeSeriesResponse(
            data=[
                TimeSeriesDataPoint(date=point.date, value=point.value)
                for point in data_points
            ],
            from_date=from_date,
            to_date=to_date,
            group_by=group_by,
            total_count=total_count,
        )

    @router.get(
        "/users/activity",
        response_model=UserActivityTimeSeriesResponse,
        status_code=status.HTTP_200_OK,
        summary="Get user activity time series",
        description=(
            "Get unique active users per day. "
            "A user is considered active if they made at least one transaction."
        ),
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_user_activity_timeseries(
        handler: FromDishka[GetUserActivityTimeSeriesHandler],
        from_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC) - timedelta(days=30),
            description="Start date (defaults to 30 days ago)",
        ),
        to_date: datetime = Query(
            default_factory=lambda: datetime.now(UTC),
            description="End date (defaults to now)",
        ),
    ) -> UserActivityTimeSeriesResponse:
        """
        Get user activity time series data.

        Returns unique user counts per day within the date range.
        """
        data_points = await handler.execute(
            from_date=from_date,
            to_date=to_date,
        )

        return UserActivityTimeSeriesResponse(
            data=[
                TimeSeriesDataPoint(date=point.date, value=point.value)
                for point in data_points
            ],
            from_date=from_date,
            to_date=to_date,
        )

    @router.get(
        "/wallets/distribution",
        response_model=WalletDistributionResponse,
        status_code=status.HTTP_200_OK,
        summary="Get wallet distribution",
        description="Get distribution of wallets by provider (privy, imported, external).",
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_wallet_distribution(
        handler: FromDishka[GetWalletDistributionHandler],
    ) -> WalletDistributionResponse:
        """
        Get wallet distribution by provider.

        Returns counts and percentages for each provider type.
        """
        distribution, total = await handler.execute()

        return WalletDistributionResponse(
            by_provider=[
                DistributionItem(
                    name=item.name,
                    count=item.count,
                    percentage=item.percentage,
                )
                for item in distribution
            ],
            total=total,
        )

    @router.get(
        "/transactions/distribution",
        response_model=TransactionDistributionResponse,
        status_code=status.HTTP_200_OK,
        summary="Get transaction distribution",
        description="Get distribution of transactions by chain, status, and type.",
        dependencies=[Security(bearer_scheme)],
    )
    @inject
    async def get_transaction_distribution(
        handler: FromDishka[GetTransactionDistributionHandler],
    ) -> TransactionDistributionResponse:
        """
        Get transaction distribution by various dimensions.

        Returns counts and percentages for chain, status, and transaction type.
        """
        by_chain, by_status, by_type, total = await handler.execute()

        return TransactionDistributionResponse(
            by_chain=[
                DistributionItem(
                    name=item.name,
                    count=item.count,
                    percentage=item.percentage,
                )
                for item in by_chain
            ],
            by_status=[
                DistributionItem(
                    name=item.name,
                    count=item.count,
                    percentage=item.percentage,
                )
                for item in by_status
            ],
            by_type=[
                DistributionItem(
                    name=item.name,
                    count=item.count,
                    percentage=item.percentage,
                )
                for item in by_type
            ],
            total=total,
        )

    return router
