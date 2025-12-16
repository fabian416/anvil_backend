"""
Offline queue adapter port.

Domain-defined interface for offline message queuing systems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.value_objects.chat.performance import OfflineQueueEntry


class OfflineQueueAdapter(ABC):
    """
    Port for offline message queuing.

    Handles message queuing when connection is unavailable
    and automatic retry when connection is restored.
    """

    @abstractmethod
    async def enqueue(self, entry: OfflineQueueEntry) -> bool:
        """
        Add message to offline queue.

        Args:
            entry: Queue entry to add

        Returns:
            True if enqueued successfully
        """
        pass

    @abstractmethod
    async def dequeue(self, user_id: UUID, limit: int = 10) -> List[OfflineQueueEntry]:
        """
        Get messages from queue for user.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to retrieve

        Returns:
            List of queued entries (ordered by priority, then creation time)
        """
        pass

    @abstractmethod
    async def remove(self, entry_id: UUID) -> bool:
        """
        Remove entry from queue.

        Args:
            entry_id: Entry identifier

        Returns:
            True if removed, False if not found
        """
        pass

    @abstractmethod
    async def get_queue_size(self, user_id: UUID) -> int:
        """
        Get number of pending messages for user.

        Args:
            user_id: User identifier

        Returns:
            Number of queued messages
        """
        pass

    @abstractmethod
    async def clear_user_queue(self, user_id: UUID) -> int:
        """
        Clear all queued messages for user.

        Args:
            user_id: User identifier

        Returns:
            Number of entries cleared
        """
        pass

    @abstractmethod
    async def update_retry_count(self, entry_id: UUID) -> Optional[OfflineQueueEntry]:
        """
        Increment retry count for entry.

        Args:
            entry_id: Entry identifier

        Returns:
            Updated entry or None if not found
        """
        pass

    @abstractmethod
    async def get_failed_entries(self, user_id: UUID) -> List[OfflineQueueEntry]:
        """
        Get entries that have exceeded max retries.

        Args:
            user_id: User identifier

        Returns:
            List of failed entries
        """
        pass
