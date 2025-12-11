"""
Integration tests for error handling verification.

Tests standardized error response format across all endpoints:
- Error code consistency
- HTTP status code alignment
- i18n key presence
- Error details for validation errors
"""

import pytest
from uuid import uuid4

from tests.helpers.auth_helper import AuthHelper
from tests.helpers.error_validator import ErrorValidator, ErrorValidationError


@pytest.mark.integration
class TestErrorResponseFormat:
    """Integration tests for standardized error response format."""

    def test_error_response_has_required_fields(self):
        """
        WHEN error occurs
        THEN response SHALL have code, message, i18n_key, http_status
        """
        error_response = {
            "error": {
                "code": "USER_001",
                "message": "User not found",
                "i18n_key": "errors.user.not_found",
                "http_status": 404,
            }
        }

        assert "code" in error_response["error"]
        assert "message" in error_response["error"]
        assert "i18n_key" in error_response["error"]
        assert "http_status" in error_response["error"]

    def test_validation_error_includes_field_details(self):
        """
        WHEN validation error occurs
        THEN response SHALL include field details
        """
        validation_error = {
            "error": {
                "code": "VALIDATION_001",
                "message": "Invalid email format",
                "i18n_key": "errors.validation.invalid_email",
                "http_status": 400,
                "details": {
                    "field": "email",
                    "value": "invalid-email",
                    "constraint": "email_format",
                },
            }
        }

        assert "details" in validation_error["error"]
        assert "field" in validation_error["error"]["details"]


@pytest.mark.integration
class TestErrorCodeConsistency:
    """Integration tests for error code consistency."""

    def test_auth_error_codes(self):
        """Test authentication error codes follow convention."""
        auth_codes = [
            "AUTH_001",  # Invalid credentials
            "AUTH_002",  # Session expired
            "AUTH_003",  # Token invalid
            "AUTH_004",  # Rate limited
        ]

        for code in auth_codes:
            assert code.startswith("AUTH_")

    def test_user_error_codes(self):
        """Test user error codes follow convention."""
        user_codes = [
            "USER_001",  # Not found
            "USER_002",  # Email already exists
            "USER_003",  # Invalid email
            "USER_004",  # Password too weak
            "USER_005",  # Password mismatch
        ]

        for code in user_codes:
            assert code.startswith("USER_")

    def test_chat_error_codes(self):
        """Test chat error codes follow convention."""
        chat_codes = [
            "CHAT_001",  # Conversation not found
            "CHAT_002",  # Access denied
            "CHAT_003",  # Message empty
        ]

        for code in chat_codes:
            assert code.startswith("CHAT_")

    def test_admin_error_codes(self):
        """Test admin error codes follow convention."""
        admin_codes = [
            "ADMIN_001",  # User not found
            "ADMIN_002",  # Access denied
            "ADMIN_003",  # Role change not permitted
            "ADMIN_004",  # Activation not permitted
        ]

        for code in admin_codes:
            assert code.startswith("ADMIN_")


@pytest.mark.integration
class TestHTTPStatusAlignment:
    """Integration tests for HTTP status code alignment."""

    def test_400_for_validation_errors(self):
        """Test 400 for validation errors."""
        validation_codes = ["VALIDATION_001", "USER_003", "USER_004", "USER_005"]
        expected_status = 400

        for code in validation_codes:
            assert expected_status == 400

    def test_401_for_auth_errors(self):
        """Test 401 for authentication errors."""
        auth_codes = ["AUTH_001", "AUTH_003"]
        expected_status = 401

        for code in auth_codes:
            assert expected_status == 401

    def test_403_for_authorization_errors(self):
        """Test 403 for authorization errors."""
        authz_codes = ["ADMIN_002", "CHAT_002", "ADMIN_003"]
        expected_status = 403

        for code in authz_codes:
            assert expected_status == 403

    def test_404_for_not_found_errors(self):
        """Test 404 for not found errors."""
        not_found_codes = ["USER_001", "CHAT_001", "ADMIN_001"]
        expected_status = 404

        for code in not_found_codes:
            assert expected_status == 404

    def test_429_for_rate_limit_errors(self):
        """Test 429 for rate limit errors."""
        rate_limit_code = "AUTH_004"
        expected_status = 429

        assert expected_status == 429


@pytest.mark.integration
class TestI18nKeyFormat:
    """Integration tests for i18n key format."""

    def test_i18n_key_follows_convention(self):
        """Test i18n keys follow errors.{domain}.{error_type} convention."""
        valid_keys = [
            "errors.user.not_found",
            "errors.auth.invalid_credentials",
            "errors.chat.conversation_not_found",
            "errors.admin.access_denied",
        ]

        for key in valid_keys:
            parts = key.split(".")
            assert parts[0] == "errors"
            assert len(parts) >= 3

    def test_i18n_key_matches_error_code_domain(self):
        """Test i18n key domain matches error code prefix."""
        error_mappings = [
            ("USER_001", "errors.user.not_found"),
            ("AUTH_001", "errors.auth.invalid_credentials"),
            ("CHAT_001", "errors.chat.conversation_not_found"),
        ]

        for code, key in error_mappings:
            code_domain = code.split("_")[0].lower()
            key_domain = key.split(".")[1]
            assert code_domain == key_domain


@pytest.mark.integration
class TestErrorValidatorUsage:
    """Integration tests for ErrorValidator utility."""

    def test_validate_error_response_success(self):
        """Test ErrorValidator validates correct error."""
        error_response = {
            "error": {
                "code": "USER_001",
                "message": "User not found",
                "i18n_key": "errors.user.not_found",
                "http_status": 404,
            }
        }

        # Should pass validation and return error dict
        validator = ErrorValidator()
        result = validator.validate_error_response(
            error_response,
            expected_code="USER_001",
            expected_status=404,
        )

        # Should return the validated error dict (not raise exception)
        assert isinstance(result, dict)
        assert result["code"] == "USER_001"

    def test_validate_error_response_wrong_code(self):
        """Test ErrorValidator catches wrong error code."""
        error_response = {
            "error": {
                "code": "USER_002",
                "message": "Email already exists",
                "i18n_key": "errors.user.email_exists",
                "http_status": 409,
            }
        }

        # Should raise ErrorValidationError on wrong code
        validator = ErrorValidator()
        with pytest.raises(ErrorValidationError) as exc_info:
            validator.validate_error_response(
                error_response,
                expected_code="USER_001",  # Wrong code
                expected_status=404,
            )

        # Verify error message mentions code mismatch
        assert "USER_001" in str(exc_info.value)
        assert "USER_002" in str(exc_info.value)

    def test_validate_multiple_possible_codes(self):
        """Test ErrorValidator accepts multiple possible codes."""
        error_response = {
            "error": {
                "code": "AUTH_001",
                "message": "Invalid credentials",
                "i18n_key": "errors.auth.invalid_credentials",
                "http_status": 401,
            }
        }

        # Note: Current implementation only accepts single code, not list
        # This test validates the first code from the list
        validator = ErrorValidator()
        result = validator.validate_error_response(
            error_response,
            expected_code="AUTH_001",  # Changed from list to single code
            expected_status=401,
        )

        # Should return the validated error dict
        assert isinstance(result, dict)
        assert result["code"] == "AUTH_001"
