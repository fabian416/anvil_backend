"""
Unit tests for admin policy management controllers.

These tests validate the module structure and basic expectations.
"""

import pytest


@pytest.mark.unit
class TestAdminPoliciesControllerStructure:
    def test_admin_policies_router_module_exists(self):
        try:
            from app.presentation.http.controllers.admin.policies.router import (
                create_admin_policies_router,
            )

            assert callable(create_admin_policies_router)
        except ImportError:
            pytest.fail("Admin policies router module missing")

    def test_openapi_includes_admin_policies_paths(self):
        """Smoke-test that the API router exposes /api/v1/admin/policies paths."""
        from app.run import make_app

        app = make_app()
        schema = app.openapi()
        paths = schema.get("paths", {})

        # Core paths we added
        assert "/api/v1/admin/policies/" in paths
        assert "/api/v1/admin/policies/{policy_id}" in paths
        assert "/api/v1/admin/policies/{policy_id}/rules" in paths
        assert "/api/v1/admin/policies/{policy_id}/rules/{rule_id}" in paths

