# Module: LLM Budgets

**Route**: `/admin/intelligence-ops/budgets`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/budgets`

## 1. Overview
Protects the platform from runaway AI costs. Admins can define spending limits (Daily/Weekly/Monthly) with alert thresholds and configure hard or soft limits. Hard limits block all AI requests once exceeded, while soft limits only trigger alerts.

## 2. API Contract

### List Budgets
**Endpoint**: `GET /api/admin/llm/budgets`  
**Query Params**: None

#### Response Body (`BudgetResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `BudgetListData` | Budget list data |

**BudgetListData Object**:
| Field | Type | Description |
|---|---|---|
| `budgets` | `Budget[]` | Array of budget objects |

**Budget Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Budget UUID |
| `name` | `string` | Budget name |
| `budget_type` | `string` | Budget type: `daily`, `weekly`, `monthly` |
| `budget_amount_usd` | `number` | Budget amount in USD |
| `current_spend_usd` | `number` | Current spend in USD |
| `percentage_used` | `number` | Percentage used (0-100) |
| `warning_threshold_percent` | `number` | Warning threshold (0-100) |
| `critical_threshold_percent` | `number` | Critical threshold (0-100) |
| `is_hard_limit` | `boolean` | Whether this is a hard limit |
| `period_start` | `string` | ISO 8601 period start |
| `period_end` | `string` | ISO 8601 period end |

**JSON Example**:
```json
{
  "success": true,
  "data": {
    "budgets": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Global Daily Limit",
        "budget_type": "daily",
        "budget_amount_usd": 500.00,
        "current_spend_usd": 125.00,
        "percentage_used": 25.0,
        "warning_threshold_percent": 80,
        "critical_threshold_percent": 95,
        "is_hard_limit": true,
        "period_start": "2024-01-15T00:00:00Z",
        "period_end": "2024-01-16T00:00:00Z"
      }
    ]
  }
}
```

### Create Budget
**Endpoint**: `POST /api/admin/llm/budgets`  
**Query Params**: None

#### Request Body (`CreateBudgetRequest`)
| Field | Type | Description |
|---|---|---|
| `name` | `string` | Budget name (required) |
| `budget_type` | `string` | Budget type: `daily`, `weekly`, `monthly` (required) |
| `budget_amount_usd` | `number` | Budget amount in USD (required) |
| `warning_threshold_percent` | `number` | Warning threshold 0-100 (Default: 80) |
| `critical_threshold_percent` | `number` | Critical threshold 0-100 (Default: 95) |
| `is_hard_limit` | `boolean` | Whether this is a hard limit (Default: false) |
| `notify_emails` | `string[]` | Optional: Email addresses for alerts |
| `notify_slack_channel` | `string` | Optional: Slack channel for alerts |

**JSON Example**:
```json
{
  "name": "Research Team Monthly",
  "budget_type": "monthly",
  "budget_amount_usd": 2000.00,
  "warning_threshold_percent": 80,
  "critical_threshold_percent": 95,
  "is_hard_limit": false,
  "notify_emails": ["admin@anvil.com"],
  "notify_slack_channel": "#alerts-llm"
}
```

#### Response Body (`BudgetResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `BudgetCreateData` | Budget creation data |

**BudgetCreateData Object**:
| Field | Type | Description |
|---|---|---|
| `budget_id` | `string` | Created budget UUID |
| `name` | `string` | Budget name |
| `created` | `boolean` | Whether budget was created |

### Update Budget
**Endpoint**: `PUT /api/admin/llm/budgets/{budget_id}`  
**Path Params**:
- `budget_id` (string, **required**): Budget UUID.

#### Request Body (`UpdateBudgetRequest`)
| Field | Type | Description |
|---|---|---|
| `budget_amount_usd` | `number` | Optional: New budget amount |
| `warning_threshold_percent` | `number` | Optional: New warning threshold |
| `critical_threshold_percent` | `number` | Optional: New critical threshold |
| `is_hard_limit` | `boolean` | Optional: Whether this is a hard limit |

**JSON Example**:
```json
{
  "budget_amount_usd": 2500.00,
  "is_hard_limit": true
}
```

#### Response Body (`BudgetResponse`)
| Field | Type | Description |
|---|---|---|
| `success` | `boolean` | Whether request was successful |
| `data` | `BudgetUpdateData` | Budget update data |

**BudgetUpdateData Object**:
| Field | Type | Description |
|---|---|---|
| `budget_id` | `string` | Budget UUID |
| `updated` | `boolean` | Whether budget was updated |

### Delete Budget
**Endpoint**: `DELETE /api/admin/llm/budgets/{budget_id}`  
**Path Params**:
- `budget_id` (string, **required**): Budget UUID.

#### Response
`204 No Content` - No response body

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Budget not found | Show error: "Budget not found" |
| `400` | `DomainFieldError` | Invalid request data | Show error: "Invalid budget configuration" |
| `409` | `DomainConflictError` | Budget conflict | Show error: "Budget conflict" |
| `500` | `Exception` | Internal server error | Show error: "Failed to manage budget" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useBudgets()` hook which fetches `/api/admin/llm/budgets`.
2. **Display**:
   - Budget cards: Display `budgets` array with budget information.
   - Progress bar: Visualize `percentage_used` with color coding:
     - < `warning_threshold_percent`: Green
     - >= `warning_threshold_percent` and < `critical_threshold_percent`: Orange
     - >= `critical_threshold_percent`: Red
   - Hard limit indicator: Show badge if `is_hard_limit` is true.
   - Current spend: Display `current_spend_usd` and `budget_amount_usd`.
3. **Create Budget**: On "Create Budget" button click:
   - Open create budget modal/form.
   - Show hard limit warning if selected: "This will block all AI requests once the limit is reached."
   - On submit, call `POST /api/admin/llm/budgets` with request body.
   - On success: Add budget to list, show success toast, invalidate query cache.
4. **Update Budget**: On "Edit" button click:
   - Open edit modal with current values pre-populated.
   - On submit, call `PUT /api/admin/llm/budgets/{budget_id}` with request body.
   - On success: Update display, show success toast, invalidate query cache.
5. **Delete Budget**: On "Delete" button click:
   - Show confirmation modal: "Are you sure you want to delete this budget?"
   - On confirm, call `DELETE /api/admin/llm/budgets/{budget_id}`.
   - On success: Remove from list, show success toast, invalidate query cache.
