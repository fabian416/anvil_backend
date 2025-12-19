# Error Handling Implementation Plan

**Version:** 1.0  
**Last Updated:** December 6, 2025  
**Status:** Implementation Required

---

## Overview

This document outlines the implementation plan for standardizing error codes and i18n support across all 262 API endpoints.

---

## Current State Analysis

### Existing Error Handling

The codebase currently uses:
- `fastapi-error-map` for contextual error handling
- Custom exception classes in `src/app/domain/exceptions/`
- HTTP exception handlers in presentation layer

### Gaps Identified

1. **No standardized error codes** - Errors use free-form messages
2. **No i18n keys** - Messages are hardcoded in English
3. **Inconsistent response format** - Different endpoints return different error structures
4. **No error code registry** - No central place to track all error codes

---

## Implementation Plan

### Phase 1: Error Code Infrastructure (Priority: P0)

**Estimated Time:** 2-3 days

#### 1.1 Create Error Code Registry

```python
# src/app/domain/exceptions/error_codes.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional


@dataclass
class ErrorDefinition:
    """Definition of an error code."""
    code: str
    i18n_key: str
    default_message: str
    http_status: int


class ErrorCode(Enum):
    """All error codes in the system."""
    
    # Authentication (AUTH_001 - AUTH_099)
    AUTH_INVALID_CREDENTIALS = ErrorDefinition(
        code="AUTH_001",
        i18n_key="errors.auth.invalid_credentials",
        default_message="Invalid email or password",
        http_status=401,
    )
    AUTH_TOKEN_EXPIRED = ErrorDefinition(
        code="AUTH_002",
        i18n_key="errors.auth.token_expired",
        default_message="Session has expired, please login again",
        http_status=401,
    )
    AUTH_TOKEN_INVALID = ErrorDefinition(
        code="AUTH_003",
        i18n_key="errors.auth.token_invalid",
        default_message="Invalid authentication token",
        http_status=401,
    )
    AUTH_TOKEN_MISSING = ErrorDefinition(
        code="AUTH_004",
        i18n_key="errors.auth.token_missing",
        default_message="Authentication required",
        http_status=401,
    )
    AUTH_INSUFFICIENT_PERMISSIONS = ErrorDefinition(
        code="AUTH_005",
        i18n_key="errors.auth.insufficient_permissions",
        default_message="You don't have permission to perform this action",
        http_status=403,
    )
    AUTH_ACCOUNT_DISABLED = ErrorDefinition(
        code="AUTH_006",
        i18n_key="errors.auth.account_disabled",
        default_message="Your account has been disabled",
        http_status=403,
    )
    AUTH_ACCOUNT_NOT_VERIFIED = ErrorDefinition(
        code="AUTH_007",
        i18n_key="errors.auth.account_not_verified",
        default_message="Please verify your email address",
        http_status=403,
    )
    AUTH_ADMIN_REQUIRED = ErrorDefinition(
        code="AUTH_008",
        i18n_key="errors.auth.admin_required",
        default_message="Administrator access required",
        http_status=403,
    )
    AUTH_TOO_MANY_ATTEMPTS = ErrorDefinition(
        code="AUTH_009",
        i18n_key="errors.auth.too_many_attempts",
        default_message="Too many login attempts, please try again later",
        http_status=429,
    )
    AUTH_REFRESH_TOKEN_INVALID = ErrorDefinition(
        code="AUTH_010",
        i18n_key="errors.auth.refresh_token_invalid",
        default_message="Session refresh failed, please login again",
        http_status=401,
    )
    
    # User (USER_001 - USER_099)
    USER_NOT_FOUND = ErrorDefinition(
        code="USER_001",
        i18n_key="errors.user.not_found",
        default_message="User not found",
        http_status=404,
    )
    USER_EMAIL_EXISTS = ErrorDefinition(
        code="USER_002",
        i18n_key="errors.user.email_exists",
        default_message="An account with this email already exists",
        http_status=409,
    )
    USER_INVALID_EMAIL = ErrorDefinition(
        code="USER_003",
        i18n_key="errors.user.invalid_email",
        default_message="Please enter a valid email address",
        http_status=400,
    )
    USER_PASSWORD_TOO_WEAK = ErrorDefinition(
        code="USER_004",
        i18n_key="errors.user.password_too_weak",
        default_message="Password must be at least 8 characters with uppercase, lowercase, and number",
        http_status=400,
    )
    
    # Chat (CHAT_001 - CHAT_099)
    CHAT_CONVERSATION_NOT_FOUND = ErrorDefinition(
        code="CHAT_001",
        i18n_key="errors.chat.conversation_not_found",
        default_message="Conversation not found",
        http_status=404,
    )
    CHAT_ACCESS_DENIED = ErrorDefinition(
        code="CHAT_002",
        i18n_key="errors.chat.conversation_access_denied",
        default_message="You don't have access to this conversation",
        http_status=403,
    )
    CHAT_MESSAGE_EMPTY = ErrorDefinition(
        code="CHAT_003",
        i18n_key="errors.chat.message_empty",
        default_message="Message cannot be empty",
        http_status=400,
    )
    CHAT_AGENT_UNAVAILABLE = ErrorDefinition(
        code="CHAT_005",
        i18n_key="errors.chat.agent_unavailable",
        default_message="The requested agent is currently unavailable",
        http_status=422,
    )
    
    # ... Add all other error codes from ERROR_CODES_REFERENCE.md
    
    # System (SYS_001 - SYS_099)
    SYS_INTERNAL_ERROR = ErrorDefinition(
        code="SYS_001",
        i18n_key="errors.system.internal",
        default_message="An unexpected error occurred",
        http_status=500,
    )
    SYS_EXTERNAL_SERVICE = ErrorDefinition(
        code="SYS_002",
        i18n_key="errors.system.external_service",
        default_message="External service error",
        http_status=502,
    )
    SYS_MAINTENANCE = ErrorDefinition(
        code="SYS_003",
        i18n_key="errors.system.maintenance",
        default_message="System is under maintenance",
        http_status=503,
    )
```

