# Error Codes Reference - Enterprise i18n Support

**Version:** 1.0  
**Last Updated:** December 6, 2025  
**Status:** Implementation Required

---

## Overview

This document defines all error codes used across the Anvil DeFi platform API. Each error code is designed for:
- **Consistency** across all endpoints
- **i18n Support** with translation keys
- **Frontend Handling** with structured error objects
- **User-Friendly Messages** in multiple languages

---

## Error Response Structure

All API errors follow this standard structure:

```typescript
interface APIError {
  error: {
    code: string;           // Unique error code (e.g., "AUTH_001")
    message: string;        // Default English message
    i18n_key: string;       // Translation key for frontend
    details?: Record<string, any>;  // Additional context
    field?: string;         // Field that caused the error (for validation)
    http_status: number;    // HTTP status code
  };
}

// Example:
{
  "error": {
    "code": "AUTH_001",
    "message": "Invalid email or password",
    "i18n_key": "errors.auth.invalid_credentials",
    "details": {},
    "http_status": 401
  }
}
```

---

## HTTP Status Code Mapping

| Status | Category | Description |
|--------|----------|-------------|
| 400 | Bad Request | Validation errors, malformed requests |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists |
| 422 | Unprocessable | Business rule violation |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Error | Server-side error |
| 502 | Bad Gateway | External service failure |
| 503 | Service Unavailable | Temporary unavailability |

---

## Error Code Categories

### AUTH - Authentication & Authorization (AUTH_001 - AUTH_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| AUTH_001 | 401 | errors.auth.invalid_credentials | Invalid email or password |
| AUTH_002 | 401 | errors.auth.token_expired | Session has expired, please login again |
| AUTH_003 | 401 | errors.auth.token_invalid | Invalid authentication token |
| AUTH_004 | 401 | errors.auth.token_missing | Authentication required |
| AUTH_005 | 403 | errors.auth.insufficient_permissions | You don't have permission to perform this action |
| AUTH_006 | 403 | errors.auth.account_disabled | Your account has been disabled |
| AUTH_007 | 403 | errors.auth.account_not_verified | Please verify your email address |
| AUTH_008 | 403 | errors.auth.admin_required | Administrator access required |
| AUTH_009 | 429 | errors.auth.too_many_attempts | Too many login attempts, please try again later |
| AUTH_010 | 401 | errors.auth.refresh_token_invalid | Session refresh failed, please login again |

---

### USER - User Management (USER_001 - USER_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| USER_001 | 404 | errors.user.not_found | User not found |
| USER_002 | 409 | errors.user.email_exists | An account with this email already exists |
| USER_003 | 400 | errors.user.invalid_email | Please enter a valid email address |
| USER_004 | 400 | errors.user.password_too_weak | Password must be at least 8 characters with uppercase, lowercase, and number |
| USER_005 | 400 | errors.user.password_mismatch | Passwords do not match |
| USER_006 | 400 | errors.user.invalid_current_password | Current password is incorrect |
| USER_007 | 400 | errors.user.name_required | First name and last name are required |
| USER_008 | 400 | errors.user.invalid_phone | Please enter a valid phone number |
| USER_009 | 422 | errors.user.profile_incomplete | Please complete your profile |
| USER_010 | 429 | errors.user.verification_rate_limit | Please wait before requesting another verification email |

---

### CHAT - Chat & Conversations (CHAT_001 - CHAT_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| CHAT_001 | 404 | errors.chat.conversation_not_found | Conversation not found |
| CHAT_002 | 403 | errors.chat.conversation_access_denied | You don't have access to this conversation |
| CHAT_003 | 400 | errors.chat.message_empty | Message cannot be empty |
| CHAT_004 | 400 | errors.chat.message_too_long | Message exceeds maximum length |
| CHAT_005 | 422 | errors.chat.agent_unavailable | The requested agent is currently unavailable |
| CHAT_006 | 422 | errors.chat.conversation_closed | This conversation has been closed |
| CHAT_007 | 429 | errors.chat.rate_limit | You're sending messages too quickly |
| CHAT_008 | 500 | errors.chat.agent_error | Agent encountered an error processing your request |
| CHAT_009 | 503 | errors.chat.service_overloaded | Chat service is experiencing high load |
| CHAT_010 | 400 | errors.chat.invalid_agent_type | Invalid agent type specified |

---

