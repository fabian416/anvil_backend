# Authentication & User Management - API Endpoints

**Document Version:** 1.0
**Last Updated:** 2026-01-25
**Architecture:** Hexagonal (Clean Architecture)

---

## Table of Contents

1. [Overview](#overview)
2. [Guest Endpoints (Unauthenticated)](#guest-endpoints-unauthenticated)
3. [User Endpoints (Authenticated)](#user-endpoints-authenticated)
4. [Admin Endpoints (Privileged)](#admin-endpoints-privileged)
5. [Endpoint Summary Table](#endpoint-summary-table)

---

## Overview

The Authentication & User Management module follows **Hexagonal Architecture** with strict separation between:

- **Presentation Layer**: HTTP controllers (`src/app/presentation/http/controllers/`)
- **Application Layer**: Commands, queries, interactors (`src/app/application/`)
- **Domain Layer**: Business logic, entities, services (`src/app/domain/`)
- **Infrastructure Layer**: Auth handlers, database adapters (`src/app/infrastructure/`)

**Key Architectural Patterns:**
- **CQRS**: Separate commands (writes) and queries (reads)
- **Port-Adapter**: External dependencies accessed through domain-defined interfaces
- **Dependency Injection**: Dishka framework for IoC container management
- **Error Handling**: `fastapi-error-map` for contextual, per-route error responses

**Base URL:** `/api/v1`

**Authentication:** JWT Bearer tokens with session management
- Access tokens: Short-lived (configurable expiration)
- Refresh tokens: Long-lived, used to obtain new access tokens
- Sessions stored in `auth_sessions` table with FK to `users.id`

---

## Guest Endpoints (Unauthenticated)

These endpoints are publicly accessible and do not require authentication.

### 1. Sign Up

**Create a new user account with email and password.**

- **Endpoint:** `POST /api/v1/account/signup`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/sign_up.py`
- **Handler:** `src/app/infrastructure/auth/handlers/sign_up.py:SignUpHandler`
- **Authentication:** None (public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePassword123!",
  "country_id": 1,          // Optional
  "city_id": 100,           // Optional
  "language": "en"          // Optional, defaults to "en"
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "session_id": "uuid-session-id",
  "user_id": 123,
  "expires_at": "2026-01-26T12:00:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "is_active": true
}
```

**Business Logic:**
- Validates email uniqueness (`EmailAlreadyExistsError` if duplicate)
- Validates country_id and city_id against database
- Hashes password with pepper and salt (bcrypt)
- Auto-login: Creates session and returns tokens
- Enqueues email verification task via Celery
- Tracks registration IP and user agent

**Domain Service:** `src/app/domain/services/user.py:UserService.create_user()`

**Error Responses:**
- `400 Bad Request`: Invalid input (email format, password strength)
- `409 Conflict`: Email already exists
- `503 Service Unavailable`: Database error

---

### 2. Log In

**Authenticate existing user with email and password.**

- **Endpoint:** `POST /api/v1/account/login`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/log_in.py`
- **Handler:** `src/app/infrastructure/auth/handlers/log_in.py:LogInHandler`
- **Authentication:** None (public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 123,
  "expires_at": "2026-01-26T12:00:00Z"
}
```

**Business Logic:**
- Verifies email exists
- Validates password using bcrypt
- Increments `retry_count` on failed attempt
- Resets `retry_count` and updates `last_login` on success
- Creates auth session and JWT tokens
- Records session in `sessions` table with IP tracking

**Domain Service:** `src/app/domain/services/user.py:UserService.is_password_valid()`

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 3. Privy Login

**Authenticate via Privy (wallet, social login, or Privy email).**

- **Endpoint:** `POST /api/v1/account/privy-login`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/privy_login.py`
- **Interactor:** `src/app/application/commands/auth/privy_login.py:PrivyLogin`
- **Authentication:** None (public)

**Request Body:**
```json
{
  "privy_user_id": "did:privy:abc123xyz",
  "email": "user@example.com",              // Optional
  "wallet_address": "0x1234...5678",        // Optional
  "auth_provider": "wallet",                // privy, wallet, google, apple, etc.
  "first_name": "John",                     // Optional
  "last_name": "Doe"                        // Optional
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 123,
  "email": "user@example.com",
  "is_new_user": false
}
```

**Business Logic:**
1. **Find User:**
   - Try by `privy_user_id` (full format: `did:privy:...`)
   - Try by `privy_user_id` (legacy format without prefix)
   - Try by `email` (if provided)
   - Try by generated email (`{clean_id}@wallet.anvil.io` for wallet-only users)

2. **Create User** (if not found):
   - Generate email if not provided
   - Default names: "Anvil User"
   - Auto-assign admin role if email in `ALLOWED_ADMIN_EMAILS`
   - Set `is_verified=True` (Privy users pre-verified)
   - Set empty password (no password for Privy users)

3. **Update Existing User:**
   - Update `privy_user_id` to new format if using legacy
   - Update `primary_wallet_address` if provided
   - Auto-upgrade to admin if email in whitelist

4. **Wallet Sync:**
   - Automatically creates/updates wallet in `wallets` table
   - Determines chain type from address format
   - Links wallet to user for portfolio tracking

5. **User Context:**
   - Creates entry in `user_context_aware` table for AI agents
   - Links to `chat_users` table (UUID-based)
   - Used by authenticated supervisor for personalized responses

**File Reference:** `src/app/application/commands/auth/privy_login.py:107-236`

**Error Responses:**
- `400 Bad Request`: Invalid privy_user_id or wallet_address
- `401 Unauthorized`: Authentication failed
- `409 Conflict`: Email already exists with different auth provider
- `503 Service Unavailable`: Database error

---

### 4. Refresh Token

**Obtain new access token using refresh token.**

- **Endpoint:** `POST /api/v1/account/refresh-token`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/refresh_token.py`
- **Handler:** `src/app/infrastructure/auth/handlers/refresh_token.py:RefreshTokenHandler`
- **Authentication:** None (requires refresh token)

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_at": "2026-01-26T12:00:00Z"
}
```

**Business Logic:**
- Validates refresh token signature
- Checks session expiration
- Generates new access token
- Updates session `last_activity` timestamp
- Optionally rotates refresh token

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `503 Service Unavailable`: Database error

---

### 5. Forgot Password

**Request password reset token via email.**

- **Endpoint:** `POST /api/v1/account/forgot-password`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/password_reset.py`
- **Handler:** `src/app/infrastructure/auth/handlers/password_reset.py:ForgotPasswordHandler`
- **Authentication:** None (public)

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Password reset email sent"
}
```

**Business Logic:**
- Validates email exists
- Generates secure reset token (32 bytes)
- Stores token in `password_resets` table with 24-hour expiration
- Enqueues email task via Celery: `tasks.email_tasks.send_password_reset_email`

**Error Responses:**
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 6. Reset Password

**Reset password using valid reset token.**

- **Endpoint:** `POST /api/v1/account/reset-password`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/password_reset.py`
- **Handler:** `src/app/infrastructure/auth/handlers/password_reset.py:ResetPasswordHandler`
- **Authentication:** None (requires reset token)

**Request Body:**
```json
{
  "token": "secure-reset-token-from-email",
  "new_password": "NewSecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Password has been reset"
}
```

**Business Logic:**
- Validates reset token (not expired, not already used)
- Hashes new password with bcrypt
- Updates user password
- Marks token as used
- Invalidates all existing sessions for security

**Domain Service:** `src/app/domain/services/user.py:UserService.change_password()`

**Error Responses:**
- `400 Bad Request`: Invalid or expired token
- `503 Service Unavailable`: Database error

---

## User Endpoints (Authenticated)

These endpoints require a valid JWT access token in the `Authorization` header.

**Authentication Header:** `Authorization: Bearer <access_token>`

### 7. Get Current User Profile

**Retrieve authenticated user's profile information.**

- **Endpoint:** `GET /api/v1/account/me`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/me.py`
- **Handler:** `src/app/infrastructure/auth/handlers/account_me.py:GetMeHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "USER",
  "is_active": true,
  "is_verified": true,
  "language": "en",
  "created_at": "2026-01-15T10:30:00Z",
  "last_login": "2026-01-25T08:45:00Z",
  "privy_user_id": "did:privy:abc123",
  "primary_wallet_address": "0x1234...5678",
  "auth_provider": "wallet"
}
```

**Business Logic:**
- Extracts user ID from JWT token
- Fetches user from database
- Returns sanitized profile (excludes password hash)

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `503 Service Unavailable`: Database error

---

### 8. Update Current User Profile

**Update authenticated user's profile information.**

- **Endpoint:** `PUT /api/v1/account/me`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/me.py`
- **Handler:** `src/app/infrastructure/auth/handlers/account_me.py:UpdateMeHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "language": "es",
  "phone_number": "+1234567890"
}
```

**Response:** `200 OK`
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "language": "es",
  "phone_number": "+1234567890",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

**Business Logic:**
- Validates input fields
- Updates user entity
- Commits transaction
- Returns updated profile

**Error Responses:**
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid token
- `503 Service Unavailable`: Database error

---

### 9. Log Out

**Invalidate current authentication session.**

- **Endpoint:** `DELETE /api/v1/account/logout`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/log_out.py`
- **Handler:** `src/app/infrastructure/auth/handlers/log_out.py:LogOutHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response:** `204 No Content`

**Business Logic:**
- Extracts session ID from JWT token
- Deletes session from `auth_sessions` table
- Marks session as inactive in `sessions` table
- Token becomes invalid immediately

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `503 Service Unavailable`: Database error

---

### 10. Change Own Password

**Change password for authenticated user.**

- **Endpoint:** `POST /api/v1/account/change-password`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/change_password.py`
- **Handler:** `src/app/infrastructure/auth/handlers/change_password.py:ChangeOwnPasswordHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Password changed successfully"
}
```

**Business Logic:**
- Validates current password
- Validates new password strength
- Hashes new password
- Updates user password
- Enqueues password change notification email
- Invalidates all other sessions for security

**Domain Service:** `src/app/domain/services/user.py:UserService.change_password()`

**Error Responses:**
- `400 Bad Request`: Invalid input or weak password
- `401 Unauthorized`: Current password incorrect
- `503 Service Unavailable`: Database error

---

### 11. Send Email Verification

**Request verification email for authenticated user.**

- **Endpoint:** `POST /api/v1/account/email/verify/send`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/email_verification.py`
- **Handler:** `src/app/infrastructure/auth/handlers/send_email_verification.py:SendEmailVerificationHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Verification email enqueued"
}
```

**Business Logic:**
- Checks if user already verified
- Generates verification token (32 bytes)
- Stores token in `email_verifications` table with 24-hour expiration
- Enqueues email task: `tasks.email_tasks.send_verification_email`

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `503 Service Unavailable`: Database error

---

### 12. Verify Email

**Verify email using token for authenticated user.**

- **Endpoint:** `PUT /api/v1/account/email/verify?token=<token>`
- **Router:** `src/app/presentation/http/controllers/account/router.py`
- **Controller:** `src/app/presentation/http/controllers/account/email_verification.py`
- **Handler:** `src/app/infrastructure/auth/handlers/verify_email.py:VerifyEmailHandler`
- **Authentication:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Query Parameters:**
- `token`: Verification token from email

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Email verified"
}
```

**Business Logic:**
- Validates token (not expired, matches user)
- Sets `is_verified=True` on user entity
- Deletes verification token
- Updates user in database

**Error Responses:**
- `400 Bad Request`: Invalid or expired token
- `401 Unauthorized`: Missing or invalid bearer token
- `503 Service Unavailable`: Database error

---

## Admin Endpoints (Privileged)

These endpoints require authentication AND admin role (`UserRole.ADMIN`).

**Authentication:** Bearer token + Admin role check

### 13. List All Users

**Retrieve paginated list of users with search and sorting.**

- **Endpoint:** `GET /api/v1/admin/users/`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/list_users.py`
- **Query Service:** `src/app/application/queries/list_users.py:ListUsersQueryService`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Query Parameters:**
- `limit`: Max results per page (1-100, default: 20)
- `offset`: Number of records to skip (default: 0)
- `sorting_field`: Field to sort by (default: "email")
- `sorting_order`: "asc" or "desc" (default: "asc")
- `search`: Search term for email/name filtering (optional)

