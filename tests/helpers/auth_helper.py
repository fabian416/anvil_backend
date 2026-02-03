"""
Authentication test helper for creating test users and managing sessions.

Provides utilities for:
- Creating test users with specific roles
- Generating valid JWT tokens
- Managing test sessions
- Generating authentication headers

Usage:
    from tests.helpers.auth_helper import AuthHelper, create_test_user

    # Create a regular user
    user, token = await create_test_user("user")

    # Create an admin user
    user, token = await create_test_user("admin")

    # Get auth headers
    headers = get_auth_headers(token)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID, uuid4
import jwt

from tests.builders.user_builder import UserBuilder


def _utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# Type alias for user roles
UserRole = Literal["user", "admin", "super_admin"]


@dataclass
class TestUser:
    """
    Represents a test user with authentication information.

    Attributes:
        id: Unique user identifier
        email: User email address
        password: Plain text password (for testing)
        role: User role (user, admin, super_admin)
        is_active: Whether user account is active
        is_verified: Whether user email is verified
        access_token: JWT access token (if authenticated)
        refresh_token: JWT refresh token (if authenticated)
        session_id: Session identifier (if session created)
    """

    id: UUID
    email: str
    password: str
    role: UserRole
    is_active: bool = True
    is_verified: bool = True
    access_token: str | None = None
    refresh_token: str | None = None
    session_id: str | None = None
    first_name: str = "Test"
    last_name: str = "User"
    created_at: datetime = field(default_factory=_utc_now)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at.isoformat(),
        }


class AuthHelper:
    """
    Helper class for authentication-related test operations.

    Provides methods for creating test users, generating JWT tokens,
    and managing test sessions.
    """

    # Default test secret for JWT signing - matches config/local/.secrets.toml
    _test_secret: str = "your-super-secret-jwt-key-change-in-production"
    _test_sessions: dict[str, dict] = {}

    @classmethod
    def set_secret(cls, secret: str) -> None:
        """Set the JWT secret for token generation."""
        cls._test_secret = secret

    @classmethod
    def create_jwt_token_with_session(
        cls,
        session_id: str,
        user_id_int: int,
        email: str,
        role: str,
        token_type: str = "access",
        expires_in_hours: int = 1,
    ) -> str:
        """
        Create a JWT token with session ID for database-backed authentication.

        Args:
            session_id: Auth session identifier
            user_id_int: User integer ID from database
            email: User email
            role: User role
            token_type: Token type (access or refresh)
            expires_in_hours: Token expiration in hours

        Returns:
            JWT token string with auth_session_id field
        """
        now = _utc_now()
        payload = {
            "auth_session_id": session_id,  # Required field for auth validation
            "exp": int((now + timedelta(hours=expires_in_hours)).timestamp()),
        }

        # Use PyJWT library to ensure 100% compatibility with app's JWT validation
        token = jwt.encode(payload, cls._test_secret, algorithm="HS256")
        return token

    @classmethod
    def create_jwt_token(
        cls,
        user_id: UUID,
        email: str,
        role: str,
        token_type: str = "access",
        expires_in_hours: int = 1,
    ) -> str:
        """
        Create a JWT token for testing (in-memory only).

        Args:
            user_id: User identifier
            email: User email
            role: User role
            token_type: Token type (access or refresh)
            expires_in_hours: Token expiration in hours

        Returns:
            JWT token string
        """
        now = _utc_now()
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.upper(),
            "type": token_type,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=expires_in_hours)).timestamp()),
            "jti": uuid4().hex,
        }

        # Use PyJWT library
        token = jwt.encode(payload, cls._test_secret, algorithm="HS256")
        return token

    @classmethod
    def create_expired_token(
        cls,
        user_id: UUID,
        email: str,
        role: str,
        token_type: str = "access",
    ) -> str:
        """
        Create an expired JWT token for testing expiration handling.

        Args:
            user_id: User identifier
            email: User email
            role: User role
            token_type: Token type (access or refresh)

        Returns:
            Expired JWT token string
        """
        now = _utc_now()
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role.upper(),
            "type": token_type,
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
            "jti": uuid4().hex,
        }

        # Use PyJWT library
        token = jwt.encode(payload, cls._test_secret, algorithm="HS256")
        return token

    @classmethod
    async def create_test_user_in_db(
        cls,
        db_session,
        role: UserRole = "user",
        email: str | None = None,
        password: str = "TestPassword123!",
        is_active: bool = True,
        is_verified: bool = True,
        first_name: str = "Test",
        last_name: str = "User",
    ) -> tuple[TestUser, str]:
        """
        Create a test user with authentication token in the database.

        Args:
            db_session: SQLAlchemy async session
            role: User role (user, admin, super_admin)
            email: User email (auto-generated if not provided)
            password: User password
            is_active: Whether user is active
            is_verified: Whether user email is verified
            first_name: User first name
            last_name: User last name

        Returns:
            Tuple of (TestUser, access_token)
        """
        from sqlalchemy import text
        from datetime import datetime, timedelta

        # Generate user ID and email
        user_id_int = abs(hash(str(uuid4()))) % (10**9)  # Convert UUID to integer
        if email is None:
            email = f"test_{uuid4().hex[:8]}@example.com"

        # Hash password
        import bcrypt

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert user into database
        insert_user_sql = text("""
            INSERT INTO users (id, email, first_name, last_name, role, is_active, is_verified, password, created_at, updated_at)
            VALUES (:id, :email, :first_name, :last_name, :role, :is_active, :is_verified, :password, :created_at, :updated_at)
            RETURNING id
        """)

        result = await db_session.execute(
            insert_user_sql,
            {
                "id": user_id_int,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "is_active": is_active,
                "is_verified": is_verified,
                "password": password_hash,
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
            },
        )
        created_user_id = result.scalar_one()

        # Create session ID and expiration
        session_id = uuid4().hex
        expiration = _utc_now() + timedelta(hours=24)

        # Insert auth session into database
        insert_session_sql = text("""
            INSERT INTO auth_sessions (id, user_id, expiration)
            VALUES (:id, :user_id, :expiration)
        """)

        await db_session.execute(
            insert_session_sql,
            {
                "id": session_id,
                "user_id": created_user_id,
                "expiration": expiration,
            },
        )

        await db_session.commit()

        # Create access token with session ID
        access_token = cls.create_jwt_token_with_session(
            session_id=session_id,
            user_id_int=created_user_id,
            email=email,
            role=role,
            token_type="access",
            expires_in_hours=1,
        )

        # Create refresh token
        refresh_token = cls.create_jwt_token_with_session(
            session_id=session_id,
            user_id_int=created_user_id,
            email=email,
            role=role,
            token_type="refresh",
            expires_in_hours=24,
        )

        user = TestUser(
            id=UUID(int=created_user_id),  # Convert back to UUID
            email=email,
            password=password,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            first_name=first_name,
            last_name=last_name,
        )

        return user, access_token

    @classmethod
    def create_test_user(
        cls,
        role: UserRole = "user",
        email: str | None = None,
        password: str = "TestPassword123!",
        is_active: bool = True,
        is_verified: bool = True,
        first_name: str = "Test",
        last_name: str = "User",
    ) -> tuple[TestUser, str]:
        """
        Create a test user with authentication token (in-memory only, for backwards compatibility).

        Note: This does NOT create database records. Use create_test_user_in_db for integration tests.

        Args:
            role: User role (user, admin, super_admin)
            email: User email (auto-generated if not provided)
            password: User password
            is_active: Whether user is active
            is_verified: Whether user email is verified
            first_name: User first name
            last_name: User last name

        Returns:
            Tuple of (TestUser, access_token)
        """
        user_id = uuid4()
        if email is None:
            email = f"test_{user_id.hex[:8]}@example.com"

        # Create access token
        access_token = cls.create_jwt_token(
            user_id=user_id,
            email=email,
            role=role,
            token_type="access",
            expires_in_hours=1,
        )

        # Create refresh token
        refresh_token = cls.create_jwt_token(
            user_id=user_id,
            email=email,
            role=role,
            token_type="refresh",
            expires_in_hours=24,
        )

        # Create session
        session_id = uuid4().hex
        cls._test_sessions[session_id] = {
            "user_id": str(user_id),
            "email": email,
            "role": role,
            "created_at": _utc_now().isoformat(),
        }

        user = TestUser(
            id=user_id,
            email=email,
            password=password,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
            access_token=access_token,
            refresh_token=refresh_token,
            session_id=session_id,
            first_name=first_name,
            last_name=last_name,
        )

        return user, access_token

    @classmethod
    def create_admin_session(cls) -> tuple[TestUser, str]:
        """
        Create an admin user with a session.

        Returns:
            Tuple of (TestUser, access_token) with admin role
        """
        return cls.create_test_user(role="admin")

    @classmethod
    def create_super_admin_session(cls) -> tuple[TestUser, str]:
        """
        Create a super admin user with a session.

        Returns:
            Tuple of (TestUser, access_token) with super_admin role
        """
        return cls.create_test_user(role="super_admin")

    @classmethod
    def invalidate_session(cls, session_id: str) -> bool:
        """
        Invalidate a test session.

        Args:
            session_id: Session identifier to invalidate

        Returns:
            True if session was invalidated, False if not found
        """
        if session_id in cls._test_sessions:
            del cls._test_sessions[session_id]
            return True
        return False

    @classmethod
    def clear_all_sessions(cls) -> None:
        """Clear all test sessions."""
        cls._test_sessions.clear()

    @classmethod
    def is_session_valid(cls, session_id: str) -> bool:
        """Check if a session is valid."""
        return session_id in cls._test_sessions

    @staticmethod
    def get_auth_headers(token: str) -> dict[str, str]:
        """
        Generate authentication headers with Bearer token.

        Args:
            token: JWT access token

        Returns:
            Dictionary with Authorization and Content-Type headers
        """
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }


# Convenience functions for module-level access
def create_test_user(
    role: UserRole = "user",
    email: str | None = None,
    **kwargs,
) -> tuple[TestUser, str]:
    """
    Create a test user with authentication token.

    Args:
        role: User role (user, admin, super_admin)
        email: User email (auto-generated if not provided)
        **kwargs: Additional user attributes

    Returns:
        Tuple of (TestUser, access_token)
    """
    return AuthHelper.create_test_user(role=role, email=email, **kwargs)


def get_auth_headers(token: str) -> dict[str, str]:
    """
    Generate authentication headers with Bearer token.

    Args:
        token: JWT access token

    Returns:
        Dictionary with Authorization and Content-Type headers
    """
    return AuthHelper.get_auth_headers(token)


def create_admin_session() -> tuple[TestUser, str]:
    """
    Create an admin user with a session.

    Returns:
        Tuple of (TestUser, access_token) with admin role
    """
    return AuthHelper.create_admin_session()


def invalidate_session(session_id: str) -> bool:
    """
    Invalidate a test session.

    Args:
        session_id: Session identifier to invalidate

    Returns:
        True if session was invalidated, False if not found
    """
    return AuthHelper.invalidate_session(session_id)
