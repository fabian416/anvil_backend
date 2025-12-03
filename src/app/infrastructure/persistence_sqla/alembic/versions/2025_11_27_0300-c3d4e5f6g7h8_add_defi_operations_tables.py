"""Add DeFi operations tables

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2025-11-27 03:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create Enums (checkfirst=True to avoid error if already exists)
    sa.Enum("long", "short", name="side").create(op.get_bind(), checkfirst=True)
    sa.Enum("open", "closed", "liquidated", name="positionstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("active", "withdrawn", "emergency_exit", name="earnstatus").create(op.get_bind(), checkfirst=True)
    sa.Enum("daily", "weekly", "biweekly", "monthly", name="frequency").create(op.get_bind(), checkfirst=True)
    sa.Enum("active", "paused", "completed", "failed", name="schedulestatus").create(op.get_bind(), checkfirst=True)

    # --- Hyperliquid Positions ---
    op.create_table(
        "hyperliquid_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("side", sa.Enum("long", "short", name="side"), nullable=False),
        sa.Column("leverage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("size", sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column("entry_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("mark_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("liquidation_price", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("realized_pnl", sa.Numeric(precision=20, scale=8), server_default='0', nullable=True),
        sa.Column("margin", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("funding_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("last_funding_payment", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("status", sa.Enum("open", "closed", "liquidated", name="positionstatus"), server_default='open', nullable=True),
        sa.Column("hyperliquid_order_id", sa.String(length=100), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_hyperliquid_positions_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_hyperliquid_positions_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_hyperliquid_positions")),
    )
    op.create_index(op.f("ix_hyperliquid_positions_user_id"), "hyperliquid_positions", ["user_id"], unique=False)
    op.create_index(op.f("ix_hyperliquid_positions_symbol"), "hyperliquid_positions", ["symbol"], unique=False)
    op.create_index(op.f("ix_hyperliquid_positions_status"), "hyperliquid_positions", ["status"], unique=False)
    op.create_index(op.f("ix_hyperliquid_positions_opened_at"), "hyperliquid_positions", ["opened_at"], unique=False)

    # --- Earn Positions ---
    op.create_table(
        "earn_positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("chain", sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype"), nullable=False),
        sa.Column("protocol", sa.String(length=50), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("amount_deposited", sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column("current_value", sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column("apy", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("current_apy", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("rewards_earned", sa.Numeric(precision=30, scale=18), server_default='0', nullable=True),
        sa.Column("rewards_earned_usd", sa.Numeric(precision=20, scale=2), server_default='0', nullable=True),
        sa.Column("status", sa.Enum("active", "withdrawn", "emergency_exit", name="earnstatus"), server_default='active', nullable=True),
        sa.Column("transaction_hash", sa.String(length=66), nullable=True),
        sa.Column("deposit_tx_hash", sa.String(length=66), nullable=True),
        sa.Column("withdraw_tx_hash", sa.String(length=66), nullable=True),
        sa.Column("deposited_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_earn_positions_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_earn_positions_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_earn_positions")),
    )
    op.create_index(op.f("ix_earn_positions_user_id"), "earn_positions", ["user_id"], unique=False)
    op.create_index(op.f("ix_earn_positions_chain"), "earn_positions", ["chain"], unique=False)
    op.create_index(op.f("ix_earn_positions_protocol"), "earn_positions", ["protocol"], unique=False)
    op.create_index(op.f("ix_earn_positions_status"), "earn_positions", ["status"], unique=False)
    op.create_index(op.f("ix_earn_positions_deposited_at"), "earn_positions", ["deposited_at"], unique=False)

    # --- Save Schedules ---
    op.create_table(
        "save_schedules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("chain", sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype"), nullable=False),
        sa.Column("asset", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=30, scale=18), nullable=False),
        sa.Column("frequency", sa.Enum("daily", "weekly", "biweekly", "monthly", name="frequency"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("destination_protocol", sa.String(length=50), nullable=True),
        sa.Column("status", sa.Enum("active", "paused", "completed", "failed", name="schedulestatus"), server_default='active', nullable=True),
        sa.Column("next_execution_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_execution_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_saved", sa.Numeric(precision=30, scale=18), server_default='0', nullable=True),
        sa.Column("execution_count", sa.Integer(), server_default='0', nullable=True),
        sa.Column("max_executions", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_save_schedules_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_save_schedules_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_save_schedules")),
    )
    op.create_index(op.f("ix_save_schedules_user_id"), "save_schedules", ["user_id"], unique=False)
    op.create_index(op.f("ix_save_schedules_status"), "save_schedules", ["status"], unique=False)
    op.create_index(op.f("ix_save_schedules_next_execution_at"), "save_schedules", ["next_execution_at"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_save_schedules_next_execution_at"), table_name="save_schedules")
    op.drop_index(op.f("ix_save_schedules_status"), table_name="save_schedules")
    op.drop_index(op.f("ix_save_schedules_user_id"), table_name="save_schedules")
    op.drop_table("save_schedules")

    op.drop_index(op.f("ix_earn_positions_deposited_at"), table_name="earn_positions")
    op.drop_index(op.f("ix_earn_positions_status"), table_name="earn_positions")
    op.drop_index(op.f("ix_earn_positions_protocol"), table_name="earn_positions")
    op.drop_index(op.f("ix_earn_positions_chain"), table_name="earn_positions")
    op.drop_index(op.f("ix_earn_positions_user_id"), table_name="earn_positions")
    op.drop_table("earn_positions")

    op.drop_index(op.f("ix_hyperliquid_positions_opened_at"), table_name="hyperliquid_positions")
    op.drop_index(op.f("ix_hyperliquid_positions_status"), table_name="hyperliquid_positions")
    op.drop_index(op.f("ix_hyperliquid_positions_symbol"), table_name="hyperliquid_positions")
    op.drop_index(op.f("ix_hyperliquid_positions_user_id"), table_name="hyperliquid_positions")
    op.drop_table("hyperliquid_positions")

    sa.Enum(name="schedulestatus").drop(op.get_bind())
    sa.Enum(name="frequency").drop(op.get_bind())
    sa.Enum(name="earnstatus").drop(op.get_bind())
    sa.Enum(name="positionstatus").drop(op.get_bind())
    sa.Enum(name="side").drop(op.get_bind())
