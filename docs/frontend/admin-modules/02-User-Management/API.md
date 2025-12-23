# User Management API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URLs**: `/api/admin/users`, `/api/admin/wallets`

---

## 📋 Table of Contents

1. [User Operations Endpoints](#user-operations-endpoints)
2. [Wallet Management Endpoints](#wallet-management-endpoints)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Error Handling](#error-handling)
5. [API Design Trade-off Analysis](#api-design-trade-off-analysis)

---

## 🔌 User Operations Endpoints

### 1. List Users

**Method**: `GET`  
**Endpoint**: `/api/admin/users/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Users per page | `20` |
| `offset` | `number` | No | Pagination offset | `0` |
| `sorting_field` | `string` | No | Field to sort by | `email` |
| `sorting_order` | `string` | No | Sort order | `ASC` |

**Valid `sorting_field` Values**: `email`, `created_at`, `is_active`, `is_admin`

**Valid `sorting_order` Values**: `ASC`, `DESC`

**Valid `limit` Range**: 1-100

#### Response

##### Success Response (200 OK)
```typescript
interface ListUsersResponse {
  items: User[];
  total: number;
  limit: number;
  offset: number;
}

interface User {
  id: string;                            // UUID
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;                    // ISO 8601
}
```

**JSON Example**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "is_active": true,
      "is_admin": false,
      "created_at": "2023-10-01T10:00:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `PaginationError` | Invalid pagination params | Show error: "Invalid pagination" |
| `400` | `SortingError` | Invalid sorting params | Show error: "Invalid sorting" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

### 2. Activate User

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/activate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid email format | Show error: "Invalid email" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `403` | `ActivationChangeNotPermittedError` | Cannot activate | Show error: "Cannot activate this user" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

### 3. Deactivate User

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/deactivate`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

##### Error Responses

Same as Activate User endpoint.

---

### 4. Grant Admin Role

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/grant-admin`  
**Auth Required**: Yes (Bearer Token - Super Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not super admin | Show error: "Super admin access required" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

### 5. Revoke Admin Role

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/revoke-admin`  
**Auth Required**: Yes (Bearer Token - Super Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

#### Response

##### Success Response (204 No Content)
No response body

**Note**: Cannot revoke super admin role.

##### Error Responses

Same as Grant Admin Role endpoint.

---

### 6. Change User Password

**Method**: `PATCH`  
**Endpoint**: `/api/admin/users/{email}/password`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | `string` | **Yes** | User email address |

##### Request Body
```typescript
interface ChangePasswordRequest {
  password: string;                      // Required: New password (min 8 chars)
}
```

**JSON Example**:
```json
{
  "password": "newSecurePassword123"
}
```

#### Response

##### Success Response (204 No Content)
No response body

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid password | Show error: "Password must be at least 8 characters" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 💼 Wallet Management Endpoints

### 7. Get Wallet Details

**Method**: `GET`  
**Endpoint**: `/api/admin/wallets/{privy_wallet_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `privy_wallet_id` | `string` | **Yes** | Privy wallet identifier |

#### Response

##### Success Response (200 OK)
```typescript
interface AdminWalletDetailsResponse {
  local_wallet_id: number | null;
  privy_wallet_id: string;
  address: string;
  chain_type: string;
  user_id: number | null;
  owner_type: string | null;
  owner_id: string | null;
  policy_ids: string[];
  additional_signers: AdditionalSignerResponse[];
  provider: string;
  status: string;
  created_at: string;                   // ISO 8601
  updated_at: string;                   // ISO 8601
}

interface AdditionalSignerResponse {
  signer_id: string;
  override_policy_ids: string[] | null;
}
```

**JSON Example**:
```json
{
  "local_wallet_id": 123,
  "privy_wallet_id": "wallet-abc123",
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain_type": "ethereum",
  "user_id": 456,
  "owner_type": "user",
  "owner_id": "did:privy:xxx",
  "policy_ids": ["policy-1", "policy-2"],
  "additional_signers": [
    {
      "signer_id": "signer-1",
      "override_policy_ids": ["policy-3"]
    }
  ],
  "provider": "privy",
  "status": "active",
  "created_at": "2023-10-01T10:00:00Z",
  "updated_at": "2023-10-15T14:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `WalletNotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `502` | `WalletQueryError` | Privy API error | Show error: "Unable to fetch wallet" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

### 8. Update Wallet

**Method**: `PATCH`  
**Endpoint**: `/api/admin/wallets/{privy_wallet_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `privy_wallet_id` | `string` | **Yes** | Privy wallet identifier |

##### Request Body
```typescript
interface UpdateWalletRequest {
  policy_ids?: string[];
  owner?: { [key: string]: any };
  owner_id?: string;
  additional_signers?: AdditionalSignerRequest[];
}

interface AdditionalSignerRequest {
  signer_id: string;
  override_policy_ids?: string[] | null;
}
```

**JSON Example**:
```json
{
  "policy_ids": ["policy-1", "policy-2"],
  "owner": {
    "user_id": "did:privy:xxx"
  },
  "additional_signers": [
    {
      "signer_id": "signer-1",
      "override_policy_ids": ["policy-3"]
    }
  ]
}
```

**Validation Rules**:
- Cannot provide both `owner` and `owner_id` (mutually exclusive)
- `owner` must include either `user_id` or `public_key`

#### Response

##### Success Response (200 OK)
```typescript
interface UpdateWalletResponse {
  success: boolean;
  changes_applied: {
    policy_ids?: string[];
    owner?: { [key: string]: any };
    additional_signers?: AdditionalSignerResponse[];
  };
  privy_wallet_id: string;
  updated_at: string;                    // ISO 8601
}
```

**JSON Example**:
```json
{
  "success": true,
  "changes_applied": {
    "policy_ids": ["policy-1", "policy-2"],
    "additional_signers": [
      {
        "signer_id": "signer-1",
        "override_policy_ids": ["policy-3"]
      }
    ]
  },
  "privy_wallet_id": "wallet-abc123",
  "updated_at": "2023-10-15T14:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValueError` | Invalid request (e.g., both owner and owner_id) | Show error: "Invalid request" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `WalletNotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `422` | `ValueError` | Validation error | Show field-level errors |
| `502` | `WalletUpdateError` | Privy API error | Show error: "Unable to update wallet" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 📝 Request/Response Schemas

### Complete TypeScript Interfaces

See individual endpoint sections above for detailed schemas.

### Common Types

```typescript
// User entity
interface User {
  id: string;                            // UUID
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;                    // ISO 8601
}

// Pagination response
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// Error response format
interface ErrorResponse {
  detail: string;
}
```

---

## ⚠️ Error Handling

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Authorization Errors (403)**
   - Not admin user
   - Not super admin (for grant/revoke admin)
   - **Action**: Show error: "Admin access required" or "Super admin access required"

3. **Validation Errors (400)**
   - Invalid pagination parameters
   - Invalid sorting parameters
   - Invalid email format
   - **Action**: Show inline field errors

4. **Not Found Errors (404)**
   - User not found by email
   - Wallet not found
   - **Action**: Show error: "User not found" or "Wallet not found"

5. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

6. **Bad Gateway (502)**
   - Privy API error (for wallet operations)
   - **Action**: Show error: "Unable to connect to Privy" + Retry

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Error Handling Summary

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `PaginationError` | Invalid pagination | Show error: "Invalid pagination" |
| `400` | `SortingError` | Invalid sorting | Show error: "Invalid sorting" |
| `400` | `DomainFieldError` | Invalid field | Show inline errors |
| `400` | `ValueError` | Invalid request | Show error: "Invalid request" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not authorized | Show error: "Admin access required" |
| `403` | `ActivationChangeNotPermittedError` | Cannot activate | Show error: "Cannot activate this user" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `404` | `WalletNotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `422` | `ValueError` | Validation error | Show field-level errors |
| `502` | `WalletQueryError` | Privy API error | Show error: "Unable to fetch wallet" + Retry |
| `502` | `WalletUpdateError` | Privy API error | Show error: "Unable to update wallet" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 🔐 Authentication

All endpoints require:
- **Bearer Token**: Admin JWT token in `Authorization` header
- **Admin Role**: User must have admin privileges
- **Super Admin Role**: Required for grant/revoke admin operations

**Header Format**:
```http
Authorization: Bearer {jwt_token}
```

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Email as Identifier** | UUID | Human-readable vs. Stability | Email is more user-friendly for admins, but UUIDs are more stable |
| **Pagination vs. Infinite Scroll** | All Results | Performance vs. UX | Pagination handles large user lists better, but requires more clicks |
| **Separate Wallet Endpoints** | Nested under Users | Separation vs. Convenience | Separate endpoints allow wallet management without user context |
| **204 No Content for Updates** | 200 with Response | Simplicity vs. Feedback | 204 is RESTful, but 200 with response provides more feedback |

### Risk Assessment

**Cognitive Limitations:**
- Email-based identification may be confusing if emails change
- Pagination parameters may be complex for some admins
- Wallet updates require understanding of Privy concepts

**Technical Debt:**
- Email lookups may become slow with large user base
- Privy API integration adds external dependency
- Wallet update operations require careful validation

**Validation Strategy:**
- ✅ Monitor user list query performance
- ✅ Track wallet update success rates
- ✅ Alert on Privy API failures
- ✅ Monitor admin operation audit logs

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/admin/user/list_users.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/user/activate_user.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/wallet/get_wallet_details.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/wallet/update_wallet.py`
- **Domain Entities**: `src/app/domain/user/entities/user.py`
- **Frontend Implementation**: `02-User-Management/IMPLEMENTATION.md`
- **UI/UX Design**: `02-User-Management/UI_UX.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
