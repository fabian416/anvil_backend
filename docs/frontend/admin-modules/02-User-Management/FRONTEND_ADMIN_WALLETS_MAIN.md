# Module: Wallet Management

**Route**: `/admin/wallets`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/wallets`

## 1. Overview
Enables administrators to view and manage user wallet configurations. Provides access to wallet details from both the local database and Privy API, allowing admins to update wallet policies, owners, and additional signers.

## 2. API Contract

### Get Wallet Details
**Endpoint**: `GET /api/admin/wallets/{privy_wallet_id}`  
**Path Params**:
- `privy_wallet_id` (string, **required**): Privy wallet identifier.

#### Response Body (`AdminWalletDetailsResponse`)
| Field | Type | Description |
|---|---|---|
| `local_wallet_id` | `number \| null` | Local database wallet ID or null |
| `privy_wallet_id` | `string` | Privy wallet identifier |
| `address` | `string` | Wallet address (0x...) |
| `chain_type` | `string` | Chain type (e.g., "evm") |
| `user_id` | `number \| null` | Associated user ID or null |
| `owner_type` | `string \| null` | Owner type or null |
| `owner_id` | `string \| null` | Owner identifier or null |
| `policy_ids` | `string[]` | Array of policy IDs |
| `additional_signers` | `AdditionalSignerResponse[]` | Array of additional signers |
| `provider` | `string` | Wallet provider |
| `status` | `string` | Wallet status |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `updated_at` | `string` | ISO 8601 update timestamp |

**AdditionalSignerResponse Object**:
| Field | Type | Description |
|---|---|---|
| `signer_id` | `string` | Signer identifier |
| `override_policy_ids` | `string[] \| null` | Override policy IDs or null |

**JSON Example**:
```json
{
  "local_wallet_id": 123,
  "privy_wallet_id": "wallet-abc123",
  "address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "chain_type": "evm",
  "user_id": 456,
  "owner_type": "user",
  "owner_id": "user-uuid",
  "policy_ids": ["policy-1", "policy-2"],
  "additional_signers": [
    {
      "signer_id": "signer-xyz",
      "override_policy_ids": ["policy-3"]
    }
  ],
  "provider": "privy",
  "status": "active",
  "created_at": "2023-10-01T10:00:00Z",
  "updated_at": "2023-10-15T14:30:00Z"
}
```

### Update Wallet
**Endpoint**: `PATCH /api/admin/wallets/{privy_wallet_id}`  
**Path Params**:
- `privy_wallet_id` (string, **required**): Privy wallet identifier.

#### Request Body (`UpdateWalletRequest`)
| Field | Type | Description |
|---|---|---|
| `policy_ids` | `string[]` | Optional: Array of policy IDs |
| `owner` | `{ [key: string]: any }` | Optional: Owner object |
| `owner_id` | `string` | Optional: Owner identifier |
| `additional_signers` | `AdditionalSignerRequest[]` | Optional: Array of additional signers |

**AdditionalSignerRequest Object**:
| Field | Type | Description |
|---|---|---|
| `signer_id` | `string` | Signer identifier |
| `override_policy_ids` | `string[] \| null` | Optional: Override policy IDs |

**JSON Example**:
```json
{
  "policy_ids": ["policy-1", "policy-2", "policy-3"],
  "owner": {
    "user_id": "user-uuid",
    "public_key": "0x..."
  },
  "additional_signers": [
    {
      "signer_id": "signer-xyz",
      "override_policy_ids": ["policy-4"]
    }
  ]
}
```

#### Response Body (`UpdateWalletResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether update was successful |
| `changes_applied` | `WalletChanges` | Object describing changes applied |
| `privy_wallet_id` | `string` | Privy wallet identifier |
| `updated_at` | `string` | ISO 8601 update timestamp |

**WalletChanges Object**:
| Field | Type | Description |
|---|---|---|
| `policy_ids` | `string[]` | Updated policy IDs (if changed) |
| `owner` | `{ [key: string]: any }` | Updated owner (if changed) |
| `additional_signers` | `AdditionalSignerResponse[]` | Updated signers (if changed) |

**JSON Example**:
```json
{
  "success": true,
  "changes_applied": {
    "policy_ids": ["policy-1", "policy-2", "policy-3"],
    "additional_signers": [
      {
        "signer_id": "signer-xyz",
        "override_policy_ids": ["policy-4"]
      }
    ]
  },
  "privy_wallet_id": "wallet-abc123",
  "updated_at": "2024-01-15T14:35:00Z"
}
```

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid wallet configuration" |
| `502` | `GatewayError` | Privy API error | Show error: "Unable to connect to Privy" + Retry button |
| `500` | `Exception` | Internal server error | Show error: "Failed to update wallet" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useWalletDetails(privyWalletId)` hook which fetches `/api/admin/wallets/{privy_wallet_id}`.
2. **Display**:
   - Wallet header: Display `privy_wallet_id` and `address` prominently.
   - Policies section: Display `policy_ids` as tags with links to policy management.
   - Owner section: Display `owner_type`, `owner_id`, and owner details if available.
   - Additional signers section: Display `additional_signers` in a table with signer IDs and override policies.
   - Metadata: Display `created_at` and `updated_at` timestamps.
3. **Edit Wallet**: On "Edit Wallet" button click, open edit form/modal with current values pre-populated.
4. **Update Wallet**: On form submit:
   - Validate form data (ensure policy IDs are valid, signers are valid).
   - Show confirmation modal: "Are you sure you want to update this wallet configuration?"
   - Call `PATCH /api/admin/wallets/{privy_wallet_id}` with request body.
   - On success: Update display, show success toast, invalidate query cache.
   - On error: Display error message based on error code, provide retry option.
5. **Error Handling**: Handle Privy API errors (502) with specific messaging and retry option.
