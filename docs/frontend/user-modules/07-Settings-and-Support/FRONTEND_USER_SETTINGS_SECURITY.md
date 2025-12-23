# FRONTEND_USER_SETTINGS_SECURITY

> **Enterprise Grade Specification**
> Version: 2.0.0
> Status: **Live**
> Source Validation: `src/app/presentation/http/controllers/account` & `wallet`

## 1. Module Overview
The **Security Settings** module handles sensitive operations like password updates (if applicable) and wallet key exports.

**Base URL**: `/api/v1`

---

## 2. Endpoints

### 2.1 Export Wallet Key
**POST** `/api/v1/wallet/export`

Requests an encrypted export of the embedded wallet's private key.

**Request**:
*   Requires re-authentication (MFA or password confirmation) via Privy.

**Response (200 OK):**
```json
{
  "encrypted_key": "...",
  "format": "hpke"
}
```

### 2.2 Change Password / Auth Methods
*   **Redirect**: Authentication settings are managed directly via the **Privy Modal** on the frontend.
*   **API**: Backend endpoints for auth updates are primarily internal hooks for Privy webhooks.

---

## 3. Security Notes
*   **MFA**: Critical actions require step-up authentication.
*   **Audit**: All exports are logged in `audit_log` table.
