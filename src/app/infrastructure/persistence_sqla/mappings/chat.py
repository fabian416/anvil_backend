"""SQLAlchemy mappings for authenticated chat tables.

Tables:
- chat_users: Authenticated chat users (bridge to legacy users table)
- chat_conversations: Authenticated user conversations
- chat_messages: Messages in authenticated conversations
"""

from sqlalchemy import String, DateTime, Boolean, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_chat_tables() -> None:
    """Map all authenticated chat tables (idempotent)."""
    _map_chat_users_table()
    _map_chat_conversations_table()
    _map_chat_messages_table()


def _map_chat_users_table() -> None:
    """Map chat_users table."""
    if "chat_users" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatUsersTable:
        __tablename__ = "chat_users"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        user_id = mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
        email = mapped_column(String(255), nullable=False, index=True)
        subscription_tier = mapped_column(String(20), default="free", index=True)
        total_messages = mapped_column(Integer, default=0)
        language = mapped_column(String(5), default="en")
        chat_preferences = mapped_column(JSONB, default={}, server_default="{}")
        first_seen_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        last_seen_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )
        created_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        updated_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )


def _map_chat_conversations_table() -> None:
    """Map chat_conversations table."""
    if "chat_conversations" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatConversationsTable:
        __tablename__ = "chat_conversations"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        chat_user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        title = mapped_column(String(255), nullable=True)
        status = mapped_column(String(20), default="active", index=True)
        message_count = mapped_column(Integer, default=0)
        language = mapped_column(String(5), default="en")
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )
        updated_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        archived_at = mapped_column(DateTime(timezone=True), nullable=True)


def _map_chat_messages_table() -> None:
    """Map chat_messages table."""
    if "chat_messages" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class ChatMessagesTable:
        __tablename__ = "chat_messages"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            default=uuid.uuid4,
        )
        conversation_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("chat_conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        role = mapped_column(String(20), nullable=False)
        content = mapped_column(Text, nullable=False)
        intent = mapped_column(String(50), nullable=True, index=True)
        handler = mapped_column(String(50), nullable=True)
        confidence = mapped_column(Float, nullable=True)
        language = mapped_column(String(5), default="en")
        is_restricted_action = mapped_column(Boolean, default=False)
        # Note: 'metadata' is reserved in SQLAlchemy, so we use 'extra_metadata' as attribute name
        # but map it to 'metadata' column in the database
        extra_metadata = mapped_column(
            "metadata", JSONB, default={}, server_default="{}"
        )
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )
