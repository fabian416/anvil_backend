# FRONTEND_ADMIN_TELEMETRY

## Admin Telemetry & Observability Module

**User Type:** Administrator  
**Module:** Telemetry & Observability  
**Route:** `/admin/telemetry/*`  
**Platform:** Web Admin Dashboard  
**Version:** 1.0  
**Last Updated:** December 6, 2025

---

## 📋 Module Overview

### Title
**Telemetry Dashboard** - Enterprise-Grade Observability for Anvil Platform

### Description
Comprehensive telemetry and observability system providing real-time metrics, distributed tracing, error tracking, and performance monitoring across all platform components including APIs, LLM providers, and database operations.

### Key Capabilities
- ✅ API metrics (latency, errors, throughput)
- ✅ LLM provider monitoring (costs, tokens, latency)
- ✅ Database query telemetry (slow queries, patterns)
- ✅ Distributed tracing (request flow visualization)
- ✅ Feature flags (granular telemetry control)
- ✅ Prometheus export (for external monitoring)
- ✅ Alert destinations (email, Slack, PagerDuty)

---

## 🔌 API Integration

### Base URL
```
/api/v1/admin/telemetry/*
```

### Authentication
All endpoints require admin authentication:
```
Authorization: Bearer <admin_jwt_token>
```

---

## 📊 API Telemetry Endpoints

### 1. Get API Metrics

```typescript
// GET /api/v1/admin/telemetry/metrics
// Description: Get API performance metrics
// Authentication: Admin Required
// Rate Limit: 100 requests/minute

// Query Parameters
interface TelemetryMetricsQuery {
  api?: string;       // Filter by API name (coingecko, defillama, etc.)
  hours?: number;     // Time range in hours (default: 24)
}

// Response
interface TelemetryMetricsResponse {
  timestamp: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  cache_hits: number;
  cache_misses: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  error_rate: number;
  apis: Record<string, APIMetrics>;
}

interface APIMetrics {
  name: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  error_rate: number;
  last_error?: string;
  last_error_time?: string;
}

// Example Request
GET /api/v1/admin/telemetry/metrics?api=coingecko&hours=24

// Example Response (200 OK)
{
  "timestamp": "2025-12-06T10:30:00Z",
  "total_requests": 125000,
  "successful_requests": 123750,
  "failed_requests": 1250,
  "cache_hits": 45000,
  "cache_misses": 80000,
  "avg_latency_ms": 145.5,
  "p95_latency_ms": 320.0,
  "p99_latency_ms": 890.0,
  "error_rate": 0.01,
  "apis": {
    "coingecko": {
      "name": "coingecko",
      "total_requests": 45000,
      "successful_requests": 44820,
      "failed_requests": 180,
      "avg_latency_ms": 120.5,
      "p95_latency_ms": 280.0,
      "error_rate": 0.004
    }
  }
}

// Error Response (401 Unauthorized)
{
  "error": {
    "code": "AUTH_004",
    "message": "Authentication required",
    "i18n_key": "errors.auth.token_missing",
    "http_status": 401
  }
}

// Error Response (403 Forbidden)
{
  "error": {
    "code": "ADM_001",
    "message": "Administrator access required",
    "i18n_key": "errors.admin.access_denied",
    "http_status": 403
  }
}
```

---

### 2. Get Error Summary

