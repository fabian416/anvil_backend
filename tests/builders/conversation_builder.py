"""
Builder for creating Conversation test data.

Provides fluent interface for test data creation.
"""

from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional


class ConversationBuilder:
    """Fluent builder for Conversation test data."""
    
    def __init__(self):
        """Initialize with default values."""
        self._id: UUID = uuid4()
        self._user_id: int = 12345
        self._created_at: datetime = datetime.utcnow()
        self._updated_at: datetime = datetime.utcnow()
        self._title: Optional[str] = None
    
    def with_id(self, id_: UUID) -> 'ConversationBuilder':
        """Set conversation ID."""
        self._id = id_
        return self
    
    def with_user_id(self, user_id: int) -> 'ConversationBuilder':
        """Set user ID."""
        self._user_id = user_id
        return self
    
    def with_title(self, title: str) -> 'ConversationBuilder':
        """Set conversation title."""
        self._title = title
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> 'ConversationBuilder':
        """Set timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def build_dict(self) -> dict:
        """Build as dictionary."""
        return {
            "id": str(self._id),
            "user_id": self._user_id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "title": self._title
        }
    
    @classmethod
    def a_conversation(cls) -> 'ConversationBuilder':
        """Start building a conversation."""
        return cls()
    
    @classmethod
    def default(cls) -> 'ConversationBuilder':
        """Create with default values."""
        return cls()


# Convenience function
def a_conversation() -> ConversationBuilder:
    """Start building a conversation."""
    return ConversationBuilder()
