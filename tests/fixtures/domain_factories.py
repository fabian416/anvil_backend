"""
Domain entity factories for tests.

Provides factory functions for creating test instances of domain entities
with sensible defaults.
"""

from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List


class ConversationFactory:
    """Factory for creating test Conversation entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        messages: Optional[List] = None,
        **kwargs,
    ):
        """
        Create a test conversation with sensible defaults.

        Args:
            id: Conversation ID (generates new UUID if not provided)
            user_id: User ID (generates new UUID if not provided)
            title: Conversation title (default: "Test Conversation")
            created_at: Creation timestamp (default: now)
            updated_at: Update timestamp (default: now)
            messages: List of messages (default: empty list)
            **kwargs: Additional attributes

        Returns:
            Mock conversation object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            user_id=user_id or uuid4(),
            title=title or "Test Conversation",
            created_at=created_at or datetime.utcnow(),
            updated_at=updated_at or datetime.utcnow(),
            messages=messages or [],
            **kwargs,
        )


class MessageFactory:
    """Factory for creating test Message entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        content: Optional[str] = None,
        role: str = "USER",
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        """
        Create a test message with sensible defaults.

        Args:
            id: Message ID (generates new UUID if not provided)
            conversation_id: Conversation ID (generates new UUID if not provided)
            content: Message content (default: "Test message content")
            role: Message role (default: "USER")
            created_at: Creation timestamp (default: now)
            **kwargs: Additional attributes

        Returns:
            Mock message object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            conversation_id=conversation_id or uuid4(),
            content=content or "Test message content",
            role=role,
            created_at=created_at or datetime.utcnow(),
            **kwargs,
        )


class UserFactory:
    """Factory for creating test User entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        is_active: bool = True,
        role: str = "USER",
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        """
        Create a test user with sensible defaults.

        Args:
            id: User ID (generates new UUID if not provided)
            email: User email (default: "test@example.com")
            name: User name (default: "Test User")
            is_active: User active status (default: True)
            role: User role (default: "USER")
            created_at: Creation timestamp (default: now)
            **kwargs: Additional attributes

        Returns:
            Mock user object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            email=email or f"test-{uuid4().hex[:8]}@example.com",
            name=name or "Test User",
            is_active=is_active,
            role=role,
            created_at=created_at or datetime.utcnow(),
            **kwargs,
        )


class AgentFactory:
    """Factory for creating test Agent entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        agent_type: str = "TRADING",
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        **kwargs,
    ):
        """
        Create a test agent with sensible defaults.

        Args:
            id: Agent ID (generates new UUID if not provided)
            agent_type: Agent type (default: "TRADING")
            name: Agent name (default: "Test Trading Agent")
            description: Agent description
            is_active: Agent active status (default: True)
            **kwargs: Additional attributes

        Returns:
            Mock agent object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            agent_type=agent_type,
            name=name or f"Test {agent_type.title()} Agent",
            description=description or f"Test {agent_type.lower()} agent for testing",
            is_active=is_active,
            **kwargs,
        )


class AgentSessionFactory:
    """Factory for creating test AgentSession entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None,
        state: Optional[dict] = None,
        created_at: Optional[datetime] = None,
        **kwargs,
    ):
        """
        Create a test agent session with sensible defaults.

        Args:
            id: Session ID (generates new UUID if not provided)
            conversation_id: Conversation ID (generates new UUID if not provided)
            agent_id: Agent ID (generates new UUID if not provided)
            state: Session state (default: empty dict)
            created_at: Creation timestamp (default: now)
            **kwargs: Additional attributes

        Returns:
            Mock agent session object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            conversation_id=conversation_id or uuid4(),
            agent_id=agent_id or uuid4(),
            state=state or {},
            created_at=created_at or datetime.utcnow(),
            **kwargs,
        )


class ProtocolFactory:
    """Factory for creating test Protocol entities."""

    @staticmethod
    def create(
        id: Optional[UUID] = None,
        name: Optional[str] = None,
        risk_score: float = 3.5,
        tvl: float = 1000000000.0,
        category: str = "LENDING",
        chain: str = "ethereum",
        **kwargs,
    ):
        """
        Create a test protocol with sensible defaults.

        Args:
            id: Protocol ID (generates new UUID if not provided)
            name: Protocol name (default: "Test Protocol")
            risk_score: Risk score 0-10 (default: 3.5)
            tvl: Total Value Locked (default: 1B)
            category: Protocol category (default: "LENDING")
            chain: Blockchain (default: "ethereum")
            **kwargs: Additional attributes

        Returns:
            Mock protocol object with all attributes
        """
        from types import SimpleNamespace

        return SimpleNamespace(
            id=id or uuid4(),
            name=name or f"Test Protocol {uuid4().hex[:8]}",
            risk_score=risk_score,
            tvl=tvl,
            category=category,
            chain=chain,
            **kwargs,
        )
