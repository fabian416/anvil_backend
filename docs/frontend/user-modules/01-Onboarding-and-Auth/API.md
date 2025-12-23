# Authentication & Onboarding API Documentation

> **Complete API and WebSocket Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/account`

---

## 📋 Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Request/Response Schemas](#requestresponse-schemas)
3. [Error Handling](#error-handling)
4. [Authentication Flow](#authentication-flow)
5. [WebSocket Connections](#websocket-connections)

---

## 🔌 API Endpoints

### 1. Privy Login

**Method**: `POST`  
**Endpoint**: `/api/v1/account/privy-login`  
**Auth Required**: No (Public)  
**Content-Type**: `application/json`

#### Request

##### Headers
```http
Content-Type: application/json
```

##### Request Body
```typescript
interface PrivyLoginRequest {
  privy_user_id: string;        // Required: Privy user ID (did:privy:xxxxx)
  email?: string;                // Optional: User email if available
  wallet_address?: string;       // Optional: Primary wallet address (0x...)
  auth_provider?: string;        // Optional: "privy" | "google" | "apple" | "discord" | "wallet" (default: "privy")
  first_name?: string;           // Optional: User first name
  last_name?: string;            // Optional: User last name
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `privy_user_id` | `string` | **Yes** | Privy user ID | Format: `did:privy:xxxxx` |
| `email` | `string` | No | User email | Valid email format |
| `wallet_address` | `string` | No | Primary wallet address | Valid 0x address |
| `auth_provider` | `string` | No | Auth provider | One of: privy, wallet, google, apple, discord |
| `first_name` | `string` | No | User first name | Max 100 chars |
| `last_name` | `string` | No | User last name | Max 100 chars |

**JSON Example**:
```json
{
  "privy_user_id": "did:privy:abc123xyz",
  "email": "user@example.com",
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "auth_provider": "wallet",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface PrivyLoginResponse {
  access_token: string;          // JWT access token
  refresh_token: string;         // JWT refresh token
  token_type: string;            // "bearer"
  user_id: number;               // Internal user ID
  email: string;                // User email
  is_new_user: boolean;          // True if account was just created
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| `access_token` | `string` | JWT access token (expires in 15 minutes) |
| `refresh_token` | `string` | JWT refresh token (expires in 7 days) |
| `token_type` | `string` | Always "bearer" |
| `user_id` | `number` | Internal user ID |
| `email` | `string` | User email |
| `is_new_user` | `boolean` | True if account was just created |

**JSON Example**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 123,
  "email": "user@example.com",
  "is_new_user": false
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid request data | Show inline errors for invalid fields |
| `400` | `ValueError` | Invalid privy_user_id format | Show error: "Invalid Privy user ID" |
| `401` | `AuthenticationError` | Authentication failed | Show error: "Authentication failed" |
| `409` | `EmailAlreadyExistsError` | Email exists with different provider | Show error: "Email already registered with different method" |
| `500` | `Exception` | Internal server error | Show error: "An error occurred. Please try again." |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

**Error Response Format**:
```json
{
  "detail": "Error message description"
}
```

---

### 2. Sign Up

**Method**: `POST`  
**Endpoint**: `/api/v1/account/signup`  
**Auth Required**: No (Public)  
**Content-Type**: `application/json`

#### Request

##### Request Body
```typescript
interface SignUpRequest {
  email: string;                 // Required: User email
  password: string;              // Required: User password (min 8 chars)
  first_name: string;            // Required: User first name
  last_name: string;             // Required: User last name
  country_id?: number;          // Optional: Country ID
  city_id?: number;             // Optional: City ID
  language?: string;            // Optional: Language code (e.g., "en", "es")
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `email` | `string` | **Yes** | User email | Valid email format, unique |
| `password` | `string` | **Yes** | User password | Min 8 characters |
| `first_name` | `string` | **Yes** | User first name | Max 100 chars |
| `last_name` | `string` | **Yes** | User last name | Max 100 chars |
| `country_id` | `number` | No | Country ID | Valid country ID |
| `city_id` | `number` | No | City ID | Valid city ID in country |
| `language` | `string` | No | Language code | ISO 639-1 code (e.g., "en") |

#### Response

##### Success Response (201 Created)
```typescript
interface SignUpResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  email: string;
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid request data | Show inline errors |
| `400` | `CountryNotFoundError` | Invalid country ID | Show error: "Invalid country" |
| `400` | `CityNotFoundInCountryError` | City doesn't belong to country | Show error: "City not found in selected country" |
| `403` | `AlreadyAuthenticatedError` | User already logged in | Redirect to dashboard |
| `403` | `AuthorizationError` | Authorization failed | Show error: "Authorization failed" |
| `409` | `EmailAlreadyExistsError` | Email already registered | Show error: "Email already registered" |
| `422` | `RoleAssignmentNotPermittedError` | Invalid role assignment | Show error: "Invalid role" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

---

### 3. Log In

**Method**: `POST`  
**Endpoint**: `/api/v1/account/login`  
**Auth Required**: No (Public)  
**Content-Type**: `application/json`

#### Request

##### Request Body
```typescript
interface LogInRequest {
  email: string;                 // Required: User email
  password: string;              // Required: User password
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface LogInResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: number;
  email: string;
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `DomainFieldError` | Invalid request data | Show inline errors |
| `401` | `AuthenticationError` | Invalid credentials | Show error: "Invalid email or password" |
| `403` | `AlreadyAuthenticatedError` | User already logged in | Redirect to dashboard |
| `403` | `AuthorizationError` | Authorization failed | Show error: "Authorization failed" |
| `404` | `UserNotFoundByEmailError` | User not found | Show error: "User not found" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

---

### 4. Get Profile

**Method**: `GET`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Response

##### Success Response (200 OK)
```typescript
interface MeResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;                  // "user" | "admin" | "super_admin"
  is_active: boolean;
  is_blocked: boolean;
  is_verified: boolean;
  retry_count: number;
  profile_picture: string | null;
  phone_number: string | null;
  last_login: string | null;     // ISO 8601
  country_id: number | null;
  country_name: string | null;
  country_code: string | null;   // ISO 2-letter code
  city_id: number | null;
  city_name: string | null;
  language: string;             // Language code
  subscription: string | null;  // Subscription tier
}
```

**JSON Example**:
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_active": true,
  "is_blocked": false,
  "is_verified": true,
  "retry_count": 0,
  "profile_picture": "https://example.com/avatar.jpg",
  "phone_number": "+1234567890",
  "last_login": "2024-01-15T10:30:00Z",
  "country_id": 1,
  "country_name": "United States",
  "country_code": "US",
  "city_id": 100,
  "city_name": "New York",
  "language": "en",
  "subscription": "premium"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to load profile" + Retry |

---

### 5. Update Profile

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface UpdateMeRequest {
  first_name?: string;           // Optional: User first name
  last_name?: string;            // Optional: User last name
  phone_number?: string;         // Optional: Phone number
  profile_picture?: string;      // Optional: Profile picture URL
  language?: string;             // Optional: Language code
  address?: string;              // Optional: Street address
  postal_code?: string;          // Optional: Postal code
  country_id?: number;           // Optional: Country ID
  city_id?: number;              // Optional: City ID (must belong to country_id)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `first_name` | `string` | No | User first name | Max 100 chars |
| `last_name` | `string` | No | User last name | Max 100 chars |
| `phone_number` | `string` | No | Phone number | Valid phone format |
| `profile_picture` | `string` | No | Profile picture URL | Valid URL |
| `language` | `string` | No | Language code | ISO 639-1 code |
| `address` | `string` | No | Street address | Max 255 chars |
| `postal_code` | `string` | No | Postal code | Max 20 chars |
| `country_id` | `number` | No | Country ID | Valid country ID |
| `city_id` | `number` | No | City ID | Must belong to country_id |

**Note**: If `country_id` is updated and `city_id` doesn't belong to the new country, `city_id` will be reset to `null`.

#### Response

##### Success Response (200 OK)
Returns `MeResponse` (same as GET /me)

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValueError` | Invalid country/city ID | Show error: "Invalid country or city" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to update profile" + Retry |

---

### 6. Refresh Token

**Method**: `POST`  
**Endpoint**: `/api/v1/account/refresh-token`  
**Auth Required**: No (Public)  
**Content-Type**: `application/json`

#### Request

##### Request Body
```typescript
interface RefreshTokenRequest {
  refresh_token: string;          // Required: JWT refresh token
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface RefreshTokenResponse {
  access_token: string;           // New JWT access token
  refresh_token: string;          // New JWT refresh token (optional, if rotated)
  token_type: string;            // "bearer"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid or expired refresh token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to refresh token" + Retry |

---

### 7. Log Out

**Method**: `DELETE`  
**Endpoint**: `/api/v1/account/logout`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
```

#### Response

##### Success Response (204 No Content)
No response body

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Authorization failed | Show error: "Authorization failed" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to logout" + Retry |

---

### 8. Change Password

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/change-password`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ChangePasswordRequest {
  current_password: string;       // Required: Current password
  new_password: string;          // Required: New password (min 8 chars)
  confirm_password: string;      // Required: Confirm new password
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `current_password` | `string` | **Yes** | Current password | Must match current password |
| `new_password` | `string` | **Yes** | New password | Min 8 characters, must match confirm_password |
| `confirm_password` | `string` | **Yes** | Confirm new password | Must match new_password |

#### Response

##### Success Response (200 OK)
```typescript
interface ChangePasswordResponse {
  message: string;                // "Password changed successfully"
  access_token: string;           // New access token (all sessions invalidated)
  refresh_token: string;          // New refresh token
}
```

**Note**: Changing password invalidates all existing sessions and issues new tokens.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValueError` | Invalid password or mismatch | Show error: "Passwords do not match" or "Invalid current password" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to change password" + Retry |

---

### 9. Verify Email

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/email/verify`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `token` | `string` | **Yes** | Verification token from email |

#### Response

##### Success Response (200 OK)
```typescript
interface EmailVerificationResponse {
  status: string;                 // "success"
  message: string;                // "Email verified"
}
```

**JSON Example**:
```json
{
  "status": "success",
  "message": "Email verified"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValueError` | Invalid verification token | Show error: "Invalid verification token" |
| `403` | `AuthorizationError` | Authorization failed | Show error: "Authorization failed" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to verify email" + Retry |

---

### 10. Send Email Verification

**Method**: `POST`  
**Endpoint**: `/api/v1/account/email/verify/send`  
**Auth Required**: Yes (Bearer Token)

#### Request

No request body or query parameters required

#### Response

##### Success Response (200 OK)
```typescript
interface SendEmailVerificationResponse {
  status: string;                 // "success"
  message: string;                // "Verification email enqueued"
}
```

**JSON Example**:
```json
{
  "status": "success",
  "message": "Verification email enqueued"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `403` | `AuthorizationError` | Authorization failed | Show error: "Authorization failed" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to send verification email" + Retry |

---

### 11. Forgot Password (Request Reset)

**Method**: `POST`  
**Endpoint**: `/api/v1/account/forgot-password`  
**Auth Required**: No (Public)

#### Request

##### Request Body
```typescript
interface ForgotPasswordRequest {
  email: string;                  // Required: User email
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `email` | `string` | **Yes** | User email | Valid email format |

**JSON Example**:
```json
{
  "email": "user@example.com"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ForgotPasswordResponse {
  status: string;                 // "success"
  message: string;                // "Password reset email sent"
}
```

**JSON Example**:
```json
{
  "status": "success",
  "message": "Password reset email sent"
}
```

**Note**: Always returns success (200) even if email doesn't exist (security best practice to prevent email enumeration).

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `404` | `UserNotFoundByEmailError` | User not found | Still show success message (security) |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to send reset email" + Retry |

---

### 12. Reset Password (Confirm Reset)

**Method**: `POST`  
**Endpoint**: `/api/v1/account/reset-password`  
**Auth Required**: No (Public)

#### Request

##### Request Body
```typescript
interface ResetPasswordRequest {
  token: string;                   // Required: Reset token from email
  new_password: string;           // Required: New password (min 8 chars)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `token` | `string` | **Yes** | Reset token from email | Valid token format |
| `new_password` | `string` | **Yes** | New password | Min 8 characters |

**JSON Example**:
```json
{
  "token": "reset_token_abc123",
  "new_password": "newSecurePassword123"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ResetPasswordResponse {
  status: string;                 // "success"
  message: string;                // "Password has been reset"
}
```

**JSON Example**:
```json
{
  "status": "success",
  "message": "Password has been reset"
}
```

**Note**: After successful reset, user should log in with new password.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `AttributeError` | Invalid token or expired | Show error: "Invalid or expired reset token" |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to reset password" + Retry |

---

## 🔄 Authentication Flow

### Standard Flow (Privy)

1. **User authenticates with Privy** (frontend)
   - User connects wallet or uses social login
   - Privy returns user data

2. **Frontend calls `/api/v1/account/privy-login`**
   - Sends Privy user ID and optional metadata
   - Backend creates/updates user account
   - Backend returns JWT tokens

3. **Frontend stores tokens**
   - Store `access_token` in memory (15 min expiry)
   - Store `refresh_token` securely (7 day expiry)

4. **Frontend uses access token for API calls**
   - Include `Authorization: Bearer {access_token}` header
   - Token expires after 15 minutes

5. **When access token expires**
   - Frontend calls `/api/v1/account/refresh-token`
   - Backend returns new access token
   - Continue using new token

6. **When refresh token expires**
   - User must log in again
   - Redirect to login screen

### Token Management Best Practices

- **Access Token**: Store in memory, never in localStorage
- **Refresh Token**: Store securely (httpOnly cookie or secure storage)
- **Token Refresh**: Refresh access token before expiry (e.g., at 14 minutes)
- **Error Handling**: On 401, attempt refresh; if refresh fails, redirect to login

---

## 🔌 WebSocket Connections

### Authentication WebSocket

**Status**: Not applicable for this module

The Authentication module does not use WebSocket connections. All communication is via REST API.

**Note**: Real-time features (notifications, chat) use WebSocket connections documented in their respective modules.

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Attempt token refresh, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Service Unavailable (503)**
   - Database or external service down
   - **Action**: Show error message + Retry button

4. **Conflict Errors (409)**
   - Resource already exists (e.g., email)
   - **Action**: Show specific error message with resolution

### Error Response Format

All errors follow this format:
```json
{
  "detail": "Error message description"
}
```

Some errors may include additional fields:
```json
{
  "detail": "Validation failed",
  "errors": {
    "email": ["Invalid email format"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/account/`
- **Domain Entities**: `src/app/domain/entities/user/`
- **Application Interactors**: `src/app/application/commands/auth/`
- **Frontend Implementation**: `01-Onboarding-and-Auth/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
