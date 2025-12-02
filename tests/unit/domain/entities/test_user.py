"""
Tests for User entity.

Tests user creation, role management, and user attributes.
"""

import pytest
from datetime import datetime

from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.language import Language
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt


@pytest.mark.unit
class TestUser:
    """Test suite for User entity."""
    
    def test_create_user_with_valid_data_succeeds(self):
        """Test user creation with valid data."""
        # Arrange
        user_data = {
            "id": UserId(1),
            "email": Email("test@example.com"),
            "first_name": FirstName("John"),
            "last_name": LastName("Doe"),
            "role": UserRole.USER,
            "is_active": UserActive(True),
            "is_blocked": UserBlocked(False),
            "is_verified": UserVerified(True),
            "retry_count": RetryCount(0),
            "password": UserPasswordHash("hashed_password"),
            "language": Language("en"),
            "created_at": CreatedAt(datetime.utcnow()),
            "updated_at": UpdatedAt(datetime.utcnow()),
        }
        
        # Act
        user = User(**user_data)
        
        # Assert
        assert user.id == user_data["id"]
        assert user.email == user_data["email"]
        assert user.first_name == user_data["first_name"]
        assert user.role == UserRole.USER
        assert user.is_active == user_data["is_active"]
    
    def test_user_with_admin_role_succeeds(self):
        """Test creating user with admin role."""
        # Arrange & Act
        user = User(
            id=UserId(2),
            email=Email("admin@example.com"),
            first_name=FirstName("Admin"),
            last_name=LastName("User"),
            role=UserRole.ADMIN,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(True),
            retry_count=RetryCount(0),
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
        )
        
        # Assert
        assert user.role == UserRole.ADMIN
    
    def test_user_active_status_can_be_false(self):
        """Test user can be created as inactive."""
        # Arrange & Act
        user = User(
            id=UserId(3),
            email=Email("inactive@example.com"),
            first_name=FirstName("Inactive"),
            last_name=LastName("User"),
            role=UserRole.USER,
            is_active=UserActive(False),  # Inactive
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(False),
            retry_count=RetryCount(0),
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
        )
        
        # Assert
        assert user.is_active.value is False
    
    def test_user_blocked_status_works(self):
        """Test user can be blocked."""
        # Arrange & Act
        user = User(
            id=UserId(4),
            email=Email("blocked@example.com"),
            first_name=FirstName("Blocked"),
            last_name=LastName("User"),
            role=UserRole.USER,
            is_active=UserActive(True),
            is_blocked=UserBlocked(True),  # Blocked
            is_verified=UserVerified(True),
            retry_count=RetryCount(0),
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
        )
        
        # Assert
        assert user.is_blocked.value is True
    
    def test_user_verified_status_works(self):
        """Test user verification status."""
        # Arrange & Act
        user = User(
            id=UserId(5),
            email=Email("unverified@example.com"),
            first_name=FirstName("Unverified"),
            last_name=LastName("User"),
            role=UserRole.USER,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(False),  # Not verified
            retry_count=RetryCount(0),
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
        )
        
        # Assert
        assert user.is_verified.value is False
    
    def test_user_retry_count_tracks_attempts(self):
        """Test user retry count attribute."""
        # Arrange & Act
        user = User(
            id=UserId(6),
            email=Email("retry@example.com"),
            first_name=FirstName("Retry"),
            last_name=LastName("User"),
            role=UserRole.USER,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(True),
            retry_count=RetryCount(3),  # 3 retries
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
        )
        
        # Assert
        assert user.retry_count.value == 3
    
    def test_user_optional_fields_can_be_none(self):
        """Test user optional fields (profile_picture, phone, etc.)."""
        # Arrange & Act
        user = User(
            id=UserId(7),
            email=Email("minimal@example.com"),
            first_name=FirstName("Minimal"),
            last_name=LastName("User"),
            role=UserRole.USER,
            is_active=UserActive(True),
            is_blocked=UserBlocked(False),
            is_verified=UserVerified(True),
            retry_count=RetryCount(0),
            password=UserPasswordHash("hashed"),
            language=Language("en"),
            created_at=CreatedAt(datetime.utcnow()),
            updated_at=UpdatedAt(datetime.utcnow()),
            # All optional fields not provided
        )
        
        # Assert
        assert user.last_login is None
        assert user.profile_picture is None
        assert user.phone_number is None
        assert user.address is None
        assert user.postal_code is None
        assert user.country_id is None
        assert user.city_id is None
        assert user.subscription is None
        assert user.privy_user_id is None
        assert user.primary_wallet_address is None
        assert user.auth_provider is None
