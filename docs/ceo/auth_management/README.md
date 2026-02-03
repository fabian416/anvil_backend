# Authentication & User Management - Module Documentation

**Module:** Authentication & User Management
**Architecture:** Hexagonal (Clean Architecture)
**Document Version:** 1.0
**Last Updated:** 2026-01-25

---

## Overview

This directory contains comprehensive documentation for the **Authentication & User Management** module of the Anvil Backend system.

**Module Responsibilities:**
- User registration and authentication
- Session management with JWT tokens
- Email verification and password reset
- Role-based access control (RBAC)
- Admin user management
- Privy integration (wallet & social login)
- Background task processing (emails, analytics)
- User context tracking for AI agents

---

## Documentation Files

### 1. [endpoints.md](./endpoints.md)
**Complete API endpoint documentation.**

**Contents:**
- 20 documented endpoints across guest, user, and admin access levels
- Request/response schemas with examples
- Authentication requirements
- Business logic explanations
- Error response codes
- File references with line numbers

**Coverage:**
- **Guest Endpoints (6):** Sign up, login, Privy login, refresh token, password reset
- **User Endpoints (6):** Profile management, logout, password change, email verification
- **Admin Endpoints (8):** User management, role assignment, activation control

---

### 2. [services.md](./services.md)
**Service layer architecture and implementation.**

**Contents:**
- Domain services (pure business logic)
- Application services (use case orchestration)
- Infrastructure services (external adapters)
- Service dependency graph
- Error handling strategy
- Testing patterns

**Key Services Documented:**
- `UserService` - Core user management business logic
- `AuthService` - Authentication/authorization logic
- `SignUpHandler` - User registration workflow
- `LogInHandler` - Authentication workflow
- `PrivyLogin` - Wallet/social login integration
- Email verification and password reset handlers
- Admin user management interactors
- User context service for AI agents

---

### 3. [celery.md](./celery.md)
**Background task processing with Celery.**

**Contents:**
- Email task implementations (4 tasks)
- User context tasks (3 tasks)
- Queue routing and configuration
- Scheduled tasks (Celery Beat)
- Monitoring with Flower
- Retry policies and error handling
- Production deployment guides

**Task Categories:**
- **Email Tasks:** Verification, password reset, notifications
- **User Context Tasks:** Context updates, analytics generation
- **Scheduled Tasks:** 10-minute context updates, daily analytics

---

## Quick Navigation

### By Concern

