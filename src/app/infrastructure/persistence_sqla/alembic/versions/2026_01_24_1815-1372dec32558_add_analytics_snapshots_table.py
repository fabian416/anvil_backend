"""add_analytics_snapshots_table

Revision ID: 1372dec32558
Revises: fb353f64e8fb
Create Date: 2026-01-24 18:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1372dec32558"
down_revision: Union[str, None] = "fb353f64e8fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analytics_snapshots table for storing aggregated user metrics
    op.create_table(
        "analytics_snapshots",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Snapshot identification
        sa.Column(
            "snapshot_date",
            sa.Date(),
            nullable=False,
            comment="Date of the snapshot",
        ),
        sa.Column(
            "snapshot_type",
            sa.String(50),
            nullable=False,
            comment="Type: daily, weekly, monthly",
        ),
        # User counts by portfolio state
        sa.Column(
            "portfolio_empty_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with $0 balance",
        ),
        sa.Column(
            "portfolio_starter_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with $0.01-$99.99 balance",
        ),
        sa.Column(
            "portfolio_active_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with $100-$9,999.99 balance",
        ),
        sa.Column(
            "portfolio_whale_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with $10,000+ balance",
        ),
        # User counts by activity level
        sa.Column(
            "activity_new_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="New users (< 7 days)",
        ),
        sa.Column(
            "activity_very_active_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with 5+ sessions/week",
        ),
        sa.Column(
            "activity_active_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with 2-4 sessions/week",
        ),
        sa.Column(
            "activity_weekly_active_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with 1 session/week",
        ),
        sa.Column(
            "activity_monthly_active_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users with monthly engagement",
        ),
        sa.Column(
            "activity_inactive_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users inactive 30+ days",
        ),
        sa.Column(
            "activity_reactivated_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users who returned after inactivity",
        ),
        # User counts by type
        sa.Column(
            "type_new_user_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="New users with minimal interactions",
        ),
        sa.Column(
            "type_casual_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Casual users with few executions",
        ),
        sa.Column(
            "type_trader_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users focused on swaps/trading",
        ),
        sa.Column(
            "type_yield_farmer_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Users focused on lending/yield",
        ),
        sa.Column(
            "type_power_user_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Highly active diverse users",
        ),
        # Aggregate totals
        sa.Column(
            "total_users",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total users in snapshot",
        ),
        sa.Column(
            "total_executions",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total workflow executions",
        ),
        sa.Column(
            "total_balance_usd",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
            server_default="0",
            comment="Sum of all user balances",
        ),
        # Execution breakdown
        sa.Column(
            "exec_swap_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total swap executions",
        ),
        sa.Column(
            "exec_buy_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total buy executions",
        ),
        sa.Column(
            "exec_lending_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total lending executions",
        ),
        sa.Column(
            "exec_transfer_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total transfer executions",
        ),
        sa.Column(
            "exec_cashout_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Total cashout executions",
        ),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Additional metrics (JSONB for flexibility)
        sa.Column(
            "additional_metrics",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="Additional metrics as JSON",
        ),
    )

    # Create indexes
    op.create_index(
        "idx_analytics_snapshot_date",
        "analytics_snapshots",
        ["snapshot_date"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_analytics_snapshot_type",
        "analytics_snapshots",
        ["snapshot_type"],
        postgresql_using="btree",
    )
    # Unique constraint on date + type
    op.create_unique_constraint(
        "uq_analytics_snapshot_date_type",
        "analytics_snapshots",
        ["snapshot_date", "snapshot_type"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_analytics_snapshot_date_type",
        "analytics_snapshots",
        type_="unique",
    )
    op.drop_index("idx_analytics_snapshot_type", table_name="analytics_snapshots")
    op.drop_index("idx_analytics_snapshot_date", table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")
