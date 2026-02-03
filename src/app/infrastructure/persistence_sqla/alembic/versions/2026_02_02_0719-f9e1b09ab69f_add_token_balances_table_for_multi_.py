"""add token_balances table for multi-token tracking

Revision ID: f9e1b09ab69f
Revises: a5840134eea0
Create Date: 2026-02-02 07:19:28.123456

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f9e1b09ab69f"
down_revision: Union[str, None] = "a5840134eea0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create token_balances table for tracking all tokens per wallet/chain
    op.create_table(
        "token_balances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "wallet_id",
            sa.Integer(),
            sa.ForeignKey("wallets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chain", sa.String(50), nullable=False, index=True),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        # Token info
        sa.Column("token_symbol", sa.String(50), nullable=False, index=True),
        sa.Column("token_name", sa.String(255), nullable=True),
        sa.Column(
            "token_address", sa.String(255), nullable=True
        ),  # NULL for native tokens
        sa.Column("token_decimals", sa.Integer(), default=18),
        # Balance
        sa.Column("balance_raw", sa.String(78), nullable=True),  # Raw balance as string
        sa.Column("balance_human", sa.Numeric(38, 18), default=0),  # Human-readable
        sa.Column("balance_usd", sa.Numeric(20, 2), default=0),  # USD value
        sa.Column("price_usd", sa.Numeric(20, 8), nullable=True),  # Token price
        # Flags
        sa.Column(
            "is_native", sa.Boolean(), default=False
        ),  # True for ETH, MATIC, etc.
        sa.Column(
            "can_pay_gas", sa.Boolean(), default=False
        ),  # True only for native tokens
        sa.Column(
            "is_stablecoin", sa.Boolean(), default=False
        ),  # True for USDC, USDT, DAI
        # Metadata
        sa.Column("portfolio_pct", sa.Numeric(5, 2), nullable=True),  # Portfolio %
        sa.Column("last_balance_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        # Unique constraint: one entry per wallet/chain/token
        sa.UniqueConstraint(
            "wallet_id", "chain", "token_symbol", name="unique_wallet_chain_token"
        ),
    )

    # Add index for common queries
    op.create_index(
        "idx_token_balances_can_pay_gas",
        "token_balances",
        ["wallet_id", "can_pay_gas"],
        postgresql_where=sa.text("can_pay_gas = true"),
    )

    op.execute(
        "COMMENT ON TABLE token_balances IS "
        "'Multi-token balance tracking per wallet/chain. Includes native tokens, stablecoins, and wrapped tokens.'"
    )


def downgrade() -> None:
    op.drop_index("idx_token_balances_can_pay_gas", table_name="token_balances")
    op.drop_table("token_balances")
