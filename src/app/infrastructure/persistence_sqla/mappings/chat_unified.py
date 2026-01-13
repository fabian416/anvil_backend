"""
SQLAlchemy mappings for Unified Chat tables.

Tables:
- chat_users: Unified user table for guest and authenticated users
- chat_conversations: Conversations with full CRUD support
- chat_messages: Messages with enhanced metadata
- chat_rate_limits: Rate limiting tracking
"""

from sqlalchemy import String, DateTime, Boolean, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_unified_chat_tables() -> None:
    """Map all unified chat tables (idempotent)."""
    _map_chat_users_table()
    _map_chat_conversations_table()
    _map_chat_messages_table()
    _map_chat_rate_limits_table()


def _map_chat_users_table() -> None:
    """Map chat_users table."""
    if "chat_users" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatUsersTable:
        __tablename__ = "chat_users"
        __table_args__ = (
            sa.Index("idx_chat_users_identifier", "user_type", "identifier", unique=True),
            sa.Index("idx_chat_users_privy_id", "privy_id", unique=True, postgresql_where=sa.text("privy_id IS NOT NULL")),
            {"extend_existing": True}
        )
        
        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            default=uuid.uuid4
        )
        user_type = mapped_column(String(20), nullable=False, index=True)  # guest | authenticated | premium
        identifier = mapped_column(String(255), nullable=False)  # IP for guest, privy_id for authenticated
        privy_id = mapped_column(String(255), nullable=True)
        email = mapped_column(String(255), nullable=True)
        preferred_language = mapped_column(String(5), default="en")
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        last_active_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        is_blocked = mapped_column(Boolean, default=False)
        extra_metadata = mapped_column("metadata", JSONB, default={})


def _map_chat_conversations_table() -> None:
    """Map chat_conversations table."""
    if "chat_conversations" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatConversationsTable:
        __tablename__ = "chat_conversations"
        __table_args__ = (
            sa.Index("idx_chat_conversations_user_status", "user_id", "status"),
            {"extend_existing": True}
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            default=uuid.uuid4
        )
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        title = mapped_column(String(255), nullable=True)
        status = mapped_column(String(20), default="active", index=True)  # active | archived | deleted
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        updated_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        last_message_at = mapped_column(DateTime(timezone=True), nullable=True)
        message_count = mapped_column(Integer, server_default=sa.text('0'), default=0)
        language = mapped_column(String(5), default="en")
        extra_metadata = mapped_column("metadata", JSONB, default={})


def _map_chat_messages_table() -> None:
    """Map chat_messages table."""
    if "chat_messages" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatMessagesTable:
        __tablename__ = "chat_messages"
        __table_args__ = (
            sa.Index("idx_chat_messages_conversation", "conversation_id", "created_at"),
            {"extend_existing": True}
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            default=uuid.uuid4
        )
        conversation_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        role = mapped_column(String(20), nullable=False)  # user | assistant | system
        content = mapped_column(Text, nullable=False)
        intent = mapped_column(String(50), nullable=True)
        intent_confidence = mapped_column(Float, nullable=True)
        handler = mapped_column(String(100), nullable=True)
        is_restricted_action = mapped_column(Boolean, default=False)
        language = mapped_column(String(5), default="en")
        created_at = mapped_column(DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'))
        extra_metadata = mapped_column("metadata", JSONB, default={})  # tokens, entities, enrichment data


def _map_chat_rate_limits_table() -> None:
    """Map chat_rate_limits table."""
    if "chat_rate_limits" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatRateLimitsTable:
        __tablename__ = "chat_rate_limits"
        __table_args__ = (
            sa.UniqueConstraint("user_id", "window_type", "window_start", name="uq_rate_limits_user_window"),
            {"extend_existing": True}
        )

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
            default=uuid.uuid4
        )
        user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        window_type = mapped_column(String(20), nullable=False)  # hourly | daily
        window_start = mapped_column(DateTime(timezone=True), nullable=False)
        message_count = mapped_column(Integer, default=0)

