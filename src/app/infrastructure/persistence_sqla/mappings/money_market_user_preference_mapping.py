"""
SQLAlchemy mapping for money_market_user_preferences table.

Maps MoneyMarketUserPreference domain entity to database table using table-only mapping.
Stores user-specific rate alert preferences and notification settings.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_user_preferences_table() -> None:
    """Map money_market_user_preferences table (idempotent)."""
    if "money_market_user_preferences" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MoneyMarketUserPreferencesTable:
        """
        Table metadata for money_market_user_preferences.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "money_market_user_preferences"
        __table_args__ = (
            # Index on user_id (unique constraint)
            Index(
                "idx_money_market_user_preferences_user_id",
                "user_id",
            ),
            # Check constraints for validation
            CheckConstraint(
                "risk_tolerance IN ('conservative', 'moderate', 'aggressive')",
                name="chk_risk_tolerance",
            ),
            CheckConstraint(
                "sort_by IN ('best_rate', 'tvl', 'liquidity', 'utilization')",
                name="chk_sort_by",
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

        # User Reference (one-to-one)
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )

        # Preferred Protocols
        preferred_protocols = mapped_column(
            ARRAY(String(20)),
            nullable=True,
            comment="User's preferred protocols for comparisons",
        )
        excluded_protocols = mapped_column(
            ARRAY(String(20)),
            nullable=True,
            comment="Protocols to exclude from comparisons",
        )

        # Chain Preferences
        preferred_chains = mapped_column(
            ARRAY(String(20)),
            nullable=True,
            comment="Preferred blockchain networks",
        )

        # Rate Preferences
        min_supply_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Minimum acceptable supply APY",
        )
        max_borrow_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Maximum acceptable borrow APY",
        )

        # Risk Preferences
        risk_tolerance = mapped_column(
            String(20),
            nullable=False,
            server_default="moderate",
            comment="'conservative', 'moderate', 'aggressive'",
        )
        min_liquidity_usd = mapped_column(
            Numeric(20, 2),
            nullable=True,
            comment="Minimum liquidity required",
        )
        max_utilization_rate = mapped_column(
            Numeric(5, 2),
            nullable=True,
            comment="Maximum acceptable utilization rate",
        )

        # Notification Preferences
        enable_rate_alerts = mapped_column(
            Boolean,
            nullable=False,
            server_default="true",
        )
        notification_channels = mapped_column(
            ARRAY(String(20)),
            nullable=False,
            server_default="'{in_app}'",
            comment="Array of enabled notification channels",
        )

        # Display Preferences
        show_rewards = mapped_column(
            Boolean,
            nullable=False,
            server_default="true",
            comment="Include reward APY in comparisons",
        )
        sort_by = mapped_column(
            String(20),
            nullable=False,
            server_default="best_rate",
            comment="'best_rate', 'tvl', 'liquidity', 'utilization'",
        )

        # Timestamps
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
