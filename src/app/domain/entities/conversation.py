"""
Conversation entity for chat conversations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4


class Conversation:
    """
    Conversation entity representing a chat conversation.
    
    A conversation belongs to a user and contains messages exchanged
    with DeFi agents.
    """
    
    def __init__(
        self,
        id: UUID,
        user_id: int,
        title: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize conversation.
        
        Args:
            id: Conversation identifier
            user_id: User identifier
            title: Optional conversation title
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.user_id = user_id
        self.title = title
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    @classmethod
    def create(
        cls,
        user_id: int,
        title: Optional[str] = None,
    ) -> "Conversation":
        """
        Create a new conversation.
        
        Args:
            user_id: User identifier
            title: Optional conversation title
        
        Returns:
            New conversation instance
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            title=title,
        )
    
    def update_title(self, title: str) -> None:
        """
        Update conversation title.
        
        Args:
            title: New title
        """
        self.title = title
        self.updated_at = datetime.utcnow()
    
    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
