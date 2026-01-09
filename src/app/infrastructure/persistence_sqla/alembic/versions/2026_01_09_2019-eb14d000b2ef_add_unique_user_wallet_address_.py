"""add_unique_user_wallet_address_constraint

Revision ID: eb14d000b2ef
Revises: expand_agenttype_enum
Create Date: 2026-01-09 20:19:46.340580

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "eb14d000b2ef"
down_revision: Union[str, None] = "expand_agenttype_enum"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique_user_wallet_address constraint if it doesn't exist."""
    connection = op.get_bind()
    
    # Check if constraint exists
    from sqlalchemy import text
    result = connection.execute(text(
        "SELECT 1 FROM pg_constraint WHERE conname = 'unique_user_wallet_address' AND conrelid = 'wallets'::regclass"
    ))
    if not result.fetchone():
        op.create_unique_constraint(
            "unique_user_wallet_address",
            "wallets",
            ["user_id", "address"],
        )


def downgrade() -> None:
    """Remove unique_user_wallet_address constraint."""
    try:
        op.drop_constraint("unique_user_wallet_address", "wallets", type_="unique")
    except Exception:
        pass  # Constraint may not exist
