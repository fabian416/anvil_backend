"""
Analytics Repository Port for user context analytics.

Defines the interface for persisting and querying analytics snapshots.
"""

from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.chat.entities.analytics_snapshot import (
    AnalyticsSnapshot,
    AnalyticsTrend,
    CohortAnalysis,
)


class AnalyticsRepository(Protocol):
    """
    Repository interface for analytics snapshots.
    
    Provides methods for:
    - Saving daily/weekly/monthly snapshots
    - Querying historical data
    - Calculating trends
    - Cohort analysis
    """
    
    # ═══════════════════════════════════════════════════════════════
    # SNAPSHOT CRUD
    # ═══════════════════════════════════════════════════════════════
    
    async def save(self, snapshot: AnalyticsSnapshot) -> None:
        """
        Save or update an analytics snapshot.
        
        Uses upsert to handle duplicate date/type combinations.
        """
        ...
    
    async def get_by_id(self, snapshot_id: UUID) -> AnalyticsSnapshot | None:
        """Get a snapshot by ID."""
        ...
    
    async def get_by_date(
        self,
        snapshot_date: date,
        snapshot_type: str = "daily",
    ) -> AnalyticsSnapshot | None:
        """Get a snapshot by date and type."""
        ...
    
    async def get_latest(
        self,
        snapshot_type: str = "daily",
    ) -> AnalyticsSnapshot | None:
        """Get the most recent snapshot of a given type."""
        ...
    
    # ═══════════════════════════════════════════════════════════════
    # HISTORICAL DATA
    # ═══════════════════════════════════════════════════════════════
    
    async def get_range(
        self,
        start_date: date,
        end_date: date,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsSnapshot]:
        """
        Get snapshots within a date range.
        
        Returns snapshots ordered by date ascending.
        """
        ...
    
    async def get_last_n_days(
        self,
        days: int = 30,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsSnapshot]:
        """Get the last N days of snapshots."""
        ...
    
    # ═══════════════════════════════════════════════════════════════
    # TREND ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_trends(
        self,
        current_date: date,
        comparison_date: date,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsTrend]:
        """
        Calculate trends between two dates.
        
        Returns trends for all key metrics.
        """
        ...
    
    async def get_week_over_week(
        self,
        reference_date: date | None = None,
    ) -> list[AnalyticsTrend]:
        """Get week-over-week trends."""
        ...
    
    async def get_month_over_month(
        self,
        reference_date: date | None = None,
    ) -> list[AnalyticsTrend]:
        """Get month-over-month trends."""
        ...
    
    # ═══════════════════════════════════════════════════════════════
    # AGGREGATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_total_users(self) -> int:
        """Get total user count from latest snapshot."""
        ...
    
    async def get_total_balance(self) -> float:
        """Get total balance from latest snapshot."""
        ...
    
    async def get_user_distribution_summary(self) -> dict:
        """Get current user distribution by all classifications."""
        ...
    
    # ═══════════════════════════════════════════════════════════════
    # COHORT ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_cohort_analysis(
        self,
        cohort_type: str = "monthly",  # "weekly", "monthly"
        num_cohorts: int = 6,
    ) -> list[CohortAnalysis]:
        """
        Get cohort analysis for user groups.
        
        Note: This requires joining with user_context_aware table
        and calculating retention metrics.
        """
        ...