```typescript
// GET /api/v1/admin/telemetry/errors
// Description: Get error summary by category
// Authentication: Admin Required

// Query Parameters
interface ErrorSummaryQuery {
  hours?: number;     // Time range (default: 24)
  severity?: string;  // Filter: critical, error, warning
}

// Response
interface ErrorSummaryResponse {
  timestamp: string;
  total_errors: number;
  by_severity: Record<string, number>;
  by_api: Record<string, APIErrorSummary>;
  recent_errors: ErrorEntry[];
}

interface APIErrorSummary {
  api_name: string;
  total_errors: number;
  critical: number;
  error: number;
  warning: number;
  top_error_codes: string[];
}

interface ErrorEntry {
  timestamp: string;
  api_name: string;
  error_code: string;
  message: string;
  severity: string;
  count: number;
}

// Example Response (200 OK)
{
  "timestamp": "2025-12-06T10:30:00Z",
  "total_errors": 1250,
  "by_severity": {
    "critical": 12,
    "error": 238,
    "warning": 1000
  },
  "by_api": {
    "coingecko": {
      "api_name": "coingecko",
      "total_errors": 180,
      "critical": 2,
      "error": 28,
      "warning": 150,
      "top_error_codes": ["429", "503", "timeout"]
    }
  },
  "recent_errors": [
    {
      "timestamp": "2025-12-06T10:29:55Z",
      "api_name": "coingecko",
      "error_code": "429",
      "message": "Rate limit exceeded",
      "severity": "warning",
      "count": 5
    }
  ]
}
```

---

### 3. Get Slow Calls

```typescript
// GET /api/v1/admin/telemetry/slow-calls
// Description: Get slowest API calls
// Authentication: Admin Required

// Query Parameters
interface SlowCallsQuery {
  hours?: number;        // Time range (default: 24)
  threshold_ms?: number; // Minimum latency (default: 1000)
  limit?: number;        // Max results (default: 100)
}

// Response
interface SlowCallsResponse {
  threshold_ms: number;
  total_slow_calls: number;
  calls: SlowCall[];
}

interface SlowCall {
  timestamp: string;
  api_name: string;
  endpoint: string;
  method: string;
  latency_ms: number;
  status_code: number;
  cache_hit: boolean;
}

// Example Response (200 OK)
{
  "threshold_ms": 1000,
  "total_slow_calls": 45,
  "calls": [
    {
      "timestamp": "2025-12-06T10:28:30Z",
      "api_name": "defillama",
      "endpoint": "/protocols/all",
      "method": "GET",
      "latency_ms": 3250,
      "status_code": 200,
      "cache_hit": false
    }
  ]
}
```

---

### 4. Get Health Status

```typescript
// GET /api/v1/admin/telemetry/health
// Description: Overall telemetry system health
// Authentication: Admin Required

// Response
interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  components: Record<string, ComponentHealth>;
  last_check: string;
}

interface ComponentHealth {
  name: string;
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms?: number;
  error_rate?: number;
  message?: string;
}

// Example Response (200 OK)
{
  "status": "healthy",
  "components": {
    "api_telemetry": {
      "name": "API Telemetry",
      "status": "healthy",
      "latency_ms": 45
    },
    "llm_telemetry": {
      "name": "LLM Telemetry",
      "status": "healthy",
      "latency_ms": 32
    },
    "db_telemetry": {
      "name": "Database Telemetry",
      "status": "healthy",
      "latency_ms": 18
    },
    "redis": {
      "name": "Redis",
      "status": "healthy",
      "latency_ms": 2
    }
  },
  "last_check": "2025-12-06T10:30:00Z"
}
```

---

### 5. Reset Metrics

```typescript
// POST /api/v1/admin/telemetry/reset
// Description: Reset telemetry metrics
// Authentication: Admin Required

// Request Body
interface ResetMetricsRequest {
  component?: string;  // Optional: specific component to reset
  confirm: boolean;    // Must be true to confirm
}

// Response
interface ResetMetricsResponse {
  success: boolean;
  reset_at: string;
  components_reset: string[];
}

// Example Request
POST /api/v1/admin/telemetry/reset
{
  "component": "api",
  "confirm": true
}

// Example Response (200 OK)
{
  "success": true,
  "reset_at": "2025-12-06T10:30:00Z",
  "components_reset": ["api_telemetry"]
}
```

---

## 🤖 LLM Telemetry Endpoints

### 6. Get LLM Metrics

