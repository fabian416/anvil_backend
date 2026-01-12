"""Repository ports for authenticated chat domain.

This module defines the interfaces (ports) for chat persistence operations,
following hexagonal architecture principles. Concrete implementations will be
in the infrastructure layer.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from app.domain.chat.entities import ChatUser, ChatConversation, ChatMessage


class ChatUserRepository(ABC):
    """Repository interface for ChatUser persistence."""

    @abstractmethod
    async def create(self, chat_user: ChatUser) -> ChatUser:
        """Create a new chat user.

        Args:
            chat_user: ChatUser entity to create

        Returns:
            Created ChatUser with generated ID

        Raises:
            IntegrityError: If user_id already exists
        """
        pass

    @abstractmethod
    async def get_by_id(self, chat_user_id: UUID) -> Optional[ChatUser]:
        """Get chat user by UUID.

        Args:
            chat_user_id: Chat user UUID

        Returns:
            ChatUser if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[ChatUser]:
        """Get chat user by legacy user ID.

        Args:
            user_id: Legacy users table ID (INTEGER)

        Returns:
            ChatUser if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[ChatUser]:
        """Get chat user by email.

        Args:
            email: User email address

        Returns:
            ChatUser if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, chat_user: ChatUser) -> ChatUser:
        """Update existing chat user.

        Args:
            chat_user: ChatUser entity with updated fields

        Returns:
            Updated ChatUser

        Raises:
            NotFoundError: If chat user doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, chat_user_id: UUID) -> None:
        """Delete chat user by ID.

        Args:
            chat_user_id: Chat user UUID

        Note:
            This will cascade delete all conversations and messages
        """
        pass

    @abstractmethod
    async def update_last_seen(self, chat_user_id: UUID) -> None:
        """Update last seen timestamp for chat user.

        Args:
            chat_user_id: Chat user UUID
        """
        pass

    @abstractmethod
    async def increment_message_count(self, chat_user_id: UUID) -> None:
        """Increment total message count for chat user.

        Args:
            chat_user_id: Chat user UUID
        """
        pass


class ChatConversationRepository(ABC):
    """Repository interface for ChatConversation persistence."""

    @abstractmethod
    async def create(self, conversation: ChatConversation) -> ChatConversation:
        """Create a new conversation.

        Args:
            conversation: ChatConversation entity to create

        Returns:
            Created ChatConversation with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Optional[ChatConversation]:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation UUID

        Returns:
            ChatConversation if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_active_conversation(
        self, chat_user_id: UUID, language: str
    ) -> Optional[ChatConversation]:
        """Get the most recent active conversation for a user in a language.

        Args:
            chat_user_id: Chat user UUID
            language: Language code (en, es, pt, zh)

        Returns:
            Most recent active ChatConversation, or None if no active conversation
        """
        pass

    @abstractmethod
    async def list_by_user(
        self,
        chat_user_id: UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatConversation]:
        """List conversations for a user.

        Args:
            chat_user_id: Chat user UUID
            status: Filter by status (active/archived), or None for all
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip

        Returns:
            List of ChatConversations ordered by updated_at DESC
        """
        pass

    @abstractmethod
    async def update(self, conversation: ChatConversation) -> ChatConversation:
        """Update existing conversation.

        Args:
            conversation: ChatConversation entity with updated fields

        Returns:
            Updated ChatConversation

        Raises:
            NotFoundError: If conversation doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, conversation_id: UUID) -> None:
        """Delete conversation by ID.

        Args:
            conversation_id: Conversation UUID

        Note:
            This will cascade delete all messages
        """
        pass

    @abstractmethod
    async def archive(self, conversation_id: UUID) -> None:
        """Archive a conversation.

        Args:
            conversation_id: Conversation UUID
        """
        pass

    @abstractmethod
    async def unarchive(self, conversation_id: UUID) -> None:
        """Restore an archived conversation.

        Args:
            conversation_id: Conversation UUID
        """
        pass

    @abstractmethod
    async def increment_message_count(self, conversation_id: UUID) -> None:
        """Increment message count for conversation.

        Args:
            conversation_id: Conversation UUID
        """
        pass


class ChatMessageRepository(ABC):
    """Repository interface for ChatMessage persistence."""

    @abstractmethod
    async def create(self, message: ChatMessage) -> ChatMessage:
        """Create a new message.

        Args:
            message: ChatMessage entity to create

        Returns:
            Created ChatMessage with generated ID
        """
        pass

    @abstractmethod
    async def get_by_id(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get message by ID.

        Args:
            message_id: Message UUID

        Returns:
            ChatMessage if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_by_conversation(
        self,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """List messages in a conversation.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of ChatMessages ordered by created_at ASC
        """
        pass

    @abstractmethod
    async def list_by_conversation_since(
        self,
        conversation_id: UUID,
        since: datetime,
    ) -> List[ChatMessage]:
        """List messages in a conversation since a timestamp.

        Args:
            conversation_id: Conversation UUID
            since: Timestamp to fetch messages after

        Returns:
            List of ChatMessages created after 'since', ordered by created_at ASC
        """
        pass

    @abstractmethod
    async def count_by_conversation(self, conversation_id: UUID) -> int:
        """Count messages in a conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Total message count
        """
        pass

    @abstractmethod
    async def delete(self, message_id: UUID) -> None:
        """Delete message by ID.

        Args:
            message_id: Message UUID
        """
        pass

    @abstractmethod
    async def delete_by_conversation(self, conversation_id: UUID) -> None:
        """Delete all messages in a conversation.

        Args:
            conversation_id: Conversation UUID
        """
        pass

    @abstractmethod
    async def get_latest_by_conversation(
        self, conversation_id: UUID
    ) -> Optional[ChatMessage]:
        """Get the most recent message in a conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Latest ChatMessage, or None if conversation is empty
        """
        pass

    @abstractmethod
    async def search_by_intent(
        self,
        chat_user_id: UUID,
        intent: str,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Search messages by Hunter AI intent.

        Args:
            chat_user_id: Chat user UUID (to scope search)
            intent: Intent to search for (hunter_sentiment, etc.)
            limit: Maximum number of messages to return

        Returns:
            List of ChatMessages with matching intent, ordered by created_at DESC
        """
        pass
