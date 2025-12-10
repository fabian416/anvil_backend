"""
Builder for creating Conversation test data.

Provides fluent interface for test data creation.
"""

from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Optional, List
from dataclasses import dataclass, field


@dataclass
class TestConversation:
    """Test conversation data class."""
    id: UUID
    user_id: int
    created_at: datetime
    updated_at: datetime
    title: Optional[str] = None
    messages: List[dict] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        """Return number of messages."""
        return len(self.messages)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title,
            "messages": self.messages,
        }


class ConversationBuilder:
    """Fluent builder for Conversation test data."""
    
    def __init__(self):
        """Initialize with default values."""
        self._id: UUID = uuid4()
        self._user_id: int = 12345
        self._created_at: datetime = datetime.now(timezone.utc)
        self._updated_at: datetime = datetime.now(timezone.utc)
        self._title: Optional[str] = None
        self._messages: List[dict] = []
    
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

    def with_messages(self, count: int = 1) -> 'ConversationBuilder':
        """Add pairs of user/agent messages (count pairs = 2*count messages)."""
        for i in range(count):
            # User message
            self._messages.append({
                "id": str(uuid4()),
                "conversation_id": str(self._id),
                "role": "user",
                "content": f"User message {i + 1}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            # Agent response
            self._messages.append({
                "id": str(uuid4()),
                "conversation_id": str(self._id),
                "role": "agent",
                "content": f"Agent response {i + 1}",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        return self
    
    def build_dict(self) -> dict:
        """Build as dictionary."""
        return {
            "id": str(self._id),
            "user_id": self._user_id,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "title": self._title,
            "messages": self._messages,
        }

    def build(self) -> TestConversation:
        """Build as TestConversation dataclass."""
        return TestConversation(
            id=self._id,
            user_id=self._user_id,
            created_at=self._created_at,
            updated_at=self._updated_at,
            title=self._title,
            messages=self._messages,
        )
    
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
