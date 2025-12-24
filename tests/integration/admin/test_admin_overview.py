"""
Integration tests for Admin Overview (Module 01).

Focus:
- Route availability under /api/v1/admin/*
- Basic access control behavior (401/403) without assuming local auth setup
"""

import pytest


@pytest.mark.integration
@pytest.mark.admin
class TestAdminOverviewDashboards:
    def test_security_dashboard_route_exists(self, client) -> None:
        """
        WHEN requesting the admin security dashboard
        THEN the API SHALL respond (200 for configured admin auth, otherwise 401/403).
        """
        response = client.get("/api/v1/admin/security/dashboard")
        assert response.status_code in (200, 401, 403)

    def test_chat_dashboard_route_exists(self, client) -> None:
        """
        WHEN requesting the admin chat dashboard
        THEN the API SHALL respond (200 for configured admin auth, otherwise 401/403).
        """
        response = client.get("/api/v1/admin/chat/dashboard")
        assert response.status_code in (200, 401, 403)

    def test_unauthenticated_returns_401_or_403(self, client) -> None:
        """
        WHEN requesting admin dashboards without auth
        THEN the API SHALL reject the request (401/403 depending on environment).
        """
        security = client.get("/api/v1/admin/security/dashboard")
        chat = client.get("/api/v1/admin/chat/dashboard")
        assert security.status_code in (401, 403)
        assert chat.status_code in (401, 403)

    def test_admin_transactions_route_exists(self, client) -> None:
        """
        WHEN requesting the admin transactions endpoint
        THEN the API SHALL respond (200 for configured admin auth, otherwise 401/403).
        """
        response = client.get("/api/v1/admin/transactions?limit=5&offset=0")
        assert response.status_code in (200, 401, 403)


