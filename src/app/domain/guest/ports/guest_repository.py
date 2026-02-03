"""
Guest Repository Port.

Defines the interface for guest user persistence operations.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.guest.entities.guest_conversation import GuestConversation
from app.domain.guest.entities.guest_message import GuestMessage
from app.domain.guest.entities.guest_user import GuestUser


class GuestRepository(Protocol):
    """
    Repository interface for guest user operations.

    Handles CRUD for guest_users, guest_conversations, guest_messages.
    """

    # ========================================
    # Guest User Operations
    # ========================================

    async def get_guest_by_ip(self, ip_address: str) -> GuestUser | None:
        """Get guest user by IP address."""
        ...

    async def get_guest_by_id(self, guest_id: UUID) -> GuestUser | None:
        """Get guest user by ID."""
        ...

    async def create_guest(self, guest: GuestUser) -> GuestUser:
        """Create a new guest user."""
        ...

    async def update_guest(self, guest: GuestUser) -> GuestUser:
        """Update an existing guest user."""
        ...

    # ========================================
    # Guest Conversation Operations
    # ========================================

    async def get_active_conversation(
        self, guest_user_id: UUID
    ) -> GuestConversation | None:
        """Get the active conversation for a guest user."""
        ...

    async def get_conversation_by_id(
        self, conversation_id: UUID
    ) -> GuestConversation | None:
        """Get conversation by ID."""
        ...

    async def create_conversation(
        self, conversation: GuestConversation
    ) -> GuestConversation:
        """Create a new conversation."""
        ...

    async def update_conversation(
        self, conversation: GuestConversation
    ) -> GuestConversation:
        """Update an existing conversation."""
        ...

    async def archive_inactive_conversations(self, older_than: datetime) -> int:
        """Archive conversations older than specified time. Returns count archived."""
        ...

    async def delete_conversation_for_guest(self, guest_user_id: UUID) -> bool:
        """
        Delete (archive) the active conversation for a guest user and clear all messages.
        Returns True if successful, False if no active conversation found.
        """
        ...

    # ========================================
    # Guest Message Operations
    # ========================================

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GuestMessage]:
        """Get messages for a conversation."""
        ...

    async def create_message(self, message: GuestMessage) -> GuestMessage:
        """Create a new message."""
        ...

    async def get_message_count(self, conversation_id: UUID) -> int:
        """Get message count for a conversation."""
        ...

    # ========================================
    # Telemetry Operations
    # ========================================

    async def log_telemetry(
        self,
        guest_user_id: UUID,
        event_type: str,
        ip_address: str,
        conversation_id: UUID | None = None,
        event_data: dict | None = None,
        user_agent: str | None = None,
        referer: str | None = None,
        language: str = "en",
    ) -> None:
        """Log a telemetry event."""
        ...

    # ========================================
    # Rate Limiting
    # ========================================

    async def get_message_count_since(
        self,
        guest_user_id: UUID,
        since: datetime,
    ) -> int:
        """Get message count since a timestamp (for rate limiting)."""
        ...
