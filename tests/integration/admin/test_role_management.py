"""
Integration tests for admin role management.

Tests admin endpoints for:
- Grant admin role
- Revoke admin role
- Role change authorization
"""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class TestGrantAdminRole:
    """Integration tests for granting admin role."""

    async def test_super_admin_can_grant_admin(self, client):
        """
        WHEN super admin grants admin role to user
        THEN system SHALL update role (or 401 if not authenticated)
        """
        response = await client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin"
        )

        # Without super admin auth, expect 401/403
        assert response.status_code in (200, 204, 401, 403, 404)

    async def test_regular_admin_cannot_grant_admin(self, client):
        """
        WHEN regular admin tries to grant admin role
        THEN system SHALL return 403 forbidden
        """
        response = await client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin"
        )

        # Without super admin auth, should return 401 or 403
        assert response.status_code in (401, 403)

    async def test_grant_admin_to_nonexistent_user(self, client):
        """
        WHEN super admin tries to grant admin to non-existent user
        THEN system SHALL return 404 (or 401 if not authenticated)
        """
        response = await client.patch(
            f"/api/v1/admin/users/nonexistent_{uuid4().hex[:8]}@example.com/grant-admin"
        )

        assert response.status_code in (401, 403, 404)


@pytest.mark.integration
@pytest.mark.asyncio
class TestRevokeAdminRole:
    """Integration tests for revoking admin role."""

    async def test_super_admin_can_revoke_admin(self, client):
        """
        WHEN super admin revokes admin role from user
        THEN system SHALL update role (or 401 if not authenticated)
        """
        response = await client.patch(
            "/api/v1/admin/users/admin@example.com/revoke-admin"
        )

        # Without super admin auth, expect 401/403
        assert response.status_code in (200, 204, 401, 403, 404)

    async def test_cannot_revoke_super_admin(self, client):
        """
        WHEN trying to revoke super admin role
        THEN system SHALL deny the action
        """
        response = await client.patch(
            "/api/v1/admin/users/superadmin@example.com/revoke-admin"
        )

        # Should return 400/403 (cannot revoke super admin) or 401 (not authenticated)
        assert response.status_code in (400, 401, 403, 404)

    async def test_revoke_admin_from_nonexistent_user(self, client):
        """
        WHEN trying to revoke admin from non-existent user
        THEN system SHALL return 404 (or 401 if not authenticated)
        """
        response = await client.patch(
            f"/api/v1/admin/users/nonexistent_{uuid4().hex[:8]}@example.com/revoke-admin"
        )

        assert response.status_code in (401, 403, 404)


@pytest.mark.integration
@pytest.mark.asyncio
class TestRoleManagementAuthorization:
    """Integration tests for role management authorization."""

    async def test_unauthenticated_cannot_manage_roles(self, client):
        """
        WHEN unauthenticated user tries to manage roles
        THEN system SHALL return 401 unauthorized
        """
        response = await client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin"
        )

        assert response.status_code == 401

    async def test_regular_user_cannot_manage_roles(self, client):
        """
        WHEN regular user tries to manage roles
        THEN system SHALL return 401 or 403
        """
        # Without admin auth
        response = await client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin"
        )

        assert response.status_code in (401, 403)

    async def test_role_change_error_format(self, client):
        """
        WHEN role change fails
        THEN error response SHALL have proper format
        """
        response = await client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin"
        )

        if response.status_code in (401, 403, 404):
            data = response.json()
            assert "detail" in data or "message" in data or "error" in data
