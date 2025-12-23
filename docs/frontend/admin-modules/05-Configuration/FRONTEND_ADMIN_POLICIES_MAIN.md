# Module: Policy Management

**Route**: `/admin/configuration/policies`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/configuration/policies`

## 1. Overview
Enables administrators to manage Privy policies for wallet security and access control. Policies define rules for wallet operations, transaction limits, and authorization requirements. Policies are managed through Privy API integration.

## 2. API Contract

### List Policies
**Endpoint**: `GET /api/admin/policies/`  
**Query Params**:
- `cursor` (string, optional): Pagination cursor.
- `limit` (number, optional): Number of results (1-1000, default varies).
- `chain_type` (string, optional): Filter by chain type (e.g., "ethereum").
- `include_raw` (boolean, optional): Include raw Privy response (Default: false).
- `refresh` (boolean, optional): Refresh from Privy before returning (Default: false).
- `meta_key` (string, optional): Filter by local metadata key.
- `meta_value` (string, optional): Filter by local metadata key value.

#### Response Body (`ListPoliciesResponse`)
| Field | Type | Description |
|---|---|---|
| `policies` | `PolicySummary[]` | Array of policy summaries |
| `next_cursor` | `string \| null` | Pagination cursor or null |
| `total_count` | `number` | Total number of policies |
| `raw` | `any \| null` | Raw Privy response or null (if include_raw=true) |

**PolicySummary Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Policy identifier |
| `name` | `string` | Policy name |
| `version` | `string` | Policy version |
| `chain_type` | `string` | Chain type |
| `owner_id` | `string` | Owner UUID |

**JSON Example**:
```json
{
  "policies": [
    {
      "id": "policy-abc123",
      "name": "Standard Wallet Policy",
      "version": "1.0",
      "chain_type": "ethereum",
      "owner_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "next_cursor": "cursor-string",
  "total_count": 25,
  "raw": null
}
```

### Get Policy
**Endpoint**: `GET /api/admin/policies/{policy_id}`  
**Path Params**:
- `policy_id` (string, **required**): Policy identifier.

#### Response Body (`GetPolicyResponse`)
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Policy identifier |
| `name` | `string` | Policy name |
| `version` | `string` | Policy version |
| `chain_type` | `string` | Chain type |
| `rules` | `PolicyRule[]` | Array of policy rules |
| `owner_id` | `string` | Owner UUID |
| `metadata` | `{ [key: string]: any } \| null` | Optional metadata |

**PolicyRule Object**:
| Field | Type | Description |
|---|---|---|
| `rule_id` | `string` | Rule identifier |
| `type` | `string` | Rule type |
| `config` | `{ [key: string]: any }` | Rule configuration |

**JSON Example**:
```json
{
  "id": "policy-abc123",
  "name": "Standard Wallet Policy",
  "version": "1.0",
  "chain_type": "ethereum",
  "rules": [
    {
      "rule_id": "rule-1",
      "type": "transaction_limit",
      "config": {
        "max_amount": "1000",
        "currency": "USD"
      }
    }
  ],
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "description": "Standard policy for regular users"
  }
}
```

### Create Policy
**Endpoint**: `POST /api/admin/policies/`  
**Query Params**: None

#### Request Body (`CreatePolicyRequest`)
| Field | Type | Description |
|---|---|---|
| `version` | `string` | Policy version (required) |
| `name` | `string` | Policy name (required) |
| `chain_type` | `string` | Chain type (required) |
| `rules` | `PolicyRuleRequestBody[]` | Array of policy rules (required) |
| `metadata` | `{ [key: string]: any }` | Optional: Metadata |
| `owner` | `{ [key: string]: any }` | Optional: Owner object |
| `authorization_signature` | `string` | Optional: Authorization signature |

**PolicyRuleRequestBody Object**:
| Field | Type | Description |
|---|---|---|
| `type` | `string` | Rule type (required) |
| `config` | `{ [key: string]: any }` | Rule configuration (required) |

**JSON Example**:
```json
{
  "version": "1.0",
  "name": "Custom Wallet Policy",
  "chain_type": "ethereum",
  "rules": [
    {
      "type": "transaction_limit",
      "config": {
        "max_amount": "5000",
        "currency": "USD"
      }
    }
  ],
  "metadata": {
    "description": "Custom policy for high-value transactions"
  },
  "owner": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### Response Body (`CreatePolicyResponse`)
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Created policy identifier |
| `name` | `string` | Policy name |
| `version` | `string` | Policy version |
| `chain_type` | `string` | Chain type |
| `rules` | `PolicyRuleResponse[]` | Array of policy rules |
| `owner_id` | `string` | Owner UUID |

### Update Policy
**Endpoint**: `PATCH /api/admin/policies/{policy_id}`  
**Path Params**:
- `policy_id` (string, **required**): Policy identifier.

#### Request Body (`UpdatePolicyRequestBody`)
| Field | Type | Description |
|---|---|---|
| `name` | `string` | Optional: Updated policy name |
| `rules` | `PolicyRuleRequestBody[]` | Optional: Updated rules |
| `metadata` | `{ [key: string]: any }` | Optional: Updated metadata |
| `authorization_signature` | `string` | Optional: Authorization signature |

**JSON Example**:
```json
{
  "name": "Updated Policy Name",
  "rules": [
    {
      "type": "transaction_limit",
      "config": {
        "max_amount": "10000",
        "currency": "USD"
      }
    }
  ]
}
```

#### Response Body (`UpdatePolicyResponse`)
Returns updated policy object.

### Create Policy Rule
**Endpoint**: `POST /api/admin/policies/{policy_id}/rules`  
**Path Params**:
- `policy_id` (string, **required**): Policy identifier.

#### Request Body (`PolicyRuleRequestBody`)
| Field | Type | Description |
|---|---|---|
| `type` | `string` | Rule type (required) |
| `config` | `{ [key: string]: any }` | Rule configuration (required) |

#### Response Body (`PolicyRuleResponse`)
| Field | Type | Description |
|---|---|---|
| `rule_id` | `string` | Created rule identifier |
| `type` | `string` | Rule type |
| `config` | `{ [key: string]: any }` | Rule configuration |
| `priority` | `number` | Rule priority |
| `created_at` | `string` | ISO 8601 creation timestamp |

### Update Policy Rule
**Endpoint**: `PATCH /api/admin/policies/{policy_id}/rules/{rule_id}`  
**Path Params**:
- `policy_id` (string, **required**): Policy identifier.
- `rule_id` (string, **required**): Rule identifier.

#### Request Body (`PolicyRuleRequestBody`)
Same as create rule.

#### Response Body (`PolicyRuleResponse`)
Returns updated rule object.

### Delete Policy Rule
**Endpoint**: `DELETE /api/admin/policies/{policy_id}/rules/{rule_id}`  
**Path Params**:
- `policy_id` (string, **required**): Policy identifier.
- `rule_id` (string, **required**): Rule identifier.

#### Response
`204 No Content` - No response body

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Policy or rule not found | Show error: "Policy not found" or "Rule not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid policy configuration" |
| `502` | `GatewayError` | Privy API error | Show error: "Unable to connect to Privy" + Retry button |
| `500` | `Exception` | Internal server error | Show error: "Failed to manage policy" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `usePolicies({ cursor, limit, chain_type, refresh })` hook which fetches `/api/admin/policies/`.
2. **Display**:
   - Policies table: Display `policies` array with columns: Name, Version, Chain Type, Owner, Rules Count, Actions.
   - Pagination: Use `next_cursor` for cursor-based pagination.
   - Filter: Provide filters for chain type and metadata.
3. **Create Policy**: On "Create Policy" button click:
   - Open create policy modal/form.
   - Collect required fields (version, name, chain_type, rules).
   - Validate rules configuration.
   - On submit, call `POST /api/admin/policies/` with request body.
   - On success: Add policy to list, show success toast, invalidate query cache.
   - On Privy API error (502): Show specific error message with retry option.
4. **View Policy Details**: On policy click, call `GET /api/admin/policies/{policy_id}` to show detailed view in modal or navigate to detail page.
5. **Update Policy**: On "Edit" button click:
   - Open edit modal with current values pre-populated.
   - Allow updating name, rules, metadata.
   - On submit, call `PATCH /api/admin/policies/{policy_id}` with request body.
   - On success: Update display, show success toast, invalidate query cache.
6. **Manage Policy Rules**:
   - In policy details view, display `rules` array.
   - **Create Rule**: On "Add Rule" button click:
     - Open create rule modal.
     - Select rule type and configure rule config.
     - Call `POST /api/admin/policies/{policy_id}/rules` with request body.
     - On success: Add rule to list, show success toast.
   - **Update Rule**: On "Edit Rule" button click:
     - Open edit modal with current rule values.
     - Call `PATCH /api/admin/policies/{policy_id}/rules/{rule_id}` with request body.
     - On success: Update rule in list, show success toast.
   - **Delete Rule**: On "Delete Rule" button click:
     - Show confirmation modal: "Are you sure you want to delete this rule?"
     - Call `DELETE /api/admin/policies/{policy_id}/rules/{rule_id}`.
     - On success: Remove rule from list, show success toast.
7. **Refresh from Privy**: On "Refresh from Privy" button click:
   - Call `GET /api/admin/policies/?refresh=true` to refresh policies from Privy API.
   - Show loading state during refresh.
   - On success: Update policies list, show success toast.
