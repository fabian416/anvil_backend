"""add_wallet_balance_columns_to_user_context

Add columns for wallet balance aggregation to user_context_aware table.
These columns enable accurate portfolio_state classification based on
actual wallet balances instead of defaults.

Note: wallet_count and primary_wallet_address already exist in the
original user_context_aware migration, so we only add the new columns.

Revision ID: fb353f64e8fb
Revises: 11f37a0774ff
Create Date: 2026-01-24 14:32:28.340510

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "fb353f64e8fb"
down_revision: Union[str, None] = "11f37a0774ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add NEW wallet balance columns to user_context_aware table
    # Note: wallet_count and primary_wallet_address already exist
    
    op.add_column(
        "user_context_aware",
        sa.Column(
            "wallet_total_usd",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
            server_default="0",
            comment="Total USD value across all user wallets",
        ),
    )
    
    op.add_column(
        "user_context_aware",
        sa.Column(
            "wallet_chain_breakdown",
            postgresql.JSONB,
            nullable=False,
            server_default="{}",
            comment="Balance breakdown by chain (JSON: {chain: usd_value})",
        ),
    )
    
    op.add_column(
        "user_context_aware",
        sa.Column(
            "wallet_last_sync_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last time wallet balances were synced",
        ),
    )
    
    # Create index for querying by wallet balance (for analytics)
    op.create_index(
        "idx_user_context_wallet_total",
        "user_context_aware",
        ["wallet_total_usd"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    # Drop index
    op.drop_index("idx_user_context_wallet_total", table_name="user_context_aware")
    
    # Drop columns (only the ones added by this migration)
    op.drop_column("user_context_aware", "wallet_last_sync_at")
    op.drop_column("user_context_aware", "wallet_chain_breakdown")
    op.drop_column("user_context_aware", "wallet_total_usd")
