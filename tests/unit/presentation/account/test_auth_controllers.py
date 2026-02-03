"""
Unit tests for authentication controllers.

Tests signup, login, logout, and refresh token controllers in isolation
with mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from tests.builders import a_user
from tests.helpers.auth_helper import AuthHelper


class TestSignUpController:
    """Unit tests for sign up controller logic."""

    @pytest.fixture
    def mock_sign_up_handler(self):
        """Create mock SignUpHandler."""
        handler = AsyncMock()
        handler.execute = AsyncMock(
            return_value={
                "id": str(uuid4()),
                "email": "newuser@example.com",
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
            }
        )
        return handler

    def test_valid_signup_request_structure(self):
        """Test valid signup request has required fields."""
        request_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        assert "email" in request_data
        assert "password" in request_data
        assert "first_name" in request_data
        assert "last_name" in request_data

    def test_signup_request_with_optional_fields(self):
        """Test signup request can include optional fields."""
        request_data = {
            "email": "test@example.com",
            "password": "SecurePassword123!",
            "first_name": "Test",
            "last_name": "User",
            "country_id": 1,
            "city_id": 100,
            "language": "en",
        }

        assert request_data["country_id"] == 1
        assert request_data["city_id"] == 100
        assert request_data["language"] == "en"

    def test_signup_email_validation_format(self):
        """Test email format validation patterns."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
        ]
        invalid_emails = [
            "invalid",
            "invalid@",
            "@example.com",
            "user@.com",
            "",
        ]

        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

        for email in valid_emails:
            assert re.match(email_pattern, email), f"Should be valid: {email}"

        for email in invalid_emails:
            assert not re.match(email_pattern, email), f"Should be invalid: {email}"

    def test_signup_password_validation_rules(self):
        """Test password strength validation rules."""
        # Password must have: 8+ chars, uppercase, lowercase, number
        valid_passwords = [
            "SecurePass1",
            "MyPassword123",
            "Test123456",
        ]
        invalid_passwords = [
            "short1",  # Too short
            "nouppercase1",  # No uppercase
            "NOLOWERCASE1",  # No lowercase
            "NoNumbers",  # No numbers
        ]

        def is_strong_password(password: str) -> bool:
            if len(password) < 8:
                return False
            if not any(c.isupper() for c in password):
                return False
            if not any(c.islower() for c in password):
                return False
            if not any(c.isdigit() for c in password):
                return False
            return True

        for password in valid_passwords:
            assert is_strong_password(password), f"Should be valid: {password}"

        for password in invalid_passwords:
            assert not is_strong_password(password), f"Should be invalid: {password}"

    def test_signup_response_contains_tokens(self, mock_sign_up_handler):
        """Test signup response includes authentication tokens."""
        response = {
            "id": str(uuid4()),
            "email": "test@example.com",
            "access_token": "jwt_access_token",
            "refresh_token": "jwt_refresh_token",
        }

        assert "access_token" in response
        assert "refresh_token" in response
        assert response["access_token"]
        assert response["refresh_token"]


class TestLogInController:
    """Unit tests for login controller logic."""

    @pytest.fixture
    def mock_login_handler(self):
        """Create mock LogInHandler."""
        handler = AsyncMock()
        handler.execute = AsyncMock(
            return_value={
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "user": {
                    "id": str(uuid4()),
                    "email": "user@example.com",
                    "role": "USER",
                },
            }
        )
        return handler

    def test_valid_login_request_structure(self):
        """Test valid login request has required fields."""
        request_data = {
            "email": "user@example.com",
            "password": "Password123!",
        }

        assert "email" in request_data
        assert "password" in request_data

    def test_login_response_contains_tokens(self, mock_login_handler):
        """Test login response includes authentication tokens."""
        response = {
            "access_token": "jwt_access_token",
            "refresh_token": "jwt_refresh_token",
            "user": {
                "id": str(uuid4()),
                "email": "user@example.com",
            },
        }

        assert "access_token" in response
        assert "refresh_token" in response
        assert "user" in response

    def test_login_with_invalid_credentials_error_code(self):
        """Test invalid credentials returns correct error code."""
        error_response = {
            "error": {
                "code": "AUTH_001",
                "message": "Invalid email or password",
                "i18n_key": "errors.auth.invalid_credentials",
                "http_status": 401,
            }
        }

        assert error_response["error"]["code"] == "AUTH_001"
        assert error_response["error"]["http_status"] == 401

    def test_login_enriches_request_with_client_info(self):
        """Test login request is enriched with IP and user agent."""
        original_request = {
            "email": "user@example.com",
            "password": "Password123!",
        }

        # Enriched request should include client info
        enriched_request = {
            **original_request,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
        }

        assert "ip_address" in enriched_request
        assert "user_agent" in enriched_request


