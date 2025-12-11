"""
SQLAlchemy mapping for PortfolioSnapshot and TokenHolding tables.

These tables store point-in-time captures of wallet holdings
for analytics, history, and caching purposes.
"""

import sqlalchemy as sa
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import mapped_column

from app.domain.enums.chain_type import ChainType
from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_portfolio_snapshot_tables() -> None:
    """Map PortfolioSnapshot and TokenHolding entities to database tables (idempotent)."""
    if "portfolio_snapshots" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class PortfolioSnapshotsTable:
        __tablename__ = "portfolio_snapshots"
        __table_args__ = (
            Index("ix_portfolio_snapshots_wallet_captured", "wallet_id", "captured_at"),
            {"extend_existing": True},
        )

        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)

        # Relationships
        wallet_id = mapped_column(
            Integer,
            ForeignKey("wallets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Snapshot data
        chain = mapped_column(
            Enum(ChainType, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            index=True,
        )
        total_usd = mapped_column(Numeric(20, 8), nullable=False, default=0)
        native_balance = mapped_column(Numeric(36, 18), nullable=False, default=0)
        native_usd_value = mapped_column(Numeric(20, 8), nullable=True)

        # Timestamps
        captured_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            index=True,
        )
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    @mapping_registry.mapped
    class TokenHoldingsTable:
        __tablename__ = "token_holdings"
        __table_args__ = (
            Index(
                "ix_token_holdings_snapshot_token",
                "snapshot_id",
                "token_address",
            ),
            {"extend_existing": True},
        )

        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)

        # Relationships
        snapshot_id = mapped_column(
            Integer,
            ForeignKey("portfolio_snapshots.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Token data
        token_address = mapped_column(
            String(42),
            nullable=True,
            index=True,
        )  # None for native token
        symbol = mapped_column(String(20), nullable=False)
        name = mapped_column(String(100), nullable=False)
        decimals = mapped_column(Integer, nullable=False, default=18)

        # Balance and value
        amount = mapped_column(Numeric(36, 18), nullable=False, default=0)
        usd_value = mapped_column(Numeric(20, 8), nullable=True)
        usd_price = mapped_column(Numeric(20, 8), nullable=True)
        percentage = mapped_column(Numeric(10, 6), nullable=False, default=0)
