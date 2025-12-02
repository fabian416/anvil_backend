"""
Authentication fixtures for tests.

Provides mock authentication tokens, user contexts, and
auth-related test data.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta


@pytest.fixture
def mock_user_id():
    """Generate mock user ID for tests."""
    return uuid4()


@pytest.fixture
def mock_auth_token():
    """Generate mock JWT authentication token."""
    return "mock_jwt_token_for_testing_" + uuid4().hex[:16]


@pytest.fixture
def mock_admin_token():
    """Generate mock admin JWT token."""
    return "mock_admin_jwt_token_" + uuid4().hex[:16]


@pytest.fixture
def mock_expired_token():
    """Generate mock expired JWT token."""
    return "mock_expired_jwt_token_" + uuid4().hex[:16]


@pytest.fixture
def mock_jwt_payload(mock_user_id):
    """
    Generate mock JWT payload.
    
    Returns dict with standard JWT claims.
    """
    now = datetime.utcnow()
    return {
        "sub": str(mock_user_id),
        "email": "test@example.com",
        "role": "USER",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "type": "access",
    }


@pytest.fixture
def mock_admin_jwt_payload(mock_user_id):
    """Generate mock admin JWT payload."""
    now = datetime.utcnow()
    return {
        "sub": str(mock_user_id),
        "email": "admin@example.com",
        "role": "ADMIN",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "type": "access",
    }


@pytest.fixture
def auth_headers(mock_auth_token):
    """Generate authentication headers for API requests."""
    return {
        "Authorization": f"Bearer {mock_auth_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_auth_headers(mock_admin_token):
    """Generate admin authentication headers."""
    return {
        "Authorization": f"Bearer {mock_admin_token}",
        "Content-Type": "application/json",
    }
