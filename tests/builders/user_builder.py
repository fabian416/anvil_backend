"""
Builder for creating User test data.

Provides fluent interface for test data creation.
"""

from datetime import datetime
from typing import Optional


class UserBuilder:
    """Fluent builder for User test data."""

    def __init__(self):
        """Initialize with default values."""
        self._id: int = 12345
        self._email: str = "test@example.com"
        self._first_name: str = "Test"
        self._last_name: str = "User"
        self._password_hash: str = "hashed_password"
        self._role: str = "user"
        self._active: bool = True
        self._blocked: bool = False
        self._verified: bool = True
        self._created_at: datetime = datetime.utcnow()

    def with_id(self, id_: int) -> "UserBuilder":
        """Set user ID."""
        self._id = id_
        return self

    def with_email(self, email: str) -> "UserBuilder":
        """Set email."""
        self._email = email
        return self

    def with_name(self, first_name: str, last_name: str) -> "UserBuilder":
        """Set first and last name."""
        self._first_name = first_name
        self._last_name = last_name
        return self

    def with_role(self, role: str) -> "UserBuilder":
        """Set user role."""
        self._role = role
        return self

    def as_admin(self) -> "UserBuilder":
        """Configure as admin user."""
        self._role = "admin"
        return self

    def as_super_admin(self) -> "UserBuilder":
        """Configure as super admin user."""
        self._role = "super_admin"
        return self

    def as_active(self) -> "UserBuilder":
        """Configure as active user."""
        self._active = True
        self._blocked = False
        return self

    def as_inactive(self) -> "UserBuilder":
        """Configure as inactive user."""
        self._active = False
        return self

    def as_blocked(self) -> "UserBuilder":
        """Configure as blocked user."""
        self._blocked = True
        return self

    def as_verified(self) -> "UserBuilder":
        """Configure as verified user."""
        self._verified = True
        return self

    def as_unverified(self) -> "UserBuilder":
        """Configure as unverified user."""
        self._verified = False
        return self

    def build_dict(self) -> dict:
        """Build as dictionary."""
        return {
            "id": self._id,
            "email": self._email,
            "first_name": self._first_name,
            "last_name": self._last_name,
            "role": self._role,
            "active": self._active,
            "blocked": self._blocked,
            "verified": self._verified,
            "created_at": self._created_at.isoformat(),
        }

    @classmethod
    def a_user(cls) -> "UserBuilder":
        """Start building a user."""
        return cls()

    @classmethod
    def an_admin(cls) -> "UserBuilder":
        """Build an admin user."""
        return cls().as_admin()

    @classmethod
    def a_super_admin(cls) -> "UserBuilder":
        """Build a super admin user."""
        return cls().as_super_admin()


# Convenience functions
def a_user() -> UserBuilder:
    """Start building a user."""
    return UserBuilder()


def an_admin() -> UserBuilder:
    """Build an admin user."""
    return UserBuilder().as_admin()


def a_super_admin() -> UserBuilder:
    """Build a super admin user."""
    return UserBuilder().as_super_admin()
