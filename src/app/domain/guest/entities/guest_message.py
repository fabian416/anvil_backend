"""
Guest Message entity.

Represents a message in a guest conversation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class GuestMessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class GuestMessage:
    """
    Guest message entity.

    Stores chat messages for guest conversations.
    """

    id: UUID = field(default_factory=uuid4)
    conversation_id: UUID = field(default_factory=uuid4)
    role: GuestMessageRole = GuestMessageRole.USER
    content: str = ""
    intent: str | None = None
    handler: str | None = None
    confidence: float | None = None
    language: str = "en"
    is_restricted_action: bool = False
    metadata: dict | None = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create_user_message(
        cls,
        conversation_id: UUID,
        content: str,
        language: str = "en",
    ) -> "GuestMessage":
        """Create a user message."""
        return cls(
            conversation_id=conversation_id,
            role=GuestMessageRole.USER,
            content=content,
            language=language,
        )

    @classmethod
    def create_assistant_message(
        cls,
        conversation_id: UUID,
        content: str,
        intent: str | None = None,
        handler: str | None = None,
        confidence: float | None = None,
        language: str = "en",
        is_restricted_action: bool = False,
        metadata: dict | None = None,
    ) -> "GuestMessage":
        """Create an assistant message."""
        return cls(
            conversation_id=conversation_id,
            role=GuestMessageRole.ASSISTANT,
            content=content,
            intent=intent,
            handler=handler,
            confidence=confidence,
            language=language,
            is_restricted_action=is_restricted_action,
            metadata=metadata or {},
        )
