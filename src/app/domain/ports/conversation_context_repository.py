"""
Repository port for ConversationContext.
"""

from typing import Protocol, Optional
from uuid import UUID

from app.domain.chat.entities.conversation_context import ConversationContext


class ConversationContextRepository(Protocol):
    """
    Repository interface for conversation context persistence.
    """
    
    async def get_by_conversation_id(
        self,
        conversation_id: UUID,
    ) -> Optional[ConversationContext]:
        """
        Get context by conversation ID.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            ConversationContext or None if not found
        """
        ...
    
    async def get_by_user_id(
        self,
        user_id: UUID,
    ) -> Optional[ConversationContext]:
        """
        Get the most recent context for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Most recent ConversationContext or None
        """
        ...
    
    async def save(self, context: ConversationContext) -> None:
        """
        Save or update conversation context.
        
        Args:
            context: ConversationContext to save
        """
        ...
    
    async def delete(self, context_id: UUID) -> None:
        """
        Delete conversation context.
        
        Args:
            context_id: Context identifier
        """
        ...
