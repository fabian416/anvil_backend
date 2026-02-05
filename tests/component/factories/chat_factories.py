"""
Test data factories for chat domain.

Provides convenient factory methods for creating test conversations,
messages, and related entities with sensible defaults.

Design Principles:
- Sensible defaults (minimize test setup code)
- Override capability (customize when needed)
- Batch creation (create multiple entities easily)
- Helper methods (create_user_message, create_agent_message)

Usage:
    >>> factory = ConversationFactory()
    >>> conversation = factory.create(user_id=123, title="Test")
    >>> messages = factory.create_batch(count=5, user_id=123)
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.chat.value_objects.message_role import MessageRole
from app.domain.common.datetime_utils import utc_now


class ConversationFactory:
    """
    Factory for creating test conversations.

    Provides convenient methods for creating conversations with
    sensible defaults and override capability.
    """

    def create(
        self,
        id: Optional[UUID] = None,
        user_id: int = 123,
        title: Optional[str] = "Test Conversation",
        project_id: Optional[UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> Conversation:
        """
        Create a test conversation.

        Args:
            id: Conversation ID (default: random UUID)
            user_id: User ID (default: 123)
            title: Conversation title (default: "Test Conversation")
            project_id: Optional project ID
            created_at: Creation timestamp (default: now)
            updated_at: Update timestamp (default: now)

        Returns:
            Conversation entity

        Example:
            >>> factory = ConversationFactory()
            >>> conversation = factory.create(user_id=456, title="DeFi Questions")
        """
        return Conversation(
            id=id or uuid4(),
            user_id=user_id,
            title=title,
            project_id=project_id,
            created_at=created_at or utc_now(),
            updated_at=updated_at or utc_now(),
        )

    def create_batch(
        self,
        count: int,
        **kwargs,
    ) -> List[Conversation]:
        """
        Create multiple conversations.

        Args:
            count: Number of conversations to create
            **kwargs: Arguments passed to create()

        Returns:
            List of conversation entities

        Example:
            >>> factory = ConversationFactory()
            >>> conversations = factory.create_batch(count=5, user_id=123)
        """
        return [self.create(**kwargs) for _ in range(count)]

    def create_for_user(
        self,
        user_id: int,
        count: int = 1,
    ) -> List[Conversation]:
        """
        Create conversations for a specific user.

        Args:
            user_id: User ID
            count: Number of conversations to create

        Returns:
            List of conversation entities

        Example:
            >>> factory = ConversationFactory()
            >>> conversations = factory.create_for_user(user_id=123, count=3)
        """
        return self.create_batch(count=count, user_id=user_id)


class MessageFactory:
    """
    Factory for creating test messages.

    Provides convenient methods for creating messages with
    different roles and content.
    """

    def create(
        self,
        id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        role: str = "user",
        content: str = "Test message",
        agent_type: Optional[str] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Create a test message.

        Args:
            id: Message ID (default: random UUID)
            conversation_id: Parent conversation ID (default: random UUID)
            role: Message role - "user", "agent", or "system" (default: "user")
            content: Message content (default: "Test message")
            agent_type: Optional agent type (e.g., "HUNTER_AI")
            created_at: Creation timestamp (default: now)
            metadata: Optional metadata dictionary

        Returns:
            Message entity

        Example:
            >>> factory = MessageFactory()
            >>> message = factory.create(
            ...     conversation_id=conversation.id,
            ...     role="user",
            ...     content="What is DeFi?",
            ... )
        """
        return Message(
            id=id or uuid4(),
            conversation_id=conversation_id or uuid4(),
            role=MessageRole(role),
            content=content,
            agent_type=agent_type,
            created_at=created_at or utc_now(),
            metadata=metadata or {},
        )

    def create_user_message(
        self,
        conversation_id: UUID,
        content: str = "Hello",
    ) -> Message:
        """
        Create a user message.

        Args:
            conversation_id: Parent conversation ID
            content: Message content

        Returns:
            User message entity

        Example:
            >>> factory = MessageFactory()
            >>> message = factory.create_user_message(
            ...     conversation_id=conversation.id,
            ...     content="What is DeFi?",
            ... )
        """
        return self.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    def create_agent_message(
        self,
        conversation_id: UUID,
        content: str = "I'm happy to help!",
        agent_type: Optional[str] = None,
    ) -> Message:
        """
        Create an agent message.

        Args:
            conversation_id: Parent conversation ID
            content: Message content
            agent_type: Optional agent type (e.g., "HUNTER_AI")

        Returns:
            Agent message entity

        Example:
            >>> factory = MessageFactory()
            >>> message = factory.create_agent_message(
            ...     conversation_id=conversation.id,
            ...     content="DeFi stands for Decentralized Finance...",
            ...     agent_type="CHAT",
            ... )
        """
        return self.create(
            conversation_id=conversation_id,
            role="agent",
            content=content,
            agent_type=agent_type,
        )

    def create_system_message(
        self,
        conversation_id: UUID,
        content: str = "System message",
    ) -> Message:
        """
        Create a system message.

        Args:
            conversation_id: Parent conversation ID
            content: Message content

        Returns:
            System message entity

        Example:
            >>> factory = MessageFactory()
            >>> message = factory.create_system_message(
            ...     conversation_id=conversation.id,
            ...     content="Conversation started",
            ... )
        """
        return self.create(
            conversation_id=conversation_id,
            role="system",
            content=content,
        )

    def create_conversation_history(
        self,
        conversation_id: UUID,
        turns: List[tuple[str, str]],
    ) -> List[Message]:
        """
        Create a conversation history.

        Args:
            conversation_id: Parent conversation ID
            turns: List of (user_message, agent_response) tuples

        Returns:
            List of message entities (alternating user/agent)

        Example:
            >>> factory = MessageFactory()
            >>> messages = factory.create_conversation_history(
            ...     conversation_id=conversation.id,
            ...     turns=[
            ...         ("Hello", "Hi! How can I help you?"),
            ...         ("What is DeFi?", "DeFi is decentralized finance..."),
            ...     ],
            ... )
            >>> assert len(messages) == 4  # 2 turns = 4 messages
        """
        messages = []
        for user_msg, agent_msg in turns:
            messages.append(self.create_user_message(conversation_id, user_msg))
            messages.append(self.create_agent_message(conversation_id, agent_msg))
        return messages

    def create_batch(
        self,
        count: int,
        **kwargs,
    ) -> List[Message]:
        """
        Create multiple messages.

        Args:
            count: Number of messages to create
            **kwargs: Arguments passed to create()

        Returns:
            List of message entities

        Example:
            >>> factory = MessageFactory()
            >>> messages = factory.create_batch(
            ...     count=5,
            ...     conversation_id=conversation.id,
            ...     role="user",
            ... )
        """
        return [self.create(**kwargs) for _ in range(count)]


class UserFactory:
    """
    Factory for creating test users.

    Provides convenient methods for creating users with sensible defaults.
    Note: User entity may not exist in this simplified system, placeholder for future.
    """

    def create(
        self,
        id: int = 123,
        email: str = "test@example.com",
        first_name: str = "Test",
        last_name: str = "User",
    ) -> dict:
        """
        Create a test user (as dictionary).

        Args:
            id: User ID
            email: User email
            first_name: User first name
            last_name: User last name

        Returns:
            User dictionary

        Example:
            >>> factory = UserFactory()
            >>> user = factory.create(id=456, email="alice@example.com")
        """
        return {
            "id": id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }
