"""add eth_balance to chain_addresses

Revision ID: a5840134eea0
Revises: b2c3d4e5f6a7
Create Date: 2026-02-02 06:51:06.896282

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a5840134eea0"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add eth_balance column to store native ETH/gas token balance
    # This is needed to check if user has gas for transactions on each chain
    op.add_column(
        "chain_addresses",
        sa.Column("eth_balance", sa.Numeric(30, 18), nullable=True, default=0),
    )
    # Add comment for clarity
    op.execute(
        "COMMENT ON COLUMN chain_addresses.eth_balance IS "
        "'Native token balance (ETH/MATIC/etc) in full units for gas fee checks'"
    )


def downgrade() -> None:
    op.drop_column("chain_addresses", "eth_balance")
