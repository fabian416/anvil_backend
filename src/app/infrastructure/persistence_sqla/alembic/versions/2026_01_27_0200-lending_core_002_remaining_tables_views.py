"""lending_core_002_remaining_tables_views

Create remaining lending tables and views:
- user_lending_preferences
- lending_health_checks
- leverage_loop_executions
- lending_alerts
- user_lending_summary view
- protocol_comparison view

Revision ID: lending_core_002
Revises: lending_core_001
Create Date: 2026-01-27 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic
revision = "lending_core_002"
down_revision = "lending_core_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create remaining lending tables and views."""

    # =========================================================================
    # CREATE ADDITIONAL POSTGRESQL ENUMS (idempotent)
    # =========================================================================

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_tolerance_enum') THEN
                CREATE TYPE risk_tolerance_enum AS ENUM ('conservative', 'moderate', 'aggressive');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'health_factor_level_enum') THEN
                CREATE TYPE health_factor_level_enum AS ENUM ('safe', 'caution', 'danger', 'critical', 'liquidatable');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'loop_status_enum') THEN
                CREATE TYPE loop_status_enum AS ENUM ('pending', 'in_progress', 'completed', 'failed', 'cancelled');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_type_enum') THEN
                CREATE TYPE alert_type_enum AS ENUM ('health_factor_low', 'liquidation_risk', 'position_closed', 'loop_completed', 'loop_failed', 'rate_change');
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_severity_enum') THEN
                CREATE TYPE alert_severity_enum AS ENUM ('info', 'warning', 'critical');
            END IF;
        END $$;
    """)

    # =========================================================================
    # TABLE: user_lending_preferences
    # =========================================================================

    op.create_table(
        "user_lending_preferences",
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
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Risk Preferences
        sa.Column(
            "risk_tolerance",
            sa.Enum(
                "conservative",
                "moderate",
                "aggressive",
                name="risk_tolerance_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="moderate",
        ),
        sa.Column(
            "min_health_factor",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="1.5",
        ),
        sa.Column(
            "max_leverage",
            sa.Numeric(3, 1),
            nullable=False,
            server_default="3.0",
        ),
        # Protocol Preferences
        sa.Column(
            "preferred_protocol",
            sa.String(20),
            nullable=True,
        ),
        # Auto-Management Settings
        sa.Column(
            "auto_rebalance",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        # Notification Settings
        sa.Column(
            "notification_health_threshold",
            sa.Numeric(10, 2),
            nullable=True,
            server_default="1.3",
        ),
        sa.Column(
            "notification_email",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "notification_enabled",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "risk_tolerance IN ('conservative', 'moderate', 'aggressive')",
            name="chk_risk_tolerance",
        ),
        sa.CheckConstraint(
            "preferred_protocol IN ('aave', 'morpho') OR preferred_protocol IS NULL",
            name="chk_preferred_protocol",
        ),
        sa.CheckConstraint(
            "min_health_factor >= 1.0 AND min_health_factor <= 10.0",
            name="chk_min_health_factor",
        ),
        sa.CheckConstraint(
            "max_leverage >= 1.0 AND max_leverage <= 10.0",
            name="chk_max_leverage",
        ),
    )

    # Indexes for user_lending_preferences
    op.create_index(
        "idx_user_lending_preferences_user_id",
        "user_lending_preferences",
        ["user_id"],
    )

    # =========================================================================
    # TABLE: lending_health_checks
    # =========================================================================

    op.create_table(
        "lending_health_checks",
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
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "chain",
            sa.String(50),
            nullable=False,
        ),
        # Health Metrics
        sa.Column(
            "health_factor",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "health_factor_level",
            sa.Enum(
                "safe",
                "caution",
                "danger",
                "critical",
                "liquidatable",
                name="health_factor_level_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "total_collateral_usd",
            sa.Numeric(18, 2),
            nullable=False,
        ),
        sa.Column(
            "total_debt_usd",
            sa.Numeric(18, 2),
            nullable=False,
        ),
        sa.Column(
            "available_to_borrow_usd",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        sa.Column(
            "liquidation_price",
            sa.Numeric(18, 8),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "checked_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "health_factor_level IN ('safe', 'caution', 'danger', 'critical', 'liquidatable')",
            name="chk_health_factor_level",
        ),
    )

    # Indexes for lending_health_checks
    op.create_index(
        "idx_lending_health_checks_user_id",
        "lending_health_checks",
        ["user_id"],
    )
    op.create_index(
        "idx_lending_health_checks_checked_at",
        "lending_health_checks",
        ["checked_at"],
    )
    op.create_index(
        "idx_lending_health_checks_health_level",
        "lending_health_checks",
        ["health_factor_level"],
    )
    op.create_index(
        "idx_lending_health_checks_user_protocol",
        "lending_health_checks",
        ["user_id", "protocol"],
    )

    # =========================================================================
    # TABLE: leverage_loop_executions
    # =========================================================================

    op.create_table(
        "leverage_loop_executions",
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
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol Information
        sa.Column(
            "protocol",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "chain",
            sa.String(50),
            nullable=False,
        ),
        # Asset Information
        sa.Column(
            "asset_address",
            sa.String(42),
            nullable=False,
        ),
        sa.Column(
            "asset_symbol",
            sa.String(10),
            nullable=False,
        ),
        # Loop Configuration
        sa.Column(
            "initial_amount",
            sa.Numeric(78, 18),
            nullable=False,
        ),
        sa.Column(
            "target_leverage",
            sa.Numeric(3, 1),
            nullable=False,
        ),
        sa.Column(
            "actual_leverage",
            sa.Numeric(3, 1),
            nullable=True,
        ),
        # Execution Progress
        sa.Column(
            "total_steps",
            sa.Integer,
            nullable=False,
        ),
        sa.Column(
            "current_step",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "steps_completed",
            sa.ARRAY(sa.Text),
            nullable=False,
            server_default="'{}'",
        ),
        # Status
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                "cancelled",
                name="loop_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        # Results
        sa.Column(
            "final_health_factor",
            sa.Numeric(10, 2),
            nullable=True,
        ),
        sa.Column(
            "final_collateral_usd",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        sa.Column(
            "final_debt_usd",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        # Cost Tracking
        sa.Column(
            "total_gas_used",
            sa.Numeric(78, 0),
            nullable=True,
        ),
        sa.Column(
            "total_cost_usd",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        # Error Information
        sa.Column(
            "error_message",
            sa.Text,
            nullable=True,
        ),
        # Metadata
        sa.Column(
            "metadata",
            JSONB,
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Constraints
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')",
            name="chk_loop_status",
        ),
    )

    # Indexes for leverage_loop_executions
    op.create_index(
        "idx_leverage_loop_user_id",
        "leverage_loop_executions",
        ["user_id"],
    )
    op.create_index(
        "idx_leverage_loop_status",
        "leverage_loop_executions",
        ["status"],
    )
    op.create_index(
        "idx_leverage_loop_created_at",
        "leverage_loop_executions",
        ["created_at"],
    )
    op.create_index(
        "idx_leverage_loop_user_status",
        "leverage_loop_executions",
        ["user_id", "status"],
    )

    # =========================================================================
    # TABLE: lending_alerts
    # =========================================================================

    op.create_table(
        "lending_alerts",
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
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Position Reference (nullable)
        sa.Column(
            "position_id",
            UUID(as_uuid=True),
            sa.ForeignKey("lending_positions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        # Alert Information
        sa.Column(
            "alert_type",
            sa.Enum(
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
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "info",
                "warning",
                "critical",
                name="alert_severity_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text,
            nullable=False,
        ),
        # Alert Details
        sa.Column(
            "health_factor",
            sa.Numeric(10, 2),
            nullable=True,
        ),
        sa.Column(
            "threshold_value",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        sa.Column(
            "current_value",
            sa.Numeric(18, 2),
            nullable=True,
        ),
        # Status
        sa.Column(
            "is_read",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "sent_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Metadata
        sa.Column(
            "metadata",
            JSONB,
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "alert_type IN ('health_factor_low', 'liquidation_risk', 'position_closed', 'loop_completed', 'loop_failed', 'rate_change')",
            name="chk_alert_type",
        ),
        sa.CheckConstraint(
            "severity IN ('info', 'warning', 'critical')",
            name="chk_alert_severity",
        ),
    )

    # Indexes for lending_alerts
    op.create_index(
        "idx_lending_alerts_user_id",
        "lending_alerts",
        ["user_id"],
    )
    op.create_index(
        "idx_lending_alerts_is_read",
        "lending_alerts",
        ["is_read"],
    )
    op.create_index(
        "idx_lending_alerts_severity",
        "lending_alerts",
        ["severity"],
    )
    op.create_index(
        "idx_lending_alerts_created_at",
        "lending_alerts",
        ["created_at"],
    )
    # Partial index for unread alerts
    op.create_index(
        "idx_lending_alerts_user_unread",
        "lending_alerts",
        ["user_id", "is_read"],
        postgresql_where=sa.text("is_read = false"),
    )

    # =========================================================================
    # VIEW: user_lending_summary
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW user_lending_summary AS
        SELECT
            u.id AS user_id,
            u.email,
            COUNT(DISTINCT lp.id) AS total_positions,
            COUNT(DISTINCT CASE WHEN lp.position_type = 'supply' THEN lp.id END) AS supply_positions,
            COUNT(DISTINCT CASE WHEN lp.position_type = 'borrow' THEN lp.id END) AS borrow_positions,
            COUNT(DISTINCT lp.protocol) AS protocols_used,
            SUM(CASE WHEN lp.position_type = 'supply' THEN lp.amount_usd ELSE 0 END) AS total_supplied_usd,
            SUM(CASE WHEN lp.position_type = 'borrow' THEN lp.amount_usd ELSE 0 END) AS total_borrowed_usd,
            MIN(CASE WHEN lp.position_type = 'borrow' THEN lp.health_factor END) AS min_health_factor,
            AVG(CASE WHEN lp.position_type = 'supply' THEN lp.apy END) AS avg_supply_apy,
            AVG(CASE WHEN lp.position_type = 'borrow' THEN lp.apy END) AS avg_borrow_apy,
            COUNT(DISTINCT la.id) FILTER (WHERE la.is_read = false AND la.severity = 'critical') AS unread_critical_alerts,
            MAX(lp.updated_at) AS last_activity_at
        FROM
            chat_users u
            LEFT JOIN lending_positions lp ON u.id = lp.user_id AND lp.status = 'active'
            LEFT JOIN lending_alerts la ON u.id = la.user_id
        WHERE
            u.id IN (SELECT DISTINCT user_id FROM lending_positions)
        GROUP BY
            u.id, u.email;
    """)

    op.execute("""
        COMMENT ON VIEW user_lending_summary IS 'Aggregated view of user lending positions across all protocols';
    """)

    # =========================================================================
    # VIEW: protocol_comparison
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW protocol_comparison AS
        SELECT
            protocol,
            chain,
            asset_symbol,
            position_type,
            COUNT(DISTINCT user_id) AS unique_users,
            COUNT(*) AS total_positions,
            SUM(amount_usd) AS total_tvl_usd,
            AVG(apy) AS avg_apy,
            MIN(apy) AS min_apy,
            MAX(apy) AS max_apy,
            AVG(health_factor) FILTER (WHERE position_type = 'borrow') AS avg_health_factor,
            COUNT(*) FILTER (WHERE status = 'active') AS active_positions,
            COUNT(*) FILTER (WHERE status = 'liquidated') AS liquidated_positions,
            MAX(updated_at) AS last_updated
        FROM
            lending_positions
        GROUP BY
            protocol, chain, asset_symbol, position_type
        ORDER BY
            total_tvl_usd DESC;
    """)

    op.execute("""
        COMMENT ON VIEW protocol_comparison IS 'Real-time comparison view across lending protocols';
    """)


def downgrade() -> None:
    """Drop remaining lending tables, views, and enums."""

    # Drop views
    op.execute("DROP VIEW IF EXISTS protocol_comparison")
    op.execute("DROP VIEW IF EXISTS user_lending_summary")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("lending_alerts")
    op.drop_table("leverage_loop_executions")
    op.drop_table("lending_health_checks")
    op.drop_table("user_lending_preferences")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS alert_severity_enum")
    op.execute("DROP TYPE IF EXISTS alert_type_enum")
    op.execute("DROP TYPE IF EXISTS loop_status_enum")
    op.execute("DROP TYPE IF EXISTS health_factor_level_enum")
    op.execute("DROP TYPE IF EXISTS risk_tolerance_enum")
