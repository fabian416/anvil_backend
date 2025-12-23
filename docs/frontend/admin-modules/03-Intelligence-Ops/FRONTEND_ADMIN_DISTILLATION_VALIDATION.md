# Module: Distillation Validation

**Route**: `/admin/intelligence-ops/distillation/validation`  
**Auth Required**: Yes (Admin Only)  
**Package**: `admin/intelligence-ops/distillation/validation`

## 1. Overview
Enables administrators to review, approve, and manage validation responses for distillation. Provides a workflow for validating static responses and ensuring quality before they are used in production. Includes analytics on validation responses and approval rates.

## 2. API Contract

### List Validation Responses
**Endpoint**: `GET /api/admin/distillation/validation/responses`  
**Query Params**:
- `status` (string, optional): Filter by status - `pending`, `approved`, `rejected` (Default: all).
- `intent` (string, optional): Filter by intent.
- `limit` (number, optional): Limit results (Default: 50, Max: 100).
- `offset` (number, optional): Pagination offset (Default: 0).

#### Response Body (`ValidationResponseList`)
| Field | Type | Description |
|---|---|---|
| `items` | `ValidationResponse[]` | Array of validation responses |
| `total` | `number` | Total number of responses |
| `limit` | `number` | Limit used |
| `offset` | `number` | Offset used |

**ValidationResponse Object**:
| Field | Type | Description |
|---|---|---|
| `id` | `string` | Validation response UUID |
| `intent` | `string` | Intent identifier |
| `original_query` | `string` | Original user query |
| `proposed_response` | `string` | Proposed static response |
| `confidence` | `number` | Confidence score (0-1) |
| `status` | `string` | Status: `pending`, `approved`, `rejected` |
| `metadata` | `{ [key: string]: any }` | Optional: Additional metadata |
| `created_at` | `string` | ISO 8601 creation timestamp |
| `reviewed_by` | `string \| null` | Reviewer user ID or null |
| `reviewed_at` | `string \| null` | ISO 8601 review timestamp or null |
| `rejection_reason` | `string \| null` | Rejection reason or null |

**JSON Example**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "intent": "price_query",
      "original_query": "What is the price of ETH?",
      "proposed_response": "The current price of ETH is $2,500",
      "confidence": 0.95,
      "status": "pending",
      "metadata": {
        "data_source": "coingecko",
        "template_variables": {"token": "ETH", "price": "2500"}
      },
      "created_at": "2024-01-15T10:00:00Z",
      "reviewed_by": null,
      "reviewed_at": null,
      "rejection_reason": null
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

### Get Validation Response
**Endpoint**: `GET /api/admin/distillation/validation/responses/{response_id}`  
**Path Params**:
- `response_id` (string, **required**): Validation response UUID.

#### Response Body (`ValidationResponse`)
Returns detailed validation response object (same structure as above).

### Approve Validation Response
**Endpoint**: `PATCH /api/admin/distillation/validation/responses/{response_id}/approve`  
**Path Params**:
- `response_id` (string, **required**): Validation response UUID.

#### Request Body (`ApproveValidationRequest`)
| Field | Type | Description |
|---|---|---|
| `notes` | `string` | Optional: Approval notes |

**JSON Example**:
```json
{
  "notes": "Response looks good, approved for production"
}
```

#### Response
`200 OK` - No response body

### Reject Validation Response
**Endpoint**: `PATCH /api/admin/distillation/validation/responses/{response_id}/reject`  
**Path Params**:
- `response_id` (string, **required**): Validation response UUID.

#### Request Body (`RejectValidationRequest`)
| Field | Type | Description |
|---|---|---|
| `reason` | `string` | Rejection reason (required) |
| `notes` | `string` | Optional: Additional notes |

**JSON Example**:
```json
{
  "reason": "Response is inaccurate",
  "notes": "Price data is outdated, needs refresh"
}
```

#### Response
`200 OK` - No response body

### Get Validation Analytics
**Endpoint**: `GET /api/admin/distillation/validation/analytics`  
**Query Params**:
- `period` (string, optional): Time period - `24h`, `7d`, `30d` (Default: `7d`).
- `intent` (string, optional): Filter by intent.

