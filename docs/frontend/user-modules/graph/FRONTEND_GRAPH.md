# FRONTEND_GRAPH

## GraphRAG & Analytics Module

**User Type:** Authenticated User  
**Module:** GraphRAG - Knowledge Graph Search & Analytics  
**Route:** `/graph`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**GraphRAG** - Advanced Knowledge Graph Search & Analytics

### Description
Enterprise-grade knowledge graph system providing hybrid search (vector + graph), protocol analytics, dependency mapping, and real-time monitoring for DeFi intelligence.

### Key Capabilities
- ✅ Hybrid semantic + graph search
- ✅ Protocol similarity matching
- ✅ Contextual search with preferences
- ✅ Graph analytics & insights
- ✅ Integrity validation
- ✅ Embedding generation
- ✅ Performance monitoring

---

## 🔌 API Integration

### Graph Search Endpoints

#### 1. Hybrid Search

```typescript
// POST /api/v1/graph/search/hybrid
// Description: Semantic + graph hybrid search
// Authentication: Required (Bearer token)

interface HybridSearchRequest {
  query: string;
  limit?: number;
  include_risks?: boolean;
  include_dependencies?: boolean;
  similarity_threshold?: number; // 0-1
}

interface HybridSearchResponse {
  query: string;
  results: HybridSearchResult[];
  total: number;
  metadata: Record<string, any>;
}

interface HybridSearchResult {
  protocol_id: string;
  protocol_name: string;
  score: number; // Combined score
  vector_similarity: number; // Semantic similarity
  graph_importance: number; // Graph centrality
  context: ProtocolContext;
  risk_info?: RiskInfo;
}

interface ProtocolContext {
  tvl: number;
  category: string;
  dependent_count: number;
  degree: number;
  audit_count: number;
  chain_count: number;
  dependencies?: string[];
}

const hybridSearch = async (request: HybridSearchRequest): Promise<HybridSearchResponse> => {
  const response = await api.post('/api/v1/graph/search/hybrid', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Request:
{
  "query": "decentralized lending protocol",
  "limit": 10,
  "include_risks": true,
  "include_dependencies": true,
  "similarity_threshold": 0.5
}

// Example Response (200 OK):
{
  "query": "decentralized lending protocol",
  "results": [
    {
      "protocol_id": "aave-uuid",
      "protocol_name": "Aave V3",
      "score": 0.92,
      "vector_similarity": 0.88,
      "graph_importance": 0.96,
      "context": {
        "tvl": 5600000000,
        "category": "Lending",
        "dependent_count": 156,
        "degree": 45,
        "audit_count": 8,
        "chain_count": 7,
        "dependencies": ["chainlink", "compound"]
      },
      "risk_info": {
        "risk_score": 2.5,
        "direct_risks": ["Oracle dependency"],
        "systemic_risks": ["High TVL concentration"],
        "top_recommendation": "Monitor oracle health"
      }
    }
  ],
  "total": 10
}
```

#### 2. Find Similar Protocols

```typescript
// POST /api/v1/graph/search/similar
// Description: Find protocols similar to reference
// Authentication: Required (Bearer token)

interface SimilarProtocolsRequest {
  protocol_id: string;
  limit?: number;
}

interface SimilarProtocolsResponse {
  reference_protocol_id: string;
  results: HybridSearchResult[];
  total: number;
}

const findSimilarProtocols = async (
  protocolId: string,
  limit: number = 10
): Promise<SimilarProtocolsResponse> => {
  const response = await api.post('/api/v1/graph/search/similar', {
    protocol_id: protocolId,
    limit
  }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

#### 3. Contextual Search

```typescript
// POST /api/v1/graph/search/contextual
// Description: Search with user preference filtering
// Authentication: Required (Bearer token)

interface ContextualSearchRequest {
  query: string;
  preferences?: {
    category?: string;
    max_risk_score?: number;
    min_tvl?: number;
  };
  limit?: number;
}

interface ContextualSearchResponse {
  query: string;
  preferences?: any;
  results: HybridSearchResult[];
  total: number;
}

