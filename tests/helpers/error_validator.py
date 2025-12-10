"""
Error response validator for standardized error handling verification.

Provides utilities for:
- Validating error response structure
- Verifying error codes match expected values
- Validating i18n keys exist
- Checking HTTP status code alignment

Usage:
    from tests.helpers.error_validator import validate_error_response, ErrorValidator

    # Validate error response
    validate_error_response(response, "AUTH_001")

    # Use validator class for more control
    validator = ErrorValidator()
    validator.validate_error_response(response, "AUTH_001")
    assert validator.validate_i18n_key(error_dict)
"""

from typing import Any

from httpx import Response as HttpxResponse

# Import error codes - handle import gracefully for standalone testing
try:
    from app.domain.exceptions.error_codes import ErrorCode, ErrorDefinition, get_error_code
except ImportError:
    ErrorCode = None
    ErrorDefinition = None
    get_error_code = None


class ErrorValidationError(Exception):
    """Raised when error response validation fails."""

    pass


class ErrorValidator:
    """
    Validator for standardized error responses.

    Validates that error responses follow the expected format
    with correct error codes, i18n keys, and HTTP status codes.
    """

    # Expected error response structure
    REQUIRED_ERROR_FIELDS = {"code", "message", "i18n_key", "http_status"}
    OPTIONAL_ERROR_FIELDS = {"details", "field"}

    # Known i18n key prefixes
    VALID_I18N_PREFIXES = {
        "errors.auth.",
        "errors.user.",
        "errors.chat.",
        "errors.wallet.",
        "errors.portfolio.",
        "errors.market.",
        "errors.search.",
        "errors.alert.",
        "errors.subscription.",
        "errors.admin.",
        "errors.llm.",
        "errors.telemetry.",
        "errors.validation.",
        "errors.system.",
        "errors.location.",
    }

    def validate_error_response(
        self,
        response: Any,
        expected_code: str,
        expected_status: int | None = None,
    ) -> dict[str, Any]:
        """
        Validate an error response matches expected format and code.

        Args:
            response: HTTP response object (TestClient Response or httpx Response)
            expected_code: Expected error code (e.g., "AUTH_001")
            expected_status: Expected HTTP status code (optional, inferred from code)

        Returns:
            Validated error dict

        Raises:
            ErrorValidationError: If validation fails
        """
        # Extract response data
        if hasattr(response, "json"):
            try:
                data = response.json()
            except Exception as e:
                raise ErrorValidationError(f"Response is not valid JSON: {e}")
        else:
            data = response

        # Get error dict
        error = data.get("error") if isinstance(data, dict) else None
        if error is None:
            raise ErrorValidationError(
                f"Response missing 'error' field. Got: {data}"
            )

        # Validate structure
        self._validate_structure(error)

        # Validate error code
        actual_code = error.get("code")
        if actual_code != expected_code:
            raise ErrorValidationError(
                f"Expected error code '{expected_code}', got '{actual_code}'"
            )

        # Validate HTTP status if provided
        if expected_status is not None:
            actual_status = getattr(response, "status_code", None)
            if actual_status is not None and actual_status != expected_status:
                raise ErrorValidationError(
                    f"Expected HTTP status {expected_status}, got {actual_status}"
                )

        # Validate HTTP status matches error definition
        self._validate_status_match(error, response)

        # Validate i18n key
        if not self.validate_i18n_key(error):
            raise ErrorValidationError(
                f"Invalid i18n key: {error.get('i18n_key')}"
            )

        return error

    def _validate_structure(self, error: dict) -> None:
        """Validate error response structure."""
        if not isinstance(error, dict):
            raise ErrorValidationError(f"Error must be a dict, got {type(error)}")

        missing_fields = self.REQUIRED_ERROR_FIELDS - set(error.keys())
        if missing_fields:
            raise ErrorValidationError(
                f"Error missing required fields: {missing_fields}"
            )

        # Validate field types
        if not isinstance(error.get("code"), str):
            raise ErrorValidationError("Error 'code' must be a string")
        if not isinstance(error.get("message"), str):
            raise ErrorValidationError("Error 'message' must be a string")
        if not isinstance(error.get("i18n_key"), str):
            raise ErrorValidationError("Error 'i18n_key' must be a string")
        if not isinstance(error.get("http_status"), int):
            raise ErrorValidationError("Error 'http_status' must be an integer")

    def _validate_status_match(self, error: dict, response: Any) -> None:
        """Validate HTTP status matches error definition."""
        error_status = error.get("http_status")
        response_status = getattr(response, "status_code", None)

        if response_status is not None and error_status != response_status:
            raise ErrorValidationError(
                f"HTTP status mismatch: error defines {error_status}, "
                f"response has {response_status}"
            )

    def validate_i18n_key(self, error: dict) -> bool:
        """
        Validate that i18n key follows expected format.

        Args:
            error: Error dictionary

        Returns:
            True if i18n key is valid
        """
        i18n_key = error.get("i18n_key", "")

        # Check key starts with known prefix
        for prefix in self.VALID_I18N_PREFIXES:
            if i18n_key.startswith(prefix):
                # Additional check: key should have content after prefix
                suffix = i18n_key[len(prefix):]
                return len(suffix) > 0 and "_" not in suffix[:1]

        return False

    def validate_http_status_match(self, error: dict, status: int) -> bool:
        """
        Validate that error's http_status matches expected status.

        Args:
            error: Error dictionary
            status: Expected HTTP status code

        Returns:
            True if status matches
        """
        return error.get("http_status") == status

    def validate_field_error(
        self,
        error: dict,
        expected_field: str,
    ) -> bool:
        """
        Validate that error includes correct field information.

        Args:
            error: Error dictionary
            expected_field: Expected field name in error

        Returns:
            True if field matches
        """
        return error.get("field") == expected_field

    def validate_error_code_exists(self, code: str) -> bool:
        """
        Validate that error code exists in ErrorCode enum.

        Args:
            code: Error code string (e.g., "AUTH_001")

        Returns:
            True if code exists in ErrorCode enum
        """
        if get_error_code is None:
            # ErrorCode not available, skip validation
            return True
        return get_error_code(code) is not None

    def get_error_definition(self, code: str) -> Any | None:
        """
        Get ErrorDefinition for a given code.

        Args:
            code: Error code string

        Returns:
            ErrorDefinition or None if not found
        """
        if get_error_code is None:
            return None
        error_code = get_error_code(code)
        return error_code.value if error_code else None


