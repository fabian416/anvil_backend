# Authentication & Authorization System - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

Anvil Backend implementa un sistema de autenticación híbrido que soporta:

1. **Privy Authentication** (Web3-native): Wallet connections, social logins
2. **Traditional Authentication**: Email/password for legacy users
3. **Role-Based Access Control (RBAC)**: User, Moderator, Admin, Guest roles
4. **Super Admin**: Configured via environment variable

---

## Authentication Methods

### 1. Privy Authentication (Primary - Recommended)

**Endpoint**: `POST /api/v1/account/privy-login`

Privy es el método principal de autenticación, soportando:

- **Wallet Connections**: MetaMask, WalletConnect, Coinbase Wallet, etc.
- **Social Logins**: Google, Apple, Twitter, Discord
- **Email via Privy**: Email OTP authentication

#### Flow Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │     │   Privy SDK     │     │  Anvil Backend  │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │  1. User connects     │                       │
         │  wallet/social ──────►│                       │
         │                       │                       │
         │  2. Privy validates   │                       │
         │  & returns user data  │                       │
         │◄─────────────────────│                       │
         │                       │                       │
         │  3. POST /privy-login │                       │
         │  with privy_user_id ─────────────────────────►│
         │                       │                       │
         │                       │   4. Find/Create user │
         │                       │   5. Generate JWT     │
         │                       │   6. Create session   │
         │                       │                       │
         │  7. Return tokens    ◄────────────────────────│
         │◄─────────────────────│                       │
         │                       │                       │
         │  8. Store tokens,     │                       │
         │  user authenticated   │                       │
         ▼                       ▼                       ▼
```

#### Request Schema

```json
{
  "privy_user_id": "did:privy:abc123xyz",
  "email": "user@example.com",           // Optional
  "wallet_address": "0x1234...5678",     // Optional
  "auth_provider": "wallet",             // privy, wallet, google, apple
  "first_name": "John",                  // Optional
  "last_name": "Doe"                     // Optional
}
```

#### Response Schema

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

#### Auto-Registration

- Si el usuario no existe, se crea automáticamente
- Usuarios Privy son marcados como `is_verified: true` (pre-verified)
- Wallet address se sincroniza a la tabla `wallets` automáticamente

### 2. Traditional Authentication (Email/Password)

**Endpoints**:
- `POST /api/v1/account/signup` - Registro
- `POST /api/v1/account/login` - Login
- `POST /api/v1/account/logout` - Logout

#### Signup Flow

```python
# Request
{
  "email": "user@example.com",
  "password": "SecureP@ssword123",
  "first_name": "John",
  "last_name": "Doe"
}