**Example:**
```
GET /api/v1/admin/users/?limit=50&offset=0&sorting_field=created_at&sorting_order=desc&search=john
```

**Response:** `200 OK`
```json
{
  "users": [
    {
      "id": 123,
      "email": "john@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "USER",
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-01-15T10:30:00Z",
      "last_login": "2026-01-25T08:45:00Z"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Business Logic:**
- Validates admin role via `AuthorizationError` check
- Uses CQRS query model (optimized read operation)
- Supports full-text search on email, first_name, last_name
- Efficient pagination with offset/limit

**File Reference:** `src/app/application/queries/list_users.py`

**Error Responses:**
- `400 Bad Request`: Invalid pagination or sorting parameters
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: User is not admin
- `503 Service Unavailable`: Database error

---

### 14. Activate User

**Activate a deactivated user account.**

- **Endpoint:** `PATCH /api/v1/admin/users/{email}/activate`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/activate_user.py`
- **Interactor:** `src/app/application/commands/user/activate_user.py:ActivateUserInteractor`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Path Parameters:**
- `email`: Email of user to activate

**Response:** `204 No Content`

**Business Logic:**
- Validates email exists
- Checks if role is changeable (cannot activate super admin)
- Sets `is_active=True`
- Updates `updated_at` timestamp
- Commits transaction

