"""
Message entity for chat messages.
"""

from datetime import datetime, UTC
from typing import Dict, Optional, Any
from uuid import UUID, uuid4

from app.domain.chat.value_objects.message_role import MessageRole


class Message:
    """
    Message entity representing a single message in a conversation.

    Messages can be from users or agents.
    """

    def __init__(
        self,
        id: UUID,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        agent_type: Optional[str] = None,
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize message.

        Args:
            id: Message identifier
            conversation_id: Parent conversation identifier
            role: Message role (user/agent/system)
            content: Message content
            agent_type: Optional agent type if from agent
            created_at: Creation timestamp
            metadata: Optional metadata dictionary (e.g., distillation info)
        """
        self.id = id
        self.conversation_id = conversation_id
        self.role = role
        self.content = content
        self.agent_type = agent_type
        self.created_at = created_at or datetime.now(UTC)
        self.metadata = metadata or {}

    @classmethod
    def create(
        cls,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """
        Create a new message with auto-generated ID and timestamp.

        Args:
            conversation_id: Parent conversation identifier
            role: Message role (user/agent/system)
            content: Message content
            agent_type: Optional agent type if from agent
            metadata: Optional metadata dictionary

        Returns:
            New message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_type=agent_type,
            metadata=metadata,
        )

    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
    ) -> "Message":
        """
        Create a user message.

        Args:
            conversation_id: Parent conversation identifier
            content: Message content

        Returns:
            New user message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

    @classmethod
    def create_agent_message(
        cls,
        conversation_id: UUID,
        content: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Message":
        """
        Create an agent message.

        Args:
            conversation_id: Parent conversation identifier
            content: Message content
            agent_type: Optional agent type
            metadata: Optional metadata dictionary

        Returns:
            New agent message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.AGENT,
            content=content,
            agent_type=agent_type,
            metadata=metadata,
        )

    @classmethod
    def create_system_message(
        cls,
        conversation_id: UUID,
        content: str,
    ) -> "Message":
        """
        Create a system message.

        Args:
            conversation_id: Parent conversation identifier
            content: Message content

        Returns:
            New system message instance
        """
        return cls(
            id=uuid4(),
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=content,
        )
