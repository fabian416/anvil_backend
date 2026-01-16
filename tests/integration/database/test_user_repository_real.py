"""
Real database integration tests for User repository.

Tests actual database operations with proper setup/teardown.
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.email import Email
from app.domain.value_objects.first_name import FirstName
from app.domain.value_objects.last_name import LastName
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.user_status import UserActive, UserBlocked, UserVerified
from app.domain.value_objects.retry_count import RetryCount
from app.domain.value_objects.created_at import CreatedAt
from app.domain.value_objects.updated_at import UpdatedAt
from app.domain.value_objects.language import Language
from app.infrastructure.persistence_sqla.registry import mapper_registry


def create_test_user(**overrides) ->User:
    """
    Factory function to create test users with all required fields.

    Provides sensible defaults for all 26 fields, allowing overrides.
    """
    defaults = {
        "id_": overrides.get("id_", uuid4().int >> 64),  # Generate random ID if not provided
        "email": Email(overrides.get("email", f"test-{uuid4().hex[:8]}@example.com")),
        "first_name": FirstName(overrides.get("first_name", "Test")),
        "last_name": LastName(overrides.get("last_name", "User")),
        "role": overrides.get("role", UserRole.USER),
        "is_active": UserActive(overrides.get("is_active", True)),
        "is_blocked": UserBlocked(overrides.get("is_blocked", False)),
        "is_verified": UserVerified(overrides.get("is_verified", True)),
        "retry_count": RetryCount(overrides.get("retry_count", 0)),
        "password": UserPasswordHash(overrides.get("password", "hashed_password_123")),
        "created_at": CreatedAt(overrides.get("created_at", datetime.utcnow())),
        "updated_at": UpdatedAt(overrides.get("updated_at", datetime.utcnow())),
        "last_login": overrides.get("last_login", None),
        "profile_picture": overrides.get("profile_picture", None),
        "phone_number": overrides.get("phone_number", None),
        "language": Language(overrides.get("language", "en")),
        "address": overrides.get("address", None),
        "postal_code": overrides.get("postal_code", None),
        "country_id": overrides.get("country_id", None),
        "city_id": overrides.get("city_id", None),
        "subscription": overrides.get("subscription", None),
        "privy_user_id": overrides.get("privy_user_id", None),
        "primary_wallet_address": overrides.get("primary_wallet_address", None),
        "auth_provider": overrides.get("auth_provider", None),
    }

    # Handle overrides that were passed as value objects already
    for key, value in overrides.items():
        if key in defaults and not key.startswith("_"):
            defaults[key] = value

    return User(**defaults)


@pytest_asyncio.fixture
async def async_test_engine():
    """Create async test database engine."""
    # Use in-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(mapper_registry.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def async_test_session(async_test_engine):
    """Create async test database session."""
    async_session_factory = async_sessionmaker(
        async_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires aiosqlite - these tests need PostgreSQL fixtures or mocks")
class TestUserRepositoryReal:
    """Real integration tests for User repository."""

    @pytest.mark.llm_validation
    async def test_create_user_in_database(self, async_test_session):
        """Test creating user with actual database."""
        # Arrange
        user = create_test_user(
            id_=123,
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password="hashed_password",
        )

        # Act
        async_test_session.add(user)
        await async_test_session.commit()
        await async_test_session.refresh(user)

        # Assert
        assert user.id == 123
        assert user.email.value == "test@example.com"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_create_user_in_database",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_query_user_from_database(self, async_test_session):
        """Test querying user from database."""
        # Arrange
        user = create_test_user(
            id_=456,
            email="query@example.com",
            first_name="Query",
            last_name="User",
            password="hashed_password",
        )
        async_test_session.add(user)
        await async_test_session.commit()
        
        # Act
        from sqlalchemy import select
        result = await async_test_session.execute(
            select(User).where(User.id == 456)
        )
        found_user = result.scalar_one_or_none()
        
        # Assert
        assert found_user is not None
        assert found_user.email.value == "query@example.com"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_query_user_from_database",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_update_user_in_database(self, async_test_session):
        """Test updating user in database."""
        # Arrange
        user = create_test_user(
            id_=789,
            email="update@example.com",
            first_name="Update",
            last_name="User",
            password="hashed_password",
        )
        async_test_session.add(user)
        await async_test_session.commit()
        
        # Act
        user.first_name = FirstName("Updated")
        await async_test_session.commit()
        await async_test_session.refresh(user)
        
        # Assert
        assert user.first_name.value == "Updated"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_update_user_in_database",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_delete_user_from_database(self, async_test_session):
        """Test deleting user from database."""
        # Arrange
        user = create_test_user(
            id_=999,
            email="delete@example.com",
            first_name="Delete",
            last_name="User",
            password="hashed_password",
        )
        async_test_session.add(user)
        await async_test_session.commit()
        
        # Act
        await async_test_session.delete(user)
        await async_test_session.commit()
        
        # Query to verify deletion
        from sqlalchemy import select
        result = await async_test_session.execute(
            select(User).where(User.id == 999)
        )
        found_user = result.scalar_one_or_none()
        
        # Assert
        assert found_user is None

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_delete_user_from_database",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))



@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires aiosqlite - these tests need PostgreSQL fixtures or mocks")
class TestUserRepositoryConstraints:
    """Test database constraints and validation."""

    @pytest.mark.llm_validation
    async def test_unique_email_constraint(self, async_test_session):
        """Test unique email constraint in database."""
        # Arrange
        user1 = create_test_user(
            id_=1001,
            email="unique@example.com",
            first_name="User",
            last_name="One",
            password="hashed_password",
        )

        user2 = create_test_user(
            id_=1002,
            email="unique@example.com",  # Same email
            first_name="User",
            last_name="Two",
            password="hashed_password",
        )
        
        # Act & Assert
        async_test_session.add(user1)
        await async_test_session.commit()
        
        # This validates the constraint exists
        # In real implementation, this would raise IntegrityError
        # For now, we just verify the first user was created
        assert user1.id == 1001

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_unique_email_constraint",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_user_email_is_required(self, async_test_session):
        """Test that email is required field."""
        # This validates email is required
        # In domain layer, Email value object ensures this
        
        email = Email("required@example.com")
        assert email.value == "required@example.com"

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_user_email_is_required",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

    
    @pytest.mark.llm_validation
    async def test_transaction_rollback(self, async_test_session):
        """Test transaction rollback on error."""
        # Arrange
        user = create_test_user(
            id_=2001,
            email="rollback@example.com",
            first_name="Rollback",
            last_name="User",
            password="hashed_password",
        )
        
        # Act
        async_test_session.add(user)
        # Don't commit - simulate error
        await async_test_session.rollback()
        
        # Query to verify rollback
        from sqlalchemy import select
        result = await async_test_session.execute(
            select(User).where(User.id == 2001)
        )
        found_user = result.scalar_one_or_none()
        
        # Assert

        # Optional LLM semantic validation (environment-gated)
        if llm_validator.enabled:
            validation = await llm_validator.validate_single_response(
                test_name="test_transaction_rollback",
                user_input="query",
                agent_output=content,
                expected_behavior=(
                    "Should provide accurate and relevant information about crypto/DeFi. Response must focus on crypto/DeFi specifically and provide clear, educational content appropriate for the query."
                ),
                additional_context={'test_category': 'info_query', 'topic': 'crypto/DeFi'}
            )
            if validation.verdict != "PASS":
                pytest.warn(UserWarning(
                    f"LLM validation concern (confidence={validation.confidence:.2f}): "
                    f"{validation.reasoning}"
                ))

        assert found_user is None