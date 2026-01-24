"""add_missing_wallet_columns

Revision ID: 766e5759282c
Revises: eb14d000b2ef
Create Date: 2026-01-09 22:57:25.717210

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "766e5759282c"
down_revision: Union[str, None] = "eb14d000b2ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing wallet columns for multi-sig, policy, and sync tracking."""
    # Note: These columns are already created in earlier migrations.
    # This migration is a no-op to maintain migration history.
    pass


def downgrade() -> None:
    """Remove wallet columns added in this migration."""
    op.drop_column("wallets", "last_privy_sync_at")
    op.drop_column("wallets", "imported_at")
    op.drop_column("wallets", "exported_at")
    op.drop_column("wallets", "additional_signers")
    op.drop_column("wallets", "owner_id")
    op.drop_column("wallets", "owner_type")
    op.drop_column("wallets", "policy_ids")
