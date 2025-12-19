# FRONTEND_ADMIN_DISTILLATION

## Admin Knowledge Distillation Module

**User Type:** Admin Only  
**Module:** Admin Distillation - Knowledge Caching & AI Response Optimization  
**Route:** `/admin/distillation`  
**Platform:** Web (Admin Dashboard)  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Admin Distillation** - Manage AI Knowledge Distillation, Caching, and Response Optimization

### Description
Advanced admin interface for managing AI knowledge distillation system, including static response templates, caching strategies, telemetry monitoring, and performance optimization.

### Key Capabilities
- ✅ Manage static response templates
- ✅ Configure distillation settings
- ✅ Monitor cache performance
- ✅ Invalidate cached responses
- ✅ View telemetry and analytics
- ✅ Optimize AI response times

---

## 🔌 API Integration

### Static Responses

#### 1. Create Static Response

```typescript
// POST /api/v1/admin/distillation/static-responses
// Description: Create pre-defined response template for common queries
// Authentication: Required (Admin role)

interface StaticResponseCreate {
  intent: string; // Query intent classification
  variant: string; // Response variation identifier
  response_template: string; // Template with {{variables}}
  template_variables?: Record<string, any>; // Variable definitions
  data_source?: string; // Where to fetch dynamic data
  conditions?: Record<string, any>; // Conditions for activation
  priority?: number; // Priority when multiple match
  is_active?: boolean;
}

const createStaticResponse = async (
  data: StaticResponseCreate
): Promise<StaticResponseResponse> => {
  const response = await api.post(
    '/api/v1/admin/distillation/static-responses',
    data
  );
  return response.data;
};

// Example Request:
{
  "intent": "get_protocol_tvl",
  "variant": "aave_v3",
  "response_template": "Aave V3 currently has {{tvl_formatted}} in total value locked across {{chain_count}} chains.",
  "template_variables": {
    "tvl_formatted": "$.tvl",
    "chain_count": "$.chains.length"
  },
  "data_source": "defi_llama_api",
  "priority": 10,
  "is_active": true
}

// Example Response (201 Created):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "intent": "get_protocol_tvl",
  "variant": "aave_v3",
  "response_template": "Aave V3 currently has {{tvl_formatted}}...",
  "priority": 10,
  "is_active": true,
  "created_at": "2025-12-01T12:00:00Z",
  "updated_at": "2025-12-01T12:00:00Z"
}
```

#### 2. List Static Responses

```typescript
// GET /api/v1/admin/distillation/static-responses?intent=get_protocol_tvl&is_active=true
// Description: List all static response templates
// Authentication: Required (Admin role)

const listStaticResponses = async (filters?: {
  intent?: string;
  is_active?: boolean;
}): Promise<StaticResponseResponse[]> => {
  const response = await api.get('/api/v1/admin/distillation/static-responses', {
    params: filters
  });
  return response.data;
};
```

#### 3. Update Static Response

```typescript
// PATCH /api/v1/admin/distillation/static-responses/{response_id}
// Description: Update static response template
// Authentication: Required (Admin role)

const updateStaticResponse = async (
  responseId: string,
  updates: Partial<StaticResponseCreate>
): Promise<StaticResponseResponse> => {
  const response = await api.patch(
    `/api/v1/admin/distillation/static-responses/${responseId}`,
    updates
  );
  return response.data;
};
```

#### 4. Delete Static Response

```typescript
// DELETE /api/v1/admin/distillation/static-responses/{response_id}
// Description: Delete static response template
// Authentication: Required (Admin role)

const deleteStaticResponse = async (responseId: string): Promise<void> => {
  await api.delete(`/api/v1/admin/distillation/static-responses/${responseId}`);
};
```

---

### Distillation Configuration

#### 5. Get Distillation Config

```typescript
// GET /api/v1/admin/distillation/config
// Description: Get current distillation system configuration
// Authentication: Required (Admin role)

interface DistillationConfigResponse {
  cache_ttl_seconds: number;
  max_cache_size_mb: number;
  enable_static_responses: boolean;
  enable_semantic_cache: boolean;
  similarity_threshold: number;
  enable_telemetry: boolean;
}

const getDistillationConfig = async (): Promise<DistillationConfigResponse> => {
  const response = await api.get('/api/v1/admin/distillation/config');
  return response.data;
};

// Example Response (200 OK):
{
  "cache_ttl_seconds": 3600,
  "max_cache_size_mb": 500,
  "enable_static_responses": true,
  "enable_semantic_cache": true,
  "similarity_threshold": 0.85,
  "enable_telemetry": true
}
```

#### 6. Update Distillation Config

```typescript
// PATCH /api/v1/admin/distillation/config
// Description: Update distillation configuration
// Authentication: Required (Admin role)

interface DistillationConfigUpdate {
  cache_ttl_seconds?: number;
  max_cache_size_mb?: number;
  enable_static_responses?: boolean;
  enable_semantic_cache?: boolean;
  similarity_threshold?: number;
}

const updateDistillationConfig = async (
  updates: DistillationConfigUpdate
): Promise<DistillationConfigResponse> => {
  const response = await api.patch('/api/v1/admin/distillation/config', updates);
  return response.data;
};
```

---

### Cache Management

#### 7. Get Cache Stats

