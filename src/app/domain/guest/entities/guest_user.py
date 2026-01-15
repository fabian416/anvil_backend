"""
Guest User entity.

Represents an unauthenticated user tracked by IP address.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from uuid import UUID, uuid4


@dataclass
class GuestUser:
    """
    Guest user entity for demo/unauthenticated users.

    Tracked by IP address with optional browser fingerprint.
    """

    id: UUID = field(default_factory=uuid4)
    ip_address: str = ""
    fingerprint: str | None = None
    first_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    total_messages: int = 0
    language: str = "en"
    country_code: str | None = None
    is_blocked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def increment_messages(self) -> None:
        """Increment total message count."""
        self.total_messages += 1
        self.last_seen_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def update_last_seen(self) -> None:
        """Update last seen timestamp."""
        self.last_seen_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def block(self) -> None:
        """Block this guest user."""
        self.is_blocked = True
        self.updated_at = datetime.now(UTC)

    def unblock(self) -> None:
        """Unblock this guest user."""
        self.is_blocked = False
        self.updated_at = datetime.now(UTC)
