"""
Get conversation query.
"""

from uuid import UUID
from typing import Optional

from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository


class GetConversation:
    """
    Get a conversation by ID.
    """
    
    def __init__(self, repository: ConversationRepository):
        """
        Initialize interactor.
        
        Args:
            repository: Conversation repository
        """
        self._repository = repository
    
    async def execute(
        self,
        user_id: int,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """
        Execute the query.
        
        Args:
            user_id: User identifier (for verification)
            conversation_id: Conversation identifier
        
        Returns:
            Conversation entity or None
        
        Raises:
            ValueError: If conversation doesn't belong to user
        """
        conversation = await self._repository.get_conversation(conversation_id)
        
        if conversation is None:
            return None
        
        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")
        
        return conversation
