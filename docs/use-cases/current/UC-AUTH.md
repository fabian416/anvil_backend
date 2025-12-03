# UC-AUTH: Authentication & User Management

**Version:** 1.0.0  
**Status:** ✅ LIVE (Production)  
**Category:** Core Platform  
**Total Use Cases:** 8

---

## 📊 **OVERVIEW**

Complete authentication and user management system providing secure user registration, login, session management, and role-based access control.

### **Business Value**
- Secure user authentication
- Role-based authorization
- Admin user management
- Session management
- Email verification
- Password reset flow

### **Technical Stack**
- **Authentication:** JWT tokens with Bearer authentication
- **Session Storage:** Database-backed sessions (`AuthSessionRepository`)
- **Password Hashing:** bcrypt
- **Email Verification:** Token-based verification
- **Authorization:** Role-based access control (RBAC)

---

## 🎯 **USE CASES**

### **UC-AUTH-1: User Registration**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** CRITICAL
- **API Endpoint:** `POST /api/v1/account/signup`

**Business Value:**
```
User Story: As a new user, I want to register an account 
           so that I can access the platform.

Value Proposition: Enable user acquisition and onboarding

Success Metrics:
  • Registration success rate > 95%
  • Email verification rate > 70%
  • Time to first login < 5 minutes
```

**Technical Specification:**
```python
# Domain Layer
- Entity: User (UserId, Email, FirstName, LastName, UserPasswordHash)
- Value Objects: Email, UserPasswordHash, UserActive, UserVerified

# Application Layer
- Handler: SignUpHandler
- Port: UserCommandGateway

# Infrastructure Layer
- Adapter: UserRepositorySqla
- Password Hashing: bcrypt

# Presentation Layer
- Controller: POST /api/v1/account/signup
- Request: SignUpRequest (email, password, first_name, last_name)
- Response: SignUpResponse (user_id, email)
```

**Configuration:**
```toml
# config/local/config.toml
[auth]
min_password_length = 8
require_email_verification = true
bcrypt_rounds = 12
```

**Security:**
- ✅ Password strength validation
- ✅ Email format validation
- ✅ bcrypt password hashing
- ✅ Unique email constraint
- ✅ SQL injection prevention (parameterized queries)

**Testing:**
```python
# tests/unit/application/test_signup_handler.py
- test_successful_registration()
- test_duplicate_email_error()
- test_invalid_email_format()
- test_weak_password_rejection()
- test_password_hashing()
```

---

### **UC-AUTH-2: User Login**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** CRITICAL
- **API Endpoint:** `POST /api/v1/account/login`

**Business Value:**
```
User Story: As a registered user, I want to log in 
           so that I can access my account.

Value Proposition: Secure access to user accounts

Success Metrics:
  • Login success rate > 98%
  • Average login time < 1 second
  • Failed login rate < 2%
```

**Technical Specification:**
```python
# Domain Layer
- Entity: User
- Value Objects: Email, UserPasswordHash

# Application Layer
- Handler: LogInHandler
- Service: AuthSessionService
- Port: UserQueryGateway

# Infrastructure Layer
- Adapter: UserRepositorySqla
- Password Verification: bcrypt.checkpw()
- JWT Generation: PyJWT

# Presentation Layer
- Controller: POST /api/v1/account/login
- Request: LogInRequest (email, password)
- Response: LogInResponse (access_token, refresh_token, expires_in)
```

**JWT Token Structure:**
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "roles": ["user"],
  "exp": 1701520800,
  "iat": 1701516000
}
```

**Configuration:**
```toml
[auth.jwt]
secret_key = "${JWT_SECRET_KEY}"
algorithm = "HS256"
access_token_expire_minutes = 60
refresh_token_expire_days = 30
```

**Security:**
- ✅ Constant-time password comparison (bcrypt)
- ✅ JWT token signing
- ✅ Token expiration
- ✅ Secure HTTP-only cookies (optional)
- ✅ Rate limiting on login attempts

**Testing:**
```python
# tests/integration/auth/test_login.py
- test_successful_login()
- test_invalid_credentials()
- test_jwt_token_generation()
- test_session_creation()
- test_rate_limiting()
```

---

### **UC-AUTH-3: JWT Authentication**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** CRITICAL
- **Implementation:** Bearer token authentication

**Business Value:**
```
User Story: As a logged-in user, I want to access protected resources 
           so that I can use premium features.

Value Proposition: Stateless, scalable authentication

Success Metrics:
  • Token validation time < 50ms
  • Token refresh success rate > 99%
  • Session expiration handling > 95%
```

**Technical Specification:**
```python
# Presentation Layer
- Security: bearer_scheme (Security dependency)
- Dependency: from app.presentation.http.auth.fastapi_openapi_markers import bearer_scheme

# Usage in Controllers:
@router.get("/protected")
async def protected_endpoint(
    authorization: Annotated[str, Security(bearer_scheme)],
):
    """Requires Bearer token in Authorization header"""
    pass
