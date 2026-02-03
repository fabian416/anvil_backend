"""
SQLAlchemy mapping for lending_positions table.

Maps LendingPosition domain entity to database table using explicit imperative mapping.
"""

from sqlalchemy import String, Numeric, DateTime, Enum
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_lending_positions_table() -> None:
    """Map lending_positions table (idempotent)."""
    if "lending_positions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LendingPositionsTable:
        """
        Table metadata for lending_positions.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "lending_positions"
        __table_args__ = (
            sa.Index(
                "idx_lending_positions_user_protocol", "user_id", "protocol"
            ),
            sa.Index("idx_lending_positions_status", "status"),
            sa.Index(
                "idx_lending_positions_user_protocol_status",
                "user_id",
                "protocol",
                "status",
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
            UUID(as_uuid=True), nullable=False, index=True
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
        position_type = mapped_column(
            Enum(
                "supply",
                "borrow",
                name="position_type_enum",
                create_type=False,
            ),
            nullable=False,
        )
        asset_address = mapped_column(String(42), nullable=False)
        asset_symbol = mapped_column(String(20), nullable=False)
        amount = mapped_column(Numeric(78, 18), nullable=False)
        amount_usd = mapped_column(Numeric(18, 2), nullable=False)
        health_factor = mapped_column(Numeric(10, 2), nullable=True)
        apy = mapped_column(Numeric(6, 2), nullable=False)
        status = mapped_column(
            Enum(
                "active",
                "closed",
                "liquidated",
                name="lending_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        )
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
