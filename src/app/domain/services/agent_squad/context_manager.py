"""
Context Manager domain service - Preserves conversation history.
"""

from typing import Protocol
from dataclasses import dataclass, field
from datetime import datetime, UTC

from app.domain.value_objects.conversation_id import ConversationId
from app.domain.value_objects.message_id import MessageId
from app.domain.enums.agent_type import AgentType


@dataclass
class ConversationMessage:
    """Single conversation message."""

    message_id: MessageId
    role: str  # "user", "assistant", "system"
    content: str
    agent_type: AgentType | None  # Which agent generated this (if assistant)
    timestamp: datetime
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "message_id": str(self.message_id.value),
            "role": self.role,
            "content": self.content,
            "agent_type": self.agent_type.value if self.agent_type else None,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ContextManager:
    """
    Context Manager domain service.

    Responsibilities:
    - Preserve conversation history across agent calls
    - Manage context window (token limits)
    - Provide conversation summary for new agents
    - Support multi-turn conversations with context

    Architecture:
    - Domain service (framework-agnostic)
    - Uses storage port for persistence (Redis/PostgreSQL)
    - Manages conversation state

    Context Strategies:
    - Full history: Keep all messages (up to limit)
    - Sliding window: Keep last N messages
    - Summary: Summarize old messages, keep recent full
    """

    def __init__(
        self,
        storage: "ContextStoragePort",
        history_limit: int = 20,  # Maximum messages to keep
        token_limit: int = 8000,  # Maximum context tokens
    ):
        """
        Initialize context manager.

        Args:
            storage: Context storage port (Redis/PostgreSQL)
            history_limit: Maximum messages to keep (default 20)
            token_limit: Maximum context tokens (default 8000)
        """
        self._storage = storage
        self._history_limit = history_limit
        self._token_limit = token_limit

    async def add_message(
        self,
        conversation_id: ConversationId,
        message_id: MessageId,
        role: str,
        content: str,
        agent_type: AgentType | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Add message to conversation history.

        Args:
            conversation_id: Conversation identifier
            message_id: Message identifier
            role: Message role ("user", "assistant", "system")
            content: Message content
            agent_type: Agent that generated message (if assistant)
            metadata: Additional metadata
        """
        message = ConversationMessage(
            message_id=message_id,
            role=role,
            content=content,
            agent_type=agent_type,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )

        await self._storage.add_message(conversation_id, message)

        # Enforce history limit
        await self._enforce_history_limit(conversation_id)

    async def get_conversation_context(
        self,
        conversation_id: ConversationId,
        max_messages: int | None = None,
    ) -> "ConversationContext":
        """
        Get conversation context for agent.

        Args:
            conversation_id: Conversation identifier
            max_messages: Maximum messages to retrieve (default: history_limit)

        Returns:
            ConversationContext with history and metadata
        """
        limit = max_messages or self._history_limit

        # Get recent messages
        messages = await self._storage.get_messages(conversation_id, limit=limit)

        # Get conversation metadata
        metadata = await self._storage.get_metadata(conversation_id)

        # Build context
        from .intent_classifier import ConversationContext

        return ConversationContext(
            conversation_history=[msg.to_dict() for msg in messages],
            user_metadata=metadata.get("user", {}),
            session_metadata=metadata.get("session", {}),
        )

    async def get_summary(
        self,
        conversation_id: ConversationId,
    ) -> str:
        """
        Get conversation summary (for new agents joining).

        Args:
            conversation_id: Conversation identifier

        Returns:
            Summary of conversation so far
        """
        # Get recent messages
        messages = await self._storage.get_messages(conversation_id, limit=10)

        if not messages:
            return "No previous conversation history."

        # Build summary
        summary_parts = [f"Conversation summary ({len(messages)} recent messages):"]

        for msg in messages:
            agent_info = f" [{msg.agent_type.value}]" if msg.agent_type else ""
            summary_parts.append(f"- {msg.role}{agent_info}: {msg.content[:100]}...")

        return "\n".join(summary_parts)

    async def update_metadata(
        self,
        conversation_id: ConversationId,
        user_metadata: dict | None = None,
        session_metadata: dict | None = None,
    ) -> None:
        """
        Update conversation metadata.

        Args:
            conversation_id: Conversation identifier
            user_metadata: User-related metadata
            session_metadata: Session-related metadata
        """
        await self._storage.update_metadata(
            conversation_id,
            user_metadata=user_metadata,
            session_metadata=session_metadata,
        )

    async def clear_history(
        self,
        conversation_id: ConversationId,
    ) -> None:
        """
        Clear conversation history.

        Args:
            conversation_id: Conversation identifier
        """
        await self._storage.clear_messages(conversation_id)

    async def _enforce_history_limit(
        self,
        conversation_id: ConversationId,
    ) -> None:
        """Enforce history limit (keep only last N messages)."""
        message_count = await self._storage.get_message_count(conversation_id)

        if message_count > self._history_limit:
            # Remove oldest messages
            remove_count = message_count - self._history_limit
            await self._storage.remove_oldest_messages(conversation_id, remove_count)

    async def estimate_token_count(
        self,
        conversation_id: ConversationId,
    ) -> int:
        """
        Estimate token count for conversation context.

        Rough estimation: ~4 characters per token.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Estimated token count
        """
        messages = await self._storage.get_messages(
            conversation_id, limit=self._history_limit
        )

        total_chars = sum(len(msg.content) for msg in messages)
        estimated_tokens = total_chars // 4  # Rough estimate

        return estimated_tokens


# Port (interface) for dependency injection


class ContextStoragePort(Protocol):
    """Port for context storage (Redis/PostgreSQL)."""

    async def add_message(
        self,
        conversation_id: ConversationId,
        message: ConversationMessage,
    ) -> None:
        """Add message to conversation history."""
        ...

    async def get_messages(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[ConversationMessage]:
        """Get recent messages."""
        ...

    async def get_metadata(
        self,
        conversation_id: ConversationId,
    ) -> dict:
        """Get conversation metadata."""
        ...

    async def update_metadata(
        self,
        conversation_id: ConversationId,
        user_metadata: dict | None,
        session_metadata: dict | None,
    ) -> None:
        """Update conversation metadata."""
        ...

    async def clear_messages(
        self,
        conversation_id: ConversationId,
    ) -> None:
        """Clear conversation history."""
        ...

    async def get_message_count(
        self,
        conversation_id: ConversationId,
    ) -> int:
        """Get message count."""
        ...

    async def remove_oldest_messages(
        self,
        conversation_id: ConversationId,
        count: int,
    ) -> None:
        """Remove oldest messages."""
        ...
