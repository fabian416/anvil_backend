"""
List conversations query.
"""

from typing import List

from app.domain.entities.conversation import Conversation
from app.domain.ports.conversation_repository import ConversationRepository


class ListConversations:
    """
    List conversations for a user.
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
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        Execute the query.
        
        Args:
            user_id: User identifier
            limit: Maximum conversations to return
            offset: Offset for pagination
        
        Returns:
            List of conversation entities
        """
        conversations = await self._repository.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        
        return conversations
