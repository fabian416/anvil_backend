"""
Builder for creating Message test data.

Provides fluent interface for test data creation.
"""

from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional


class MessageBuilder:
    """Fluent builder for Message test data."""
    
    def __init__(self):
        """Initialize with default values."""
        self._id: UUID = uuid4()
        self._conversation_id: UUID = uuid4()
        self._role: str = "user"
        self._content: str = "Test message"
        self._created_at: datetime = datetime.utcnow()
        self._agent_type: Optional[str] = None
    
    def with_id(self, id_: UUID) -> 'MessageBuilder':
        """Set message ID."""
        self._id = id_
        return self
    
    def with_conversation_id(self, conversation_id: UUID) -> 'MessageBuilder':
        """Set conversation ID."""
        self._conversation_id = conversation_id
        return self
    
    def with_role(self, role: str) -> 'MessageBuilder':
        """Set message role (user, agent, system)."""
        self._role = role
        return self
    
    def with_content(self, content: str) -> 'MessageBuilder':
        """Set message content."""
        self._content = content
        return self
    
    def with_agent_type(self, agent_type: str) -> 'MessageBuilder':
        """Set agent type (for agent messages)."""
        self._agent_type = agent_type
        return self
    
    def from_user(self) -> 'MessageBuilder':
        """Configure as user message."""
        self._role = "user"
        self._agent_type = None
        return self
    
    def from_agent(self, agent_type: str = "general") -> 'MessageBuilder':
        """Configure as agent message."""
        self._role = "agent"
        self._agent_type = agent_type
        return self
    
    def from_system(self) -> 'MessageBuilder':
        """Configure as system message."""
        self._role = "system"
        self._agent_type = None
        return self
    
    def build_dict(self) -> dict:
        """Build as dictionary."""
        return {
            "id": str(self._id),
            "conversation_id": str(self._conversation_id),
            "role": self._role,
            "content": self._content,
            "created_at": self._created_at.isoformat(),
            "agent_type": self._agent_type
        }
    
    @classmethod
    def a_message(cls) -> 'MessageBuilder':
        """Start building a message."""
        return cls()
    
    @classmethod
    def a_user_message(cls) -> 'MessageBuilder':
        """Build a user message."""
        return cls().from_user()
    
    @classmethod
    def an_agent_message(cls) -> 'MessageBuilder':
        """Build an agent message."""
        return cls().from_agent()


# Convenience functions
def a_message() -> MessageBuilder:
    """Start building a message."""
    return MessageBuilder()


def a_user_message() -> MessageBuilder:
    """Build a user message."""
    return MessageBuilder().from_user()


def an_agent_message() -> MessageBuilder:
    """Build an agent message."""
    return MessageBuilder().from_agent()
