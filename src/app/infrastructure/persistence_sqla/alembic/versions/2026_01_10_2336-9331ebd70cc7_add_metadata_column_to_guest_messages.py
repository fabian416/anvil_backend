"""add_metadata_column_to_guest_messages

Revision ID: 9331ebd70cc7
Revises: ac22693e3b44
Create Date: 2026-01-10 23:36:03.923322

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "9331ebd70cc7"
down_revision: Union[str, None] = "ac22693e3b44"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add metadata column to guest_messages table
    op.add_column(
        'guest_messages',
        sa.Column('metadata', JSONB, nullable=True, server_default='{}')
    )


def downgrade() -> None:
    # Remove metadata column from guest_messages table
    op.drop_column('guest_messages', 'metadata')
