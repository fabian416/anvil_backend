"""add hl_spot_tokens table for Hyperliquid spot token catalog + sentiment

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-12 01:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # hl_spot_tokens: catalog of ALL Hyperliquid spot tokens + sentiment enrichment.
    #
    # Two Celery processes:
    #   1. Seed task (every 24h): fetches spotMeta, inserts new tokens as "pending"
    #   2. Enrich task (every 1 min): picks 1 pending/stale token, runs sentiment
    #      analysis via AssetSentimentService, updates sentiment fields.
    #      Rotation: picks token with oldest updated_at (>1h) to avoid API exhaustion.
    op.create_table(
        "hl_spot_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        # Token identity from Hyperliquid spotMeta
        sa.Column("name", sa.String(30), nullable=False, unique=True),
        sa.Column("token_id", sa.String(66), nullable=False),
        sa.Column("token_index", sa.Integer(), nullable=False),
        sa.Column("sz_decimals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wei_decimals", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("is_canonical", sa.Boolean(), nullable=False, server_default="false"),
        # Status: "pending" (just seeded), "enriched" (sentiment done), "error"
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        # Sentiment enrichment fields (populated by enrich task)
        sa.Column("sentiment_score", sa.Numeric(5, 1), nullable=True),
        sa.Column("sentiment_classification", sa.String(20), nullable=True),
        sa.Column("sentiment_interpretation", sa.String(50), nullable=True),
        sa.Column("sentiment_confidence", sa.Numeric(4, 2), nullable=True),
        sa.Column("sentiment_source", sa.String(30), nullable=True),
        sa.Column("sentiment_time_horizon", sa.String(10), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "sentiment_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    # Index for the enrich rotation query:
    # SELECT ... WHERE status IN ('pending','enriched')
    # ORDER BY sentiment_updated_at ASC NULLS FIRST LIMIT 1
    op.create_index(
        "idx_hl_spot_tokens_enrich_rotation",
        "hl_spot_tokens",
        ["status", "sentiment_updated_at"],
    )
    op.create_index(
        "idx_hl_spot_tokens_name",
        "hl_spot_tokens",
        ["name"],
    )


def downgrade() -> None:
    op.drop_table("hl_spot_tokens")
