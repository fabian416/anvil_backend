# Admin Overview API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework  
> **Base URLs**: `/api/admin/chat`, `/api/admin/security`

---

## 📋 Table of Contents

1. [Chat Dashboard Endpoints](#chat-dashboard-endpoints)
2. [Security Dashboard Endpoints](#security-dashboard-endpoints)
3. [Request/Response Schemas](#requestresponse-schemas)
4. [Error Handling](#error-handling)

---

## 🔌 Chat Dashboard Endpoints

### 1. Get Chat Dashboard
**GET** `/api/admin/chat/dashboard`

Retrieve comprehensive chat analytics dashboard data.

**Response**:
```json
{
  "active_conversations": 50,
  "total_messages": 1250,
  "agent_performance": [...],
  "cost_tracking": {...}
}
```

### 2. Get Agent Performance
**GET** `/api/admin/chat/dashboard/agents/performance`

Get agent performance metrics.

### 3. Get Cache Efficiency
**GET** `/api/admin/chat/dashboard/cache/efficiency`

Get cache efficiency metrics.

### 4. Get Costs
**GET** `/api/admin/chat/dashboard/costs`

Get cost tracking data.

### 5. Get Errors
**GET** `/api/admin/chat/dashboard/errors`

Get error monitoring data.

### 6. Get Active Users
**GET** `/api/admin/chat/dashboard/users/active`

Get active user metrics.

### 7. Get Conversations
**GET** `/api/admin/chat/dashboard/conversations`

Get conversation metrics.

### 8. Export Data
**GET** `/api/admin/chat/dashboard/export`

Export dashboard data.

---

## 🔒 Security Dashboard Endpoints

### 1. Get Security Dashboard
**GET** `/api/admin/security/dashboard`

Get security dashboard overview.

**Response**:
```json
{
  "status": "critical",
  "latest_scan": {...},
  "critical_alerts": [...]
}
```

### 2. Get Latest Scan
**GET** `/api/admin/security/scans/latest`

Get latest security scan results.

### 3. Get Scan Details
**GET** `/api/admin/security/scans/{scan_id}`

Get detailed scan results.

### 4. Get Security Trends
**GET** `/api/admin/security/trends`

Get security trend data.

### 5. Get Security Posture
**GET** `/api/admin/security/posture`

Get security posture assessment.

### 6. Get Attack Monitoring
**GET** `/api/admin/security/attacks`

Get attack monitoring data.

### 7. Get Approvals
**GET** `/api/admin/security/approvals`

Get security approval data.

### 8. Get PII Protection
**GET** `/api/admin/security/pii-protection`

Get PII protection status.

### 9. Get Agent Isolation
**GET** `/api/admin/security/agent-isolation`

Get agent isolation status.

### 10. Get Security Tools
**GET** `/api/admin/security/tools`

Get security tools information.

---

## 📝 Request/Response Schemas

### Chat Dashboard Response
```typescript
interface ChatDashboardResponse {
  active_conversations: number;
  total_messages: number;
  agent_performance: AgentPerformance[];
  cost_tracking: CostData;
  cache_efficiency: CacheMetrics;
  errors: ErrorMetrics;
  active_users: UserMetrics;
}
```

### Security Dashboard Response
```typescript
interface SecurityDashboardResponse {
  status: 'critical' | 'warning' | 'healthy';
  latest_scan: ScanResult | null;
  critical_alerts: SecurityAlert[];
  trends: SecurityTrend[];
  posture: SecurityPosture;
}
```

---

## ⚠️ Error Handling

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Not authenticated | Redirect to login |
| `403` | `AuthorizationError` | Not authorized | Show error message |
| `500` | `Exception` | Internal server error | Show error with retry |
| `503` | `DataMapperError` | Service unavailable | Show error with retry |

---

## 🔐 Authentication

All endpoints require:
- **Bearer Token**: Admin JWT token in `Authorization` header
- **Admin Role**: User must have admin privileges

---

## 📡 Real-time Updates

**WebSocket Connection**: `/ws/admin/dashboard`

**Events**:
- `security_alert`: New security alert
- `chat_metrics_update`: Updated chat metrics
- `system_health_change`: System health status change
