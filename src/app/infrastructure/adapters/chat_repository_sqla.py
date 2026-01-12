"""Chat Repository SQLAlchemy Adapter.

Implements the ChatRepository ports using SQLAlchemy with imperative mapping.
"""

import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import delete, func, select, update, and_
from sqlalchemy.exc import SQLAlchemyError

from app.domain.chat.entities import ChatUser, ChatConversation, ChatMessage
from app.domain.ports.chat_repository import (
    ChatUserRepository,
    ChatConversationRepository,
    ChatMessageRepository,
)
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.chat import map_chat_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class ChatUserRepositorySqla(ChatUserRepository):
    """SQLAlchemy implementation of ChatUserRepository."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_chat_tables()

    async def create(self, chat_user: ChatUser) -> ChatUser:
        """Create a new chat user."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                table.insert()
                .values(
                    id=chat_user.id_,
                    user_id=chat_user.user_id,
                    email=chat_user.email,
                    subscription_tier=chat_user.subscription_tier,
                    total_messages=chat_user.total_messages,
                    language=chat_user.language,
                    chat_preferences=chat_user.chat_preferences,
                    first_seen_at=chat_user.first_seen_at,
                    last_seen_at=chat_user.last_seen_at,
                    created_at=chat_user.created_at,
                    updated_at=chat_user.updated_at,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            chat_user.id_ = new_id
            await self._session.commit()
            return chat_user
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create chat user: {e}")
            raise DataMapperError("Failed to create chat user") from e

    async def get_by_id(self, chat_user_id: UUID) -> Optional[ChatUser]:
        """Get chat user by UUID."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(table.c.id == chat_user_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get chat user by ID: {e}")
            raise DataMapperError("Failed to get chat user") from e

    async def get_by_user_id(self, user_id: int) -> Optional[ChatUser]:
        """Get chat user by legacy user ID."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(table.c.user_id == user_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get chat user by user_id: {e}")
            raise DataMapperError("Failed to get chat user") from e

    async def get_by_email(self, email: str) -> Optional[ChatUser]:
        """Get chat user by email."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(table.c.email == email)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get chat user by email: {e}")
            raise DataMapperError("Failed to get chat user") from e

    async def update(self, chat_user: ChatUser) -> ChatUser:
        """Update existing chat user."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                update(table)
                .where(table.c.id == chat_user.id_)
                .values(
                    email=chat_user.email,
                    subscription_tier=chat_user.subscription_tier,
                    total_messages=chat_user.total_messages,
                    language=chat_user.language,
                    chat_preferences=chat_user.chat_preferences,
                    last_seen_at=chat_user.last_seen_at,
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return chat_user
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update chat user: {e}")
            raise DataMapperError("Failed to update chat user") from e

    async def delete(self, chat_user_id: UUID) -> None:
        """Delete chat user by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = delete(table).where(table.c.id == chat_user_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete chat user: {e}")
            raise DataMapperError("Failed to delete chat user") from e

    async def update_last_seen(self, chat_user_id: UUID) -> None:
        """Update last seen timestamp."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                update(table)
                .where(table.c.id == chat_user_id)
                .values(last_seen_at=datetime.utcnow(), updated_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update last seen: {e}")
            raise DataMapperError("Failed to update last seen") from e

    async def increment_message_count(self, chat_user_id: UUID) -> None:
        """Increment total message count."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                update(table)
                .where(table.c.id == chat_user_id)
                .values(
                    total_messages=table.c.total_messages + 1,
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to increment message count: {e}")
            raise DataMapperError("Failed to increment message count") from e

    @staticmethod
    def _row_to_entity(row) -> ChatUser:
        """Convert database row to ChatUser entity."""
        return ChatUser(
            id_=row["id"],
            user_id=row["user_id"],
            email=row["email"],
            subscription_tier=row["subscription_tier"],
            total_messages=row["total_messages"],
            language=row["language"],
            chat_preferences=row["chat_preferences"] or {},
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class ChatConversationRepositorySqla(ChatConversationRepository):
    """SQLAlchemy implementation of ChatConversationRepository."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_chat_tables()

    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Create a new conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                table.insert()
                .values(
                    id=conversation.id_,
                    chat_user_id=conversation.chat_user_id,
                    title=conversation.title,
                    status=conversation.status,
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
            conversation.id_ = new_id
            await self._session.commit()
            return conversation
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create conversation: {e}")
            raise DataMapperError("Failed to create conversation") from e

    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Get conversation by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = select(table).where(table.c.id == conversation_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation by ID: {e}")
            raise DataMapperError("Failed to get conversation") from e

    async def get_active_conversation(
        self, chat_user_id: UUID, language: str
    ) -> Optional[ChatConversation]:
        """Get the most recent active conversation for a user in a language."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                select(table)
                .where(
                    and_(
                        table.c.chat_user_id == chat_user_id,
                        table.c.status == "active",
                        table.c.language == language,
                    )
                )
                .order_by(table.c.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get active conversation: {e}")
            raise DataMapperError("Failed to get active conversation") from e

    async def list_by_user(
        self,
        chat_user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatConversation]:
        """List conversations for a user."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = select(table).where(table.c.chat_user_id == chat_user_id)

            if status:
                stmt = stmt.where(table.c.status == status)

            stmt = stmt.order_by(table.c.updated_at.desc()).limit(limit).offset(offset)

            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_entity(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list conversations: {e}")
            raise DataMapperError("Failed to list conversations") from e

    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Update existing conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation.id_)
                .values(
                    title=conversation.title,
                    status=conversation.status,
                    message_count=conversation.message_count,
                    language=conversation.language,
                    archived_at=conversation.archived_at,
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return conversation
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update conversation: {e}")
            raise DataMapperError("Failed to update conversation") from e

    async def delete(self, conversation_id: UUID) -> None:
        """Delete conversation by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = delete(table).where(table.c.id == conversation_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete conversation: {e}")
            raise DataMapperError("Failed to delete conversation") from e

    async def archive(self, conversation_id: UUID) -> None:
        """Archive a conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation_id)
                .values(
                    status="archived",
                    archived_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to archive conversation: {e}")
            raise DataMapperError("Failed to archive conversation") from e

    async def unarchive(self, conversation_id: UUID) -> None:
        """Restore an archived conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation_id)
                .values(
                    status="active", archived_at=None, updated_at=datetime.utcnow()
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to unarchive conversation: {e}")
            raise DataMapperError("Failed to unarchive conversation") from e

    async def increment_message_count(self, conversation_id: UUID) -> None:
        """Increment message count."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation_id)
                .values(
                    message_count=table.c.message_count + 1,
                    updated_at=datetime.utcnow(),
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to increment message count: {e}")
            raise DataMapperError("Failed to increment message count") from e

    @staticmethod
    def _row_to_entity(row) -> ChatConversation:
        """Convert database row to ChatConversation entity."""
        return ChatConversation(
            id_=row["id"],
            chat_user_id=row["chat_user_id"],
            title=row["title"],
            status=row["status"],
            message_count=row["message_count"],
            language=row["language"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            archived_at=row["archived_at"],
        )


class ChatMessageRepositorySqla(ChatMessageRepository):
    """SQLAlchemy implementation of ChatMessageRepository."""

    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_chat_tables()

    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = (
                table.insert()
                .values(
                    id=message.id_,
                    conversation_id=message.conversation_id,
                    role=message.role,
                    content=message.content,
                    intent=message.intent,
                    handler=message.handler,
                    confidence=message.confidence,
                    language=message.language,
                    is_restricted_action=message.is_restricted_action,
                    # Note: column is 'metadata' but SQLAlchemy uses 'extra_metadata' attribute
                    metadata=message.metadata,
                    created_at=message.created_at,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            message.id_ = new_id
            await self._session.commit()
            return message
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to create message: {e}")
            raise DataMapperError("Failed to create message") from e

    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get message by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = select(table).where(table.c.id == message_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get message by ID: {e}")
            raise DataMapperError("Failed to get message") from e

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """List messages in a conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = (
                select(table)
                .where(table.c.conversation_id == conversation_id)
                .order_by(table.c.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_entity(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list messages: {e}")
            raise DataMapperError("Failed to list messages") from e

    async def list_by_conversation_since(
        self,
        conversation_id: UUID,
        since: datetime,
    ) -> List[ChatMessage]:
        """List messages in a conversation since a timestamp."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = (
                select(table)
                .where(
                    and_(
                        table.c.conversation_id == conversation_id,
                        table.c.created_at > since,
                    )
                )
                .order_by(table.c.created_at.asc())
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_entity(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list messages since: {e}")
            raise DataMapperError("Failed to list messages") from e

    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = select(func.count(table.c.id)).where(
                table.c.conversation_id == conversation_id
            )
            result = await self._session.execute(stmt)
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Failed to count messages: {e}")
            raise DataMapperError("Failed to count messages") from e

    async def delete(self, message_id: UUID) -> None:
        """Delete message by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = delete(table).where(table.c.id == message_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete message: {e}")
            raise DataMapperError("Failed to delete message") from e

    async def delete_by_conversation(self, conversation_id: UUID) -> None:
        """Delete all messages in a conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = delete(table).where(table.c.conversation_id == conversation_id)
            await self._session.execute(stmt)
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete messages by conversation: {e}")
            raise DataMapperError("Failed to delete messages") from e

    async def get_latest_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[ChatMessage]:
        """Get the most recent message in a conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = (
                select(table)
                .where(table.c.conversation_id == conversation_id)
                .order_by(table.c.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_entity(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get latest message: {e}")
            raise DataMapperError("Failed to get latest message") from e

    async def search_by_intent(
        self,
        chat_user_id: UUID,
        intent: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Search messages by Hunter AI intent."""
        try:
            messages_table = mapping_registry.metadata.tables["chat_messages"]
            conversations_table = mapping_registry.metadata.tables["chat_conversations"]

            stmt = (
                select(messages_table)
                .join(
                    conversations_table,
                    messages_table.c.conversation_id == conversations_table.c.id,
                )
                .where(
                    and_(
                        conversations_table.c.chat_user_id == chat_user_id,
                        messages_table.c.intent == intent,
                    )
                )
                .order_by(messages_table.c.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_entity(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to search messages by intent: {e}")
            raise DataMapperError("Failed to search messages") from e

    @staticmethod
    def _row_to_entity(row) -> ChatMessage:
        """Convert database row to ChatMessage entity."""
        return ChatMessage(
            id_=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            intent=row["intent"],
            handler=row["handler"],
            confidence=row["confidence"],
            language=row["language"],
            is_restricted_action=row["is_restricted_action"],
            metadata=row["metadata"] if "metadata" in row else row.get("extra_metadata", {}),
            created_at=row["created_at"],
        )
