"""add swap_positions table for cached Hyperliquid positions

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # swap_positions: cached Hyperliquid spot balances + perps positions
    # Background Celery task syncs every 60s instead of live API calls per request.
    # Supports 1000+ users within Hyperliquid's 1200 req/min rate limit.
    op.create_table(
        "swap_positions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("wallet_address", sa.String(42), nullable=False, index=True),
        # "spot" or "perps"
        sa.Column("source", sa.String(10), nullable=False),
        # Token symbol: "USDC", "PURR", "ETH", etc.
        sa.Column("token", sa.String(20), nullable=False),
        # Token balance (spot) or position size (perps)
        sa.Column("balance", sa.Numeric(30, 18), nullable=False, server_default="0"),
        # USD value of the position
        sa.Column("usd_value", sa.Numeric(18, 2), nullable=False, server_default="0"),
        # "hold" for spot, "long"/"short" for perps
        sa.Column("side", sa.String(10), nullable=False, server_default="hold"),
        # Perps-only fields
        sa.Column("entry_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("mark_price", sa.Numeric(18, 6), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(18, 6), nullable=True),
        sa.Column("leverage", sa.Numeric(6, 2), nullable=True),
        sa.Column("liquidation_price", sa.Numeric(18, 6), nullable=True),
        # Timestamps
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    # Composite unique: one row per (wallet, source, token)
    op.create_unique_constraint(
        "uq_swap_positions_wallet_source_token",
        "swap_positions",
        ["wallet_address", "source", "token"],
    )
    # Index for fast lookups by wallet
    op.create_index(
        "idx_swap_positions_wallet_source",
        "swap_positions",
        ["wallet_address", "source"],
    )
    # Index for Celery cleanup of stale rows
    op.create_index(
        "idx_swap_positions_synced_at",
        "swap_positions",
        ["synced_at"],
    )


def downgrade() -> None:
    op.drop_table("swap_positions")
