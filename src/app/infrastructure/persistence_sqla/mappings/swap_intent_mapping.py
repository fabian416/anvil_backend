"""
SQLAlchemy mapping for swap_intents table.

Tracks swap execute_data opened from chat (swap workflow).
A Celery task watches pending intents for 15 minutes and updates tx history
when Hyperliquid userFills match.
"""

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import mapped_column

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_swap_intents_table() -> None:
    """Map swap_intents table (idempotent)."""
    if "swap_intents" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class SwapIntentsTable:
        __tablename__ = "swap_intents"
        __table_args__ = (
            sa.Index(
                "idx_swap_intents_pending_15min",
                "created_at",
                "status",
                postgresql_where=sa.text("status = 'pending' AND tx_hash IS NULL"),
            ),
            {"extend_existing": True},
        )

        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        wallet_id = mapped_column(
            Integer,
            ForeignKey("wallets.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        )
        wallet_address = mapped_column(String(42), nullable=False, index=True)
        conversation_id = mapped_column(sa.Uuid(), nullable=True, index=True)
        from_token = mapped_column(String(20), nullable=False)
        to_token = mapped_column(String(20), nullable=False)
        amount = mapped_column(Numeric(30, 18), nullable=False)
        source = mapped_column(String(50), nullable=False, server_default="hyperliquid_swap")
        tx_hash = mapped_column(String(66), nullable=True, index=True)
        status = mapped_column(String(20), nullable=False, server_default="pending", index=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        )
