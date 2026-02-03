# Authentication & User Management - Services Documentation

**Document Version:** 1.0
**Last Updated:** 2026-01-25
**Architecture:** Hexagonal (Clean Architecture)

---

## Table of Contents

1. [Overview](#overview)
2. [Domain Services](#domain-services)
3. [Application Services](#application-services)
4. [Infrastructure Services](#infrastructure-services)
5. [External Integrations](#external-integrations)
6. [Service Dependency Graph](#service-dependency-graph)

---

## Overview

The Authentication & User Management module follows **Hexagonal Architecture** with services organized across four layers:

```
Domain Layer (Business Logic)
    ↓
Application Layer (Use Cases)
    ↓
Infrastructure Layer (Adapters)
    ↓
External Services (Email, Celery, etc.)
```

**Key Principles:**
- **Domain Independence**: Domain services have no external dependencies
- **Port-Adapter Pattern**: Infrastructure implements domain-defined interfaces
- **Dependency Injection**: Dishka framework manages service lifecycles
- **CQRS**: Separate command (write) and query (read) services

---

## Domain Services

Domain services contain **pure business logic** with no framework or infrastructure dependencies.

### 1. UserService

**Core business logic for user management.**

**Location:** `src/app/domain/services/user.py:UserService`

**Responsibilities:**
- User creation with validation
- Password verification
- Password changing
- User activation/deactivation
- Role management
- Login retry tracking

**Dependencies:**
```python
def __init__(
    self,
    user_id_generator: UserIdGenerator,  # Port (interface)
    password_hasher: PasswordHasher,     # Port (interface)
) -> None:
```

**Key Methods:**

#### `create_user()` (Lines 45-99)
```python
def create_user(
    self,
    email: Email,
    first_name: FirstName,
    last_name: LastName,
    password: RawPassword,
    role: UserRole = UserRole.USER,
    phone_number: Optional[PhoneNumber] = None,
    language: Language = Language("en"),
    address: Optional[Address] = None,
    postal_code: Optional[PostalCode] = None,
    country_id: Optional[CountryId] = None,
    city_id: Optional[CityId] = None,
    subscription: Optional[Subscription] = None,
    privy_user_id: Optional[PrivyUserId] = None,
    primary_wallet_address: Optional[WalletAddress] = None,
    auth_provider: Optional[AuthProvider] = None,
) -> User:
```

**Business Rules:**
- Validates role is assignable (`RoleAssignmentNotPermittedError`)
- Generates unique user ID
- Hashes password with pepper and salt
- Sets initial state: `is_active=True`, `is_blocked=False`, `is_verified=False`
- Initializes `retry_count=0`
- Sets `created_at` and `updated_at` to current UTC time

**Returns:** User entity (not yet persisted)

---

#### `is_password_valid()` (Lines 101-105)
```python
def is_password_valid(self, user: User, raw_password: RawPassword) -> bool:
```

**Business Rules:**
- Verifies raw password against stored hash using bcrypt
- Constant-time comparison for security

**Returns:** `True` if password matches, `False` otherwise

---

#### `change_password()` (Lines 107-110)
```python
def change_password(self, user: User, raw_password: RawPassword) -> None:
```

**Business Rules:**
- Hashes new password
- Updates user entity's password field
- Updates `updated_at` timestamp

**Side Effects:** Modifies user entity in-place

---

#### `toggle_user_activation()` (Lines 112-119)
```python
def toggle_user_activation(self, user: User, *, is_active: bool) -> None:
```

**Business Rules:**
- Validates role is changeable (`ActivationChangeNotPermittedError`)
- Updates `is_active` status
- Updates `updated_at` timestamp

**Raises:** `ActivationChangeNotPermittedError` if user role cannot be changed

---

#### `toggle_user_admin_role()` (Lines 121-128)
```python
def toggle_user_admin_role(self, user: User, *, is_admin: bool) -> None:
```

**Business Rules:**
- Validates role is changeable (`RoleChangeNotPermittedError`)
- Promotes to `UserRole.ADMIN` or demotes to `UserRole.USER`
- Updates `updated_at` timestamp

**Raises:** `RoleChangeNotPermittedError` if user role cannot be changed

---

#### `increment_login_retry_count()` (Lines 130-135)
```python
def increment_login_retry_count(self, user: User) -> None:
```

**Business Rules:**
- Increments failed login attempt counter
- Updates `updated_at` timestamp
- Used for rate limiting and security

---

#### `record_successful_login()` (Lines 137-144)
```python
def record_successful_login(self, user: User) -> None:
```

**Business Rules:**
- Resets `retry_count` to 0
- Updates `last_login` to current UTC time
- Updates `updated_at` timestamp

---

### 2. AuthService

**Authentication and authorization business logic.**

**Location:** `src/app/domain/services/auth.py:AuthService`

**Responsibilities:**
- Authorization header validation
- Super admin permission checks
- Admin permission checks
- Role change validation

**Dependencies:**
```python
def __init__(self):
    # Reads from environment: ADMIN_USER_ADMIN or USER_ADMIN
    self._super_admin_email = os.getenv("ADMIN_USER_ADMIN") or os.getenv("USER_ADMIN")
```

**Key Methods:**

#### `validate_authorization_header()` (Lines 29-45)
```python
def validate_authorization_header(self, authorization: Optional[str]) -> str:
```

**Business Rules:**
- Validates header format: `Bearer <token>`
- Extracts and returns token

**Raises:** `InvalidAuthorizationHeaderError` if format invalid

---

#### `check_super_admin_permission()` (Lines 47-58)
```python
def check_super_admin_permission(self, user_email: Email) -> None:
```

**Business Rules:**
- Compares user email against super admin email from config
- Used for privileged operations (role changes, etc.)

**Raises:** `InsufficientPermissionsError` if not super admin

---

#### `check_admin_permission()` (Lines 60-71)
```python
def check_admin_permission(self, user_role: UserRole) -> None:
```

**Business Rules:**
- Validates user has `UserRole.ADMIN` role
- Used for admin-only endpoints

**Raises:** `InsufficientPermissionsError` if not admin

---

#### `validate_role_change()` (Lines 73-86)
```python
def validate_role_change(self, current_role: UserRole, new_role: UserRole) -> None:
```

**Business Rules:**
- Prevents downgrading admin role
- Enforces business rules for role transitions

**Raises:** `RoleChangeNotAllowedError` if change not allowed

---

#### `is_super_admin()` (Lines 88-98)
```python
def is_super_admin(self, email: Email) -> bool:
```

**Returns:** `True` if email matches super admin, `False` otherwise

---

## Application Services

Application services orchestrate domain logic and coordinate with infrastructure.

### 3. SignUpHandler

**User registration handler.**

**Location:** `src/app/infrastructure/auth/handlers/sign_up.py:SignUpHandler`

**Note:** Despite location in `infrastructure/`, this is an application service (legacy naming).

**Responsibilities:**
- User registration workflow
- Email uniqueness validation
- Location validation (country/city)
- Auto-login after registration
- Email verification queue

**Dependencies:**
```python
def __init__(
    self,
    current_user_service: CurrentUserService,
    user_service: UserService,                      # Domain service
    user_command_gateway: UserCommandGateway,       # Port
    flusher: Flusher,                               # Port
    transaction_manager: TransactionManager,        # Port
    auth_session_service: AuthSessionService,       # Infrastructure service
    session_recorder: SessionRecorder,              # Port
    country_query_gateway: CountryQueryGateway,     # Port
    city_query_gateway: CityQueryGateway,           # Port
    email_verification_repo: EmailVerificationRepository,  # Port
):
```

**Key Method:** `execute()` (Lines 93-197)

**Workflow:**
1. **Pre-check:** Reject if already authenticated
2. **Validate Input:** Email, name, password, country, city
3. **Create User:** Via domain service
4. **Persist:** Flush and commit to database
5. **Auto-Login:** Create session and JWT tokens
6. **Record Session:** Save to `sessions` table with IP tracking
7. **Email Verification:** Enqueue Celery task

**Transaction Handling:**
- Uses explicit transaction management
- Rolls back on `EmailAlreadyExistsError`
- Commits after user creation and after session creation

**Celery Integration:** (Lines 179-187)
```python
celery_app.send_task(
    "tasks.email_tasks.send_verification_email",
    kwargs={
        "to_email": user.email.value,
        "verification_url": token,
    },
)
```

---

### 4. LogInHandler

**User authentication handler.**

**Location:** `src/app/infrastructure/auth/handlers/log_in.py:LogInHandler`

**Responsibilities:**
- Email/password authentication
- Password verification
- Retry count tracking
- Session creation
- IP/user-agent tracking

**Dependencies:** Similar to `SignUpHandler`

**Key Method:** `execute()`

**Workflow:**
1. **Pre-check:** Reject if already authenticated
2. **Find User:** By email
3. **Verify Password:** Via domain service
4. **Success Path:**
   - Record successful login (reset retry count, update last_login)
   - Create session and JWT tokens
   - Record session with IP tracking
5. **Failure Path:**
   - Increment retry count
   - Raise `AuthenticationError`

**Security Features:**
- Rate limiting via `retry_count`
- IP address logging
- User-agent tracking

---

### 5. PrivyLogin (Interactor)

**Privy authentication handler.**

**Location:** `src/app/application/commands/auth/privy_login.py:PrivyLogin`

**Responsibilities:**
- Privy user authentication
- Wallet-based login
- Social login (Google, Apple, etc.)
- Auto-registration for new users
- Wallet synchronization
- User context creation for AI agents

**Dependencies:**
```python
def __init__(
    self,
    user_gateway: UserCommandGateway,
    auth_session_service: AuthSessionService,
    transaction_manager: TransactionManager,
    flusher: Flusher,
    session_recorder: SessionRecorder,
    admin_settings: AdminSettings,
    wallet_repository: WalletRepository,
    # Optional for backwards compatibility:
    user_context_service: UserContextService | None = None,
    chat_user_repository: ChatUserRepository | None = None,
):
```

**Key Method:** `execute()` (Lines 107-236)

**Workflow:**
1. **Find User:**
   - Try by `privy_user_id` (full format: `did:privy:...`)
   - Try by `privy_user_id` (legacy format without prefix)
   - Try by email (if provided)
   - Try by generated email for wallet-only users

2. **Update Existing User:**
   - Update `privy_user_id` to new format
   - Update `primary_wallet_address`
   - Update `auth_provider`
   - Update `last_ip`

3. **Create New User:** (Lines 278-342)
   - Generate email if not provided: `{clean_id}@wallet.anvil.io`
   - Default names: "Anvil User"
   - Auto-assign admin role if email in `ALLOWED_ADMIN_EMAILS`
   - Set `is_verified=True` (Privy users pre-verified)
   - Set empty password (no password for Privy users)
   - Track registration IP and last IP

4. **Wallet Sync:** (Lines 411-449)
   - Determine chain type from address format
   - Upsert to `wallets` table
   - Link wallet to user for portfolio tracking

5. **User Context Creation:** (Lines 344-409)
   - Get or create `chat_users` entry (UUID-based)
   - Create `user_context_aware` entry for AI agents
   - Used by authenticated supervisor for personalized responses

6. **Session Creation:**
   - Create auth session
   - Generate JWT tokens
   - Record session with IP tracking
   - Commit transaction

**Auto-Admin Logic:** (Lines 262-276, 299-305)
```python
if self._admin_settings.is_admin_email(email):
    role = UserRole.ADMIN
```

**Transaction Handling:**
- Explicit transaction management
- Rollback on `EmailAlreadyExistsError` or `DataMapperError`
- Multiple commits: after user creation, after wallet sync, after session

---

### 6. RefreshTokenHandler

**Token refresh handler.**

**Location:** `src/app/infrastructure/auth/handlers/refresh_token.py:RefreshTokenHandler`

**Responsibilities:**
- Refresh token validation
- New access token generation
- Session extension
- Token rotation (optional)

**Workflow:**
1. Validate refresh token signature
2. Check session expiration
3. Generate new access token
4. Update session `last_activity`
5. Optionally rotate refresh token

---

### 7. LogOutHandler

**Session termination handler.**

**Location:** `src/app/infrastructure/auth/handlers/log_out.py:LogOutHandler`

**Responsibilities:**
- Session invalidation
- Token blacklisting

**Workflow:**
1. Extract session ID from JWT
2. Delete session from `auth_sessions` table
3. Mark session as inactive in `sessions` table

---

### 8. GetMeHandler / UpdateMeHandler

**User profile management.**

**Location:** `src/app/infrastructure/auth/handlers/account_me.py`

**Responsibilities:**
- Retrieve current user profile
- Update user profile fields

**GetMeHandler Workflow:**
1. Extract user ID from JWT
2. Fetch user from database
3. Return sanitized profile (exclude password)

**UpdateMeHandler Workflow:**
1. Extract user ID from JWT
2. Validate input fields
3. Update user entity
4. Commit transaction
5. Return updated profile

---

### 9. Email Verification Services

**Location:** `src/app/infrastructure/auth/handlers/`

#### SendEmailVerificationHandler
- Generates verification token (32 bytes)
- Stores in `email_verifications` table with 24-hour expiration
- Enqueues Celery task: `tasks.email_tasks.send_verification_email`

#### VerifyEmailHandler
- Validates token (not expired, matches user)
- Sets `is_verified=True`
- Deletes verification token

---

### 10. Password Reset Services

**Location:** `src/app/infrastructure/auth/handlers/password_reset.py`

#### ForgotPasswordHandler
- Validates email exists
- Generates reset token (32 bytes)
- Stores in `password_resets` table with 24-hour expiration
- Enqueues Celery task: `tasks.email_tasks.send_password_reset_email`

#### ResetPasswordHandler
- Validates reset token (not expired, not used)
- Changes password via domain service
- Marks token as used
- Invalidates all sessions for security

---

### 11. Admin User Management Interactors

**Location:** `src/app/application/commands/user/`

#### ActivateUserInteractor
- File: `activate_user.py`
- Validates admin permission
- Calls `UserService.toggle_user_activation(is_active=True)`

#### DeactivateUserInteractor
- File: `deactivate_user.py`
- Validates admin permission
- Calls `UserService.toggle_user_activation(is_active=False)`
- Invalidates all user sessions

#### GrantAdminInteractor
- File: `grant_admin.py`
- Validates admin permission
- Calls `UserService.toggle_user_admin_role(is_admin=True)`

#### RevokeAdminInteractor
- File: `revoke_admin.py`
- Validates admin permission
- Calls `UserService.toggle_user_admin_role(is_admin=False)`

#### ChangePasswordInteractor
- File: `change_password.py`
- Validates admin permission
- Calls `UserService.change_password()`
- Invalidates all user sessions
- Enqueues password change notification email

---

### 12. Auth Command Interactors

**Location:** `src/app/application/commands/auth/`

#### UpgradeToAdminInteractor
- File: `upgrade_to_admin.py`
- Validates super admin permission
- Promotes current user to admin
- Used for self-service admin promotion

#### ChangeRoleInteractor
- File: `change_role.py`
- Validates super admin permission
- Changes target user's role
- Validates role change via `AuthService.validate_role_change()`

---

### 13. Query Services

**Location:** `src/app/application/queries/`

#### ListUsersQueryService
- File: `list_users.py`
- CQRS read model (optimized queries)
- Supports pagination, sorting, search
- Returns lightweight user DTOs

**Key Features:**
- Efficient pagination with offset/limit
- Full-text search on email, first_name, last_name
- Sorting by any field (email, created_at, etc.)
- Admin permission check

---

## Infrastructure Services

Infrastructure services implement domain ports and handle external concerns.

### 14. AuthSessionService

**JWT session management.**

**Location:** `src/app/infrastructure/auth/session/service.py:AuthSessionService`

**Responsibilities:**
- JWT token generation
- Session creation and storage
- Token validation
- Session expiration

**Key Methods:**

#### `create_session()`
```python
async def create_session(self, user_id: UserId) -> tuple[AuthSession, str]:
```

**Returns:** `(AuthSession, access_token)`

**Logic:**
1. Generate session ID (UUID)
2. Calculate expiration (configurable TTL)
3. Create refresh token (optional)
4. Store session in `auth_sessions` table
5. Generate JWT access token with session ID and user ID

---

#### `validate_session()`
```python
async def validate_session(self, access_token: str) -> AuthSession:
```

**Logic:**
1. Decode JWT token
2. Extract session ID
3. Fetch session from database
4. Check expiration
5. Return session if valid

**Raises:** `AuthenticationError` if invalid or expired

---

### 15. PasswordHasher (Adapter)

**Bcrypt password hashing.**

**Location:** `src/app/infrastructure/adapters/password_hasher_bcrypt.py`

**Implements:** `src/app/domain/ports/password_hasher.py:PasswordHasher`

**Key Methods:**

#### `hash()`
```python
def hash(self, raw_password: RawPassword) -> bytes:
```

**Logic:**
- Adds pepper from config
- Uses bcrypt with salt rounds (configurable)
- Returns hashed password bytes

---

#### `verify()`
```python
def verify(self, raw_password: RawPassword, hashed_password: bytes) -> bool:
```

**Logic:**
- Adds pepper to raw password
- Compares with bcrypt (constant-time)
- Returns `True` if match, `False` otherwise

---

### 16. UserCommandGateway (Adapter)

**User write operations repository.**

**Location:** `src/app/infrastructure/adapters/user_data_mapper_sqla.py:SqlaUserDataMapper`

**Implements:** `src/app/application/common/ports/user_command_gateway.py:UserCommandGateway`

**Key Methods:**

#### `add(user: User)`
- Inserts user into database
- Maps domain entity to SQLAlchemy model

#### `update(user: User)`
- Updates user in database
- Uses optimistic locking (updated_at)

#### `read_by_email(email: Email)`
- Fetches user by email
- Returns domain entity

#### `read_by_privy_user_id(privy_user_id: PrivyUserId)`
- Fetches user by Privy user ID
- Supports both full and legacy formats

---

### 17. UserQueryGateway (Adapter)

**User read operations repository (CQRS).**

**Location:** `src/app/infrastructure/adapters/user_query_mapper_sqla.py`

**Implements:** `src/app/application/common/ports/user_query_gateway.py:UserQueryGateway`

**Optimized Read Models:**
- Lightweight DTOs without full entity hydration
- Efficient joins and pagination
- Search and filtering support

---

### 18. SessionRecorder (Adapter)

**Session tracking repository.**

**Location:** `src/app/infrastructure/adapters/session_recorder_sqla.py`

**Implements:** `src/app/application/common/ports/session_recorder.py:SessionRecorder`

**Key Method:** `add()`

**Stores:**
- User ID
- Access token (for lookup)
- Refresh token
- IP address
- User agent
- Created at
- Expires at
- Last activity
- Is active

---

### 19. EmailVerificationRepository (Adapter)

**Email verification token storage.**

**Location:** `src/app/infrastructure/adapters/email_verification_repository_sqla.py`

**Key Methods:**
- `add(user_id, token, expires_at)`
- `get(token)`
- `delete(token)`

---

### 20. CurrentUserService

**Extracts current user from request context.**

**Location:** `src/app/application/common/services/current_user.py:CurrentUserService`

**Responsibilities:**
- Extract JWT from request
- Validate session
- Return current user entity

**Usage:** Used by handlers to get authenticated user

---

## External Integrations

### 21. Email Service (Mailgun)

**Email delivery via Mailgun API.**

**Location:** `src/app/infrastructure/celery/compat_tasks.py`

**Integration Function:** `_send_email_via_mailgun()` (Lines 17-43)

**Configuration:**
```python
settings = load_settings()
mailgun = settings.mailgun
domain = mailgun.domain
api_key = mailgun.api_key
```

**Mailgun API Call:**
```python
requests.post(
    f"https://api.mailgun.net/v3/{domain}/messages",
    auth=("api", api_key),
    data={
        "from": f"noreply@{domain}",
        "to": [to_email],
        "subject": subject,
        "text": body,
    },
    timeout=10,
)
```

**Email Types:**
1. **Verification Email:** Welcome email with verification token
2. **Password Reset:** Email with reset token
3. **Password Change Notification:** Security alert

---

### 22. Celery Integration

**Background task processing.**

**Celery App:** `src/app/infrastructure/celery/app.py:celery_app`

**Email Tasks:** See `celery.md` for detailed documentation

**Task Names:**
- `tasks.email_tasks.send_email`
- `tasks.email_tasks.send_verification_email`
- `tasks.email_tasks.send_password_reset_email`
- `tasks.email_tasks.send_password_change_notification`

**Queue Routing:** (Lines in `app.py`)
```python
"tasks.email_tasks.*": {"queue": "email"},
```

---

### 23. Privy Integration

**Wallet and social authentication.**

**Note:** Privy integration is **client-side** (frontend handles Privy SDK).

**Backend Role:**
1. Accept Privy user data from frontend
2. Validate Privy user ID format
3. Create/update user account
4. Generate backend JWT tokens

**No direct API calls to Privy from backend.**

---

### 24. User Context Service (AI Agents)

**Context-aware agent personalization.**

**Location:** `src/app/application/chat/services/user_context_service.py:UserContextService`

**Responsibilities:**
- Create user context entries for new users
- Update context based on user activity
- Calculate user classifications (portfolio state, activity level, user type)

**Used By:**
- `PrivyLogin` interactor (creates context on first login)
- Celery task: `update_user_context` (background updates)
- Authenticated supervisor (personalized responses)

**Context Fields:**
- Portfolio state: empty, starter, active, whale
- Activity level: new, very_active, active, weekly_active, monthly_active, inactive, reactivated
- User type: new_user, casual, trader, yield_farmer, power_user

**Data Sources:**
- Chat message count
- Wallet balance (USD)
- Execution history (swaps, buys, etc.)
- Last activity timestamp

**File Reference:** `src/app/application/chat/services/user_context_service.py`

---

## Service Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  (FastAPI Controllers: sign_up.py, log_in.py, me.py, etc.) │
└────────────────────────┬────────────────────────────────────┘
                         │ Dishka DI
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  SignUpHandler   │  │  PrivyLogin      │                │
│  │  LogInHandler    │  │  ActivateUser    │                │
│  │  LogOutHandler   │  │  GrantAdmin      │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                            │
│           │ uses                │ uses                       │
│           ↓                     ↓                            │
│  ┌──────────────────────────────────────────┐              │
│  │         Domain Layer                      │              │
│  │  ┌───────────────┐  ┌──────────────────┐ │              │
│  │  │ UserService   │  │  AuthService     │ │              │
│  │  │ - create_user │  │  - check_admin   │ │              │
│  │  │ - is_password │  │  - validate_role │ │              │
│  │  └───────┬───────┘  └──────────────────┘ │              │
│  │          │ uses ports                     │              │
│  └──────────┼────────────────────────────────┘              │
│             ↓                                                │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Domain Ports (Interfaces)           │       │
│  │  - UserIdGenerator                               │       │
│  │  - PasswordHasher                                │       │
│  │  - UserCommandGateway                            │       │
│  │  - UserQueryGateway                              │       │
│  └──────────────────────┬───────────────────────────┘       │
└─────────────────────────┼───────────────────────────────────┘
                          │ implemented by
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │ PasswordHasherBcrypt │  │ SqlaUserDataMapper         │  │
│  │ (implements          │  │ (implements                │  │
│  │  PasswordHasher)     │  │  UserCommandGateway)       │  │
│  └──────────────────────┘  └────────────┬───────────────┘  │
│                                          │                   │
│  ┌──────────────────────┐               │                   │
│  │ AuthSessionService   │               │                   │
│  │ - create_session     │               │                   │
│  │ - validate_session   │               │                   │
│  └──────────────────────┘               ↓                   │
│                                ┌────────────────────────┐   │
│                                │  SQLAlchemy ORM        │   │
│                                │  - users table         │   │
│                                │  - auth_sessions table │   │
│                                └────────┬───────────────┘   │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                                          ↓
                                  ┌───────────────┐
                                  │  PostgreSQL   │
                                  └───────────────┘

External Services:
┌─────────────────┐
│  Mailgun API    │ ← Email tasks
└─────────────────┘

┌─────────────────┐
│  Celery Worker  │ ← Background tasks
└─────────────────┘

┌─────────────────┐
│  Privy (Client) │ ← Frontend integration
└─────────────────┘
```

---

## Service Lifecycle (Dishka Scopes)

**Dishka Configuration:** `src/app/setup/ioc/`

### Scope: REQUEST
- **Lifetime:** Per HTTP request
- **Services:**
  - All handlers/interactors
  - Repositories/gateways
  - Current user service
  - Transaction manager

### Scope: SESSION
- **Lifetime:** Per database session (SQLAlchemy)
- **Services:**
  - SQLAlchemy AsyncSession
  - Flusher
  - Session recorder

### Scope: APP
- **Lifetime:** Application lifetime
- **Services:**
  - Settings
  - Password hasher
  - User ID generator
  - Celery app

---

## Error Handling Strategy

### Domain Exceptions
**Location:** `src/app/domain/exceptions/`

**User Exceptions:**
- `EmailAlreadyExistsError`
- `UserNotFoundByEmailError`
- `ActivationChangeNotPermittedError`
- `RoleChangeNotPermittedError`
- `RoleAssignmentNotPermittedError`

**Auth Exceptions:**
- `InvalidAuthorizationHeaderError`
- `InsufficientPermissionsError`
- `RoleChangeNotAllowedError`

### Infrastructure Exceptions
**Location:** `src/app/infrastructure/exceptions/`

- `AuthenticationError`: Invalid credentials
- `AlreadyAuthenticatedError`: User already logged in
- `DataMapperError`: Database operation failed
- `ReaderError`: Read operation failed

### HTTP Error Mapping
**Library:** `fastapi-error-map`

**Example:** (from `sign_up.py`)
```python
error_map={
    AlreadyAuthenticatedError: status.HTTP_403_FORBIDDEN,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    DataMapperError: rule(
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
        translator=ServiceUnavailableTranslator(),
        on_error=log_error,
    ),
}
```

---

## Testing Strategy

### Unit Tests
- Test domain services in isolation
- Mock all ports (interfaces)
- Focus on business logic

**Example:**
```python
def test_create_user_with_invalid_role():
    # Given
    user_service = UserService(mock_id_gen, mock_hasher)

    # When/Then
    with pytest.raises(RoleAssignmentNotPermittedError):
        user_service.create_user(
            email=Email("test@example.com"),
            password=RawPassword("password"),
            role=UserRole.SYSTEM,  # Not assignable
        )
```

### Integration Tests
- Test handlers with real database
- Use test fixtures for database state
- Test transaction management

**Example:**
```python
async def test_sign_up_handler(test_db_session):
    # Given
    handler = SignUpHandler(...)

    # When
    response = await handler.execute(
        SignUpRequest(email="new@example.com", ...)
    )

    # Then
    assert response.user_id > 0
    assert response.access_token is not None
```

---

**End of Document**
