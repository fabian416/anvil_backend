"""
SQLAlchemy mapping for user_lending_preferences table.

Maps UserLendingPreferences domain entity to database table using explicit imperative mapping.
"""

from sqlalchemy import String, Numeric, Boolean, DateTime, Enum
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_user_lending_preferences_table() -> None:
    """Map user_lending_preferences table (idempotent)."""
    if "user_lending_preferences" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class UserLendingPreferencesTable:
        """
        Table metadata for user_lending_preferences.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "user_lending_preferences"
        __table_args__ = (
            sa.Index("idx_user_lending_preferences_user_id", "user_id"),
            {"extend_existing": True},
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        user_id = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
        risk_tolerance = mapped_column(
            Enum(
                "conservative",
                "moderate",
                "aggressive",
                name="risk_tolerance_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="moderate",
        )
        min_health_factor = mapped_column(
            Numeric(10, 2), nullable=False, server_default="1.5"
        )
        max_leverage = mapped_column(
            Numeric(3, 1), nullable=False, server_default="3.0"
        )
        preferred_protocol = mapped_column(String(20), nullable=True)
        auto_rebalance = mapped_column(Boolean, nullable=False, server_default="false")
        notification_health_threshold = mapped_column(
            Numeric(10, 2), nullable=True, server_default="1.3"
        )
        notification_email = mapped_column(String(255), nullable=True)
        notification_enabled = mapped_column(
            Boolean, nullable=False, server_default="true"
        )
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