```typescript
// GET /api/v1/admin/telemetry/llm/metrics
// Description: LLM usage and performance metrics
// Authentication: Admin Required

// Query Parameters
interface LLMMetricsQuery {
  hours?: number;      // Time range (default: 24)
  provider?: string;   // Filter by provider
  model?: string;      // Filter by model
}

// Response
interface LLMMetricsResponse {
  timestamp: string;
  total_requests: number;
  total_tokens_used: number;
  total_cost_usd: number;
  avg_latency_ms: number;
  providers: Record<string, ProviderMetrics>;
  models: Record<string, ModelMetrics>;
}

interface ProviderMetrics {
  name: string;
  requests: number;
  tokens_used: number;
  cost_usd: number;
  avg_latency_ms: number;
  error_rate: number;
  status: "healthy" | "degraded" | "unavailable";
}

interface ModelMetrics {
  model_id: string;
  provider: string;
  requests: number;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  avg_latency_ms: number;
}

// Example Response (200 OK)
{
  "timestamp": "2025-12-06T10:30:00Z",
  "total_requests": 15000,
  "total_tokens_used": 4500000,
  "total_cost_usd": 125.50,
  "avg_latency_ms": 850,
  "providers": {
    "xai": {
      "name": "xAI",
      "requests": 8000,
      "tokens_used": 2400000,
      "cost_usd": 48.00,
      "avg_latency_ms": 720,
      "error_rate": 0.002,
      "status": "healthy"
    },
    "openai": {
      "name": "OpenAI",
      "requests": 4000,
      "tokens_used": 1200000,
      "cost_usd": 45.00,
      "avg_latency_ms": 950,
      "error_rate": 0.001,
      "status": "healthy"
    }
  },
  "models": {
    "grok-2": {
      "model_id": "grok-2",
      "provider": "xai",
      "requests": 6000,
      "input_tokens": 1800000,
      "output_tokens": 450000,
      "cost_usd": 36.00,
      "avg_latency_ms": 680
    }
  }
}
```

---

### 7. Get LLM Costs

```typescript
// GET /api/v1/admin/telemetry/llm/costs
// Description: Detailed cost breakdown
// Authentication: Admin Required

// Query Parameters
interface LLMCostsQuery {
  period?: "daily" | "weekly" | "monthly";
  group_by?: "model" | "provider" | "agent";
}

// Response
interface LLMCostsResponse {
  period: string;
  total_cost_usd: number;
  budget_usd: number;
  budget_used_percent: number;
  breakdown: CostBreakdown[];
  forecast: CostForecast;
}

interface CostBreakdown {
  name: string;
  cost_usd: number;
  requests: number;
  tokens: number;
  percent_of_total: number;
}

interface CostForecast {
  projected_daily: number;
  projected_weekly: number;
  projected_monthly: number;
  trend: "increasing" | "stable" | "decreasing";
}

// Example Response (200 OK)
{
  "period": "daily",
  "total_cost_usd": 125.50,
  "budget_usd": 500.00,
  "budget_used_percent": 25.1,
  "breakdown": [
    {
      "name": "grok-2",
      "cost_usd": 36.00,
      "requests": 6000,
      "tokens": 2250000,
      "percent_of_total": 28.7
    },
    {
      "name": "gpt-4o",
      "cost_usd": 32.50,
      "requests": 2500,
      "tokens": 875000,
      "percent_of_total": 25.9
    }
  ],
  "forecast": {
    "projected_daily": 130.00,
    "projected_weekly": 910.00,
    "projected_monthly": 3900.00,
    "trend": "stable"
  }
}
```

---

## 🗃️ Database Telemetry Endpoints

### 8. Get Database Metrics

