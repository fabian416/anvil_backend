"""
Guest Conversation entity.

Represents a chat conversation for a guest user.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from uuid import UUID, uuid4


class GuestConversationStatus(str, Enum):
    """Status of a guest conversation."""

    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass
class GuestConversation:
    """
    Guest conversation entity.

    Auto-created for new/archived IPs, archived hourly by Celery.
    """

    id: UUID = field(default_factory=uuid4)
    guest_user_id: UUID = field(default_factory=uuid4)
    title: str | None = None
    status: GuestConversationStatus = GuestConversationStatus.ACTIVE
    message_count: int = 0
    language: str = "en"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    archived_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == GuestConversationStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
        """Check if conversation is archived."""
        return self.status == GuestConversationStatus.ARCHIVED

    def increment_messages(self) -> None:
        """Increment message count."""
        self.message_count += 1
        self.updated_at = datetime.now(UTC)

    def archive(self) -> None:
        """Archive this conversation."""
        self.status = GuestConversationStatus.ARCHIVED
        self.archived_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def set_title(self, title: str) -> None:
        """Set conversation title."""
        self.title = title[:255] if title else None
        self.updated_at = datetime.now(UTC)