#### 1.2 Create Base Application Exception

```python
# src/app/domain/exceptions/base.py

from typing import Any, Dict, Optional
from app.domain.exceptions.error_codes import ErrorCode, ErrorDefinition


class ApplicationError(Exception):
    """Base exception for all application errors."""
    
    def __init__(
        self,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        override_message: Optional[str] = None,
    ):
        self.error_code = error_code
        self.definition: ErrorDefinition = error_code.value
        self.details = details or {}
        self.field = field
        self.message = override_message or self.definition.default_message
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response format."""
        result = {
            "code": self.definition.code,
            "message": self.message,
            "i18n_key": self.definition.i18n_key,
            "http_status": self.definition.http_status,
        }
        if self.details:
            result["details"] = self.details
        if self.field:
            result["field"] = self.field
        return result


# Specific exception classes
class AuthenticationError(ApplicationError):
    """Authentication-related errors."""
    pass


class AuthorizationError(ApplicationError):
    """Authorization/permission errors."""
    pass


class NotFoundError(ApplicationError):
    """Resource not found errors."""
    pass


class ValidationError(ApplicationError):
    """Validation errors."""
    pass


class ConflictError(ApplicationError):
    """Resource conflict errors."""
    pass


class BusinessRuleError(ApplicationError):
    """Business rule violation errors."""
    pass


class ExternalServiceError(ApplicationError):
    """External service errors."""
    pass
```

#### 1.3 Create Global Exception Handler

```python
# src/app/presentation/http/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.exceptions.base import ApplicationError


async def application_error_handler(
    request: Request,
    exc: ApplicationError,
) -> JSONResponse:
    """Handle all ApplicationError exceptions."""
    return JSONResponse(
        status_code=exc.definition.http_status,
        content={"error": exc.to_dict()},
    )


def register_exception_handlers(app):
    """Register all exception handlers."""
    app.add_exception_handler(ApplicationError, application_error_handler)
    
    # Handle unexpected errors
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "SYS_001",
                    "message": "An unexpected error occurred",
                    "i18n_key": "errors.system.internal",
                    "http_status": 500,
                }
            },
        )
```

---

### Phase 2: Update Existing Exceptions (Priority: P0)

**Estimated Time:** 3-4 days

#### 2.1 Update Auth Exceptions