**Domain Service:** `src/app/domain/services/user.py:UserService.toggle_user_activation()`

**Error Responses:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not admin OR user role not changeable
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 15. Deactivate User

**Deactivate a user account.**

- **Endpoint:** `PATCH /api/v1/admin/users/{email}/deactivate`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/deactivate_user.py`
- **Interactor:** `src/app/application/commands/user/deactivate_user.py:DeactivateUserInteractor`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Path Parameters:**
- `email`: Email of user to deactivate

**Response:** `204 No Content`

**Business Logic:**
- Validates email exists
- Checks if role is changeable (cannot deactivate super admin)
- Sets `is_active=False`
- Invalidates all active sessions
- Updates `updated_at` timestamp

**Domain Service:** `src/app/domain/services/user.py:UserService.toggle_user_activation()`

**Error Responses:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not admin OR user role not changeable
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 16. Grant Admin Role

**Promote user to admin role.**

- **Endpoint:** `PATCH /api/v1/admin/users/{email}/grant-admin`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/grant_admin.py`
- **Interactor:** `src/app/application/commands/user/grant_admin.py:GrantAdminInteractor`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Path Parameters:**
- `email`: Email of user to promote

**Response:** `204 No Content`

**Business Logic:**
- Validates email exists
- Checks if role is changeable
- Sets `role=UserRole.ADMIN`
- Updates `updated_at` timestamp

