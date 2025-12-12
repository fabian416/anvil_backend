"""merge_heads_for_analytics

Revision ID: a731a70de118
Revises: add_privy_and_metrics, j0k1l2m3n4o5
Create Date: 2025-12-10 21:37:05.864876

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a731a70de118"
down_revision: Union[str, None] = ("add_privy_and_metrics", "txan_20251211")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