```python
# src/app/domain/exceptions/auth.py

from app.domain.exceptions.base import AuthenticationError, AuthorizationError
from app.domain.exceptions.error_codes import ErrorCode


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__(ErrorCode.AUTH_INVALID_CREDENTIALS)


class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__(ErrorCode.AUTH_TOKEN_EXPIRED)


class TokenInvalidError(AuthenticationError):
    def __init__(self):
        super().__init__(ErrorCode.AUTH_TOKEN_INVALID)


class InsufficientPermissionsError(AuthorizationError):
    def __init__(self, required_role: str = None):
        super().__init__(
            ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
            details={"required_role": required_role} if required_role else None,
        )


class AccountDisabledError(AuthorizationError):
    def __init__(self):
        super().__init__(ErrorCode.AUTH_ACCOUNT_DISABLED)
```

#### 2.2 Update Chat Exceptions

```python
# src/app/domain/exceptions/chat.py

from app.domain.exceptions.base import NotFoundError, ValidationError, BusinessRuleError
from app.domain.exceptions.error_codes import ErrorCode


class ConversationNotFoundError(NotFoundError):
    def __init__(self, conversation_id: str):
        super().__init__(
            ErrorCode.CHAT_CONVERSATION_NOT_FOUND,
            details={"conversation_id": conversation_id},
        )


class ConversationAccessDeniedError(NotFoundError):
    def __init__(self, conversation_id: str):
        super().__init__(
            ErrorCode.CHAT_ACCESS_DENIED,
            details={"conversation_id": conversation_id},
        )


class MessageEmptyError(ValidationError):
    def __init__(self):
        super().__init__(
            ErrorCode.CHAT_MESSAGE_EMPTY,
            field="message",
        )


class AgentUnavailableError(BusinessRuleError):
    def __init__(self, agent_type: str):
        super().__init__(
            ErrorCode.CHAT_AGENT_UNAVAILABLE,
            details={"agent_type": agent_type},
        )
```

---

### Phase 3: Endpoint Updates (Priority: P1)

**Estimated Time:** 5-7 days

#### 3.1 Update Controllers to Use New Exceptions

```python
# Example: src/app/presentation/http/controllers/chat/router.py

from app.domain.exceptions.chat import (
    ConversationNotFoundError,
    ConversationAccessDeniedError,
    MessageEmptyError,
)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user: CurrentUser,
    interactor: SendMessage,
):
    # Validation
    if not request.content.strip():
        raise MessageEmptyError()
    
    # Check conversation exists
    conversation = await interactor.get_conversation(conversation_id)
    if not conversation:
        raise ConversationNotFoundError(str(conversation_id))
    
    # Check access
    if conversation.user_id != current_user.id:
        raise ConversationAccessDeniedError(str(conversation_id))
    
    # Process message
    result = await interactor.execute(conversation_id, request.content)
    return result
```

#### 3.2 Endpoint Migration Priority

| Priority | Module | Endpoints | Estimated Time |
|----------|--------|-----------|----------------|
| P0 | Auth/Account | 12 | 1 day |
| P0 | Chat | 11 | 1 day |
| P1 | Wallet | 4 | 0.5 day |
| P1 | Portfolio | 4 | 0.5 day |
| P1 | Markets | 4 | 0.5 day |
| P1 | Search | 6 | 0.5 day |
| P1 | Alerts | 7 | 0.5 day |
| P2 | Graph | 12 | 1 day |
| P2 | ML | 8 | 0.5 day |
| P2 | Hunter | 6 | 0.5 day |
| P2 | ULTRA | 8 | 0.5 day |
| P3 | Admin Users | 6 | 0.5 day |
| P3 | Admin LLM | 36 | 1.5 day |
| P3 | Admin Telemetry | 32 | 1 day |
| P3 | Admin Other | 45 | 1.5 day |

---

### Phase 4: Testing (Priority: P1)

**Estimated Time:** 2-3 days

#### 4.1 Unit Tests for Error Codes

