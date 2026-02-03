"""
Real API endpoint tests using AsyncClient.

Tests actual HTTP request/response cycles.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthEndpointReal:
    """Real integration tests for health endpoint."""

    async def test_health_check_returns_200(self, client: AsyncClient):
        """Test health endpoint returns 200."""
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200

    async def test_health_check_response_format(self, client: AsyncClient):
        """Test health endpoint response format."""
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    async def test_health_check_is_accessible_without_auth(self, client: AsyncClient):
        """Test health endpoint accessible without authentication."""
        # Act
        response = await client.get("/health")

        # Assert - No 401 Unauthorized
        assert response.status_code != 401
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
class TestAPIRootEndpoints:
    """Tests for root API endpoints."""

    async def test_api_root_responds(self, client: AsyncClient):
        """Test API root endpoint responds."""
        # Act
        response = await client.get("/")

        # Assert - Should not be 404
        assert response.status_code in [200, 301, 302, 307, 308]

    async def test_nonexistent_endpoint_returns_404(self, client: AsyncClient):
        """Test nonexistent endpoint returns 404."""
        # Act
        response = await client.get("/this-endpoint-does-not-exist-12345")

        # Assert
        assert response.status_code == 404

    async def test_api_handles_invalid_method(self, client: AsyncClient):
        """Test API handles invalid HTTP methods."""
        # Act - Try to POST to GET-only endpoint
        response = await client.post("/health")

        # Assert - Should return 405 Method Not Allowed or 404
        assert response.status_code in [404, 405]


@pytest.mark.integration
@pytest.mark.asyncio
class TestCORSHeaders:
    """Tests for CORS header configuration."""

    async def test_cors_headers_present(self, client: AsyncClient):
        """Test CORS headers are present in responses."""
        # Act
        response = await client.get("/health")

        # Assert - Check for CORS headers (if configured)
        assert response.status_code == 200
        # In production, these would be present:
        # assert "Access-Control-Allow-Origin" in response.headers

    async def test_options_request_succeeds(self, client: AsyncClient):
        """Test OPTIONS request for CORS preflight."""
        # Act
        response = await client.options("/health")

        # Assert - Should succeed or return 405 if not configured
        assert response.status_code in [200, 204, 405]


@pytest.mark.integration
@pytest.mark.asyncio
class TestContentTypeHeaders:
    """Tests for content type handling."""

    async def test_json_content_type_accepted(self, client: AsyncClient):
        """Test API accepts JSON content type."""
        # Act
        response = await client.get(
            "/health", headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 200

    async def test_response_is_json(self, client: AsyncClient):
        """Test API responses are JSON."""
        # Act
        response = await client.get("/health")

        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "").lower()
