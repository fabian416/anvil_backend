"""money_market_core_001_create_money_market_tables

Create money market tables for rate comparison and optimization:
- money_market_protocols: Protocol registry (Aave V3, Compound V3, Morpho)
- money_market_rates: Rate cache with 60s TTL
- money_market_comparisons: User comparison history
- money_market_user_preferences: User settings and preferences
- money_market_rate_alerts: Rate monitoring alerts
- money_market_alert_history: Alert notification log
- v_latest_money_market_rates: Latest rates view
- v_best_supply_rates: Best supply rates view
- v_protocol_comparison_summary: Protocol comparison summary

NOTE: money_market_comparison_assets table was commented out on 2026-02-01
because no SQLAlchemy mapping or application code exists for it.

Revision ID: money_market_core_001
Revises: lending_core_002
Create Date: 2026-01-28 01:51:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

# revision identifiers, used by Alembic
revision = "money_market_core_001"
down_revision = "lending_core_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create money market tables, indexes, and views."""

    # =========================================================================
    # CREATE POSTGRESQL ENUMS (drop existing first for idempotency)
    # =========================================================================

    # Drop ENUMs if they exist (idempotent - no error if not exists)
    op.execute("DROP TYPE IF EXISTS money_market_protocol_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS money_market_data_source_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS money_market_comparison_type_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS money_market_alert_condition_enum CASCADE;")
    op.execute("DROP TYPE IF EXISTS money_market_notification_channel_enum CASCADE;")

    # Create ENUMs
    op.execute(
        "CREATE TYPE money_market_protocol_enum AS ENUM ('aave_v3', 'compound_v3', 'morpho');"
    )
    op.execute(
        "CREATE TYPE money_market_data_source_enum AS ENUM ('on_chain', 'api', 'graph', 'estimated');"
    )
    op.execute(
        "CREATE TYPE money_market_comparison_type_enum AS ENUM ('supply', 'borrow', 'both');"
    )
    op.execute(
        "CREATE TYPE money_market_alert_condition_enum AS ENUM ('rate_above', 'rate_below', 'rate_change_percent', 'best_rate_available');"
    )
    op.execute(
        "CREATE TYPE money_market_notification_channel_enum AS ENUM ('email', 'push', 'in_app');"
    )

    # =========================================================================
    # TABLE 1: money_market_protocols (Protocol Registry)
    # =========================================================================

    op.create_table(
        "money_market_protocols",
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
            sa.Enum(
                "aave_v3",
                "compound_v3",
                "morpho",
                name="money_market_protocol_enum",
                create_type=False,
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "display_name",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text,
            nullable=True,
        ),
        # Chain Support
        sa.Column(
            "supported_chains",
            sa.ARRAY(sa.String(20)),
            nullable=False,
            server_default="'{ethereum,polygon,arbitrum,optimism}'",
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
            sa.Numeric(20, 2),
            nullable=True,
            comment="Total value locked across all chains",
        ),
        sa.Column(
            "avg_supply_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Average supply APY across all assets",
        ),
        sa.Column(
            "avg_borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Average borrow APY across all assets",
        ),
        sa.Column(
            "asset_count",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="Number of supported assets",
        ),
        # Status
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "priority",
            sa.Integer,
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
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Indexes for money_market_protocols
    op.create_index(
        "idx_money_market_protocols_name",
        "money_market_protocols",
        ["protocol_name"],
    )
    op.create_index(
        "idx_money_market_protocols_active",
        "money_market_protocols",
        ["is_active", "priority"],
    )

    # =========================================================================
    # TABLE 2: money_market_rates (Rate Cache - 60s TTL)
    # =========================================================================

    op.create_table(
        "money_market_rates",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Protocol Reference
        sa.Column(
            "protocol_id",
            UUID(as_uuid=True),
            sa.ForeignKey("money_market_protocols.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Asset & Chain
        sa.Column(
            "asset_symbol",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "asset_address",
            sa.String(42),
            nullable=False,
        ),
        sa.Column(
            "chain",
            sa.String(20),
            nullable=False,
        ),
        # Supply Rates
        sa.Column(
            "supply_apy",
            sa.Numeric(10, 4),
            nullable=False,
            comment="Annual percentage yield for supplying (e.g., 5.2500 = 5.25%)",
        ),
        sa.Column(
            "supply_apr",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Annual percentage rate (non-compounded)",
        ),
        # Borrow Rates
        sa.Column(
            "borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Annual percentage yield for borrowing",
        ),
        sa.Column(
            "borrow_apr",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Annual percentage rate for borrowing",
        ),
        sa.Column(
            "variable_borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Variable borrow APY (if applicable)",
        ),
        sa.Column(
            "stable_borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Stable borrow APY (Aave only)",
        ),
        # Market Metrics
        sa.Column(
            "total_supply_usd",
            sa.Numeric(20, 2),
            nullable=True,
            comment="Total supplied in USD",
        ),
        sa.Column(
            "total_borrow_usd",
            sa.Numeric(20, 2),
            nullable=True,
            comment="Total borrowed in USD",
        ),
        sa.Column(
            "utilization_rate",
            sa.Numeric(5, 2),
            nullable=True,
            comment="Utilization rate percentage (e.g., 75.50 = 75.5%)",
        ),
        sa.Column(
            "liquidity_usd",
            sa.Numeric(20, 2),
            nullable=True,
            comment="Available liquidity in USD",
        ),
        # Rewards & Incentives
        sa.Column(
            "reward_tokens",
            JSONB,
            nullable=True,
            comment="Array of reward token APYs: [{symbol, apy, address}]",
        ),
        sa.Column(
            "total_incentive_apy",
            sa.Numeric(10, 4),
            nullable=True,
            server_default="0",
            comment="Sum of all reward APYs",
        ),
        # Data Source
        sa.Column(
            "data_source",
            sa.Enum(
                "on_chain",
                "api",
                "graph",
                "estimated",
                name="money_market_data_source_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="api",
        ),
        # Cache Control (60s TTL)
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "valid_until",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW() + INTERVAL '60 seconds'"),
            comment="Cache expiration time (60s TTL)",
        ),
        sa.Column(
            "last_updated_on_chain",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Timestamp from blockchain/API",
        ),
        # Metadata
        sa.Column(
            "metadata",
            JSONB,
            nullable=True,
            comment="Additional protocol-specific data",
        ),
        # Constraints
        sa.CheckConstraint(
            "supply_apy >= 0 AND supply_apy <= 10000",
            name="chk_supply_apy_range",
        ),
        sa.CheckConstraint(
            "utilization_rate >= 0 AND utilization_rate <= 100",
            name="chk_utilization_range",
        ),
    )

    # CRITICAL INDEXES for money_market_rates (Hot Path Optimization)

    # 1. Partial index for active cache entries (WHERE valid_until > NOW())
    op.create_index(
        "idx_money_market_rates_active_cache",
        "money_market_rates",
        ["asset_symbol", "chain", "protocol_id", "valid_until"],
        postgresql_where=sa.text("valid_until > NOW()"),
    )

    # 2. Covering index for common query pattern (avoid table lookups)
    op.execute("""
        CREATE INDEX idx_money_market_rates_covering 
        ON money_market_rates (protocol_id, asset_symbol, chain)
        INCLUDE (supply_apy, borrow_apy, total_incentive_apy, utilization_rate, created_at, valid_until)
        WHERE valid_until > NOW();
    """)

    # 3. BRIN index for time-series queries (efficient on large datasets)
    op.create_index(
        "idx_money_market_rates_brin_time",
        "money_market_rates",
        ["created_at", "valid_until"],
        postgresql_using="brin",
    )

    # 4. GIN index for JSONB metadata searches
    op.create_index(
        "idx_money_market_rates_metadata_gin",
        "money_market_rates",
        ["metadata"],
        postgresql_using="gin",
    )

    # 5. Composite index for protocol-specific queries
    op.create_index(
        "idx_money_market_rates_protocol_asset",
        "money_market_rates",
        ["protocol_id", "asset_symbol", "chain"],
    )

    # =========================================================================
    # TABLE 3: money_market_comparisons (Comparison Results)
    # =========================================================================

    op.create_table(
        "money_market_comparisons",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Comparison Type
        sa.Column(
            "comparison_type",
            sa.Enum(
                "supply",
                "borrow",
                "both",
                name="money_market_comparison_type_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        # Chain
        sa.Column(
            "chain",
            sa.String(20),
            nullable=False,
        ),
        # Comparison Results (denormalized for analytics)
        sa.Column(
            "best_supply_protocol_id",
            UUID(as_uuid=True),
            sa.ForeignKey("money_market_protocols.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "best_supply_apy",
            sa.Numeric(10, 4),
            nullable=True,
        ),
        sa.Column(
            "best_borrow_protocol_id",
            UUID(as_uuid=True),
            sa.ForeignKey("money_market_protocols.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "best_borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
        ),
        # Comparison Details
        sa.Column(
            "protocols_compared",
            sa.ARRAY(sa.String(20)),
            nullable=False,
            comment="Array of protocol names compared",
        ),
        sa.Column(
            "assets_compared_count",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        # Full Results (JSONB for detailed analysis)
        sa.Column(
            "full_results",
            JSONB,
            nullable=False,
            comment="Complete comparison data: [{protocol, asset, supplyAPY, borrowAPY, etc}]",
        ),
        # Optimization Suggestions
        sa.Column(
            "suggestions",
            JSONB,
            nullable=True,
            comment="AI-generated optimization suggestions",
        ),
        # Performance Metrics
        sa.Column(
            "cache_hit_count",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="Number of protocols served from cache",
        ),
        sa.Column(
            "rpc_call_count",
            sa.Integer,
            nullable=False,
            server_default="0",
            comment="Number of RPC calls made",
        ),
        sa.Column(
            "execution_time_ms",
            sa.Integer,
            nullable=True,
            comment="Total execution time in milliseconds",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Indexes for money_market_comparisons
    op.create_index(
        "idx_money_market_comparisons_user_created",
        "money_market_comparisons",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_money_market_comparisons_chain",
        "money_market_comparisons",
        ["chain", "created_at"],
    )
    op.create_index(
        "idx_money_market_comparisons_type",
        "money_market_comparisons",
        ["comparison_type", "created_at"],
    )
    # GIN index for full_results JSONB
    op.create_index(
        "idx_money_market_comparisons_results_gin",
        "money_market_comparisons",
        ["full_results"],
        postgresql_using="gin",
    )

    # =========================================================================
    # TABLE 4: money_market_user_preferences (User Settings)
    # =========================================================================

    op.create_table(
        "money_market_user_preferences",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference (one-to-one)
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Preferred Protocols
        sa.Column(
            "preferred_protocols",
            sa.ARRAY(sa.String(20)),
            nullable=True,
            comment="User's preferred protocols for comparisons",
        ),
        sa.Column(
            "excluded_protocols",
            sa.ARRAY(sa.String(20)),
            nullable=True,
            comment="Protocols to exclude from comparisons",
        ),
        # Chain Preferences
        sa.Column(
            "preferred_chains",
            sa.ARRAY(sa.String(20)),
            nullable=True,
            comment="Preferred blockchain networks",
        ),
        # Rate Preferences
        sa.Column(
            "min_supply_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Minimum acceptable supply APY",
        ),
        sa.Column(
            "max_borrow_apy",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Maximum acceptable borrow APY",
        ),
        # Risk Preferences
        sa.Column(
            "risk_tolerance",
            sa.String(20),
            nullable=False,
            server_default="moderate",
            comment="'conservative', 'moderate', 'aggressive'",
        ),
        sa.Column(
            "min_liquidity_usd",
            sa.Numeric(20, 2),
            nullable=True,
            comment="Minimum liquidity required",
        ),
        sa.Column(
            "max_utilization_rate",
            sa.Numeric(5, 2),
            nullable=True,
            comment="Maximum acceptable utilization rate",
        ),
        # Notification Preferences
        sa.Column(
            "enable_rate_alerts",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "notification_channels",
            sa.ARRAY(sa.String(20)),
            nullable=False,
            server_default="'{in_app}'",
            comment="Array of enabled notification channels",
        ),
        # Display Preferences
        sa.Column(
            "show_rewards",
            sa.Boolean,
            nullable=False,
            server_default="true",
            comment="Include reward APY in comparisons",
        ),
        sa.Column(
            "sort_by",
            sa.String(20),
            nullable=False,
            server_default="best_rate",
            comment="'best_rate', 'tvl', 'liquidity', 'utilization'",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "risk_tolerance IN ('conservative', 'moderate', 'aggressive')",
            name="chk_risk_tolerance",
        ),
        sa.CheckConstraint(
            "sort_by IN ('best_rate', 'tvl', 'liquidity', 'utilization')",
            name="chk_sort_by",
        ),
    )

    # Indexes for money_market_user_preferences
    op.create_index(
        "idx_money_market_user_preferences_user_id",
        "money_market_user_preferences",
        ["user_id"],
    )

    # =========================================================================
    # TABLE 5: money_market_rate_alerts (Rate Monitoring)
    # =========================================================================

    op.create_table(
        "money_market_rate_alerts",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Protocol & Asset
        sa.Column(
            "protocol_id",
            UUID(as_uuid=True),
            sa.ForeignKey("money_market_protocols.id", ondelete="CASCADE"),
            nullable=True,
            comment="Null = any protocol",
        ),
        sa.Column(
            "asset_symbol",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "chain",
            sa.String(20),
            nullable=False,
        ),
        # Alert Configuration
        sa.Column(
            "alert_type",
            sa.String(20),
            nullable=False,
            comment="'supply' or 'borrow'",
        ),
        sa.Column(
            "condition",
            sa.Enum(
                "rate_above",
                "rate_below",
                "rate_change_percent",
                "best_rate_available",
                name="money_market_alert_condition_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "threshold_value",
            sa.Numeric(10, 4),
            nullable=True,
            comment="Threshold APY or percentage change",
        ),
        # Notification Settings
        sa.Column(
            "notification_channels",
            sa.ARRAY(
                sa.Enum(
                    "email",
                    "push",
                    "in_app",
                    name="money_market_notification_channel_enum",
                    create_type=False,
                )
            ),
            nullable=False,
            server_default="'{in_app}'",
        ),
        sa.Column(
            "cooldown_minutes",
            sa.Integer,
            nullable=False,
            server_default="60",
            comment="Minimum time between alerts",
        ),
        # Status
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "triggered_count",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "last_triggered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "alert_type IN ('supply', 'borrow')",
            name="chk_alert_type",
        ),
        sa.CheckConstraint(
            "cooldown_minutes >= 1 AND cooldown_minutes <= 1440",
            name="chk_cooldown_range",
        ),
    )

    # Indexes for money_market_rate_alerts
    op.create_index(
        "idx_money_market_rate_alerts_user_active",
        "money_market_rate_alerts",
        ["user_id", "is_active"],
    )
    op.create_index(
        "idx_money_market_rate_alerts_asset_chain",
        "money_market_rate_alerts",
        ["asset_symbol", "chain", "is_active"],
    )
    # Partial index for active alerts ready to trigger
    op.create_index(
        "idx_money_market_rate_alerts_ready",
        "money_market_rate_alerts",
        ["asset_symbol", "chain", "condition"],
        postgresql_where=sa.text(
            "is_active = true AND (last_triggered_at IS NULL OR last_triggered_at < NOW() - (cooldown_minutes || ' minutes')::INTERVAL)"
        ),
    )

    # =========================================================================
    # TABLE 6: money_market_comparison_assets (M2M Junction)
    # COMMENTED OUT: This table was never implemented in the application code.
    # No SQLAlchemy mapping exists and no code references this table.
    # Removed on 2026-02-01 to keep migrations in sync with actual usage.
    # =========================================================================

    # op.create_table(
    #     "money_market_comparison_assets",
    #     # Primary Key
    #     sa.Column(
    #         "id",
    #         UUID(as_uuid=True),
    #         primary_key=True,
    #         server_default=sa.text("gen_random_uuid()"),
    #     ),
    #     # Foreign Keys
    #     sa.Column(
    #         "comparison_id",
    #         UUID(as_uuid=True),
    #         sa.ForeignKey("money_market_comparisons.id", ondelete="CASCADE"),
    #         nullable=False,
    #     ),
    #     sa.Column(
    #         "asset_symbol",
    #         sa.String(20),
    #         nullable=False,
    #     ),
    #     sa.Column(
    #         "asset_address",
    #         sa.String(42),
    #         nullable=True,
    #     ),
    #     # Amount (optional)
    #     sa.Column(
    #         "amount",
    #         sa.Numeric(78, 18),
    #         nullable=True,
    #         comment="Amount to supply/borrow (for yield calculation)",
    #     ),
    #     # Timestamps
    #     sa.Column(
    #         "created_at",
    #         sa.TIMESTAMP(timezone=True),
    #         nullable=False,
    #         server_default=sa.text("NOW()"),
    #     ),
    #     # Unique constraint
    #     sa.UniqueConstraint(
    #         "comparison_id",
    #         "asset_symbol",
    #         name="uq_comparison_asset",
    #     ),
    # )

    # Indexes for money_market_comparison_assets (commented out)
    # op.create_index(
    #     "idx_money_market_comparison_assets_comparison",
    #     "money_market_comparison_assets",
    #     ["comparison_id"],
    # )
    # op.create_index(
    #     "idx_money_market_comparison_assets_asset",
    #     "money_market_comparison_assets",
    #     ["asset_symbol"],
    # )

    # =========================================================================
    # TABLE 7: money_market_alert_history (Alert Log)
    # =========================================================================

    op.create_table(
        "money_market_alert_history",
        # Primary Key
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Alert Reference
        sa.Column(
            "alert_id",
            UUID(as_uuid=True),
            sa.ForeignKey("money_market_rate_alerts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # User Reference
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # Alert Details
        sa.Column(
            "alert_type",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "condition_met",
            sa.String(100),
            nullable=False,
            comment="Human-readable condition that was met",
        ),
        # Rate Details
        sa.Column(
            "protocol_name",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "asset_symbol",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "chain",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "current_rate",
            sa.Numeric(10, 4),
            nullable=False,
        ),
        sa.Column(
            "threshold_value",
            sa.Numeric(10, 4),
            nullable=True,
        ),
        # Notification Status
        sa.Column(
            "notification_sent",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "notification_channels_used",
            sa.ARRAY(sa.String(20)),
            nullable=True,
        ),
        sa.Column(
            "notification_error",
            sa.Text,
            nullable=True,
        ),
        # Metadata
        sa.Column(
            "metadata",
            JSONB,
            nullable=True,
            comment="Additional context (rate_id, comparison results, etc.)",
        ),
        # Timestamps
        sa.Column(
            "triggered_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "notified_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    # Indexes for money_market_alert_history
    op.create_index(
        "idx_money_market_alert_history_alert",
        "money_market_alert_history",
        ["alert_id", "triggered_at"],
    )
    op.create_index(
        "idx_money_market_alert_history_user",
        "money_market_alert_history",
        ["user_id", "triggered_at"],
    )
    op.create_index(
        "idx_money_market_alert_history_notification_status",
        "money_market_alert_history",
        ["notification_sent", "triggered_at"],
    )

    # =========================================================================
    # VIEW 1: v_latest_money_market_rates (Latest Valid Rates)
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW v_latest_money_market_rates AS
        SELECT DISTINCT ON (r.protocol_id, r.asset_symbol, r.chain)
            r.id,
            r.protocol_id,
            p.protocol_name,
            p.display_name AS protocol_display_name,
            r.asset_symbol,
            r.asset_address,
            r.chain,
            r.supply_apy,
            r.supply_apr,
            r.borrow_apy,
            r.borrow_apr,
            r.variable_borrow_apy,
            r.stable_borrow_apy,
            r.total_supply_usd,
            r.total_borrow_usd,
            r.utilization_rate,
            r.liquidity_usd,
            r.reward_tokens,
            r.total_incentive_apy,
            (r.supply_apy + COALESCE(r.total_incentive_apy, 0)) AS total_supply_apy,
            r.data_source,
            r.created_at,
            r.valid_until,
            r.metadata
        FROM
            money_market_rates r
            INNER JOIN money_market_protocols p ON r.protocol_id = p.id
        WHERE
            r.valid_until > NOW()
            AND p.is_active = true
        ORDER BY
            r.protocol_id, r.asset_symbol, r.chain, r.created_at DESC;
    """)

    op.execute("""
        COMMENT ON VIEW v_latest_money_market_rates IS 
        'Latest valid (non-expired) rates for each protocol/asset/chain combination with protocol details';
    """)

    # =========================================================================
    # VIEW 2: v_best_supply_rates (Best Supply Rates per Asset/Chain)
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW v_best_supply_rates AS
        SELECT
            asset_symbol,
            chain,
            protocol_id AS best_protocol_id,
            protocol_display_name AS best_protocol_name,
            total_supply_apy AS best_total_apy,
            supply_apy AS best_base_apy,
            total_incentive_apy AS best_reward_apy,
            total_supply_usd AS tvl_usd,
            utilization_rate,
            liquidity_usd,
            created_at AS rate_updated_at
        FROM (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY asset_symbol, chain 
                    ORDER BY total_supply_apy DESC, liquidity_usd DESC
                ) AS rank
            FROM v_latest_money_market_rates
            WHERE supply_apy IS NOT NULL
        ) ranked
        WHERE rank = 1;
    """)

    op.execute("""
        COMMENT ON VIEW v_best_supply_rates IS 
        'Best supply APY for each asset/chain combination across all protocols';
    """)

    # =========================================================================
    # VIEW 3: v_protocol_comparison_summary (Protocol Performance Summary)
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE VIEW v_protocol_comparison_summary AS
        SELECT
            p.protocol_name,
            p.display_name,
            COUNT(DISTINCT r.asset_symbol) AS unique_assets,
            COUNT(DISTINCT r.chain) AS supported_chains,
            AVG(r.supply_apy) AS avg_supply_apy,
            MAX(r.supply_apy) AS max_supply_apy,
            AVG(r.borrow_apy) FILTER (WHERE r.borrow_apy IS NOT NULL) AS avg_borrow_apy,
            MIN(r.borrow_apy) FILTER (WHERE r.borrow_apy IS NOT NULL) AS min_borrow_apy,
            SUM(r.total_supply_usd) AS total_tvl_usd,
            SUM(r.total_borrow_usd) AS total_borrowed_usd,
            AVG(r.utilization_rate) AS avg_utilization_rate,
            AVG(r.total_incentive_apy) FILTER (WHERE r.total_incentive_apy > 0) AS avg_reward_apy,
            COUNT(*) AS total_markets,
            MAX(r.created_at) AS last_rate_update
        FROM
            money_market_protocols p
            INNER JOIN money_market_rates r ON p.id = r.protocol_id
        WHERE
            r.valid_until > NOW()
            AND p.is_active = true
        GROUP BY
            p.protocol_name, p.display_name
        ORDER BY
            total_tvl_usd DESC;
    """)

    op.execute("""
        COMMENT ON VIEW v_protocol_comparison_summary IS 
        'Aggregated protocol performance metrics for comparison analytics';
    """)

    # =========================================================================
    # SEED DATA: Insert Protocol Registry
    # =========================================================================

    # Seed Aave V3
    op.execute("""
        INSERT INTO money_market_protocols (
            protocol_name,
            display_name,
            description,
            supported_chains,
            contract_addresses,
            is_active,
            priority,
            api_config
        ) VALUES (
            'aave_v3',
            'Aave V3',
            'Leading decentralized lending protocol with multi-chain support and advanced features like isolation mode and e-mode',
            ARRAY['ethereum', 'polygon', 'arbitrum', 'optimism', 'base', 'avalanche'],
            '{
                "ethereum": {
                    "poolAddress": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
                    "poolDataProvider": "0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3"
                },
                "polygon": {
                    "poolAddress": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
                    "poolDataProvider": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
                },
                "arbitrum": {
                    "poolAddress": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
                    "poolDataProvider": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
                },
                "optimism": {
                    "poolAddress": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
                    "poolDataProvider": "0x69FA688f1Dc47d4B5d8029D5a35FB7a548310654"
                }
            }'::jsonb,
            true,
            1,
            '{
                "apiEndpoint": "https://aave-api-v2.aave.com",
                "subgraphUrl": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
                "rateLimit": 100,
                "rateLimitWindow": 60
            }'::jsonb
        ) ON CONFLICT (protocol_name) DO NOTHING;
    """)

    # Seed Compound V3
    op.execute("""
        INSERT INTO money_market_protocols (
            protocol_name,
            display_name,
            description,
            supported_chains,
            contract_addresses,
            is_active,
            priority,
            api_config
        ) VALUES (
            'compound_v3',
            'Compound V3',
            'Battle-tested lending protocol with isolated markets and superior capital efficiency',
            ARRAY['ethereum', 'polygon', 'arbitrum', 'base'],
            '{
                "ethereum": {
                    "cometUSDC": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
                    "cometWETH": "0xA17581A9E3356d9A858b789D68B4d866e593aE94"
                },
                "polygon": {
                    "cometUSDC": "0xF25212E676D1F7F89Cd72fFEe66158f541246445"
                },
                "arbitrum": {
                    "cometUSDC": "0x9c4ec768c28520B50860ea7a15bd7213a9fF58bf"
                },
                "base": {
                    "cometUSDC": "0x46e6b214b524310239732D51387075E0e70970bf"
                }
            }'::jsonb,
            true,
            2,
            '{
                "apiEndpoint": "https://api.compound.finance/api/v2",
                "subgraphUrl": "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v3",
                "rateLimit": 100,
                "rateLimitWindow": 60
            }'::jsonb
        ) ON CONFLICT (protocol_name) DO NOTHING;
    """)

    # Seed Morpho
    op.execute("""
        INSERT INTO money_market_protocols (
            protocol_name,
            display_name,
            description,
            supported_chains,
            contract_addresses,
            is_active,
            priority,
            api_config
        ) VALUES (
            'morpho',
            'Morpho',
            'Next-generation lending optimizer built on top of Aave and Compound with peer-to-peer matching for enhanced rates',
            ARRAY['ethereum', 'base'],
            '{
                "ethereum": {
                    "morphoAave": "0x777777c9898D384F785Ee44Acfe945efDFf5f3E0",
                    "morphoCompound": "0x8888882f8f843896699869179fB6E4f7e3B58888"
                },
                "base": {
                    "morphoBlue": "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
                }
            }'::jsonb,
            true,
            3,
            '{
                "apiEndpoint": "https://api.morpho.org/v1",
                "subgraphUrl": "https://api.thegraph.com/subgraphs/name/morpho-labs/morpho",
                "rateLimit": 100,
                "rateLimitWindow": 60
            }'::jsonb
        ) ON CONFLICT (protocol_name) DO NOTHING;
    """)


def downgrade() -> None:
    """Drop money market tables, views, and enums."""

    # Drop views
    op.execute("DROP VIEW IF EXISTS v_protocol_comparison_summary")
    op.execute("DROP VIEW IF EXISTS v_best_supply_rates")
    op.execute("DROP VIEW IF EXISTS v_latest_money_market_rates")

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("money_market_alert_history")
    # op.drop_table("money_market_comparison_assets")  # Table was never created (commented out in upgrade)
    op.drop_table("money_market_rate_alerts")
    op.drop_table("money_market_user_preferences")
    op.drop_table("money_market_comparisons")
    op.drop_table("money_market_rates")
    op.drop_table("money_market_protocols")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS money_market_notification_channel_enum")
    op.execute("DROP TYPE IF EXISTS money_market_alert_condition_enum")
    op.execute("DROP TYPE IF EXISTS money_market_comparison_type_enum")
    op.execute("DROP TYPE IF EXISTS money_market_data_source_enum")
    op.execute("DROP TYPE IF EXISTS money_market_protocol_enum")