```python
# tests/unit/domain/exceptions/test_error_codes.py

import pytest
from app.domain.exceptions.error_codes import ErrorCode
from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.auth import InvalidCredentialsError


def test_error_code_format():
    """All error codes should follow naming convention."""
    for code in ErrorCode:
        assert code.value.code.startswith(("AUTH_", "USER_", "CHAT_", "SYS_"))
        assert code.value.i18n_key.startswith("errors.")
        assert 100 <= code.value.http_status < 600


def test_invalid_credentials_error():
    """Test InvalidCredentialsError."""
    error = InvalidCredentialsError()
    result = error.to_dict()
    
    assert result["code"] == "AUTH_001"
    assert result["i18n_key"] == "errors.auth.invalid_credentials"
    assert result["http_status"] == 401


def test_error_with_details():
    """Test error with additional details."""
    from app.domain.exceptions.chat import ConversationNotFoundError
    
    error = ConversationNotFoundError("test-uuid")
    result = error.to_dict()
    
    assert result["code"] == "CHAT_001"
    assert result["details"]["conversation_id"] == "test-uuid"
```

#### 4.2 Integration Tests

```python
# tests/integration/test_error_responses.py

import pytest
from fastapi.testclient import TestClient


def test_authentication_error_response(client: TestClient):
    """Test auth error returns correct format."""
    response = client.post(
        "/api/v1/account/login",
        json={"email": "wrong@email.com", "password": "wrong"},
    )
    
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "AUTH_001"
    assert error["i18n_key"] == "errors.auth.invalid_credentials"


def test_not_found_error_response(client: TestClient, auth_headers):
    """Test 404 error returns correct format."""
    response = client.get(
        "/api/v1/user/chat/conversations/nonexistent-id",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "CHAT_001"
    assert "conversation_id" in error.get("details", {})
```

---

### Phase 5: Documentation Updates (Priority: P2)

**Estimated Time:** 1-2 days

1. Update all endpoint documentation with error codes
2. Generate error code reference from code
3. Create frontend integration examples
4. Update OpenAPI schema with error responses

---

## Implementation Checklist

### Phase 1: Infrastructure
- [ ] Create `error_codes.py` with all error definitions
- [ ] Create `base.py` with base exception classes
- [ ] Create `exception_handlers.py` with global handlers
- [ ] Register handlers in `app.py`
- [ ] Add unit tests for error code module

### Phase 2: Exception Updates
- [ ] Update auth exceptions
- [ ] Update user exceptions
- [ ] Update chat exceptions
- [ ] Update wallet exceptions
- [ ] Update portfolio exceptions
- [ ] Update market exceptions
- [ ] Update search exceptions
- [ ] Update alert exceptions
- [ ] Update subscription exceptions
- [ ] Update admin exceptions
- [ ] Update telemetry exceptions
- [ ] Update system exceptions

### Phase 3: Endpoint Updates
- [ ] Update auth endpoints
- [ ] Update account endpoints
- [ ] Update chat endpoints
- [ ] Update wallet endpoints
- [ ] Update portfolio endpoints
- [ ] Update market endpoints
- [ ] Update search endpoints
- [ ] Update alert endpoints
- [ ] Update graph endpoints
- [ ] Update ML endpoints
- [ ] Update hunter endpoints
- [ ] Update ultra endpoints
- [ ] Update admin user endpoints
- [ ] Update admin LLM endpoints
- [ ] Update admin telemetry endpoints
- [ ] Update admin other endpoints

### Phase 4: Testing
- [ ] Unit tests for all error codes
- [ ] Integration tests for error responses
- [ ] E2E tests for error flows

### Phase 5: Documentation
- [ ] Update endpoint docs with error codes
- [ ] Generate error code reference
- [ ] Create frontend integration guide
- [ ] Update OpenAPI schema

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Infrastructure | 2-3 days | 📋 Planned |
| Phase 2: Exception Updates | 3-4 days | 📋 Planned |
| Phase 3: Endpoint Updates | 5-7 days | 📋 Planned |
| Phase 4: Testing | 2-3 days | 📋 Planned |
| Phase 5: Documentation | 1-2 days | 📋 Planned |
| **Total** | **13-19 days** | |

---

## Resources Required

- 1 Backend Developer (full-time)
- 1 QA Engineer (part-time, Phase 4)
- 1 Technical Writer (part-time, Phase 5)

---

**Document Status:** Implementation Plan  
**Next Steps:** Begin Phase 1 implementation
