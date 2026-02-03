"""
SQLAlchemy mapping for lending_borrows table.

Maps BorrowPosition domain entity to database table.
"""

from sqlalchemy import String, Numeric, DateTime, Enum, BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_lending_borrows_table() -> None:
    """Map lending_borrows table (idempotent)."""
    if "lending_borrows" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LendingBorrowsTable:
        """
        Table metadata for lending_borrows.

        Defines table structure for borrow positions (Aave only).
        """

        __tablename__ = "lending_borrows"
        __table_args__ = (
            sa.Index("idx_lending_borrows_position_id", "position_id"),
            sa.Index("idx_lending_borrows_user_id", "user_id"),
            sa.Index("idx_lending_borrows_transaction_hash", "transaction_hash"),
            {"extend_existing": True},
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        position_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("lending_positions.id", ondelete="CASCADE"),
            nullable=False,
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
        asset_address = mapped_column(String(42), nullable=False)
        asset_symbol = mapped_column(String(20), nullable=False)
        amount = mapped_column(Numeric(78, 18), nullable=False)
        interest_rate = mapped_column(Numeric(6, 2), nullable=False)
        variable_rate = mapped_column(Boolean, nullable=False, server_default="true")
        health_factor_at_borrow = mapped_column(Numeric(10, 2), nullable=False)
        transaction_hash = mapped_column(String(66), nullable=False, unique=True)
        block_number = mapped_column(BigInteger, nullable=False)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