**Domain Service:** `src/app/domain/services/user.py:UserService.toggle_user_admin_role()`

**Error Responses:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not admin OR user role not changeable
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 17. Revoke Admin Role

**Demote admin user to regular user role.**

- **Endpoint:** `PATCH /api/v1/admin/users/{email}/revoke-admin`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/revoke_admin.py`
- **Interactor:** `src/app/application/commands/user/revoke_admin.py:RevokeAdminInteractor`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Path Parameters:**
- `email`: Email of user to demote

**Response:** `204 No Content`

**Business Logic:**
- Validates email exists
- Checks if role is changeable
- Sets `role=UserRole.USER`
- Updates `updated_at` timestamp

**Domain Service:** `src/app/domain/services/user.py:UserService.toggle_user_admin_role()`

**Error Responses:**
- `400 Bad Request`: Invalid email format
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not admin OR user role not changeable
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 18. Change User Password (Admin)

**Admin can change any user's password.**

- **Endpoint:** `PATCH /api/v1/admin/users/{email}/change-password`
- **Router:** `src/app/presentation/http/controllers/admin/user/router.py`
- **Controller:** `src/app/presentation/http/controllers/admin/user/change_password.py`
- **Interactor:** `src/app/application/commands/user/change_password.py:ChangePasswordInteractor`
- **Authentication:** Required (Bearer token + Admin role)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Path Parameters:**
- `email`: Email of user whose password to change

**Request Body:**
```json
{
  "new_password": "NewSecurePassword789!"
}
```

**Response:** `204 No Content`

**Business Logic:**
- Validates email exists
- Validates new password strength
- Hashes new password
- Updates user password
- Invalidates all user's sessions
- Enqueues password change notification email

**Domain Service:** `src/app/domain/services/user.py:UserService.change_password()`

**Error Responses:**
- `400 Bad Request`: Invalid email or weak password
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not admin
- `404 Not Found`: Email not found
- `503 Service Unavailable`: Database error

---

### 19. Upgrade to Admin (Super Admin Only)

**Super admin can upgrade any user to admin role.**

- **Endpoint:** `POST /api/v1/auth/upgrade-to-admin`
- **Router:** `src/app/presentation/http/controllers/auth/router.py`
- **Controller:** `src/app/presentation/http/controllers/auth/upgrade_to_admin.py`
- **Interactor:** `src/app/application/commands/auth/upgrade_to_admin.py:UpgradeToAdminInteractor`
- **Authentication:** Required (Bearer token + Super Admin email)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Response:** `200 OK`
```json
{
  "id": 456,
  "email": "promoted@example.com",
  "role": "ADMIN",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

**Business Logic:**
- Validates requester is super admin (email in `ALLOWED_ADMIN_EMAILS`)
- Promotes current user to admin
- Updates role and timestamp
- Returns updated user profile

**Domain Service:** `src/app/domain/services/auth.py:AuthService.check_super_admin_permission()`

**Error Responses:**
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not super admin
- `503 Service Unavailable`: Database error

---

### 20. Change User Role (Super Admin Only)

**Super admin can change any user's role.**

- **Endpoint:** `POST /api/v1/auth/change-role`
- **Router:** `src/app/presentation/http/controllers/auth/router.py`
- **Controller:** `src/app/presentation/http/controllers/auth/change_role.py`
- **Interactor:** `src/app/application/commands/auth/change_role.py:ChangeRoleInteractor`
- **Authentication:** Required (Bearer token + Super Admin email)

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "new_role": "ADMIN"
}
```

**Response:** `200 OK`
```json
{
  "id": 789,
  "email": "user@example.com",
  "role": "ADMIN",
  "updated_at": "2026-01-25T12:00:00Z"
}
```

**Business Logic:**
- Validates requester is super admin
- Validates target email exists
- Validates role change is allowed (domain business rules)
- Updates user role
- Returns updated user profile

**Domain Service:** `src/app/domain/services/auth.py:AuthService.validate_role_change()`

**Error Responses:**
- `400 Bad Request`: Invalid role or role change not allowed
- `401 Unauthorized`: Missing or invalid token
- `403 Forbidden`: Not super admin
- `404 Not Found`: Target email not found
- `503 Service Unavailable`: Database error

---

## Endpoint Summary Table

| # | Method | Endpoint | Authentication | Role | Description |
|---|--------|----------|----------------|------|-------------|
| 1 | POST | `/api/v1/account/signup` | None | Public | Create new user account |
| 2 | POST | `/api/v1/account/login` | None | Public | Login with email/password |
| 3 | POST | `/api/v1/account/privy-login` | None | Public | Login via Privy (wallet/social) |
| 4 | POST | `/api/v1/account/refresh-token` | None | Public | Refresh access token |
| 5 | POST | `/api/v1/account/forgot-password` | None | Public | Request password reset |
| 6 | POST | `/api/v1/account/reset-password` | None | Public | Reset password with token |
| 7 | GET | `/api/v1/account/me` | Bearer | User | Get current user profile |
| 8 | PUT | `/api/v1/account/me` | Bearer | User | Update current user profile |
| 9 | DELETE | `/api/v1/account/logout` | Bearer | User | Logout (invalidate session) |
| 10 | POST | `/api/v1/account/change-password` | Bearer | User | Change own password |
| 11 | POST | `/api/v1/account/email/verify/send` | Bearer | User | Send verification email |
| 12 | PUT | `/api/v1/account/email/verify` | Bearer | User | Verify email with token |
| 13 | GET | `/api/v1/admin/users/` | Bearer | Admin | List all users (paginated) |
| 14 | PATCH | `/api/v1/admin/users/{email}/activate` | Bearer | Admin | Activate user account |
| 15 | PATCH | `/api/v1/admin/users/{email}/deactivate` | Bearer | Admin | Deactivate user account |
| 16 | PATCH | `/api/v1/admin/users/{email}/grant-admin` | Bearer | Admin | Grant admin role |
| 17 | PATCH | `/api/v1/admin/users/{email}/revoke-admin` | Bearer | Admin | Revoke admin role |
| 18 | PATCH | `/api/v1/admin/users/{email}/change-password` | Bearer | Admin | Change user password |
| 19 | POST | `/api/v1/auth/upgrade-to-admin` | Bearer | Super Admin | Upgrade self to admin |
| 20 | POST | `/api/v1/auth/change-role` | Bearer | Super Admin | Change any user's role |

**Legend:**
- **Bearer**: Requires JWT access token in `Authorization: Bearer <token>` header
- **User**: Any authenticated user
- **Admin**: Requires `UserRole.ADMIN` role
- **Super Admin**: Email must be in `ALLOWED_ADMIN_EMAILS` config

---

## Architecture Notes

### Request Flow (Hexagonal Pattern)

```
HTTP Request
    ↓
