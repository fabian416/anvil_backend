"""
Test helpers module for comprehensive API testing.

This module provides centralized utilities for:
- Authentication helpers (JWT generation, session management)
- API test client with authentication support
- Database test management
- Error response validation
- LLM response verification

Usage:
    from tests.helpers import AuthHelper, AuthenticatedClient, ErrorValidator
    from tests.helpers.auth_helper import create_test_user, get_auth_headers
    from tests.helpers.api_client import AuthenticatedClient
    from tests.helpers.db_manager import DatabaseTestManager
    from tests.helpers.error_validator import validate_error_response
    from tests.helpers.llm_verifier import verify_llm_response
"""

# Import with graceful fallbacks for missing dependencies
__all__ = []

# Auth helper - always available
try:
    from tests.helpers.auth_helper import (
        AuthHelper,
        create_test_user,
        get_auth_headers,
        create_admin_session,
        invalidate_session,
    )

    __all__.extend([
        "AuthHelper",
        "create_test_user",
        "get_auth_headers",
        "create_admin_session",
        "invalidate_session",
    ])
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import auth_helper: {e}")

# API client - requires httpx
try:
    from tests.helpers.api_client import AuthenticatedClient

    __all__.append("AuthenticatedClient")
except (ImportError, RuntimeError) as e:
    # RuntimeError is raised by starlette if httpx is missing
    AuthenticatedClient = None
    import warnings

    warnings.warn(f"AuthenticatedClient not available (httpx may be missing): {e}")

# Database manager
try:
    from tests.helpers.db_manager import DatabaseTestManager

    __all__.append("DatabaseTestManager")
except ImportError as e:
    DatabaseTestManager = None
    import warnings

    warnings.warn(f"DatabaseTestManager not available: {e}")

# Error validator - always available
try:
    from tests.helpers.error_validator import (
        ErrorValidator,
        validate_error_response,
        validate_i18n_key,
        validate_http_status_match,
    )

    __all__.extend([
        "ErrorValidator",
        "validate_error_response",
        "validate_i18n_key",
        "validate_http_status_match",
    ])
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import error_validator: {e}")

# LLM verifier
try:
    from tests.helpers.llm_verifier import (
        LLMVerifier,
        verify_response_structure,
        verify_content_relevance,
        verify_risk_disclaimers,
        verify_defi_data_format,
    )

    __all__.extend([
        "LLMVerifier",
        "verify_response_structure",
        "verify_content_relevance",
        "verify_risk_disclaimers",
        "verify_defi_data_format",
    ])
except ImportError as e:
    import warnings

    warnings.warn(f"Could not import llm_verifier: {e}")
