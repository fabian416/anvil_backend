# Admin Overview API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URLs**: `/api/admin/chat`, `/api/admin/security`

---

## 📋 Table of Contents

1. [Chat Dashboard Endpoints](#chat-dashboard-endpoints)
2. [Security Dashboard Endpoints](#security-dashboard-endpoints)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Error Handling](#error-handling)
5. [WebSocket Connections](#websocket-connections)
6. [API Design Trade-off Analysis](#api-design-trade-off-analysis)

---

## 🔌 Chat Dashboard Endpoints

### 1. Get Chat Dashboard

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date for analytics | 30 days ago |
| `date_to` | `datetime` | No | End date for analytics | Now |

**Date Format**: ISO 8601 (e.g., `2024-01-15T10:30:00Z`)

#### Response

##### Success Response (200 OK)
```typescript
interface AdminChatDashboardSummaryResponse {
  date_from: string;                    // ISO 8601
  date_to: string;                       // ISO 8601
  total_conversations: number;
  total_messages: number;
  total_active_users: number;
  total_cost_usd: number;
  total_agent_invocations: number;
  most_used_agent: string;
  avg_success_rate: number;              // 0-1
  avg_response_time_ms: number;
  error_rate: number;                    // 0-1
  cache_hit_rate: number;                // 0-1
  top_agents: AgentLeaderboardEntry[];   // Top 5
  conversation_trend: TimeSeriesDataPoint[];
  cost_trend: TimeSeriesDataPoint[];
}

interface AgentLeaderboardEntry {
  agent_type: string;
  agent_name: string;
  rank: number;
  total_invocations: number;
  success_rate: number;                  // 0-1
  avg_response_time_ms: number;
  total_cost_usd: number;
  error_count: number;
  last_used: string | null;              // ISO 8601
}

interface TimeSeriesDataPoint {
  timestamp: string;                     // ISO 8601
  value: number;
  label: string | null;
}
```

**JSON Example**:
```json
{
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-15T10:30:00Z",
  "total_conversations": 1250,
  "total_messages": 8900,
  "total_active_users": 450,
  "total_cost_usd": 125.50,
  "total_agent_invocations": 5000,
  "most_used_agent": "swap_agent",
  "avg_success_rate": 0.987,
  "avg_response_time_ms": 1200,
  "error_rate": 0.005,
  "cache_hit_rate": 0.45,
  "top_agents": [
    {
      "agent_type": "swap_agent",
      "agent_name": "Swap Agent",
      "rank": 1,
      "total_invocations": 2500,
      "success_rate": 0.99,
      "avg_response_time_ms": 800,
      "total_cost_usd": 45.00,
      "error_count": 25,
      "last_used": "2024-01-15T10:25:00Z"
    }
  ],
  "conversation_trend": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 50,
      "label": "Day 1"
    }
  ],
  "cost_trend": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 4.50,
      "label": "Day 1"
    }
  ]
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `500` | `Exception` | Internal server error | Show error: "Failed to load dashboard" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

---

### 2. Get Agent Performance

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/agents/performance`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `agent_type` | `string` | No | Filter by agent type | All agents |
| `sort_by` | `string` | No | Sort metric | `invocations` |
| `limit` | `number` | No | Max results | `10` |

**Valid `sort_by` Values**: `invocations`, `success_rate`, `avg_response_time`, `total_cost`

**Valid `limit` Range**: 1-50

#### Response

##### Success Response (200 OK)
```typescript
interface AgentPerformanceResponse {
  date_from: string;
  date_to: string;
  total_agents: number;
  leaderboard: AgentLeaderboardEntry[];
  total_invocations: number;
  overall_success_rate: number;         // 0-1
  avg_response_time_ms: number;
  total_cost_usd: number;
  invocation_trend: TimeSeriesDataPoint[];
  response_time_trend: TimeSeriesDataPoint[];
}
```

**JSON Example**:
```json
{
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-15T10:30:00Z",
  "total_agents": 8,
  "leaderboard": [
    {
      "agent_type": "swap_agent",
      "agent_name": "Swap Agent",
      "rank": 1,
      "total_invocations": 2500,
      "success_rate": 0.99,
      "avg_response_time_ms": 800,
      "total_cost_usd": 45.00,
      "error_count": 25,
      "last_used": "2024-01-15T10:25:00Z"
    }
  ],
  "total_invocations": 5000,
  "overall_success_rate": 0.987,
  "avg_response_time_ms": 1200,
  "total_cost_usd": 125.50,
  "invocation_trend": [...],
  "response_time_trend": [...]
}
```

---

### 3. Get Cache Efficiency

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/cache/efficiency`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 7 days ago |
| `date_to` | `datetime` | No | End date | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface CacheEfficiencyResponse {
  date_from: string;
  date_to: string;
  overall_hit_rate: number;              // 0-1
  overall_miss_rate: number;             // 0-1
  total_memory_usage_mb: number;
  total_cache_entries: number;
  cache_statistics: CacheStatistics[];
  avg_cache_hit_time_ms: number;
  avg_cache_miss_time_ms: number;
  estimated_time_saved_seconds: number;
  hit_rate_trend: TimeSeriesDataPoint[];
  memory_usage_trend: TimeSeriesDataPoint[];
}

interface CacheStatistics {
  cache_type: string;
  hit_count: number;
  miss_count: number;
  hit_rate: number;                      // 0-1
  memory_usage_mb: number;
  eviction_count: number;
  avg_lookup_time_ms: number;
}
```

---

### 4. Get Costs

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/costs`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `group_by` | `string` | No | Group dimension | `agent` |

**Valid `group_by` Values**: `agent`, `model`, `day`, `user`

#### Response

##### Success Response (200 OK)
```typescript
interface CostTrackingResponse {
  date_from: string;
  date_to: string;
  total_cost_usd: number;
  avg_cost_per_conversation: number;
  total_tokens_used: number;
  cost_breakdown: CostBreakdownEntry[];
  most_expensive_agent: string;
  most_expensive_model: string;
  highest_cost_user_id: number | null;
  projected_monthly_cost_usd: number;
  cost_change_percentage: number;
  daily_cost_trend: TimeSeriesDataPoint[];
  cost_by_agent_trend: { [agent: string]: TimeSeriesDataPoint[] };
}

interface CostBreakdownEntry {
  category: string;
  name: string;
  cost_usd: number;
  percentage: number;                    // 0-100
  invocations: number;
  avg_cost_per_invocation: number;
}
```

---

### 5. Get Errors

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/errors`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 7 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `severity` | `string` | No | Filter by severity | All severities |

**Valid `severity` Values**: `critical`, `high`, `medium`, `low`

#### Response

##### Success Response (200 OK)
```typescript
interface ErrorMonitoringResponse {
  date_from: string;
  date_to: string;
  total_errors: number;
  error_rate: number;                    // 0-1
  errors_by_type: ErrorStatistics[];
  errors_by_agent: { [agent: string]: number };
  errors_by_severity: { [severity: string]: number };
  critical_errors: number;
  critical_error_messages: string[];
  error_rate_trend: TimeSeriesDataPoint[];
  errors_by_severity_trend: { [severity: string]: TimeSeriesDataPoint[] };
}

interface ErrorStatistics {
  error_type: string;
  count: number;
  percentage: number;                    // 0-100
  severity: 'critical' | 'high' | 'medium' | 'low';
  most_common_message: string | null;
  affected_agents: string[];
  first_occurrence: string;              // ISO 8601
  last_occurrence: string;               // ISO 8601
}
```

---

### 6. Get Active Users

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/users/active`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface ActiveUsersResponse {
  date_from: string;
  date_to: string;
  engagement_metrics: UserEngagementMetrics;
  users_by_activity_level: { [level: string]: number };
  most_active_users: Array<{ user_id: number; message_count: number }>;
  dau_trend: TimeSeriesDataPoint[];
  new_users_trend: TimeSeriesDataPoint[];
}

interface UserEngagementMetrics {
  total_active_users: number;
  daily_active_users: number;
  weekly_active_users: number;
  monthly_active_users: number;
  new_users: number;
  avg_sessions_per_user: number;
  avg_messages_per_user: number;
  user_retention_rate: number;          // 0-1
}
```

---

### 7. Get Conversations

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/conversations`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |

#### Response

##### Success Response (200 OK)
```typescript
interface ConversationMetricsResponse {
  date_from: string;
  date_to: string;
  conversation_stats: ConversationStats;
  top_topics: Array<{ topic: string; count: number }>;
  messages_by_hour: { [hour: number]: number };  // 0-23
  messages_by_day: { [day: string]: number };
  conversation_trend: TimeSeriesDataPoint[];
  message_trend: TimeSeriesDataPoint[];
}

interface ConversationStats {
  total_conversations: number;
  total_messages: number;
  avg_messages_per_conversation: number;
  avg_conversation_duration_seconds: number;
  completion_rate: number;               // 0-1
  peak_activity_hour: number;            // 0-23
  peak_activity_day: string;
}
```

---

### 8. Export Data

**Method**: `GET`  
**Endpoint**: `/api/admin/chat/dashboard/export`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `date_from` | `datetime` | No | Start date | 30 days ago |
| `date_to` | `datetime` | No | End date | Now |
| `format` | `string` | **Yes** | Export format | - |
| `include_sections` | `string[]` | No | Sections to include | All sections |

**Valid `format` Values**: `json`, `csv`

**Valid `include_sections` Values**: `agents`, `costs`, `errors`, `users`, `conversations`

#### Response

##### Success Response (200 OK)
```typescript
interface ExportDataResponse {
  export_format: 'json' | 'csv';
  date_from: string;
  date_to: string;
  sections_included: string[];
  data: { [section: string]: any };
  generated_at: string;                 // ISO 8601
  record_count: number;
  file_size_bytes: number | null;
}
```

---

## 🔒 Security Dashboard Endpoints

### 9. Get Security Dashboard

**Method**: `GET`  
**Endpoint**: `/api/admin/security/dashboard`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

No query parameters

#### Response

##### Success Response (200 OK)
```typescript
interface SecurityDashboardResponse {
  timestamp: string;                    // ISO 8601
  security_posture: {
    overall_score: number;             // 0-100
    level: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  };
  latest_scan: {
    scan_id: string;
    scan_date: string;                   // ISO 8601
    status: 'completed' | 'running' | 'failed';
    vulnerabilities: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
  };
  attack_statistics: {
    xss_attempts: {
      total: number;
      blocked: number;
    };
    prompt_injections: {
      total: number;
      blocked: number;
    };
  };
  total_scans: number;
  active_tools: string[];
  overall_status: 'healthy' | 'warning' | 'critical' | 'unknown';
}
```

**JSON Example**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "security_posture": {
    "overall_score": 92,
    "level": "EXCELLENT"
  },
  "latest_scan": {
    "scan_id": "scan_20240115_020000",
    "scan_date": "2024-01-15T02:00:00Z",
    "status": "completed",
    "vulnerabilities": {
      "critical": 0,
      "high": 2,
      "medium": 5,
      "low": 10
    }
  },
  "attack_statistics": {
    "xss_attempts": {
      "total": 127,
      "blocked": 127
    },
    "prompt_injections": {
      "total": 43,
      "blocked": 43
    }
  },
  "total_scans": 150,
  "active_tools": ["bandit", "semgrep", "safety"],
  "overall_status": "warning"
}
```

---

### 10. Get Latest Scan

**Method**: `GET`  
**Endpoint**: `/api/admin/security/scans/latest`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface SecurityScanResult {
  scan_id: string;
  scan_date: string;                     // ISO 8601
  tools_executed: string[];
  duration_seconds: number;
  reports_path: string;
  errors: string[];
  vulnerabilities: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}
```

---

### 11. Get Scan Details

**Method**: `GET`  
**Endpoint**: `/api/admin/security/scans/{scan_id}`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `scan_id` | `string` | **Yes** | Scan identifier |

#### Response

##### Success Response (200 OK)
Returns detailed scan results with tool-specific outputs.

---

### 12. Get Security Trends

**Method**: `GET`  
**Endpoint**: `/api/admin/security/trends`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `days` | `number` | No | Lookback period | `30` |

**Valid `days` Range**: 1-90

#### Response

##### Success Response (200 OK)
```typescript
interface VulnerabilityTrendsResponse {
  dates: string[];                       // ISO 8601 dates
  critical: number[];
  high: number[];
  medium: number[];
  low: number[];
}
```

---

### 13. Get Security Posture

**Method**: `GET`  
**Endpoint**: `/api/admin/security/posture`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface SecurityPostureResponse {
  overall_score: number;                 // 0-100
  level: 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR' | 'CRITICAL';
  factors: {
    critical_vulnerabilities: number;
    high_vulnerabilities: number;
    medium_vulnerabilities: number;
    block_rate: number;                  // 0-1
  };
  calculation_details: {
    base_score: number;
    deductions: Array<{ reason: string; amount: number }>;
    bonuses: Array<{ reason: string; amount: number }>;
  };
}
```

---

### 14. Get Attack Monitoring

**Method**: `GET`  
**Endpoint**: `/api/admin/security/attacks`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface AttackStatisticsResponse {
  period: '24h' | '7d' | '30d';
  xss_attempts: {
    total: number;
    blocked: number;
    block_rate: number;                  // 0-1
    top_patterns: Array<{ pattern: string; count: number }>;
  };
  prompt_injections: {
    total: number;
    blocked: number;
    block_rate: number;                  // 0-1
    top_patterns: Array<{ pattern: string; count: number }>;
  };
}
```

---

### 15. Get Approvals

**Method**: `GET`  
**Endpoint**: `/api/admin/security/approvals`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface TransactionApprovalStatsResponse {
  total_requests: number;
  approved: number;
  denied: number;
  pending: number;
  avg_response_time_seconds: number;
  breakdown_by_type: { [type: string]: { approved: number; denied: number } };
}
```

---

### 16. Get PII Protection

**Method**: `GET`  
**Endpoint**: `/api/admin/security/pii-protection`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface PIIProtectionResponse {
  total_detections: number;
  redactions_performed: number;
  pii_by_type: {
    email: number;
    phone: number;
    ssn: number;
    credit_card: number;
    wallet_address: number;
    api_key: number;
    jwt_token: number;
  };
  compliance_status: {
    gdpr: 'compliant' | 'non-compliant';
    ccpa: 'compliant' | 'non-compliant';
  };
}
```

---

### 17. Get Agent Isolation

**Method**: `GET`  
**Endpoint**: `/api/admin/security/agent-isolation`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface AgentIsolationResponse {
  permission_checks: number;
  access_denials: number;
  isolation_violations: number;
  active_agents_by_role: { [role: string]: number };
  violation_details: Array<{
    agent_id: string;
    violation_type: string;
    timestamp: string;                   // ISO 8601
  }>;
}
```

---

### 18. Get Security Tools

**Method**: `GET`  
**Endpoint**: `/api/admin/security/tools`  
**Auth Required**: Yes (Bearer Token - Admin Only)

#### Response

##### Success Response (200 OK)
```typescript
interface SecurityToolsResponse {
  tools: Array<{
    name: string;
    version: string;
    status: 'active' | 'inactive' | 'error';
    last_run: string | null;             // ISO 8601
    patterns_detected: number;
  }>;
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
  timestamp: string;                     // ISO 8601
  value: number;
  label: string | null;
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
   - Invalid parameter values
   - **Action**: Show inline field errors

4. **Not Found Errors (404)**
   - Scan not found
   - **Action**: Show error: "Scan not found"

5. **Service Unavailable (503)**
   - Backend service down
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Error Handling Summary

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `BadRequestError` | Invalid parameters | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `AuthorizationError` | Not admin | Show error: "Admin access required" |
| `404` | `NotFoundError` | Resource not found | Show error: "Resource not found" |
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

## 📡 WebSocket Connections

### Admin Dashboard WebSocket

**Endpoint**: `ws://localhost:8000/api/admin/llm/dashboard/ws`  
**Auth Required**: Yes (JWT Token in Query Parameter)  
**Purpose**: Real-time updates for LLM dashboard metrics

#### Connection

**Connection URL**:
```
ws://localhost:8000/api/admin/llm/dashboard/ws?token={jwt_token}
```

#### Client-to-Server Messages

##### Heartbeat (Ping)
```typescript
interface PingMessage {
  type: "ping";
}
```

**JSON Example**:
```json
{
  "type": "ping"
}
```

#### Server-to-Client Messages

##### Connection Confirmed
```typescript
interface ConnectionMessage {
  type: "connection";
  status: "connected";
  timestamp: string;                     // ISO 8601
}
```

##### Heartbeat Response (Pong)
```typescript
interface PongMessage {
  type: "pong";
  timestamp: string;                     // ISO 8601
}
```

##### Metrics Update
```typescript
interface MetricsUpdateMessage {
  type: "metrics_update";
  data: {
    total_requests: number;
    total_cost_usd: number;
    avg_response_time_ms: number;
    error_rate: number;
  };
  timestamp: string;                     // ISO 8601
}
```

##### Error Message
```typescript
interface ErrorMessage {
  type: "error";
  message: string;
}
```

#### Connection Lifecycle

1. **Connect**: Client connects with JWT token
2. **Receive Updates**: Server broadcasts updates periodically
3. **Heartbeat**: Client sends ping every 30 seconds
4. **Disconnect**: Client closes connection or server disconnects on error

#### Error Handling

**Connection Errors**:
- Invalid token → Connection rejected (code 1008)
- Network error → Client should reconnect
- Server error → Connection closed (code 1011)

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **WebSocket for Real-time Updates** | Polling | Real-time vs. Resource usage | WebSocket reduces server load vs. polling, but requires connection management |
| **Date Range Parameters** | Fixed Periods | Flexibility vs. Complexity | Date ranges allow custom analysis, but require validation |
| **Export Format Options** | Single Format | User Choice vs. Maintenance | Multiple formats (JSON/CSV) improve usability, but require more code |
| **Aggregated Dashboard Endpoint** | Separate Endpoints | Performance vs. Granularity | Single endpoint reduces requests, but limits granular control |

### Risk Assessment

**Cognitive Limitations:**
- WebSocket connection management may be complex for frontend developers
- Date range validation requires careful handling
- Large export files may cause memory issues

**Technical Debt:**
- WebSocket reconnection logic must handle network failures gracefully
- Date range queries may become slow with large datasets
- Export generation may block other requests

**Validation Strategy:**
- ✅ Monitor WebSocket connection health and reconnection rates
- ✅ Track dashboard load times
- ✅ Alert on export generation failures
- ✅ Monitor query performance for date ranges

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/admin/chat_dashboard.py`
- **Backend Controller**: `src/app/presentation/http/controllers/admin/security_router.py`
- **Response Schemas**: `src/app/presentation/http/schemas/admin_chat_dashboard.py`
- **Frontend Implementation**: `01-Admin-Overview/IMPLEMENTATION.md`
- **UI/UX Design**: `01-Admin-Overview/UI_UX.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
