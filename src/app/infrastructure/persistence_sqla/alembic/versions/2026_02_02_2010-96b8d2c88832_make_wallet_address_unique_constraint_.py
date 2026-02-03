"""make wallet address unique constraint case insensitive

Revision ID: 96b8d2c88832
Revises: f9e1b09ab69f
Create Date: 2026-02-02 20:10:11.301936

This migration:
1. First normalizes all existing wallet addresses to lowercase
2. Drops the old case-sensitive unique constraint
3. Creates a new case-insensitive unique index using LOWER()

This prevents duplicate wallets from being created due to different casing
(e.g., 0xABC... and 0xabc... are the same wallet on Ethereum).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "96b8d2c88832"
down_revision: Union[str, None] = "f9e1b09ab69f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Normalize all existing addresses to lowercase
    op.execute("UPDATE wallets SET address = LOWER(address)")

    # Step 2: Drop the old case-sensitive unique constraint
    op.drop_constraint("unique_user_wallet_address", "wallets", type_="unique")

    # Step 3: Create a new case-insensitive unique index
    # Using a functional index with LOWER() ensures case-insensitive uniqueness
    op.create_index(
        "unique_user_wallet_address_ci",
        "wallets",
        [sa.text("user_id"), sa.text("LOWER(address)")],
        unique=True,
    )


def downgrade() -> None:
    # Drop the case-insensitive index
    op.drop_index("unique_user_wallet_address_ci", table_name="wallets")

    # Recreate the original case-sensitive constraint
    op.create_unique_constraint(
        "unique_user_wallet_address",
        "wallets",
        ["user_id", "address"],
    )
