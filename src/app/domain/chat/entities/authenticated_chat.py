"""
Authenticated Chat Entities.

Domain entities for authenticated user chat system that bridges to
legacy users table (INTEGER user_id).
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional
from uuid import UUID

from app.domain.entities.base import Entity


@dataclass(eq=False, kw_only=True)
class AuthChatUser(Entity[UUID]):
    """
    Authenticated chat user entity.

    Bridges to legacy users table via INTEGER user_id foreign key.
    """

    user_id: int  # Foreign key to legacy users.id (INTEGER)
    email: str
    subscription_tier: str  # free, premium, enterprise
    total_messages: int = 0
    language: str = "en"
    chat_preferences: Optional[dict] = None
    last_seen_at: datetime = None

    def __post_init__(self):
        super().__post_init__()
        if self.last_seen_at is None:
            self.last_seen_at = datetime.now(UTC)

    def update_subscription_tier(self, tier: str) -> None:
        """Update subscription tier with validation."""
        valid_tiers = {"free", "premium", "enterprise"}
        if tier not in valid_tiers:
            raise ValueError(
                f"Invalid subscription tier: {tier}. "
                f"Must be one of: {', '.join(valid_tiers)}"
            )
        self.subscription_tier = tier
        self.updated_at = datetime.now(UTC)

    def increment_message_count(self) -> None:
        """Increment total message count."""
        self.total_messages += 1
        self.updated_at = datetime.now(UTC)

    def update_language(self, language: str) -> None:
        """Update preferred language."""
        supported_languages = {"en", "es", "pt", "zh"}
        if language not in supported_languages:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Must be one of: {', '.join(supported_languages)}"
            )
        self.language = language
        self.updated_at = datetime.now(UTC)


@dataclass(eq=False, kw_only=True)
class AuthChatConversation(Entity[UUID]):
    """
    Authenticated chat conversation entity.

    Links to AuthChatUser, supports multiple languages and lifecycle.
    """

    chat_user_id: UUID  # Foreign key to chat_users.id
    title: Optional[str] = None
    language: str = "en"
    status: str = "active"  # active, archived
    message_count: int = 0
    archived_at: Optional[datetime] = None

    def archive(self) -> None:
        """Archive this conversation."""
        if self.status != "archived":
            self.status = "archived"
            self.archived_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)

    def reactivate(self) -> None:
        """Reactivate an archived conversation."""
        if self.status == "archived":
            self.status = "active"
            self.archived_at = None
            self.updated_at = datetime.now(UTC)

    def update_title(self, title: str) -> None:
        """Update conversation title."""
        self.title = title
        self.updated_at = datetime.now(UTC)

    def increment_message_count(self) -> None:
        """Increment message count."""
        self.message_count += 1
        self.updated_at = datetime.now(UTC)

    @property
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == "active"

    @property
    def is_archived(self) -> bool:
        """Check if conversation is archived."""
        return self.status == "archived"


@dataclass(eq=False, kw_only=True)
class AuthChatMessage(Entity[UUID]):
    """
    Authenticated chat message entity.

    Stores user and assistant messages with Hunter AI metadata.
    """

    conversation_id: UUID  # Foreign key to chat_conversations.id
    role: str  # user, assistant
    content: str
    intent: Optional[str] = None
    language: str = "en"
    metadata: dict = None  # Hunter AI enrichment data (stored as JSONB)

    def __post_init__(self):
        super().__post_init__()
        if self.metadata is None:
            self.metadata = {}

    def validate_role(self) -> None:
        """Validate message role."""
        valid_roles = {"user", "assistant"}
        if self.role not in valid_roles:
            raise ValueError(
                f"Invalid role: {self.role}. "
                f"Must be one of: {', '.join(valid_roles)}"
            )

    def add_enrichment(self, key: str, value: any) -> None:
        """Add enrichment data to metadata."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    @property
    def is_user_message(self) -> bool:
        """Check if message is from user."""
        return self.role == "user"

    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant."""
        return self.role == "assistant"