const contextualSearch = async (
  request: ContextualSearchRequest
): Promise<ContextualSearchResponse> => {
  const response = await api.post('/api/v1/graph/search/contextual', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### Graph Analytics Endpoints

#### 4. Get Graph Analytics

```typescript
// GET /api/v1/graph/analytics/overview
// Description: Comprehensive graph statistics
// Authentication: Required (Bearer token)

interface GraphAnalyticsResponse {
  overview: GraphOverviewStats;
  top_protocols: TopProtocol[];
  category_distribution: Record<string, number>;
  chain_distribution: Record<string, number>;
}

interface GraphOverviewStats {
  total_nodes: number;
  total_edges: number;
  protocol_count: number;
  chain_count: number;
  category_count: number;
  avg_degree: number;
  density: number;
  last_updated: string;
}

const getGraphAnalytics = async (): Promise<GraphAnalyticsResponse> => {
  const response = await api.get('/api/v1/graph/analytics/overview', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

#### 5. Validate Graph

```typescript
// POST /api/v1/graph/analytics/validate
// Description: Run graph integrity checks
// Authentication: Required (Bearer token)

interface GraphValidationResponse {
  timestamp: string;
  checks: Record<string, ValidationIssue>;
  total_issues: number;
  is_valid: boolean;
}

interface ValidationIssue {
  passed: boolean;
  issues_found: number;
  details?: string[];
}

const validateGraph = async (): Promise<GraphValidationResponse> => {
  const response = await api.post('/api/v1/graph/analytics/validate', {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

#### 6. Generate Embeddings (Admin)

```typescript
// POST /api/v1/graph/analytics/embeddings/generate
// Description: Generate protocol embeddings
// Authentication: Required (Bearer token - Admin only)

interface EmbeddingGenerationRequest {
  limit?: number;
  force_regenerate?: boolean;
}

interface EmbeddingGenerationResponse {
  processed: number;
  skipped: number;
  errors: number;
  duration_seconds: number;
}

const generateEmbeddings = async (
  request: EmbeddingGenerationRequest
): Promise<EmbeddingGenerationResponse> => {
  const response = await api.post('/api/v1/graph/analytics/embeddings/generate', request, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### Graph Monitoring Endpoints

#### 7. Get Cache Stats

```typescript
// GET /api/v1/graph/monitoring/cache-stats
// Description: Cache performance metrics
// Authentication: Required (Bearer token)

interface CacheStats {
  graph_cache_keys: number;
  total_keys: number;
  hits: number;
  misses: number;
  hit_rate: number;
}

interface PerformanceMetrics {
  cache_stats: CacheStats;
  message: string;
}

const getCacheStats = async (): Promise<PerformanceMetrics> => {
  const response = await api.get('/api/v1/graph/monitoring/cache-stats', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

#### 8. Clear Cache (Admin)

```typescript
// POST /api/v1/graph/monitoring/cache/clear
// Description: Clear all graph caches
// Authentication: Required (Bearer token - Admin only)

const clearCache = async (): Promise<{message: string; status: string}> => {
  const response = await api.post('/api/v1/graph/monitoring/cache/clear', {}, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function useHybridSearch() {
  return useMutation({
    mutationFn: hybridSearch,
  });
}

export function useSimilarProtocols() {
  return useMutation({
    mutationFn: (protocolId: string) => findSimilarProtocols(protocolId),
  });
}

export function useContextualSearch() {
  return useMutation({
    mutationFn: contextualSearch,
  });
}

export function useGraphAnalytics() {
  return useQuery({
    queryKey: ['graph', 'analytics'],
    queryFn: getGraphAnalytics,
    staleTime: 60000, // 1 minute
  });
}

export function useCacheStats() {
  return useQuery({
    queryKey: ['graph', 'cache-stats'],
    queryFn: getCacheStats,
    refetchInterval: 30000,
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: GraphRAG & Analytics*  
*Backend Status: ✅ 100% Implemented (8 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
