# Module: Security Settings

**Route**: `/settings/security`
**Auth Required**: Yes
**Package**: `user/settings`

## 1. Overview
Manage account credentials and wallet exports.

## 2. API Contract

### Change Password
**Endpoint**: `PUT /api/v1/account/change-password`
**Body**:
```json
{
  "current_password": "...",
  "new_password": "...",
  "confirm_password": "..."
}
```

### Export Wallet
**Endpoint**: `POST /api/v1/wallet/export`
**Body**: `{"wallet_id": "..."}`
**Response (`ExportWalletResponse`)**:
```json
{
  "private_key": "0x...",
  "chain_type": "ethereum"
}
```
**Constraints**:
- Must be the owner.
- Verification required (Auth Token).

## 3. Implementation Flow
1.  **Export Flow**:
    - "Export Private Key" button (Red, Dangerous).
    - Modal: "Are you sure? Never share this key."
    - User confirms -> Call Backend.
    - Display Key *once*, allow copy, then clear from memory on close.
