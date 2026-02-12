"""add swap_intents and user_sync_schedule

Revision ID: a1b2c3d4e5f6
Revises: 047cc9a1c65e
Create Date: 2026-02-11 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "047cc9a1c65e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # swap_intents: track swap execute_data opened from chat (15-min watcher)
    op.create_table(
        "swap_intents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("wallet_id", sa.Integer(), sa.ForeignKey("wallets.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("wallet_address", sa.String(42), nullable=False, index=True),
        sa.Column("conversation_id", sa.UUID(), nullable=True, index=True),
        sa.Column("from_token", sa.String(20), nullable=False),
        sa.Column("to_token", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(30, 18), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="hyperliquid_swap"),
        sa.Column("tx_hash", sa.String(66), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(
        "idx_swap_intents_pending_15min",
        "swap_intents",
        ["created_at", "status"],
        postgresql_where=sa.text("status = 'pending' AND tx_hash IS NULL"),
    )

    # user_sync_schedule: incremental sync backoff for users active in last 24h
    op.create_table(
        "user_sync_schedule",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("next_sync_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("interval_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index(
        "idx_user_sync_schedule_due",
        "user_sync_schedule",
        ["next_sync_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_user_sync_schedule_due", table_name="user_sync_schedule")
    op.drop_table("user_sync_schedule")
    op.drop_index("idx_swap_intents_pending_15min", table_name="swap_intents")
    op.drop_table("swap_intents")
