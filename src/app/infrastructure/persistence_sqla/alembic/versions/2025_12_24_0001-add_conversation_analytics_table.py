"""Add conversation_analytics table for chat/admin analytics.

Revision ID: conv_analytics_20251224
Revises: pol_20251222
Create Date: 2025-12-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "conv_analytics_20251224"
down_revision: Union[str, None] = "pol_20251222"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation_analytics",
        sa.Column("analytics_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        # Message metrics
        sa.Column(
            "message_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "user_message_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "agent_message_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Agent usage (JSONB)
        sa.Column(
            "agent_usage",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # Response time metrics (milliseconds)
        sa.Column("avg_response_time_ms", sa.Float(), nullable=True),
        sa.Column("median_response_time_ms", sa.Float(), nullable=True),
        sa.Column("p95_response_time_ms", sa.Float(), nullable=True),
        sa.Column("min_response_time_ms", sa.Float(), nullable=True),
        sa.Column("max_response_time_ms", sa.Float(), nullable=True),
        # Cost metrics (USD)
        sa.Column(
            "total_cost_usd",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "avg_cost_per_message",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "cost_by_agent",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        # Quality metrics (0.0 to 1.0)
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("user_satisfaction_score", sa.Float(), nullable=True),
        # Token usage
        sa.Column(
            "total_tokens_used",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "input_tokens",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "output_tokens",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        # Timestamps
        sa.Column("first_message_at", sa.DateTime(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("analytics_id", name=op.f("pk_conversation_analytics")),
        sa.UniqueConstraint(
            "conversation_id",
            name=op.f("uq_conversation_analytics_conversation_id"),
        ),
    )

    # Base indexes
    op.create_index(
        op.f("ix_conversation_analytics_conversation_id"),
        "conversation_analytics",
        ["conversation_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_conversation_analytics_user_id"),
        "conversation_analytics",
        ["user_id"],
        unique=False,
    )

    # Analytics-optimized indexes (match `ConversationAnalyticsModel.__table_args__`)
    op.create_index(
        "idx_analytics_user_created",
        "conversation_analytics",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_analytics_user_cost",
        "conversation_analytics",
        ["user_id", "total_cost_usd"],
        unique=False,
    )
    op.create_index(
        "idx_analytics_user_messages",
        "conversation_analytics",
        ["user_id", "message_count"],
        unique=False,
    )
    op.create_index(
        "idx_analytics_quality_score",
        "conversation_analytics",
        ["quality_score"],
        unique=False,
    )
    op.create_index(
        "idx_analytics_created_at",
        "conversation_analytics",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_analytics_created_at", table_name="conversation_analytics")
    op.drop_index("idx_analytics_quality_score", table_name="conversation_analytics")
    op.drop_index("idx_analytics_user_messages", table_name="conversation_analytics")
    op.drop_index("idx_analytics_user_cost", table_name="conversation_analytics")
    op.drop_index("idx_analytics_user_created", table_name="conversation_analytics")
    op.drop_index(op.f("ix_conversation_analytics_user_id"), table_name="conversation_analytics")
    op.drop_index(
        op.f("ix_conversation_analytics_conversation_id"),
        table_name="conversation_analytics",
    )
    op.drop_table("conversation_analytics")


