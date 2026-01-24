"""
SQLAlchemy mapping for user_context_aware table.

This table stores pre-computed user context data for context-aware
agent responses. Data is updated periodically by a Celery task.
"""

from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Integer,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
    Numeric,
)
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_user_context_aware_table() -> None:
    """Map user_context_aware table (idempotent)."""
    if "user_context_aware" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class UserContextAwareTable:
        __tablename__ = "user_context_aware"
        __table_args__ = (
            # Unique constraint: one context per chat user
            Index(
                "idx_user_context_unique_chat_user",
                "chat_user_id",
                unique=True,
            ),
            # Index for finding users eligible for update
            Index(
                "idx_user_context_next_update",
                "next_update_eligible_at",
                postgresql_where=sa.text("next_update_eligible_at <= CURRENT_TIMESTAMP"),
            ),
            # Index for filtering by portfolio state
            Index("idx_user_context_portfolio_state", "portfolio_state"),
            # Index for filtering by activity level
            Index("idx_user_context_activity_level", "activity_level"),
            # Index for filtering by user type
            Index("idx_user_context_user_type", "user_type"),
            # Index for legacy user lookup
            Index(
                "idx_user_context_legacy_user",
                "legacy_user_id",
                postgresql_where=sa.text("legacy_user_id IS NOT NULL"),
            ),
            # Index for last updated (for analytics)
            Index("idx_user_context_updated_at", "context_updated_at"),
            # Constraints
            CheckConstraint(
                "portfolio_state IN ('empty', 'starter', 'active', 'whale')",
                name="valid_portfolio_state",
            ),
            CheckConstraint(
                "activity_level IN ('very_active', 'active', 'weekly_active', 'monthly_active', 'inactive', 'reactivated', 'new')",
                name="valid_activity_level",
            ),
            CheckConstraint(
                "user_type IN ('new_user', 'casual', 'trader', 'yield_farmer', 'power_user')",
                name="valid_user_type",
            ),
            {"extend_existing": True},
        )

        # Primary key
        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )

        # Foreign key to chat_users (UUID-based)
        chat_user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
        )

        # Optional foreign key to legacy users table (INTEGER)
        legacy_user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        )

        # ═══════════════════════════════════════════════════════════════
        # PORTFOLIO STATE
        # ═══════════════════════════════════════════════════════════════
        portfolio_state = mapped_column(
            String(20),
            nullable=False,
            default="empty",
        )
        total_balance_usd = mapped_column(
            Numeric(18, 2),
            nullable=False,
            default=0.00,
        )
        token_count = mapped_column(Integer, nullable=False, default=0)
        primary_chain = mapped_column(String(50), nullable=True)

        # ═══════════════════════════════════════════════════════════════
        # ACTIVITY LEVEL
        # ═══════════════════════════════════════════════════════════════
        activity_level = mapped_column(
            String(20),
            nullable=False,
            default="new",
        )
        last_active_at = mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )
        first_active_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        chat_sessions_30d = mapped_column(Integer, nullable=False, default=0)
        messages_sent_30d = mapped_column(Integer, nullable=False, default=0)

        # ═══════════════════════════════════════════════════════════════
        # USER TYPE
        # ═══════════════════════════════════════════════════════════════
        user_type = mapped_column(
            String(30),
            nullable=False,
            default="new_user",
        )

        # ═══════════════════════════════════════════════════════════════
        # EXECUTION HISTORY
        # ═══════════════════════════════════════════════════════════════
        swap_count = mapped_column(Integer, nullable=False, default=0)
        buy_count = mapped_column(Integer, nullable=False, default=0)
        cashout_count = mapped_column(Integer, nullable=False, default=0)
        lending_count = mapped_column(Integer, nullable=False, default=0)
        money_market_count = mapped_column(Integer, nullable=False, default=0)
        transfer_count = mapped_column(Integer, nullable=False, default=0)
        total_executions = mapped_column(Integer, nullable=False, default=0)
        failed_executions = mapped_column(Integer, nullable=False, default=0)
        execution_success_rate = mapped_column(
            Numeric(5, 2),
            nullable=False,
            default=0.00,
        )

        # ═══════════════════════════════════════════════════════════════
        # CHAT INTERACTIONS
        # ═══════════════════════════════════════════════════════════════
        total_conversations = mapped_column(Integer, nullable=False, default=0)
        total_messages = mapped_column(Integer, nullable=False, default=0)
        shortcuts_used_count = mapped_column(Integer, nullable=False, default=0)
        multi_step_completed_count = mapped_column(Integer, nullable=False, default=0)
        avg_messages_per_session = mapped_column(
            Numeric(5, 2),
            nullable=False,
            default=0.00,
        )
        detected_language = mapped_column(String(5), nullable=False, default="en")
        language_history = mapped_column(JSONB, nullable=False, default=[])
        most_used_agents = mapped_column(JSONB, nullable=False, default=[])
        agent_usage_counts = mapped_column(JSONB, nullable=False, default={})

        # ═══════════════════════════════════════════════════════════════
        # WALLET DATA
        # ═══════════════════════════════════════════════════════════════
        wallet_count = mapped_column(Integer, nullable=False, default=0)
        has_connected_wallet = mapped_column(Boolean, nullable=False, default=False)
        primary_wallet_address = mapped_column(String(255), nullable=True)
        wallet_provider = mapped_column(String(50), nullable=True)
        
        # Wallet balance aggregation (for accurate portfolio_state)
        wallet_total_usd = mapped_column(
            Numeric(20, 2),
            nullable=False,
            default=0.00,
            comment="Total USD value across all user wallets",
        )
        wallet_chain_breakdown = mapped_column(
            JSONB,
            nullable=False,
            default={},
            comment="Balance breakdown by chain {chain: usd_value}",
        )
        wallet_last_sync_at = mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="Last time wallet balances were synced",
        )

        # ═══════════════════════════════════════════════════════════════
        # PROCESSING METADATA
        # ═══════════════════════════════════════════════════════════════
        context_updated_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        next_update_eligible_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        update_count = mapped_column(Integer, nullable=False, default=0)

        # Timestamps
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        updated_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
        )
