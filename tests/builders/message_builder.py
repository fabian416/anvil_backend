"""
Builder for creating Message test data.

Provides fluent interface for test data creation.
"""

from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass


@dataclass
class TestMessage:
    """Test message data class."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    agent_type: Optional[str] = None
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "agent_type": self.agent_type,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


class MessageBuilder:
    """Fluent builder for Message test data."""
    
    def __init__(self):
        """Initialize with default values."""
        self._id: UUID = uuid4()
        self._conversation_id: UUID = uuid4()
        self._role: str = "user"
        self._content: str = "Test message"
        self._created_at: datetime = datetime.now(timezone.utc)
        self._agent_type: Optional[str] = None
        self._metadata: Optional[dict] = None
    
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

    def with_metadata(self, metadata: dict) -> 'MessageBuilder':
        """Set message metadata."""
        self._metadata = metadata
        return self

    def with_llm_response(
        self, 
        content: Optional[str] = None, 
        model: str = "gpt-4", 
        tokens: int = 100,
        include_disclaimer: bool = False,
    ) -> 'MessageBuilder':
        """Add LLM response metadata and optionally set content."""
        if content:
            self._content = content
            if include_disclaimer:
                self._content += "\n\n*This is not financial advice.*"
        self._metadata = {
            "model": model,
            "tokens_used": tokens,
            "finish_reason": "stop",
        }
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
        result = {
            "id": str(self._id),
            "conversation_id": str(self._conversation_id),
            "role": self._role,
            "content": self._content,
            "created_at": self._created_at.isoformat(),
            "agent_type": self._agent_type,
        }
        if self._metadata:
            result["metadata"] = self._metadata
        return result

    def build(self) -> TestMessage:
        """Build as TestMessage dataclass."""
        return TestMessage(
            id=self._id,
            conversation_id=self._conversation_id,
            role=self._role,
            content=self._content,
            created_at=self._created_at,
            agent_type=self._agent_type,
            metadata=self._metadata,
        )
    
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
