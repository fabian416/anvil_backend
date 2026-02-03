"""
Admin Analytics Router for User Context Analytics.

Provides API endpoints for viewing user distribution analytics,
trends, and cohort analysis.

All endpoints require admin authentication.
"""

from datetime import date, timedelta
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException, Query, Security, status
from pydantic import BaseModel, Field

from app.domain.chat.entities.analytics_snapshot import (
    AnalyticsSnapshot,
    AnalyticsTrend,
)
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Admin - Analytics"],
)


# ═══════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════


class DistributionResponse(BaseModel):
    """Response for user distribution endpoint."""

    portfolio: dict[str, int] = Field(
        description="User count by portfolio state (empty, starter, active, whale)"
    )
    activity: dict[str, int] = Field(description="User count by activity level")
    user_types: dict[str, int] = Field(description="User count by behavioral type")
    executions: dict[str, int] = Field(description="Total executions by type")
    totals: dict[str, Any] = Field(description="Total users and balance")


class SnapshotResponse(BaseModel):
    """Response for a single analytics snapshot."""

    id: str
    snapshot_date: str
    snapshot_type: str
    portfolio: dict[str, int]
    activity: dict[str, int]
    user_types: dict[str, int]
    executions: dict[str, int]
    total_users: int
    total_balance_usd: float
    created_at: str | None


class SnapshotListResponse(BaseModel):
    """Response for list of snapshots."""

    snapshots: list[SnapshotResponse]
    count: int
    start_date: str
    end_date: str


class TrendResponse(BaseModel):
    """Response for a single trend metric."""

    metric_name: str
    current_value: float | int
    previous_value: float | int
    change_absolute: float | int
    change_percent: float
    trend: str  # "up", "down", "stable"


class TrendsListResponse(BaseModel):
    """Response for list of trends."""

    trends: list[TrendResponse]
    current_date: str
    comparison_date: str


class SummaryResponse(BaseModel):
    """Response for analytics summary."""

    total_users: int
    total_balance_usd: float
    engaged_users: int
    execution_users: int
    total_executions: int
    portfolio_distribution: dict[str, float]
    activity_distribution: dict[str, float]
    user_type_distribution: dict[str, float]
    as_of_date: str


# ═══════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@router.get(
    "/users/distribution",
    response_model=DistributionResponse,
    summary="Get current user distribution",
    description="Get the current distribution of users by portfolio state, activity level, and user type.",
)
@inject
async def get_user_distribution(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
) -> DistributionResponse:
    """Get current user distribution by all classifications."""
    try:
        summary = await analytics_repo.get_user_distribution_summary()
        return DistributionResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch distribution: {str(e)}",
        )


@router.get(
    "/users/summary",
    response_model=SummaryResponse,
    summary="Get analytics summary",
    description="Get a high-level summary of user analytics with percentages.",
)
@inject
async def get_analytics_summary(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
) -> SummaryResponse:
    """Get analytics summary with key metrics and percentages."""
    try:
        latest = await analytics_repo.get_latest("daily")

        if not latest:
            return SummaryResponse(
                total_users=0,
                total_balance_usd=0.0,
                engaged_users=0,
                execution_users=0,
                total_executions=0,
                portfolio_distribution={},
                activity_distribution={},
                user_type_distribution={},
                as_of_date=date.today().isoformat(),
            )

        total = latest.total_users or 1  # Avoid division by zero

        # Calculate percentages
        portfolio_pct = {
            "empty": round(latest.portfolio.empty / total * 100, 1),
            "starter": round(latest.portfolio.starter / total * 100, 1),
            "active": round(latest.portfolio.active / total * 100, 1),
            "whale": round(latest.portfolio.whale / total * 100, 1),
        }

        activity_pct = {
            "new": round(latest.activity.new / total * 100, 1),
            "very_active": round(latest.activity.very_active / total * 100, 1),
            "active": round(latest.activity.active / total * 100, 1),
            "weekly_active": round(latest.activity.weekly_active / total * 100, 1),
            "monthly_active": round(latest.activity.monthly_active / total * 100, 1),
            "inactive": round(latest.activity.inactive / total * 100, 1),
            "reactivated": round(latest.activity.reactivated / total * 100, 1),
        }

        user_type_pct = {
            "new_user": round(latest.user_types.new_user / total * 100, 1),
            "casual": round(latest.user_types.casual / total * 100, 1),
            "trader": round(latest.user_types.trader / total * 100, 1),
            "yield_farmer": round(latest.user_types.yield_farmer / total * 100, 1),
            "power_user": round(latest.user_types.power_user / total * 100, 1),
        }

        return SummaryResponse(
            total_users=latest.total_users,
            total_balance_usd=float(latest.total_balance_usd),
            engaged_users=latest.activity.engaged,
            execution_users=latest.user_types.execution_focused,
            total_executions=latest.executions.total,
            portfolio_distribution=portfolio_pct,
            activity_distribution=activity_pct,
            user_type_distribution=user_type_pct,
            as_of_date=latest.snapshot_date.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch summary: {str(e)}",
        )


@router.get(
    "/snapshots/latest",
    response_model=SnapshotResponse,
    summary="Get latest snapshot",
    description="Get the most recent analytics snapshot.",
)
@inject
async def get_latest_snapshot(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
    snapshot_type: Annotated[
        str, Query(description="Snapshot type: daily, weekly, monthly")
    ] = "daily",
) -> SnapshotResponse:
    """Get the most recent snapshot of a given type."""
    try:
        snapshot = await analytics_repo.get_latest(snapshot_type)

        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {snapshot_type} snapshot found",
            )

        return _snapshot_to_response(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch snapshot: {str(e)}",
        )


