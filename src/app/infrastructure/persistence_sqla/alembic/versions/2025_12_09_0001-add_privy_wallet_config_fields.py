"""Add Privy wallet configuration fields for admin management.

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-12-09 00:01:00.000000

This migration adds new columns to the wallets table to store
Privy wallet configuration data that can be managed by admins:
- policy_ids: JSON array of policy IDs attached to the wallet
- owner_type: Type of owner (user, authorization_key, etc.)
- owner_id: ID of the owner
- additional_signers: JSON array of additional signers with their configurations
- exported_at: Timestamp when the wallet was exported
- imported_at: Timestamp when the wallet was imported
- last_privy_sync_at: Last time we synced with Privy API
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "pwc_20251209"
down_revision: Union[str, None] = "retry_telemetry_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Privy wallet configuration columns."""
    # Add policy_ids column (JSON array)
    op.add_column(
        "wallets",
        sa.Column("policy_ids", sa.JSON(), nullable=True),
    )
    
    # Add owner_type column
    op.add_column(
        "wallets",
        sa.Column("owner_type", sa.String(50), nullable=True),
    )
    
    # Add owner_id column (for Privy owner identification)
    op.add_column(
        "wallets",
        sa.Column("owner_id", sa.String(255), nullable=True),
    )
    
    # Add additional_signers column (JSON array of signer objects)
    op.add_column(
        "wallets",
        sa.Column("additional_signers", sa.JSON(), nullable=True),
    )
    
    # Add exported_at timestamp
    op.add_column(
        "wallets",
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Add imported_at timestamp
    op.add_column(
        "wallets",
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
    )
    
    # Add last_privy_sync_at timestamp
    op.add_column(
        "wallets",
        sa.Column("last_privy_sync_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Remove Privy wallet configuration columns."""
    op.drop_column("wallets", "last_privy_sync_at")
    op.drop_column("wallets", "imported_at")
    op.drop_column("wallets", "exported_at")
    op.drop_column("wallets", "additional_signers")
    op.drop_column("wallets", "owner_id")
    op.drop_column("wallets", "owner_type")
    op.drop_column("wallets", "policy_ids")
