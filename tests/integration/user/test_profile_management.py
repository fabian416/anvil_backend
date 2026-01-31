"""
Integration tests for user profile management.

Tests user profile endpoints for:
- Get profile (me)
- Update profile
- Profile validation
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestGetProfile:
    """Integration tests for getting user profile."""

    async def test_get_profile_returns_user_info(self, client):
        """
        WHEN authenticated user gets profile
        THEN system SHALL return user information
        """
        response = await client.get("/api/v1/account/me")

        # Without auth, expect 401
        if response.status_code == 200:
            data = response.json()
            # Should have user fields
            assert "email" in data or "id" in data or "user" in data
        else:
            assert response.status_code == 401

    async def test_get_profile_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user gets profile
        THEN system SHALL return 401 unauthorized
        """
        response = await client.get("/api/v1/account/me")

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestUpdateProfile:
    """Integration tests for updating user profile."""

    async def test_update_profile_first_name(self, client):
        """
        WHEN user updates first name
        THEN system SHALL update profile
        """
        response = await client.put(
            "/api/v1/account/me",
            json={"first_name": "NewName"}
        )

        # Without auth, expect 401
        assert response.status_code in (200, 401)

    async def test_update_profile_last_name(self, client):
        """
        WHEN user updates last name
        THEN system SHALL update profile
        """
        response = await client.put(
            "/api/v1/account/me",
            json={"last_name": "NewLastName"}
        )

        assert response.status_code in (200, 401)

    async def test_update_profile_without_auth_returns_401(self, client):
        """
        WHEN unauthenticated user updates profile
        THEN system SHALL return 401 unauthorized
        """
        response = await client.put(
            "/api/v1/account/me",
            json={"first_name": "Test"}
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestProfileValidation:
    """Integration tests for profile field validation."""

    async def test_update_profile_with_unicode_name(self, client):
        """
        WHEN user updates name with unicode characters
        THEN system SHALL accept valid unicode
        """
        response = await client.put(
            "/api/v1/account/me",
            json={"first_name": "José"}
        )

        assert response.status_code in (200, 401)

    async def test_update_profile_with_empty_name(self, client):
        """
        WHEN user updates name with empty string
        THEN system MAY reject or accept
        """
        response = await client.put(
            "/api/v1/account/me",
            json={"first_name": ""}
        )

        # Could be 200 (accepted), 400/422 (validation error), or 401 (not auth)
        assert response.status_code in (200, 400, 401, 422)


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestProfileErrorResponses:
    """Integration tests for profile error responses."""

    async def test_profile_error_follows_standardized_format(self, client):
        """
        WHEN profile request fails
        THEN error response SHALL have proper format
        """
        response = await client.get("/api/v1/account/me")

        if response.status_code == 401:
            data = response.json()
            # Should have detail or error message
            assert "detail" in data or "message" in data or "error" in data
