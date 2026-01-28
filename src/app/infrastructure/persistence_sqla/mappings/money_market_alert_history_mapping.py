"""
SQLAlchemy mapping for money_market_alert_history table.

Maps MoneyMarketAlert domain entity to database table using table-only mapping.
Stores rate change alerts triggered by user preferences.
"""

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_alert_history_table() -> None:
    """Map money_market_alert_history table (idempotent)."""
    if "money_market_alert_history" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MoneyMarketAlertHistoryTable:
        """
        Table metadata for money_market_alert_history.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "money_market_alert_history"
        __table_args__ = (
            # Indexes for common query patterns
            Index(
                "idx_money_market_alert_history_alert",
                "alert_id",
                "triggered_at",
            ),
            Index(
                "idx_money_market_alert_history_user",
                "user_id",
                "triggered_at",
            ),
            Index(
                "idx_money_market_alert_history_notification_status",
                "notification_sent",
                "triggered_at",
            ),
            {"extend_existing": True},
        )

        # Primary Key
        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )

        # Alert Reference
        alert_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("money_market_rate_alerts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # User Reference
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Alert Details
        alert_type = mapped_column(
            String(20),
            nullable=False,
        )
        condition_met = mapped_column(
            String(100),
            nullable=False,
            comment="Human-readable condition that was met",
        )

        # Rate Details
        protocol_name = mapped_column(
            String(50),
            nullable=False,
        )
        asset_symbol = mapped_column(
            String(20),
            nullable=False,
        )
        chain = mapped_column(
            String(20),
            nullable=False,
        )
        current_rate = mapped_column(
            Numeric(10, 4),
            nullable=False,
        )
        threshold_value = mapped_column(
            Numeric(10, 4),
            nullable=True,
        )

        # Notification Status
        notification_sent = mapped_column(
            Boolean,
            nullable=False,
            server_default="false",
        )
        notification_channels_used = mapped_column(
            ARRAY(String(20)),
            nullable=True,
        )
        notification_error = mapped_column(
            Text,
            nullable=True,
        )

        # Metadata
        metadata = mapped_column(
            "metadata",
            JSONB,
            nullable=True,
            comment="Additional context (rate_id, comparison results, etc.)",
        )

        # Timestamps
        triggered_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
        notified_at = mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
