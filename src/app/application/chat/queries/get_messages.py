"""
Get messages query.
"""

from uuid import UUID
from typing import List

from app.domain.chat.entities.message import Message
from app.domain.chat.entities.conversation import Conversation
from app.domain.chat.ports.conversation_repository import ConversationRepository


class GetMessages:
    """
    Get messages for a conversation.
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
        limit: int = 50,
    ) -> List[Message]:
        """
        Execute the query.
        
        Args:
            user_id: User identifier (for verification)
            conversation_id: Conversation identifier
            limit: Maximum messages to return
        
        Returns:
            List of message entities
        
        Raises:
            ValueError: If conversation not found or not owned by user
        """
        # Verify conversation ownership
        conversation = await self._repository.get_conversation(conversation_id)
        
        if conversation is None:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        if conversation.user_id != user_id:
            raise ValueError("Conversation does not belong to user")
        
        # Get messages
        messages = await self._repository.get_messages(
            conversation_id=conversation_id,
            limit=limit,
        )
        
        return messages
