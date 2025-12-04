# Retry System Admin Dashboard

## Overview

Admin dashboard for monitoring and controlling the enterprise retry system. Provides real-time visibility into service health, circuit breaker status, and retry metrics.

## API Endpoints

Base URL: `/api/v1/admin/retry`

### 1. List All Services

```http
GET /api/v1/admin/retry/services
```

**Response**:
```json
{
  "services": [
    {
      "service_name": "defillama_mcp",
      "enabled": true,
      "circuit_state": "CLOSED",
      "failure_count": 2,
      "success_count": 98,
      "last_error": null,
      "last_error_at": null,
      "override_reason": null,
      "override_expires_at": null
    }
  ]
}
```

### 2. Get Service Status

```http
GET /api/v1/admin/retry/services/{service_name}
```

**Response**: Same as individual service object above.

### 3. Disable Service

```http
POST /api/v1/admin/retry/services/{service_name}/disable
Content-Type: application/json

{
  "reason": "1inch API outage - https://status.1inch.io/incidents/123",
  "duration_minutes": 180
}
```

**Response**:
```json
{
  "message": "Service 'oneinch_mcp' disabled",
  "reason": "1inch API outage",
  "duration_minutes": 180
}
```

### 4. Enable Service

```http
POST /api/v1/admin/retry/services/{service_name}/enable
Content-Type: application/json

{
  "reason": "1inch API back online - verified"
}
```

### 5. Get Circuit Breakers

```http
GET /api/v1/admin/retry/circuit-breakers
```

**Response**:
```json
[
  {
    "service_name": "defillama_mcp",
    "state": "CLOSED",
    "failure_count": 0,
    "success_count": 0,
    "opened_at": null,
    "config": {
      "failure_threshold": 5,
      "success_threshold": 2,
      "timeout_seconds": 60
    }
  }
]
```

### 6. Reset Circuit Breaker

```http
POST /api/v1/admin/retry/circuit-breakers/{service_name}/reset
Content-Type: application/json

{
  "reason": "Manual reset after fixing API credentials"
}
```

### 7. Get Service Metrics

```http
GET /api/v1/admin/retry/metrics/{service_name}?days=7
```

**Response**:
```json
{
  "service_name": "defillama_mcp",
  "days": 7,
  "metrics": [
    {
      "date": "2025-12-01",
      "total_requests": 1000,
      "successful_requests": 980,
      "failed_requests": 20,
      "retry_attempts": 35,
      "avg_latency_ms": 245.3,
      "circuit_breaker_opens": 1,
      "success_rate": 0.98
    }
  ],
  "summary": {
    "total_requests": 7000,
    "avg_success_rate": 0.97,
    "avg_latency_ms": 250.5,
    "total_circuit_opens": 3
  }
}
```

## UI Components

### Service List View

**Features**:
- Table with all services
- Status indicators (enabled/disabled, circuit state)
- Failure/success counts
- Quick actions (disable/enable, reset circuit)

**Columns**:
| Service | Status | Circuit | Failures | Success Rate | Actions |
|---------|--------|---------|----------|--------------|---------|
| defillama_mcp | ✅ Enabled | 🟢 CLOSED | 2/5 | 98% | [Disable] [Details] |
| oneinch_mcp | ⚠️ Disabled | 🔴 OPEN | 5/5 | 85% | [Enable] [Reset] |

### Service Detail View

**Sections**:
1. **Status Overview**: Current state, enabled/disabled, override info
2. **Circuit Breaker**: State, thresholds, history
3. **Metrics Chart**: 7-day trend (success rate, latency)
4. **Recent Events**: Last 20 retry attempts

### Metrics Dashboard

**Charts**:
1. **Success Rate Over Time** (Line chart, 7-30-90 days)
2. **Latency Distribution** (Box plot, P50/P95/P99)
3. **Circuit Opens** (Bar chart by service)
4. **Retry Rate** (Line chart)

### Actions Panel

**Quick Actions**:
- Disable Service (with reason + duration)
- Enable Service (with reason)
- Reset Circuit Breaker (with reason)
- View Logs

## State Management

```typescript
interface RetryState {
  services: Service[];
  selectedService: Service | null;
  metrics: ServiceMetrics | null;
  loading: boolean;
  error: string | null;
}

interface Service {
  service_name: string;
  enabled: boolean;
  circuit_state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failure_count: number;
  success_count: number;
  last_error?: string;
  last_error_at?: string;
  override_reason?: string;
  override_expires_at?: string;
}
```

## Implementation Notes

- Poll `/services` endpoint every 30 seconds for live updates
- Show toast notifications for actions (disable/enable/reset)
- Require confirmation modal for disruptive actions
- Use color coding: Green (CLOSED), Yellow (HALF_OPEN), Red (OPEN)
- Cache metrics data for 5 minutes
- Implement role-based access (admin only)

---

**Last Updated**: December 1, 2025
