"""
Conversation Context value object.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.enums.agent_type import AgentType


@dataclass(frozen=True)
class ConversationMessage:
    """
    Individual message in a conversation context.
    
    Represents a single message with role, content, and metadata.
    """
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ConversationContext:
    """
    Conversation context for intent classification and agent execution.
    
    Contains:
    - conversation_history: Recent messages (for context)
    - user_metadata: User preferences, portfolio, etc.
    - session_metadata: Current session info
    """
    conversation_history: list[dict] = field(default_factory=list)
    user_metadata: dict = field(default_factory=dict)
    session_metadata: dict = field(default_factory=dict)
    
    def last_n_messages(self, n: int = 5) -> list[dict]:
        """Get last N messages for context."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    @property
    def has_history(self) -> bool:
        """Check if conversation has history."""
        return len(self.conversation_history) > 0
    
    @property
    def message_count(self) -> int:
        """Get total message count."""
        return len(self.conversation_history)

    @property
    def last_agent_type(self) -> Optional["AgentType"]:
        """Get the agent type of the last agent message."""
        from app.domain.enums.agent_type import AgentType

        for message in reversed(self.conversation_history):
            if message.get("role") == "agent" and message.get("agent_type"):
                return AgentType(message["agent_type"])
        return None

    def with_new_message(self, message: dict) -> "ConversationContext":
        """Create new context with additional message."""
        return ConversationContext(
            conversation_history=[*self.conversation_history, message],
            user_metadata=self.user_metadata,
            session_metadata=self.session_metadata,
        )
