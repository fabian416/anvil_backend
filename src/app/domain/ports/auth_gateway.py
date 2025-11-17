"""
Auth gateway port for the hexagonal architecture.
Defines the interface for auth-related operations.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.auth import AuthContext, RoleChangeRequest
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.enums.user_role import UserRole


class AuthGateway(ABC):
    """
    Gateway interface for authentication and authorization operations.
    """
    
    @abstractmethod
    async def validate_token(self, access_token: str) -> Optional[AuthContext]:
        """
        Validate an access token and return the auth context.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            AuthContext if valid, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: Email) -> Optional[User]:
        """
        Get a user by email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update_user_role(self, user_id: str, new_role: UserRole) -> Optional[User]:
        """
        Update a user's role.
        
        Args:
            user_id: The ID of the user to update
            new_role: The new role to assign
            
        Returns:
            Updated User if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def is_super_admin(self, email: Email) -> bool:
        """
        Check if a user is a super admin (USER_ADMIN from environment).
        
        Args:
            email: The email to check
            
        Returns:
            True if super admin, False otherwise
        """
        pass
