"""
SQLAlchemy implementation of ConversationRepository.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.entities.message import Message
from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_id import MessageId
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.conversation_title import ConversationTitle
from app.domain.value_objects.message_content import MessageContent
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.enums.message_role import MessageRole
from app.domain.enums.agent_type import AgentType
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaConversationRepository(ConversationRepository):
    """
    SQLAlchemy implementation of conversation repository.
    
    Maps between domain entities and database tables using
    the imperative mapping pattern.
    """
    
    def __init__(self, session: MainAsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def add_conversation(self, conversation: Conversation) -> None:
        """Add a new conversation to the database."""
        # Get the mapped table
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if not conversations_table:
            raise RuntimeError("conversations table not found in metadata")
        
        # Insert conversation data
        stmt = conversations_table.insert().values(
            id=conversation.id_.value,
            user_id=conversation.user_id.value,
            title=conversation.title.value if conversation.title else None,
            created_at=conversation.created_at.value,
            updated_at=conversation.updated_at.value
        )
        
        await self._session.execute(stmt)
        await self._session.flush()
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if not conversations_table:
            raise RuntimeError("conversations table not found in metadata")
        
        stmt = select(conversations_table).where(
            conversations_table.c.id == conversation_id
        )
        
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        # Map row to entity
        return Conversation(
            id_=ConversationId(row.id),
            user_id=UserId(row.user_id),
            title=ConversationTitle(row.title) if row.title else None,
            created_at=CreatedAt(row.created_at),
            updated_at=UpdatedAt(row.updated_at)
        )
    
    async def list_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations for a user."""
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if not conversations_table:
            raise RuntimeError("conversations table not found in metadata")
        
        stmt = (
            select(conversations_table)
            .where(conversations_table.c.user_id == user_id)
            .order_by(conversations_table.c.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        # Map rows to entities
        conversations = []
        for row in rows:
            conversation = Conversation(
                id_=ConversationId(row.id),
                user_id=UserId(row.user_id),
                title=ConversationTitle(row.title) if row.title else None,
                created_at=CreatedAt(row.created_at),
                updated_at=UpdatedAt(row.updated_at)
            )
            conversations.append(conversation)
        
        return conversations
    
    async def add_message(self, message: Message) -> None:
        """Add a message to a conversation."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if not messages_table:
            raise RuntimeError("messages table not found in metadata")
        
        # Insert message data
        stmt = messages_table.insert().values(
            id=message.id_.value,
            conversation_id=message.conversation_id.value,
            role=message.role.value,
            content=message.content.value,
            agent_type=message.agent_type.value if message.agent_type else None,
            created_at=message.created_at.value
        )
        
        await self._session.execute(stmt)
        await self._session.flush()
    
    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if not messages_table:
            raise RuntimeError("messages table not found in metadata")
        
        stmt = select(messages_table).where(
            messages_table.c.id == message_id
        )
        
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return None
        
        # Map row to entity
        return Message(
            id_=MessageId(row.id),
            conversation_id=ConversationId(row.conversation_id),
            role=MessageRole(row.role),
            content=MessageContent(row.content),
            agent_type=AgentType(row.agent_type) if row.agent_type else None,
            created_at=CreatedAt(row.created_at)
        )
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if not messages_table:
            raise RuntimeError("messages table not found in metadata")
        
        stmt = (
            select(messages_table)
            .where(messages_table.c.conversation_id == conversation_id)
            .order_by(messages_table.c.created_at.asc())  # Oldest first
            .limit(limit)
        )
        
        result = await self._session.execute(stmt)
        rows = result.fetchall()
        
        # Map rows to entities
        messages = []
        for row in rows:
            message = Message(
                id_=MessageId(row.id),
                conversation_id=ConversationId(row.conversation_id),
                role=MessageRole(row.role),
                content=MessageContent(row.content),
                agent_type=AgentType(row.agent_type) if row.agent_type else None,
                created_at=CreatedAt(row.created_at)
            )
            messages.append(message)
        
        return messages
