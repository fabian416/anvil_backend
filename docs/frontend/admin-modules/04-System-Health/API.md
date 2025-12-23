# System Health API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URLs**: `/api/admin/metrics`, `/api/admin/stats`, `/api/v1/admin/retry`

---

## 📋 Table of Contents

1. [Metrics Endpoints](#metrics-endpoints)
2. [Stats Endpoints](#stats-endpoints)
3. [Retry System Endpoints](#retry-system-endpoints)
4. [Request/Response Schemas](#requestresponse-schemas)
5. [Error Handling](#error-handling)
6. [API Design Trade-off Analysis](#api-design-trade-off-analysis)

---

## 📊 Metrics Endpoints

### 1. Get Metrics Overview

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/overview`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

No query parameters

#### Response

##### Success Response (200 OK)
```typescript
interface AdminMetricsOverview {
  wallets: WalletOverviewMetrics;
  transactions: TransactionOverviewMetrics;
  users: UserOverviewMetrics;
  generated_at: string;                  // ISO 8601
}

interface WalletOverviewMetrics {
  total_wallets: number;
  active_wallets: number;
  privy_wallets: number;
  imported_wallets: number;
  external_wallets: number;
}

interface TransactionOverviewMetrics {
  total_transactions: number;
  pending_transactions: number;
  successful_transactions: number;
  failed_transactions: number;
}

interface UserOverviewMetrics {
  total_users: number;
  total_users_with_transactions: number;
  active_users_today: number;
  active_users_7d: number;
  active_users_30d: number;
}
```

**JSON Example**:
```json
{
  "wallets": {
    "total_wallets": 1500,
    "active_wallets": 1200,
    "privy_wallets": 800,
    "imported_wallets": 500,
    "external_wallets": 200
  },
  "transactions": {
    "total_transactions": 5000,
    "pending_transactions": 50,
    "successful_transactions": 4800,
    "failed_transactions": 150
  },
  "users": {
    "total_users": 1000,
    "total_users_with_transactions": 500,
    "active_users_today": 50,
    "active_users_7d": 200,
    "active_users_30d": 400
  },
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

### 2. Get Transaction Time Series

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/transactions/timeseries`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `from_date` | `datetime` | No | Start date | 30 days ago |
| `to_date` | `datetime` | No | End date | Now |
| `chain` | `string` | No | Filter by chain | All chains |
| `tx_type` | `string` | No | Filter by transaction type | All types |
| `group_by` | `string` | No | Grouping interval | `day` |

**Valid `group_by` Values**: `day`, `week`, `month`

**Valid `chain` Values**: `ethereum`, `polygon`, `base`, `arbitrum`, `optimism`

**Valid `tx_type` Values**: `SEND`, `SWAP`, `STAKE`, `UNSTAKE`, etc.

#### Response

##### Success Response (200 OK)
```typescript
interface TransactionTimeSeriesResponse {
  data: TimeSeriesDataPoint[];
  from_date: string;                     // ISO 8601
  to_date: string;                       // ISO 8601
  group_by: string;
  chain: string | null;
  tx_type: string | null;
  total_count: number;
}

interface TimeSeriesDataPoint {
  date: string;                          // ISO 8601
  value: number;
}
```

---

### 3. Get Wallet Time Series

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/wallets/timeseries`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `from_date` | `datetime` | No | Start date | 30 days ago |
| `to_date` | `datetime` | No | End date | Now |
| `group_by` | `string` | No | Grouping interval | `day` |

#### Response

##### Success Response (200 OK)
```typescript
interface WalletTimeSeriesResponse {
  data: TimeSeriesDataPoint[];
  from_date: string;                     // ISO 8601
  to_date: string;                       // ISO 8601
  group_by: string;
  total_count: number;
}
```

---

### 4. Get User Activity Time Series

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/users/activity`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `from_date` | `datetime` | No | Start date | 30 days ago |
| `to_date` | `datetime` | No | End date | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface UserActivityTimeSeriesResponse {
  data: TimeSeriesDataPoint[];
  from_date: string;                     // ISO 8601
  to_date: string;                       // ISO 8601
}
```

---

### 5. Get Wallet Distribution

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/wallets/distribution`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface WalletDistributionResponse {
  by_provider: DistributionItem[];
  total: number;
}

interface DistributionItem {
  name: string;
  count: number;
  percentage: number;                    // 0-100
}
```

**JSON Example**:
```json
{
  "by_provider": [
    {
      "name": "privy",
      "count": 800,
      "percentage": 53.3
    },
    {
      "name": "imported",
      "count": 500,
      "percentage": 33.3
    },
    {
      "name": "external",
      "count": 200,
      "percentage": 13.3
    }
  ],
  "total": 1500
}
```

---

### 6. Get Transaction Distribution

**Method**: `GET`  
**Endpoint**: `/api/admin/metrics/transactions/distribution`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface TransactionDistributionResponse {
  by_chain: DistributionItem[];
  by_status: DistributionItem[];
  by_type: DistributionItem[];
  total: number;
}
```

---

## 📈 Stats Endpoints

### 7. Get System Statistics

**Method**: `GET`  
**Endpoint**: `/api/admin/stats/`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface AdminStats {
  active_conversations: number;
  total_messages: number;
  active_agents: number;
  agent_usage: AgentUsage[];
}

interface AgentUsage {
  agent_type: string;
  count: number;
}
```

**JSON Example**:
```json
{
  "active_conversations": 10,
  "total_messages": 150,
  "active_agents": 5,
  "agent_usage": [
    {
      "agent_type": "trading",
      "count": 50
    },
    {
      "agent_type": "research",
      "count": 30
    }
  ]
}
```

---

## 🔄 Retry System Endpoints

### 8. List Services

**Method**: `GET`  
**Endpoint**: `/api/v1/admin/retry/services`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface ServiceListResponse {
  services: ServiceStatusResponse[];
}

interface ServiceStatusResponse {
  service_name: string;
  enabled: boolean;
  circuit_state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  success_count: number;
  last_error: string | null;
  last_error_at: string | null;          // ISO 8601
  override_reason: string | null;
  override_expires_at: string | null;    // ISO 8601
}
```

---

### 9. Get Service Status

**Method**: `GET`  
**Endpoint**: `/api/v1/admin/retry/services/{service_name}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `service_name` | `string` | **Yes** | Service name |

#### Response

##### Success Response (200 OK)
Returns `ServiceStatusResponse`

---

### 10. Disable Service

**Method**: `POST`  
**Endpoint**: `/api/v1/admin/retry/services/{service_name}/disable`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `service_name` | `string` | **Yes** | Service name |

##### Request Body
```typescript
interface DisableServiceRequest {
  reason: string;                        // Required: Reason for disabling
  duration_minutes?: number | null;      // Optional: Auto re-enable after duration (null = permanent)
}
```

**JSON Example**:
```json
{
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Service 'openai_api' disabled",
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

---

### 11. Enable Service

**Method**: `POST`  
**Endpoint**: `/api/v1/admin/retry/services/{service_name}/enable`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `service_name` | `string` | **Yes** | Service name |

##### Request Body
```typescript
interface EnableServiceRequest {
  reason: string;                        // Required: Reason for enabling
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Service 'openai_api' enabled",
  "reason": "Maintenance complete"
}
```

---

### 12. Get Circuit Breakers

**Method**: `GET`  
**Endpoint**: `/api/v1/admin/retry/circuit-breakers`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface CircuitBreakerStatusResponse {
  service_name: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  success_count: number;
  opened_at: string | null;              // ISO 8601
  config: {
    failure_threshold: number;
    success_threshold: number;
    timeout_seconds: number;
  };
}
```

Returns `CircuitBreakerStatusResponse[]`

---

### 13. Reset Circuit Breaker

**Method**: `POST`  
**Endpoint**: `/api/v1/admin/retry/circuit-breakers/{service_name}/reset`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `service_name` | `string` | **Yes** | Service name |

##### Request Body
```typescript
interface ResetCircuitBreakerRequest {
  reason: string;                        // Required: Reason for reset
}
```

#### Response

##### Success Response (200 OK)
```json
{
  "message": "Circuit breaker for 'openai_api' reset to CLOSED",
  "reason": "Issue resolved"
}
```

---

### 14. Get Service Metrics

**Method**: `GET`  
**Endpoint**: `/api/v1/admin/retry/metrics/{service_name}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `service_name` | `string` | **Yes** | Service name |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `days` | `number` | No | Number of days | `7` |

**Valid `days` Range**: 1-90

#### Response

##### Success Response (200 OK)
```typescript
interface ServiceMetricsResponse {
  service_name: string;
  days: number;
  metrics: ServiceMetricDay[];
  summary: {
    total_requests: number;
    avg_success_rate: number;            // 0-1
    avg_latency_ms: number;
    total_circuit_breaker_opens: number;
  };
}

interface ServiceMetricDay {
  date: string;                          // ISO 8601 date
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  retry_attempts: number;
  avg_latency_ms: number;
  circuit_breaker_opens: number;
  success_rate: number;                  // 0-1
}
```

---

## 📝 Request/Response Schemas

### Complete TypeScript Interfaces

See individual endpoint sections above for detailed schemas.

### Common Types

```typescript
// Time series data point
interface TimeSeriesDataPoint {
  date: string;                          // ISO 8601
  value: number;
}

// Distribution item
interface DistributionItem {
  name: string;
  count: number;
  percentage: number;                    // 0-100
}

// Error response format
interface ErrorResponse {
  detail: string;
}
```

---

## ⚠️ Error Handling

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Authorization Errors (403)**
   - Not admin user
   - **Action**: Show error: "Admin access required"

3. **Validation Errors (400)**
   - Invalid date range
   - Invalid service name
   - **Action**: Show inline field errors

4. **Not Found Errors (404)**
   - Service not found
   - **Action**: Show error: "Service not found"

5. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Handling Summary

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid parameters | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Service not found | Show error: "Service not found" |
| `500` | `Exception` | Internal server error | Show error: "Internal error" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service unavailable" + Retry |

---

## 🔐 Authentication

All endpoints require:
- **Bearer Token**: Admin JWT token in `Authorization` header
- **Admin Role**: User must have admin privileges

**Header Format**:
```http
Authorization: Bearer {jwt_token}
```

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Separate Metrics Endpoints** | Single Aggregated | Granularity vs. Performance | Separate endpoints allow focused queries, but increase request count |
| **Time Series Grouping** | Raw Data | Performance vs. Detail | Grouping reduces data size, but limits granularity |
| **Retry System Control** | Automatic Only | Control vs. Automation | Manual control allows intervention, but requires admin oversight |

### Risk Assessment

**Cognitive Limitations:**
- Multiple metrics endpoints may be overwhelming
- Retry system control requires understanding of circuit breakers
- Time series grouping may hide important details

**Technical Debt:**
- Time series queries may become slow with large datasets
- Retry system state management requires careful coordination
- Metrics aggregation may become resource-intensive

**Validation Strategy:**
- ✅ Monitor metrics query performance
- ✅ Track retry system operation success rates
- ✅ Alert on service failures
- ✅ Monitor circuit breaker state changes

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/admin/metrics/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/stats/router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/retry/router.py`
- **Response Schemas**: `src/app/presentation/http/schemas/admin/metrics.py`
- **Frontend Implementation**: `04-System-Health/IMPLEMENTATION.md`
- **UI/UX Design**: `04-System-Health/UI_UX.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
