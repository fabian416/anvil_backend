# Error Handling System - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅  
**Methodology**: CTO Engineering Framework

---

## Executive Summary

The Anvil Backend error handling system provides a comprehensive, standardized approach to error management across all layers of the application. It follows the CTO methodology with:

- **Problem Decomposition**: Organized by error types (Domain, Application, Infrastructure)
- **Solution Generation**: Unified error response format with i18n support
- **Risk Assessment**: Comprehensive coverage with fallback handlers

**Key Features**:
- ✅ Standardized error codes (100+ codes across 15 categories)
- ✅ i18n support (en, es, pt, zh)
- ✅ Automatic HTTP status code mapping
- ✅ Global and route-level error handling
- ✅ Structured logging and telemetry
- ✅ Developer-friendly error messages

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Architecture                   │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   FastAPI App        │
                    │  (Global Handlers)   │
                    └──────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Domain      │    │ Application   │    │Infrastructure │
│   Layer       │    │   Layer       │    │   Layer       │
├───────────────┤    ├───────────────┤    ├───────────────┤
│DomainError    │    │ApplicationError│   │External API   │
│DomainFieldError│   │(with ErrorCode)│   │Errors         │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌──────────────────────┐
                    │  Error Handlers      │
                    │  (handlers.py)       │
                    └──────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Translators  │    │  Callbacks    │    │  Error Codes  │
│(translators.py)│   │(callbacks.py) │    │(error_codes.py)│
│  (i18n)       │    │  (logging)    │    │  (standard)   │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Standardized        │
                    │  API Response        │
                    └──────────────────────┘
```

---

## Error Code System

### Categories

| Category | Code Range | Description | Examples |
|----------|-----------|------------|----------|
| **AUTH** | 001-099 | Authentication & Authorization | `AUTH_001`: Invalid credentials |
| **USER** | 001-099 | User Management | `USER_001`: User not found |
| **CHAT** | 001-099 | Chat & Conversations | `CHAT_001`: Conversation not found |
| **WALLET** | 001-099 | Wallet Operations | `WALLET_001`: Wallet not found |
| **PORT** | 001-099 | Portfolio Management | `PORT_001`: Portfolio not found |
| **MKT** | 001-099 | Market Data | `MKT_001`: Protocol not found |
| **SRCH** | 001-099 | Search & Discovery | `SRCH_001`: Query empty |
| **ALRT** | 001-099 | Alerts & Notifications | `ALRT_001`: Alert not found |
| **SUB** | 001-099 | Subscriptions & Payments | `SUB_001`: Subscription not found |
| **ADM** | 001-099 | Admin Operations | `ADM_001`: Access denied |
| **LLM** | 001-099 | LLM Operations | `LLM_001`: Provider unavailable |
| **TEL** | 001-099 | Telemetry & Monitoring | `TEL_001`: Access denied |
| **VAL** | 001-099 | Field Validation | `VAL_001`: Field required |
| **SYS** | 001-099 | System Errors | `SYS_001`: Internal error |
| **LOC** | 001-099 | Location Errors | `LOC_001`: Country not found |

### Error Code Structure

Each error code includes:
- **Code**: Unique identifier (e.g., `AUTH_001`)
- **i18n_key**: Translation key (e.g., `errors.auth.invalid_credentials`)
- **default_message**: English message
- **http_status**: HTTP status code (401, 403, 404, etc.)

**Example**:
```python
AUTH_INVALID_CREDENTIALS = ErrorDefinition(
    code="AUTH_001",
    i18n_key="errors.auth.invalid_credentials",
    default_message="Invalid email or password",
    http_status=401,
)
```

---

## Error Response Format

### Standardized Response

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "AUTH_001",
    "message": "Invalid email or password",
    "i18n_key": "errors.auth.invalid_credentials",
    "http_status": 401,
    "details": {
      "attempts_remaining": 2
    },
    "field": "email"
  }
}
```

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | ✅ | Error code (e.g., `AUTH_001`) |
| `message` | string | ✅ | Human-readable message |
| `i18n_key` | string | ✅ | Translation key for frontend |
| `http_status` | integer | ✅ | HTTP status code |
| `details` | object | ❌ | Additional error context |
| `field` | string | ❌ | Field name (for validation errors) |

---

## Error Handling Layers

### 1. Domain Layer

**Purpose**: Business rule violations and domain invariants

**Exception Types**:
- `DomainError`: Complex business rule violations
- `DomainFieldError`: Single-field validation errors

**Example**:
```python
from app.domain.exceptions.user import UserNotFoundByEmailError

raise UserNotFoundByEmailError(email=email)
```

