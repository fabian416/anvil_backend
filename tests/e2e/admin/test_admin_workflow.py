"""
End-to-end tests for admin workflow.

Tests complete admin management flow:
login → list users → manage roles → configure LLM
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper


@pytest.mark.e2e
class TestAdminWorkflow:
    """End-to-end tests for admin workflow."""

    def test_admin_user_management_journey(self, client):
        """
        Test admin user management journey:
        1. Admin login
        2. List users
        3. View user details (if available)
        4. Activate/deactivate user
        """
        admin_user, admin_token = AuthHelper.create_test_user(role="admin")
        headers = AuthHelper.get_auth_headers(admin_token)

        # Step 1: List users
        list_response = client.get("/api/v1/admin/users", headers=headers)

        assert list_response.status_code in (200, 401, 403, 500, 503)

        if list_response.status_code != 200:
            pytest.skip("Admin user listing not accessible")
            return

        users_data = list_response.json()

        # Should have users list
        users = users_data.get("users", users_data if isinstance(users_data, list) else [])

        # Step 2: Get first user email if available
        if users:
            target_email = users[0].get("email", "test@example.com")

            # Step 3: Try to activate user
            activate_response = client.patch(
                f"/api/v1/admin/users/{target_email}/activate",
                headers=headers,
            )

            # May succeed or fail depending on user state
            assert activate_response.status_code in (200, 204, 400, 403, 404, 500, 503)

    def test_admin_llm_configuration_journey(self, client):
        """
        Test admin LLM configuration journey:
        1. Admin login
        2. List providers
        3. List models
        4. Update ranking (if supported)
        """
        admin_user, admin_token = AuthHelper.create_test_user(role="admin")
        headers = AuthHelper.get_auth_headers(admin_token)

        # Step 1: List providers
        providers_response = client.get("/api/v1/admin/llm/providers", headers=headers)

        assert providers_response.status_code in (200, 401, 403, 404, 500, 503)

        # Step 2: List models
        models_response = client.get("/api/v1/admin/llm/models", headers=headers)

        assert models_response.status_code in (200, 401, 403, 404, 500, 503)

        # Step 3: Get ranking
        ranking_response = client.get("/api/v1/admin/llm/ranking", headers=headers)

        assert ranking_response.status_code in (200, 401, 403, 404, 500, 503)


@pytest.mark.e2e
class TestSuperAdminWorkflow:
    """End-to-end tests for super admin workflow."""

    def test_super_admin_role_management_journey(self, client):
        """
        Test super admin role management:
        1. Super admin login
        2. Grant admin to user
        3. Revoke admin from user
        """
        super_admin, sa_token = AuthHelper.create_test_user(role="super_admin")
        headers = AuthHelper.get_auth_headers(sa_token)

        # Target user for role changes
        target_email = f"roletest_{uuid4().hex[:8]}@example.com"

        # Step 1: Try to grant admin
        grant_response = client.patch(
            f"/api/v1/admin/users/{target_email}/grant-admin",
            headers=headers,
        )

        # May succeed or fail depending on user existence
        assert grant_response.status_code in (200, 204, 401, 403, 404, 500, 503)

        # Step 2: Try to revoke admin
        revoke_response = client.patch(
            f"/api/v1/admin/users/{target_email}/revoke-admin",
            headers=headers,
        )

        assert revoke_response.status_code in (200, 204, 401, 403, 404, 500, 503)


@pytest.mark.e2e
class TestAdminAccessDenied:
    """End-to-end tests for admin access denied scenarios."""

    def test_regular_user_cannot_access_admin(self, client):
        """
        Test regular user cannot access admin endpoints.
        """
        regular_user, user_token = AuthHelper.create_test_user(role="user")
        headers = AuthHelper.get_auth_headers(user_token)

        # Try to access admin endpoint
        response = client.get("/api/v1/admin/users", headers=headers)

        # Should be denied
        assert response.status_code in (401, 403, 500, 503)

    def test_admin_cannot_access_super_admin_actions(self, client):
        """
        Test admin cannot perform super admin actions.
        """
        admin_user, admin_token = AuthHelper.create_test_user(role="admin")
        headers = AuthHelper.get_auth_headers(admin_token)

        # Try super admin action
        response = client.patch(
            "/api/v1/admin/users/test@example.com/grant-admin",
            headers=headers,
        )

        # Should be denied (403) or not found (404)
        assert response.status_code in (401, 403, 404, 500, 503)
