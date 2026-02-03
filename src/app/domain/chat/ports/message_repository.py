"""
Repository port for message persistence.
"""

from typing import Protocol, List, Optional
from uuid import UUID

from app.domain.entities.message import Message


class MessageRepository(Protocol):
    """
    Repository for persisting chat messages.

    This port defines the interface for message storage operations,
    allowing the domain layer to remain independent of persistence details.
    """

    async def save(self, message: Message) -> None:
        """
        Save a message to the repository.

        Args:
            message: Message entity to persist
        """
        ...

    async def get(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message entity or None if not found
        """
        ...

    async def get_by_conversation(
        self, conversation_id: UUID, limit: int = 50
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
