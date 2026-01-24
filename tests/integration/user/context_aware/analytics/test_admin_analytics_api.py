"""
Tests for Admin Analytics API Endpoints.

Tests all /admin/analytics/* endpoints with authentication.
"""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient

from ..conftest import (
    ContextAwareCSVReporter,
    create_context_test_result,
)
from ...conftest import BASE_URL


ADMIN_ANALYTICS_TESTS = [
    # Distribution endpoints
    {
        "test_id": "analytics_dist_001",
        "endpoint": "/api/v1/admin/analytics/users/distribution",
        "method": "GET",
        "expected_status": 200,
        "expected_fields": ["portfolio", "activity", "user_types", "executions", "totals"],
        "category": "analytics",
        "subcategory": "distribution",
    },
    {
        "test_id": "analytics_summary_001",
        "endpoint": "/api/v1/admin/analytics/users/summary",
        "method": "GET",
        "expected_status": 200,
        "expected_fields": ["total_users", "total_balance_usd", "portfolio_distribution"],
        "category": "analytics",
        "subcategory": "summary",
    },
    
    # Snapshot endpoints
    {
        "test_id": "analytics_latest_001",
        "endpoint": "/api/v1/admin/analytics/snapshots/latest",
        "method": "GET",
        "expected_status": [200, 404],  # 404 if no snapshots
        "category": "analytics",
        "subcategory": "snapshots",
    },
    {
        "test_id": "analytics_history_001",
        "endpoint": "/api/v1/admin/analytics/snapshots/history",
        "method": "GET",
        "params": {"days": 30},
        "expected_status": 200,
        "expected_fields": ["snapshots", "count"],
        "category": "analytics",
        "subcategory": "snapshots",
    },
    
    # Trend endpoints
    {
        "test_id": "analytics_wow_001",
        "endpoint": "/api/v1/admin/analytics/trends/week-over-week",
        "method": "GET",
        "expected_status": 200,
        "expected_fields": ["trends", "current_date", "comparison_date"],
        "category": "analytics",
        "subcategory": "trends",
    },
    {
        "test_id": "analytics_mom_001",
        "endpoint": "/api/v1/admin/analytics/trends/month-over-month",
        "method": "GET",
        "expected_status": 200,
        "expected_fields": ["trends"],
        "category": "analytics",
        "subcategory": "trends",
    },
    
    # Totals endpoint
    {
        "test_id": "analytics_totals_001",
        "endpoint": "/api/v1/admin/analytics/totals",
        "method": "GET",
        "expected_status": 200,
        "expected_fields": ["total_users", "total_balance_usd"],
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
    
    async def test_distribution_requires_auth(self):
        """Test that distribution endpoint requires authentication."""
        # Create unauthenticated client
        from httpx import AsyncClient
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.get("/api/v1/admin/analytics/users/distribution")
            assert response.status_code == 401
    
    @pytest.mark.parametrize("test_case", ADMIN_ANALYTICS_TESTS, ids=lambda t: t["test_id"])
    async def test_admin_endpoint(self, test_case: dict):
        """Test admin analytics endpoint."""
        endpoint = test_case["endpoint"]
        method = test_case["method"]
        params = test_case.get("params", {})
        
        # Make request
        if method == "GET":
            response = await self.client.get(endpoint, params=params)
        else:
            response = await self.client.request(method, endpoint, params=params)
        
        # Check status
        expected_status = test_case["expected_status"]
        if isinstance(expected_status, list):
            assert response.status_code in expected_status, \
                f"Expected status {expected_status}, got {response.status_code}"
        else:
            assert response.status_code == expected_status, \
                f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        # Check response fields if successful
        if response.status_code == 200:
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
            response_data={"content": str(response.json()) if response.status_code == 200 else response.text},
            response_time_ms=int(response.elapsed.total_seconds() * 1000) if hasattr(response, "elapsed") else 0,
        )
        self.reporter.add_result(result)


@pytest.mark.asyncio
@pytest.mark.integration
class TestAnalyticsSnapshotOperations:
    """Test analytics snapshot operations."""
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, authenticated_client, analytics_reporter, sample_analytics_snapshots):
        """Setup test fixtures with sample data."""
        self.client = authenticated_client
        self.reporter = analytics_reporter
        self.snapshots = sample_analytics_snapshots
    
    async def test_get_snapshot_by_date(self):
        """Test getting snapshot by specific date."""
        today = date.today().isoformat()
        response = await self.client.get(
            f"/api/v1/admin/analytics/snapshots/date/{today}"
        )
        
        # May be 200 or 404 depending on test data
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "snapshot_date" in data
            assert "portfolio" in data
    
    async def test_custom_trend_range(self):
        """Test custom date range trends."""
        current = date.today()
        comparison = current - timedelta(days=14)
        
        response = await self.client.get(
            "/api/v1/admin/analytics/trends/custom",
            params={
                "current_date": current.isoformat(),
                "comparison_date": comparison.isoformat(),
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
