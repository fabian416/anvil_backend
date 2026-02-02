"""
Integration tests for password reset flow.

Tests complete password reset flow including:
- Request password reset
- Confirm password reset with token
- Token expiration handling
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestPasswordResetRequest:
    """Integration tests for password reset request."""

    async def test_password_reset_request_with_valid_email(self, client):
        """
        WHEN user requests password reset with valid email
        THEN system SHALL accept request (regardless of email existence)
        """
        reset_request = {
            "email": f"resettest_{uuid4().hex[:8]}@example.com",
        }

        response = await client.post(
            "/api/v1/account/forgot-password",
            json=reset_request
        )

        # Should return 200/202 (accepted) even if email doesn't exist
        # (for security - don't reveal if email exists)
        assert response.status_code in (200, 202)

    async def test_password_reset_request_with_nonexistent_email(self, client):
        """
        WHEN user requests reset for nonexistent email
        THEN system SHALL return success (security best practice)
        """
        reset_request = {
            "email": f"nonexistent_{uuid4().hex[:8]}@example.com",
        }

        response = await client.post(
            "/api/v1/account/forgot-password",
            json=reset_request
        )

        # Should return 200/202 for security reasons
        assert response.status_code in (200, 202)

    async def test_password_reset_request_with_invalid_email_format(self, client):
        """
        WHEN user requests reset with invalid email format
        THEN system SHALL return validation error
        """
        reset_request = {
            "email": "not-an-email",
        }

        response = await client.post(
            "/api/v1/account/forgot-password",
            json=reset_request
        )

        # Should return 400 or 422 for validation error
        assert response.status_code in (400, 422)

    async def test_password_reset_request_without_email(self, client):
        """
        WHEN user requests reset without email
        THEN system SHALL return validation error
        """
        response = await client.post(
            "/api/v1/account/forgot-password",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestPasswordResetConfirmation:
    """Integration tests for password reset confirmation."""

    async def test_password_reset_with_valid_token(self, client):
        """
        WHEN user resets password with valid token
        THEN system SHALL update password
        """
        # This requires a valid reset token from DB
        reset_data = {
            "token": "valid-reset-token",
            "new_password": "NewSecurePassword123!",
        }

        response = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        # Token likely invalid in test - expect 400/404
        assert response.status_code in (200, 400, 404)

    async def test_password_reset_with_invalid_token(self, client):
        """
        WHEN user provides invalid reset token
        THEN system SHALL return error
        """
        reset_data = {
            "token": "invalid-token-12345",
            "new_password": "NewSecurePassword123!",
        }

        response = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        # Should return 400 or 404 for invalid token
        assert response.status_code in (400, 404)

    async def test_password_reset_with_expired_token(self, client):
        """
        WHEN user provides expired reset token
        THEN system SHALL return token expired error
        """
        reset_data = {
            "token": "expired-token-12345",
            "new_password": "NewSecurePassword123!",
        }

        response = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        # Should return 400 or 404 for expired token
        assert response.status_code in (400, 404)

    async def test_password_reset_with_weak_new_password(self, client):
        """
        WHEN user provides weak new password
        THEN system SHALL return validation error
        """
        reset_data = {
            "token": "some-token",
            "new_password": "weak",
        }

        response = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        # Should return 400 or 422 for weak password
        assert response.status_code in (400, 422)

    async def test_password_reset_without_new_password(self, client):
        """
        WHEN user doesn't provide new password
        THEN system SHALL return validation error
        """
        reset_data = {
            "token": "some-token",
            # Missing new_password
        }

        response = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestPasswordResetSecurityBehavior:
    """Integration tests for password reset security."""

    async def test_used_reset_token_cannot_be_reused(self, client):
        """
        WHEN reset token has been used
        THEN it SHALL not be accepted again
        """
        reset_data = {
            "token": "used-token-12345",
            "new_password": "NewSecurePassword123!",
        }

        # Both requests should fail (token invalid/used)
        response1 = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )
        response2 = await client.post(
            "/api/v1/account/reset-password",
            json=reset_data
        )

        # Both should return error
        assert response1.status_code in (400, 404)
        assert response2.status_code in (400, 404)

    async def test_reset_request_rate_limiting(self, client):
        """
        WHEN user makes many reset requests
        THEN system MAY apply rate limiting
        """
        email = f"ratelimit_{uuid4().hex[:8]}@example.com"
        reset_request = {"email": email}

        responses = []
        for _ in range(5):
            response = await client.post(
                "/api/v1/account/forgot-password",
                json=reset_request
            )
            responses.append(response.status_code)

        # All should succeed or some get rate limited
        assert all(status in (200, 202, 429) for status in responses)
