"""merge_heads

Revision ID: 11f37a0774ff
Revises: 3f7f6f89818e, b85c12f320c7
Create Date: 2026-01-24 14:31:53.015191

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "11f37a0774ff"
down_revision: Union[str, None] = ("3f7f6f89818e", "b85c12f320c7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
