# Settings & Support API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/account`, `/api/v1/subscription`, `/api/v1/support`

---

## 📋 Table of Contents

1. [Profile Endpoints](#profile-endpoints)
2. [Password Endpoints](#password-endpoints)
3. [Subscription Endpoints](#subscription-endpoints)
4. [Preferences Endpoints](#preferences-endpoints)
5. [Alert Endpoints](#alert-endpoints)
6. [Payment Endpoints](#payment-endpoints)
7. [User Projects Endpoints](#user-projects-endpoints)
8. [Support Endpoints](#support-endpoints)
9. [WebSocket Connections](#websocket-connections)
10. [Request/Response Schemas](#requestresponse-schemas)
11. [Error Handling](#error-handling)

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

## 🔌 User Projects Endpoints

> **Project Selection & Management**  
> **Purpose**: Allow users to view, select, and join projects (workspaces/environments)

### 27. Get User Projects

**Method**: `GET`  
**Endpoint**: `/api/v1/user/projects`  
**Auth Required**: Yes (Bearer Token)

#### Request

No request body or query parameters required.

#### Response

##### Success Response (200 OK)
```typescript
interface UserProjectsResponse {
  assigned_projects: ProjectSummary[];
  active_project_id: string | null;  // UUID of currently active project
}

interface ProjectSummary {
  id: string;                         // UUID
  slug: string;                       // URL-friendly identifier
  name: string;                       // Display name
  description: string;                // Project description
  icon: string | null;                // Icon URL or emoji
  color: string | null;               // Theme color (hex)
  welcome_message: string | null;     // Welcome message for new users
  is_featured: boolean;               // Featured project flag
}
```

**JSON Example**:
```json
{
  "assigned_projects": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "slug": "defi-analytics",
      "name": "DeFi Analytics",
      "description": "Advanced DeFi analytics and insights",
      "icon": "📊",
      "color": "#3B82F6",
      "welcome_message": "Welcome to DeFi Analytics!",
      "is_featured": true
    }
  ],
  "active_project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 28. List Available Projects

**Method**: `GET`  
**Endpoint**: `/api/v1/user/projects/available`  
**Auth Required**: Yes (Bearer Token)

#### Request

No request body or query parameters required.

#### Response

##### Success Response (200 OK)
```typescript
interface AvailableProjectsResponse {
  projects: ProjectSummary[];
}
```

**JSON Example**:
```json
{
  "projects": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "slug": "defi-analytics",
      "name": "DeFi Analytics",
      "description": "Advanced DeFi analytics and insights",
      "icon": "📊",
      "color": "#3B82F6",
      "welcome_message": "Welcome to DeFi Analytics!",
      "is_featured": true
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "slug": "nft-portfolio",
      "name": "NFT Portfolio",
      "description": "Manage your NFT collection",
      "icon": "🖼️",
      "color": "#8B5CF6",
      "welcome_message": null,
      "is_featured": false
    }
  ]
}
```

**Note**: Returns only publicly available projects that users can join.

---

### 29. Select (Activate) Project

**Method**: `POST`  
**Endpoint**: `/api/v1/user/projects/{project_id}/select`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project UUID to activate |

#### Response

##### Success Response (204 No Content)
No response body. Project is set as active for the user.

**Behavior**:
- If user is not assigned to the project but it's public, user is auto-assigned
- If project is private and user is not assigned, returns 403 Forbidden
- Sets the project as the user's active project

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Project not found"
}
```

**400 Bad Request**:
```json
{
  "detail": "Project is not active"
}
```

**403 Forbidden**:
```json
{
  "detail": "User is not assigned to this project"
}
```

---

### 30. Join Public Project

**Method**: `POST`  
**Endpoint**: `/api/v1/user/projects/{project_id}/join`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_id` | `UUID` | **Yes** | Project UUID to join |

#### Response

##### Success Response (204 No Content)
No response body. User is assigned to the project and it's set as active.

**Behavior**:
- Only works for public projects
- Creates self-assignment for the user
- Sets the project as active
- Respects `max_users` limit if set

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Project not found"
}
```

**400 Bad Request**:
```json
{
  "detail": "Project is not active"
}
```

or

```json
{
  "detail": "User is already assigned to this project"
}
```

or

```json
{
  "detail": "Project has reached maximum user capacity"
}
```

**403 Forbidden**:
```json
{
  "detail": "Project is not publicly available"
}
```

---

### 31. Get Project by Slug

**Method**: `GET`  
**Endpoint**: `/api/v1/user/projects/{project_slug}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `project_slug` | `string` | **Yes** | Project slug (URL-friendly identifier) |

#### Response

##### Success Response (200 OK)
```typescript
interface ProjectSummaryResponse {
  id: string;                         // UUID
  slug: string;                       // URL-friendly identifier
  name: string;                       // Display name
  description: string;                // Project description
  icon: string | null;                // Icon URL or emoji
  color: string | null;               // Theme color (hex)
  welcome_message: string | null;     // Welcome message for new users
  is_featured: boolean;               // Featured project flag
}
```

**JSON Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "defi-analytics",
  "name": "DeFi Analytics",
  "description": "Advanced DeFi analytics and insights",
  "icon": "📊",
  "color": "#3B82F6",
  "welcome_message": "Welcome to DeFi Analytics!",
  "is_featured": true
}
```

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Project not found"
}
```

---

## 🔌 Support Endpoints

> **⚠️ Note**: Support ticket endpoints are **PLANNED** but not yet implemented in the backend. The following documentation is provided for future implementation.

### 32. Create Support Ticket

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

### 33. Get Support Tickets

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

### 34. Get Support Ticket

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

## 🔌 WebSocket Connections

### Settings & Support WebSocket

**Status**: ⚠️ **Not Applicable**

The Settings & Support module does not use WebSocket connections. All communication is via REST API:
- Profile management (GET, PUT)
- Password changes (PUT)
- Subscription management (GET, POST, PUT)
- Preferences management (GET, PUT, POST, DELETE)
- Alert management (GET, POST, PUT, DELETE)
- Payment transactions (GET, POST)
- Support tickets (POST, GET) - Planned

**Note**: Real-time notifications for alerts and subscription updates can be received via the Dashboard Analytics WebSocket (`/api/v1/analytics/ws/{user_id}`) if subscribed to alerts.

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Stripe Subscription Integration** | Custom billing | Third-party vs. Control | Stripe handles compliance, but adds external dependency |
| **Preference Persistence** | Session-only | Persistence vs. Privacy | Persistent preferences improve UX, but store user data |
| **Alert Subscription System** | All-or-nothing | Granularity vs. Complexity | Subscription system allows fine-grained control, but adds management overhead |
| **Project Selection** | Single workspace | Flexibility vs. Complexity | Multiple projects enable diverse use cases, but add context switching |
| **Self-Service Project Joining** | Admin-only assignment | User autonomy vs. Control | Self-service reduces admin burden, but may lead to project sprawl |

### Risk Assessment

**Cognitive Limitations:**
- Stripe webhook failures may cause subscription state inconsistencies
- Preference changes may not propagate immediately to all services
- Alert subscriptions may overwhelm users with notifications
- Project switching may cause context loss

**Technical Debt:**
- Stripe integration requires webhook reliability
- Preference synchronization across services
- Alert delivery requires reliable notification infrastructure
- Project assignment logic must handle edge cases

**Validation Strategy:**
- ✅ Monitor Stripe webhook delivery success rates
- ✅ Track preference persistence and synchronization
- ✅ Monitor alert delivery rates and user engagement
- ✅ Track project selection and switching patterns
- ✅ Alert on subscription billing errors
- ✅ Monitor project capacity limits

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
