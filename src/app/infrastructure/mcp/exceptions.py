"""
MCP Server Exception Hierarchy.

Standard exceptions for all MCP server errors, enabling better error classification
and retry decision-making.
"""


class MCPServerError(Exception):
    """
    Base exception for all MCP server errors.

    Attributes:
        message: Error message
        server_name: Name of the MCP server
        retryable: Whether this error should trigger a retry
    """

    retryable = True  # Default: most errors are retryable

    def __init__(self, message: str, server_name: str):
        """
        Initialize exception.

        Args:
            message: Error message
            server_name: Name of the MCP server
        """
        self.message = message
        self.server_name = server_name
        super().__init__(message)


class MCPRateLimitError(MCPServerError):
    """
    Raised when API rate limit is exceeded.

    Should trigger retry with exponential backoff.
    """

    retryable = True


class MCPTimeoutError(MCPServerError):
    """
    Raised when API request times out.

    Should trigger retry.
    """

    retryable = True


class MCPServiceUnavailableError(MCPServerError):
    """
    Raised when API service is unavailable (503, 502, 504).

    Should trigger retry.
    """

    retryable = True


class MCPNetworkError(MCPServerError):
    """
    Raised on network/connection errors.

    Should trigger retry.
    """

    retryable = True


class MCPAuthenticationError(MCPServerError):
    """
    Raised on authentication/authorization errors (401, 403).

    Should NOT retry (fix credentials first).
    """

    retryable = False


class MCPInvalidRequestError(MCPServerError):
    """
    Raised on invalid request errors (400).

    Should NOT retry (fix request first).
    """

    retryable = False


class MCPNotFoundError(MCPServerError):
    """
    Raised when resource is not found (404).

    Should NOT retry (resource doesn't exist).
    """

    retryable = False


class MCPServerInternalError(MCPServerError):
    """
    Raised on server internal errors (500).

    Should retry (server-side issue).
    """

    retryable = True


class MCPUnknownError(MCPServerError):
    """
    Raised for unclassified errors.

    Should retry (safer default).
    """

    retryable = True


# Exception mapping for HTTP status codes
HTTP_STATUS_TO_EXCEPTION = {
    429: MCPRateLimitError,
    401: MCPAuthenticationError,
    403: MCPAuthenticationError,
    400: MCPInvalidRequestError,
    404: MCPNotFoundError,
    500: MCPServerInternalError,
    502: MCPServiceUnavailableError,
    503: MCPServiceUnavailableError,
    504: MCPServiceUnavailableError,
}


def classify_http_error(
    status_code: int, message: str, server_name: str
) -> MCPServerError:
    """
    Classify HTTP error into appropriate exception.

    Args:
        status_code: HTTP status code
        message: Error message
        server_name: Name of the MCP server

    Returns:
        Appropriate MCP exception
    """
    exception_class = HTTP_STATUS_TO_EXCEPTION.get(status_code, MCPUnknownError)
    return exception_class(message, server_name)
