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
    pass


def downgrade() -> None:
    pass