**Handler**: `domain_error_handler` → Maps to appropriate `ErrorCode`

### 2. Application Layer

**Purpose**: Use case errors with standardized error codes

**Exception Type**: `ApplicationError`

**Example**:
```python
from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode

raise ApplicationError(
    error_code=ErrorCode.USER_NOT_FOUND,
    details={"user_id": user_id},
)
```

**Handler**: `application_error_handler` → Direct mapping to API response

### 3. Infrastructure Layer

**Purpose**: External service errors, database errors, etc.

**Exception Types**: Various (e.g., `DataMapperError`, `AuthenticationError`)

**Example** (using `fastapi-error-map`):
```python
from fastapi_error_map import ErrorAwareRouter, rule
from app.presentation.http.errors.translators import ServiceUnavailableTranslator
from app.presentation.http.errors.callbacks import log_error

router = ErrorAwareRouter()

@router.post(
    "/endpoint",
    error_map={
        DataMapperError: rule(
            status=503,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
    },
)
async def endpoint(...):
    ...
```

**Handler**: Route-level handlers via `fastapi-error-map` or global handlers

---

## Usage Patterns

### Pattern 1: ApplicationError (Recommended)

**When**: Application layer errors with known error codes

```python
from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode

class GetUserInteractor:
    async def execute(self, user_id: UUID) -> User:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise ApplicationError(
                error_code=ErrorCode.USER_NOT_FOUND,
                details={"user_id": str(user_id)},
            )
        return user
```

**Response**:
```json
{
  "error": {
    "code": "USER_001",
    "message": "User not found",
    "i18n_key": "errors.user.not_found",
    "http_status": 404,
    "details": {"user_id": "123e4567-e89b-12d3-a456-426614174000"}
  }
}
```

### Pattern 2: DomainError (Legacy)

**When**: Domain layer business rule violations

```python
from app.domain.exceptions.user import UserNotFoundByEmailError

raise UserNotFoundByEmailError(email=email)
```

**Handler**: Automatically mapped to `ErrorCode.USER_NOT_FOUND`

### Pattern 3: Route-Level Error Mapping

**When**: Infrastructure errors in route handlers

```python
from fastapi_error_map import ErrorAwareRouter, rule
from app.presentation.http.errors.translators import ServiceUnavailableTranslator
from app.presentation.http.errors.callbacks import log_error

router = ErrorAwareRouter()

@router.post(
    "/endpoint",
    error_map={
        DataMapperError: rule(
            status=503,
            translator=ServiceUnavailableTranslator(),
            on_error=log_error,
        ),
        ValidationError: rule(
            status=400,
            translator=ValidationErrorTranslator(),
            on_error=log_info,
        ),
    },
)
async def endpoint(...):
    ...
```

### Pattern 4: Pydantic Validation Errors

**When**: Request validation fails (automatic)

```python
from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    email: str
    password: str

# If validation fails, automatically returns:
# {
#   "error": {
#     "code": "VAL_004",
#     "message": "Validation error",
#     "i18n_key": "errors.validation.invalid_format",
#     "http_status": 422,
#     "details": {
#       "errors": [
#         {"field": "email", "message": "field required", "type": "value_error.missing"}
#       ]
#     }
#   }
# }
```

---

## Global Exception Handlers

### Registration

Handlers are automatically registered in `app_factory.py`:

```python
from app.presentation.http.errors.handlers import register_exception_handlers

register_exception_handlers(app)
```

### Handler Order

Handlers are registered in order of specificity:

1. **ApplicationError** → `application_error_handler`
2. **DomainFieldError** → `domain_field_error_handler`
3. **DomainError** → `domain_error_handler`
4. **AuthenticationError** → `authentication_error_handler`
5. **AuthorizationError** → `authorization_error_handler`
6. **RequestValidationError** → `validation_error_handler`
7. **StarletteHTTPException** → `http_exception_handler`
8. **Exception** (catch-all) → `unhandled_exception_handler`

### Handler Behavior

| Handler | Status Code | Logging | i18n |
|---------|------------|---------|------|
| `application_error_handler` | From `ErrorCode` | INFO | ✅ |
| `domain_error_handler` | From mapped `ErrorCode` | WARNING | ✅ |
| `authentication_error_handler` | 401 | INFO | ✅ |
| `authorization_error_handler` | 403 | INFO | ✅ |
| `validation_error_handler` | 422 | INFO | ✅ |
| `http_exception_handler` | From exception | INFO | ✅ |
| `unhandled_exception_handler` | 500 | EXCEPTION | ✅ |

