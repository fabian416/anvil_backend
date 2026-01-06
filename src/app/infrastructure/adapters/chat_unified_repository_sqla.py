"""
Unified Chat Repository SQLAlchemy Adapter.

Implements repositories for the unified chat system:
- ChatUserRepository
- ChatConversationRepository  
- ChatMessageRepository
- RateLimitRepository
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update, delete
from sqlalchemy.exc import SQLAlchemyError

from app.domain.chat.entities.chat_user import ChatUser, UserType
from app.domain.chat.entities.chat_conversation import ChatConversation, ConversationStatus
from app.domain.chat.entities.chat_message import ChatMessage, MessageRole
from app.domain.chat.entities.rate_limit import RateLimit, WindowType
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.exceptions.gateway import DataMapperError
from app.infrastructure.persistence_sqla.mappings.chat_unified import map_unified_chat_tables
from app.infrastructure.persistence_sqla.registry import mapping_registry

logger = logging.getLogger(__name__)


class ChatUserRepositorySqla:
    """SQLAlchemy implementation of ChatUserRepository."""
    
    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_unified_chat_tables()
    
    async def get_by_id(self, user_id: UUID) -> ChatUser | None:
        """Get user by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(table.c.id == user_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user by ID: {e}")
            raise DataMapperError("Failed to get user") from e
    
    async def get_by_privy_id(self, privy_id: str) -> ChatUser | None:
        """Get user by Privy ID."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(table.c.privy_id == privy_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user by Privy ID: {e}")
            raise DataMapperError("Failed to get user") from e
    
    async def get_by_identifier(self, user_type: str, identifier: str) -> ChatUser | None:
        """Get user by type and identifier."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = select(table).where(
                (table.c.user_type == user_type) &
                (table.c.identifier == identifier)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_user(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get user by identifier: {e}")
            raise DataMapperError("Failed to get user") from e
    
    async def save(self, user: ChatUser) -> ChatUser:
        """Save a new user."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                table.insert()
                .values(
                    id=user.id,
                    user_type=user.user_type.value,
                    identifier=user.identifier,
                    privy_id=user.privy_id,
                    email=user.email,
                    preferred_language=user.preferred_language,
                    created_at=user.created_at,
                    last_active_at=user.last_active_at,
                    is_blocked=user.is_blocked,
                    metadata=user.metadata,
                )
                .returning(table.c.id)
            )
            result = await self._session.execute(stmt)
            new_id = result.scalar_one()
            user.id = new_id
            await self._session.commit()
            return user
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to save user: {e}")
            raise DataMapperError("Failed to save user") from e
    
    async def update(self, user: ChatUser) -> ChatUser:
        """Update an existing user."""
        try:
            table = mapping_registry.metadata.tables["chat_users"]
            stmt = (
                update(table)
                .where(table.c.id == user.id)
                .values(
                    user_type=user.user_type.value,
                    identifier=user.identifier,
                    privy_id=user.privy_id,
                    email=user.email,
                    preferred_language=user.preferred_language,
                    last_active_at=user.last_active_at,
                    is_blocked=user.is_blocked,
                    metadata=user.metadata,
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return user
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise DataMapperError("Failed to update user") from e
    
    @staticmethod
    def _row_to_user(row: dict) -> ChatUser:
        """Convert DB row to ChatUser entity."""
        return ChatUser(
            id=row["id"],
            user_type=UserType(row["user_type"]),
            identifier=row["identifier"],
            privy_id=row.get("privy_id"),
            email=row.get("email"),
            preferred_language=row.get("preferred_language", "en"),
            created_at=row["created_at"],
            last_active_at=row["last_active_at"],
            is_blocked=row.get("is_blocked", False),
            metadata=row.get("metadata", {}),
        )


class ChatConversationRepositorySqla:
    """SQLAlchemy implementation of ChatConversationRepository."""
    
    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_unified_chat_tables()
    
    async def get_by_id(self, conversation_id: UUID) -> ChatConversation | None:
        """Get conversation by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = select(table).where(table.c.id == conversation_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_conversation(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation: {e}")
            raise DataMapperError("Failed to get conversation") from e
    
    async def get_by_id_and_user(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> ChatConversation | None:
        """Get conversation by ID and user (for ownership check)."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = select(table).where(
                (table.c.id == conversation_id) &
                (table.c.user_id == user_id)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_conversation(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get conversation: {e}")
            raise DataMapperError("Failed to get conversation") from e
    
    async def get_active_for_user(self, user_id: UUID) -> ChatConversation | None:
        """Get active conversation for user (most recent)."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                select(table)
                .where(table.c.user_id == user_id)
                .where(table.c.status == "active")
                .order_by(table.c.updated_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_conversation(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get active conversation: {e}")
            raise DataMapperError("Failed to get conversation") from e
    
    async def list_for_user(
        self,
        user_id: UUID,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[ChatConversation]:
        """List conversations for user."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                select(table)
                .where(table.c.user_id == user_id)
                .where(table.c.status == status)
                .order_by(table.c.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            return [self._row_to_conversation(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list conversations: {e}")
            raise DataMapperError("Failed to list conversations") from e
    
    async def count_for_user(self, user_id: UUID, status: str = "active") -> int:
        """Count conversations for user."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                select(func.count(table.c.id))
                .where(table.c.user_id == user_id)
                .where(table.c.status == status)
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to count conversations: {e}")
            return 0
    
    async def save(self, conversation: ChatConversation) -> ChatConversation:
        """Save a new conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                table.insert()
                .values(
                    id=conversation.id,
                    user_id=conversation.user_id,
                    title=conversation.title,
                    status=conversation.status.value,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    last_message_at=conversation.last_message_at,
                    message_count=conversation.message_count,
                    language=conversation.language,
                    metadata=conversation.metadata,
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
            logger.error(f"Failed to save conversation: {e}")
            raise DataMapperError("Failed to save conversation") from e
    
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Update an existing conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation.id)
                .values(
                    title=conversation.title,
                    status=conversation.status.value,
                    updated_at=datetime.utcnow(),
                    last_message_at=conversation.last_message_at,
                    message_count=conversation.message_count,
                    language=conversation.language,
                    metadata=conversation.metadata,
                )
            )
            await self._session.execute(stmt)
            await self._session.commit()
            return conversation
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to update conversation: {e}")
            raise DataMapperError("Failed to update conversation") from e
    
    async def delete_for_user(self, conversation_id: UUID, user_id: UUID) -> bool:
        """Soft delete conversation (mark as deleted)."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.id == conversation_id)
                .where(table.c.user_id == user_id)
                .values(
                    status="deleted",
                    updated_at=datetime.utcnow(),
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to delete conversation: {e}")
            raise DataMapperError("Failed to delete conversation") from e
    
    async def archive_inactive(self, older_than: datetime) -> int:
        """Archive inactive conversations."""
        try:
            table = mapping_registry.metadata.tables["chat_conversations"]
            stmt = (
                update(table)
                .where(table.c.status == "active")
                .where(table.c.updated_at < older_than)
                .values(
                    status="archived",
                    updated_at=datetime.utcnow(),
                )
            )
            result = await self._session.execute(stmt)
            await self._session.commit()
            return result.rowcount
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to archive conversations: {e}")
            raise DataMapperError("Failed to archive conversations") from e
    
    @staticmethod
    def _row_to_conversation(row: dict) -> ChatConversation:
        """Convert DB row to ChatConversation entity."""
        return ChatConversation(
            id=row["id"],
            user_id=row["user_id"],
            title=row.get("title"),
            status=ConversationStatus(row.get("status", "active")),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            last_message_at=row.get("last_message_at"),
            message_count=row.get("message_count", 0),
            language=row.get("language", "en"),
            metadata=row.get("metadata", {}),
        )


class ChatMessageRepositorySqla:
    """SQLAlchemy implementation of ChatMessageRepository."""
    
    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_unified_chat_tables()
    
    async def get_by_id(self, message_id: UUID) -> ChatMessage | None:
        """Get message by ID."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = select(table).where(table.c.id == message_id)
            result = await self._session.execute(stmt)
            row = result.mappings().first()
            return self._row_to_message(row) if row else None
        except SQLAlchemyError as e:
            logger.error(f"Failed to get message: {e}")
            raise DataMapperError("Failed to get message") from e
    
    async def get_recent_messages(
        self,
        conversation_id: UUID,
        limit: int = 10,
    ) -> list[ChatMessage]:
        """Get recent messages from conversation (oldest first)."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            # Get most recent N, then reverse for chronological order
            stmt = (
                select(table)
                .where(table.c.conversation_id == conversation_id)
                .order_by(table.c.created_at.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            rows = result.mappings().all()
            messages = [self._row_to_message(row) for row in rows]
            return list(reversed(messages))  # Chronological order
        except SQLAlchemyError as e:
            logger.error(f"Failed to get messages: {e}")
            raise DataMapperError("Failed to get messages") from e
    
    async def list_for_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ChatMessage]:
        """List all messages for conversation."""
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
            return [self._row_to_message(row) for row in rows]
        except SQLAlchemyError as e:
            logger.error(f"Failed to list messages: {e}")
            raise DataMapperError("Failed to list messages") from e
    
    async def save(self, message: ChatMessage) -> ChatMessage:
        """Save a new message."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = (
                table.insert()
                .values(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    role=message.role.value,
                    content=message.content,
                    intent=message.intent,
                    intent_confidence=message.intent_confidence,
                    handler=message.handler,
                    is_restricted_action=message.is_restricted_action,
                    language=message.language,
                    created_at=message.created_at,
                    metadata=message.metadata,
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
            logger.error(f"Failed to save message: {e}")
            raise DataMapperError("Failed to save message") from e
    
    async def count_for_conversation(self, conversation_id: UUID) -> int:
        """Count messages in conversation."""
        try:
            table = mapping_registry.metadata.tables["chat_messages"]
            stmt = select(func.count(table.c.id)).where(
                table.c.conversation_id == conversation_id
            )
            result = await self._session.execute(stmt)
            return result.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to count messages: {e}")
            return 0
    
    @staticmethod
    def _row_to_message(row: dict) -> ChatMessage:
        """Convert DB row to ChatMessage entity."""
        return ChatMessage(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=MessageRole(row["role"]),
            content=row["content"],
            intent=row.get("intent"),
            intent_confidence=row.get("intent_confidence"),
            handler=row.get("handler"),
            is_restricted_action=row.get("is_restricted_action", False),
            language=row.get("language", "en"),
            created_at=row["created_at"],
            metadata=row.get("metadata", {}),
        )


class RateLimitRepositorySqla:
    """SQLAlchemy implementation of RateLimitRepository."""
    
    def __init__(self, session: MainAsyncSession):
        self._session = session
        map_unified_chat_tables()
    
    async def get_hourly_count(self, user_id: UUID) -> int:
        """Get message count for current hour."""
        try:
            table = mapping_registry.metadata.tables["chat_rate_limits"]
            hour_start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            
            stmt = select(table.c.message_count).where(
                (table.c.user_id == user_id) &
                (table.c.window_type == "hourly") &
                (table.c.window_start == hour_start)
            )
            result = await self._session.execute(stmt)
            row = result.scalar()
            return row or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get hourly count: {e}")
            return 0
    
    async def get_daily_count(self, user_id: UUID) -> int:
        """Get message count for current day."""
        try:
            table = mapping_registry.metadata.tables["chat_rate_limits"]
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            stmt = select(table.c.message_count).where(
                (table.c.user_id == user_id) &
                (table.c.window_type == "daily") &
                (table.c.window_start == day_start)
            )
            result = await self._session.execute(stmt)
            row = result.scalar()
            return row or 0
        except SQLAlchemyError as e:
            logger.error(f"Failed to get daily count: {e}")
            return 0
    
    async def increment(self, user_id: UUID) -> None:
        """Increment message counts for hourly and daily windows."""
        try:
            table = mapping_registry.metadata.tables["chat_rate_limits"]
            now = datetime.utcnow()
            hour_start = now.replace(minute=0, second=0, microsecond=0)
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Upsert hourly
            await self._upsert_count(table, user_id, "hourly", hour_start)
            
            # Upsert daily
            await self._upsert_count(table, user_id, "daily", day_start)
            
            await self._session.commit()
        except SQLAlchemyError as e:
            await self._session.rollback()
            logger.error(f"Failed to increment rate limit: {e}")
    
    async def _upsert_count(
        self,
        table,
        user_id: UUID,
        window_type: str,
        window_start: datetime,
    ) -> None:
        """Upsert rate limit count."""
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(table).values(
            user_id=user_id,
            window_type=window_type,
            window_start=window_start,
            message_count=1,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_rate_limits_user_window",
            set_={"message_count": table.c.message_count + 1},
        )
        await self._session.execute(stmt)