# Response
{
  "user_id": 123,
  "email": "user@example.com",
  "message": "Account created successfully"
}
```

#### Login Flow

```python
# Request
{
  "email": "user@example.com",
  "password": "SecureP@ssword123"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 123,
  "expires_at": "2026-01-03T12:00:00Z"
}
```

---

## JWT Token System

### Token Configuration

```toml
# config/local/.secrets.toml
[security.auth]
JWT_SECRET = "your-super-secret-jwt-key"
JWT_ALGORITHM = "HS256"
SESSION_TTL_MIN = 60              # 60 minutes
SESSION_REFRESH_THRESHOLD = 0.5   # Refresh at 50% remaining
```

### Token Structure

```json
{
  "sub": "123",                    // User ID
  "session_id": "uuid-here",       // Session ID
  "iat": 1704189600,              // Issued at
  "exp": 1704193200,              // Expiration
  "type": "access"                // Token type
}
```

### Token Refresh

**Endpoint**: `POST /api/v1/account/refresh-token`

- Tokens se refrescan automáticamente antes de expirar
- El umbral de refresh es configurable (default: 50%)
- Requiere el refresh_token válido

---

## Session Management

### Session Storage

Sessions se almacenan en PostgreSQL para persistencia y auditoría:

```sql
CREATE TABLE auth_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    access_token TEXT,
    refresh_token TEXT,
    token_type VARCHAR(50),
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    last_activity TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
```

### Session Features

- **IP Tracking**: Registra IP de registro y último login
- **User Agent**: Almacena información del navegador/app
- **Activity Tracking**: Actualiza `last_activity` en cada request
- **Multi-Session**: Un usuario puede tener múltiples sesiones activas

---

## Role-Based Access Control (RBAC)

### User Roles

| Role | Level | Permissions |
|------|-------|-------------|
| **ADMIN** | 1 | Full system access, user management |
| **MODERATOR** | 2 | Content moderation, limited admin |
| **USER** | 3 | Standard authenticated features |
| **GUEST** | 4 | Limited public features |

### Role Hierarchy

```python
class UserRole(StrEnum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"
    
    @classmethod
    def get_hierarchy(cls, role: str) -> List[str]:
        """Higher roles inherit lower role permissions."""
        if role == cls.ADMIN:
            return [cls.ADMIN, cls.MODERATOR, cls.USER, cls.GUEST]
        elif role == cls.MODERATOR:
            return [cls.MODERATOR, cls.USER, cls.GUEST]
        elif role == cls.USER:
            return [cls.USER, cls.GUEST]
        return [cls.GUEST]
```

### Permission Checks

```python
# In interactor
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import CanManageRole

# Check permission
authorize(
    CanManageRole(),
    context=RoleManagementContext(
        subject=current_user,
        target_role=UserRole.ADMIN,
    ),
)
```

---

## Admin System

### Super Admin

El **Super Admin** es un usuario especial configurado por email:

```toml
# config/local/config.toml
[admin]
USER_ADMIN = "admin@anvilcrypto.com"
ALLOWED_ADMIN_EMAILS = [
    "admin@anvilcrypto.com",
    "ops@anvilcrypto.com",
    "cto@anvilcrypto.com"
]
```

### Super Admin Capabilities

- Único que puede **grant/revoke admin roles**
- No puede ser desactivado ni eliminado
- Se protege contra modificaciones

### Auto-Admin Assignment

Usuarios con email en `ALLOWED_ADMIN_EMAILS`:
- Se asignan automáticamente como ADMIN en registro
- Se promueven a ADMIN si ya existen (en login)

```python
# In PrivyLogin interactor
if self._admin_settings.is_admin_email(email):
    role = UserRole.ADMIN
```

### Admin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/users` | GET | List all users |
| `/admin/users/{email}/grant-admin` | PATCH | Grant admin role |
| `/admin/users/{email}/revoke-admin` | PATCH | Revoke admin role |
| `/admin/users/{email}/activate` | PATCH | Activate user |
| `/admin/users/{email}/deactivate` | PATCH | Deactivate user |
| `/admin/users/{email}/password` | PATCH | Change user password |

---

## Privy Integration Details

### Configuration

```toml
# config/local/config.toml
[privy]
APP_ID = "your-privy-app-id"
API_BASE_URL = "https://api.privy.io"

# config/local/.secrets.toml
[privy]
APP_SECRET = "your-privy-app-secret"
```

### Privy Client Features

```python
class PrivyClient(EmbeddedWalletProviderPort):
    """HTTP client for Privy API."""
    
    # Token Verification
    async def verify_token(self, access_token: str) -> TokenVerificationResult
    
    # User Operations
    async def get_user(self, user_id: str) -> UserInfo
    async def get_user_by_email(self, email: str) -> UserInfo | None
    async def get_user_by_wallet_address(self, address: str) -> UserInfo | None
    
    # Wallet Operations
    async def get_wallet(self, wallet_id: str) -> WalletInfo
    async def list_user_wallets(self, user_id: str) -> list[WalletInfo]
    async def create_wallet_for_user(self, user_id: str, chain: ChainType) -> WalletInfo
    async def export_wallet(self, wallet_id: str, public_key: str) -> WalletExportResponse
    
    # Policy Operations
    async def create_policy(self, ...) -> dict
    async def list_policies(self, ...) -> list
    async def update_policy(self, policy_id: str, ...) -> dict
```

### Supported Chains

```python
class ChainType(Enum):
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    OTHER = "other"
```

---

## Security Features

### Password Security

- **Hashing**: bcrypt with configurable work factor
- **Pepper**: Application-level secret added to passwords
- **Salt**: Unique per-password (bcrypt default)

```toml
[security.password]
PEPPER = "your-password-pepper"
```

### Brute Force Protection

- Login retry counter incrementado en cada fallo
- Bloqueo temporal después de N intentos fallidos
- Reset automático en login exitoso

```python
# In UserService
def increment_login_retry_count(self, user: User) -> None:
    user.retry_count = RetryCount(user.retry_count.value + 1)
    
def record_successful_login(self, user: User) -> None:
    user.retry_count = RetryCount(0)  # Reset on success
    user.last_login = datetime.utcnow()
```

### Rate Limiting

| Endpoint Type | Limit |
|---------------|-------|
| Login | 5 attempts / 15 min |
| Password Reset | 3 requests / hour |
| Signup | 10 / hour / IP |
| API General | 100 / minute |

### Input Validation

- Email format validation (Pydantic)
- Password strength requirements
- Wallet address format validation
- Privy user ID format validation

---

## Error Handling

### Authentication Errors

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `AuthenticationError` | 401 | Invalid credentials |
| `AlreadyAuthenticatedError` | 400 | User already logged in |
| `TokenExpiredError` | 401 | JWT token expired |
| `InvalidTokenError` | 401 | Malformed JWT |

### Authorization Errors

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `AuthorizationError` | 403 | Insufficient permissions |
| `InsufficientPermissionsError` | 403 | Not authorized for action |
| `RoleChangeNotAllowedError` | 403 | Cannot change role |

### User Errors

| Error | HTTP Status | Description |
|-------|-------------|-------------|
| `UserNotFoundByEmailError` | 404 | User not found |
| `EmailAlreadyExistsError` | 409 | Email already registered |
| `AccountInactiveError` | 401 | Account deactivated |
| `AccountBlockedError` | 401 | Account blocked |

---

## Implementation Architecture

### Layer Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                            │
│  Controllers: privy_login.py, log_in.py, sign_up.py, etc.      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  Interactors: PrivyLogin, GrantAdminInteractor                  │
│  Services: CurrentUserService, AuthorizationService             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                          │
│  Handlers: LogInHandler, SignUpHandler, etc.                    │
│  Adapters: AuthGatewaySqla, PrivyClient                         │
│  Session: AuthSessionService                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
│  Services: AuthService, UserService                              │
│  Entities: User, AuthSession                                     │
│  Value Objects: Email, Password, PrivyUserId, WalletAddress     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files

| Layer | File | Purpose |
|-------|------|---------|
| Presentation | `controllers/account/privy_login.py` | Privy login endpoint |
| Presentation | `controllers/account/router.py` | Account routes |
| Application | `commands/auth/privy_login.py` | Privy login interactor |
| Application | `commands/user/grant_admin.py` | Grant admin interactor |
| Infrastructure | `privy/client.py` | Privy API client |
| Infrastructure | `auth/handlers/log_in.py` | Login handler |
| Infrastructure | `auth/session/service.py` | Session management |
| Domain | `services/auth.py` | Auth business logic |
| Domain | `enums/user_role.py` | Role definitions |
| Config | `config/admin.py` | Admin settings |

---

## Testing Authentication

### Test Privy Login

```bash
curl -X POST http://localhost:8000/api/v1/account/privy-login \
  -H "Content-Type: application/json" \
  -d '{
    "privy_user_id": "did:privy:test123",
    "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
    "auth_provider": "wallet"
  }'
```

### Test Traditional Login

```bash
curl -X POST http://localhost:8000/api/v1/account/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ssword123"
  }'
```

### Test Protected Endpoint

```bash
curl http://localhost:8000/api/v1/user/chat/conversations \
  -H "Authorization: Bearer <access_token>"
```

### Test Admin Endpoint

```bash
curl -X PATCH http://localhost:8000/api/v1/admin/users/user@example.com/grant-admin \
  -H "Authorization: Bearer <super_admin_token>"
```

---

## Quick Reference

### Authentication Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/account/signup` | POST | ❌ | Register new user |
| `/account/login` | POST | ❌ | Email/password login |
| `/account/privy-login` | POST | ❌ | Privy auth login |
| `/account/logout` | DELETE | ✅ | Logout user |
| `/account/refresh-token` | POST | ✅ | Refresh tokens |
| `/account/me` | GET | ✅ | Get current user |
| `/account/password` | PUT | ✅ | Change password |
| `/account/password-reset/request` | POST | ❌ | Request reset |
| `/account/password-reset/confirm` | POST | ❌ | Confirm reset |

### Admin Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/admin/users` | GET | 🔒 Admin | List users |
| `/admin/users/{email}/grant-admin` | PATCH | 🔒 Super | Grant admin |
| `/admin/users/{email}/revoke-admin` | PATCH | 🔒 Super | Revoke admin |
| `/admin/users/{email}/activate` | PATCH | 🔒 Admin | Activate user |
| `/admin/users/{email}/deactivate` | PATCH | 🔒 Admin | Deactivate user |

---

**Last Updated**: January 2, 2026
