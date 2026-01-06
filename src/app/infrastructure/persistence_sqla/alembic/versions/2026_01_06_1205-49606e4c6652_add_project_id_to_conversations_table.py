"""add project_id to conversations table

Revision ID: 49606e4c6652
Revises: guest_chat_20251229
Create Date: 2026-01-06 12:05:45.065644

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "49606e4c6652"
down_revision: Union[str, None] = "guest_chat_20251229"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add project_id column to conversations table (nullable)
    op.add_column(
        "conversations",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    # Remove project_id column from conversations table
    op.drop_column("conversations", "project_id")
