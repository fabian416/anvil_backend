"""
Builder for creating Error Test Case data.

Provides fluent interface for creating parametrized error test cases
with expected error codes, HTTP statuses, and request configurations.

Usage:
    from tests.builders.error_test_case_builder import ErrorTestCaseBuilder, an_error_test_case

    # Build error test case
    test_case = (
        an_error_test_case()
        .for_endpoint("/api/v1/account/login")
        .with_method("POST")
        .with_request_data({"email": "invalid"})
        .expecting_error("AUTH_001")
        .expecting_status(401)
        .build()
    )

    # Use in parametrized tests
    @pytest.mark.parametrize("test_case", error_test_cases)
    def test_error_handling(test_case, client):
        response = getattr(client, test_case.method.lower())(
            test_case.endpoint,
            json=test_case.request_data
        )
        assert response.status_code == test_case.expected_status
"""

from dataclasses import dataclass, field
from typing import Any, Literal

# Import error codes if available
try:
    from app.domain.exceptions.error_codes import ErrorCode, get_error_code
except ImportError:
    ErrorCode = None
    get_error_code = None


HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"]


@dataclass
class ErrorTestCase:
    """
    Represents an error test case for parametrized testing.

    Attributes:
        name: Test case name/description
        endpoint: API endpoint path
        method: HTTP method
        request_data: Request body data
        expected_status: Expected HTTP status code
        expected_error_code: Expected error code string
        expected_i18n_key: Expected i18n translation key
        auth_required: Whether endpoint requires authentication
        admin_required: Whether endpoint requires admin role
        headers: Additional request headers
        query_params: Query parameters
        path_params: Path parameter values
    """

    name: str
    endpoint: str
    method: HttpMethod
    request_data: dict | None = None
    expected_status: int = 400
    expected_error_code: str = ""
    expected_i18n_key: str = ""
    auth_required: bool = True
    admin_required: bool = False
    headers: dict = field(default_factory=dict)
    query_params: dict = field(default_factory=dict)
    path_params: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Generate test case ID for pytest parametrize."""
        return f"{self.method}_{self.endpoint}_{self.expected_error_code}"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "method": self.method,
            "request_data": self.request_data,
            "expected_status": self.expected_status,
            "expected_error_code": self.expected_error_code,
            "expected_i18n_key": self.expected_i18n_key,
            "auth_required": self.auth_required,
            "admin_required": self.admin_required,
            "headers": self.headers,
            "query_params": self.query_params,
            "path_params": self.path_params,
        }


class ErrorTestCaseBuilder:
    """
    Fluent builder for Error Test Cases.

    Supports building test cases for all error scenarios
    with proper error codes and expected responses.
    """

    # Common error code to status mappings
    ERROR_STATUS_MAP = {
        # Auth errors
        "AUTH_001": 401,
        "AUTH_002": 401,
        "AUTH_003": 401,
        "AUTH_004": 401,
        "AUTH_005": 403,
        "AUTH_006": 403,
        "AUTH_007": 403,
        "AUTH_008": 403,
        "AUTH_009": 429,
        "AUTH_010": 401,
        # User errors
        "USER_001": 404,
        "USER_002": 409,
        "USER_003": 400,
        "USER_004": 400,
        "USER_005": 400,
        "USER_006": 400,
        "USER_014": 400,
        # Chat errors
        "CHAT_001": 404,
        "CHAT_002": 403,
        "CHAT_003": 400,
        "CHAT_004": 400,
        "CHAT_005": 422,
        # Subscription errors
        "SUB_001": 404,
        "SUB_002": 409,
        "SUB_003": 422,
        # Admin errors
        "ADM_001": 403,
        "ADM_002": 404,
        # LLM errors
        "LLM_001": 503,
        "LLM_002": 429,
        "LLM_003": 422,
        # Search errors
        "SRCH_001": 400,
        "SRCH_002": 400,
        # Validation errors
        "VAL_001": 400,
        "VAL_002": 400,
        "VAL_003": 400,
        "VAL_004": 400,
        # System errors
        "SYS_001": 500,
        "SYS_002": 502,
        "SYS_003": 503,
    }

    # Error code to i18n key mapping
    ERROR_I18N_MAP = {
        "AUTH_001": "errors.auth.invalid_credentials",
        "AUTH_002": "errors.auth.token_expired",
        "AUTH_003": "errors.auth.token_invalid",
        "AUTH_004": "errors.auth.token_missing",
        "AUTH_005": "errors.auth.insufficient_permissions",
        "USER_001": "errors.user.not_found",
        "USER_002": "errors.user.email_exists",
        "USER_014": "errors.user.password_same_as_current",
        "CHAT_001": "errors.chat.conversation_not_found",
        "CHAT_003": "errors.chat.message_empty",
        "SUB_001": "errors.subscription.not_found",
        "SUB_003": "errors.subscription.payment_failed",
    }

    def __init__(self):
        """Initialize with default values."""
        self._name: str = "Test error case"
        self._endpoint: str = "/"
        self._method: HttpMethod = "POST"
        self._request_data: dict | None = None
        self._expected_status: int | None = None
        self._expected_error_code: str = ""
        self._expected_i18n_key: str = ""
        self._auth_required: bool = True
        self._admin_required: bool = False
        self._headers: dict = {}
        self._query_params: dict = {}
        self._path_params: dict = {}

    def with_name(self, name: str) -> "ErrorTestCaseBuilder":
        """Set test case name."""
        self._name = name
        return self

    def for_endpoint(self, endpoint: str) -> "ErrorTestCaseBuilder":
        """Set target endpoint."""
        self._endpoint = endpoint
        return self

    def with_method(self, method: HttpMethod) -> "ErrorTestCaseBuilder":
        """Set HTTP method."""
        self._method = method
        return self

    def with_request_data(self, data: dict | None) -> "ErrorTestCaseBuilder":
        """Set request body data."""
        self._request_data = data
        return self

    def expecting_error(self, code: str) -> "ErrorTestCaseBuilder":
        """
        Set expected error code.

        Also sets expected status and i18n key if known.
        """
        self._expected_error_code = code

        # Auto-fill status and i18n key if known
        if self._expected_status is None and code in self.ERROR_STATUS_MAP:
            self._expected_status = self.ERROR_STATUS_MAP[code]

        if not self._expected_i18n_key and code in self.ERROR_I18N_MAP:
            self._expected_i18n_key = self.ERROR_I18N_MAP[code]

        return self

    def expecting_status(self, status: int) -> "ErrorTestCaseBuilder":
        """Set expected HTTP status code."""
        self._expected_status = status
        return self

    def expecting_i18n_key(self, key: str) -> "ErrorTestCaseBuilder":
        """Set expected i18n translation key."""
        self._expected_i18n_key = key
        return self

    def requires_auth(self, required: bool = True) -> "ErrorTestCaseBuilder":
        """Set whether authentication is required."""
        self._auth_required = required
        return self

    def requires_admin(self, required: bool = True) -> "ErrorTestCaseBuilder":
        """Set whether admin role is required."""
        self._admin_required = required
        if required:
            self._auth_required = True
        return self

    def with_headers(self, headers: dict) -> "ErrorTestCaseBuilder":
        """Set additional request headers."""
        self._headers = headers
        return self

    def with_query_params(self, params: dict) -> "ErrorTestCaseBuilder":
        """Set query parameters."""
        self._query_params = params
        return self

    def with_path_params(self, params: dict) -> "ErrorTestCaseBuilder":
        """Set path parameters."""
        self._path_params = params
        return self

    # Convenience methods for common error scenarios
    def for_invalid_credentials(self) -> "ErrorTestCaseBuilder":
        """Configure for invalid credentials error."""
        return (
            self.for_endpoint("/api/v1/account/login")
            .with_method("POST")
            .with_request_data({"email": "test@example.com", "password": "wrong"})
            .expecting_error("AUTH_001")
            .requires_auth(False)
            .with_name("Invalid credentials")
        )

    def for_token_missing(self) -> "ErrorTestCaseBuilder":
        """Configure for missing token error."""
        return (
            self.for_endpoint("/api/v1/account/me")
            .with_method("GET")
            .expecting_error("AUTH_004")
            .requires_auth(False)
            .with_name("Missing authentication token")
        )

    def for_token_expired(self) -> "ErrorTestCaseBuilder":
        """Configure for expired token error."""
        return (
            self.for_endpoint("/api/v1/account/me")
            .with_method("GET")
            .expecting_error("AUTH_002")
            .with_name("Expired authentication token")
        )

    def for_insufficient_permissions(self) -> "ErrorTestCaseBuilder":
        """Configure for insufficient permissions error."""
        return (
            self.for_endpoint("/api/v1/admin/users")
            .with_method("GET")
            .expecting_error("AUTH_005")
            .with_name("Insufficient permissions")
        )

    def for_user_not_found(self) -> "ErrorTestCaseBuilder":
        """Configure for user not found error."""
        return (
            self.for_endpoint("/api/v1/admin/users/nonexistent@example.com")
            .with_method("GET")
            .expecting_error("USER_001")
            .requires_admin()
            .with_name("User not found")
        )

    def for_email_exists(self) -> "ErrorTestCaseBuilder":
        """Configure for email exists error."""
        return (
            self.for_endpoint("/api/v1/account/signup")
            .with_method("POST")
            .with_request_data({"email": "existing@example.com", "password": "Test123!"})
            .expecting_error("USER_002")
            .requires_auth(False)
            .with_name("Email already exists")
        )

    def for_conversation_not_found(self) -> "ErrorTestCaseBuilder":
        """Configure for conversation not found error."""
        return (
            self.for_endpoint("/api/v1/chat/conversations/00000000-0000-0000-0000-000000000000")
            .with_method("GET")
            .expecting_error("CHAT_001")
            .with_name("Conversation not found")
        )

    def for_empty_message(self) -> "ErrorTestCaseBuilder":
        """Configure for empty message error."""
        return (
            self.for_endpoint("/api/v1/chat/conversations/{id}/messages")
            .with_method("POST")
            .with_request_data({"content": ""})
            .expecting_error("CHAT_003")
            .with_name("Empty message content")
        )

    def for_password_same_as_current(self) -> "ErrorTestCaseBuilder":
        """Configure for same password error."""
        return (
            self.for_endpoint("/api/v1/account/password")
            .with_method("PUT")
            .with_request_data({"current_password": "Test123!", "new_password": "Test123!"})
            .expecting_error("USER_014")
            .with_name("New password same as current")
        )

    def build(self) -> ErrorTestCase:
        """Build the error test case."""
        return ErrorTestCase(
            name=self._name,
            endpoint=self._endpoint,
            method=self._method,
            request_data=self._request_data,
            expected_status=self._expected_status or 400,
            expected_error_code=self._expected_error_code,
            expected_i18n_key=self._expected_i18n_key,
            auth_required=self._auth_required,
            admin_required=self._admin_required,
            headers=self._headers,
            query_params=self._query_params,
            path_params=self._path_params,
        )

    def build_dict(self) -> dict:
        """Build as dictionary."""
        return self.build().to_dict()

    @classmethod
    def an_error_test_case(cls) -> "ErrorTestCaseBuilder":
        """Start building an error test case."""
        return cls()

    @classmethod
    def build_auth_error_cases(cls) -> list[ErrorTestCase]:
        """Build common authentication error test cases."""
        return [
            cls().for_invalid_credentials().build(),
            cls().for_token_missing().build(),
            cls().for_token_expired().build(),
            cls().for_insufficient_permissions().build(),
        ]

    @classmethod
    def build_user_error_cases(cls) -> list[ErrorTestCase]:
        """Build common user error test cases."""
        return [
            cls().for_user_not_found().build(),
            cls().for_email_exists().build(),
            cls().for_password_same_as_current().build(),
        ]

    @classmethod
    def build_chat_error_cases(cls) -> list[ErrorTestCase]:
        """Build common chat error test cases."""
        return [
            cls().for_conversation_not_found().build(),
            cls().for_empty_message().build(),
        ]

    @classmethod
    def build_all_error_cases(cls) -> list[ErrorTestCase]:
        """Build all common error test cases."""
        return (
            cls.build_auth_error_cases()
            + cls.build_user_error_cases()
            + cls.build_chat_error_cases()
        )


# Convenience functions
def an_error_test_case() -> ErrorTestCaseBuilder:
    """Start building an error test case."""
    return ErrorTestCaseBuilder()


def auth_error_test_cases() -> list[ErrorTestCase]:
    """Get all authentication error test cases."""
    return ErrorTestCaseBuilder.build_auth_error_cases()


def user_error_test_cases() -> list[ErrorTestCase]:
    """Get all user error test cases."""
    return ErrorTestCaseBuilder.build_user_error_cases()


def chat_error_test_cases() -> list[ErrorTestCase]:
    """Get all chat error test cases."""
    return ErrorTestCaseBuilder.build_chat_error_cases()


def all_error_test_cases() -> list[ErrorTestCase]:
    """Get all common error test cases."""
    return ErrorTestCaseBuilder.build_all_error_cases()