```

**Authorization Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Validation Flow:**
```
1. Extract token from Authorization header
2. Verify JWT signature (HS256)
3. Check token expiration
4. Extract user_id and roles
5. Load user from database
6. Check user active status
7. Return authenticated user context
```

**Security:**
- ✅ JWT signature verification
- ✅ Token expiration checks
- ✅ Secure secret key storage
- ✅ Token revocation via session management
- ✅ Protection against replay attacks

---

### **UC-AUTH-4: Password Reset**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** HIGH
- **API Endpoints:**
  - `POST /api/v1/account/password-reset/request`
  - `POST /api/v1/account/password-reset/confirm`

**Business Value:**
```
User Story: As a user who forgot my password, I want to reset it 
           so that I can regain access to my account.

Value Proposition: Self-service account recovery

Success Metrics:
  • Password reset completion rate > 60%
  • Reset token expiration < 1 hour
  • Email delivery rate > 99%
```

**Technical Specification:**
```python
# Domain Layer
- Entity: PasswordResetToken
- Value Objects: Email, ExpiresAt

# Application Layer
- Handler: RequestPasswordResetHandler
- Handler: ConfirmPasswordResetHandler
- Port: PasswordResetRepository

# Infrastructure Layer
- Adapter: PasswordResetRepositorySqla
- Email Service: Mailgun integration
- Token Generation: secrets.token_urlsafe()

# Presentation Layer
- Controller: POST /api/v1/account/password-reset/request
- Controller: POST /api/v1/account/password-reset/confirm
```

**Reset Token Structure:**
```python
{
    "user_id": UUID,
    "token": "secure_random_token",
    "expires_at": datetime (1 hour from creation),
    "used": False
}
```

**Configuration:**
```toml
[auth.password_reset]
token_expire_minutes = 60
max_reset_attempts = 3
cleanup_expired_tokens = true
```

**Security:**
- ✅ Cryptographically secure token generation
- ✅ Token expiration (1 hour)
- ✅ Single-use tokens
- ✅ Email verification before reset
- ✅ Rate limiting on reset requests

**Testing:**
```python
# tests/integration/auth/test_password_reset.py
- test_request_password_reset()
- test_confirm_password_reset()
- test_expired_token_rejection()
- test_invalid_token_rejection()
- test_single_use_token()
```

---

### **UC-AUTH-5: Email Verification**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** MEDIUM
- **API Endpoints:**
  - `PUT /api/v1/account/email-verification`
  - `POST /api/v1/account/email-verification/send`

**Business Value:**
```
User Story: As a new user, I want to verify my email 
           so that I can access full platform features.

Value Proposition: Reduce spam accounts, ensure valid emails

Success Metrics:
  • Verification rate > 70%
  • Average verification time < 10 minutes
  • Bounce rate < 5%
```

**Technical Specification:**
```python
# Domain Layer
- Value Object: UserVerified (boolean)
- Entity: EmailVerificationToken

# Application Layer
- Handler: VerifyEmailHandler
- Handler: SendVerificationEmailHandler

# Infrastructure Layer
- Email Service: Mailgun
- Token Storage: Database
```

**Configuration:**
```toml
[auth.email_verification]
token_expire_hours = 24
require_verification_for_login = false
resend_cooldown_minutes = 5
```

---

### **UC-AUTH-6: User Profile Management**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** MEDIUM
- **API Endpoints:**
  - `GET /api/v1/account/me`
  - `PUT /api/v1/account/me`
  - `PUT /api/v1/account/password`

**Business Value:**
```
User Story: As a user, I want to view and update my profile 
           so that I can keep my information current.

Value Proposition: User account management

Success Metrics:
  • Profile update success rate > 98%
  • Average update time < 2 seconds
```

**Technical Specification:**
```python
# Application Layer
- Handler: GetMeHandler
- Handler: UpdateMeHandler
- Handler: ChangePasswordHandler

# Presentation Layer
- Controller: GET /api/v1/account/me
- Request: UpdateMeRequest (first_name, last_name)
- Response: UserResponse (id, email, first_name, last_name, roles)
```

---

### **UC-AUTH-7: Role-Based Access Control**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Free
- **Priority:** HIGH
- **Roles:** User, Admin, Super Admin

**Business Value:**
```
User Story: As a platform, I want to control access to features 
           so that users only access appropriate resources.

Value Proposition: Secure feature gating

Success Metrics:
  • Authorization check time < 10ms
  • Unauthorized access rate < 0.01%
```

**Technical Specification:**
```python
# Application Layer
- Service: AuthorizationService
- Method: has_role(user_id: UUID, role: str) -> bool

# Domain Layer
- Value Object: UserRole (Enum: USER, ADMIN, SUPER_ADMIN)

# Usage:
if not await self._auth_service.has_role(user_id, "admin"):
    raise InsufficientPermissionsError("Admin access required")
```

**Role Hierarchy:**
```
SUPER_ADMIN (highest)
  ├─ All ADMIN permissions
  ├─ Cannot be revoked
  └─ Grant/revoke admin roles

ADMIN
  ├─ All USER permissions
  ├─ Access admin endpoints
  ├─ Manage users
  └─ View metrics

