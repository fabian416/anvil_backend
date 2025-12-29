"""
Conversation entity for chat conversations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from app.domain.common.datetime_utils import utc_now


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
        project_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize conversation.
        
        Args:
            id: Conversation identifier
            user_id: User identifier
            title: Optional conversation title
            project_id: Optional project identifier (for project-scoped conversations)
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.user_id = user_id
        self.title = title
        self.project_id = project_id
        self.created_at = created_at or utc_now()
        self.updated_at = updated_at or utc_now()
    
    @classmethod
    def create(
        cls,
        user_id: int,
        title: Optional[str] = None,
        project_id: Optional[UUID] = None,
    ) -> "Conversation":
        """
        Create a new conversation.
        
        Args:
            user_id: User identifier
            title: Optional conversation title
            project_id: Optional project identifier (for project-scoped conversations)
        
        Returns:
            New conversation instance
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            title=title,
            project_id=project_id,
        )
    
    def update_title(self, title: str) -> None:
        """
        Update conversation title.
        
        Args:
            title: New title
        """
        self.title = title
        self.updated_at = utc_now()
    
    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = utc_now()
    
    @property
    def is_project_scoped(self) -> bool:
        """
        Check if conversation is scoped to a project.
        
        Returns:
            True if conversation is linked to a project
        """
        return self.project_id is not None