```typescript
// GET /api/v1/admin/telemetry/db/metrics
// Description: Database performance metrics
// Authentication: Admin Required

// Response
interface DBMetricsResponse {
  timestamp: string;
  total_queries: number;
  avg_query_time_ms: number;
  slow_queries_count: number;
  connection_pool: ConnectionPoolStatus;
  by_table: Record<string, TableMetrics>;
}

interface ConnectionPoolStatus {
  size: number;
  in_use: number;
  available: number;
  waiting: number;
  max_size: number;
}

interface TableMetrics {
  table_name: string;
  query_count: number;
  avg_time_ms: number;
  row_count: number;
}

// Example Response (200 OK)
{
  "timestamp": "2025-12-06T10:30:00Z",
  "total_queries": 250000,
  "avg_query_time_ms": 12.5,
  "slow_queries_count": 45,
  "connection_pool": {
    "size": 20,
    "in_use": 8,
    "available": 12,
    "waiting": 0,
    "max_size": 50
  },
  "by_table": {
    "conversations": {
      "table_name": "conversations",
      "query_count": 45000,
      "avg_time_ms": 8.2,
      "row_count": 125000
    },
    "messages": {
      "table_name": "messages",
      "query_count": 120000,
      "avg_time_ms": 5.1,
      "row_count": 2500000
    }
  }
}
```

---

### 9. Get Slow Queries

```typescript
// GET /api/v1/admin/telemetry/db/slow-queries
// Description: Slowest database queries
// Authentication: Admin Required

// Query Parameters
interface SlowQueriesQuery {
  hours?: number;        // Time range (default: 24)
  threshold_ms?: number; // Minimum time (default: 100)
  limit?: number;        // Max results (default: 50)
}

// Response
interface SlowQueriesResponse {
  threshold_ms: number;
  total_slow_queries: number;
  queries: SlowQuery[];
}

interface SlowQuery {
  timestamp: string;
  query_hash: string;
  query_pattern: string;  // Parameterized query
  execution_time_ms: number;
  table_name: string;
  operation: "SELECT" | "INSERT" | "UPDATE" | "DELETE";
  rows_affected: number;
}

// Example Response (200 OK)
{
  "threshold_ms": 100,
  "total_slow_queries": 45,
  "queries": [
    {
      "timestamp": "2025-12-06T10:28:15Z",
      "query_hash": "abc123",
      "query_pattern": "SELECT * FROM messages WHERE conversation_id = $1 ORDER BY created_at",
      "execution_time_ms": 450,
      "table_name": "messages",
      "operation": "SELECT",
      "rows_affected": 5000
    }
  ]
}
```

---

## 🎛️ Feature Flags Endpoints

### 10. Get Feature Flags

```typescript
// GET /api/v1/admin/telemetry/flags
// Description: Get current telemetry feature flags
// Authentication: Admin Required

// Response
interface FeatureFlagsResponse {
  enabled: boolean;
  api_telemetry_enabled: boolean;
  llm_telemetry_enabled: boolean;
  db_telemetry_enabled: boolean;
  tracing_enabled: boolean;
  metrics_export_enabled: boolean;
  sampling_rates: SamplingRates;
  disabled_apis: string[];
  disabled_llm_providers: string[];
  endpoint_config: EndpointConfig;
}

interface SamplingRates {
  api: number;      // 0.0 - 1.0
  llm: number;
  db: number;
  trace: number;
}

interface EndpointConfig {
  enabled: boolean;
  admin_telemetry_enabled: boolean;
  disabled_endpoints: string[];
}

// Example Response (200 OK)
{
  "enabled": true,
  "api_telemetry_enabled": true,
  "llm_telemetry_enabled": true,
  "db_telemetry_enabled": true,
  "tracing_enabled": true,
  "metrics_export_enabled": true,
  "sampling_rates": {
    "api": 0.1,
    "llm": 1.0,
    "db": 0.1,
    "trace": 0.05
  },
  "disabled_apis": [],
  "disabled_llm_providers": [],
  "endpoint_config": {
    "enabled": true,
    "admin_telemetry_enabled": true,
    "disabled_endpoints": []
  }
}
```

---

### 11. Update Feature Flags

