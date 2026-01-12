"""SQLAlchemy repository implementations for authenticated chat.

This module provides concrete implementations of the chat repository ports,
using SQLAlchemy for database persistence.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.entities import ChatUser, ChatConversation, ChatMessage
from app.domain.ports.chat_repository import (
    ChatUserRepository,
    ChatConversationRepository,
    ChatMessageRepository,
)


class SQLAlchemyChatUserRepository(ChatUserRepository):
    """SQLAlchemy implementation of ChatUserRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(self, chat_user: ChatUser) -> ChatUser:
        """Create a new chat user."""
        from app.infrastructure.persistence_sqla.registry import mapping_registry

        chat_users_table = mapping_registry.metadata.tables["chat_users"]

        stmt = chat_users_table.insert().values(
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
        ).returning(chat_users_table)

        result = await self._session.execute(stmt)
        await self._session.flush()
        row = result.fetchone()

        return self._row_to_entity(row)

    async def get_by_id(self, chat_user_id: UUID) -> Optional[ChatUser]:
        """Get chat user by UUID."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        result = await self._session.execute(
            select(ChatUserModel).where(ChatUserModel.id == chat_user_id)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_by_user_id(self, user_id: int) -> Optional[ChatUser]:
        """Get chat user by legacy user ID."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        result = await self._session.execute(
            select(ChatUserModel).where(ChatUserModel.user_id == user_id)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[ChatUser]:
        """Get chat user by email."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        result = await self._session.execute(
            select(ChatUserModel).where(ChatUserModel.email == email)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def update(self, chat_user: ChatUser) -> ChatUser:
        """Update existing chat user."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        await self._session.execute(
            update(ChatUserModel)
            .where(ChatUserModel.id == chat_user.id_)
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
        await self._session.flush()

        return await self.get_by_id(chat_user.id_)

    async def delete(self, chat_user_id: UUID) -> None:
        """Delete chat user by ID."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        await self._session.execute(
            delete(ChatUserModel).where(ChatUserModel.id == chat_user_id)
        )
        await self._session.flush()

    async def update_last_seen(self, chat_user_id: UUID) -> None:
        """Update last seen timestamp."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        await self._session.execute(
            update(ChatUserModel)
            .where(ChatUserModel.id == chat_user_id)
            .values(last_seen_at=datetime.utcnow(), updated_at=datetime.utcnow())
        )
        await self._session.flush()

    async def increment_message_count(self, chat_user_id: UUID) -> None:
        """Increment total message count."""
        from app.infrastructure.persistence_sqla.models import ChatUserModel

        await self._session.execute(
            update(ChatUserModel)
            .where(ChatUserModel.id == chat_user_id)
            .values(
                total_messages=ChatUserModel.total_messages + 1,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.flush()

    @staticmethod
    def _model_to_entity(model) -> ChatUser:
        """Convert SQLAlchemy model to domain entity."""
        return ChatUser(
            id_=model.id,
            user_id=model.user_id,
            email=model.email,
            subscription_tier=model.subscription_tier,
            total_messages=model.total_messages,
            language=model.language,
            chat_preferences=model.chat_preferences or {},
            first_seen_at=model.first_seen_at,
            last_seen_at=model.last_seen_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class SQLAlchemyChatConversationRepository(ChatConversationRepository):
    """SQLAlchemy implementation of ChatConversationRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Create a new conversation."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        model = ChatConversationModel(
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

        self._session.add(model)
        await self._session.flush()

        return self._model_to_entity(model)

    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Get conversation by ID."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        result = await self._session.execute(
            select(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id
            )
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def get_active_conversation(
        self, chat_user_id: UUID, language: str
    ) -> Optional[ChatConversation]:
        """Get the most recent active conversation for a user in a language."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        result = await self._session.execute(
            select(ChatConversationModel)
            .where(
                and_(
                    ChatConversationModel.chat_user_id == chat_user_id,
                    ChatConversationModel.status == "active",
                    ChatConversationModel.language == language,
                )
            )
            .order_by(ChatConversationModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def list_by_user(
        self,
        chat_user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatConversation]:
        """List conversations for a user."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        query = select(ChatConversationModel).where(
            ChatConversationModel.chat_user_id == chat_user_id
        )

        if status:
            query = query.where(ChatConversationModel.status == status)

        query = (
            query.order_by(ChatConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(query)
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Update existing conversation."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        await self._session.execute(
            update(ChatConversationModel)
            .where(ChatConversationModel.id == conversation.id_)
            .values(
                title=conversation.title,
                status=conversation.status,
                message_count=conversation.message_count,
                language=conversation.language,
                archived_at=conversation.archived_at,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.flush()

        return await self.get_by_id(conversation.id_)

    async def delete(self, conversation_id: UUID) -> None:
        """Delete conversation by ID."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        await self._session.execute(
            delete(ChatConversationModel).where(
                ChatConversationModel.id == conversation_id
            )
        )
        await self._session.flush()

    async def archive(self, conversation_id: UUID) -> None:
        """Archive a conversation."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        await self._session.execute(
            update(ChatConversationModel)
            .where(ChatConversationModel.id == conversation_id)
            .values(
                status="archived",
                archived_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.flush()

    async def unarchive(self, conversation_id: UUID) -> None:
        """Restore an archived conversation."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        await self._session.execute(
            update(ChatConversationModel)
            .where(ChatConversationModel.id == conversation_id)
            .values(
                status="active", archived_at=None, updated_at=datetime.utcnow()
            )
        )
        await self._session.flush()

    async def increment_message_count(self, conversation_id: UUID) -> None:
        """Increment message count."""
        from app.infrastructure.persistence_sqla.models import ChatConversationModel

        await self._session.execute(
            update(ChatConversationModel)
            .where(ChatConversationModel.id == conversation_id)
            .values(
                message_count=ChatConversationModel.message_count + 1,
                updated_at=datetime.utcnow(),
            )
        )
        await self._session.flush()

    @staticmethod
    def _model_to_entity(model) -> ChatConversation:
        """Convert SQLAlchemy model to domain entity."""
        return ChatConversation(
            id_=model.id,
            chat_user_id=model.chat_user_id,
            title=model.title,
            status=model.status,
            message_count=model.message_count,
            language=model.language,
            created_at=model.created_at,
            updated_at=model.updated_at,
            archived_at=model.archived_at,
        )


class SQLAlchemyChatMessageRepository(ChatMessageRepository):
    """SQLAlchemy implementation of ChatMessageRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        model = ChatMessageModel(
            id=message.id_,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            intent=message.intent,
            handler=message.handler,
            confidence=message.confidence,
            language=message.language,
            is_restricted_action=message.is_restricted_action,
            metadata=message.metadata,
            created_at=message.created_at,
        )

        self._session.add(model)
        await self._session.flush()

        return self._model_to_entity(model)

    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get message by ID."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        result = await self._session.execute(
            select(ChatMessageModel).where(ChatMessageModel.id == message_id)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """List messages in a conversation."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        result = await self._session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.conversation_id == conversation_id)
            .order_by(ChatMessageModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def list_by_conversation_since(
        self,
        conversation_id: UUID,
        since: datetime,
    ) -> List[ChatMessage]:
        """List messages in a conversation since a timestamp."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        result = await self._session.execute(
            select(ChatMessageModel)
            .where(
                and_(
                    ChatMessageModel.conversation_id == conversation_id,
                    ChatMessageModel.created_at > since,
                )
            )
            .order_by(ChatMessageModel.created_at.asc())
        )
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Count messages in a conversation."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        result = await self._session.execute(
            select(func.count(ChatMessageModel.id)).where(
                ChatMessageModel.conversation_id == conversation_id
            )
        )
        return result.scalar()

    async def delete(self, message_id: UUID) -> None:
        """Delete message by ID."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        await self._session.execute(
            delete(ChatMessageModel).where(ChatMessageModel.id == message_id)
        )
        await self._session.flush()

    async def delete_by_conversation(self, conversation_id: UUID) -> None:
        """Delete all messages in a conversation."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        await self._session.execute(
            delete(ChatMessageModel).where(
                ChatMessageModel.conversation_id == conversation_id
            )
        )
        await self._session.flush()

    async def get_latest_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[ChatMessage]:
        """Get the most recent message in a conversation."""
        from app.infrastructure.persistence_sqla.models import ChatMessageModel

        result = await self._session.execute(
            select(ChatMessageModel)
            .where(ChatMessageModel.conversation_id == conversation_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()

        return self._model_to_entity(model) if model else None

    async def search_by_intent(
        self,
        chat_user_id: UUID,
        intent: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Search messages by Hunter AI intent."""
        from app.infrastructure.persistence_sqla.models import (
            ChatMessageModel,
            ChatConversationModel,
        )

        result = await self._session.execute(
            select(ChatMessageModel)
            .join(
                ChatConversationModel,
                ChatMessageModel.conversation_id == ChatConversationModel.id,
            )
            .where(
                and_(
                    ChatConversationModel.chat_user_id == chat_user_id,
                    ChatMessageModel.intent == intent,
                )
            )
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        models = result.scalars().all()

        return [self._model_to_entity(model) for model in models]

    @staticmethod
    def _model_to_entity(model) -> ChatMessage:
        """Convert SQLAlchemy model to domain entity."""
        return ChatMessage(
            id_=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            intent=model.intent,
            handler=model.handler,
            confidence=model.confidence,
            language=model.language,
            is_restricted_action=model.is_restricted_action,
            metadata=model.metadata or {},
            created_at=model.created_at,
        )
