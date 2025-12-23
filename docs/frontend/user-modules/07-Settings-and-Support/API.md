# Settings & Support API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/account`, `/api/v1/subscription`, `/api/v1/support`

---

## 📋 Table of Contents

1. [Profile Endpoints](#profile-endpoints)
2. [Password Endpoints](#password-endpoints)
3. [Subscription Endpoints](#subscription-endpoints)
4. [Support Endpoints](#support-endpoints)
5. [Request/Response Schemas](#requestresponse-schemas)
6. [Error Handling](#error-handling)

---

## 🔌 Profile Endpoints

### 1. Get Profile

**Method**: `GET`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

*See Auth module API.md for complete specification.*

---

### 2. Update Profile

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/me`  
**Auth Required**: Yes (Bearer Token)

*See Auth module API.md for complete specification.*

---

## 🔌 Password Endpoints

### 3. Change Password

**Method**: `PUT`  
**Endpoint**: `/api/v1/account/change-password`  
**Auth Required**: Yes (Bearer Token)

*See Auth module API.md for complete specification.*

---

## 🔌 Subscription Endpoints

### 4. Get Subscriptions

**Method**: `GET`  
**Endpoint**: `/api/v1/subscription`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Response

##### Success Response (200 OK)
```typescript
interface SubscriptionListResponse {
  subscriptions: Subscription[];
  current_subscription?: Subscription;
}

interface Subscription {
  id: string;
  name: string;
  price_usd: number;
  features: string[];
  is_active: boolean;
}
```

**JSON Example**:
```json
{
  "subscriptions": [
    {
      "id": "basic",
      "name": "Basic",
      "price_usd": 0,
      "features": ["Basic features"],
      "is_active": true
    },
    {
      "id": "premium",
      "name": "Premium",
      "price_usd": 29.99,
      "features": ["All basic features", "Advanced DeFi", "Priority support"],
      "is_active": false
    }
  ],
  "current_subscription": {
    "id": "basic",
    "name": "Basic",
    "price_usd": 0,
    "features": ["Basic features"],
    "is_active": true
  }
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 5. Create Subscription

**Method**: `POST`  
**Endpoint**: `/api/v1/subscription/{subscription_id}/subscribe`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `subscription_id` | `number` | **Yes** | Subscription plan ID (integer) |

**Note**: No request body required. The subscription_id is in the path.

#### Response

##### Success Response (200 OK)
```typescript
interface SubscriptionResponse {
  subscription_id: number;
  status: string;                 // "active" | "pending" | "cancelled"
  stripe_checkout_url?: string;  // If payment required
  message?: string;
}
```

**JSON Example**:
```json
{
  "subscription_id": 1,
  "status": "pending",
  "stripe_checkout_url": "https://checkout.stripe.com/...",
  "message": "Subscription created successfully"
}
```

**Note**: If payment is required, redirect user to `stripe_checkout_url`.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `Exception` | Invalid subscription ID | Show error: "Invalid subscription plan" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `404` | `ValueError` | Subscription plan not found | Show error: "Subscription plan not found" |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

### 6. Cancel Subscription

**Method**: `POST`  
**Endpoint**: `/api/v1/subscription/{subscription_id}/cancel`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `subscription_id` | `number` | **Yes** | Subscription ID to cancel |

**Note**: No request body required.

#### Response

##### Success Response (200 OK)
```typescript
interface CancelSubscriptionResponse {
  subscription_id: number;
  status: string;
  message: string;
}
```

**JSON Example**:
```json
{
  "subscription_id": 1,
  "status": "cancelled",
  "message": "Subscription cancelled successfully"
}
```

**Note**: User retains access until end of billing period.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `404` | `ValueError` | Subscription not found | Show error: "Subscription not found" |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

### 7. Subscription Success Callback

**Method**: `GET`  
**Endpoint**: `/api/v1/subscription/success`  
**Auth Required**: No (Public - Stripe callback)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `session_id` | `string` | **Yes** | Stripe session ID |

#### Response

##### Success Response (200 OK)
```typescript
interface SubscriptionSuccessResponse {
  subscription_id: number;
  status: string;
  message: string;
}
```

**Note**: This is a callback endpoint called by Stripe after successful payment. Frontend should redirect here after Stripe checkout.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `Exception` | Invalid session ID | Show error: "Invalid payment session" |
| `404` | `ValueError` | Session not found | Show error: "Payment session not found" |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

### 8. Subscription Cancel Callback

**Method**: `GET`  
**Endpoint**: `/api/v1/subscription/cancel`  
**Auth Required**: No (Public - Stripe callback)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `session_id` | `string` | **Yes** | Stripe session ID |

#### Response

##### Success Response (200 OK)
```typescript
interface SubscriptionCancelResponse {
  message: string;
}
```

**Note**: This is a callback endpoint called by Stripe when payment is cancelled.

---

### 9. Initialize Subscriptions (Admin)

**Method**: `POST`  
**Endpoint**: `/api/v1/subscription/init`  
**Auth Required**: Yes (Bearer Token - Admin only)

#### Request

No request body required

#### Response

##### Success Response (200 OK)
```typescript
interface InitSubscriptionsResponse {
  subscriptions: Subscription[];
  message: string;
}
```

**Note**: This endpoint initializes default subscription plans (PRO and CORPORATE). Admin only.

---

## 🔌 Preferences Endpoints

### 8. Get Preferences

**Method**: `GET`  
**Endpoint**: `/api/v1/user/preferences`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: string;         // "conservative" | "moderate" | "aggressive"
  preferred_chains: string[];
  preferred_categories: string[];
  excluded_protocols: string[];
  favorite_protocols: string[];
  search_settings: {
    default_similarity_threshold: number;
    default_risk_filter: string;
    search_history_enabled: boolean;
  };
  notification_settings: {
    risk_alerts_enabled: boolean;
    push_enabled: boolean;
    min_severity: string;
  };
  default_currency: string;
  theme: string;
}
```

---

### 9. Update Risk Tolerance

**Method**: `PUT`  
**Endpoint**: `/api/v1/user/preferences/risk-tolerance`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface UpdateRiskToleranceRequest {
  risk_tolerance: string;         // Required: "conservative" | "moderate" | "aggressive"
}
```

#### Response

##### Success Response (200 OK)
Returns `UserPreferencesResponse` (updated preferences)

---

### 10. Update Chain Preferences

**Method**: `PUT`  
**Endpoint**: `/api/v1/user/preferences/chains`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface UpdateChainPreferencesRequest {
  preferred_chains: string[];      // Required: Array of chain names
}
```

#### Response

##### Success Response (200 OK)
Returns `UserPreferencesResponse` (updated preferences)

---

### 11. Save Search

**Method**: `POST`  
**Endpoint**: `/api/v1/user/preferences/search/saved`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SaveSearchRequest {
  name: string;                    // Required: Search preset name
  query: string;                   // Required: Search query
  filters: object;                  // Required: Search filters
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface SavedSearchResponse {
  id: string;                       // UUID
  name: string;
  query: string;
  filters: object;
  created_at: string;               // ISO 8601
}
```

---

### 12. Delete Saved Search

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/preferences/search/saved/{search_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (204 No Content)
No response body

---

### 13. Add Favorite Protocol

**Method**: `POST`  
**Endpoint**: `/api/v1/user/preferences/favorites/protocols/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```json
{
  "success": true
}
```

---

### 14. Remove Favorite Protocol

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/preferences/favorites/protocols/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (204 No Content)
No response body

---

## 🔌 Alert Endpoints

### 15. Get Risk Alerts

**Method**: `GET`  
**Endpoint**: `/api/v1/user/alerts/risk`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `unacknowledged_only` | `boolean` | No | Only unacknowledged alerts | `false` |
| `severity` | `string` | No | Filter by severity | All severities |
| `limit` | `number` | No | Max results | `50` |

**Valid Severity Values**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

#### Response

##### Success Response (200 OK)
```typescript
interface RiskAlertListResponse {
  alerts: RiskAlert[];
  total: number;
  unacknowledged: number;
}

interface RiskAlert {
  id: string;                      // UUID
  type: string;                    // "risk" | "anomaly" | "protocol_update"
  severity: string;                // "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  title: string;
  message: string;
  protocol_id?: string;
  acknowledged: boolean;
  created_at: string;              // ISO 8601
}
```

---

### 16. Acknowledge Alert

**Method**: `PUT`  
**Endpoint**: `/api/v1/user/alerts/risk/{alert_id}/acknowledge`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface AcknowledgeAlertRequest {
  acted_upon?: boolean;            // Optional: Mark as acted upon
}
```

#### Response

##### Success Response (200 OK)
Returns `RiskAlertResponse` (updated alert)

---

### 17. Dismiss Alert

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/alerts/risk/{alert_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (204 No Content)
No response body

---

### 18. Get Alert Subscription

**Method**: `GET`  
**Endpoint**: `/api/v1/user/alerts/subscription`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface AlertSubscriptionResponse {
  risk_alerts_enabled: boolean;
  anomaly_alerts_enabled: boolean;
  protocol_update_alerts_enabled: boolean;
  price_alerts_enabled: boolean;
  min_severity: string;
  subscribed_protocols: string[];
  excluded_protocols: string[];
  push_notifications: boolean;
  email_notifications: boolean;
  websocket_notifications: boolean;
  max_alerts_per_hour: number;
}
```

---

### 19. Update Alert Subscription

**Method**: `PUT`  
**Endpoint**: `/api/v1/user/alerts/subscription`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface UpdateSubscriptionRequest {
  risk_alerts_enabled?: boolean;
  anomaly_alerts_enabled?: boolean;
  protocol_update_alerts_enabled?: boolean;
  price_alerts_enabled?: boolean;
  min_severity?: string;
  push_notifications?: boolean;
  email_notifications?: boolean;
  websocket_notifications?: boolean;
  max_alerts_per_hour?: number;
}
```

#### Response

##### Success Response (200 OK)
Returns `AlertSubscriptionResponse` (updated subscription)

---

### 20. Subscribe to Protocol Alerts

**Method**: `POST`  
**Endpoint**: `/api/v1/user/alerts/subscription/protocols/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Subscribed to protocol {protocol_id}"
}
```

---

### 21. Unsubscribe from Protocol Alerts

**Method**: `DELETE`  
**Endpoint**: `/api/v1/user/alerts/subscription/protocols/{protocol_id}`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (204 No Content)
No response body

---

## 🔌 Payment Endpoints

### 22. Get User Payments

**Method**: `GET`  
**Endpoint**: `/api/v1/payments/user`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `page` | `number` | No | Page number | `1` |
| `per_page` | `number` | No | Items per page | `10` |

#### Response

##### Success Response (200 OK)
```typescript
interface UserPaymentsResponse {
  items: Payment[];
  page: number;
  per_page: number;
}

interface Payment {
  id: number;
  amount: number;
  currency: string;
  status: string;                  // "pending" | "completed" | "failed"
  subscription_id?: number;
  created_at: string;               // ISO 8601
}
```

---

### 23. Create Payment Transaction

**Method**: `POST`  
**Endpoint**: `/api/v1/payments/transaction`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface CreatePaymentTransactionRequest {
  amount: number;                   // Required: Payment amount
  currency: string;                 // Required: Currency code (e.g., "USD")
  description: string;              // Required: Payment description
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "status": "success",
  "payment": {
    "id": 123,
    "amount": 29.99,
    "currency": "USD",
    "description": "Monthly subscription",
    "status": "pending"
  }
}
```

---

## 🔌 Support Endpoints

> **⚠️ Note**: Support ticket endpoints are **PLANNED** but not yet implemented in the backend. The following documentation is provided for future implementation.

### 24. Create Support Ticket

**Method**: `POST`  
**Endpoint**: `/api/v1/support/tickets`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **PLANNED** (Not yet implemented)

#### Request

##### Request Body
```typescript
interface CreateTicketRequest {
  subject: string;                // Required: Max 200 chars
  message: string;                 // Required: Max 5000 chars
  category?: string;              // Optional: "technical" | "billing" | "general"
  priority?: string;              // Optional: "low" | "medium" | "high"
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `subject` | `string` | **Yes** | Ticket subject | Max 200 chars |
| `message` | `string` | **Yes** | Ticket message | Max 5000 chars |
| `category` | `string` | No | Ticket category | "technical", "billing", "general" |
| `priority` | `string` | No | Ticket priority | "low", "medium", "high" |

**JSON Example**:
```json
{
  "subject": "Unable to connect wallet",
  "message": "I'm having trouble connecting my MetaMask wallet...",
  "category": "technical",
  "priority": "high"
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface TicketResponse {
  ticket_id: string;
  subject: string;
  status: string;                 // "open" | "in_progress" | "resolved" | "closed"
  created_at: string;             // ISO 8601
  updated_at: string;             // ISO 8601
}
```

**JSON Example**:
```json
{
  "ticket_id": "ticket-123",
  "subject": "Unable to connect wallet",
  "status": "open",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValidationError` | Invalid request data | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `ServiceError` | Service unavailable | Show error + Retry |

---

### 25. Get Support Tickets

**Method**: `GET`  
**Endpoint**: `/api/v1/support/tickets`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **PLANNED** (Not yet implemented)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `status` | `string` | No | Filter by status | All statuses |
| `limit` | `number` | No | Max results | `20` |
| `offset` | `number` | No | Pagination offset | `0` |

#### Response

##### Success Response (200 OK)
```typescript
interface TicketListResponse {
  tickets: TicketResponse[];
  total: number;
}
```

---

### 26. Get Support Ticket

**Method**: `GET`  
**Endpoint**: `/api/v1/support/tickets/{ticket_id}`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **PLANNED** (Not yet implemented)

#### Response

##### Success Response (200 OK)
```typescript
interface TicketDetailResponse extends TicketResponse {
  message: string;
  replies: TicketReply[];
}

interface TicketReply {
  id: string;
  message: string;
  from_support: boolean;
  created_at: string;             // ISO 8601
}
```

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Not Found Errors (404)**
   - Ticket or subscription not found
   - **Action**: Show error message

4. **Conflict Errors (409)**
   - Already subscribed
   - **Action**: Show error message with current subscription info

5. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/account/me.py`
- **Backend Controller**: `src/app/presentation/http/controllers/subscription/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/support/` (if exists)
- **Domain Entities**: `src/app/domain/user/entities/user.py`
- **Frontend Implementation**: `07-Settings-and-Support/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