---

## Error Translators

Translators convert exceptions to standardized responses for `fastapi-error-map`:

### Available Translators

| Translator | Status | Use Case |
|------------|--------|----------|
| `BadRequestTranslator` | 400 | Invalid request format |
| `NotFoundTranslator` | 404 | Resource not found |
| `NotFoundErrorTranslator` | 404 | Resource not found (with context) |
| `ServiceUnavailableTranslator` | 503 | External service unavailable |
| `ValidationErrorTranslator` | 400 | Validation errors |
| `StandardizedErrorTranslator` | Variable | Errors with error codes |
| `ConflictTranslator` | 409 | Resource conflicts |
| `UnauthorizedTranslator` | 401 | Authentication required |
| `ForbiddenTranslator` | 403 | Authorization failed |

### Usage

```python
from app.presentation.http.errors.translators import ServiceUnavailableTranslator

@router.post(
    "/endpoint",
    error_map={
        DataMapperError: rule(
            status=503,
            translator=ServiceUnavailableTranslator(),
        ),
    },
)
```

---

## Error Callbacks

Callbacks handle logging for route-level errors:

### Available Callbacks

| Callback | Log Level | Use Case |
|----------|-----------|----------|
| `log_info` | INFO | Expected errors (validation, not found) |
| `log_error` | ERROR | Unexpected errors (external services, database) |

### Usage

```python
from app.presentation.http.errors.callbacks import log_error, log_info

@router.post(
    "/endpoint",
    error_map={
        ValidationError: rule(
            status=400,
            on_error=log_info,  # Expected error
        ),
        DataMapperError: rule(
            status=503,
            on_error=log_error,  # Unexpected error
        ),
    },
)
```

---

## Best Practices

### 1. Use ApplicationError for New Code

**✅ DO**:
```python
raise ApplicationError(
    error_code=ErrorCode.USER_NOT_FOUND,
    details={"user_id": str(user_id)},
)
```

**❌ DON'T**:
```python
raise Exception("User not found")  # No error code, no i18n
```

### 2. Provide Context in Details

**✅ DO**:
```python
raise ApplicationError(
    error_code=ErrorCode.WALLET_INSUFFICIENT_BALANCE,
    details={
        "required": str(amount),
        "available": str(balance),
        "token": token_symbol,
    },
)
```

**❌ DON'T**:
```python
raise ApplicationError(
    error_code=ErrorCode.WALLET_INSUFFICIENT_BALANCE,
)  # No context
```

### 3. Use Appropriate Error Codes

**✅ DO**: Use specific error codes
```python
ErrorCode.AUTH_INVALID_CREDENTIALS  # Specific
```

**❌ DON'T**: Use generic error codes
```python
ErrorCode.SYS_INTERNAL_ERROR  # Too generic
```

### 4. Handle Errors at Appropriate Layer

- **Domain Layer**: Business rule violations → `DomainError`
- **Application Layer**: Use case errors → `ApplicationError`
- **Infrastructure Layer**: External errors → Route-level handlers

### 5. Log Appropriately

- **Expected errors** (validation, not found): `log_info`
- **Unexpected errors** (external services, database): `log_error`
- **Security errors**: Always log with full context

---

## Error Code Reference

### Authentication & Authorization (AUTH_001 - AUTH_014)

| Code | Message | Status |
|------|---------|--------|
| `AUTH_001` | Invalid email or password | 401 |
| `AUTH_002` | Session has expired | 401 |
| `AUTH_003` | Invalid authentication token | 401 |
| `AUTH_004` | Authentication required | 401 |
| `AUTH_005` | Insufficient permissions | 403 |
| `AUTH_006` | Account disabled | 403 |
| `AUTH_007` | Email not verified | 403 |
| `AUTH_008` | Administrator access required | 403 |
| `AUTH_009` | Too many login attempts | 429 |
| `AUTH_010` | Refresh token invalid | 401 |
| `AUTH_011` | Already authenticated | 403 |
| `AUTH_012` | Role change not allowed | 403 |
| `AUTH_013` | Email already verified | 409 |
| `AUTH_014` | Session invalid | 401 |

### User Management (USER_001 - USER_014)

| Code | Message | Status |
|------|---------|--------|
| `USER_001` | User not found | 404 |
| `USER_002` | Email already exists | 409 |
| `USER_003` | Invalid email | 400 |
| `USER_004` | Password too weak | 400 |
| `USER_005` | Passwords do not match | 400 |
| `USER_006` | Invalid current password | 400 |
| `USER_007` | Name required | 400 |
| `USER_008` | Invalid phone | 400 |
| `USER_009` | Profile incomplete | 422 |
| `USER_010` | Verification rate limit | 429 |
| `USER_011` | Activation not permitted | 403 |
| `USER_012` | Role assignment not permitted | 403 |
| `USER_013` | Role change not permitted | 403 |
| `USER_014` | Password same as current | 400 |

