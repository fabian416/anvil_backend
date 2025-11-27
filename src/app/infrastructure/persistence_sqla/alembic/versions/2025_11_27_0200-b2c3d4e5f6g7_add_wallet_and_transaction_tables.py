"""Add wallet and transaction tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-27 02:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create Enums if they don't exist (Postgres specific)
    # We use existing Enums or create new ones.
    # WalletProvider and ChainType are used as Enums in mapping but mapped to Enum column in DB.
    sa.Enum("privy", "external", name="walletprovider").create(op.get_bind())
    sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype").create(op.get_bind())
    sa.Enum("inactive", "active", "deleted", name="walletstatus").create(op.get_bind())

    # --- WALLETS ---
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("privy_wallet_id", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=42), nullable=False),
        sa.Column("provider", sa.Enum("privy", "external", name="walletprovider"), nullable=False),
        sa.Column("default_chain", sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype"), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False, server_default='1'),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_wallets_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wallets")),
        sa.UniqueConstraint("privy_wallet_id", name=op.f("uq_wallets_privy_wallet_id")),
        sa.UniqueConstraint("address", name=op.f("uq_wallets_address")),
    )
    op.create_index(op.f("ix_wallets_user_id"), "wallets", ["user_id"], unique=False)
    op.create_index(op.f("ix_wallets_privy_wallet_id"), "wallets", ["privy_wallet_id"], unique=True)
    op.create_index(op.f("ix_wallets_address"), "wallets", ["address"], unique=True)

    # --- CHAIN ADDRESSES ---
    op.create_table(
        "chain_addresses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("chain", sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype"), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default='true'),
        sa.Column("balance_usd", sa.Numeric(precision=20, scale=2), nullable=True, server_default='0.00'),
        sa.Column("last_balance_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_chain_addresses_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chain_addresses")),
        sa.UniqueConstraint("wallet_id", "chain", name="unique_wallet_chain"),
    )
    op.create_index(op.f("ix_chain_addresses_wallet_id"), "chain_addresses", ["wallet_id"], unique=False)
    op.create_index(op.f("ix_chain_addresses_chain"), "chain_addresses", ["chain"], unique=False)

    # --- TRANSACTIONS ---
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wallet_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("chain", sa.Enum("arbitrum", "base", "hyperliquid", name="chaintype"), nullable=False),
        sa.Column("asset_in", sa.String(length=20), nullable=True),
        sa.Column("amount_in", sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column("asset_out", sa.String(length=20), nullable=True),
        sa.Column("amount_out", sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column("fee", sa.Numeric(precision=30, scale=18), nullable=True),
        sa.Column("fee_usd", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("tx_hash", sa.String(length=66), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False, server_default='0'),
        sa.Column("dex_aggregator", sa.String(length=50), nullable=True),
        sa.Column("dex_route", sa.JSON(), nullable=True),
        sa.Column("slippage", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_transactions_user_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"], name=op.f("fk_transactions_wallet_id_wallets"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.UniqueConstraint("tx_hash", name=op.f("uq_transactions_tx_hash")),
    )
    op.create_index(op.f("ix_transactions_user_id"), "transactions", ["user_id"], unique=False)
    op.create_index(op.f("ix_transactions_wallet_id"), "transactions", ["wallet_id"], unique=False)
    op.create_index(op.f("ix_transactions_tx_hash"), "transactions", ["tx_hash"], unique=True)
    op.create_index(op.f("ix_transactions_type"), "transactions", ["type"], unique=False)
    op.create_index(op.f("ix_transactions_status"), "transactions", ["status"], unique=False)
    op.create_index(op.f("ix_transactions_created_at"), "transactions", ["created_at"], unique=False)

def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_created_at"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_status"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_type"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_tx_hash"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_wallet_id"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_user_id"), table_name="transactions")
    op.drop_table("transactions")

    op.drop_index(op.f("ix_chain_addresses_chain"), table_name="chain_addresses")
    op.drop_index(op.f("ix_chain_addresses_wallet_id"), table_name="chain_addresses")
    op.drop_table("chain_addresses")

    op.drop_index(op.f("ix_wallets_address"), table_name="wallets")
    op.drop_index(op.f("ix_wallets_privy_wallet_id"), table_name="wallets")
    op.drop_index(op.f("ix_wallets_user_id"), table_name="wallets")
    op.drop_table("wallets")

    sa.Enum(name="walletstatus").drop(op.get_bind())
    sa.Enum(name="chaintype").drop(op.get_bind())
    sa.Enum(name="walletprovider").drop(op.get_bind())
