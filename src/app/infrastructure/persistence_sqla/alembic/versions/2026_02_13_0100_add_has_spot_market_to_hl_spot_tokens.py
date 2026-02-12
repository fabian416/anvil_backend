"""add has_spot_market column to hl_spot_tokens

Distinguishes tokens with an active Core spot order book (tradeable via API)
from EVM-only tokens that exist in spotMeta.tokens but have no universe entry.

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-13 01:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # has_spot_market: True when the token is a base asset in spotMeta.universe
    # (i.e. it has a Core spot order book and can be traded via the API).
    # Tokens that only exist as EVM tokens get False.
    op.add_column(
        "hl_spot_tokens",
        sa.Column(
            "has_spot_market",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    # Index for the sentiment query that filters tradeable tokens
    op.create_index(
        "idx_hl_spot_tokens_tradeable_sentiment",
        "hl_spot_tokens",
        ["has_spot_market", "status", "sentiment_score"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_hl_spot_tokens_tradeable_sentiment",
        table_name="hl_spot_tokens",
    )
    op.drop_column("hl_spot_tokens", "has_spot_market")
