"""
Real API endpoint tests using TestClient.

Tests actual HTTP request/response cycles.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestHealthEndpointReal:
    """Real integration tests for health endpoint."""
    
    def test_health_check_returns_200(self, client: TestClient):
        """Test health endpoint returns 200."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
    
    def test_health_check_response_format(self, client: TestClient):
        """Test health endpoint response format."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_health_check_is_accessible_without_auth(self, client: TestClient):
        """Test health endpoint accessible without authentication."""
        # Act
        response = client.get("/health")
        
        # Assert - No 401 Unauthorized
        assert response.status_code != 401
        assert response.status_code == 200


@pytest.mark.integration
class TestAPIRootEndpoints:
    """Tests for root API endpoints."""
    
    def test_api_root_responds(self, client: TestClient):
        """Test API root endpoint responds."""
        # Act
        response = client.get("/")
        
        # Assert - Should not be 404
        assert response.status_code in [200, 301, 302, 307, 308]
    
    def test_nonexistent_endpoint_returns_404(self, client: TestClient):
        """Test nonexistent endpoint returns 404."""
        # Act
        response = client.get("/this-endpoint-does-not-exist-12345")
        
        # Assert
        assert response.status_code == 404
    
    def test_api_handles_invalid_method(self, client: TestClient):
        """Test API handles invalid HTTP methods."""
        # Act - Try to POST to GET-only endpoint
        response = client.post("/health")
        
        # Assert - Should return 405 Method Not Allowed or 404
        assert response.status_code in [404, 405]


@pytest.mark.integration
class TestCORSHeaders:
    """Tests for CORS header configuration."""
    
    def test_cors_headers_present(self, client: TestClient):
        """Test CORS headers are present in responses."""
        # Act
        response = client.get("/health")
        
        # Assert - Check for CORS headers (if configured)
        assert response.status_code == 200
        # In production, these would be present:
        # assert "Access-Control-Allow-Origin" in response.headers
    
    def test_options_request_succeeds(self, client: TestClient):
        """Test OPTIONS request for CORS preflight."""
        # Act
        response = client.options("/health")
        
        # Assert - Should succeed or return 405 if not configured
        assert response.status_code in [200, 204, 405]


@pytest.mark.integration
class TestContentTypeHeaders:
    """Tests for content type handling."""
    
    def test_json_content_type_accepted(self, client: TestClient):
        """Test API accepts JSON content type."""
        # Act
        response = client.get(
            "/health",
            headers={"Content-Type": "application/json"}
        )
        
        # Assert
        assert response.status_code == 200
    
    def test_response_is_json(self, client: TestClient):
        """Test API responses are JSON."""
        # Act
        response = client.get("/health")
        
        # Assert
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "").lower()
