"""
SQLAlchemy mappings for Guest tables.

Tables:
- guest_users: Track guest users by IP
- guest_conversations: Guest chat conversations
- guest_messages: Messages in guest conversations
- guest_telemetry: Analytics for guest interactions
"""

from sqlalchemy import String, DateTime, Boolean, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
import sqlalchemy as sa
import uuid

from app.infrastructure.persistence_sqla.registry import mapping_registry


def map_guest_tables() -> None:
    """Map all guest tables (idempotent)."""
    _map_guest_users_table()
    _map_guest_conversations_table()
    _map_guest_messages_table()
    _map_guest_telemetry_table()


def _map_guest_users_table() -> None:
    """Map guest_users table."""
    if "guest_users" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class GuestUsersTable:
        __tablename__ = "guest_users"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        ip_address = mapped_column(String(45), nullable=False, unique=True, index=True)
        fingerprint = mapped_column(String(255), nullable=True)
        first_seen_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        last_seen_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        total_messages = mapped_column(Integer, default=0)
        language = mapped_column(String(5), default="en")
        country_code = mapped_column(String(2), nullable=True)
        is_blocked = mapped_column(Boolean, default=False)
        created_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        updated_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )


def _map_guest_conversations_table() -> None:
    """Map guest_conversations table."""
    if "guest_conversations" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class GuestConversationsTable:
        __tablename__ = "guest_conversations"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        guest_user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("guest_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        title = mapped_column(String(255), nullable=True)
        status = mapped_column(String(20), default="active", index=True)
        message_count = mapped_column(Integer, default=0)
        language = mapped_column(String(5), default="en")
        created_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        updated_at = mapped_column(
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )
        archived_at = mapped_column(DateTime(timezone=True), nullable=True)


def _map_guest_messages_table() -> None:
    """Map guest_messages table."""
    if "guest_messages" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class GuestMessagesTable:
        __tablename__ = "guest_messages"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        conversation_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("guest_conversations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        role = mapped_column(String(20), nullable=False)
        content = mapped_column(Text, nullable=False)
        intent = mapped_column(String(50), nullable=True)
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
            DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        )


def _map_guest_telemetry_table() -> None:
    """Map guest_telemetry table."""
    if "guest_telemetry" in mapping_registry.metadata.tables:
        return

    @mapping_registry.mapped
    class GuestTelemetryTable:
        __tablename__ = "guest_telemetry"
        __table_args__ = {"extend_existing": True}

        id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        guest_user_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("guest_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
        conversation_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey("guest_conversations.id", ondelete="SET NULL"),
            nullable=True,
        )
        event_type = mapped_column(String(50), nullable=False, index=True)
        event_data = mapped_column(JSONB, nullable=True)
        ip_address = mapped_column(String(45), nullable=False)
        user_agent = mapped_column(Text, nullable=True)
        referer = mapped_column(Text, nullable=True)
        language = mapped_column(String(5), default="en")
        created_at = mapped_column(
            DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        )
