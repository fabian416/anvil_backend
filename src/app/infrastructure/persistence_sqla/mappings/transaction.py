"""
SQLAlchemy mapping for Transaction table metadata.

Stores on-chain transactions initiated by users via Privy/frontend.
Supports analytics with fields per TASKS.md requirements:
- Core: tx_hash, from (wallet_id), to_address, value, chain, type, status, user_id, created_at
- Analytics: gas_used, gas_price, metadata (JSON for extra context)
"""

import sqlalchemy as sa
from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import mapped_column

from app.domain.enums.chain_type import ChainType
from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_transaction_table() -> None:
    """Map Transaction entity to database table (idempotent)."""
    if "transactions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class TransactionsTable:
        __tablename__ = "transactions"
        __table_args__ = (
            # Unique constraint on (user_id, tx_hash) allows the same transaction
            # to appear in both sender's and receiver's history
            sa.UniqueConstraint(
                "user_id", "tx_hash", name="uq_transactions_user_tx_hash"
            ),
            {"extend_existing": True},
        )

        # Primary key
        id = mapped_column(Integer, primary_key=True, autoincrement=True)

        # Relationships
        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        wallet_id = mapped_column(
            Integer,
            ForeignKey("wallets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Core transaction details
        to_address = mapped_column(
            String(42), nullable=True, index=True
        )  # Recipient address (0x...)
        type = mapped_column(
            Integer, nullable=False, index=True
        )  # 0=SWAP, 1=FUND, 5=SEND, etc.
        chain = mapped_column(
            Enum(ChainType, values_callable=lambda x: [e.value for e in x]),
            nullable=False,
            index=True,
        )

        # Asset details
        asset_in = mapped_column(String(20), nullable=True)
        amount_in = mapped_column(Numeric(30, 18), nullable=True)
        asset_out = mapped_column(String(20), nullable=True)
        amount_out = mapped_column(Numeric(30, 18), nullable=True)

        # Fees
        fee = mapped_column(Numeric(30, 18), nullable=True)
        fee_usd = mapped_column(Numeric(10, 2), nullable=True)

        # On-chain data
        # NOTE: tx_hash is NOT globally unique - the same tx can appear for both sender
        # and receiver. Uniqueness is enforced by (user_id, tx_hash) via migration.
        tx_hash = mapped_column(String(66), nullable=True, index=True)
        status = mapped_column(
            Integer, default=0, nullable=False, index=True
        )  # 0=PENDING, 1=SUCCESS, 2=FAILED

        # DEX/Swap details
        dex_aggregator = mapped_column(String(50), nullable=True)
        dex_route = mapped_column(JSON, nullable=True)
        slippage = mapped_column(Numeric(5, 2), nullable=True)
        error_message = mapped_column(Text, nullable=True)

        # Confirmation data
        block_number = mapped_column(Integer, nullable=True, index=True)
        confirmed_at = mapped_column(DateTime(timezone=True), nullable=True)

        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )

        # Analytics fields (mid-term per TASKS.md)
        gas_used = mapped_column(BigInteger, nullable=True)  # Gas units consumed
        gas_price = mapped_column(BigInteger, nullable=True)  # Gas price in wei
        tx_metadata = mapped_column(
            JSON, nullable=True
        )  # Extra context: contract address, protocol, etc.
