"""add_wallet_qr_columns

Revision ID: 047cc9a1c65e
Revises: 470ce2af2db6
Create Date: 2026-02-10 02:24:39.563657

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "047cc9a1c65e"
down_revision: Union[str, None] = "470ce2af2db6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add QR code columns to wallets table
    op.add_column(
        "wallets",
        sa.Column("qr_image_url", sa.String(512), nullable=True),
    )
    op.add_column(
        "wallets",
        sa.Column(
            "qr_storage_type",
            sa.String(10),
            nullable=True,
            server_default="pending",
        ),
    )
    op.add_column(
        "wallets",
        sa.Column("qr_generated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "wallets",
        sa.Column("qr_chain_id", sa.Integer(), nullable=True, server_default="8453"),
    )

    # Indexes for Celery task queries - partial indexes for efficient lookup
    op.create_index(
        "idx_wallets_qr_pending",
        "wallets",
        ["qr_storage_type"],
        postgresql_where=sa.text("qr_storage_type = 'pending' OR qr_storage_type IS NULL"),
    )
    op.create_index(
        "idx_wallets_qr_local",
        "wallets",
        ["qr_storage_type"],
        postgresql_where=sa.text("qr_storage_type = 'local'"),
    )


def downgrade() -> None:
    op.drop_index("idx_wallets_qr_local", table_name="wallets")
    op.drop_index("idx_wallets_qr_pending", table_name="wallets")
    op.drop_column("wallets", "qr_chain_id")
    op.drop_column("wallets", "qr_generated_at")
    op.drop_column("wallets", "qr_storage_type")
    op.drop_column("wallets", "qr_image_url")
