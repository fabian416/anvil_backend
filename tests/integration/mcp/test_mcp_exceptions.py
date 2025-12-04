"""
Integration tests for MCP exception hierarchy.

Tests error classification and retry decisions.
"""
import pytest

from app.infrastructure.mcp.exceptions import (
    MCPServerError,
    MCPRateLimitError,
    MCPTimeoutError,
    MCPServiceUnavailableError,
    MCPNetworkError,
    MCPAuthenticationError,
    MCPInvalidRequestError,
    MCPNotFoundError,
    MCPServerInternalError,
    MCPUnknownError,
    classify_http_error,
)


class TestMCPExceptions:
    """Test MCP exception hierarchy."""
    
    def test_rate_limit_error_retryable(self):
        """Test rate limit error is retryable."""
        error = MCPRateLimitError("Rate limit exceeded", "test_server")
        assert error.retryable is True
        assert error.server_name == "test_server"
    
    def test_auth_error_not_retryable(self):
        """Test authentication error is not retryable."""
        error = MCPAuthenticationError("Unauthorized", "test_server")
        assert error.retryable is False
    
    def test_invalid_request_not_retryable(self):
        """Test invalid request error is not retryable."""
        error = MCPInvalidRequestError("Bad request", "test_server")
        assert error.retryable is False
    
    def test_not_found_not_retryable(self):
        """Test not found error is not retryable."""
        error = MCPNotFoundError("Not found", "test_server")
        assert error.retryable is False
    
    def test_service_unavailable_retryable(self):
        """Test service unavailable is retryable."""
        error = MCPServiceUnavailableError("Service unavailable", "test_server")
        assert error.retryable is True
    
    def test_timeout_retryable(self):
        """Test timeout is retryable."""
        error = MCPTimeoutError("Request timeout", "test_server")
        assert error.retryable is True
    
    def test_classify_http_error_429(self):
        """Test HTTP 429 maps to rate limit error."""
        error = classify_http_error(429, "Rate limit", "test_server")
        assert isinstance(error, MCPRateLimitError)
        assert error.retryable is True
    
    def test_classify_http_error_401(self):
        """Test HTTP 401 maps to authentication error."""
        error = classify_http_error(401, "Unauthorized", "test_server")
        assert isinstance(error, MCPAuthenticationError)
        assert error.retryable is False
    
    def test_classify_http_error_404(self):
        """Test HTTP 404 maps to not found error."""
        error = classify_http_error(404, "Not found", "test_server")
        assert isinstance(error, MCPNotFoundError)
        assert error.retryable is False
    
    def test_classify_http_error_503(self):
        """Test HTTP 503 maps to service unavailable."""
        error = classify_http_error(503, "Service unavailable", "test_server")
        assert isinstance(error, MCPServiceUnavailableError)
        assert error.retryable is True
    
    def test_classify_http_error_unknown(self):
        """Test unknown HTTP status maps to unknown error."""
        error = classify_http_error(418, "I'm a teapot", "test_server")
        assert isinstance(error, MCPUnknownError)
        assert error.retryable is True  # Default to retryable
