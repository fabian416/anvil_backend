"""
Context Storage Gateway port.
"""

from typing import Protocol

from app.domain.value_objects.conversation_id import ConversationId
from app.domain.services.agent_squad.context_manager import ConversationMessage


class ContextStorageGateway(Protocol):
    """
    Context Storage Gateway port.
    
    Implementing adapters:
    - ContextStorageRedis (Redis implementation)
    - ContextStoragePostgreSQL (PostgreSQL implementation)
    """
    
    async def add_message(
        self,
        conversation_id: ConversationId,
        message: ConversationMessage,
    ) -> None:
        """Add message to conversation history."""
        ...
    
    async def get_messages(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[ConversationMessage]:
        """Get recent messages."""
        ...
    
    async def get_metadata(
        self,
        conversation_id: ConversationId,
    ) -> dict:
        """Get conversation metadata."""
        ...
    
    async def update_metadata(
        self,
        conversation_id: ConversationId,
        user_metadata: dict | None,
        session_metadata: dict | None,
    ) -> None:
        """Update conversation metadata."""
        ...
    
    async def clear_messages(
        self,
        conversation_id: ConversationId,
    ) -> None:
        """Clear conversation history."""
        ...
    
    async def get_message_count(
        self,
        conversation_id: ConversationId,
    ) -> int:
        """Get message count."""
        ...
    
    async def remove_oldest_messages(
        self,
        conversation_id: ConversationId,
        count: int,
    ) -> None:
        """Remove oldest messages."""
        ...
