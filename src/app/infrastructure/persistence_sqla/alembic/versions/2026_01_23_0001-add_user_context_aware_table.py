"""Add user_context_aware table for context-aware agents.

Revision ID: 3f7f6f89818e
Revises: b85c12f320c7
Create Date: 2026-01-23 00:01:00.000000

This table stores pre-computed user context data for context-aware
agent responses. Data is updated periodically by a Celery task.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "3f7f6f89818e"
down_revision = "1bc72b16a56e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_context_aware table
    op.create_table(
        "user_context_aware",
        # Primary key
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column("chat_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("legacy_user_id", sa.Integer(), nullable=True),
        # Portfolio State
        sa.Column(
            "portfolio_state", sa.String(20), nullable=False, server_default="empty"
        ),
        sa.Column(
            "total_balance_usd",
            sa.Numeric(18, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("primary_chain", sa.String(50), nullable=True),
        # Activity Level
        sa.Column(
            "activity_level", sa.String(20), nullable=False, server_default="new"
        ),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "first_active_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "chat_sessions_30d", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "messages_sent_30d", sa.Integer(), nullable=False, server_default="0"
        ),
        # User Type
        sa.Column(
            "user_type", sa.String(30), nullable=False, server_default="new_user"
        ),
        # Execution History
        sa.Column("swap_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("buy_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cashout_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lending_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "money_market_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("transfer_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_executions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "failed_executions", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "execution_success_rate",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0.00",
        ),
        # Chat Interactions
        sa.Column(
            "total_conversations", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "shortcuts_used_count", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "multi_step_completed_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "avg_messages_per_session",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "detected_language", sa.String(5), nullable=False, server_default="en"
        ),
        sa.Column(
            "language_history",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "most_used_agents",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "agent_usage_counts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        # Wallet Data
        sa.Column("wallet_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "has_connected_wallet", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("primary_wallet_address", sa.String(255), nullable=True),
        sa.Column("wallet_provider", sa.String(50), nullable=True),
        # Processing Metadata
        sa.Column(
            "context_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "next_update_eligible_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("update_count", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Primary key constraint
        sa.PrimaryKeyConstraint("id"),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["chat_user_id"], ["chat_users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["legacy_user_id"], ["users.id"], ondelete="SET NULL"),
        # Check constraints
        sa.CheckConstraint(
            "portfolio_state IN ('empty', 'starter', 'active', 'whale')",
            name="valid_portfolio_state",
        ),
        sa.CheckConstraint(
            "activity_level IN ('very_active', 'active', 'weekly_active', 'monthly_active', 'inactive', 'reactivated', 'new')",
            name="valid_activity_level",
        ),
        sa.CheckConstraint(
            "user_type IN ('new_user', 'casual', 'trader', 'yield_farmer', 'power_user')",
            name="valid_user_type",
        ),
    )

    # Create indexes
    # Unique index for one context per chat user
    op.create_index(
        "idx_user_context_unique_chat_user",
        "user_context_aware",
        ["chat_user_id"],
        unique=True,
    )

    # Index for finding users eligible for update
    # Note: Cannot use partial index with CURRENT_TIMESTAMP (not immutable)
    # Query will use this index with WHERE clause at query time
    op.create_index(
        "idx_user_context_next_update",
        "user_context_aware",
        ["next_update_eligible_at"],
    )

    # Index for filtering by portfolio state
    op.create_index(
        "idx_user_context_portfolio_state",
        "user_context_aware",
        ["portfolio_state"],
    )

    # Index for filtering by activity level
    op.create_index(
        "idx_user_context_activity_level",
        "user_context_aware",
        ["activity_level"],
    )

    # Index for filtering by user type
    op.create_index(
        "idx_user_context_user_type",
        "user_context_aware",
        ["user_type"],
    )

    # Index for legacy user lookup
    op.create_index(
        "idx_user_context_legacy_user",
        "user_context_aware",
        ["legacy_user_id"],
        postgresql_where=sa.text("legacy_user_id IS NOT NULL"),
    )

    # Index for last updated (for analytics)
    op.create_index(
        "idx_user_context_updated_at",
        "user_context_aware",
        ["context_updated_at"],
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_user_context_updated_at", table_name="user_context_aware")
    op.drop_index("idx_user_context_legacy_user", table_name="user_context_aware")
    op.drop_index("idx_user_context_user_type", table_name="user_context_aware")
    op.drop_index("idx_user_context_activity_level", table_name="user_context_aware")
    op.drop_index("idx_user_context_portfolio_state", table_name="user_context_aware")
    op.drop_index("idx_user_context_next_update", table_name="user_context_aware")
    op.drop_index("idx_user_context_unique_chat_user", table_name="user_context_aware")

    # Drop table
    op.drop_table("user_context_aware")