**Authentication Flows:**
- [Email/Password Sign Up](./endpoints.md#1-sign-up) → [SignUpHandler](./services.md#3-signuphandler)
- [Email/Password Login](./endpoints.md#2-log-in) → [LogInHandler](./services.md#4-loginhandler)
- [Privy Login](./endpoints.md#3-privy-login) → [PrivyLogin](./services.md#5-privylogin-interactor)
- [Token Refresh](./endpoints.md#4-refresh-token) → [RefreshTokenHandler](./services.md#6-refreshtokenhandler)

**User Profile:**
- [Get Profile](./endpoints.md#7-get-current-user-profile) → [GetMeHandler](./services.md#8-getmehandler--updatemehandler)
- [Update Profile](./endpoints.md#8-update-current-user-profile) → [UpdateMeHandler](./services.md#8-getmehandler--updatemehandler)

**Password Management:**
- [Forgot Password](./endpoints.md#5-forgot-password) → [ForgotPasswordHandler](./services.md#10-password-reset-services)
- [Reset Password](./endpoints.md#6-reset-password) → [ResetPasswordHandler](./services.md#10-password-reset-services)
- [Change Password](./endpoints.md#10-change-own-password) → [ChangePasswordInteractor](./services.md#11-admin-user-management-interactors)

**Email Verification:**
- [Send Verification](./endpoints.md#11-send-email-verification) → [SendEmailVerificationHandler](./services.md#9-email-verification-services)
- [Verify Email](./endpoints.md#12-verify-email) → [VerifyEmailHandler](./services.md#9-email-verification-services)

**Admin Operations:**
- [List Users](./endpoints.md#13-list-all-users) → [ListUsersQueryService](./services.md#13-query-services)
- [Activate/Deactivate](./endpoints.md#14-activate-user) → [ActivateUserInteractor](./services.md#11-admin-user-management-interactors)
- [Grant/Revoke Admin](./endpoints.md#16-grant-admin-role) → [GrantAdminInteractor](./services.md#11-admin-user-management-interactors)

**Background Tasks:**
- [Email Tasks](./celery.md#email-tasks) → 4 email task types
- [User Context Tasks](./celery.md#user-context-tasks) → 3 context management tasks

---

## Architecture Summary

### Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  HTTP Controllers (FastAPI)                                 │
│  - Request/response handling                                │
│  - Pydantic validation                                      │
│  - Error mapping                                            │
└────────────────────────┬────────────────────────────────────┘
                         │ Dishka DI
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  Handlers & Interactors                                     │
│  - Use case orchestration                                   │
│  - Transaction management                                   │
│  - Port coordination                                        │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                             │
│  Domain Services                                            │
│  - Pure business logic                                      │
│  - Entity management                                        │
│  - Business rule enforcement                                │
└────────────────────────┬────────────────────────────────────┘
                         │ Defines Ports
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  Adapters & Repositories                                    │
│  - Database operations                                      │
│  - External integrations                                    │
│  - Authentication handlers                                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Patterns

**CQRS (Command Query Responsibility Segregation):**
- Commands: Write operations via `UserCommandGateway`
- Queries: Read operations via `UserQueryGateway`
- Separate models for optimal performance

**Port-Adapter Pattern:**
- Domain defines interfaces (ports)
- Infrastructure provides implementations (adapters)
- Example: `PasswordHasher` port → `PasswordHasherBcrypt` adapter

**Dependency Injection (Dishka):**
- Request scope: Controllers, handlers, repositories
- Session scope: Database sessions
- App scope: Settings, password hasher

**Error Handling:**
- Domain exceptions: Business rule violations
- Infrastructure exceptions: External service errors
- HTTP mapping: `fastapi-error-map` for contextual errors

---

## Database Schema

### Primary Tables

**users**
- User accounts and profiles
- Columns: id, email, password, first_name, last_name, role, is_active, is_verified, privy_user_id, primary_wallet_address, etc.

**auth_sessions**
- JWT session storage (short-lived)
- Columns: id (session_id), user_id, expiration
- FK: `user_id → users.id`

**sessions**
- Session tracking with IP/user-agent
- Columns: id, user_id, access_token, refresh_token, ip_address, user_agent, created_at, expires_at, last_activity, is_active
- FK: `user_id → users.id`

**email_verifications**
- Email verification tokens
- Columns: id, user_id, token, expires_at, created_at

**password_resets**
- Password reset tokens
- Columns: id, user_id, token, expires_at, used_at

**user_context_aware**
- User context for AI agents
- Columns: id, chat_user_id, portfolio_state, activity_level, user_type, wallet_balance, total_executions, etc.
- Used by authenticated supervisor for personalized responses

---

## Technology Stack

**Framework:** FastAPI 0.116.1

**ORM:** SQLAlchemy 2.0.41 (explicit mappings pattern)

**DI Container:** Dishka 1.6.0

**Database:** PostgreSQL

**Background Tasks:** Celery 5.3.6 + Redis

**Authentication:** JWT with session management

**Password Hashing:** Bcrypt with pepper

**Email:** Mailgun API

**Validation:** Pydantic 2.11.7

**Testing:** Pytest with asyncio

---

## Development Workflow

### Setup

```bash
# Environment setup
export APP_ENV=local
make dotenv           # Generate .env from TOML
make venv             # Create virtual environment
uv pip install -e '.[dev,test]'

# Database setup
make up.db            # Start PostgreSQL
make create-db        # Create database
alembic upgrade head  # Apply migrations
```

### Development Server

```bash
# Start all services
make start-dev        # FastAPI + MCP + Celery + Flower

# Or start individually
make start            # FastAPI only
make celery.worker    # Celery worker
make celery.beat      # Celery Beat scheduler
make celery.flower    # Flower monitoring
```

### Code Quality

```bash
make code.format      # Format with ruff
make code.lint        # Lint (ruff + mypy + slotscheck)
make code.test        # Run pytest
make code.check       # Lint + test
```

---

## Testing

### Unit Tests

**Focus:** Domain services and business logic

**Pattern:** Mock all ports (interfaces)

**Location:** `tests/unit/domain/services/`

**Example:**
```python
def test_user_service_create_user():
    # Given
    user_service = UserService(mock_id_gen, mock_hasher)

    # When
    user = user_service.create_user(
        email=Email("test@example.com"),
        first_name=FirstName("John"),
        last_name=LastName("Doe"),
        password=RawPassword("SecurePass123!"),
    )

    # Then
    assert user.email.value == "test@example.com"
    assert user.is_active.value is True
    assert user.is_verified.value is False
```

### Integration Tests

**Focus:** Handlers and database operations

**Pattern:** Use test database with fixtures

**Location:** `tests/integration/auth/`

**Example:**
```python
async def test_sign_up_handler(test_db_session):
    # Given
    handler = SignUpHandler(...)
    request = SignUpRequest(
        email="new@example.com",
        first_name="Jane",
        last_name="Doe",
        password="SecurePass123!",
    )

    # When
    response = await handler.execute(request)

    # Then
    assert response.user_id > 0
    assert response.access_token is not None
    assert response.refresh_token is not None
```

### API Tests

**Focus:** HTTP endpoints end-to-end

**Pattern:** Use FastAPI TestClient

**Location:** `tests/api/`

**Example:**
```python
def test_login_endpoint(client):
    # Given
    payload = {
        "email": "user@example.com",
        "password": "Password123!",
    }

    # When
    response = client.post("/api/v1/account/login", json=payload)

    # Then
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

## Monitoring

### Application Logs

```bash
# Development
make logs-fastapi

# Production
sudo journalctl -u fastapi -f
```

### Celery Monitoring

```bash
# Flower dashboard
http://localhost:5555

# View active tasks
celery -A app.infrastructure.celery.app inspect active

# Worker logs
make logs-celery
```

### Metrics

**Endpoints:**
- User registrations per day
- Login attempts (success/failure)
- Email delivery rate
- User context update performance

**Tools:**
- Flower for Celery metrics
- Sentry for error tracking
- PostgreSQL slow query log

---

## Security Considerations

### Password Security
- Bcrypt with configurable work factor (default: 12 rounds)
- Pepper stored in config (environment-specific)
- No plaintext password storage

### JWT Security
- Short-lived access tokens (configurable expiration)
- Refresh token rotation (optional)
- Session invalidation on logout
- Server-side session storage

### Email Security
- Verification tokens: 256-bit random (32 bytes)
- Reset tokens: 256-bit random, single-use
- 24-hour expiration on all tokens

### IP Tracking
- Registration IP stored for audit
- Last IP updated on login
- User-agent tracking for suspicious activity

### Rate Limiting
- Login retry count tracking
- Future: Rate limiting middleware (not yet implemented)

### Admin Controls
- Super admin email whitelist
- Role-based access control
- Audit logging for admin actions

---

## Migration Guide

### Legacy to New System

**Email/Password Users:**
- No migration needed (compatible)

**Privy Users:**
- New format: `did:privy:...`
- Legacy format: stripped prefix
- Auto-upgrade on login

**Sessions:**
- Old sessions remain valid until expiration
- New sessions use new format

**User Context:**
- Celery task creates missing contexts
- Runs every 10 minutes
- Backfills existing users

---

## Troubleshooting

### Email Not Sending

**Check:**
1. Mailgun configuration in `config/{env}/.secrets.toml`
2. Celery worker is running: `make celery.worker`
3. Email queue has workers: `celery inspect active_queues`
4. Mailgun logs: https://app.mailgun.com/logs

**Debug:**
```bash
# Check Celery logs
make logs-celery

# Manually trigger email task
celery -A app.infrastructure.celery.app call tasks.email_tasks.send_email \
    --kwargs='{"to_email": "test@example.com", "subject": "Test", "body": "Hello"}'
```

---

### JWT Token Invalid

**Common Issues:**
1. Token expired (check `expires_at`)
2. Session deleted (check `auth_sessions` table)
3. User logged out (session invalidated)
4. JWT secret changed (invalidates all tokens)

**Debug:**
```python
# Decode JWT without verification
import jwt
token = "eyJhbGciOiJIUzI1NiIs..."
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

---

### User Context Not Creating

**Check:**
1. Celery Beat is running: `make celery.beat`
2. `update_user_context` task scheduled
3. User is authenticated (not guest)
4. `chat_users` table has entry

**Debug:**
```bash
# Manually trigger
celery -A app.infrastructure.celery.app call update_user_context

# Check logs
make logs-celery
```

---

## Contributing

### Adding New Endpoints

1. **Define endpoint** in `src/app/presentation/http/controllers/`
2. **Create handler/interactor** in `src/app/application/` or `src/app/infrastructure/auth/handlers/`
3. **Implement business logic** in domain service (if needed)
4. **Add error mapping** in controller
5. **Write tests** (unit + integration + API)
6. **Update documentation** in this folder

### Adding New Background Tasks

1. **Define task** in `src/app/infrastructure/celery/tasks/`
2. **Add to beat schedule** in `src/app/infrastructure/celery/app.py` (if scheduled)
3. **Add queue routing** in `task_routes` (if dedicated queue)
4. **Write tests** (unit + integration)
5. **Update [celery.md](./celery.md)** documentation

---

## Related Documentation

**General Documentation:**
- [Main README](../../../README.md) - Project overview
- [CLAUDE.md](../../../CLAUDE.md) - Development guidelines
- [Architecture Guide](../../architecture/) - Hexagonal architecture patterns

**API Documentation:**
- [Swagger UI](http://localhost:8000/docs) - Interactive API docs (development)
- [ReDoc](http://localhost:8000/redoc) - Alternative API docs

**External References:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Dishka Documentation](https://dishka.readthedocs.io/)

---

## Contact

**Module Owner:** Backend Team

**Questions:** See main project README for contact information

---

**Document Status:** Complete
**Review Date:** 2026-01-25
**Next Review:** 2026-04-25 (quarterly)

---

**End of README**
