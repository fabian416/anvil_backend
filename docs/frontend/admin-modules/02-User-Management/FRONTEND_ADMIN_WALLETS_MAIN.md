# Admin Module: Wallet Management

> **Technical Specification**: `FRONTEND_ADMIN_WALLETS_MAIN`
> **Backend Controllers**: `admin/wallet/get_wallet_details.py`, `admin/wallet/update_wallet.py`
> **Base URL**: `/api/admin/wallets`

## 📖 Overview
The **Wallet Management** submodule enables administrators to view and manage user wallet configurations. It provides access to wallet details from both the local database and Privy API, allowing admins to update wallet policies, owners, and additional signers.

### Key Capabilities
1. **Wallet Details**: View comprehensive wallet information including Privy wallet ID, policies, owner, and signers.
2. **Wallet Configuration**: Update wallet policies, owner, and additional signers.
3. **Status Monitoring**: View wallet status and configuration state.

---

## 🔌 API Endpoints

### 1. Get Wallet Details
**GET** `/api/admin/wallets/{privy_wallet_id}`
Retrieve detailed wallet information from both local database and Privy API.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `privy_wallet_id` | `str` | **Yes** | Privy wallet identifier (in URL path). |

**Response (`AdminWalletDetailsResponse`)**:
```json
{
  "privy_wallet_id": "wallet-abc123",
  "policy_ids": ["policy-1", "policy-2"],
  "owner": {
    "user_id": "user-uuid",
    "public_key": "0x..."
  },
  "additional_signers": [
    {
      "user_id": "user-uuid-2",
      "public_key": "0x..."
    }
  ],
  "created_at": "2023-10-01T10:00:00Z",
  "updated_at": "2023-10-15T14:30:00Z"
}
```

### 2. Update Wallet
**PATCH** `/api/admin/wallets/{privy_wallet_id}`
Update wallet configuration including policies, owner, and additional signers.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `privy_wallet_id` | `str` | **Yes** | Privy wallet identifier (in URL path). |

**Request Body (`UpdateWalletRequest`)**:
```json
{
  "policy_ids": ["policy-1", "policy-2"],
  "owner": {
    "user_id": "user-uuid",
    "public_key": "0x..."
  },
  "additional_signers": [
    {
      "user_id": "user-uuid-2",
      "public_key": "0x..."
    }
  ]
}
```

**Response (`UpdateWalletResponse`)**:
```json
{
  "privy_wallet_id": "wallet-abc123",
  "policy_ids": ["policy-1", "policy-2"],
  "owner": {
    "user_id": "user-uuid",
    "public_key": "0x..."
  },
  "additional_signers": [
    {
      "user_id": "user-uuid-2",
      "public_key": "0x..."
    }
  ],
  "updated_at": "2023-10-15T14:30:00Z"
}
```

---

## 🎨 UI/UX Guidelines

### Wallet Details View
- **Header**: Display Privy wallet ID prominently.
- **Sections**:
  - **Policies**: List of policy IDs with links to policy management.
  - **Owner**: Display owner user ID and public key.
  - **Additional Signers**: Table of additional signers with user IDs and public keys.
  - **Metadata**: Created/Updated timestamps.
- **Actions**: "Edit Wallet" button to open update form.

### Update Wallet Form
- **Policy Selection**: Multi-select dropdown or tag input for policy IDs.
- **Owner Configuration**: User selector or public key input.
- **Additional Signers**: Dynamic list with add/remove buttons.
- **Validation**: Ensure owner and signers are valid user IDs or public keys.
- **Confirmation**: Show confirmation modal before updating wallet configuration.

### Error Handling
- **404 Not Found**: Display "Wallet not found" message with wallet ID.
- **502 Bad Gateway**: Show "Unable to connect to Privy" error with retry option.
- **503 Service Unavailable**: Display service unavailable message.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Sensitive Data**: Wallet IDs and public keys are sensitive; ensure proper access controls.
- **Audit Trail**: Log all wallet configuration changes for audit purposes.
