# Admin Module: Retry System

> **Technical Specification**: `FRONTEND_ADMIN_RETRY_MAIN`
> **Backend Controller**: `admin/retry/router.py`
> **Base URL**: `/api/v1/admin/retry`

## 📖 Overview
The **Retry System** submodule enables administrators to monitor and control the retry system for service reliability. It provides visibility into service status, circuit breakers, and retry metrics, allowing admins to manage service availability and troubleshoot issues.

### Key Capabilities
1. **Service Status Monitoring**: View status of all services in the retry system.
2. **Service Control**: Enable or disable services manually.
3. **Circuit Breaker Management**: View and reset circuit breakers.
4. **Retry Metrics**: View aggregated metrics for services over time.

---

## 🔌 API Endpoints

### Services

#### 1. List Services
**GET** `/api/v1/admin/retry/services`
Get comprehensive status of all services in the retry system.

**Response (`ServiceListResponse`)**:
```json
{
  "services": [
    {
      "service_name": "openai_api",
      "status": "enabled",
      "circuit_breaker_state": "closed",
      "retry_count": 3,
      "last_success": "2023-10-01T10:00:00Z",
      "last_failure": null,
      "consecutive_failures": 0
    }
  ]
}
```

#### 2. Get Service Status
**GET** `/api/v1/admin/retry/services/{service_name}`
Get detailed status for a specific service.

**Response (`ServiceStatusResponse`)**:
```json
{
  "service_name": "openai_api",
  "status": "enabled",
  "circuit_breaker_state": "closed",
  "retry_count": 3,
  "last_success": "2023-10-01T10:00:00Z",
  "last_failure": null,
  "consecutive_failures": 0,
  "failure_threshold": 5,
  "success_threshold": 2,
  "timeout_seconds": 30
}
```

#### 3. Disable Service
**POST** `/api/v1/admin/retry/services/{service_name}/disable`
Manually disable a service (stops all retry attempts).

**Request Body (`DisableServiceRequest`)**:
```json
{
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

**Response**:
```json
{
  "message": "Service 'openai_api' disabled",
  "reason": "Maintenance window",
  "duration_minutes": 60
}
```

#### 4. Enable Service
**POST** `/api/v1/admin/retry/services/{service_name}/enable`
Manually enable a previously disabled service.

**Request Body (`EnableServiceRequest`)**:
```json
{
  "reason": "Maintenance complete"
}
```

**Response**:
```json
{
  "message": "Service 'openai_api' enabled",
  "reason": "Maintenance complete"
}
```

### Circuit Breakers

#### 5. Get Circuit Breakers
**GET** `/api/v1/admin/retry/circuit-breakers`
Get circuit breaker status for all services.

**Response (`List[CircuitBreakerStatusResponse]`)**:
```json
[
  {
    "service_name": "openai_api",
    "state": "closed",
    "failure_count": 0,
    "success_count": 100,
    "last_state_change": "2023-10-01T09:00:00Z",
    "next_attempt_at": null
  }
]
```

**Circuit Breaker States**:
- `closed`: Normal operation, requests allowed.
- `open`: Circuit is open, requests blocked.
- `half_open`: Testing state, limited requests allowed.

#### 6. Reset Circuit Breaker
**POST** `/api/v1/admin/retry/circuit-breakers/{service_name}/reset`
Manually reset a circuit breaker to CLOSED state.

**Request Body (`ResetCircuitBreakerRequest`)**:
```json
{
  "reason": "Issue resolved"
}
```

**Response**:
```json
{
  "message": "Circuit breaker for 'openai_api' reset to CLOSED",
  "reason": "Issue resolved"
}
```

### Metrics

#### 7. Get Service Metrics
**GET** `/api/v1/admin/retry/metrics/{service_name}`
Get aggregated metrics for a service over time.

| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `days` | `int` | No | Number of days to retrieve (1-90, default: 7). |

**Response (`ServiceMetricsResponse`)**:
```json
{
  "service_name": "openai_api",
  "period_days": 7,
  "total_requests": 15000,
  "successful_requests": 14850,
  "failed_requests": 150,
  "success_rate": 0.99,
  "avg_retry_count": 1.2,
  "circuit_breaker_opens": 2,
  "circuit_breaker_resets": 2,
  "daily_breakdown": [
    {
      "date": "2023-10-01",
      "requests": 2000,
      "successful": 1980,
      "failed": 20,
      "avg_retry_count": 1.1
    }
  ]
}
```

---

## 🎨 UI/UX Guidelines

### Service List View
- **Table Display**: Table showing all services with:
  - Service name
  - Status badge (enabled/disabled)
  - Circuit breaker state (closed/open/half-open) with color coding
  - Retry count
  - Last success/failure timestamps
  - Consecutive failures count
- **Status Indicators**:
  - **Enabled**: Green badge
  - **Disabled**: Grey badge
  - **Circuit Closed**: Green indicator
  - **Circuit Open**: Red indicator
  - **Circuit Half-Open**: Yellow indicator
- **Actions**: 
  - Enable/Disable buttons (contextual based on current status)
  - View details link
  - Reset circuit breaker button (if open)

### Service Detail View
- **Header**: Service name and current status.
- **Status Card**: Large status display with:
  - Current status (enabled/disabled)
  - Circuit breaker state
  - Last success/failure timestamps
- **Configuration Section**: Display retry configuration:
  - Retry count
  - Failure threshold
  - Success threshold
  - Timeout seconds
- **Metrics Section**: Show recent metrics and trends.
- **Actions**: 
  - Enable/Disable service button
  - Reset circuit breaker button
  - View metrics link

### Circuit Breaker Management
- **Circuit Breaker List**: Table showing all circuit breakers:
  - Service name
  - State (with color coding)
  - Failure count
  - Success count
  - Last state change timestamp
  - Next attempt timestamp (if half-open)
  - Reset button
- **State Indicators**:
  - **Closed**: Green badge (normal operation)
  - **Open**: Red badge (blocking requests)
  - **Half-Open**: Yellow badge (testing state)
- **Reset Confirmation**: Require confirmation before resetting circuit breaker.

### Service Control
- **Disable Service Form**:
  - Reason textarea (required)
  - Duration input (optional, in minutes)
  - Confirmation checkbox
- **Enable Service Form**:
  - Reason textarea (required)
  - Confirmation checkbox
- **Confirmation Modal**: Show confirmation before enabling/disabling services.

### Metrics Dashboard
- **Summary Cards**: Display key metrics:
  - Total requests
  - Success rate (with color coding)
  - Average retry count
  - Circuit breaker opens/resets
- **Daily Breakdown Chart**: Line or bar chart showing daily metrics over time.
- **Period Selector**: Dropdown to select number of days (1-90).
- **Export Button**: Export metrics to CSV.

### Error Handling
- **Service Not Found**: Display "Service not found" message.
- **Operation Failed**: Show error message with retry option.
- **Validation Errors**: Display field-level validation errors.

---

## 🔒 Security Considerations

- **Admin Only**: All endpoints require admin authentication.
- **Service Control**: Require confirmation for enable/disable operations.
- **Circuit Breaker Reset**: Require confirmation and reason for reset operations.
- **Audit Trail**: Log all service control and circuit breaker operations.

---

## 📝 Notes

- Circuit breakers automatically transition between states based on failure/success thresholds.
- Manual service disable takes precedence over automatic retry logic.
- Service metrics are aggregated from retry system logs.
- Circuit breaker resets should be used carefully; ensure underlying issues are resolved first.
