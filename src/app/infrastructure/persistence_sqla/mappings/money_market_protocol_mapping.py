"""
SQLAlchemy mapping for money_market_protocols table.

Maps protocol registry table for money market rate comparisons.
This table stores protocol metadata (Aave V3, Compound V3, Morpho).
"""

from sqlalchemy import (
    Boolean,
    Integer,
    Numeric,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy import Enum as SQLEnum
import sqlalchemy as sa

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_money_market_protocols_table() -> None:
    """Map money_market_protocols table (idempotent)."""
    if "money_market_protocols" in mapping_registry.metadata.tables:
        return  # Already mapped
    
    # Create enum type for SQLAlchemy (using string values from migration)
    # Migration uses: 'aave_v3', 'compound_v3', 'morpho'
    protocol_enum = SQLEnum(
        "aave_v3",
        "compound_v3",
        "morpho",
        name="money_market_protocol_enum",
        create_type=False,  # Type already exists in DB
    )
    
    table = sa.Table(
        "money_market_protocols",
        mapping_registry.metadata,
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Protocol Information
        sa.Column(
            "protocol_name",
            protocol_enum,
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "display_name",
            String(50),
            nullable=False,
        ),
        sa.Column(
            "description",
            Text,
            nullable=True,
        ),
        # Chain Support
        sa.Column(
            "supported_chains",
            ARRAY(String(20)),
            nullable=False,
            server_default=sa.text("ARRAY['ethereum','polygon','arbitrum','optimism']"),
        ),
        # Contract Addresses (JSONB for multi-chain)
        sa.Column(
            "contract_addresses",
            JSONB,
            nullable=False,
            comment="Chain-specific contract addresses: {chain: {poolAddress, dataProvider, etc}}",
        ),
        # Protocol Metadata
        sa.Column(
            "total_tvl_usd",
            Numeric(20, 2),
            nullable=True,
            comment="Total value locked across all chains",
        ),
        sa.Column(
            "avg_supply_apy",
            Numeric(10, 4),
            nullable=True,
            comment="Average supply APY across all assets",
        ),
        sa.Column(
            "avg_borrow_apy",
            Numeric(10, 4),
            nullable=True,
            comment="Average borrow APY across all assets",
        ),
        sa.Column(
            "asset_count",
            Integer,
            nullable=False,
            server_default="0",
            comment="Number of supported assets",
        ),
        # Status
        sa.Column(
            "is_active",
            Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "priority",
            Integer,
            nullable=False,
            server_default="100",
            comment="Display priority (lower = higher priority)",
        ),
        # API Configuration
        sa.Column(
            "api_config",
            JSONB,
            nullable=True,
            comment="API endpoints, rate limits, etc.",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    
    # Create indexes
    sa.Index(
        "idx_money_market_protocols_name",
        table.c.protocol_name,
    )
    sa.Index(
        "idx_money_market_protocols_active",
        table.c.is_active,
        table.c.priority,
    )