[Presentation Layer] FastAPI Controller
    ↓ (Dishka DI)
[Application Layer] Interactor/Handler
    ↓ (Domain Ports)
[Domain Layer] Domain Service (business logic)
    ↓ (Infrastructure Ports)
[Infrastructure Layer] Repository/Gateway (database)
    ↓
Database (PostgreSQL)
```

### Key Components

**Controllers:** `src/app/presentation/http/controllers/`
- Handle HTTP-specific concerns (request/response)
- Use Pydantic for request/response validation
- Delegate business logic to application layer

**Handlers/Interactors:** `src/app/infrastructure/auth/handlers/`, `src/app/application/commands/`
- Orchestrate use case execution
- Coordinate domain services and repositories
- Handle transaction management

**Domain Services:** `src/app/domain/services/`
- Pure business logic (framework-agnostic)
- No infrastructure dependencies
- Enforce business invariants

**Repositories/Gateways:** `src/app/infrastructure/adapters/`
- Implement domain ports (interfaces)
- Handle database operations via SQLAlchemy
- Isolated from business logic

### Database Schema

**Primary Tables:**
- `users`: User accounts and profiles
- `auth_sessions`: JWT session storage (short-lived)
- `sessions`: Session tracking with IP/user-agent
- `email_verifications`: Email verification tokens
- `password_resets`: Password reset tokens
- `user_events`: Audit log for user actions
- `user_context_aware`: Context for AI agents

**Relationships:**
- `auth_sessions.user_id` → `users.id` (FK)
- `sessions.user_id` → `users.id` (FK)
- `email_verifications.user_id` → `users.id` (FK)
- `password_resets.user_id` → `users.id` (FK)

---

**End of Document**
