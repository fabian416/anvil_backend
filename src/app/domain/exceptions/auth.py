"""
Auth-specific domain exceptions.
"""

from app.domain.exceptions.base import DomainError


class InvalidAuthorizationHeaderError(DomainError):
    """Raised when the authorization header is invalid or missing."""

    pass


class UnauthorizedAccessError(DomainError):
    """Raised when a user attempts to access a resource without proper authorization."""

    pass


class InsufficientPermissionsError(DomainError):
    """Raised when a user doesn't have sufficient permissions for an action."""

    pass


class RoleChangeNotAllowedError(DomainError):
    """Raised when a role change is not allowed."""

    pass


class InvalidTokenError(DomainError):
    """Raised when a JWT token is invalid."""

    pass


class TokenExpiredError(DomainError):
    """Raised when a JWT token has expired."""

    pass