USER (default)
  ├─ Access public endpoints
  ├─ Access own profile
  └─ Basic features
```

---

### **UC-AUTH-8: Admin User Management**

**Overview:**
- **Status:** ✅ LIVE
- **Tier:** Admin
- **Priority:** MEDIUM
- **API Endpoints:**
  - `GET /api/v1/admin/users`
  - `PATCH /api/v1/admin/users/{email}/grant-admin`
  - `PATCH /api/v1/admin/users/{email}/revoke-admin`
  - `PATCH /api/v1/admin/users/{email}/activate`
  - `PATCH /api/v1/admin/users/{email}/deactivate`
  - `PATCH /api/v1/admin/users/{email}/password`

**Business Value:**
```
User Story: As an admin, I want to manage user accounts 
           so that I can moderate the platform.

Value Proposition: Platform moderation and user management

Success Metrics:
  • Admin action success rate > 99%
  • Average action time < 1 second
```

**Technical Specification:**
```python
# Application Layer
- Handler: ListUsersHandler
- Handler: GrantAdminHandler
- Handler: RevokeAdminHandler
- Handler: ActivateUserHandler
- Handler: DeactivateUserHandler
- Handler: ChangeUserPasswordHandler

# Authorization:
- Requires admin role for all endpoints
- Requires super admin for grant/revoke admin
```

---

## 🏗️ **ARCHITECTURE**

### **Hexagonal Architecture Placement**

```
Domain Layer (src/app/domain/):
  ├─ entities/
  │  └─ user.py (User entity)
  ├─ value_objects/
  │  ├─ user_id.py
  │  ├─ email.py
  │  ├─ user_password_hash.py
  │  └─ user_role.py
  └─ exceptions/
     └─ auth.py

Application Layer (src/app/application/):
  ├─ commands/
  │  ├─ signup.py (SignUpHandler)
  │  ├─ login.py (LogInHandler)
  │  └─ user/ (User management handlers)
  └─ services/
     └─ authorization.py (AuthorizationService)

Infrastructure Layer (src/app/infrastructure/):
  ├─ adapters/
  │  └─ user_repository_sqla.py
  ├─ auth/
  │  ├─ handlers/ (Login, signup handlers)
  │  ├─ jwt.py (JWT utilities)
  │  └─ session.py (Session management)
  └─ persistence_sqla/
     └─ mappings/user.py

Presentation Layer (src/app/presentation/http/):
  ├─ controllers/
  │  ├─ account/router.py (Account endpoints)
  │  └─ admin/router.py (Admin endpoints)
  └─ auth/
     └─ fastapi_openapi_markers.py (bearer_scheme)
```

---

## 🔒 **SECURITY CONSIDERATIONS**

### **Password Security**
- ✅ bcrypt hashing (12 rounds)
- ✅ Minimum password length (8 characters)
- ✅ Password strength validation
- ✅ Constant-time comparison

### **Token Security**
- ✅ JWT signature verification (HS256)
- ✅ Secure secret key storage (environment variables)
- ✅ Token expiration (60 minutes)
- ✅ Refresh token rotation

### **Session Security**
- ✅ Database-backed sessions
- ✅ Session expiration cleanup
- ✅ Logout functionality
- ✅ Concurrent session handling

### **Input Validation**
- ✅ Email format validation
- ✅ Password strength validation
- ✅ SQL injection prevention
- ✅ XSS prevention

### **Rate Limiting**
- ✅ Login attempts
- ✅ Password reset requests
- ✅ Email verification resend

---

## 📊 **SUCCESS METRICS**

### **Performance**
- Registration time: < 500ms
- Login time: < 1s
- Token validation: < 50ms
- Profile update: < 2s

### **Reliability**
- Registration success rate: > 95%
- Login success rate: > 98%
- Email delivery rate: > 99%
- Token validation success: > 99.9%

### **Security**
- Unauthorized access rate: < 0.01%
- Failed login rate: < 2%
- Password reset completion: > 60%
- Email verification rate: > 70%

---

## 🧪 **TESTING**

### **Unit Tests**
- Domain entity validation
- Password hashing
- JWT generation/validation
- Authorization service logic

### **Integration Tests**
- Full registration flow
- Login and session creation
- Password reset flow
- Email verification flow
- Admin user management

### **Security Tests**
- SQL injection attempts
- XSS attempts
- JWT tampering
- Brute force login
- Rate limiting

---

## 📚 **RELATED DOCUMENTATION**

- [User Domain Entity](../../../src/app/domain/entities/user.py)
- [Auth Infrastructure](../../../src/app/infrastructure/auth/)
- [Account Controller](../../../src/app/presentation/http/controllers/account/)
- [Admin Controller](../../../src/app/presentation/http/controllers/admin/)
- [Auth Rules](../../../.cursor/rules/project-rules/auth.mdc)

---

**Status:** ✅ 100% Complete (8/8 use cases live)  
**Last Updated:** December 2, 2025  
**Next Review:** Ongoing maintenance
