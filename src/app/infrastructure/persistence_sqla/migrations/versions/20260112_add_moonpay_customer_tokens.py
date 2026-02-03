"""
Add moonpay_customer_tokens table for storing MoonPay authentication tokens.

Revision ID: moonpay_tokens_001
Revises: chat_phase2_001
Create Date: 2026-01-12

This table stores MoonPay authentication tokens received after users complete
KYC via the swapsCustomerSetup widget flow. These tokens are required to
execute swaps via the MoonPay API.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic
revision = "moonpay_tokens_001"
down_revision = "chat_phase2_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create moonpay_customer_tokens table."""
    op.create_table(
        "moonpay_customer_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("moonpay_token", sa.String(2048), nullable=False),
        sa.Column("moonpay_csrf_token", sa.String(2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime, nullable=True),
    )
    op.create_index(
        "ix_moonpay_customer_tokens_user_id",
        "moonpay_customer_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    """Drop moonpay_customer_tokens table."""
    op.drop_index(
        "ix_moonpay_customer_tokens_user_id", table_name="moonpay_customer_tokens"
    )
    op.drop_table("moonpay_customer_tokens")
