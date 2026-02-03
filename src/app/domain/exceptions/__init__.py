"""
Domain exceptions module for the hexagonal architecture.
"""

from .base import DomainError
from .auth import (
    InvalidAuthorizationHeaderError,
    UnauthorizedAccessError,
    InsufficientPermissionsError,
    RoleChangeNotAllowedError,
)

__all__ = [
    "DomainError",
    "InvalidAuthorizationHeaderError",
    "UnauthorizedAccessError",
    "InsufficientPermissionsError",
    "RoleChangeNotAllowedError",
]
