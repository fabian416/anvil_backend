# FRONTEND_ML_NETWORK

## ML Network Analysis Module

**User Type:** Authenticated User  
**Module:** ML Network - Advanced Graph Algorithms & Network Analysis  
**Route:** `/ml/network`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**ML Network Analysis** - Advanced DeFi Network Analysis

### Description
Advanced graph algorithms for analyzing the DeFi protocol network, including PageRank importance scoring, community detection, centrality metrics, and contagion simulation.

### Key Capabilities
- ✅ PageRank importance calculation
- ✅ Community/cluster detection
- ✅ Centrality metrics (degree, betweenness, closeness, eigenvector)
- ✅ Contagion simulation
- ✅ Network propagation analysis

---

## 🔌 API Integration

### 1. Calculate PageRank

```typescript
// GET /api/v1/ml/network/pagerank
interface PageRankParams {
  damping_factor?: number; // Default: 0.85, range: 0-1
  max_iterations?: number; // Default: 100, range: 10-500
}

interface PageRankResponse {
  protocol_id: string;
  protocol_name: string;
  pagerank_score: number;
  rank: number;
  in_degree: number;
  out_degree: number;
}

interface PageRankListResponse {
  results: PageRankResponse[];
  total: number;
}

const calculatePageRank = async (params: PageRankParams = {}): Promise<PageRankListResponse> => {
  const response = await api.get('/api/v1/ml/network/pagerank', {
    params,
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 2. Detect Communities

```typescript
// GET /api/v1/ml/network/communities
interface CommunityResponse {
  community_id: number;
  protocols: string[];
  size: number;
  density: number;
  description: string;
}

interface CommunityListResponse {
  communities: CommunityResponse[];
  total_communities: number;
}

const detectCommunities = async (algorithm: string = 'label_propagation'): Promise<CommunityListResponse> => {
  const response = await api.get('/api/v1/ml/network/communities', {
    params: { algorithm },
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 3. Calculate Centrality

```typescript
// GET /api/v1/ml/network/centrality
interface CentralityResponse {
  protocol_id: string;
  protocol_name: string;
  degree_centrality: number;
  betweenness_centrality: number;
  closeness_centrality: number;
  eigenvector_centrality: number;
  importance_score: number;
}

const calculateCentrality = async (protocolId?: string): Promise<{results: CentralityResponse[], total: number}> => {
  const response = await api.get('/api/v1/ml/network/centrality', {
    params: protocolId ? { protocol_id: protocolId } : {},
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 4. Simulate Contagion

```typescript
// GET /api/v1/ml/network/contagion/{protocol_id}
interface ContagionSimulationResponse {
  origin_protocol_id: string;
  origin_protocol_name: string;
  affected_protocols: string[];
  cascade_depth: number;
  total_affected: number;
  total_tvl_at_risk: number;
  risk_score: number;
}

const simulateContagion = async (
  protocolId: string,
  propagationProbability: number = 0.8,
  maxDepth: number = 5
): Promise<ContagionSimulationResponse> => {
  const response = await api.get(`/api/v1/ml/network/contagion/${protocolId}`, {
    params: {
      propagation_probability: propagationProbability,
      max_depth: maxDepth
    },
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function usePageRank(params: PageRankParams = {}) {
  return useQuery({
    queryKey: ['ml', 'network', 'pagerank', params],
    queryFn: () => calculatePageRank(params),
  });
}

export function useCommunities(algorithm: string = 'label_propagation') {
  return useQuery({
    queryKey: ['ml', 'network', 'communities', algorithm],
    queryFn: () => detectCommunities(algorithm),
  });
}

export function useCentrality(protocolId?: string) {
  return useQuery({
    queryKey: ['ml', 'network', 'centrality', protocolId],
    queryFn: () => calculateCentrality(protocolId),
  });
}

export function useContagionSimulation() {
  return useMutation({
    mutationFn: ({ protocolId, probability, depth }: { 
      protocolId: string; 
      probability?: number; 
      depth?: number;
    }) => simulateContagion(protocolId, probability, depth),
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: ML Network Analysis*  
*Backend Status: ✅ 100% Implemented (4 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
