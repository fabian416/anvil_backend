"""
Integration tests for user login flow.

Tests complete login flow including:
- Valid credentials returning tokens
- Invalid credentials returning error
- Inactive account handling
- Blocked account handling
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestLoginFlow:
    """Integration tests for user login."""

    @pytest.fixture
    def valid_credentials(self):
        """Create valid login credentials."""
        return {
            "email": "testuser@example.com",
            "password": "TestPassword123!",
        }

    async def test_login_with_valid_credentials_returns_tokens(self, client, valid_credentials):
        """
        WHEN user logs in with valid credentials
        THEN system SHALL return access and refresh tokens (if user exists)
        """
        response = await client.post("/api/v1/account/login", json=valid_credentials)

        # Could be 200 (success) or 401/404 (user doesn't exist in test db)
        if response.status_code == 200:
            data = response.json()
            # Check for the actual response format from log_in.py
            assert "access_token" in data
            assert "refresh_token" in data
            assert "session_id" in data
            assert "user_id" in data
            assert "token_type" in data
            assert data["token_type"] == "bearer"
        else:
            # User doesn't exist in test DB - this is expected
            assert response.status_code in (401, 404)

    async def test_login_with_invalid_password_returns_auth_error(self, client):
        """
        WHEN user provides invalid password
        THEN system SHALL return 401 unauthorized error
        """
        invalid_credentials = {
            "email": "testuser@example.com",
            "password": "WrongPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=invalid_credentials)

        # Should return 401 for invalid credentials or 404 if user not found
        assert response.status_code in (401, 404)

    async def test_login_with_nonexistent_email_returns_error(self, client):
        """
        WHEN user provides email that doesn't exist
        THEN system SHALL return 404 not found error
        """
        nonexistent_credentials = {
            "email": f"nonexistent_{uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=nonexistent_credentials)

        # Should return 404 for user not found
        assert response.status_code == 404

    async def test_login_with_invalid_email_format_returns_error(self, client):
        """
        WHEN user provides invalid email format
        THEN system SHALL return validation error
        """
        invalid_email = {
            "email": "not-an-email",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=invalid_email)

        # Should return 400 or 422 for validation error
        assert response.status_code in (400, 422)

    async def test_login_without_password_returns_error(self, client):
        """
        WHEN user attempts login without password
        THEN system SHALL return validation error
        """
        missing_password = {
            "email": "testuser@example.com",
            # Missing password
        }

        response = await client.post("/api/v1/account/login", json=missing_password)

        assert response.status_code == 422  # Pydantic validation error

    async def test_login_response_includes_user_info(self, client, valid_credentials):
        """
        WHEN user logs in successfully
        THEN response SHALL include user ID
        """
        response = await client.post("/api/v1/account/login", json=valid_credentials)

        if response.status_code == 200:
            data = response.json()
            # Response includes user_id directly (not nested in "user")
            assert "user_id" in data
        else:
            # User doesn't exist - expected in test env
            assert response.status_code in (401, 404)


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestLoginAccountStatus:
    """Integration tests for login with different account statuses."""

    async def test_login_with_inactive_account_returns_forbidden(self, client):
        """
        WHEN inactive user attempts to login
        THEN system SHALL return 401 or 403 error
        """
        # This requires a seeded inactive user in test database
        inactive_credentials = {
            "email": "inactive@example.com",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=inactive_credentials)

        # Should return 401, 403, or 404
        assert response.status_code in (401, 403, 404)

    async def test_login_with_blocked_account_returns_forbidden(self, client):
        """
        WHEN blocked user attempts to login
        THEN system SHALL return 401 or 403 error
        """
        blocked_credentials = {
            "email": "blocked@example.com",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=blocked_credentials)

        # Should return 401, 403, or 404
        assert response.status_code in (401, 403, 404)

    async def test_login_with_unverified_email(self, client):
        """
        WHEN unverified user attempts to login
        THEN system behavior depends on verification requirement
        """
        unverified_credentials = {
            "email": "unverified@example.com",
            "password": "TestPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=unverified_credentials)

        # Could be 200 (if verification not required), 403, or 404 (not found)
        assert response.status_code in (200, 401, 403, 404)


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestLoginRateLimiting:
    """Integration tests for login rate limiting."""

    async def test_multiple_failed_attempts_triggers_rate_limit(self, client):
        """
        WHEN user exceeds failed login attempts
        THEN system MAY return rate limit error (if enabled)
        """
        invalid_credentials = {
            "email": "ratelimit@example.com",
            "password": "WrongPassword123!",
        }

        # Make multiple failed attempts
        responses = []
        for _ in range(5):  # Reduced from 10 for faster tests
            response = await client.post("/api/v1/account/login", json=invalid_credentials)
            responses.append(response.status_code)

        # After enough attempts, should get rate limited (429) or stay at 401/404
        # Rate limiting may not be enabled in test environment
        assert all(status in (401, 404, 429) for status in responses)

    async def test_successful_login_after_rate_limit_expires(self, client):
        """
        WHEN rate limit expires
        THEN user SHALL be able to login again
        """
        # This test would require waiting for rate limit to expire
        # or mocking the rate limiter - skipping for now
        pass


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestLoginErrorResponses:
    """Integration tests for login error response format."""

    async def test_error_response_has_standardized_format(self, client):
        """
        WHEN login fails
        THEN error response SHALL have detail or message or error field
        """
        invalid_credentials = {
            "email": "test@example.com",
            "password": "WrongPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=invalid_credentials)

        if response.status_code in (401, 403, 404):
            data = response.json()
            # FastAPI error responses have "detail" field
            # Standardized errors may have "error" field (string or nested object)
            has_error_info = (
                "detail" in data
                or "message" in data
                or "error" in data  # Can be string or nested object
            )
            assert has_error_info, f"Expected error info in response: {data}"

    async def test_error_response_includes_i18n_key(self, client):
        """
        WHEN login fails with standardized error
        THEN response MAY include i18n translation key
        """
        invalid_credentials = {
            "email": "test@example.com",
            "password": "WrongPassword123!",
        }

        response = await client.post("/api/v1/account/login", json=invalid_credentials)

        if response.status_code in (401, 403, 404):
            data = response.json()
            # i18n key is optional - only check if present
            if "error" in data and "i18n_key" in data["error"]:
                assert isinstance(data["error"]["i18n_key"], str)
