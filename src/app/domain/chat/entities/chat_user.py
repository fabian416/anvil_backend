"""
Chat User Entity.

Unified user entity for both guest and authenticated users.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class UserType(str, Enum):
    """User type classification."""
    
    GUEST = "guest"
    AUTHENTICATED = "authenticated"
    PREMIUM = "premium"


@dataclass
class ChatUser:
    """
    Unified chat user entity.
    
    Supports both guest users (identified by IP) and authenticated users
    (identified by Privy ID).
    """
    
    id: UUID = field(default_factory=uuid4)
    user_type: UserType = UserType.GUEST
    identifier: str = ""  # IP for guest, privy_id for authenticated
    privy_id: str | None = None
    email: str | None = None
    preferred_language: str = "en"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)
    is_blocked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create_guest(cls, ip_address: str, language: str = "en") -> "ChatUser":
        """Create a guest user from IP address."""
        return cls(
            user_type=UserType.GUEST,
            identifier=ip_address,
            preferred_language=language,
        )
    
    @classmethod
    def create_authenticated(
        cls,
        privy_id: str,
        email: str | None = None,
        language: str = "en",
    ) -> "ChatUser":
        """Create an authenticated user from Privy data."""
        return cls(
            user_type=UserType.AUTHENTICATED,
            identifier=privy_id,
            privy_id=privy_id,
            email=email,
            preferred_language=language,
        )
    
    def upgrade_to_premium(self) -> None:
        """Upgrade user to premium tier."""
        self.user_type = UserType.PREMIUM
    
    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active_at = datetime.utcnow()
    
    def block(self) -> None:
        """Block the user."""
        self.is_blocked = True
    
    def unblock(self) -> None:
        """Unblock the user."""
        self.is_blocked = False
    
    @property
    def is_guest(self) -> bool:
        """Check if user is a guest."""
        return self.user_type == UserType.GUEST
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (includes premium)."""
        return self.user_type in (UserType.AUTHENTICATED, UserType.PREMIUM)
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium access."""
        return self.user_type == UserType.PREMIUM

