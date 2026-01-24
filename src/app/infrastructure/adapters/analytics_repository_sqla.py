"""
SQLAlchemy implementation of AnalyticsRepository.

Provides persistence and querying for analytics snapshots.
"""

import logging
from datetime import date, datetime, timedelta, UTC
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities.analytics_snapshot import (
    AnalyticsSnapshot,
    PortfolioDistribution,
    ActivityDistribution,
    UserTypeDistribution,
    ExecutionMetrics,
    AnalyticsTrend,
    CohortAnalysis,
)
from app.domain.chat.ports.analytics_repository import AnalyticsRepository
from app.infrastructure.persistence_sqla.mappings.analytics_snapshot import (
    AnalyticsSnapshotTable,
)

logger = logging.getLogger(__name__)


class AnalyticsRepositorySqla(AnalyticsRepository):
    """SQLAlchemy implementation of AnalyticsRepository."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._table = AnalyticsSnapshotTable
    
    # ═══════════════════════════════════════════════════════════════
    # SNAPSHOT CRUD
    # ═══════════════════════════════════════════════════════════════
    
    async def save(self, snapshot: AnalyticsSnapshot) -> None:
        """Save or update an analytics snapshot using upsert."""
        data = self._entity_to_dict(snapshot)
        
        # Use PostgreSQL upsert (INSERT ... ON CONFLICT UPDATE)
        stmt = pg_insert(self._table).values(**data)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_analytics_snapshot_date_type",
            set_={
                "portfolio_empty_count": stmt.excluded.portfolio_empty_count,
                "portfolio_starter_count": stmt.excluded.portfolio_starter_count,
                "portfolio_active_count": stmt.excluded.portfolio_active_count,
                "portfolio_whale_count": stmt.excluded.portfolio_whale_count,
                "activity_new_count": stmt.excluded.activity_new_count,
                "activity_very_active_count": stmt.excluded.activity_very_active_count,
                "activity_active_count": stmt.excluded.activity_active_count,
                "activity_weekly_active_count": stmt.excluded.activity_weekly_active_count,
                "activity_monthly_active_count": stmt.excluded.activity_monthly_active_count,
                "activity_inactive_count": stmt.excluded.activity_inactive_count,
                "activity_reactivated_count": stmt.excluded.activity_reactivated_count,
                "type_new_user_count": stmt.excluded.type_new_user_count,
                "type_casual_count": stmt.excluded.type_casual_count,
                "type_trader_count": stmt.excluded.type_trader_count,
                "type_yield_farmer_count": stmt.excluded.type_yield_farmer_count,
                "type_power_user_count": stmt.excluded.type_power_user_count,
                "total_users": stmt.excluded.total_users,
                "total_executions": stmt.excluded.total_executions,
                "total_balance_usd": stmt.excluded.total_balance_usd,
                "exec_swap_count": stmt.excluded.exec_swap_count,
                "exec_buy_count": stmt.excluded.exec_buy_count,
                "exec_lending_count": stmt.excluded.exec_lending_count,
                "exec_transfer_count": stmt.excluded.exec_transfer_count,
                "exec_cashout_count": stmt.excluded.exec_cashout_count,
                "additional_metrics": stmt.excluded.additional_metrics,
            },
        )
        
        await self._session.execute(stmt)
        await self._session.commit()
        logger.info(f"Saved analytics snapshot for {snapshot.snapshot_date} ({snapshot.snapshot_type})")
    
    async def get_by_id(self, snapshot_id: UUID) -> AnalyticsSnapshot | None:
        """Get a snapshot by ID."""
        stmt = select(self._table).where(self._table.c.id == snapshot_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    async def get_by_date(
        self,
        snapshot_date: date,
        snapshot_type: str = "daily",
    ) -> AnalyticsSnapshot | None:
        """Get a snapshot by date and type."""
        stmt = select(self._table).where(
            and_(
                self._table.c.snapshot_date == snapshot_date,
                self._table.c.snapshot_type == snapshot_type,
            )
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    async def get_latest(
        self,
        snapshot_type: str = "daily",
    ) -> AnalyticsSnapshot | None:
        """Get the most recent snapshot of a given type."""
        stmt = (
            select(self._table)
            .where(self._table.c.snapshot_type == snapshot_type)
            .order_by(desc(self._table.c.snapshot_date))
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if row:
            return self._row_to_entity(row)
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # HISTORICAL DATA
    # ═══════════════════════════════════════════════════════════════
    
    async def get_range(
        self,
        start_date: date,
        end_date: date,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsSnapshot]:
        """Get snapshots within a date range."""
        stmt = (
            select(self._table)
            .where(
                and_(
                    self._table.c.snapshot_date >= start_date,
                    self._table.c.snapshot_date <= end_date,
                    self._table.c.snapshot_type == snapshot_type,
                )
            )
            .order_by(self._table.c.snapshot_date)
        )
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        return [self._row_to_entity(row) for row in rows]
    
    async def get_last_n_days(
        self,
        days: int = 30,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsSnapshot]:
        """Get the last N days of snapshots."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return await self.get_range(start_date, end_date, snapshot_type)
    
    # ═══════════════════════════════════════════════════════════════
    # TREND ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_trends(
        self,
        current_date: date,
        comparison_date: date,
        snapshot_type: str = "daily",
    ) -> list[AnalyticsTrend]:
        """Calculate trends between two dates."""
        current = await self.get_by_date(current_date, snapshot_type)
        previous = await self.get_by_date(comparison_date, snapshot_type)
        
        if not current or not previous:
            return []
        
        trends = []
        
        # Total users trend
        trends.append(AnalyticsTrend.calculate(
            "total_users",
            current.total_users,
            previous.total_users,
        ))
        
        # Total balance trend
        trends.append(AnalyticsTrend.calculate(
            "total_balance_usd",
            float(current.total_balance_usd),
            float(previous.total_balance_usd),
        ))
        
        # Portfolio distribution trends
        trends.append(AnalyticsTrend.calculate(
            "portfolio_empty",
            current.portfolio.empty,
            previous.portfolio.empty,
        ))
        trends.append(AnalyticsTrend.calculate(
            "portfolio_whale",
            current.portfolio.whale,
            previous.portfolio.whale,
        ))
        
        # Activity trends
        trends.append(AnalyticsTrend.calculate(
            "activity_engaged",
            current.activity.engaged,
            previous.activity.engaged,
        ))
        trends.append(AnalyticsTrend.calculate(
            "activity_inactive",
            current.activity.inactive,
            previous.activity.inactive,
        ))
        
        # Execution trends
        trends.append(AnalyticsTrend.calculate(
            "total_executions",
            current.executions.total,
            previous.executions.total,
        ))
        trends.append(AnalyticsTrend.calculate(
            "exec_swap",
            current.executions.swap,
            previous.executions.swap,
        ))
        trends.append(AnalyticsTrend.calculate(
            "exec_buy",
            current.executions.buy,
            previous.executions.buy,
        ))
        
        return trends
    
    async def get_week_over_week(
        self,
        reference_date: date | None = None,
    ) -> list[AnalyticsTrend]:
        """Get week-over-week trends."""
        current = reference_date or date.today()
        previous = current - timedelta(days=7)
        
        return await self.get_trends(current, previous, "daily")
    
    async def get_month_over_month(
        self,
        reference_date: date | None = None,
    ) -> list[AnalyticsTrend]:
        """Get month-over-month trends."""
        current = reference_date or date.today()
        previous = current - timedelta(days=30)
        
        return await self.get_trends(current, previous, "daily")
    
    # ═══════════════════════════════════════════════════════════════
    # AGGREGATIONS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_total_users(self) -> int:
        """Get total user count from latest snapshot."""
        latest = await self.get_latest("daily")
        return latest.total_users if latest else 0
    
    async def get_total_balance(self) -> float:
        """Get total balance from latest snapshot."""
        latest = await self.get_latest("daily")
        return float(latest.total_balance_usd) if latest else 0.0
    
    async def get_user_distribution_summary(self) -> dict:
        """Get current user distribution by all classifications."""
        latest = await self.get_latest("daily")
        
        if not latest:
            return {
                "portfolio": {},
                "activity": {},
                "user_types": {},
                "executions": {},
                "totals": {"users": 0, "balance_usd": 0},
            }
        
        return {
            "portfolio": latest.portfolio.to_dict(),
            "activity": latest.activity.to_dict(),
            "user_types": latest.user_types.to_dict(),
            "executions": latest.executions.to_dict(),
            "totals": {
                "users": latest.total_users,
                "balance_usd": float(latest.total_balance_usd),
            },
        }
    
    # ═══════════════════════════════════════════════════════════════
    # COHORT ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    async def get_cohort_analysis(
        self,
        cohort_type: str = "monthly",
        num_cohorts: int = 6,
    ) -> list[CohortAnalysis]:
        """
        Get cohort analysis for user groups.
        
        Note: This is a simplified implementation. Full cohort analysis
        requires joining with user_context_aware table.
        """
        # This is a placeholder - full implementation would need
        # to query user_context_aware with registration dates
        # and calculate retention metrics
        return []
    
    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def _row_to_entity(self, row: Any) -> AnalyticsSnapshot:
        """Convert database row to AnalyticsSnapshot entity."""
        return AnalyticsSnapshot(
            id=row.id,
            snapshot_date=row.snapshot_date,
            snapshot_type=row.snapshot_type,
            portfolio=PortfolioDistribution(
                empty=row.portfolio_empty_count,
                starter=row.portfolio_starter_count,
                active=row.portfolio_active_count,
                whale=row.portfolio_whale_count,
            ),
            activity=ActivityDistribution(
                new=row.activity_new_count,
                very_active=row.activity_very_active_count,
                active=row.activity_active_count,
                weekly_active=row.activity_weekly_active_count,
                monthly_active=row.activity_monthly_active_count,
                inactive=row.activity_inactive_count,
                reactivated=row.activity_reactivated_count,
            ),
            user_types=UserTypeDistribution(
                new_user=row.type_new_user_count,
                casual=row.type_casual_count,
                trader=row.type_trader_count,
                yield_farmer=row.type_yield_farmer_count,
                power_user=row.type_power_user_count,
            ),
            executions=ExecutionMetrics(
                total=row.total_executions,
                swap=row.exec_swap_count,
                buy=row.exec_buy_count,
                lending=row.exec_lending_count,
                transfer=row.exec_transfer_count,
                cashout=row.exec_cashout_count,
            ),
            total_users=row.total_users,
            total_balance_usd=Decimal(str(row.total_balance_usd)),
            created_at=row.created_at,
            additional_metrics=row.additional_metrics or {},
        )
    
    def _entity_to_dict(self, entity: AnalyticsSnapshot) -> dict[str, Any]:
        """Convert AnalyticsSnapshot entity to dictionary for insert/update."""
        return {
            "id": entity.id,
            "snapshot_date": entity.snapshot_date,
            "snapshot_type": entity.snapshot_type,
            "portfolio_empty_count": entity.portfolio.empty,
            "portfolio_starter_count": entity.portfolio.starter,
            "portfolio_active_count": entity.portfolio.active,
            "portfolio_whale_count": entity.portfolio.whale,
            "activity_new_count": entity.activity.new,
            "activity_very_active_count": entity.activity.very_active,
            "activity_active_count": entity.activity.active,
            "activity_weekly_active_count": entity.activity.weekly_active,
            "activity_monthly_active_count": entity.activity.monthly_active,
            "activity_inactive_count": entity.activity.inactive,
            "activity_reactivated_count": entity.activity.reactivated,
            "type_new_user_count": entity.user_types.new_user,
            "type_casual_count": entity.user_types.casual,
            "type_trader_count": entity.user_types.trader,
            "type_yield_farmer_count": entity.user_types.yield_farmer,
            "type_power_user_count": entity.user_types.power_user,
            "total_users": entity.total_users,
            "total_executions": entity.executions.total,
            "total_balance_usd": entity.total_balance_usd,
            "exec_swap_count": entity.executions.swap,
            "exec_buy_count": entity.executions.buy,
            "exec_lending_count": entity.executions.lending,
            "exec_transfer_count": entity.executions.transfer,
            "exec_cashout_count": entity.executions.cashout,
            "additional_metrics": entity.additional_metrics,
        }
