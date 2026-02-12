"""
SQLAlchemy mapping for swap_positions table.

Caches Hyperliquid spot balances and perps positions per wallet.
Background Celery task syncs every 60s; the "my swaps" agent reads from this
table instead of making live API calls (scales to 1000+ users).
"""

from sqlalchemy import String, Numeric, DateTime, Integer, ForeignKey
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_swap_positions_table() -> None:
    """Map swap_positions table (idempotent)."""
    if "swap_positions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class SwapPositionsTable:
        """
        Table metadata for swap_positions.

        NOT mapped to a domain entity – the repository / Celery task uses
        raw SQL for upserts (CQRS pattern).
        """

        __tablename__ = "swap_positions"
        __table_args__ = (
            sa.UniqueConstraint(
                "wallet_address",
                "source",
                "token",
                name="uq_swap_positions_wallet_source_token",
            ),
            sa.Index(
                "idx_swap_positions_wallet_source", "wallet_address", "source"
            ),
            sa.Index("idx_swap_positions_synced_at", "synced_at"),
            {"extend_existing": True},
        )

        id = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        wallet_address = mapped_column(String(42), nullable=False, index=True)
        source = mapped_column(String(10), nullable=False)  # "spot" or "perps"
        token = mapped_column(String(20), nullable=False)
        balance = mapped_column(
            Numeric(30, 18), nullable=False, server_default="0"
        )
        usd_value = mapped_column(
            Numeric(18, 2), nullable=False, server_default="0"
        )
        side = mapped_column(
            String(10), nullable=False, server_default="hold"
        )
        # Perps-only
        entry_price = mapped_column(Numeric(18, 6), nullable=True)
        mark_price = mapped_column(Numeric(18, 6), nullable=True)
        unrealized_pnl = mapped_column(Numeric(18, 6), nullable=True)
        leverage = mapped_column(Numeric(6, 2), nullable=True)
        liquidation_price = mapped_column(Numeric(18, 6), nullable=True)
        # Timestamps
        synced_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
