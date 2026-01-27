"""
SQLAlchemy mapping for lending_transactions table.

Maps LendingTransaction domain entity to database table.
"""

from sqlalchemy import String, Numeric, DateTime, Enum, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_lending_transactions_table() -> None:
    """Map lending_transactions table (idempotent)."""
    if "lending_transactions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LendingTransactionsTable:
        """
        Table metadata for lending_transactions.

        Tracks all lending operations with status and health factor impact.
        """

        __tablename__ = "lending_transactions"
        __table_args__ = (
            sa.Index(
                "idx_lending_transactions_user_id", "user_id"
            ),
            sa.Index(
                "idx_lending_transactions_transaction_hash", "transaction_hash"
            ),
            sa.Index(
                "idx_lending_transactions_status", "status"
            ),
            sa.Index(
                "idx_lending_transactions_user_protocol_action",
                "user_id",
                "protocol",
                "action_type",
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
                "morpho",
                name="protocol_enum",
                create_type=False,
            ),
            nullable=False,
        )
        chain = mapped_column(String(20), nullable=False)
        action_type = mapped_column(
            Enum(
                "supply",
                "withdraw",
                "borrow",
                "repay",
                "liquidate",
                name="lending_action_enum",
                create_type=False,
            ),
            nullable=False,
        )
        asset_address = mapped_column(String(42), nullable=False)
        asset_symbol = mapped_column(String(20), nullable=False)
        amount = mapped_column(Numeric(78, 18), nullable=False)
        transaction_hash = mapped_column(String(66), nullable=False, unique=True)
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
        health_factor_before = mapped_column(Numeric(10, 2), nullable=True)
        health_factor_after = mapped_column(Numeric(10, 2), nullable=True)
        metadata = mapped_column(JSONB, nullable=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        confirmed_at = mapped_column(DateTime(timezone=True), nullable=True)
