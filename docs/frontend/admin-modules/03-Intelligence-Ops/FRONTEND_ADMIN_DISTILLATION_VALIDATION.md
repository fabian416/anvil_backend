# Admin Module: Distillation Validation

> **Technical Specification**: `FRONTEND_ADMIN_DISTILLATION_VALIDATION`
> **Backend Controller**: `admin/distillation_router.py` (validation endpoints)
> **Base URL**: `/api/admin/distillation/validation`

## 📖 Overview
The **Distillation Validation** submodule enables administrators to review, approve, and manage validation responses for distillation. This module provides a workflow for validating static responses and ensuring quality before they are used in production.

### Key Capabilities
1. **Validation Response Review**: View validation responses awaiting approval.
2. **Response Approval**: Approve or reject validation responses.
3. **Validation Analytics**: View analytics on validation responses and approval rates.

---

## 🔌 API Endpoints

### Validation Responses

#### 1. List Validation Responses
**GET** `/api/admin/distillation/validation/responses`
List validation responses for review.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `status` | `str` | No | Filter by status (pending, approved, rejected). |
| `intent` | `str` | No | Filter by intent. |
| `limit` | `int` | No | Limit results (default 50). |
| `offset` | `int` | No | Pagination offset (default 0). |

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "intent": "price_query",
      "original_query": "What is the price of ETH?",
      "proposed_response": "The current price of ETH is $2,500",
      "confidence": 0.95,
      "status": "pending",
      "created_at": "2023-10-01T10:00:00Z",
      "reviewed_by": null,
      "reviewed_at": null
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

#### 2. Get Validation Response
**GET** `/api/admin/distillation/validation/responses/{response_id}`
Get detailed information about a specific validation response.

**Response**:
```json
{
  "id": "uuid",
  "intent": "price_query",
  "original_query": "What is the price of ETH?",
  "proposed_response": "The current price of ETH is $2,500",
  "confidence": 0.95,
  "status": "pending",
  "metadata": {
    "data_source": "coingecko",
    "template_variables": {"token": "ETH", "price": "2500"}
  },
  "created_at": "2023-10-01T10:00:00Z",
  "reviewed_by": null,
  "reviewed_at": null,
  "rejection_reason": null
}
```

#### 3. Approve Validation Response
**PATCH** `/api/admin/distillation/validation/responses/{response_id}/approve`
Approve a validation response.

**Request Body**:
```json
{
  "notes": "Response looks good, approved for production"
}
```

**Response**: `200 OK`

#### 4. Reject Validation Response
**PATCH** `/api/admin/distillation/validation/responses/{response_id}/reject`
Reject a validation response.

**Request Body**:
```json
{
  "reason": "Response is inaccurate",
  "notes": "Price data is outdated"
}
```

**Response**: `200 OK`

### Validation Analytics

#### 5. Get Validation Analytics
**GET** `/api/admin/distillation/validation/analytics`
Get analytics on validation responses.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `period` | `str` | No | Time period (24h, 7d, 30d, default 7d). |
| `intent` | `str` | No | Filter by intent. |

**Response**:
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
      "date": "2023-10-01",
      "total": 20,
      "approved": 18,
      "rejected": 2
    }
  ]
}
```

---

## 🎨 UI/UX Guidelines

### Validation Response List
- **Table View**: Display validation responses in a table with:
  - Intent badge
  - Original query (truncated)
  - Proposed response (truncated)
  - Confidence score (with color coding: green >0.9, yellow 0.7-0.9, red <0.7)
  - Status badge (pending, approved, rejected)
  - Created date
  - Actions (Approve/Reject buttons)
- **Filters**: Filter by status, intent, and date range.
- **Sorting**: Sort by confidence, date, or status.
- **Pagination**: Paginate results for large datasets.

### Validation Response Detail View
- **Header**: Display response ID and status.
- **Sections**:
  - **Original Query**: Full original user query.
  - **Proposed Response**: Full proposed response with formatting.
  - **Confidence Score**: Visual indicator (progress bar or gauge).
  - **Metadata**: Data source, template variables, and other metadata.
  - **Review History**: Show review status, reviewer, and review date.
- **Actions**:
  - **Approve Button**: Green button with confirmation modal.
  - **Reject Button**: Red button with reason input field.
  - **Notes Field**: Optional notes for approval/rejection.

### Validation Analytics Dashboard
- **Summary Cards**: Display key metrics:
  - Total responses
  - Pending count
  - Approval rate
  - Average confidence
- **Charts**:
  - Approval/rejection trend over time
  - Distribution by intent
  - Confidence score distribution
- **Filters**: Filter by period and intent.

### Approval/Rejection Workflow
- **Confirmation Modal**: Require confirmation before approving/rejecting.
- **Reason Input**: Require reason for rejection (optional for approval).
- **Notes Field**: Optional notes field for additional context.
- **Success Feedback**: Show success message after approval/rejection.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Audit Trail**: Log all approval/rejection actions with reviewer information.
- **Data Privacy**: Ensure validation responses don't expose sensitive user data.

---

## 📝 Notes

- This module may be expanded in the future to include:
  - Bulk approval/rejection
  - Automated validation rules
  - Validation response templates
  - Integration with static response management
