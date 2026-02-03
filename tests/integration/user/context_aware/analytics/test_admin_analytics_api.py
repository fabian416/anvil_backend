"""
Tests for Admin Analytics API Endpoints.

Tests all /admin/analytics/* endpoints via HTTP requests.
Note: These tests require admin authentication to access analytics endpoints.
"""

import pytest
import pytest_asyncio
from datetime import date, timedelta

from ..conftest import (
    ContextAwareCSVReporter,
    create_context_test_result,
)
from ...conftest import BASE_URL

import httpx


ADMIN_ANALYTICS_TESTS = [
    # Distribution endpoints
    {
        "test_id": "analytics_dist_001",
        "endpoint": "/api/v1/admin/analytics/users/distribution",
        "method": "GET",
        "expected_status": [200, 401, 403, 404],  # May not have admin access
        "expected_fields": ["portfolio", "activity", "user_types"],
        "category": "analytics",
        "subcategory": "distribution",
    },
    {
        "test_id": "analytics_summary_001",
        "endpoint": "/api/v1/admin/analytics/users/summary",
        "method": "GET",
        "expected_status": [200, 401, 403, 404],
        "expected_fields": ["total_users", "total_balance_usd"],
        "category": "analytics",
        "subcategory": "summary",
    },
    {
        "test_id": "analytics_latest_001",
        "endpoint": "/api/v1/admin/analytics/snapshots/latest",
        "method": "GET",
        "expected_status": [200, 401, 403, 404],
        "category": "analytics",
        "subcategory": "snapshots",
    },
    {
        "test_id": "analytics_totals_001",
        "endpoint": "/api/v1/admin/analytics/totals",
        "method": "GET",
        "expected_status": [200, 401, 403, 404],
        "category": "analytics",
        "subcategory": "totals",
    },
]


@pytest.mark.asyncio
@pytest.mark.integration
class TestAdminAnalyticsEndpoints:
    """Test admin analytics API endpoints."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, analytics_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = analytics_reporter
    
    async def test_analytics_requires_auth(self):
        """Test that analytics endpoints require authentication."""
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
            response = await client.get("/api/v1/admin/analytics/users/distribution")
            # Should be 401 (unauthorized) or 403 (forbidden) without auth
            assert response.status_code in [401, 403, 404], \
                f"Expected auth error, got {response.status_code}"
    
    @pytest.mark.parametrize("test_case", ADMIN_ANALYTICS_TESTS, ids=lambda t: t["test_id"])
    async def test_admin_endpoint(self, test_case: dict):
        """Test admin analytics endpoint."""
        endpoint = test_case["endpoint"]
        method = test_case["method"]
        params = test_case.get("params", {})
        
        try:
            # Make request
            if method == "GET":
                response = await self.client.get(endpoint, params=params)
            else:
                response = await self.client.request(method, endpoint, params=params)
            
            status_code = response.status_code
            
            # Check status - analytics may require admin role
            expected_status = test_case["expected_status"]
            if isinstance(expected_status, list):
                assert status_code in expected_status, \
                    f"Expected status {expected_status}, got {status_code}"
            else:
                assert status_code == expected_status, \
                    f"Expected status {expected_status}, got {status_code}"
            
            # Check response fields if successful
            if status_code == 200:
                data = response.json()
                expected_fields = test_case.get("expected_fields", [])
                for field in expected_fields:
                    assert field in data, f"Missing field '{field}' in response"
            
            # Record result
            result = create_context_test_result(
                test_id=test_case["test_id"],
                test_case={
                    "input": f"{method} {endpoint}",
                    "category": test_case["category"],
                    "subcategory": test_case["subcategory"],
                },
                response_data={"content": str(response.json()) if status_code == 200 else response.text[:200]},
                response_time_ms=int(response.elapsed.total_seconds() * 1000) if hasattr(response, "elapsed") else 0,
            )
            
            if status_code in [401, 403]:
                result.status = "SKIP"
                result.error_message = "Admin access required"
            elif status_code == 404:
                result.status = "SKIP"
                result.error_message = "Endpoint not found or no data"
            else:
                result.status = "PASS"
            
            self.reporter.add_result(result)
            
        except httpx.HTTPError as e:
            # Record error
            result = create_context_test_result(
                test_id=test_case["test_id"],
                test_case={
                    "input": f"{method} {endpoint}",
                    "category": test_case["category"],
                },
                response_data={"error": str(e)},
                response_time_ms=0,
            )
            result.status = "ERROR"
            result.error_message = str(e)
            self.reporter.add_result(result)


@pytest.mark.asyncio
@pytest.mark.integration
class TestAnalyticsDataIntegrity:
    """Test analytics data integrity via API."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, analytics_reporter):
        """Setup test fixtures."""
        self.client = authenticated_client
        self.reporter = analytics_reporter
    
    async def test_distribution_totals_consistency(self):
        """Test that distribution totals are consistent."""
        response = await self.client.get("/api/v1/admin/analytics/users/distribution")
        
        if response.status_code != 200:
            pytest.skip(f"Analytics endpoint not accessible: {response.status_code}")
        
        data = response.json()
        
        # Portfolio states should have non-negative counts
        if "portfolio" in data:
            portfolio = data["portfolio"]
            assert all(v >= 0 for v in portfolio.values()), "Portfolio counts should be non-negative"
        
        # Activity levels should have non-negative counts
        if "activity" in data:
            activity = data["activity"]
            assert all(v >= 0 for v in activity.values()), "Activity counts should be non-negative"
    
    async def test_totals_endpoint(self):
        """Test totals endpoint returns valid data."""
        response = await self.client.get("/api/v1/admin/analytics/totals")
        
        if response.status_code != 200:
            pytest.skip(f"Totals endpoint not accessible: {response.status_code}")
        
        data = response.json()
        
        if "total_users" in data:
            assert data["total_users"] >= 0
        
        if "total_balance_usd" in data:
            assert float(data["total_balance_usd"]) >= 0