```typescript
// PUT /api/v1/admin/telemetry/flags
// Description: Update telemetry feature flags
// Authentication: Admin Required

// Request Body
interface UpdateFlagsRequest {
  enabled?: boolean;
  api_telemetry_enabled?: boolean;
  llm_telemetry_enabled?: boolean;
  db_telemetry_enabled?: boolean;
  tracing_enabled?: boolean;
  metrics_export_enabled?: boolean;
  sampling_rates?: Partial<SamplingRates>;
}

// Response
interface UpdateFlagsResponse {
  success: boolean;
  updated_at: string;
  flags: FeatureFlagsResponse;
}

// Example Request
PUT /api/v1/admin/telemetry/flags
{
  "sampling_rates": {
    "api": 0.05,
    "db": 0.05
  }
}

// Example Response (200 OK)
{
  "success": true,
  "updated_at": "2025-12-06T10:30:00Z",
  "flags": { ... }
}
```

---

### 12. Persist Flags to Redis

```typescript
// POST /api/v1/admin/telemetry/flags/save
// Description: Save current flags to Redis for persistence
// Authentication: Admin Required

// Response
interface SaveFlagsResponse {
  success: boolean;
  saved_at: string;
  redis_key: string;
}

// Example Response (200 OK)
{
  "success": true,
  "saved_at": "2025-12-06T10:30:00Z",
  "redis_key": "telemetry:feature_flags"
}
```

---

### 13. Load Flags from Redis

```typescript
// POST /api/v1/admin/telemetry/flags/load
// Description: Load flags from Redis
// Authentication: Admin Required

// Response
interface LoadFlagsResponse {
  success: boolean;
  loaded_at: string;
  flags: FeatureFlagsResponse;
}

// Example Response (200 OK)
{
  "success": true,
  "loaded_at": "2025-12-06T10:30:00Z",
  "flags": { ... }
}
```

---

## 🎯 Use Cases

### Use Case 1: Monitor API Performance
**Scenario:** Admin wants to identify slow APIs affecting user experience.

```typescript
// 1. Get overall metrics
const metrics = await api.get('/admin/telemetry/metrics?hours=24');

// 2. Check slow calls
const slowCalls = await api.get('/admin/telemetry/slow-calls?threshold_ms=500');

// 3. View errors
const errors = await api.get('/admin/telemetry/errors?severity=error');

// 4. Take action based on findings
if (metrics.data.apis.coingecko.error_rate > 0.05) {
  // Disable API temporarily or increase caching
  await api.post('/admin/telemetry/flags/disable-api/coingecko');
}
```

### Use Case 2: Optimize LLM Costs
**Scenario:** Admin wants to reduce LLM spending.

```typescript
// 1. Get cost breakdown
const costs = await api.get('/admin/telemetry/llm/costs?group_by=model');

// 2. Identify expensive models
const expensiveModels = costs.data.breakdown
  .filter(m => m.cost_usd > 20)
  .sort((a, b) => b.cost_usd - a.cost_usd);

// 3. Check if cheaper alternatives work
// Review model performance in /admin/llm/models/{id}/performance

// 4. Adjust agent configurations to use cheaper models
await api.put('/admin/llm/agent-config/chat', {
  primary_model: 'grok-2-mini',
  fallback_models: ['gpt-3.5-turbo']
});
```

### Use Case 3: Reduce Telemetry Overhead
**Scenario:** Production is under high load, need to reduce telemetry overhead.

```typescript
// 1. Lower sampling rates
await api.put('/admin/telemetry/flags', {
  sampling_rates: {
    api: 0.01,    // 1% sampling
    db: 0.01,
    trace: 0.001  // 0.1% trace sampling
  }
});

// 2. Save to Redis for persistence
await api.post('/admin/telemetry/flags/save');

// 3. Verify changes
const flags = await api.get('/admin/telemetry/flags');
console.log(flags.data.sampling_rates);
```

---

## 🔧 React Hooks

