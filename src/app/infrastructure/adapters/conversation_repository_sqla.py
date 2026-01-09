"""
SQLAlchemy implementation of ConversationRepository.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chat.ports.conversation_repository import ConversationRepository
from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.entities.message import Message
from app.domain.value_objects.message_role import MessageRole
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
        if conversations_table is None:
            raise RuntimeError("conversations table not found in metadata")

        # Insert conversation data
        stmt = conversations_table.insert().values(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title if conversation.title else None,
            project_id=conversation.project_id if conversation.project_id else None,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

        await self._session.execute(stmt)
        await self._session.flush()

    async def update_conversation(self, conversation: Conversation) -> None:
        """Update an existing conversation in the database."""
        # Get the mapped table
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if conversations_table is None:
            raise RuntimeError("conversations table not found in metadata")

        # Update conversation data
        stmt = (
            conversations_table.update()
            .where(conversations_table.c.id == conversation.id)
            .values(
                title=conversation.title if conversation.title else None,
                project_id=conversation.project_id if conversation.project_id else None,
                updated_at=conversation.updated_at
            )
        )

        await self._session.execute(stmt)
        await self._session.flush()
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if conversations_table is None:
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
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            project_id=row.project_id if hasattr(row, 'project_id') else None,
            created_at=row.created_at,
            updated_at=row.updated_at
        )
    
    async def list_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """List conversations for a user."""
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        if conversations_table is None:
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
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                project_id=row.project_id if hasattr(row, 'project_id') else None,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            conversations.append(conversation)
        
        return conversations
    
    async def add_message(self, message: Message) -> None:
        """Add a message to a conversation."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if messages_table is None:
            raise RuntimeError("messages table not found in metadata")
        
        try:
            # Insert message data
            stmt = messages_table.insert().values(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role.value,
                content=message.content,
                agent_type=message.agent_type if message.agent_type else None,
                created_at=message.created_at
            )
            
            await self._session.execute(stmt)
            await self._session.flush()
        except Exception as e:
            # Rollback the transaction on error to prevent InFailedSqlTransaction
            await self._session.rollback()
            raise
    
    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get a message by ID."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if messages_table is None:
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
            id=row.id,
            conversation_id=row.conversation_id,
            role=MessageRole(row.role),
            content=row.content,
            agent_type=row.agent_type,
            created_at=row.created_at
        )
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[Message]:
        """Get messages for a conversation."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if messages_table is None:
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
                id=row.id,
                conversation_id=row.conversation_id,
                role=MessageRole(row.role),
                content=row.content,
                agent_type=row.agent_type,
                created_at=row.created_at
            )
            messages.append(message)
        
        return messages
    
    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: int
    ) -> bool:
        """Delete a conversation and its messages."""
        conversations_table = mapping_registry.metadata.tables.get("conversations")
        messages_table = mapping_registry.metadata.tables.get("messages")
        
        if conversations_table is None:
            raise RuntimeError("conversations table not found in metadata")
        
        # First verify the conversation belongs to the user
        stmt = select(conversations_table).where(
            (conversations_table.c.id == conversation_id) &
            (conversations_table.c.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()
        
        if not row:
            return False
        
        # Delete messages first (if table exists)
        if messages_table is not None:
            delete_messages_stmt = delete(messages_table).where(
                messages_table.c.conversation_id == conversation_id
            )
            await self._session.execute(delete_messages_stmt)
        
        # Delete the conversation
        delete_conv_stmt = delete(conversations_table).where(
            conversations_table.c.id == conversation_id
        )
        await self._session.execute(delete_conv_stmt)
        await self._session.commit()
        
        return True
