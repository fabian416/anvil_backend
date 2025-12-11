"""Add transaction analytics fields

This migration adds fields required for the sending flow and analytics
per TASKS.md requirements:

Core fields:
- to_address: Recipient address (critical for send transactions)

Analytics fields (mid-term):
- gas_used: Gas units consumed
- gas_price: Gas price in wei
- metadata: JSON field for additional context

Also adds index on block_number for efficient confirmation queries.

Revision ID: g7h8i9j0k1l2
Revises: 2025_12_10_0002-add_analytics_indexes
Create Date: 2025-12-11 00:01:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "txan_20251211"
down_revision: Union[str, None] = "aidx_20251210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add new fields to transactions table for analytics."""
    # Add to_address column (recipient address for sends)
    op.add_column(
        "transactions",
        sa.Column(
            "to_address",
            sa.String(length=42),
            nullable=True,
            comment="Recipient wallet address (0x...)",
        ),
    )

    # Add gas_used column
    op.add_column(
        "transactions",
        sa.Column(
            "gas_used",
            sa.BigInteger(),
            nullable=True,
            comment="Gas units consumed by the transaction",
        ),
    )

    # Add gas_price column
    op.add_column(
        "transactions",
        sa.Column(
            "gas_price",
            sa.BigInteger(),
            nullable=True,
            comment="Gas price in wei",
        ),
    )

    # Add tx_metadata column (JSON for additional context)
    # Named tx_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    op.add_column(
        "transactions",
        sa.Column(
            "tx_metadata",
            sa.JSON(),
            nullable=True,
            comment="Additional transaction context (contract, protocol, etc.)",
        ),
    )

    # Create indexes for new columns
    op.create_index(
        op.f("ix_transactions_to_address"),
        "transactions",
        ["to_address"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transactions_block_number"),
        "transactions",
        ["block_number"],
        unique=False,
    )


def downgrade() -> None:
    """Remove analytics fields from transactions table."""
    # Drop indexes
    op.drop_index(op.f("ix_transactions_block_number"), table_name="transactions")
    op.drop_index(op.f("ix_transactions_to_address"), table_name="transactions")

    # Drop columns
    op.drop_column("transactions", "tx_metadata")
    op.drop_column("transactions", "gas_price")
    op.drop_column("transactions", "gas_used")
    op.drop_column("transactions", "to_address")
