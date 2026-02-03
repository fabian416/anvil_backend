"""Add last_balance_checked_at column to wallets table

Revision ID: b2c3d4e5f6a7
Revises:
Create Date: 2026-01-28 14:00:00.000000

This migration adds a column for tracking when wallet balances
were last synced from Privy API. Used by the Celery background
task to avoid re-checking wallets too frequently.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "227b2c9cb872"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_balance_checked_at column to wallets table
    op.add_column(
        "wallets",
        sa.Column(
            "last_balance_checked_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of last Privy balance sync",
        ),
    )

    # Create index for efficient querying by last check time
    op.create_index(
        "ix_wallets_last_balance_checked_at",
        "wallets",
        ["last_balance_checked_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop index first
    op.drop_index("ix_wallets_last_balance_checked_at", table_name="wallets")

    # Drop column
    op.drop_column("wallets", "last_balance_checked_at")
