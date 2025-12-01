"""
Create conversation command.
"""

from uuid import UUID
from typing import Optional

from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository


class CreateConversation:
    """
    Create a new conversation for a user.
    
    This is the entry point for starting a new chat session.
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
        title: Optional[str] = None,
    ) -> Conversation:
        """
        Execute the command.
        
        Args:
            user_id: User identifier
            title: Optional conversation title
        
        Returns:
            Created conversation entity
        """
        # Create conversation
        conversation = Conversation.create(
            user_id=user_id,
            title=title,
        )
        
        # Save to repository
        await self._repository.add_conversation(conversation)
        
        return conversation