### Chat & Conversations (CHAT_001 - CHAT_010)

| Code | Message | Status |
|------|---------|--------|
| `CHAT_001` | Conversation not found | 404 |
| `CHAT_002` | Access denied | 403 |
| `CHAT_003` | Message empty | 400 |
| `CHAT_004` | Message too long | 400 |
| `CHAT_005` | Agent unavailable | 422 |
| `CHAT_006` | Conversation closed | 422 |
| `CHAT_007` | Rate limit | 429 |
| `CHAT_008` | Agent error | 500 |
| `CHAT_009` | Service overloaded | 503 |
| `CHAT_010` | Invalid agent type | 400 |

### Wallet Operations (WALLET_001 - WALLET_010)

| Code | Message | Status |
|------|---------|--------|
| `WALLET_001` | Wallet not found | 404 |
| `WALLET_002` | Wallet not connected | 403 |
| `WALLET_003` | Invalid address | 400 |
| `WALLET_004` | Insufficient balance | 422 |
| `WALLET_005` | Transaction failed | 422 |
| `WALLET_006` | Invalid chain | 400 |
| `WALLET_007` | Invalid amount | 400 |
| `WALLET_008` | Rate limit | 429 |
| `WALLET_009` | Network congested | 503 |
| `WALLET_010` | Invalid signature | 400 |

### System Errors (SYS_001 - SYS_007)

| Code | Message | Status |
|------|---------|--------|
| `SYS_001` | Internal error | 500 |
| `SYS_002` | External service error | 502 |
| `SYS_003` | System maintenance | 503 |
| `SYS_004` | System overloaded | 503 |
| `SYS_005` | Request timeout | 504 |
| `SYS_006` | Database error | 500 |
| `SYS_007` | Cache error | 500 |

*See `src/app/domain/exceptions/error_codes.py` for complete list (100+ codes)*

---

## Testing Error Handling

### Unit Tests

```python
import pytest
from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode

def test_user_not_found_error():
    error = ApplicationError(
        error_code=ErrorCode.USER_NOT_FOUND,
        details={"user_id": "123"},
    )
    
    assert error.code == "USER_001"
    assert error.http_status == 404
    assert error.i18n_key == "errors.user.not_found"
    
    error_dict = error.to_dict()
    assert error_dict["code"] == "USER_001"
    assert error_dict["details"] == {"user_id": "123"}
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_error_response_format(client: TestClient):
    response = client.get("/api/v1/users/nonexistent")
    
    assert response.status_code == 404
    data = response.json()
    
    assert "error" in data
    assert data["error"]["code"] == "USER_001"
    assert data["error"]["i18n_key"] == "errors.user.not_found"
    assert data["error"]["http_status"] == 404
```

---

## Migration Guide

### From Legacy DomainError to ApplicationError

**Before**:
```python
from app.domain.exceptions.user import UserNotFoundByEmailError

raise UserNotFoundByEmailError(email=email)
```

**After**:
```python
from app.domain.exceptions.base import ApplicationError
from app.domain.exceptions.error_codes import ErrorCode

raise ApplicationError(
    error_code=ErrorCode.USER_NOT_FOUND,
    details={"email": email},
)
```

**Benefits**:
- ✅ Explicit error code
- ✅ Consistent response format
- ✅ Better i18n support
- ✅ Easier testing

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `src/app/domain/exceptions/error_codes.py` | All error code definitions |
| `src/app/domain/exceptions/base.py` | Base exception classes |
| `src/app/presentation/http/errors/handlers.py` | Global exception handlers |
| `src/app/presentation/http/errors/translators.py` | Error translators for fastapi-error-map |
| `src/app/presentation/http/errors/callbacks.py` | Logging callbacks |
| `src/app/presentation/http/errors/__init__.py` | Public API exports |
| `src/app/setup/app_factory.py` | Handler registration |

---

## Statistics

| Metric | Value |
|--------|-------|
| **Total Error Codes** | 100+ |
| **Error Categories** | 15 |
| **Global Handlers** | 8 |
| **Translators** | 9 |
| **Callbacks** | 2 |
| **Supported Languages** | 4 (en, es, pt, zh) |

---

**Last Updated**: January 2, 2026
