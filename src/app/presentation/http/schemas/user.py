"""
User schemas for the hexagonal architecture.
"""

from pydantic import BaseModel
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole


class UserResponse(BaseModel):
    """Response schema for user data."""
    
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    
    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        """
        Create UserResponse from domain User entity.
        
        Args:
            user: The domain user entity
            
        Returns:
            UserResponse instance
        """
        return cls(
            id=user.id,
            email=user.email.value,
            first_name=user.first_name.value,
            last_name=user.last_name.value,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )
