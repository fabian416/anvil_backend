"""Fix wallet enums and constraints for imported wallets.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2025-12-10 00:01:00.000000

This migration fixes issues that prevent imported wallets from being stored:
1. Adds "imported" to the walletprovider enum (ALREADY APPLIED MANUALLY)
2. Adds missing chain types to the chaintype enum (ALREADY APPLIED MANUALLY)
3. Makes privy_wallet_id nullable for imported wallets
4. Adds unique_user_wallet_address constraint if not exists
5. Removes unique constraint on address alone (user can have same address as another)

NOTE: Enum changes were applied manually via psql because PostgreSQL doesn't allow
ALTER TYPE ... ADD VALUE inside a transaction.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "wef_20251210"
down_revision: Union[str, None] = "pwc_20251209"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix wallet constraints and columns."""
    connection = op.get_bind()
    
    # NOTE: Enum values (imported, ethereum, polygon, optimism) were added manually
    # via psql because PostgreSQL doesn't allow ALTER TYPE ADD VALUE in transactions
    
    # 1. Make privy_wallet_id nullable (for imported wallets that don't have a Privy ID)
    op.alter_column(
        "wallets",
        "privy_wallet_id",
        existing_type=sa.String(255),
        nullable=True,
    )
    
    # 2. Drop the unique constraint on privy_wallet_id to allow NULL values
    # and multiple imported wallets without Privy IDs
    try:
        op.drop_constraint("uq_wallets_privy_wallet_id", "wallets", type_="unique")
    except Exception:
        pass  # Constraint may not exist
    
    # 3. Drop the unique constraint on address alone 
    # (a user should be able to have same address as another user)
    try:
        op.drop_constraint("uq_wallets_address", "wallets", type_="unique")
    except Exception:
        pass  # Constraint may not exist
    
    # Drop unique index on address if exists
    try:
        op.drop_index("ix_wallets_address", table_name="wallets")
    except Exception:
        pass  # Index may not exist
    
    # 4. Create non-unique index on address for faster lookups
    # Check if index already exists first
    result = connection.execute(text(
        "SELECT 1 FROM pg_indexes WHERE indexname = 'ix_wallets_address'"
    ))
    if not result.fetchone():
        op.create_index(
            "ix_wallets_address",
            "wallets",
            ["address"],
            unique=False,
        )
    
    # 5. Add unique constraint for user_id + address combination if not exists
    result = connection.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'unique_user_wallet_address'"
    ))
    if not result.fetchone():
        op.create_unique_constraint(
            "unique_user_wallet_address",
            "wallets",
            ["user_id", "address"],
        )


def downgrade() -> None:
    """Revert wallet constraint changes."""
    # Note: Enum values cannot be easily removed from PostgreSQL
    
    # Drop the composite unique constraint
    try:
        op.drop_constraint("unique_user_wallet_address", "wallets", type_="unique")
    except Exception:
        pass
    
    # Drop the non-unique index
    try:
        op.drop_index("ix_wallets_address", table_name="wallets")
    except Exception:
        pass
    
    # Recreate unique constraint on address
    try:
        op.create_unique_constraint(
            "uq_wallets_address",
            "wallets",
            ["address"],
        )
    except Exception:
        pass
    
    # Recreate unique constraint on privy_wallet_id
    try:
        op.create_unique_constraint(
            "uq_wallets_privy_wallet_id",
            "wallets",
            ["privy_wallet_id"],
        )
    except Exception:
        pass
    
    # Make privy_wallet_id NOT NULL again
    op.alter_column(
        "wallets",
        "privy_wallet_id",
        existing_type=sa.String(255),
        nullable=False,
    )
