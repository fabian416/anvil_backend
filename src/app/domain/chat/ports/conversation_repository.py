"""
Repository port for chat conversations and messages.
"""

from typing import Protocol, List, Optional
from uuid import UUID

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message


class ConversationRepository(Protocol):
    """
    Repository for chat conversations and messages.
    
    This is separate from LLMConversationRepository which handles
    AI telemetry conversations.
    """
    
    async def add_conversation(self, conversation: Conversation) -> None:
        """
        Add a new conversation.

        Args:
            conversation: Conversation entity to persist
        """
        ...

    async def update_conversation(self, conversation: Conversation) -> None:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation entity to update
        """
        ...

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
        
        Returns:
            Conversation entity or None if not found
        """
        ...
    
    async def list_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[Conversation]:
        """
        List conversations for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Offset for pagination
        
        Returns:
            List of conversation entities
        """
        ...
    
    async def add_message(self, message: Message) -> None:
        """
        Add a message to a conversation.
        
        Args:
            message: Message entity to persist
        """
        ...
    
    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.
        
        Args:
            message_id: Message identifier
        
        Returns:
            Message entity or None if not found
        """
        ...
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[Message]:
        """
        Get messages for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
        
        Returns:
            List of message entities, ordered by created_at (oldest first)
        """
        ...