### WALLET - Wallet Operations (WALLET_001 - WALLET_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| WALLET_001 | 404 | errors.wallet.not_found | Wallet not found |
| WALLET_002 | 403 | errors.wallet.not_connected | Please connect your wallet |
| WALLET_003 | 400 | errors.wallet.invalid_address | Invalid wallet address |
| WALLET_004 | 422 | errors.wallet.insufficient_balance | Insufficient balance |
| WALLET_005 | 422 | errors.wallet.transaction_failed | Transaction failed |
| WALLET_006 | 400 | errors.wallet.invalid_chain | Unsupported blockchain network |
| WALLET_007 | 400 | errors.wallet.invalid_amount | Invalid amount specified |
| WALLET_008 | 429 | errors.wallet.rate_limit | Too many wallet operations |
| WALLET_009 | 503 | errors.wallet.network_congested | Network is congested, please try again |
| WALLET_010 | 400 | errors.wallet.signature_invalid | Invalid signature |

---

### PORTFOLIO - Portfolio Management (PORT_001 - PORT_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| PORT_001 | 404 | errors.portfolio.not_found | Portfolio not found |
| PORT_002 | 403 | errors.portfolio.access_denied | You don't have access to this portfolio |
| PORT_003 | 400 | errors.portfolio.invalid_allocation | Allocation percentages must sum to 100% |
| PORT_004 | 422 | errors.portfolio.risk_limit_exceeded | This allocation exceeds your risk tolerance |
| PORT_005 | 400 | errors.portfolio.invalid_timeframe | Invalid time frame specified |
| PORT_006 | 422 | errors.portfolio.rebalance_failed | Portfolio rebalancing failed |
| PORT_007 | 400 | errors.portfolio.invalid_position | Invalid position specified |

---

### MARKET - Market Data (MKT_001 - MKT_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| MKT_001 | 404 | errors.market.protocol_not_found | Protocol not found |
| MKT_002 | 404 | errors.market.token_not_found | Token not found |
| MKT_003 | 503 | errors.market.data_unavailable | Market data temporarily unavailable |
| MKT_004 | 400 | errors.market.invalid_symbol | Invalid token symbol |
| MKT_005 | 400 | errors.market.invalid_chain | Unsupported blockchain |
| MKT_006 | 429 | errors.market.rate_limit | Market data rate limit exceeded |

---

### SEARCH - Search & Discovery (SRCH_001 - SRCH_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| SRCH_001 | 400 | errors.search.query_empty | Search query cannot be empty |
| SRCH_002 | 400 | errors.search.query_too_short | Search query must be at least 2 characters |
| SRCH_003 | 400 | errors.search.query_too_long | Search query exceeds maximum length |
| SRCH_004 | 400 | errors.search.invalid_filters | Invalid search filters |
| SRCH_005 | 503 | errors.search.service_unavailable | Search service temporarily unavailable |
| SRCH_006 | 404 | errors.search.no_results | No results found |

---

### ALERT - Alerts & Notifications (ALRT_001 - ALRT_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| ALRT_001 | 404 | errors.alert.not_found | Alert not found |
| ALRT_002 | 409 | errors.alert.already_exists | Alert already exists for this condition |
| ALRT_003 | 400 | errors.alert.invalid_threshold | Invalid threshold value |
| ALRT_004 | 400 | errors.alert.invalid_condition | Invalid alert condition |
| ALRT_005 | 422 | errors.alert.limit_exceeded | Maximum alert limit reached |

---

### SUBSCRIPTION - Subscriptions & Payments (SUB_001 - SUB_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| SUB_001 | 404 | errors.subscription.not_found | Subscription not found |
| SUB_002 | 409 | errors.subscription.already_active | You already have an active subscription |
| SUB_003 | 422 | errors.subscription.payment_failed | Payment processing failed |
| SUB_004 | 400 | errors.subscription.invalid_plan | Invalid subscription plan |
| SUB_005 | 422 | errors.subscription.cancel_failed | Unable to cancel subscription |
| SUB_006 | 403 | errors.subscription.feature_unavailable | This feature requires a premium subscription |
| SUB_007 | 400 | errors.subscription.invalid_card | Invalid payment card |

---

### ADMIN - Admin Operations (ADM_001 - ADM_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| ADM_001 | 403 | errors.admin.access_denied | Administrator access required |
| ADM_002 | 404 | errors.admin.resource_not_found | Resource not found |
| ADM_003 | 409 | errors.admin.resource_conflict | Resource already exists |
| ADM_004 | 422 | errors.admin.operation_failed | Admin operation failed |
| ADM_005 | 400 | errors.admin.invalid_config | Invalid configuration |
| ADM_006 | 503 | errors.admin.service_unavailable | Admin service temporarily unavailable |

---

