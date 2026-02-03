"""
SQLAlchemy mapping for lending_health_checks table.

Maps LendingHealthCheck domain entity to database table using explicit imperative mapping.
"""

from sqlalchemy import String, Numeric, DateTime, Enum
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_lending_health_checks_table() -> None:
    """Map lending_health_checks table (idempotent)."""
    if "lending_health_checks" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LendingHealthChecksTable:
        """
        Table metadata for lending_health_checks.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "lending_health_checks"
        __table_args__ = (
            sa.Index("idx_lending_health_checks_user_id", "user_id"),
            sa.Index("idx_lending_health_checks_checked_at", "checked_at"),
            sa.Index("idx_lending_health_checks_health_level", "health_factor_level"),
            sa.Index(
                "idx_lending_health_checks_user_protocol", "user_id", "protocol"
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
        protocol = mapped_column(String(20), nullable=False)
        chain = mapped_column(String(50), nullable=False)
        health_factor = mapped_column(Numeric(10, 2), nullable=False)
        health_factor_level = mapped_column(
            Enum(
                "safe",
                "caution",
                "danger",
                "critical",
                "liquidatable",
                name="health_factor_level_enum",
                create_type=False,
            ),
            nullable=False,
        )
        total_collateral_usd = mapped_column(Numeric(18, 2), nullable=False)
        total_debt_usd = mapped_column(Numeric(18, 2), nullable=False)
        available_to_borrow_usd = mapped_column(Numeric(18, 2), nullable=True)
        liquidation_price = mapped_column(Numeric(18, 8), nullable=True)
        checked_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
