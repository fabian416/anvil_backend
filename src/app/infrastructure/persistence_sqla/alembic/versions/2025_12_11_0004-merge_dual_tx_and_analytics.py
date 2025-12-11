"""Merge dual_tx and analytics heads.

Revision ID: merge_20251211
Revises: a731a70de118, dual_tx_20251211
Create Date: 2025-12-11
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "merge_20251211"
down_revision: tuple[str, str] = ("a731a70de118", "dual_tx_20251211")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge point - no changes needed."""
    pass


def downgrade() -> None:
    """Merge point - no changes needed."""
    pass
