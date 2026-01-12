"""Chat domain entities for authenticated users.

This module defines the core domain entities for the authenticated chat system,
mirroring the structure of guest chat but with permanent storage and richer features.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.entities.base import Entity


@dataclass(eq=False, kw_only=True)
class ChatUser(Entity[UUID]):
    """Authenticated chat user entity.

    Bridge between legacy users table (INTEGER id) and new chat system (UUID).
    Tracks chat-specific preferences and statistics for authenticated users.

    This is separate from the main User entity to isolate chat concerns and
    enable independent evolution of the chat domain.
    """

    user_id: int  # Foreign key to legacy users table
    email: str
    subscription_tier: str  # free, premium, enterprise
    total_messages: int = 0
    language: str = "en"
    chat_preferences: dict = None  # JSONB - UI preferences, notification settings, etc.
    first_seen_at: datetime = None
    last_seen_at: datetime = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        """Initialize default values."""
        if self.chat_preferences is None:
            self.chat_preferences = {}
        if self.first_seen_at is None:
            self.first_seen_at = datetime.utcnow()
        if self.last_seen_at is None:
            self.last_seen_at = datetime.utcnow()
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def update_last_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def increment_message_count(self) -> None:
        """Increment total message count."""
        self.total_messages += 1
        self.updated_at = datetime.utcnow()

    def update_subscription_tier(self, tier: str) -> None:
        """Update subscription tier.

        Args:
            tier: New tier (free, premium, enterprise)

        Raises:
            ValueError: If tier is invalid
        """
        valid_tiers = {"free", "premium", "enterprise"}
        if tier not in valid_tiers:
            raise ValueError(
                f"Invalid subscription tier: {tier}. Must be one of {valid_tiers}"
            )
        self.subscription_tier = tier
        self.updated_at = datetime.utcnow()

    def update_preferences(self, preferences: dict) -> None:
        """Update chat preferences.

        Args:
            preferences: New preferences (merged with existing)
        """
        self.chat_preferences = {**self.chat_preferences, **preferences}
        self.updated_at = datetime.utcnow()

    def is_premium(self) -> bool:
        """Check if user has premium tier or higher."""
        return self.subscription_tier in {"premium", "enterprise"}

    def is_enterprise(self) -> bool:
        """Check if user has enterprise tier."""
        return self.subscription_tier == "enterprise"


@dataclass(eq=False, kw_only=True)
class ChatConversation(Entity[UUID]):
    """Authenticated chat conversation entity.

    Represents a conversation between an authenticated user and the Hunter AI system.
    Permanent storage with richer metadata than guest conversations.
    """

    chat_user_id: UUID  # Foreign key to chat_users table
    title: Optional[str] = None
    status: str = "active"  # active, archived
    message_count: int = 0
    language: str = "en"
    created_at: datetime = None
    updated_at: datetime = None
    archived_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def increment_message_count(self) -> None:
        """Increment message count."""
        self.message_count += 1
        self.updated_at = datetime.utcnow()

    def update_title(self, title: str) -> None:
        """Update conversation title.

        Args:
            title: New conversation title
        """
        self.title = title
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive this conversation."""
        if self.status == "archived":
            return  # Already archived

        self.status = "archived"
        self.archived_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def unarchive(self) -> None:
        """Restore archived conversation to active status."""
        if self.status == "active":
            return  # Already active

        self.status = "active"
        self.archived_at = None
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == "active"

    def is_archived(self) -> bool:
        """Check if conversation is archived."""
        return self.status == "archived"


@dataclass(eq=False, kw_only=True)
class ChatMessage(Entity[UUID]):
    """Authenticated chat message entity.

    Represents a single message in an authenticated user conversation.
    Includes Hunter AI enrichment data and metadata.
    """

    conversation_id: UUID  # Foreign key to chat_conversations table
    role: str  # user, assistant
    content: str
    intent: Optional[str] = None  # Hunter AI intent (hunter_sentiment, etc.)
    handler: Optional[str] = None  # Handler that processed message
    confidence: Optional[float] = None  # Intent classification confidence
    language: str = "en"
    is_restricted_action: bool = False  # Whether message triggered restricted action
    metadata: dict = None  # JSONB - Hunter AI enrichment data
    created_at: datetime = None

    def __post_init__(self):
        """Initialize default values."""
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == "user"

    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == "assistant"

    def has_enrichment(self) -> bool:
        """Check if message has Hunter AI enrichment data."""
        return bool(self.metadata)

    def get_enrichment_field(self, field: str, default=None):
        """Get specific enrichment field from metadata.

        Args:
            field: Field name in metadata
            default: Default value if field not found

        Returns:
            Field value or default
        """
        return self.metadata.get(field, default)

    def update_enrichment(self, enrichment: dict) -> None:
        """Update enrichment metadata.

        Args:
            enrichment: Enrichment data to merge
        """
        self.metadata = {**self.metadata, **enrichment}
