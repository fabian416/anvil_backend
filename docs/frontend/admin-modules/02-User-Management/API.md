# User Management API Documentation

> **Complete API Documentation**  
> **Base URLs**: `/api/admin/users`, `/api/admin/wallets`

---

## 🔌 User Operations Endpoints

### 1. List Users
**GET** `/api/admin/users/`

### 2. Activate User
**PATCH** `/api/admin/users/{email}/activate`

### 3. Deactivate User
**PATCH** `/api/admin/users/{email}/deactivate`

### 4. Grant Admin Role
**POST** `/api/admin/users/{email}/grant-admin`

### 5. Revoke Admin Role
**POST** `/api/admin/users/{email}/revoke-admin`

---

## 💼 Wallet Management Endpoints

### 1. Get Wallet Details
**GET** `/api/admin/wallets/{privy_wallet_id}`

### 2. Update Wallet
**PATCH** `/api/admin/wallets/{privy_wallet_id}`

---

## ⚠️ Error Handling

| Status | Error Code | Description |
|--------|------------|-------------|
| `401` | `AuthenticationError` | Not authenticated |
| `403` | `AuthorizationError` | Not authorized |
| `404` | `WalletNotFoundError` | Wallet not found |
| `503` | `DataMapperError` | Service unavailable |

---

## 🔐 Authentication

All endpoints require admin authentication with Bearer token.
