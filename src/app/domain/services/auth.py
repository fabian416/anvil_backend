"""
Auth domain service for the hexagonal architecture.
Contains business logic for authentication and authorization.
"""

import os
from typing import Optional
from app.domain.entities.auth import AuthContext, RoleChangeRequest
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.auth import (
    InvalidAuthorizationHeaderError,
    UnauthorizedAccessError,
    InsufficientPermissionsError,
    RoleChangeNotAllowedError,
)
from app.domain.value_objects.email import Email


class AuthService:
    """
    Domain service for authentication and authorization business logic.
    """
    
    def __init__(self):
        # Support both formats: ADMIN_USER_ADMIN (from TOML export) or USER_ADMIN (legacy)
        self._super_admin_email = os.getenv("ADMIN_USER_ADMIN") or os.getenv("USER_ADMIN")
    
    def validate_authorization_header(self, authorization: Optional[str]) -> str:
        """
        Validate the authorization header and extract the token.
        
        Args:
            authorization: The authorization header value
            
        Returns:
            The extracted access token
            
        Raises:
            InvalidAuthorizationHeaderError: If header is invalid
        """
        if not authorization or not authorization.startswith("Bearer "):
            raise InvalidAuthorizationHeaderError("Invalid authorization header")
        
        return authorization.split(" ")[1]
    
    def check_super_admin_permission(self, user_email: Email) -> None:
        """
        Check if the user has super admin permissions.
        
        Args:
            user_email: The email of the user to check
            
        Raises:
            InsufficientPermissionsError: If user is not super admin
        """
        if not self._super_admin_email or user_email.value != self._super_admin_email:
            raise InsufficientPermissionsError("Not authorized to perform this action")
    
    def check_admin_permission(self, user_role: UserRole) -> None:
        """
        Check if the user has admin permissions.
        
        Args:
            user_role: The role of the user to check
            
        Raises:
            InsufficientPermissionsError: If user is not admin
        """
        if user_role != UserRole.ADMIN:
            raise InsufficientPermissionsError("Only admin users can perform this action")
    
    def validate_role_change(self, current_role: UserRole, new_role: UserRole) -> None:
        """
        Validate if a role change is allowed.
        
        Args:
            current_role: The current role of the user
            new_role: The new role to assign
            
        Raises:
            RoleChangeNotAllowedError: If role change is not allowed
        """
        # Add any business rules for role changes here
        if current_role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            raise RoleChangeNotAllowedError("Cannot downgrade admin role")
    
    def is_super_admin(self, email: Email) -> bool:
        """
        Check if a user is a super admin.
        
        Args:
            email: The email to check
            
        Returns:
            True if super admin, False otherwise
        """
        return self._super_admin_email and email.value == self._super_admin_email
