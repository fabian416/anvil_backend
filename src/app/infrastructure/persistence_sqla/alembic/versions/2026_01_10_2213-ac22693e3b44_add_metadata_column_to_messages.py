"""add_metadata_column_to_messages

Revision ID: ac22693e3b44
Revises: 766e5759282c
Create Date: 2026-01-10 22:13:32.599050

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "ac22693e3b44"
down_revision: Union[str, None] = "766e5759282c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add metadata column to messages table
    op.add_column(
        'messages',
        sa.Column('metadata', JSONB, nullable=True, server_default='{}')
    )


def downgrade() -> None:
    # Remove metadata column from messages table
    op.drop_column('messages', 'metadata')
