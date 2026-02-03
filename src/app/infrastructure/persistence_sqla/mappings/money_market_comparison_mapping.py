"""
SQLAlchemy mapping for money_market_comparisons table.

Maps MoneyMarketRateComparison domain entity to database table using table-only mapping.
Logs every user comparison request for analytics and optimization tracking.
"""

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_comparisons_table() -> None:
    """Map money_market_comparisons table (idempotent)."""
    if "money_market_comparisons" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MoneyMarketComparisonsTable:
        """
        Table metadata for money_market_comparisons.

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "money_market_comparisons"
        __table_args__ = (
            # Indexes for common query patterns
            Index(
                "idx_money_market_comparisons_user_created",
                "user_id",
                "created_at",
            ),
            Index(
                "idx_money_market_comparisons_chain",
                "chain",
                "created_at",
            ),
            Index(
                "idx_money_market_comparisons_type",
                "comparison_type",
                "created_at",
            ),
            # GIN index for full_results JSONB
            Index(
                "idx_money_market_comparisons_results_gin",
                "full_results",
                postgresql_using="gin",
            ),
            {"extend_existing": True},
        )

        # Primary Key
        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )

        # User Reference
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

        # Comparison Type
        comparison_type = mapped_column(
            Enum(
                "supply",
                "borrow",
                "both",
                name="money_market_comparison_type_enum",
                create_type=False,
            ),
            nullable=False,
        )

        # Chain
        chain = mapped_column(String(20), nullable=False)

        # Comparison Results (denormalized for analytics)
        best_supply_protocol_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("money_market_protocols.id", ondelete="SET NULL"),
            nullable=True,
        )
        best_supply_apy = mapped_column(Numeric(10, 4), nullable=True)

        best_borrow_protocol_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("money_market_protocols.id", ondelete="SET NULL"),
            nullable=True,
        )
        best_borrow_apy = mapped_column(Numeric(10, 4), nullable=True)

        # Comparison Details
        protocols_compared = mapped_column(
            ARRAY(String(20)),
            nullable=False,
            comment="Array of protocol names compared",
        )
        assets_compared_count = mapped_column(
            Integer,
            nullable=False,
            server_default="1",
        )

        # Full Results (JSONB for detailed analysis)
        full_results = mapped_column(
            JSONB,
            nullable=False,
            comment="Complete comparison data: [{protocol, asset, supplyAPY, borrowAPY, etc}]",
        )

        # Optimization Suggestions
        suggestions = mapped_column(
            JSONB,
            nullable=True,
            comment="AI-generated optimization suggestions",
        )

        # Performance Metrics
        cache_hit_count = mapped_column(
            Integer,
            nullable=False,
            server_default="0",
            comment="Number of protocols served from cache",
        )
        rpc_call_count = mapped_column(
            Integer,
            nullable=False,
            server_default="0",
            comment="Number of RPC calls made",
        )
        execution_time_ms = mapped_column(
            Integer,
            nullable=True,
            comment="Total execution time in milliseconds",
        )

        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
