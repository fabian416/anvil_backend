"""Add GraphRAG ML features

Revision ID: graphrag_ml_001
Revises: (previous_revision)
Create Date: 2025-12-01 10:00:00.000000

Tables created:
- user_preferences
- saved_searches
- user_portfolios
- protocol_exposures
- risk_alerts
- alert_subscriptions
- search_history
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "graphrag_ml_001"
down_revision: Union[str, None] = None  # Update with actual previous revision
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_preferences table
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("risk_tolerance", sa.String(20), nullable=False, default="moderate"),
        sa.Column("preferred_chains", postgresql.JSONB, nullable=False, default="[]"),
        sa.Column(
            "preferred_categories", postgresql.JSONB, nullable=False, default="[]"
        ),
        sa.Column("excluded_protocols", postgresql.JSONB, nullable=False, default="[]"),
        sa.Column("favorite_protocols", postgresql.JSONB, nullable=False, default="[]"),
        sa.Column("search_settings", postgresql.JSONB, nullable=False, default="{}"),
        sa.Column(
            "notification_settings", postgresql.JSONB, nullable=False, default="{}"
        ),
        sa.Column("default_currency", sa.String(10), nullable=False, default="USD"),
        sa.Column("theme", sa.String(20), nullable=False, default="dark"),
        sa.Column("compact_mode", sa.Boolean, nullable=False, default=False),
        sa.Column("analytics_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("personalization_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_user_preferences_user_id", "user_preferences", ["user_id"])

    # Create saved_searches table
    op.create_table(
        "saved_searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("filters", postgresql.JSONB, nullable=False, default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_saved_searches_user_id", "saved_searches", ["user_id"])

    # Create user_portfolios table
    op.create_table(
        "user_portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("total_value_usd", sa.Numeric(20, 2), nullable=False, default=0),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_user_portfolios_user_id", "user_portfolios", ["user_id"])

    # Create protocol_exposures table
    op.create_table(
        "protocol_exposures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "portfolio_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column(
            "protocol_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("protocol_name", sa.String(200), nullable=False),
        sa.Column("chain", sa.String(50), nullable=False),
        sa.Column(
            "position_type", sa.String(50), nullable=False
        ),  # supplied, borrowed, lp, staked
        sa.Column("amount_usd", sa.Numeric(20, 2), nullable=False),
        sa.Column(
            "entry_date", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_protocol_exposures_portfolio_id", "protocol_exposures", ["portfolio_id"]
    )
    op.create_index(
        "idx_protocol_exposures_protocol_id", "protocol_exposures", ["protocol_id"]
    )
    op.create_foreign_key(
        "fk_protocol_exposures_portfolio",
        "protocol_exposures",
        "user_portfolios",
        ["portfolio_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create risk_alerts table
    op.create_table(
        "risk_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "protocol_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        sa.Column("protocol_name", sa.String(200), nullable=False),
        sa.Column(
            "alert_type", sa.String(50), nullable=False
        ),  # risk_increase, anomaly, critical, dependency
        sa.Column(
            "severity", sa.String(20), nullable=False
        ),  # LOW, MEDIUM, HIGH, CRITICAL
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=False, default="{}"),
        sa.Column("recommendations", postgresql.JSONB, nullable=False, default="[]"),
        sa.Column("current_risk_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("previous_risk_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("risk_change", sa.Numeric(4, 2), nullable=True),
        sa.Column("acknowledged", sa.Boolean, nullable=False, default=False),
        sa.Column("dismissed", sa.Boolean, nullable=False, default=False),
        sa.Column("acted_upon", sa.Boolean, nullable=False, default=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_risk_alerts_user_id", "risk_alerts", ["user_id"])
    op.create_index("idx_risk_alerts_protocol_id", "risk_alerts", ["protocol_id"])
    op.create_index("idx_risk_alerts_severity", "risk_alerts", ["severity"])
    op.create_index("idx_risk_alerts_acknowledged", "risk_alerts", ["acknowledged"])
    op.create_index("idx_risk_alerts_created_at", "risk_alerts", ["created_at"])

    # Create alert_subscriptions table
    op.create_table(
        "alert_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("risk_alerts_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("anomaly_alerts_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "protocol_update_alerts_enabled", sa.Boolean, nullable=False, default=True
        ),
        sa.Column("price_alerts_enabled", sa.Boolean, nullable=False, default=True),
        sa.Column("min_severity", sa.String(20), nullable=False, default="MEDIUM"),
        sa.Column(
            "subscribed_protocols", postgresql.JSONB, nullable=False, default="[]"
        ),
        sa.Column("excluded_protocols", postgresql.JSONB, nullable=False, default="[]"),
        sa.Column("push_notifications", sa.Boolean, nullable=False, default=True),
        sa.Column("email_notifications", sa.Boolean, nullable=False, default=False),
        sa.Column("websocket_notifications", sa.Boolean, nullable=False, default=True),
        sa.Column("max_alerts_per_hour", sa.Integer, nullable=False, default=10),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_alert_subscriptions_user_id", "alert_subscriptions", ["user_id"]
    )

    # Create search_history table
    op.create_table(
        "search_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column(
            "search_type", sa.String(50), nullable=False
        ),  # hybrid, similar, contextual
        sa.Column("filters", postgresql.JSONB, nullable=False, default="{}"),
        sa.Column("results_count", sa.Integer, nullable=False),
        sa.Column("clicked_protocol_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("search_time_ms", sa.Integer, nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.create_index("idx_search_history_user_id", "search_history", ["user_id"])
    op.create_index("idx_search_history_created_at", "search_history", ["created_at"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("search_history")
    op.drop_table("alert_subscriptions")
    op.drop_table("risk_alerts")
    op.drop_table("protocol_exposures")
    op.drop_table("user_portfolios")
    op.drop_table("saved_searches")
    op.drop_table("user_preferences")
