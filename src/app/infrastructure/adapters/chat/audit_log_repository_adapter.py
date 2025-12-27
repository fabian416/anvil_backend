"""
Audit log repository adapter implementation.

SQLAlchemy implementation of AuditLogRepository port for PostgreSQL.
Optimized for high-volume logging with indexed queries for compliance reporting.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Text, and_, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Index

from app.domain.entities.chat.audit_log import AuditLogEntry
from app.domain.enums.audit_event_type import AuditEventType
from app.domain.ports.audit_log_repository import AuditLogRepository
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry


class AuditLogRepositoryAdapter(AuditLogRepository):
    """
    SQLAlchemy adapter for audit logs.

    Implements persistence for audit log entries using PostgreSQL with JSONB
    for flexible metadata storage. Optimized for compliance reporting with
    indexed queries and retention policy support.
    """

    def __init__(self, session: MainAsyncSession) -> None:
        """
        Initialize repository adapter.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def save(self, entry: AuditLogEntry) -> AuditLogEntry:
        """
        Save audit log entry.

        Args:
            entry: Audit log entry to save

        Returns:
            Saved audit log entry
        """
        try:
            model = self._to_model(entry)
            self._session.add(model)
            await self._session.commit()
            return entry

        except Exception:
            await self._session.rollback()
            raise

    async def save_batch(self, entries: List[AuditLogEntry]) -> List[AuditLogEntry]:
        """
        Save multiple audit log entries in batch.

        Args:
            entries: List of audit log entries to save

        Returns:
            List of saved audit log entries
        """
        try:
            models = [self._to_model(entry) for entry in entries]
            self._session.add_all(models)
            await self._session.commit()
            return entries

        except Exception:
            await self._session.rollback()
            raise

    async def get_by_id(self, entry_id: UUID) -> Optional[AuditLogEntry]:
        """
        Get audit log entry by ID.

        Args:
            entry_id: Entry identifier

        Returns:
            AuditLogEntry or None if not found
        """
        stmt = select(AuditLogModel).where(AuditLogModel.entry_id == entry_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return None

        return self._to_domain(model)

    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        conditions = [AuditLogModel.user_id == user_id]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_event_type(
        self,
        event_type: AuditEventType,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs by event type.

        Args:
            event_type: Event type to filter by
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        conditions = [AuditLogModel.event_type == event_type.value]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_resource(
        self,
        resource_id: UUID,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for a specific resource.

        Args:
            resource_id: Resource identifier
            resource_type: Optional resource type filter
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of audit log entries (most recent first)
        """
        conditions = [AuditLogModel.resource_id == resource_id]

        if resource_type:
            conditions.append(AuditLogModel.resource_type == resource_type)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_security_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        outcome: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """
        Get security-related audit logs.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            outcome: Filter by outcome ("success", "failure")

        Returns:
            List of security event entries (most recent first)
        """
        # Get all security event types
        security_event_types = [
            event_type.value
            for event_type in AuditEventType
            if event_type.is_security_event
        ]

        conditions = [AuditLogModel.event_type.in_(security_event_types)]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)
        if outcome:
            conditions.append(AuditLogModel.outcome == outcome)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_data_access_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get data access audit logs (PII, sensitive data).

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of data access entries (most recent first)
        """
        # Get all data access event types
        data_access_event_types = [
            event_type.value
            for event_type in AuditEventType
            if event_type.is_data_access_event
        ]

        conditions = [AuditLogModel.event_type.in_(data_access_event_types)]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_failed_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
    ) -> List[AuditLogEntry]:
        """
        Get failed audit log entries.

        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            event_type: Optional event type filter

        Returns:
            List of failed entries (most recent first)
        """
        conditions = [AuditLogModel.outcome == "failure"]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)
        if event_type:
            conditions.append(AuditLogModel.event_type == event_type.value)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def get_by_ip_address(
        self,
        ip_address: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs from a specific IP address.

        Args:
            ip_address: IP address to filter by
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            List of audit log entries (most recent first)
        """
        conditions = [AuditLogModel.ip_address == ip_address]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    async def count_by_user(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count audit log entries for a user.

        Args:
            user_id: User identifier
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Number of audit log entries
        """
        conditions = [AuditLogModel.user_id == user_id]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = select(func.count()).select_from(AuditLogModel).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_event_type(
        self,
        event_type: AuditEventType,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Count audit log entries by event type.

        Args:
            event_type: Event type to filter by
            start_date: Filter entries after this date
            end_date: Filter entries before this date

        Returns:
            Number of audit log entries
        """
        conditions = [AuditLogModel.event_type == event_type.value]

        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)

        stmt = select(func.count()).select_from(AuditLogModel).where(and_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def delete_old_entries(
        self, retention_days: int, exclude_critical: bool = True
    ) -> int:
        """
        Delete audit log entries older than retention period.

        Args:
            retention_days: Number of days to retain
            exclude_critical: If True, preserve security/compliance events

        Returns:
            Number of entries deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            conditions = [AuditLogModel.created_at < cutoff_date]

            if exclude_critical:
                # Exclude security events, data access events, and admin actions
                critical_event_types = [
                    event_type.value
                    for event_type in AuditEventType
                    if event_type.requires_retention
                ]
                conditions.append(
                    AuditLogModel.event_type.notin_(critical_event_types)
                )

            stmt = select(AuditLogModel).where(and_(*conditions))
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            count = len(models)
            for model in models:
                await self._session.delete(model)

            await self._session.commit()
            return count

        except Exception:
            await self._session.rollback()
            return 0

    async def get_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[AuditEventType]] = None,
    ) -> List[AuditLogEntry]:
        """
        Get audit logs for compliance reporting.

        Args:
            start_date: Start of reporting period
            end_date: End of reporting period
            event_types: Optional list of event types to include

        Returns:
            List of audit log entries for the period
        """
        conditions = [
            AuditLogModel.created_at >= start_date,
            AuditLogModel.created_at <= end_date,
        ]

        if event_types:
            event_type_values = [event_type.value for event_type in event_types]
            conditions.append(AuditLogModel.event_type.in_(event_type_values))

        stmt = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(AuditLogModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [self._to_domain(model) for model in models]

    # =========================================================================
    # CONVERSION METHODS
    # =========================================================================

    def _to_domain(self, model: "AuditLogModel") -> AuditLogEntry:
        """
        Convert database model to domain entity.

        Args:
            model: Database model

        Returns:
            AuditLogEntry domain entity
        """
        return AuditLogEntry(
            id=model.entry_id,
            event_type=AuditEventType(model.event_type),
            action=model.action,
            outcome=model.outcome,
            user_id=model.user_id,
            resource_id=model.resource_id,
            resource_type=model.resource_type,
            metadata=model.entry_metadata or {},
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            error_message=model.error_message,
            error_code=model.error_code,
            created_at=model.created_at,
        )

    def _to_model(self, entry: AuditLogEntry) -> "AuditLogModel":
        """
        Convert domain entity to database model.

        Args:
            entry: Domain entity

        Returns:
            Database model
        """
        return AuditLogModel(
            entry_id=entry.id,
            event_type=entry.event_type.value,
            action=entry.action,
            outcome=entry.outcome,
            user_id=entry.user_id,
            resource_id=entry.resource_id,
            resource_type=entry.resource_type,
            entry_metadata=entry.metadata,
            ip_address=entry.ip_address,
            user_agent=entry.user_agent,
            error_message=entry.error_message,
            error_code=entry.error_code,
            created_at=entry.created_at,
        )


# =============================================================================
# DATABASE MODEL
# =============================================================================


@mapping_registry.mapped
class AuditLogModel:
    """
    SQLAlchemy model for audit logs.

    Maps to 'audit_logs' table in PostgreSQL with optimized indexes
    for compliance reporting and security monitoring.
    """

    __tablename__ = "audit_logs"

    entry_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Context
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    resource_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Additional Data (JSONB for flexible storage)
    entry_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Error details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamp (immutable, indexed for efficient queries)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True, default=datetime.utcnow
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        # Index for user activity queries
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        # Index for event type queries with time range
        Index("ix_audit_logs_event_created", "event_type", "created_at"),
        # Index for security monitoring
        Index("ix_audit_logs_event_outcome", "event_type", "outcome"),
        # Index for IP-based queries
        Index("ix_audit_logs_ip_created", "ip_address", "created_at"),
        # Index for resource activity
        Index("ix_audit_logs_resource", "resource_id", "resource_type"),
        # Allow table redefinition in tests
        {"extend_existing": True},
    )
