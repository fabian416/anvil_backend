# FRONTEND_USER_MARKETS

## User Markets Module

**User Type:** Authenticated User  
**Module:** Markets - Advanced Protocol Discovery & Analytics  
**Route:** `/markets`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Markets** - Advanced Protocol Discovery with ML Risk & GraphRAG Search

### Description
Comprehensive markets module providing protocol discovery, advanced filtering, GraphRAG-powered search, ML risk scoring, and detailed protocol analytics. Enables users to find and analyze DeFi protocols based on multiple criteria.

### Key Capabilities
- ✅ Protocol listing with pagination
- ✅ Advanced filtering (chain, category, TVL, risk)
- ✅ GraphRAG hybrid search
- ✅ ML risk scores for all protocols
- ✅ Similar protocol suggestions
- ✅ Protocol comparison (2-5 protocols)
- ✅ Detailed protocol analytics
- ✅ Real-time market data

---

## 🔌 API Integration

### Advanced Markets Service

```typescript
// POST /api/v1/markets/advanced-search
interface AdvancedMarketsSearchRequest {
  query?: string; // Natural language or protocol name
  chains?: string[];
  categories?: string[];
  min_tvl?: number;
  max_tvl?: number;
  min_risk_score?: number;
  max_risk_score?: number;
  sort_by?: 'tvl' | 'apy' | 'risk' | 'volume';
  sort_order?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  enable_graphrag?: boolean;
}

interface AdvancedMarketsSearchResponse {
  protocols: ProtocolResult[];
  total: number;
  filters_applied: Record<string, any>;
  search_metadata?: {
    search_type: 'semantic' | 'graph' | 'hybrid';
    query_expanded: boolean;
  };
}

interface ProtocolResult {
  protocol_id: string;
  protocol_name: string;
  chain: string;
  category: string;
  tvl_usd: number;
  apy_supply: number | null;
  risk_score: number; // 0-10 (ML-powered)
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  audit_count: number;
  logo_url: string | null;
  similarity_score?: number; // If GraphRAG search
}

const advancedSearch = async (
  filters: AdvancedMarketsSearchRequest
): Promise<AdvancedMarketsSearchResponse> => {
  const response = await api.post('/api/v1/markets/advanced-search', filters);
  return response.data;
};
```

### Protocol Comparison

```typescript
// POST /api/v1/comparison/protocols
// See FRONTEND_USER_PROTOCOL_COMPARISON.md for full details

const compareProtocols = async (
  protocolIds: string[],
  dimensions?: string[]
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', {
    protocol_ids: protocolIds,
    dimensions,
  });
  return response.data;
};
```

---

## 🎨 React Hooks

### useAdvancedMarkets Hook

```typescript
export function useAdvancedMarkets(filters: AdvancedMarketsSearchRequest) {
  const { data, isLoading } = useQuery({
    queryKey: ['advanced-markets', filters],
    queryFn: async () => {
      const response = await api.post('/api/v1/markets/advanced-search', filters);
      return response.data;
    },
    enabled: Object.keys(filters).length > 0,
  });
  
  return {
    protocols: data?.protocols || [],
    total: data?.total || 0,
    metadata: data?.search_metadata,
    isLoading,
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Markets*  
*Backend Status: ✅ 100% Implemented (1 endpoint + comparison)*  
*Frontend Status: ✅ Ready for Implementation*
