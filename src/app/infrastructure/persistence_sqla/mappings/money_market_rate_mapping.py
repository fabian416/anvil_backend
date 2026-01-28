"""
SQLAlchemy mapping for money_market_rates table.

Maps MoneyMarketProtocolData domain entity to database table using table-only mapping.
This table stores cached rate data with 60s TTL for performance optimization.
"""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import mapped_column
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_rates_table() -> None:
    """Map money_market_rates table (idempotent)."""
    if "money_market_rates" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class MoneyMarketRatesTable:
        """
        Table metadata for money_market_rates (60s TTL cache).

        This is NOT mapped to the domain entity - it only defines table structure
        for create_all(). The repository uses raw SQL queries for CQRS pattern.
        """

        __tablename__ = "money_market_rates"
        __table_args__ = (
            # Partial index for active cache entries (hot path optimization)
            Index(
                "idx_money_market_rates_active_cache",
                "asset_symbol",
                "chain",
                "protocol_id",
                "valid_until",
                postgresql_where=sa.text("valid_until > NOW()"),
            ),
            # BRIN index for time-series queries (efficient on large datasets)
            Index(
                "idx_money_market_rates_brin_time",
                "created_at",
                "valid_until",
                postgresql_using="brin",
            ),
            # GIN index for JSONB metadata searches
            Index(
                "idx_money_market_rates_metadata_gin",
                "metadata",
                postgresql_using="gin",
            ),
            # Composite index for protocol-specific queries
            Index(
                "idx_money_market_rates_protocol_asset",
                "protocol_id",
                "asset_symbol",
                "chain",
            ),
            # Check constraints
            CheckConstraint(
                "supply_apy >= 0 AND supply_apy <= 10000",
                name="chk_supply_apy_range",
            ),
            CheckConstraint(
                "utilization_rate >= 0 AND utilization_rate <= 100",
                name="chk_utilization_range",
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

        # Protocol Reference
        protocol_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("money_market_protocols.id", ondelete="RESTRICT"),
            nullable=False,
        )

        # Asset & Chain
        asset_symbol = mapped_column(String(20), nullable=False)
        asset_address = mapped_column(String(42), nullable=False)
        chain = mapped_column(String(20), nullable=False)

        # Supply Rates
        supply_apy = mapped_column(
            Numeric(10, 4),
            nullable=False,
            comment="Annual percentage yield for supplying (e.g., 5.2500 = 5.25%)",
        )
        supply_apr = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Annual percentage rate (non-compounded)",
        )

        # Borrow Rates
        borrow_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Annual percentage yield for borrowing",
        )
        borrow_apr = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Annual percentage rate for borrowing",
        )
        variable_borrow_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Variable borrow APY (if applicable)",
        )
        stable_borrow_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            comment="Stable borrow APY (Aave only)",
        )

        # Market Metrics
        total_supply_usd = mapped_column(
            Numeric(20, 2),
            nullable=True,
            comment="Total supplied in USD",
        )
        total_borrow_usd = mapped_column(
            Numeric(20, 2),
            nullable=True,
            comment="Total borrowed in USD",
        )
        utilization_rate = mapped_column(
            Numeric(5, 2),
            nullable=True,
            comment="Utilization rate percentage (e.g., 75.50 = 75.5%)",
        )
        liquidity_usd = mapped_column(
            Numeric(20, 2),
            nullable=True,
            comment="Available liquidity in USD",
        )

        # Rewards & Incentives
        reward_tokens = mapped_column(
            JSONB,
            nullable=True,
            comment="Array of reward token APYs: [{symbol, apy, address}]",
        )
        total_incentive_apy = mapped_column(
            Numeric(10, 4),
            nullable=True,
            server_default="0",
            comment="Sum of all reward APYs",
        )

        # Data Source
        data_source = mapped_column(
            Enum(
                "on_chain",
                "api",
                "graph",
                "estimated",
                name="money_market_data_source_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="api",
        )

        # Cache Control (60s TTL)
        created_at = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        )
        valid_until = mapped_column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW() + INTERVAL '60 seconds'"),
            comment="Cache expiration time (60s TTL)",
        )
        last_updated_on_chain = mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="Timestamp from blockchain/API",
        )

        # Metadata (using column name to avoid conflict with SQLAlchemy's metadata attribute)
        metadata_json = mapped_column(
            "metadata",
            JSONB,
            nullable=True,
            comment="Additional protocol-specific data",
        )
