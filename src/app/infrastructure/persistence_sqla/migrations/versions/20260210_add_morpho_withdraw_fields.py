"""Add wallet_address and market_id to lending_transactions for Morpho withdraw.

Revision ID: 20260210_morpho_withdraw
Revises: 20260112_add_moonpay_customer_tokens
Create Date: 2026-02-10

This migration adds fields required for Morpho Blue withdraw functionality:
- wallet_address: User's wallet address for position lookup
- market_id: Morpho Blue market ID (bytes32 hex string)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260210_morpho_withdraw"
down_revision = "20260112_add_moonpay_customer_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add wallet_address and market_id columns to lending_transactions."""
    # Add wallet_address column for position lookup
    op.add_column(
        "lending_transactions",
        sa.Column("wallet_address", sa.String(42), nullable=True),
    )
    
    # Add market_id column for Morpho Blue market reference
    op.add_column(
        "lending_transactions",
        sa.Column("market_id", sa.String(66), nullable=True),
    )
    
    # Create index on wallet_address for faster lookups
    op.create_index(
        "idx_lending_transactions_wallet",
        "lending_transactions",
        ["wallet_address"],
    )
    
    # Create index on market_id for Morpho Blue queries
    op.create_index(
        "idx_lending_transactions_market_id",
        "lending_transactions",
        ["market_id"],
    )


def downgrade() -> None:
    """Remove wallet_address and market_id columns from lending_transactions."""
    op.drop_index("idx_lending_transactions_market_id", table_name="lending_transactions")
    op.drop_index("idx_lending_transactions_wallet", table_name="lending_transactions")
    op.drop_column("lending_transactions", "market_id")
    op.drop_column("lending_transactions", "wallet_address")
