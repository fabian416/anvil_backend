"""
SQLAlchemy mapping for leverage_loop_executions table.

Maps LeverageLoopExecution domain entity to database table using explicit imperative mapping.
"""

from sqlalchemy import String, Numeric, Integer, DateTime, Enum, Text, ARRAY
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_leverage_loop_executions_table() -> None:
    """Map leverage_loop_executions table (idempotent)."""
    if "leverage_loop_executions" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class LeverageLoopExecutionsTable:
        """
        Table metadata for leverage_loop_executions.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "leverage_loop_executions"
        __table_args__ = (
            sa.Index("idx_leverage_loop_user_id", "user_id"),
            sa.Index("idx_leverage_loop_status", "status"),
            sa.Index("idx_leverage_loop_created_at", "created_at"),
            sa.Index("idx_leverage_loop_user_status", "user_id", "status"),
            {"extend_existing": True},
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        user_id = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
        protocol = mapped_column(String(20), nullable=False)
        chain = mapped_column(String(50), nullable=False)
        asset_address = mapped_column(String(42), nullable=False)
        asset_symbol = mapped_column(String(10), nullable=False)
        initial_amount = mapped_column(Numeric(78, 18), nullable=False)
        target_leverage = mapped_column(Numeric(3, 1), nullable=False)
        actual_leverage = mapped_column(Numeric(3, 1), nullable=True)
        total_steps = mapped_column(Integer, nullable=False)
        current_step = mapped_column(Integer, nullable=False, server_default="0")
        steps_completed = mapped_column(
            ARRAY(Text), nullable=False, server_default=sa.text("'{}'")
        )
        status = mapped_column(
            Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                "cancelled",
                name="loop_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        )
        final_health_factor = mapped_column(Numeric(10, 2), nullable=True)
        final_collateral_usd = mapped_column(Numeric(18, 2), nullable=True)
        final_debt_usd = mapped_column(Numeric(18, 2), nullable=True)
        total_gas_used = mapped_column(Numeric(78, 0), nullable=True)
        total_cost_usd = mapped_column(Numeric(18, 2), nullable=True)
        error_message = mapped_column(Text, nullable=True)
        metadata_ = mapped_column("metadata", JSONB, nullable=True)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
        completed_at = mapped_column(DateTime(timezone=True), nullable=True)
