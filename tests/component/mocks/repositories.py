"""
In-memory repository implementations for component tests.

These repositories implement the same port interfaces as production repositories
but store data in memory for fast, isolated testing.

Design Principles:
- Deep copy for mutation safety (prevent test contamination)
- Full async support (match production interface)
- Simple storage (dict/list, not database)
- Clear() method for test utilities

Performance:
- ~0.01ms per operation (vs ~100ms for real DB)
- No network overhead
- No transaction overhead
"""

from typing import List, Optional, Dict
from uuid import UUID
from copy import deepcopy
from datetime import datetime

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message


class InMemoryConversationRepository:
    """
    In-memory conversation repository.

    Stores conversations in a dictionary for O(1) lookups.
    Implements ConversationRepository port interface.

    Thread Safety: Not thread-safe (not needed for tests)
    Isolation: Deep copy prevents mutation issues
    """

    def __init__(self):
        """Initialize empty storage."""
        self._storage: Dict[UUID, Conversation] = {}

    async def add_conversation(self, conversation: Conversation) -> None:
        """
        Add a new conversation.

        Args:
            conversation: Conversation entity to persist

        Note: Uses deep copy to prevent mutations affecting stored entity
        """
        # Deep copy to prevent test mutations from affecting storage
        self._storage[conversation.id] = deepcopy(conversation)

    async def update_conversation(self, conversation: Conversation) -> None:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation entity to update

        Note: Overwrites existing conversation with same ID
        """
        self._storage[conversation.id] = deepcopy(conversation)

    async def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation entity or None if not found

        Note: Returns deep copy to prevent mutations
        """
        conversation = self._storage.get(conversation_id)
        return deepcopy(conversation) if conversation else None

    async def list_conversations(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Conversation]:
        """
        List conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            offset: Offset for pagination

        Returns:
            List of conversation entities, sorted by created_at descending

        Note: Returns deep copies to prevent mutations
        """
        # Filter by user_id
        user_conversations = [
            c for c in self._storage.values()
            if c.user_id == user_id
        ]

        # Sort by created_at descending (most recent first)
        user_conversations.sort(
            key=lambda c: c.created_at,
            reverse=True,
        )

        # Apply pagination
        paginated = user_conversations[offset:offset + limit]

        # Return deep copies
        return [deepcopy(c) for c in paginated]

    async def add_message(self, message: Message) -> None:
        """
        Add a message to a conversation.

        Args:
            message: Message entity to persist

        Note: This is a convenience method for the combined repository interface.
              Messages are actually stored in InMemoryMessageRepository.
        """
        # This method exists for interface compatibility
        # Actual message storage happens in InMemoryMessageRepository
        pass

    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message entity or None if not found

        Note: This is a convenience method. Use InMemoryMessageRepository instead.
        """
        # This method exists for interface compatibility
        # Actual message retrieval happens in InMemoryMessageRepository
        return None

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> List[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return

        Returns:
            List of message entities

        Note: This is a convenience method. Use InMemoryMessageRepository instead.
        """
        # This method exists for interface compatibility
        # Actual message listing happens in InMemoryMessageRepository
        return []

    def clear(self):
        """
        Clear all stored conversations.

        Utility method for test cleanup between tests.
        Not part of production interface.
        """
        self._storage.clear()

    def count(self) -> int:
        """
        Get total number of conversations.

        Utility method for test assertions.
        Not part of production interface.
        """
        return len(self._storage)


class InMemoryMessageRepository:
    """
    In-memory message repository.

    Stores messages in a list for chronological ordering.
    Implements MessageRepository port interface.

    Storage Strategy:
    - List storage (preserves insertion order)
    - Linear search for get_by_id (acceptable for test data size)
    - Filter + sort for get_by_conversation
    """

    def __init__(self):
        """Initialize empty storage."""
        self._storage: List[Message] = []

    async def save(self, message: Message) -> None:
        """
        Save a message to the repository.

        Args:
            message: Message entity to persist

        Note: If message with same ID exists, replaces it (upsert behavior)
        """
        # Remove existing message with same ID (upsert behavior)
        self._storage = [m for m in self._storage if m.id != message.id]

        # Add new message (deep copy for safety)
        self._storage.append(deepcopy(message))

    async def get(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: Message identifier

        Returns:
            Message entity or None if not found

        Note: Linear search, O(n) complexity (acceptable for test data)
        """
        for msg in self._storage:
            if msg.id == message_id:
                return deepcopy(msg)
        return None

    async def get_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 50,
    ) -> List[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return

        Returns:
            List of message entities, ordered by created_at ascending (oldest first)

        Note: Chronological order matches chat UI expectations
        """
        # Filter by conversation_id
        conversation_messages = [
            m for m in self._storage
            if m.conversation_id == conversation_id
        ]

        # Sort by created_at ascending (chronological order)
        conversation_messages.sort(key=lambda m: m.created_at)

        # Apply limit
        if limit:
            conversation_messages = conversation_messages[:limit]

        # Return deep copies
        return [deepcopy(m) for m in conversation_messages]

    def clear(self):
        """
        Clear all stored messages.

        Utility method for test cleanup.
        Not part of production interface.
        """
        self._storage.clear()

    def count(self) -> int:
        """
        Get total number of messages.

        Utility method for test assertions.
        Not part of production interface.
        """
        return len(self._storage)

    def count_by_conversation(self, conversation_id: UUID) -> int:
        """
        Count messages in a conversation.

        Utility method for test assertions.
        Not part of production interface.
        """
        return sum(
            1 for m in self._storage
            if m.conversation_id == conversation_id
        )