### LLM - LLM Operations (LLM_001 - LLM_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| LLM_001 | 503 | errors.llm.provider_unavailable | AI service temporarily unavailable |
| LLM_002 | 429 | errors.llm.rate_limit | AI request rate limit exceeded |
| LLM_003 | 422 | errors.llm.budget_exceeded | AI budget limit reached |
| LLM_004 | 500 | errors.llm.generation_failed | AI response generation failed |
| LLM_005 | 400 | errors.llm.invalid_prompt | Invalid prompt |
| LLM_006 | 503 | errors.llm.all_providers_failed | All AI providers are currently unavailable |

---

### TELEMETRY - Telemetry & Monitoring (TEL_001 - TEL_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| TEL_001 | 403 | errors.telemetry.access_denied | Telemetry access requires admin privileges |
| TEL_002 | 400 | errors.telemetry.invalid_timerange | Invalid time range specified |
| TEL_003 | 503 | errors.telemetry.service_unavailable | Telemetry service unavailable |
| TEL_004 | 400 | errors.telemetry.invalid_metric | Invalid metric name |

---

### VALIDATION - Field Validation (VAL_001 - VAL_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| VAL_001 | 400 | errors.validation.required | This field is required |
| VAL_002 | 400 | errors.validation.min_length | Must be at least {min} characters |
| VAL_003 | 400 | errors.validation.max_length | Must be no more than {max} characters |
| VAL_004 | 400 | errors.validation.invalid_format | Invalid format |
| VAL_005 | 400 | errors.validation.invalid_email | Invalid email format |
| VAL_006 | 400 | errors.validation.invalid_uuid | Invalid ID format |
| VAL_007 | 400 | errors.validation.invalid_date | Invalid date format |
| VAL_008 | 400 | errors.validation.out_of_range | Value must be between {min} and {max} |
| VAL_009 | 400 | errors.validation.invalid_enum | Invalid option selected |
| VAL_010 | 400 | errors.validation.array_too_long | Too many items (maximum {max}) |

---

### SYSTEM - System Errors (SYS_001 - SYS_099)

| Code | HTTP | i18n Key | Default Message |
|------|------|----------|-----------------|
| SYS_001 | 500 | errors.system.internal | An unexpected error occurred |
| SYS_002 | 502 | errors.system.external_service | External service error |
| SYS_003 | 503 | errors.system.maintenance | System is under maintenance |
| SYS_004 | 503 | errors.system.overloaded | System is currently overloaded |
| SYS_005 | 504 | errors.system.timeout | Request timed out |
| SYS_006 | 500 | errors.system.database | Database error |
| SYS_007 | 500 | errors.system.cache | Cache error |

---

## Frontend Implementation

### TypeScript Error Handler

```typescript
// src/lib/errors/types.ts
export interface APIErrorResponse {
  error: {
    code: string;
    message: string;
    i18n_key: string;
    details?: Record<string, any>;
    field?: string;
    http_status: number;
  };
}

export interface ErrorContext {
  code: string;
  message: string;
  i18nKey: string;
  httpStatus: number;
  field?: string;
  details?: Record<string, any>;
}

// src/lib/errors/errorHandler.ts
import { useTranslation } from 'react-i18next';

export const useErrorHandler = () => {
  const { t, i18n } = useTranslation();

  const getLocalizedMessage = (error: APIErrorResponse['error']): string => {
    // Try to get localized message
    const translatedMessage = t(error.i18n_key, {
      defaultValue: error.message,
      ...error.details,
    });
    return translatedMessage;
  };

  const handleError = (error: APIErrorResponse['error']): ErrorContext => {
    return {
      code: error.code,
      message: getLocalizedMessage(error),
      i18nKey: error.i18n_key,
      httpStatus: error.http_status,
      field: error.field,
      details: error.details,
    };
  };

  return { handleError, getLocalizedMessage };
};
```

### i18n Translation Files

