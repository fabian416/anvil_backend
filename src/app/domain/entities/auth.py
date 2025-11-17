"""
Auth entity for the hexagonal architecture.
Contains domain objects related to authorization.
"""

from dataclasses import dataclass
from typing import Optional
from app.domain.value_objects.access_token import AccessToken
from app.domain.value_objects.email import Email
from app.domain.enums.user_role import UserRole


@dataclass(frozen=True, slots=True)
class AuthContext:
    """
    Represents the authentication context for a request.
    """
    access_token: AccessToken
    user_email: Email
    user_role: UserRole
    user_id: str


@dataclass(frozen=True, slots=True)
class RoleChangeRequest:
    """
    Represents a request to change a user's role.
    """
    target_email: Email
    new_role: UserRole
    requested_by: Email
