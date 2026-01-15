"""
Chat Conversation Entity.

Unified conversation entity with full CRUD support.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class ConversationStatus(str, Enum):
    """Conversation status."""
    
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class ChatConversation:
    """
    Unified conversation entity.
    
    Supports conversations for both guest and authenticated users
    with full lifecycle management.
    """
    
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str | None = None
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_message_at: datetime | None = None
    message_count: int = 0
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        title: str | None = None,
        language: str = "en",
    ) -> "ChatConversation":
        """Create a new conversation."""
        return cls(
            user_id=user_id,
            title=title,
            language=language,
        )
    
    def increment_messages(self) -> None:
        """Increment message count and update timestamps."""
        self.message_count += 1
        self.updated_at = datetime.now(UTC)
        self.last_message_at = datetime.now(UTC)
    
    def set_title(self, title: str) -> None:
        """Set conversation title."""
        self.title = title
        self.updated_at = datetime.now(UTC)
    
    def archive(self) -> None:
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.now(UTC)
    
    def delete(self) -> None:
        """Mark conversation as deleted."""
        self.status = ConversationStatus.DELETED
        self.updated_at = datetime.now(UTC)
    
    def reactivate(self) -> None:
        """Reactivate an archived conversation."""
        if self.status == ConversationStatus.ARCHIVED:
            self.status = ConversationStatus.ACTIVE
            self.updated_at = datetime.now(UTC)
    
    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE
    
    @property
    def is_archived(self) -> bool:
        """Check if conversation is archived."""
        return self.status == ConversationStatus.ARCHIVED
    
    @property
    def is_deleted(self) -> bool:
        """Check if conversation is deleted."""
        return self.status == ConversationStatus.DELETED
    
    def auto_generate_title(self, first_message: str) -> None:
        """Auto-generate title from first message."""
        if not self.title and first_message:
            # Truncate to first 50 chars
            title = first_message[:50]
            if len(first_message) > 50:
                title += "..."
            self.title = title
            self.updated_at = datetime.now(UTC)

