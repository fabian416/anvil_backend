"""
Conversation export repository port.

Domain-defined interface for conversation export persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.chat.conversation_export import ConversationExport


class ExportRepository(ABC):
    """
    Port for conversation export persistence.

    Abstracts storage and retrieval of conversation export records.
    """

    @abstractmethod
    async def save(self, export: ConversationExport) -> ConversationExport:
        """
        Save or update export record.

        Args:
            export: Export entity to save

        Returns:
            Saved export entity
        """
        pass

    @abstractmethod
    async def get_by_id(self, export_id: UUID) -> Optional[ConversationExport]:
        """
        Get export by ID.

        Args:
            export_id: Export identifier

        Returns:
            ConversationExport or None if not found
        """
        pass

    @abstractmethod
    async def get_by_conversation(
        self, conversation_id: UUID
    ) -> List[ConversationExport]:
        """
        Get all exports for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            List of exports for the conversation
        """
        pass

    @abstractmethod
    async def get_by_user(
        self, user_id: UUID, limit: int = 50
    ) -> List[ConversationExport]:
        """
        Get exports created by user.

        Args:
            user_id: User identifier
            limit: Maximum number of exports to return

        Returns:
            List of user's exports (most recent first)
        """
        pass

    @abstractmethod
    async def get_pending_exports(self, limit: int = 100) -> List[ConversationExport]:
        """
        Get pending exports for processing.

        Args:
            limit: Maximum number of exports to return

        Returns:
            List of pending exports (oldest first)
        """
        pass

    @abstractmethod
    async def get_expired_exports(self, limit: int = 100) -> List[ConversationExport]:
        """
        Get completed exports that have expired.

        Args:
            limit: Maximum number of exports to return

        Returns:
            List of expired exports
        """
        pass

    @abstractmethod
    async def delete(self, export_id: UUID) -> bool:
        """
        Delete export record.

        Args:
            export_id: Export identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """
        Delete all expired export records.

        Returns:
            Number of exports deleted
        """
        pass
