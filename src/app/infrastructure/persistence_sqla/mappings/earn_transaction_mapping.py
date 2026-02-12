"""
SQLAlchemy mapping for earn_transactions table.

Maps earn transactions (Aave V3 / Compound V3 supply/withdraw)
to database table. Mirrors lending_transactions pattern.
"""

from sqlalchemy import String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_earn_transactions_table() -> None:
    """Map earn_transactions table (idempotent)."""
    if "earn_transactions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class EarnTransactionsTable:
        """
        Table metadata for earn_transactions.

        Tracks Aave V3 and Compound V3 supply/withdraw operations
        with status, APY at time of transaction, and USD value.
        """

        __tablename__ = "earn_transactions"
        __table_args__ = (
            sa.Index(
                "idx_earn_transactions_user_id",
                "user_id",
            ),
            sa.Index(
                "idx_earn_transactions_tx_hash",
                "transaction_hash",
            ),
            sa.Index(
                "idx_earn_transactions_status",
                "status",
            ),
            sa.Index(
                "idx_earn_transactions_user_protocol_action",
                "user_id",
                "protocol",
                "action_type",
            ),
            sa.Index(
                "idx_earn_transactions_wallet",
                "wallet_address",
            ),
            {"extend_existing": True},
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
        )
        protocol = mapped_column(
            Enum(
                "aave",
                "compound",
                name="earn_protocol_enum",
                create_type=False,
            ),
            nullable=False,
        )
        chain = mapped_column(String(20), nullable=False)
        action_type = mapped_column(
            Enum(
                "supply",
                "withdraw",
                name="earn_action_enum",
                create_type=False,
            ),
            nullable=False,
        )
        asset_address = mapped_column(String(42), nullable=False)
        asset_symbol = mapped_column(String(20), nullable=False)
        amount = mapped_column(Numeric(78, 18), nullable=False)
        amount_usd = mapped_column(
            Numeric(18, 2),
            nullable=True,
        )
        apy_at_time = mapped_column(
            Numeric(6, 2),
            nullable=True,
        )
        transaction_hash = mapped_column(
            String(66),
            nullable=False,
            unique=True,
        )
        status = mapped_column(
            Enum(
                "pending",
                "confirmed",
                "failed",
                name="transaction_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        )
        wallet_address = mapped_column(String(42), nullable=True)
        pool_address = mapped_column(
            String(42),
            nullable=True,
        )
        metadata_ = mapped_column("metadata", JSONB, nullable=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        confirmed_at = mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
