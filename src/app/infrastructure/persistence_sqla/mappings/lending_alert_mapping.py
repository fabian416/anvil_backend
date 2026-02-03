"""
SQLAlchemy mapping for lending_alerts table.

Maps LendingAlert domain entity to database table using explicit imperative mapping.
"""

from sqlalchemy import String, Numeric, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_lending_alerts_table() -> None:
    """Map lending_alerts table (idempotent)."""
    if "lending_alerts" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LendingAlertsTable:
        """
        Table metadata for lending_alerts.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "lending_alerts"
        __table_args__ = (
            sa.Index("idx_lending_alerts_user_id", "user_id"),
            sa.Index("idx_lending_alerts_is_read", "is_read"),
            sa.Index("idx_lending_alerts_severity", "severity"),
            sa.Index("idx_lending_alerts_created_at", "created_at"),
            sa.Index(
                "idx_lending_alerts_user_unread",
                "user_id",
                "is_read",
                postgresql_where=sa.text("is_read = false"),
            ),
            {"extend_existing": True},
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        user_id = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
        position_id = mapped_column(UUID(as_uuid=True), nullable=True)
        alert_type = mapped_column(
            Enum(
                "health_factor_low",
                "liquidation_risk",
                "position_closed",
                "loop_completed",
                "loop_failed",
                "rate_change",
                name="alert_type_enum",
                create_type=False,
            ),
            nullable=False,
        )
        severity = mapped_column(
            Enum(
                "info",
                "warning",
                "critical",
                name="alert_severity_enum",
                create_type=False,
            ),
            nullable=False,
        )
        title = mapped_column(String(255), nullable=False)
        message = mapped_column(Text, nullable=False)
        health_factor = mapped_column(Numeric(10, 2), nullable=True)
        threshold_value = mapped_column(Numeric(18, 2), nullable=True)
        current_value = mapped_column(Numeric(18, 2), nullable=True)
        is_read = mapped_column(Boolean, nullable=False, server_default="false")
        sent_at = mapped_column(DateTime(timezone=True), nullable=True)
        metadata_ = mapped_column("metadata", JSONB, nullable=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
