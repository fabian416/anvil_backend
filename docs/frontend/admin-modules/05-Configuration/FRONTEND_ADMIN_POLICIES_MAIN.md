# Admin Module: Policy Management

> **Technical Specification**: `FRONTEND_ADMIN_POLICIES_MAIN`
> **Backend Controllers**: `admin/policies/list_policies.py`, `admin/policies/get_policy.py`, `admin/policies/create_policy.py`, `admin/policies/update_policy.py`, `admin/policies/policy_rules.py`
> **Base URL**: `/api/admin/policies`

## 📖 Overview
The **Policy Management** submodule enables administrators to manage Privy policies for wallet security and access control. Policies define rules for wallet operations, transaction limits, and authorization requirements.

### Key Capabilities
1. **Policy Listing**: List and search Privy policies.
2. **Policy Details**: View detailed policy information including rules.
3. **Policy Creation**: Create new Privy policies.
4. **Policy Updates**: Update existing policies.
5. **Policy Rules Management**: Create, update, and delete individual policy rules.

---

## 🔌 API Endpoints

### Policies

#### 1. List Policies
**GET** `/api/admin/policies/`
List Privy policies with optional filtering and pagination.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `cursor` | `str` | No | Pagination cursor. |
| `limit` | `int` | No | Number of results (1-1000, default: varies). |
| `chain_type` | `str` | No | Filter by chain type (e.g., "ethereum"). |
| `include_raw` | `bool` | No | Include raw Privy response (default: false). |
| `refresh` | `bool` | No | Refresh from Privy before returning (default: false). |
| `meta_key` | `str` | No | Filter by local metadata key. |
| `meta_value` | `str` | No | Filter by local metadata key value. |

**Response (`ListPoliciesResponse`)**:
```json
{
  "policies": [
    {
      "id": "policy-abc123",
      "name": "Standard Wallet Policy",
      "version": "1.0",
      "chain_type": "ethereum",
      "owner_id": "user-uuid"
    }
  ],
  "next_cursor": "cursor-string",
  "total_count": 25,
  "raw": null
}
```

#### 2. Get Policy
**GET** `/api/admin/policies/{policy_id}`
Retrieve detailed information about a specific policy.

