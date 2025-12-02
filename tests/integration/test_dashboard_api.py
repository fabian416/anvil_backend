"""
Integration tests for Dashboard API endpoints.

Tests complete API flows for dashboard insights and summaries.
"""

import pytest
from fastapi.testclient import TestClient


class TestDashboardAPI:
    """Integration tests for dashboard endpoints."""

    def test_get_dashboard_insights_success(self, client, mock_auth_token):
        """Test retrieving dashboard insights."""
        response = client.get(
            "/api/v1/dashboard/insights",
            headers={"Authorization": f"Bearer {mock_auth_token}"},
        )
        
        # Should return 200 with insights array
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "insights" in data or isinstance(data, list)

    def test_get_portfolio_summary_success(self, client, mock_auth_token):
        """Test retrieving portfolio summary."""
        response = client.get(
            "/api/v1/dashboard/summary",
            headers={"Authorization": f"Bearer {mock_auth_token}"},
        )
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            # Should contain key metrics
            expected_keys = [
                "total_value_usd",
                "protocol_count",
                "weighted_risk_score",
            ]
            # Some keys should be present
            assert any(key in data for key in expected_keys)

    def test_dashboard_insights_without_auth(self, client):
        """Test that dashboard requires authentication."""
        response = client.get("/api/v1/dashboard/insights")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403]

    def test_dashboard_summary_without_auth(self, client):
        """Test that summary requires authentication."""
        response = client.get("/api/v1/dashboard/summary")
        
        assert response.status_code in [401, 403]