```typescript
// GET /api/v1/admin/distillation/cache/stats
// Description: Get cache performance statistics
// Authentication: Required (Admin role)

interface CacheStatsResponse {
  total_entries: number;
  cache_size_mb: number;
  hit_rate: number; // Percentage
  miss_rate: number; // Percentage
  avg_response_time_ms: number;
  cached_avg_response_time_ms: number;
  uncached_avg_response_time_ms: number;
  oldest_entry_age_seconds: number;
}

const getCacheStats = async (): Promise<CacheStatsResponse> => {
  const response = await api.get('/api/v1/admin/distillation/cache/stats');
  return response.data;
};

// Example Response (200 OK):
{
  "total_entries": 1250,
  "cache_size_mb": 125.5,
  "hit_rate": 78.5,
  "miss_rate": 21.5,
  "avg_response_time_ms": 450,
  "cached_avg_response_time_ms": 85,
  "uncached_avg_response_time_ms": 1200,
  "oldest_entry_age_seconds": 3200
}
```

#### 8. Invalidate Cache

```typescript
// POST /api/v1/admin/distillation/cache/invalidate
// Description: Invalidate cached responses by pattern or all
// Authentication: Required (Admin role)

interface CacheInvalidateRequest {
  pattern?: string; // Regex pattern to match cache keys
  intent?: string; // Invalidate by intent
  invalidate_all?: boolean; // Clear entire cache
}

const invalidateCache = async (
  data: CacheInvalidateRequest
): Promise<{ invalidated_count: number }> => {
  const response = await api.post('/api/v1/admin/distillation/cache/invalidate', data);
  return response.data;
};

// Example Request (invalidate by intent):
{
  "intent": "get_protocol_tvl"
}

// Example Response (200 OK):
{
  "invalidated_count": 45
}
```

---

### Telemetry & Analytics

#### 9. Get Distillation Telemetry

```typescript
// GET /api/v1/admin/distillation/telemetry?start_date=2025-11-01&end_date=2025-12-01
// Description: Get telemetry data for distillation system
// Authentication: Required (Admin role)

interface DistillationTelemetryResponse {
  total_queries: number;
  static_responses_used: number;
  semantic_cache_hits: number;
  semantic_cache_misses: number;
  avg_response_time_ms: number;
  cost_savings_usd: number; // Estimated savings from caching
  by_intent: Record<string, {
    query_count: number;
    cache_hit_rate: number;
    avg_response_time_ms: number;
  }>;
}

const getDistillationTelemetry = async (
  startDate: string,
  endDate: string
): Promise<DistillationTelemetryResponse> => {
  const response = await api.get('/api/v1/admin/distillation/telemetry', {
    params: { start_date: startDate, end_date: endDate }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "total_queries": 15000,
  "static_responses_used": 3500,
  "semantic_cache_hits": 8200,
  "semantic_cache_misses": 3300,
  "avg_response_time_ms": 385,
  "cost_savings_usd": 127.50,
  "by_intent": {
    "get_protocol_tvl": {
      "query_count": 5200,
      "cache_hit_rate": 85.2,
      "avg_response_time_ms": 120
    },
    "compare_protocols": {
      "query_count": 3800,
      "cache_hit_rate": 72.5,
      "avg_response_time_ms": 450
    }
  }
}
```

#### 10. Get Distillation Summary

```typescript
// GET /api/v1/admin/distillation/summary
// Description: Get high-level summary of distillation system
// Authentication: Required (Admin role)

interface DistillationSummaryResponse {
  status: 'healthy' | 'degraded' | 'critical';
  active_static_responses: number;
  cache_hit_rate_7d: number;
  avg_response_time_7d: number;
  cost_savings_30d: number;
  recommendations: string[];
}

const getDistillationSummary = async (): Promise<DistillationSummaryResponse> => {
  const response = await api.get('/api/v1/admin/distillation/summary');
  return response.data;
};

// Example Response (200 OK):
{
  "status": "healthy",
  "active_static_responses": 127,
  "cache_hit_rate_7d": 78.5,
  "avg_response_time_7d": 420,
  "cost_savings_30d": 485.25,
  "recommendations": [
    "Consider adding static response for 'get_swap_quote' intent (high volume)",
    "Cache hit rate below 80% - review similarity threshold",
    "5 static responses have not been used in 30 days - consider archiving"
  ]
}
```

---

## 🔗 React Hooks

### useDistillationManagement Hook

```typescript
export function useDistillationManagement() {
  const queryClient = useQueryClient();
  
  const { data: config } = useQuery({
    queryKey: ['distillation-config'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/distillation/config');
      return response.data;
    },
  });
  
  const { data: stats } = useQuery({
    queryKey: ['distillation-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/distillation/cache/stats');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });
  
  const updateConfig = useMutation({
    mutationFn: async (updates: DistillationConfigUpdate) => {
      const response = await api.patch('/api/v1/admin/distillation/config', updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['distillation-config'] });
      toast.success('Configuration updated successfully');
    },
  });
  
  const invalidateCache = useMutation({
    mutationFn: async (data: CacheInvalidateRequest) => {
      const response = await api.post('/api/v1/admin/distillation/cache/invalidate', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['distillation-stats'] });
      toast.success(`Invalidated ${data.invalidated_count} cache entries`);
    },
  });
  
  return {
    config,
    stats,
    updateConfig: updateConfig.mutate,
    invalidateCache: invalidateCache.mutate,
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Admin Distillation*  
*Backend Status: ✅ 100% Implemented (10 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
