"""
Analytics Snapshot entity for user context analytics.

This entity stores aggregated metrics about user classifications
at a point in time (daily, weekly, monthly snapshots).
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class PortfolioDistribution:
    """Distribution of users by portfolio state."""

    empty: int = 0
    starter: int = 0
    active: int = 0
    whale: int = 0

    @property
    def total(self) -> int:
        return self.empty + self.starter + self.active + self.whale

    def to_dict(self) -> dict[str, int]:
        return {
            "empty": self.empty,
            "starter": self.starter,
            "active": self.active,
            "whale": self.whale,
            "total": self.total,
        }

    def to_percentages(self) -> dict[str, float]:
        """Convert counts to percentages."""
        total = self.total
        if total == 0:
            return {"empty": 0, "starter": 0, "active": 0, "whale": 0}
        return {
            "empty": round(self.empty / total * 100, 1),
            "starter": round(self.starter / total * 100, 1),
            "active": round(self.active / total * 100, 1),
            "whale": round(self.whale / total * 100, 1),
        }


@dataclass
class ActivityDistribution:
    """Distribution of users by activity level."""

    new: int = 0
    very_active: int = 0
    active: int = 0
    weekly_active: int = 0
    monthly_active: int = 0
    inactive: int = 0
    reactivated: int = 0

    @property
    def total(self) -> int:
        return (
            self.new
            + self.very_active
            + self.active
            + self.weekly_active
            + self.monthly_active
            + self.inactive
            + self.reactivated
        )

    @property
    def engaged(self) -> int:
        """Users who are actively engaged (new + very_active + active + weekly)."""
        return self.new + self.very_active + self.active + self.weekly_active

    def to_dict(self) -> dict[str, int]:
        return {
            "new": self.new,
            "very_active": self.very_active,
            "active": self.active,
            "weekly_active": self.weekly_active,
            "monthly_active": self.monthly_active,
            "inactive": self.inactive,
            "reactivated": self.reactivated,
            "total": self.total,
            "engaged": self.engaged,
        }


@dataclass
class UserTypeDistribution:
    """Distribution of users by behavioral type."""

    new_user: int = 0
    casual: int = 0
    trader: int = 0
    yield_farmer: int = 0
    power_user: int = 0

    @property
    def total(self) -> int:
        return (
            self.new_user
            + self.casual
            + self.trader
            + self.yield_farmer
            + self.power_user
        )

    @property
    def execution_focused(self) -> int:
        """Users who focus on executions (trader + yield_farmer + power_user)."""
        return self.trader + self.yield_farmer + self.power_user

    def to_dict(self) -> dict[str, int]:
        return {
            "new_user": self.new_user,
            "casual": self.casual,
            "trader": self.trader,
            "yield_farmer": self.yield_farmer,
            "power_user": self.power_user,
            "total": self.total,
            "execution_focused": self.execution_focused,
        }


@dataclass
class ExecutionMetrics:
    """Aggregate execution metrics."""

    total: int = 0
    swap: int = 0
    buy: int = 0
    lending: int = 0
    transfer: int = 0
    cashout: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total": self.total,
            "swap": self.swap,
            "buy": self.buy,
            "lending": self.lending,
            "transfer": self.transfer,
            "cashout": self.cashout,
        }


@dataclass
class AnalyticsSnapshot:
    """
    Snapshot of user analytics at a point in time.

    Stores aggregated metrics about user classifications
    for trend analysis and business insights.
    """

    id: UUID
    snapshot_date: date
    snapshot_type: str  # "daily", "weekly", "monthly"

    # Distribution data
    portfolio: PortfolioDistribution
    activity: ActivityDistribution
    user_types: UserTypeDistribution
    executions: ExecutionMetrics

    # Aggregate totals
    total_users: int = 0
    total_balance_usd: Decimal = Decimal("0")

    # Timestamps
    created_at: datetime | None = None

    # Additional metrics (flexible)
    additional_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "snapshot_date": self.snapshot_date.isoformat(),
            "snapshot_type": self.snapshot_type,
            "portfolio": self.portfolio.to_dict(),
            "activity": self.activity.to_dict(),
            "user_types": self.user_types.to_dict(),
            "executions": self.executions.to_dict(),
            "total_users": self.total_users,
            "total_balance_usd": float(self.total_balance_usd),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "additional_metrics": self.additional_metrics,
        }

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of key metrics."""
        return {
            "date": self.snapshot_date.isoformat(),
            "type": self.snapshot_type,
            "total_users": self.total_users,
            "total_balance_usd": float(self.total_balance_usd),
            "engaged_users": self.activity.engaged,
            "execution_users": self.user_types.execution_focused,
            "total_executions": self.executions.total,
        }


@dataclass
class AnalyticsTrend:
    """
    Trend data for comparing analytics over time.
    """

    metric_name: str
    current_value: int | float
    previous_value: int | float
    change_absolute: int | float
    change_percent: float
    trend: str  # "up", "down", "stable"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "change_absolute": self.change_absolute,
            "change_percent": self.change_percent,
            "trend": self.trend,
        }

    @classmethod
    def calculate(
        cls,
        metric_name: str,
        current: int | float,
        previous: int | float,
    ) -> "AnalyticsTrend":
        """Calculate trend from two values."""
        change = current - previous
        if previous == 0:
            pct = 100.0 if current > 0 else 0.0
        else:
            pct = round((change / previous) * 100, 1)

        if change > 0:
            trend = "up"
        elif change < 0:
            trend = "down"
        else:
            trend = "stable"

        return cls(
            metric_name=metric_name,
            current_value=current,
            previous_value=previous,
            change_absolute=change,
            change_percent=pct,
            trend=trend,
        )


@dataclass
class CohortAnalysis:
    """
    Cohort analysis for user groups.
    """

    cohort_name: str  # e.g., "2026-01", "week-3"
    cohort_size: int
    retention_day_1: float  # Percentage
    retention_day_7: float
    retention_day_30: float
    avg_executions: float
    avg_balance_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "cohort_name": self.cohort_name,
            "cohort_size": self.cohort_size,
            "retention_day_1": self.retention_day_1,
            "retention_day_7": self.retention_day_7,
            "retention_day_30": self.retention_day_30,
            "avg_executions": self.avg_executions,
            "avg_balance_usd": self.avg_balance_usd,
        }