#### Response Body (`ValidationAnalyticsResponse`)
| Field | Type | Description |
|---|---|---|
| `period` | `string` | Time period used |
| `total_responses` | `number` | Total validation responses |
| `pending` | `number` | Pending responses count |
| `approved` | `number` | Approved responses count |
| `rejected` | `number` | Rejected responses count |
| `approval_rate` | `number` | Approval rate (0-1) |
| `average_confidence` | `number` | Average confidence score (0-1) |
| `by_intent` | `IntentAnalytics[]` | Analytics grouped by intent |
| `trends` | `ValidationTrend[]` | Daily validation trends |

**IntentAnalytics Object**:
| Field | Type | Description |
|---|---|---|
| `intent` | `string` | Intent identifier |
| `total` | `number` | Total responses for this intent |
| `approved` | `number` | Approved count |
| `rejected` | `number` | Rejected count |
| `pending` | `number` | Pending count |

**ValidationTrend Object**:
| Field | Type | Description |
|---|---|---|
| `date` | `string` | ISO 8601 date |
| `total` | `number` | Total responses on this date |
| `approved` | `number` | Approved count |
| `rejected` | `number` | Rejected count |

**JSON Example**:
```json
{
  "period": "7d",
  "total_responses": 150,
  "pending": 25,
  "approved": 110,
  "rejected": 15,
  "approval_rate": 0.88,
  "average_confidence": 0.92,
  "by_intent": [
    {
      "intent": "price_query",
      "total": 80,
      "approved": 70,
      "rejected": 5,
      "pending": 5
    }
  ],
  "trends": [
    {
      "date": "2024-01-15",
      "total": 20,
      "approved": 18,
      "rejected": 2
    }
  ]
}
```

### Error Codes
| Status | Error Code | Description | UI Behavior |
|---|---|---|---|
| `401` | `AuthenticationError` | Invalid or expired token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Validation response not found | Show error: "Validation response not found" |
| `400` | `DomainFieldError` | Invalid request data (missing reason for reject) | Show error: "Rejection reason is required" |
| `409` | `DomainConflictError` | Response already reviewed | Show error: "Response has already been reviewed" |
| `500` | `Exception` | Internal server error | Show error: "Failed to process validation" + Retry button |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry button |

## 3. Implementation Flow

1. **Mount**: Call `useValidationResponses({ status, intent, limit, offset })` hook which fetches `/api/admin/distillation/validation/responses`.
2. **Display**:
   - Validation queue table: Display `items` array with columns: Intent, Original Query, Proposed Response, Confidence, Status, Created Date, Actions.
   - Status badges: Color-code by status (Pending=Yellow, Approved=Green, Rejected=Red).
   - Confidence indicator: Display confidence score with color coding (High=Green >0.9, Medium=Yellow 0.7-0.9, Low=Red <0.7).
3. **Filter**: On status or intent filter change, update query params and refetch.
4. **Pagination**: Use `total`, `limit`, `offset` to display pagination controls.
5. **View Details**: On validation response click, call `GET /api/admin/distillation/validation/responses/{response_id}` to show detailed view in modal or navigate to detail page.
6. **Approve Response**: On "Approve" button click:
   - Open approval modal with optional notes field.
   - Call `PATCH /api/admin/distillation/validation/responses/{response_id}/approve` with optional notes.
   - On success: Update status to "approved", show success toast, invalidate query cache.
7. **Reject Response**: On "Reject" button click:
   - Open rejection modal with required reason field and optional notes.
   - Validate reason is provided.
   - Call `PATCH /api/admin/distillation/validation/responses/{response_id}/reject` with reason and notes.
   - On success: Update status to "rejected", show success toast, invalidate query cache.
8. **View Analytics**: Call `GET /api/admin/distillation/validation/analytics` with selected period to display:
   - Summary cards: Total, Pending, Approved, Rejected, Approval Rate.
   - Intent breakdown: Display `by_intent` in a table or chart.
   - Trends chart: Display `trends` as a line chart showing approval/rejection trends over time.
