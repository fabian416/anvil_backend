"""
SQLAlchemy implementation of MessageRepository.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select

from app.domain.chat.ports.message_repository import MessageRepository
from app.domain.chat.entities.message import Message
from app.domain.enums.message_role import MessageRole
from app.infrastructure.adapters.types import MainAsyncSession
from app.infrastructure.persistence_sqla.registry import mapping_registry


class SqlaMessageRepository(MessageRepository):
    """
    SQLAlchemy implementation of message repository.
    
    Handles persistence of chat messages using imperative mapping pattern.
    """
    
    def __init__(self, session: MainAsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self._session = session
    
    async def save(self, message: Message) -> None:
        """Save a message to the database."""
        messages_table = mapping_registry.metadata.tables.get("messages")
        if not messages_table:
            raise RuntimeError("messages table not found in metadata")
        
        # Get role value - handle both Enum and string
        role_value = message.role.value if hasattr(message.role, 'value') else str(message.role)
        
        # Get agent_type value if present
        agent_type_value = None
        if message.agent_type:
            agent_type_value = message.agent_type.value if hasattr(message.agent_type, 'value') else str(message.agent_type)
        
        # Insert message data
        stmt = messages_table.insert().values(
            id=message.id,
            conversation_id=message.conversation_id,
            role=role_value,
            content=message.content,
            agent_type=agent_type_value,
            created_at=message.created_at
        )
        
        await self._session.execute(stmt)
        await self._session.flush()
    
    async def get(self, message_id: UUID) -> Optional[Message]:
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
            id=row.id,
            conversation_id=row.conversation_id,
            role=MessageRole(row.role),
            content=row.content,
            agent_type=row.agent_type,
            created_at=row.created_at
        )
    
    async def get_by_conversation(
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
                id=row.id,
                conversation_id=row.conversation_id,
                role=MessageRole(row.role),
                content=row.content,
                agent_type=row.agent_type,
                created_at=row.created_at
            )
            messages.append(message)
        
        return messages
