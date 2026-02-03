"""
SQLAlchemy implementation of the UserMetricsRepository.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select, func, distinct

from app.application.metrics.ports import (
    UserMetricsRepository,
    UserMetricsSummary,
    UserEventFilter,
)
from app.domain.entities.user_event import UserEvent
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.mappings.user_event import (
    map_user_events_table,
)
from app.infrastructure.persistence_sqla.registry import mapping_registry


class UserMetricsRepositorySqla(UserMetricsRepository):
    """SQLAlchemy implementation for user metrics/events."""

    def __init__(self, session: MainAsyncSession) -> None:
        map_user_events_table()
        self._session = session
        self._table = mapping_registry.metadata.tables["user_events"]

    async def record_event(self, event: UserEvent) -> int:
        """Record a new user event."""
        stmt = (
            self._table.insert()
            .values(
                user_id=event.user_id.value,
                event_type=event.event_type,
                event_category=event.event_category,
                properties=event.properties,
                device_type=event.device_type,
                platform=event.platform,
                app_version=event.app_version,
                session_id=event.session_id,
                ip_address=event.ip_address,
                country_code=event.country_code,
            )
            .returning(self._table.c.id)
        )

        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    async def get_events(
        self,
        filters: UserEventFilter,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get user events with optional filters."""
        stmt = select(self._table).order_by(self._table.c.created_at.desc())

        if filters.get("user_id"):
            stmt = stmt.where(self._table.c.user_id == filters["user_id"])
        if filters.get("event_type"):
            stmt = stmt.where(self._table.c.event_type == filters["event_type"])
        if filters.get("event_category"):
            stmt = stmt.where(self._table.c.event_category == filters["event_category"])
        if filters.get("device_type"):
            stmt = stmt.where(self._table.c.device_type == filters["device_type"])
        if filters.get("platform"):
            stmt = stmt.where(self._table.c.platform == filters["platform"])
        if filters.get("from_date"):
            stmt = stmt.where(self._table.c.created_at >= filters["from_date"])
        if filters.get("to_date"):
            stmt = stmt.where(self._table.c.created_at <= filters["to_date"])

        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "event_type": row.event_type,
                "event_category": row.event_category,
                "properties": row.properties,
                "device_type": row.device_type,
                "platform": row.platform,
                "app_version": row.app_version,
                "session_id": row.session_id,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]

    async def get_user_metrics_summary(self, user_id: int) -> UserMetricsSummary | None:
        """Get a summary of metrics for a specific user."""
        stats_stmt = select(
            func.count(self._table.c.id).label("total_events"),
            func.min(self._table.c.created_at).label("first_event_at"),
            func.max(self._table.c.created_at).label("last_event_at"),
        ).where(self._table.c.user_id == user_id)

        stats_result = await self._session.execute(stats_stmt)
        stats = stats_result.fetchone()

        if not stats or stats.total_events == 0:
            return None

        category_stmt = (
            select(
                self._table.c.event_category,
                func.count(self._table.c.id).label("count"),
            )
            .where(
                self._table.c.user_id == user_id,
                self._table.c.event_category.isnot(None),
            )
            .group_by(self._table.c.event_category)
        )

        category_result = await self._session.execute(category_stmt)
        events_by_category = {
            r.event_category: r.count for r in category_result.fetchall()
        }

        type_stmt = (
            select(
                self._table.c.event_type,
                func.count(self._table.c.id).label("count"),
            )
            .where(self._table.c.user_id == user_id)
            .group_by(self._table.c.event_type)
        )

        type_result = await self._session.execute(type_stmt)
        events_by_type = {r.event_type: r.count for r in type_result.fetchall()}

        devices_stmt = select(distinct(self._table.c.device_type)).where(
            self._table.c.user_id == user_id,
            self._table.c.device_type.isnot(None),
        )
        devices_result = await self._session.execute(devices_stmt)
        devices_used = [r[0] for r in devices_result.fetchall()]

        platforms_stmt = select(distinct(self._table.c.platform)).where(
            self._table.c.user_id == user_id,
            self._table.c.platform.isnot(None),
        )
        platforms_result = await self._session.execute(platforms_stmt)
        platforms_used = [r[0] for r in platforms_result.fetchall()]

        return UserMetricsSummary(
            user_id=user_id,
            total_events=stats.total_events,
            first_event_at=stats.first_event_at,
            last_event_at=stats.last_event_at,
            events_by_category=events_by_category,
            events_by_type=events_by_type,
            devices_used=devices_used,
            platforms_used=platforms_used,
        )

    async def get_event_count(
        self,
        user_id: int | None = None,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """Get the count of events matching criteria."""
        stmt = select(func.count(self._table.c.id))

        if user_id:
            stmt = stmt.where(self._table.c.user_id == user_id)
        if event_type:
            stmt = stmt.where(self._table.c.event_type == event_type)
        if from_date:
            stmt = stmt.where(self._table.c.created_at >= from_date)
        if to_date:
            stmt = stmt.where(self._table.c.created_at <= to_date)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_active_users_count(
        self,
        from_date: datetime,
        to_date: datetime | None = None,
    ) -> int:
        """Get the count of unique active users in a date range."""
        stmt = select(func.count(distinct(self._table.c.user_id))).where(
            self._table.c.created_at >= from_date
        )

        if to_date:
            stmt = stmt.where(self._table.c.created_at <= to_date)

        result = await self._session.execute(stmt)
        return result.scalar_one()