**Response (`GetPolicyResponse`)**:
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
      "max_amount": "1000",
      "currency": "USD"
    }
  ],
  "owner_id": "user-uuid"
}
```

#### 3. Create Policy
**POST** `/api/admin/policies/`
Create a new Privy policy.

**Request Body (`CreatePolicyRequest`)**:
```json
{
  "version": "1.0",
  "name": "Custom Wallet Policy",
  "chain_type": "ethereum",
  "rules": [
    {
      "type": "transaction_limit",
      "max_amount": "5000",
      "currency": "USD"
    }
  ],
  "metadata": {
    "description": "Custom policy for high-value transactions"
  },
  "owner": {
    "user_id": "user-uuid"
  },
  "authorization_signature": "signature-string"
}
```

**Response (`CreatePolicyResponse`)**:
```json
{
  "id": "policy-xyz789",
  "name": "Custom Wallet Policy",
  "version": "1.0",
  "chain_type": "ethereum",
  "rules": [
    {
      "type": "transaction_limit",
      "max_amount": "5000",
      "currency": "USD"
    }
  ],
  "owner_id": "user-uuid"
}
```

#### 4. Update Policy
**PATCH** `/api/admin/policies/{policy_id}`
Update an existing Privy policy.

**Request Body (`UpdatePolicyRequest`)**:
```json
{
  "name": "Updated Policy Name",
  "rules": [
    {
      "type": "transaction_limit",
      "max_amount": "10000",
      "currency": "USD"
    }
  ],
  "authorization_signature": "signature-string"
}
```

**Response (`UpdatePolicyResponse`)**:
```json
{
  "id": "policy-abc123",
  "name": "Updated Policy Name",
  "version": "1.0",
  "chain_type": "ethereum",
  "rules": [
    {
      "type": "transaction_limit",
      "max_amount": "10000",
      "currency": "USD"
    }
  ],
  "owner_id": "user-uuid"
}
```

### Policy Rules

#### 5. Create Policy Rule
**POST** `/api/admin/policies/{policy_id}/rules`
Create a new rule for a policy.

**Request Body (`PolicyRuleRequestBody`)**:
```json
{
  "rule": {
    "type": "transaction_limit",
    "max_amount": "2000",
    "currency": "USD"
  },
  "authorization_signature": "signature-string"
}
```

**Response (`PolicyRuleResponse`)**:
```json
{
  "result": {
    "rule_id": "rule-2",
    "type": "transaction_limit",
    "max_amount": "2000",
    "currency": "USD"
  }
}
```

#### 6. Update Policy Rule
**PATCH** `/api/admin/policies/{policy_id}/rules/{rule_id}`
Update an existing policy rule.

**Request Body (`PolicyRuleRequestBody`)**:
```json
{
  "rule": {
    "type": "transaction_limit",
    "max_amount": "3000",
    "currency": "USD"
  },
  "authorization_signature": "signature-string"
}
```

**Response (`PolicyRuleResponse`)**:
```json
{
  "result": {
    "rule_id": "rule-2",
    "type": "transaction_limit",
    "max_amount": "3000",
    "currency": "USD"
  }
}
```

#### 7. Delete Policy Rule
**DELETE** `/api/admin/policies/{policy_id}/rules/{rule_id}`
Delete a policy rule.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `authorization_signature` | `str` | No | Authorization signature for owner-protected policies. |

**Response (`PolicyRuleResponse`)**:
```json
{
  "result": {
    "rule_id": "rule-2",
    "deleted": true
  }
}
```

---

## 🎨 UI/UX Guidelines

### Policy List View
- **Table Display**: Table showing policies with:
  - Policy ID (truncated with tooltip for full ID)
  - Policy name
  - Version badge
  - Chain type badge
  - Owner ID (if available)
  - Actions (View, Edit, Delete)
- **Filters**:
  - Chain type dropdown
  - Metadata key/value filters
  - Search by name or ID
- **Pagination**: Cursor-based pagination with next/previous buttons.
- **Refresh Button**: Manual refresh button to sync with Privy.
- **Create Button**: Prominent "Create Policy" button.

### Policy Detail View
- **Header**: Policy name, version, and chain type.
- **Sections**:
  - **Basic Information**: ID, name, version, chain type, owner.
  - **Rules Section**: List of policy rules with:
    - Rule ID
    - Rule type
    - Rule configuration (formatted JSON or structured display)
    - Actions (Edit, Delete)
  - **Metadata**: Display metadata if available.
- **Actions**:
  - Edit Policy button
  - Add Rule button
  - Delete Policy button (with confirmation)

### Create/Edit Policy Form
- **Basic Information**:
  - Policy name input (required)
  - Version input (default: "1.0")
  - Chain type selector (required)
  - Owner selector (optional)
- **Rules Section**:
  - List of rules with add/edit/remove buttons
  - Rule editor (JSON editor or structured form)
- **Metadata Section**:
  - Key-value pairs for metadata
- **Authorization**:
  - Authorization signature input (if required)
- **Save Button**: Save button with validation.
- **Cancel Button**: Cancel button to discard changes.

### Policy Rules Management
- **Rules List**: Display rules in a table or list:
  - Rule ID
  - Rule type badge
  - Rule configuration preview
  - Actions (Edit, Delete)
- **Add Rule Form**: Modal or inline form to add new rule:
  - Rule type selector
  - Rule configuration editor (JSON or structured form)
  - Authorization signature (if required)
- **Edit Rule Form**: Similar to add form, pre-populated with existing rule data.
- **Delete Confirmation**: Require confirmation before deleting rules.

### Error Handling
- **404 Not Found**: Display "Policy not found" message.
- **502 Bad Gateway**: Show "Unable to connect to Privy" error with retry option.
- **503 Service Unavailable**: Display service unavailable message.
- **Validation Errors**: Display field-level validation errors.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Owner Protection**: Owner-protected policies require authorization signatures.
- **Policy Rules**: Policy rules can affect wallet security; require careful review.
- **Audit Trail**: Log all policy creation, updates, and rule changes for audit.

---

## 📝 Notes

- Policies are managed through Privy API; local database stores metadata for advanced search.
- Policy rules follow Privy's policy engine format.
- Owner-protected policies require authorization signatures for modifications.
- Chain type determines which blockchain the policy applies to (e.g., "ethereum", "polygon").
