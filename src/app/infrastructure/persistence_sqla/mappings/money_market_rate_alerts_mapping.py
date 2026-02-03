"""
SQLAlchemy mapping for money_market_rate_alerts table.

Maps rate monitoring alerts table for money market rate tracking.
This table stores user-configured alerts for rate changes.
"""

from sqlalchemy import (
    Boolean,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
import sqlalchemy as sa

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_rate_alerts_table() -> None:
    """Map money_market_rate_alerts table (idempotent)."""
    if "money_market_rate_alerts" in mapping_registry.metadata.tables:
        return  # Already mapped
    
    # Create enum types for SQLAlchemy
    alert_condition_enum = SQLEnum(
        "rate_above",
        "rate_below",
        "rate_change_percent",
        "best_rate_available",
        name="money_market_alert_condition_enum",
        create_type=False,  # Type already exists in DB
    )
    
    notification_channel_enum = SQLEnum(
        "email",
        "push",
        "in_app",
        name="money_market_notification_channel_enum",
        create_type=False,  # Type already exists in DB
    )
    
    table = sa.Table(
        "money_market_rate_alerts",
        mapping_registry.metadata,
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol & Asset
        sa.Column(
            "protocol_id",
            UUID(as_uuid=True),
            ForeignKey("money_market_protocols.id", ondelete="CASCADE"),
            nullable=True,
            comment="Null = any protocol",
        ),
        sa.Column(
            "asset_symbol",
            String(20),
            nullable=False,
        ),
        sa.Column(
            "chain",
            String(20),
            nullable=False,
        ),
        # Alert Configuration
        sa.Column(
            "alert_type",
            String(20),
            nullable=False,
            comment="'supply' or 'borrow'",
        ),
        sa.Column(
            "condition",
            alert_condition_enum,
            nullable=False,
        ),
        sa.Column(
            "threshold_value",
            Numeric(10, 4),
            nullable=True,
            comment="Threshold APY or percentage change",
        ),
        sa.Column(
            "notification_channels",
            ARRAY(notification_channel_enum),
            nullable=False,
            server_default=sa.text("ARRAY['in_app']::money_market_notification_channel_enum[]"),
            comment="Array of enabled notification channels",
        ),
        sa.Column(
            "cooldown_minutes",
            Integer,
            nullable=False,
            server_default="60",
            comment="Minimum time between alerts",
        ),
        # Status
        sa.Column(
            "is_active",
            Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "triggered_count",
            Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_triggered_at",
            TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    
    # Create indexes
    sa.Index(
        "idx_money_market_rate_alerts_user_active",
        table.c.user_id,
        table.c.is_active,
    )
    sa.Index(
        "idx_money_market_rate_alerts_asset_chain",
        table.c.asset_symbol,
        table.c.chain,
        table.c.is_active,
    )
    # Note: Cannot use NOW() in partial index (not immutable)
    # Use regular index for readiness checks - filter at query time
    sa.Index(
        "idx_money_market_rate_alerts_ready",
        table.c.asset_symbol,
        table.c.chain,
        table.c.condition,
        table.c.is_active,
        table.c.last_triggered_at,
    )
    
    # Check constraints
    sa.CheckConstraint(
        "alert_type IN ('supply', 'borrow')",
        name="chk_alert_type",
    )
    sa.CheckConstraint(
        "cooldown_minutes >= 1 AND cooldown_minutes <= 1440",
        name="chk_cooldown_range",
    )