```typescript
// useTelemetryMetrics.ts
import { useQuery } from '@tanstack/react-query';

export function useTelemetryMetrics(api?: string, hours = 24) {
  return useQuery({
    queryKey: ['telemetry', 'metrics', api, hours],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (api) params.set('api', api);
      params.set('hours', hours.toString());
      
      const response = await fetch(
        `/api/v1/admin/telemetry/metrics?${params}`
      );
      if (!response.ok) throw new Error('Failed to fetch metrics');
      return response.json();
    },
    refetchInterval: 30000, // Refresh every 30s
  });
}

// useLLMCosts.ts
export function useLLMCosts(period: 'daily' | 'weekly' | 'monthly' = 'daily') {
  return useQuery({
    queryKey: ['telemetry', 'llm', 'costs', period],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/admin/telemetry/llm/costs?period=${period}`
      );
      if (!response.ok) throw new Error('Failed to fetch costs');
      return response.json();
    },
    refetchInterval: 60000, // Refresh every minute
  });
}

// useFeatureFlags.ts
export function useFeatureFlags() {
  return useQuery({
    queryKey: ['telemetry', 'flags'],
    queryFn: async () => {
      const response = await fetch('/api/v1/admin/telemetry/flags');
      if (!response.ok) throw new Error('Failed to fetch flags');
      return response.json();
    },
  });
}

// useUpdateFeatureFlags.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useUpdateFeatureFlags() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (updates: Partial<FeatureFlagsRequest>) => {
      const response = await fetch('/api/v1/admin/telemetry/flags', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to update flags');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['telemetry', 'flags'] });
    },
  });
}
```

---

## 🎨 Component Example

```typescript
// TelemetryDashboard.tsx
import React from 'react';
import { useTelemetryMetrics, useLLMCosts, useFeatureFlags } from './hooks';

export function TelemetryDashboard() {
  const { data: metrics, isLoading: metricsLoading } = useTelemetryMetrics();
  const { data: costs } = useLLMCosts('daily');
  const { data: flags } = useFeatureFlags();

  if (metricsLoading) return <LoadingSpinner />;

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* API Metrics Card */}
      <MetricCard
        title="API Requests"
        value={metrics?.total_requests.toLocaleString()}
        subtitle={`${(metrics?.error_rate * 100).toFixed(2)}% error rate`}
        trend={metrics?.error_rate < 0.01 ? 'positive' : 'negative'}
      />
      
      {/* LLM Costs Card */}
      <MetricCard
        title="LLM Costs (Today)"
        value={`$${costs?.total_cost_usd.toFixed(2)}`}
        subtitle={`${costs?.budget_used_percent.toFixed(1)}% of budget`}
        trend={costs?.budget_used_percent < 80 ? 'positive' : 'warning'}
      />
      
      {/* Latency Card */}
      <MetricCard
        title="Avg Latency"
        value={`${metrics?.avg_latency_ms.toFixed(0)}ms`}
        subtitle={`P95: ${metrics?.p95_latency_ms.toFixed(0)}ms`}
        trend={metrics?.avg_latency_ms < 200 ? 'positive' : 'warning'}
      />
      
      {/* Feature Flags Status */}
      <div className="col-span-3">
        <FeatureFlagsPanel flags={flags} />
      </div>
    </div>
  );
}
```

---

## 🔐 Security Considerations

- ✅ All endpoints require admin authentication
- ✅ Audit logging for configuration changes
- ✅ Rate limiting (100 req/min for metrics, 10 req/min for mutations)
- ✅ Sensitive data (queries) are parameterized in logs
- ✅ Redis keys are namespaced to prevent conflicts

---

## 📝 Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| TEL_001 | 403 | Telemetry access denied |
| TEL_002 | 400 | Invalid time range |
| TEL_003 | 503 | Telemetry service unavailable |
| TEL_004 | 400 | Invalid metric name |
| ADM_001 | 403 | Admin access required |

---

**Document Version:** 1.0  
**Last Updated:** December 6, 2025  
**Status:** ✅ Complete
