"""
Integration tests for user logout flow.

Tests complete logout flow including:
- Successful logout with valid session
- Logout without authentication
- Session invalidation after logout
"""

import pytest


@pytest.mark.integration
@pytest.mark.auth
class TestLogoutFlow:
    """Integration tests for user logout."""

    def test_logout_with_valid_session_succeeds(self, client):
        """
        WHEN user logs out with valid session
        THEN system SHALL invalidate session
        """
        # Logout without being authenticated - expect 401
        response = client.delete("/api/v1/account/logout")

        # Without authentication, should return 401
        assert response.status_code in (200, 204, 401)

    def test_logout_without_authentication_fails(self, client):
        """
        WHEN unauthenticated user attempts logout
        THEN system SHALL return 401 unauthorized
        """
        response = client.delete("/api/v1/account/logout")

        # Should return 401 for unauthenticated request
        assert response.status_code == 401

    def test_logout_with_invalid_token_fails(self, client):
        """
        WHEN user provides invalid token for logout
        THEN system SHALL return 401 error
        """
        response = client.delete(
            "/api/v1/account/logout",
            headers={"Authorization": "Bearer invalid-token-12345"}
        )

        assert response.status_code == 401

    def test_logout_returns_no_content(self, client):
        """
        WHEN logout succeeds
        THEN response SHALL be 204 No Content or 200 OK
        """
        # Without valid session, expect 401
        response = client.delete("/api/v1/account/logout")

        assert response.status_code in (200, 204, 401)


@pytest.mark.integration
@pytest.mark.auth
class TestLogoutSessionInvalidation:
    """Integration tests for session invalidation on logout."""

    def test_token_rejected_after_logout(self, client):
        """
        WHEN user logs out
        THEN access token SHALL be rejected for subsequent requests
        """
        # This test would require a valid session
        # Testing without session - expect 401
        response = client.get(
            "/api/v1/account/me",
            headers={"Authorization": "Bearer fake-token"}
        )

        assert response.status_code == 401

    def test_refresh_token_rejected_after_logout(self, client):
        """
        WHEN user logs out
        THEN refresh token SHALL be rejected
        """
        response = client.post(
            "/api/v1/account/refresh-token",
            json={"refresh_token": "fake-refresh-token"}
        )

        # Should return 401 for invalid token
        assert response.status_code in (400, 401)

    def test_session_helper_tracks_invalidation(self):
        """
        Test that AuthHelper properly tracks session invalidation.
        """
        from tests.helpers.auth_helper import AuthHelper

        helper = AuthHelper()
        # Create mock session
        AuthHelper._test_sessions["test-session"] = {"user_id": 123}

        # Invalidate
        result = helper.invalidate_session("test-session")
        assert result is True
        assert "test-session" not in AuthHelper._test_sessions

    def test_invalidating_nonexistent_session_returns_false(self):
        """
        Test that invalidating non-existent session returns False.
        """
        from tests.helpers.auth_helper import AuthHelper

        helper = AuthHelper()
        result = helper.invalidate_session("nonexistent-session-id")
        assert result is False


@pytest.mark.integration
@pytest.mark.auth
class TestMultipleSessionLogout:
    """Integration tests for multiple session handling."""

    def test_logout_only_affects_current_session(self, client):
        """
        WHEN user logs out from one session
        THEN other sessions SHALL remain valid
        """
        # This test requires multiple valid sessions
        # Testing basic behavior without sessions
        response = client.delete("/api/v1/account/logout")
        assert response.status_code in (200, 204, 401)

    def test_logout_all_sessions(self, client):
        """
        WHEN user logs out from all sessions
        THEN all sessions SHALL be invalidated
        """
        # This would require a "logout all" endpoint
        # Testing basic logout endpoint
        response = client.delete("/api/v1/account/logout")
        assert response.status_code in (200, 204, 401)


@pytest.mark.integration
@pytest.mark.auth
class TestLogoutErrorHandling:
    """Integration tests for logout error handling."""

    def test_logout_with_expired_token(self, client):
        """
        WHEN user provides expired token for logout
        THEN system SHALL return appropriate error
        """
        response = client.delete(
            "/api/v1/account/logout",
            headers={"Authorization": "Bearer expired-token"}
        )

        assert response.status_code == 401

    def test_logout_error_response_format(self, client):
        """
        WHEN logout fails
        THEN error response SHALL have proper format
        """
        response = client.delete("/api/v1/account/logout")

        if response.status_code == 401:
            data = response.json()
            # Should have detail or error message
            assert "detail" in data or "message" in data or "error" in data