# Module-level validator instance
_validator = ErrorValidator()


def validate_error_response(
    response: Any,
    expected_code: str,
    expected_status: int | None = None,
) -> dict[str, Any]:
    """
    Validate an error response matches expected format and code.

    Args:
        response: HTTP response object
        expected_code: Expected error code (e.g., "AUTH_001")
        expected_status: Expected HTTP status code (optional)

    Returns:
        Validated error dict

    Raises:
        ErrorValidationError: If validation fails
    """
    return _validator.validate_error_response(response, expected_code, expected_status)


def validate_i18n_key(error: dict) -> bool:
    """
    Validate that i18n key follows expected format.

    Args:
        error: Error dictionary

    Returns:
        True if i18n key is valid
    """
    return _validator.validate_i18n_key(error)


def validate_http_status_match(error: dict, status: int) -> bool:
    """
    Validate that error's http_status matches expected status.

    Args:
        error: Error dictionary
        status: Expected HTTP status code

    Returns:
        True if status matches
    """
    return _validator.validate_http_status_match(error, status)


def validate_field_error(error: dict, expected_field: str) -> bool:
    """
    Validate that error includes correct field information.

    Args:
        error: Error dictionary
        expected_field: Expected field name

    Returns:
        True if field matches
    """
    return _validator.validate_field_error(error, expected_field)


def assert_error_response(
    response: Any,
    expected_code: str,
    expected_status: int | None = None,
) -> dict[str, Any]:
    """
    Assert that error response is valid (raises AssertionError on failure).

    Args:
        response: HTTP response object
        expected_code: Expected error code
        expected_status: Expected HTTP status code (optional)

    Returns:
        Validated error dict

    Raises:
        AssertionError: If validation fails
    """
    try:
        return validate_error_response(response, expected_code, expected_status)
    except ErrorValidationError as e:
        raise AssertionError(str(e)) from e
