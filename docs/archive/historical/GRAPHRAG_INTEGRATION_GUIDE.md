# GraphRAG Integration Guide

**Version**: 1.0  
**Last Updated**: December 1, 2025  
**Target Audience**: Frontend Developers

---

## 📋 Overview

Complete guide for integrating GraphRAG-powered protocol search, discovery, and comparison into your frontend application.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install @tanstack/react-query axios
```

### 2. Setup API Client

```typescript
// lib/graphrag-client.ts
import axios from 'axios';

const graphragClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
graphragClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default graphragClient;
```

---

## 🔍 GraphRAG Search

### Hybrid Search API

```typescript
// services/graphrag.ts
export interface HybridSearchRequest {
  query: string;  // Natural language: "safe staking on Ethereum"
  filters?: {
    risk_levels?: ('LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL')[];
    chains?: string[];
    categories?: string[];
    min_tvl?: number;
  };
  limit?: number;  // Default: 10
}

export interface SearchResult {
  protocol_id: string;
  protocol_name: string;
  similarity_score: number;  // 0-1
  risk_score: number;        // 0-10
  risk_level: string;
  tvl_usd: number;
  chain: string;
  category: string;
  why_relevant: string;
}

export const searchProtocols = async (
  request: HybridSearchRequest
): Promise<SearchResult[]> => {
  const response = await graphragClient.post(
    '/api/v1/graph/search/hybrid',
    request
  );
  return response.data.results;
};
```

### React Hook

```typescript
// hooks/useGraphRAGSearch.ts
import { useQuery } from '@tanstack/react-query';

export function useGraphRAGSearch(
  query: string,
  filters?: HybridSearchRequest['filters']
) {
  return useQuery({
    queryKey: ['graphrag-search', query, filters],
    queryFn: () => searchProtocols({ query, filters }),
    enabled: query.length >= 3,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Usage
function SearchComponent() {
  const [query, setQuery] = useState('');
  const { data, isLoading } = useGraphRAGSearch(query);
  
  return (
    <div>
      <input 
        value={query} 
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search protocols..."
      />
      {isLoading && <Spinner />}
      {data?.map(result => (
        <ProtocolCard key={result.protocol_id} protocol={result} />
      ))}
    </div>
  );
}
```

---

## 🔗 Similar Protocols

```typescript
export const findSimilarProtocols = async (
  protocol_id: string,
  limit: number = 5
): Promise<SearchResult[]> => {
  const response = await graphragClient.post(
    '/api/v1/graph/search/similar-protocols',
    { protocol_id, limit }
  );
  return response.data.similar_protocols;
};

// Hook
export function useSimilarProtocols(protocol_id: string) {
  return useQuery({
    queryKey: ['similar-protocols', protocol_id],
    queryFn: () => findSimilarProtocols(protocol_id),
  });
}
```

---

## ⚖️ Protocol Comparison

```typescript
export const compareProtocols = async (
  protocol_ids: string[]
): Promise<ComparisonResult> => {
  const response = await graphragClient.post(
    '/api/v1/comparison/protocols',
    { protocol_ids }
  );
  return response.data;
};

// Hook
export function useProtocolComparison(protocol_ids: string[]) {
  return useQuery({
    queryKey: ['comparison', protocol_ids.sort().join(',')],
    queryFn: () => compareProtocols(protocol_ids),
    enabled: protocol_ids.length >= 2,
  });
}
```

---

## 🎯 Best Practices

### 1. Debounce Search Queries

```typescript
import { useDebouncedValue } from '@/hooks/useDebounce';

function SearchInput() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebouncedValue(query, 300);
  const { data } = useGraphRAGSearch(debouncedQuery);
  
  // Search triggers after 300ms of no typing
}
```

### 2. Cache Aggressively

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      cacheTime: 10 * 60 * 1000,     // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
});
```

### 3. Handle Errors Gracefully

```typescript
const { data, error, isError } = useGraphRAGSearch(query);

if (isError) {
  return (
    <ErrorState 
      message="Search failed. Please try again."
      retry={() => refetch()}
    />
  );
}
```

---

## 📊 Performance Tips

- **Prefetch Popular Queries**: Warm cache on mount
- **Virtualize Long Lists**: Use react-window for 50+ results
- **Show Skeleton Loaders**: Better UX than spinners
- **Implement Pagination**: Load 10-20 results at a time

---

*Guide Version: 1.0*  
*For complete API reference, see: API_REFERENCE_GRAPHRAG.md*
