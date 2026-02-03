"""
SQLAlchemy mapping for UserEvent table metadata.
Used for tracking user activity and metrics.
"""

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_user_events_table() -> None:
    """Map UserEvent entity to database table (idempotent)."""
    if "user_events" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class UserEventsTable:
        __tablename__ = "user_events"
        __table_args__ = (
            sa.Index("ix_user_events_user_event_type", "user_id", "event_type"),
            sa.Index("ix_user_events_created_at", "created_at"),
            {"extend_existing": True},
        )

        # Primary key
        id = mapped_column(Integer, primary_key=True, index=True)

        # User reference
        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Event information
        event_type = mapped_column(String(100), nullable=False, index=True)
        event_category = mapped_column(
            String(50), nullable=True, index=True
        )  # e.g., "auth", "trading", "navigation"

        # Event properties (flexible JSONB for any event-specific data)
        properties = mapped_column(JSONB, nullable=True, default={})

        # Device/client info
        device_type = mapped_column(
            String(50), nullable=True
        )  # "mobile", "desktop", "tablet"
        platform = mapped_column(String(50), nullable=True)  # "ios", "android", "web"
        app_version = mapped_column(String(20), nullable=True)

        # Session info
        session_id = mapped_column(String(255), nullable=True, index=True)

        # Network/location (optional, for analytics)
        ip_address = mapped_column(String(50), nullable=True)
        country_code = mapped_column(String(10), nullable=True)

        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )
