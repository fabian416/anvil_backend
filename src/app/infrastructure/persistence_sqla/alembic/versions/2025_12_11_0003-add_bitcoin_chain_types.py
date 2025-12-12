"""Add bitcoin and bitcoin_testnet to chaintype enum.

Revision ID: btc_20251211
Revises: dtx_20251211
Create Date: 2025-12-11

This migration adds Bitcoin chain types to the PostgreSQL enum.
Since ALTER TYPE ADD VALUE cannot run inside a transaction,
we use autocommit mode.
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = "btc_20251211"
down_revision: Union[str, None] = "merge_20251211"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bitcoin chain types to the chaintype enum."""
    connection = op.get_bind()
    
    # Check if 'bitcoin' already exists in the enum
    result = connection.execute(text("""
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'bitcoin' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'chaintype')
    """))
    
    if not result.fetchone():
        # Must commit current transaction first, then add value
        connection.execute(text("COMMIT"))
        connection.execute(text("ALTER TYPE chaintype ADD VALUE 'bitcoin'"))
    
    # Check if 'bitcoin_testnet' already exists
    result = connection.execute(text("""
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'bitcoin_testnet' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'chaintype')
    """))
    
    if not result.fetchone():
        connection.execute(text("COMMIT"))
        connection.execute(text("ALTER TYPE chaintype ADD VALUE 'bitcoin_testnet'"))


def downgrade() -> None:
    """Cannot remove enum values in PostgreSQL easily."""
    # PostgreSQL doesn't support removing enum values directly
    # Would need to recreate the type, which is complex
    pass
