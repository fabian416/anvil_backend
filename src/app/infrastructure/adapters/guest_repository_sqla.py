"""
Guest Repository SQLAlchemy Adapter.

Implements the GuestRepository port using SQLAlchemy.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.domain.guest.entities.guest_conversation import (
    GuestConversation,
    GuestConversationStatus,
)
from app.domain.guest.entities.guest_message import GuestMessage, GuestMessageRole
from app.domain.guest.entities.guest_user import GuestUser
from app.domain.guest.ports.guest_repository import GuestRepository
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.guest import map_guest_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class GuestRepositorySqla(GuestRepository):
    """SQLAlchemy implementation of GuestRepository."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_guest_tables()

    # ========================================
    # Guest User Operations
    # ========================================

    async def get_guest_by_ip(self, ip_address: str) -> GuestUser | None:
        """Get guest user by IP address."""
        try:
            table = mapping_registry.metadata.tables["guest_users"]
            stmt = select(table).where(table.c.ip_address == ip_address)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_guest_user(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get guest by IP: {e}")
            raise DataMapperError("Failed to get guest user") from e

    async def get_guest_by_id(self, guest_id: UUID) -> GuestUser | None:
        """Get guest user by ID."""
        try:
            table = mapping_registry.metadata.tables["guest_users"]
            stmt = select(table).where(table.c.id == guest_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_guest_user(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get guest by ID: {e}")
            raise DataMapperError("Failed to get guest user") from e

    async def create_guest(self, guest: GuestUser) -> GuestUser:
        """Create a new guest user."""
        try:
            table = mapping_registry.metadata.tables["guest_users"]
            stmt = (
                table.insert()
                .values(
                    id=guest.id,
                    ip_address=guest.ip_address,
                    fingerprint=guest.fingerprint,
                    first_seen_at=guest.first_seen_at,
                    last_seen_at=guest.last_seen_at,
                    total_messages=guest.total_messages,
                    language=guest.language,
                    country_code=guest.country_code,
                    is_blocked=guest.is_blocked,
                    created_at=guest.created_at,
                    updated_at=guest.updated_at,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            guest.id = new_id
            await self._session.commit()
            return guest
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create guest: {e}")
            raise DataMapperError("Failed to create guest user") from e

    async def update_guest(self, guest: GuestUser) -> GuestUser:
        """Update an existing guest user."""
        try:
            table = mapping_registry.metadata.tables["guest_users"]
            stmt = (
                update(table)
                .where(table.c.id == guest.id)
                .values(
                    last_seen_at=guest.last_seen_at,
                    total_messages=guest.total_messages,
                    language=guest.language,
                    is_blocked=guest.is_blocked,
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return guest
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update guest: {e}")
            raise DataMapperError("Failed to update guest user") from e

    # ========================================
    # Guest Conversation Operations
    # ========================================

    async def get_active_conversation(
        self, guest_user_id: UUID
    ) -> GuestConversation | None:
        """Get the active conversation for a guest user."""
        try:
            table = mapping_registry.metadata.tables["guest_conversations"]
            stmt = (
                select(table)
                .where(table.c.guest_user_id == guest_user_id)
                .where(table.c.status == "active")
                .order_by(table.c.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_conversation(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get active conversation: {e}")
            raise DataMapperError("Failed to get conversation") from e

    async def get_conversation_by_id(
        self, conversation_id: UUID
    ) -> GuestConversation | None:
        """Get conversation by ID."""
        try:
            table = mapping_registry.metadata.tables["guest_conversations"]
            stmt = select(table).where(table.c.id == conversation_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_conversation(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation: {e}")
            raise DataMapperError("Failed to get conversation") from e

    async def create_conversation(
        self, conversation: GuestConversation
    ) -> GuestConversation:
        """Create a new conversation."""
        try:
            table = mapping_registry.metadata.tables["guest_conversations"]
            stmt = (
                table.insert()
                .values(
                    id=conversation.id,
                    guest_user_id=conversation.guest_user_id,
                    title=conversation.title,
                    status=conversation.status.value,
                    message_count=conversation.message_count,
                    language=conversation.language,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    archived_at=conversation.archived_at,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            conversation.id = new_id
            await self._session.commit()
            return conversation
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise DataMapperError("Failed to create conversation") from e

    async def update_conversation(
        self, conversation: GuestConversation
    ) -> GuestConversation:
        """Update an existing conversation."""
        try:
            table = mapping_registry.metadata.tables["guest_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation.id)
                .values(
                    title=conversation.title,
                    status=conversation.status.value,
                    message_count=conversation.message_count,
                    updated_at=datetime.utcnow(),
                    archived_at=conversation.archived_at,
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return conversation
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update conversation: {e}")
            raise DataMapperError("Failed to update conversation") from e

    async def archive_inactive_conversations(self, older_than: datetime) -> int:
        """Archive conversations older than specified time."""
        try:
            table = mapping_registry.metadata.tables["guest_conversations"]
            stmt = (
                update(table)
                .where(table.c.status == "active")
                .where(table.c.updated_at < older_than)
                .values(
                    status="archived",
                    archived_at=datetime.utcnow(),
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to archive conversations: {e}")
            raise DataMapperError("Failed to archive conversations") from e

    async def delete_conversation_for_guest(
        self, guest_user_id: UUID
    ) -> bool:
        """
        Delete (archive) the active conversation for a guest user and clear all messages.
        Returns True if successful, False if no active conversation found.
        """
        try:
            conv_table = mapping_registry.metadata.tables["guest_conversations"]
            msg_table = mapping_registry.metadata.tables["guest_messages"]

            # Find the active conversation
            conv_stmt = (
                select(conv_table.c.id)
                .where(conv_table.c.guest_user_id == guest_user_id)
                .where(conv_table.c.status == "active")
            )
            conv_result = await self._session.execute(conv_stmt)
            conv_row = conv_result.first()

            if not conv_row:
                return False

            conversation_id = conv_row[0]

            # Delete all messages for this conversation
            delete_msgs_stmt = delete(msg_table).where(
                msg_table.c.conversation_id == conversation_id
            )
            await self._session.execute(delete_msgs_stmt)

            # Archive the conversation (soft delete)
            archive_conv_stmt = (
                update(conv_table)
                .where(conv_table.c.id == conversation_id)
                .values(
                    status="archived",
                    message_count=0,
                    archived_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(archive_conv_stmt)
            await self._session.commit()

            logger.info(f"Deleted conversation {conversation_id} for guest {guest_user_id}")
            return True

        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete conversation for guest: {e}")
            raise DataMapperError("Failed to delete conversation") from e

    # ========================================
    # Guest Message Operations
    # ========================================

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GuestMessage]:
        """Get messages for a conversation."""
        try:
            table = mapping_registry.metadata.tables["guest_messages"]
            stmt = (
                select(table)
                .where(table.c.conversation_id == conversation_id)
                .order_by(table.c.created_at.desc())  # Changed to DESC to get most recent first
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_message(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get messages: {e}")
            raise DataMapperError("Failed to get messages") from e

    async def create_message(self, message: GuestMessage) -> GuestMessage:
        """Create a new message."""
        try:
            table = mapping_registry.metadata.tables["guest_messages"]
            stmt = (
                table.insert()
                .values(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role.value,
                    content=message.content,
                    intent=message.intent,
                    handler=message.handler,
                    confidence=message.confidence,
                    language=message.language,
                    is_restricted_action=message.is_restricted_action,
                    metadata=message.metadata or {},
                    created_at=message.created_at,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            message.id = new_id
            await self._session.commit()
            return message
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create message: {e}")
            raise DataMapperError("Failed to create message") from e

    async def get_message_count(self, conversation_id: UUID) -> int:
        """Get message count for a conversation."""
        try:
            table = mapping_registry.metadata.tables["guest_messages"]
            stmt = select(func.count(table.c.id)).where(
                table.c.conversation_id == conversation_id
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get message count: {e}")
            return 0

    # ========================================
    # Telemetry Operations
    # ========================================

    async def log_telemetry(
        self,
        guest_user_id: UUID,
        event_type: str,
        ip_address: str,
        conversation_id: UUID | None = None,
        event_data: dict | None = None,
        user_agent: str | None = None,
        referer: str | None = None,
        language: str = "en",
    ) -> None:
        """Log a telemetry event."""
        try:
            table = mapping_registry.metadata.tables["guest_telemetry"]
            stmt = table.insert().values(
                guest_user_id=guest_user_id,
                conversation_id=conversation_id,
                event_type=event_type,
                event_data=event_data,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                language=language,
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.warning(f"Failed to log telemetry: {e}")

    # ========================================
    # Rate Limiting
    # ========================================

    async def get_message_count_since(
        self,
        guest_user_id: UUID,
        since: datetime,
    ) -> int:
        """Get message count since a timestamp."""
        try:
            conv_table = mapping_registry.metadata.tables["guest_conversations"]
            msg_table = mapping_registry.metadata.tables["guest_messages"]

            # Get all conversation IDs for this guest
            conv_stmt = select(conv_table.c.id).where(
                conv_table.c.guest_user_id == guest_user_id
            )
            conv_result = await self._session.execute(conv_stmt)
            conv_ids = [row[0] for row in conv_result.fetchall()]

            if not conv_ids:
                return 0

            # Count messages in those conversations since timestamp
            msg_stmt = (
                select(func.count(msg_table.c.id))
                .where(msg_table.c.conversation_id.in_(conv_ids))
                .where(msg_table.c.role == "user")
                .where(msg_table.c.created_at >= since)
            )
            result = await self._session.execute(msg_stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get message count since: {e}")
            return 0

    # ========================================
    # Row Mappers
    # ========================================

    @staticmethod
    def _row_to_guest_user(row: dict) -> GuestUser:
        """Convert DB row to GuestUser entity."""
        return GuestUser(
            id=row["id"],
            ip_address=row["ip_address"],
            fingerprint=row.get("fingerprint"),
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            total_messages=row.get("total_messages", 0),
            language=row.get("language", "en"),
            country_code=row.get("country_code"),
            is_blocked=row.get("is_blocked", False),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _row_to_conversation(row: dict) -> GuestConversation:
        """Convert DB row to GuestConversation entity."""
        return GuestConversation(
            id=row["id"],
            guest_user_id=row["guest_user_id"],
            title=row.get("title"),
            status=GuestConversationStatus(row.get("status", "active")),
            message_count=row.get("message_count", 0),
            language=row.get("language", "en"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            archived_at=row.get("archived_at"),
        )

    @staticmethod
    def _row_to_message(row: dict) -> GuestMessage:
        """Convert DB row to GuestMessage entity."""
        return GuestMessage(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=GuestMessageRole(row["role"]),
            content=row["content"],
            intent=row.get("intent"),
            handler=row.get("handler"),
            confidence=row.get("confidence"),
            language=row.get("language", "en"),
            is_restricted_action=row.get("is_restricted_action", False),
            metadata=row.get("metadata", {}),
            created_at=row["created_at"],
        )