@router.get(
    "/snapshots/history",
    response_model=SnapshotListResponse,
    summary="Get snapshot history",
    description="Get historical snapshots for a date range.",
)
@inject
async def get_snapshot_history(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
    days: Annotated[
        int, Query(description="Number of days to look back", ge=1, le=365)
    ] = 30,
    snapshot_type: Annotated[
        str, Query(description="Snapshot type: daily, weekly, monthly")
    ] = "daily",
) -> SnapshotListResponse:
    """Get historical snapshots for the last N days."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        snapshots = await analytics_repo.get_range(start_date, end_date, snapshot_type)

        return SnapshotListResponse(
            snapshots=[_snapshot_to_response(s) for s in snapshots],
            count=len(snapshots),
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}",
        )


@router.get(
    "/snapshots/date/{snapshot_date}",
    response_model=SnapshotResponse,
    summary="Get snapshot by date",
    description="Get a specific snapshot by date.",
)
@inject
async def get_snapshot_by_date(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
    snapshot_date: date,
    snapshot_type: Annotated[
        str, Query(description="Snapshot type: daily, weekly, monthly")
    ] = "daily",
) -> SnapshotResponse:
    """Get a snapshot for a specific date."""
    try:
        snapshot = await analytics_repo.get_by_date(snapshot_date, snapshot_type)

        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {snapshot_type} snapshot found for {snapshot_date}",
            )

        return _snapshot_to_response(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch snapshot: {str(e)}",
        )


@router.get(
    "/trends/week-over-week",
    response_model=TrendsListResponse,
    summary="Get week-over-week trends",
    description="Get trends comparing this week to last week.",
)
@inject
async def get_week_over_week_trends(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
) -> TrendsListResponse:
    """Get week-over-week trends for key metrics."""
    try:
        current = date.today()
        previous = current - timedelta(days=7)

        trends = await analytics_repo.get_week_over_week()

        return TrendsListResponse(
            trends=[_trend_to_response(t) for t in trends],
            current_date=current.isoformat(),
            comparison_date=previous.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}",
        )


@router.get(
    "/trends/month-over-month",
    response_model=TrendsListResponse,
    summary="Get month-over-month trends",
    description="Get trends comparing this month to last month.",
)
@inject
async def get_month_over_month_trends(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
) -> TrendsListResponse:
    """Get month-over-month trends for key metrics."""
    try:
        current = date.today()
        previous = current - timedelta(days=30)

        trends = await analytics_repo.get_month_over_month()

        return TrendsListResponse(
            trends=[_trend_to_response(t) for t in trends],
            current_date=current.isoformat(),
            comparison_date=previous.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}",
        )


@router.get(
    "/trends/custom",
    response_model=TrendsListResponse,
    summary="Get custom trends",
    description="Get trends comparing two specific dates.",
)
@inject
async def get_custom_trends(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
    current_date: Annotated[date, Query(description="Current date for comparison")],
    comparison_date: Annotated[date, Query(description="Previous date for comparison")],
    snapshot_type: Annotated[
        str, Query(description="Snapshot type: daily, weekly, monthly")
    ] = "daily",
) -> TrendsListResponse:
    """Get trends comparing two custom dates."""
    try:
        trends = await analytics_repo.get_trends(
            current_date, comparison_date, snapshot_type
        )

        return TrendsListResponse(
            trends=[_trend_to_response(t) for t in trends],
            current_date=current_date.isoformat(),
            comparison_date=comparison_date.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trends: {str(e)}",
        )


@router.get(
    "/totals",
    summary="Get total metrics",
    description="Get total users and total balance.",
)
@inject
async def get_totals(
    authorization: Annotated[str, Security(bearer_scheme)],
    analytics_repo: FromDishka[AnalyticsRepository],
) -> dict[str, Any]:
    """Get total users and total balance."""
    try:
        total_users = await analytics_repo.get_total_users()
        total_balance = await analytics_repo.get_total_balance()

        return {
            "total_users": total_users,
            "total_balance_usd": total_balance,
            "as_of": date.today().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch totals: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def _snapshot_to_response(snapshot: AnalyticsSnapshot) -> SnapshotResponse:
    """Convert AnalyticsSnapshot entity to response model."""
    return SnapshotResponse(
        id=str(snapshot.id),
        snapshot_date=snapshot.snapshot_date.isoformat(),
        snapshot_type=snapshot.snapshot_type,
        portfolio=snapshot.portfolio.to_dict(),
        activity=snapshot.activity.to_dict(),
        user_types=snapshot.user_types.to_dict(),
        executions=snapshot.executions.to_dict(),
        total_users=snapshot.total_users,
        total_balance_usd=float(snapshot.total_balance_usd),
        created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
    )


def _trend_to_response(trend: AnalyticsTrend) -> TrendResponse:
    """Convert AnalyticsTrend entity to response model."""
    return TrendResponse(
        metric_name=trend.metric_name,
        current_value=trend.current_value,
        previous_value=trend.previous_value,
        change_absolute=trend.change_absolute,
        change_percent=trend.change_percent,
        trend=trend.trend,
    )
