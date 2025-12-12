"""Allow transactions to appear in both sender and receiver history

This migration changes the unique constraint on transactions table:
- Remove unique constraint on tx_hash (allows same tx to exist for multiple users)
- Add unique constraint on (user_id, tx_hash) to prevent duplicate records per user

This enables the same on-chain transaction to appear in both the sender's
and receiver's transaction history when both parties are registered users.

Per TASKS.md: Each row represents the perspective of ONE user. A single
(user_id, tx_hash) must be unique to avoid duplicates from retries.

Revision ID: dual_tx_20251211
Revises: txan_20251211
Create Date: 2025-12-11 00:02:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dual_tx_20251211"
down_revision: Union[str, None] = "txan_20251211"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change unique constraint from tx_hash to (user_id, tx_hash)."""
    conn = op.get_bind()

    # 1. Drop the unique CONSTRAINT on tx_hash if it exists
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'transactions' 
        AND constraint_type = 'UNIQUE'
        AND constraint_name = 'transactions_tx_hash_key'
    """))
    if result.fetchone():
        op.drop_constraint(
            "transactions_tx_hash_key",
            "transactions",
            type_="unique",
        )

    # 2. Drop the unique INDEX on tx_hash if it exists and recreate as non-unique
    # This is critical - SQLAlchemy may create an index separate from the constraint
    result = conn.execute(sa.text("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'transactions'
        AND indexname = 'ix_transactions_tx_hash'
    """))
    row = result.fetchone()
    if row:
        # Check if it's a UNIQUE index
        indexdef = row[1] if row else ""
        if "UNIQUE" in indexdef.upper():
            # Drop the unique index
            op.drop_index("ix_transactions_tx_hash", table_name="transactions")
            # Recreate as a normal (non-unique) index for query performance
            op.create_index(
                "ix_transactions_tx_hash",
                "transactions",
                ["tx_hash"],
                unique=False,
            )

    # 3. Create a new unique constraint on (user_id, tx_hash)
    # This allows the same tx_hash to exist for different users
    # but prevents duplicate records for the same user
    # Check if it already exists first
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_name = 'transactions' 
        AND constraint_name = 'uq_transactions_user_tx_hash'
    """))
    if not result.fetchone():
        op.create_unique_constraint(
            "uq_transactions_user_tx_hash",
            "transactions",
            ["user_id", "tx_hash"],
        )


def downgrade() -> None:
    """Restore original unique constraint on tx_hash only."""
    # Drop the composite unique constraint
    op.drop_constraint(
        "uq_transactions_user_tx_hash",
        "transactions",
        type_="unique",
    )

    # Restore the original unique constraint on tx_hash
    op.create_unique_constraint(
        "transactions_tx_hash_key",
        "transactions",
        ["tx_hash"],
    )