```json
// locales/en/errors.json
{
  "errors": {
    "auth": {
      "invalid_credentials": "Invalid email or password",
      "token_expired": "Session has expired, please login again",
      "token_invalid": "Invalid authentication token",
      "token_missing": "Authentication required",
      "insufficient_permissions": "You don't have permission to perform this action",
      "account_disabled": "Your account has been disabled",
      "account_not_verified": "Please verify your email address",
      "admin_required": "Administrator access required",
      "too_many_attempts": "Too many login attempts, please try again later",
      "refresh_token_invalid": "Session refresh failed, please login again"
    },
    "user": {
      "not_found": "User not found",
      "email_exists": "An account with this email already exists",
      "invalid_email": "Please enter a valid email address",
      "password_too_weak": "Password must be at least 8 characters with uppercase, lowercase, and number",
      "password_mismatch": "Passwords do not match",
      "invalid_current_password": "Current password is incorrect",
      "name_required": "First name and last name are required"
    },
    "chat": {
      "conversation_not_found": "Conversation not found",
      "conversation_access_denied": "You don't have access to this conversation",
      "message_empty": "Message cannot be empty",
      "message_too_long": "Message exceeds maximum length",
      "agent_unavailable": "The requested agent is currently unavailable",
      "agent_error": "Agent encountered an error processing your request"
    },
    "validation": {
      "required": "This field is required",
      "min_length": "Must be at least {{min}} characters",
      "max_length": "Must be no more than {{max}} characters",
      "invalid_format": "Invalid format",
      "invalid_email": "Invalid email format"
    },
    "system": {
      "internal": "An unexpected error occurred",
      "maintenance": "System is under maintenance",
      "timeout": "Request timed out"
    }
  }
}
```

```json
// locales/es/errors.json
{
  "errors": {
    "auth": {
      "invalid_credentials": "Correo electrónico o contraseña inválidos",
      "token_expired": "La sesión ha expirado, por favor inicie sesión nuevamente",
      "token_invalid": "Token de autenticación inválido",
      "token_missing": "Autenticación requerida",
      "insufficient_permissions": "No tienes permiso para realizar esta acción",
      "account_disabled": "Tu cuenta ha sido deshabilitada",
      "account_not_verified": "Por favor verifica tu dirección de correo electrónico",
      "admin_required": "Se requiere acceso de administrador",
      "too_many_attempts": "Demasiados intentos de inicio de sesión, intenta más tarde",
      "refresh_token_invalid": "Error al refrescar sesión, inicia sesión nuevamente"
    },
    "user": {
      "not_found": "Usuario no encontrado",
      "email_exists": "Ya existe una cuenta con este correo electrónico",
      "invalid_email": "Por favor ingresa un correo electrónico válido",
      "password_too_weak": "La contraseña debe tener al menos 8 caracteres con mayúsculas, minúsculas y números",
      "password_mismatch": "Las contraseñas no coinciden",
      "invalid_current_password": "La contraseña actual es incorrecta",
      "name_required": "El nombre y apellido son requeridos"
    },
    "chat": {
      "conversation_not_found": "Conversación no encontrada",
      "conversation_access_denied": "No tienes acceso a esta conversación",
      "message_empty": "El mensaje no puede estar vacío",
      "message_too_long": "El mensaje excede la longitud máxima",
      "agent_unavailable": "El agente solicitado no está disponible actualmente",
      "agent_error": "El agente encontró un error al procesar tu solicitud"
    },
    "validation": {
      "required": "Este campo es requerido",
      "min_length": "Debe tener al menos {{min}} caracteres",
      "max_length": "No debe tener más de {{max}} caracteres",
      "invalid_format": "Formato inválido",
      "invalid_email": "Formato de correo electrónico inválido"
    },
    "system": {
      "internal": "Ocurrió un error inesperado",
      "maintenance": "El sistema está en mantenimiento",
      "timeout": "La solicitud expiró"
    }
  }
}
```

---

## Backend Implementation Status

### ⚠️ IMPLEMENTATION REQUIRED

The following backend changes are needed to fully implement this error system:

1. **Create Error Codes Module**
   - Location: `src/app/domain/exceptions/error_codes.py`
   - Define all error codes as an enum
   - Map to i18n keys

2. **Update Exception Classes**
   - Ensure all exceptions include error code
   - Include i18n_key in response

3. **Update Error Handlers**
   - Location: `src/app/presentation/http/error_handlers.py`
   - Return standardized error response format

4. **Create Error Response Transformer**
   - Ensure consistent error format across all endpoints

### Implementation Priority

| Priority | Category | Endpoints |
|----------|----------|-----------|
| P0 | AUTH | All authentication endpoints |
| P0 | USER | User management endpoints |
| P1 | CHAT | Chat & agent endpoints |
| P1 | WALLET | Wallet operations |
| P2 | MARKET | Market data endpoints |
| P2 | SEARCH | Search endpoints |
| P3 | ADMIN | Admin endpoints |
| P3 | TELEMETRY | Telemetry endpoints |

---

## Next Steps

1. ✅ Error codes document created
2. ⏳ Implement backend error codes enum
3. ⏳ Update exception handlers
4. ⏳ Add i18n keys to responses
5. ⏳ Create frontend error handler utilities
6. ⏳ Add translation files for all supported languages

---

**Document Status:** Reference Complete  
**Implementation Status:** Required  
**Supported Languages:** en, es (more to be added)
