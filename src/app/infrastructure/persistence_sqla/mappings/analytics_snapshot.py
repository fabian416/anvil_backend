"""
SQLAlchemy mapping for analytics_snapshots table.

This mapping defines the table structure for storing
aggregated user context analytics.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    Table,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.infrastructure.persistence_sqla.registry import mapping_registry


# Define the table
AnalyticsSnapshotTable = Table(
    "analytics_snapshots",
    mapping_registry.metadata,
    # Primary key
    Column(
        "id",
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    # Snapshot identification
    Column("snapshot_date", Date, nullable=False),
    Column("snapshot_type", String(50), nullable=False),
    # Portfolio state counts
    Column("portfolio_empty_count", Integer, nullable=False, default=0),
    Column("portfolio_starter_count", Integer, nullable=False, default=0),
    Column("portfolio_active_count", Integer, nullable=False, default=0),
    Column("portfolio_whale_count", Integer, nullable=False, default=0),
    # Activity level counts
    Column("activity_new_count", Integer, nullable=False, default=0),
    Column("activity_very_active_count", Integer, nullable=False, default=0),
    Column("activity_active_count", Integer, nullable=False, default=0),
    Column("activity_weekly_active_count", Integer, nullable=False, default=0),
    Column("activity_monthly_active_count", Integer, nullable=False, default=0),
    Column("activity_inactive_count", Integer, nullable=False, default=0),
    Column("activity_reactivated_count", Integer, nullable=False, default=0),
    # User type counts
    Column("type_new_user_count", Integer, nullable=False, default=0),
    Column("type_casual_count", Integer, nullable=False, default=0),
    Column("type_trader_count", Integer, nullable=False, default=0),
    Column("type_yield_farmer_count", Integer, nullable=False, default=0),
    Column("type_power_user_count", Integer, nullable=False, default=0),
    # Totals
    Column("total_users", Integer, nullable=False, default=0),
    Column("total_executions", Integer, nullable=False, default=0),
    Column(
        "total_balance_usd", Numeric(precision=20, scale=2), nullable=False, default=0
    ),
    # Execution counts
    Column("exec_swap_count", Integer, nullable=False, default=0),
    Column("exec_buy_count", Integer, nullable=False, default=0),
    Column("exec_lending_count", Integer, nullable=False, default=0),
    Column("exec_transfer_count", Integer, nullable=False, default=0),
    Column("exec_cashout_count", Integer, nullable=False, default=0),
    # Timestamps
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    ),
    # Additional metrics
    Column("additional_metrics", JSONB, nullable=False, default={}),
    # Constraints
    UniqueConstraint(
        "snapshot_date", "snapshot_type", name="uq_analytics_snapshot_date_type"
    ),
    # Indexes
    Index("idx_analytics_snapshot_date", "snapshot_date"),
    Index("idx_analytics_snapshot_type", "snapshot_type"),
)


def map_analytics_snapshot_table() -> None:
    """
    Map the AnalyticsSnapshot entity to the analytics_snapshots table.

    Note: This uses a simple dataclass, so we don't use SQLAlchemy ORM mapping.
    Instead, we use the table directly in the repository adapter.
    """
    # This function is called to ensure the table metadata is registered
    # The actual entity mapping is done in the repository adapter
    pass