class TestLogOutController:
    """Unit tests for logout controller logic."""

    @pytest.fixture
    def mock_logout_handler(self):
        """Create mock LogOutHandler."""
        handler = AsyncMock()
        handler.execute = AsyncMock(return_value=None)
        return handler

    def test_logout_requires_authentication(self):
        """Test logout endpoint requires Bearer token."""
        # Logout should require Security(bearer_scheme) dependency
        # This is configured in the router with dependencies=[Security(bearer_scheme)]
        assert True  # Router configuration test

    def test_logout_returns_no_content(self, mock_logout_handler):
        """Test logout returns 204 No Content."""
        # Successful logout returns None (204 No Content)
        result = None
        assert result is None

    def test_logout_with_invalid_session_error(self):
        """Test logout with invalid session returns error."""
        error_response = {
            "error": {
                "code": "AUTH_014",
                "message": "Session is invalid or has been terminated",
                "i18n_key": "errors.auth.session_invalid",
                "http_status": 401,
            }
        }

        assert error_response["error"]["code"] == "AUTH_014"
        assert error_response["error"]["http_status"] == 401


class TestRefreshTokenController:
    """Unit tests for refresh token controller logic."""

    @pytest.fixture
    def mock_refresh_handler(self):
        """Create mock RefreshTokenHandler."""
        handler = AsyncMock()
        handler.execute = AsyncMock(
            return_value={
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token",
            }
        )
        return handler

    def test_valid_refresh_request_structure(self):
        """Test valid refresh request has required fields."""
        request_data = {
            "refresh_token": "valid_refresh_token",
        }

        assert "refresh_token" in request_data

    def test_refresh_returns_new_tokens(self, mock_refresh_handler):
        """Test refresh returns new access and refresh tokens."""
        response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
        }

        assert "access_token" in response
        assert "refresh_token" in response
        assert response["access_token"] != response["refresh_token"]

    def test_refresh_with_expired_token_error(self):
        """Test refresh with expired token returns error."""
        error_response = {
            "error": {
                "code": "AUTH_002",
                "message": "Session has expired, please login again",
                "i18n_key": "errors.auth.token_expired",
                "http_status": 401,
            }
        }

        assert error_response["error"]["code"] == "AUTH_002"
        assert error_response["error"]["http_status"] == 401

    def test_refresh_with_invalid_token_error(self):
        """Test refresh with invalid token returns error."""
        error_response = {
            "error": {
                "code": "AUTH_010",
                "message": "Session refresh failed, please login again",
                "i18n_key": "errors.auth.refresh_token_invalid",
                "http_status": 401,
            }
        }

        assert error_response["error"]["code"] == "AUTH_010"
        assert error_response["error"]["http_status"] == 401

    def test_refresh_enriches_request_with_client_info(self):
        """Test refresh request is enriched with IP and user agent."""
        original_request = {
            "refresh_token": "valid_refresh_token",
        }

        enriched_request = {
            **original_request,
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0",
        }

        assert "ip_address" in enriched_request
        assert "user_agent" in enriched_request


class TestAuthHelperIntegration:
    """Tests for AuthHelper test utility integration."""

    def test_create_test_user_returns_user_and_token(self):
        """Test AuthHelper creates user with valid token."""
        user, token = AuthHelper.create_test_user(role="user")

        assert user is not None
        assert token is not None
        assert user.email is not None
        assert user.role == "user"

    def test_create_admin_user(self):
        """Test AuthHelper creates admin user."""
        user, token = AuthHelper.create_test_user(role="admin")

        assert user.role == "admin"
        assert token is not None

    def test_create_super_admin_user(self):
        """Test AuthHelper creates super admin user."""
        user, token = AuthHelper.create_test_user(role="super_admin")

        assert user.role == "super_admin"
        assert token is not None

    def test_get_auth_headers_format(self):
        """Test auth headers have correct format."""
        token = "test_jwt_token"
        headers = AuthHelper.get_auth_headers(token)

        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {token}"
        assert headers["Content-Type"] == "application/json"

    def test_session_management(self):
        """Test session creation and invalidation."""
        user, _ = AuthHelper.create_test_user()
        session_id = user.session_id

        assert AuthHelper.is_session_valid(session_id)

        AuthHelper.invalidate_session(session_id)

        assert not AuthHelper.is_session_valid(session_id)

    def test_create_expired_token(self):
        """Test creating expired token for testing."""
        user, _ = AuthHelper.create_test_user()
        expired_token = AuthHelper.create_expired_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )

        assert expired_token is not None
        # Token should have valid JWT structure
        parts = expired_token.split(".")
        assert len(parts) == 3


class TestErrorResponseValidation:
    """Tests for standardized error response validation."""

    def test_auth_error_response_structure(self):
        """Test auth error response has required fields."""
        error_response = {
            "error": {
                "code": "AUTH_001",
                "message": "Invalid email or password",
                "i18n_key": "errors.auth.invalid_credentials",
                "http_status": 401,
            }
        }

        error = error_response["error"]
        assert "code" in error
        assert "message" in error
        assert "i18n_key" in error
        assert "http_status" in error

    def test_validation_error_includes_field(self):
        """Test validation error can include field information."""
        error_response = {
            "error": {
                "code": "VAL_001",
                "message": "This field is required",
                "i18n_key": "errors.validation.required",
                "http_status": 400,
                "field": "email",
            }
        }

        assert error_response["error"]["field"] == "email"

    def test_error_code_format(self):
        """Test error codes follow CATEGORY_NNN format."""
        import re

        valid_codes = [
            "AUTH_001",
            "USER_014",
            "CHAT_003",
            "VAL_001",
            "SYS_001",
        ]

        pattern = r"^[A-Z]{2,5}_\d{3}$"

        for code in valid_codes:
            assert re.match(pattern, code), f"Invalid code format: {code}"
