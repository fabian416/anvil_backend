# Module: Login & Authentication

**Route**: `/login`
**Auth Required**: No (Public)
**Package**: `user/onboarding`

## 1. Overview
Handles strict exchange of Privy User credentials for Backend JWT Access Tokens.

## 2. API Contract

### Authentication Handshake
**Endpoint**: `POST /api/v1/account/privy-login`
**Content-Type**: `application/json`

#### Request Body (`PrivyLoginRequestSchema`)
| Field | Type | Required | Description |
|---|---|---|---|
| `privy_user_id` | `string` | **Yes** | DID from Privy (e.g., `did:privy:abc123xyz`) |
| `email` | `string` | No | User email if available |
| `wallet_address` | `string` | No | Primary wallet address |
| `auth_provider` | `string` | No | Default: "privy". Options: `google`, `apple`, `discord`, `wallet` |
| `first_name` | `string` | No | |
| `last_name` | `string` | No | |

**JSON Example**:
```json
{
  "privy_user_id": "did:privy:12345",
  "email": "alice@example.com",
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "auth_provider": "google"
}
```

#### Response Body (`PrivyLoginResponseSchema`)
| Field | Type | Description |
|---|---|---|
| `access_token` | `string` | JWT Bearer Token |
| `refresh_token` | `string` | JWT Refresh Token |
| `token_type` | `string` | Always "bearer" |
| `user_id` | `integer` | Anvil Internal User ID |
| `email` | `string` | Confirmed email |
| `is_new_user` | `boolean` | **Critical Flag**: If `true`, redirect to /onboarding/kyc |

**JSON Example**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "d7s8f7d8s...",
  "token_type": "bearer",
  "user_id": 42,
  "email": "alice@example.com",
  "is_new_user": true
}
```

### Error Codes
| Status | Code (Internal) | Description | UI Behavior |
|---|---|---|---|
| `400` | `DomainFieldError` | Missing constraints | Show "Invalid Request" toast |
| `401` | `AuthenticationError` | Invalid Privy signature | Force re-login with Privy |
| `409` | `EmailAlreadyExistsError` | Email taken by other provider | "Email already used. Try logging in with Google?" |
| `503` | `DataMapperError` | Database Unavailable | "Service Under Maintenance" |

## 3. Implementation Flow

1.  **Privy Trigger**: Call `privy.login()`.
2.  **Wait**: On `onSuccess(user)`:
    - Extract `user.id` -> `privy_user_id`.
    - Extract `user.wallet.address` -> `wallet_address`.
    - Extract `user.email.address` -> `email`.
    - **Map Provider**: If `user.google` exists -> `auth_provider="google"`.
3.  **Backend Auth**:
    - `POST` to `/privy-login`.
4.  **Token Storage**:
    - Save `access_token` to `SecureStore`.
5.  **Routing**:
    - If `response.is_new_user === true` -> `router.push('/onboarding/kyc')`.
    - Else -> `router.push('/home')`.
