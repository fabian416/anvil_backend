"""
Integration test configuration and fixtures.

These tests require:
- Running PostgreSQL database with test data
- External service mocks or connections
- Authentication fixtures
"""

import pytest
import os
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

# Check if we have database connectivity
DATABASE_URL = os.environ.get("DATABASE_URL", os.environ.get("POSTGRES_HOST", ""))
HAS_DATABASE = bool(DATABASE_URL)

# Common marker for tests requiring database
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_db_session():
    """Provide mock database session for tests that don't need real DB."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def test_admin_data():
    """Provide test admin data."""
    return {
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User",
    }


@pytest.fixture
def mock_stripe():
    """Mock Stripe client."""
    stripe = MagicMock()
    stripe.checkout.Session.create = MagicMock(return_value=MagicMock(
        id="cs_test_123",
        url="https://checkout.stripe.com/test",
    ))
    stripe.Subscription.retrieve = MagicMock(return_value=MagicMock(
        id="sub_test_123",
        status="active",
    ))
    return stripe


@pytest.fixture
def mock_mailgun():
    """Mock Mailgun client."""
    mailgun = MagicMock()
    mailgun.send = MagicMock(return_value={"id": "msg_test_123"})
    return mailgun
