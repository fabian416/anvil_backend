# FRONTEND_USER_SEARCH

## Search History & Discovery Module

**User Type:** Authenticated User  
**Module:** Search - History, Suggestions, Analytics  
**Route:** `/search`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Search History & Discovery** - Intelligent Search Management & Analytics

### Description
Comprehensive search management system providing history tracking, intelligent suggestions, popular queries, search analytics, and history management with privacy controls.

### Key Capabilities
- ✅ Track search history automatically
- ✅ Get intelligent search suggestions
- ✅ View popular/trending queries
- ✅ Delete specific search entries
- ✅ Clear all search history
- ✅ Search analytics and insights

---

## 🔌 API Integration

### 1. Get Search History

```typescript
// GET /api/v1/search/history
// Description: Retrieve user's recent search history
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - limit?: number - Max entries (default: 10, max: 50)
//   - search_type?: string - Filter by type (graphrag, protocol, token, general)

interface SearchHistoryEntry {
  id: string;
  query: string;
  type: 'graphrag' | 'protocol' | 'token' | 'general';
  results_count: number;
  filters: Record<string, any>;
  created_at: string; // ISO 8601
}

interface SearchHistoryResponse {
  history: SearchHistoryEntry[];
  total: number;
}

const getSearchHistory = async (
  limit: number = 10,
  searchType?: string
): Promise<SearchHistoryResponse> => {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (searchType) params.append('search_type', searchType);
  
  const response = await api.get(`/api/v1/search/history?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/search/history?limit=20&search_type=protocol

// Example Response (200 OK):
{
  "history": [
    {
      "id": "hist-123e4567",
      "query": "uniswap v3 liquidity pools",
      "type": "protocol",
      "results_count": 15,
      "filters": {
        "chains": ["ethereum"],
        "min_tvl": 1000000
      },
      "created_at": "2025-12-01T12:00:00Z"
    },
    {
      "id": "hist-234e5678",
      "query": "aave lending rates",
      "type": "graphrag",
      "results_count": 8,
      "filters": {},
      "created_at": "2025-12-01T11:30:00Z"
    }
  ],
  "total": 2
}
```

---

### 2. Get Search Suggestions

```typescript
// GET /api/v1/search/suggestions
// Description: Get search suggestions based on history
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - prefix: string - Search prefix (required, min 1 char)
//   - limit?: number - Max suggestions (default: 5, max: 10)

interface SearchSuggestionsResponse {
  suggestions: string[];
  prefix: string;
}

const getSearchSuggestions = async (
  prefix: string,
  limit: number = 5
): Promise<SearchSuggestionsResponse> => {
  const params = new URLSearchParams({
    prefix,
    limit: limit.toString()
  });
  
  const response = await api.get(`/api/v1/search/suggestions?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/search/suggestions?prefix=uni&limit=5

// Example Response (200 OK):
{
  "suggestions": [
    "uniswap v3 liquidity pools",
    "uniswap v2 vs v3",
    "uniswap governance",
    "uniswap token price",
    "uniswap fees"
  ],
  "prefix": "uni"
}

// Example Error Response (400 Bad Request):
{
  "error": {
    "code": "INVALID_PREFIX",
    "message": "Prefix must be at least 1 character",
    "details": {}
  }
}
```

---

### 3. Get Popular Queries

```typescript
// GET /api/v1/search/popular
// Description: Get user's most popular search queries
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - limit?: number - Max queries (default: 5, max: 20)
//   - days?: number - Look back period (default: 30, max: 90)

interface PopularQuery {
  query: string;
  count: number;
  last_searched_at: string;
}

interface PopularQueriesResponse {
  popular_queries: PopularQuery[];
  period_days: number;
}

const getPopularQueries = async (
  limit: number = 5,
  days: number = 30
): Promise<PopularQueriesResponse> => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    days: days.toString()
  });
  
  const response = await api.get(`/api/v1/search/popular?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/search/popular?limit=10&days=30

// Example Response (200 OK):
{
  "popular_queries": [
    {
      "query": "ethereum gas fees",
      "count": 15,
      "last_searched_at": "2025-12-01T10:00:00Z"
    },
    {
      "query": "defi yield farming",
      "count": 12,
      "last_searched_at": "2025-11-30T15:30:00Z"
    },
    {
      "query": "aave v3",
      "count": 10,
      "last_searched_at": "2025-11-29T09:15:00Z"
    }
  ],
  "period_days": 30
}
```

---

### 4. Delete Search Entry

```typescript
// DELETE /api/v1/search/history/{search_id}
// Description: Delete a specific search history entry
// Authentication: Required (Bearer token)

interface DeleteSearchResponse {
  success: boolean;
  message: string;
}

const deleteSearchEntry = async (searchId: string): Promise<DeleteSearchResponse> => {
  const response = await api.delete(`/api/v1/search/history/${searchId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// DELETE /api/v1/search/history/hist-123e4567

// Example Response (200 OK):
{
  "success": true,
  "message": "Search deleted"
}

// Example Error Response (404 Not Found):
{
  "success": false,
  "message": "Search not found"
}
```

---

### 5. Clear Search History

```typescript
// DELETE /api/v1/search/history
// Description: Clear user's search history
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - search_type?: string - Clear only specific type (optional)

interface ClearHistoryResponse {
  success: boolean;
  cleared_count: number;
  message: string;
}

const clearSearchHistory = async (
  searchType?: string
): Promise<ClearHistoryResponse> => {
  const params = searchType 
    ? new URLSearchParams({ search_type: searchType })
    : new URLSearchParams();
  
  const response = await api.delete(`/api/v1/search/history?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// DELETE /api/v1/search/history?search_type=protocol

// Example Response (200 OK):
{
  "success": true,
  "cleared_count": 45,
  "message": "Cleared 45 searches"
}

// Clear all history:
// DELETE /api/v1/search/history
{
  "success": true,
  "cleared_count": 120,
  "message": "Cleared 120 searches"
}
```

---

### 6. Get Search Analytics

```typescript
// GET /api/v1/search/analytics
// Description: Get search analytics and insights
// Authentication: Required (Bearer token)
//
// Query Parameters:
//   - days?: number - Look back period (default: 30, max: 90)

interface SearchAnalytics {
  total_searches: number;
  by_type: Record<string, number>;
  by_day: Array<{ date: string; count: number }>;
  top_filters: Record<string, number>;
  avg_results_per_search: number;
}

interface SearchAnalyticsResponse {
  analytics: SearchAnalytics;
  period_days: number;
}

const getSearchAnalytics = async (
  days: number = 30
): Promise<SearchAnalyticsResponse> => {
  const params = new URLSearchParams({ days: days.toString() });
  
  const response = await api.get(`/api/v1/search/analytics?${params}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
// GET /api/v1/search/analytics?days=30

// Example Response (200 OK):
{
  "analytics": {
    "total_searches": 250,
    "by_type": {
      "protocol": 120,
      "graphrag": 80,
      "token": 40,
      "general": 10
    },
    "by_day": [
      { "date": "2025-12-01", "count": 15 },
      { "date": "2025-11-30", "count": 12 },
      { "date": "2025-11-29", "count": 18 }
    ],
    "top_filters": {
      "chains.ethereum": 100,
      "chains.polygon": 45,
      "min_tvl": 80
    },
    "avg_results_per_search": 12.5
  },
  "period_days": 30
}
```

---

## 🔗 React Hooks

### useSearchHistory Hook

```typescript
export function useSearchHistory(searchType?: string) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['search', 'history', searchType],
    queryFn: () => getSearchHistory(20, searchType),
  });
  
  return {
    history: data?.history || [],
    total: data?.total || 0,
    isLoading,
    error,
  };
}

// Usage:
const { history, isLoading } = useSearchHistory('protocol');
```

### useSearchSuggestions Hook

```typescript
export function useSearchSuggestions(prefix: string) {
  const { data } = useQuery({
    queryKey: ['search', 'suggestions', prefix],
    queryFn: () => getSearchSuggestions(prefix, 5),
    enabled: prefix.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  return {
    suggestions: data?.suggestions || [],
  };
}

// Usage:
const debouncedQuery = useDebounce(query, 300);
const { suggestions } = useSearchSuggestions(debouncedQuery);
```

### usePopularQueries Hook

```typescript
export function usePopularQueries(days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['search', 'popular', days],
    queryFn: () => getPopularQueries(10, days),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
  
  return {
    popularQueries: data?.popular_queries || [],
    isLoading,
  };
}

// Usage:
const { popularQueries } = usePopularQueries(30);
```

### useDeleteSearch Hook

```typescript
export function useDeleteSearch() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteSearchEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'history'] });
      toast.success('Search deleted');
    },
  });
}

// Usage:
const deleteSearch = useDeleteSearch();
deleteSearch.mutate('hist-123e4567');
```

### useClearHistory Hook

```typescript
export function useClearHistory() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: clearSearchHistory,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['search'] });
      toast.success(`Cleared ${data.cleared_count} searches`);
    },
  });
}

// Usage:
const clearHistory = useClearHistory();
clearHistory.mutate(); // Clear all
clearHistory.mutate('protocol'); // Clear specific type
```

### useSearchAnalytics Hook

```typescript
export function useSearchAnalytics(days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['search', 'analytics', days],
    queryFn: () => getSearchAnalytics(days),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
  
  return {
    analytics: data?.analytics,
    isLoading,
  };
}

// Usage:
const { analytics } = useSearchAnalytics(30);
```

---

## 🎨 React Components

### SearchHistoryList Component

```typescript
export function SearchHistoryList() {
  const { history, isLoading } = useSearchHistory();
  const deleteSearch = useDeleteSearch();
  
  if (isLoading) return <LoadingSpinner />;
  
  if (history.length === 0) {
    return <EmptyState message="No search history yet" />;
  }
  
  return (
    <div className="search-history">
      <h3>Recent Searches</h3>
      <ul>
        {history.map(entry => (
          <li key={entry.id} className="history-entry">
            <div className="query">{entry.query}</div>
            <div className="meta">
              <span className="type">{entry.type}</span>
              <span className="results">{entry.results_count} results</span>
              <span className="date">{formatDate(entry.created_at)}</span>
            </div>
            <button
              onClick={() => deleteSearch.mutate(entry.id)}
              className="delete-btn"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### SearchWithSuggestions Component

```typescript
export function SearchWithSuggestions({ onSearch }: { onSearch: (query: string) => void }) {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);
  const { suggestions } = useSearchSuggestions(debouncedQuery);
  
  return (
    <div className="search-with-suggestions">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search protocols, tokens, strategies..."
        onKeyDown={(e) => e.key === 'Enter' && onSearch(query)}
      />
      
      {suggestions.length > 0 && (
        <div className="suggestions">
          {suggestions.map((suggestion, i) => (
            <div
              key={i}
              className="suggestion"
              onClick={() => {
                setQuery(suggestion);
                onSearch(suggestion);
              }}
            >
              {suggestion}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### PopularSearches Component

```typescript
export function PopularSearches({ onSelectQuery }: { onSelectQuery: (query: string) => void }) {
  const { popularQueries, isLoading } = usePopularQueries(30);
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div className="popular-searches">
      <h3>Trending Searches</h3>
      <div className="queries">
        {popularQueries.map((item, i) => (
          <button
            key={i}
            className="popular-query"
            onClick={() => onSelectQuery(item.query)}
          >
            <span className="query">{item.query}</span>
            <span className="count">{item.count}×</span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: Search with Auto-Suggestions

```
1. User focuses on search input
   ↓
2. User types "uni" (3 characters)
   ↓
3. GET /api/v1/search/suggestions?prefix=uni&limit=5
   ↓
4. Dropdown shows suggestions:
   - "uniswap v3 liquidity pools"
   - "uniswap v2 vs v3"
   - etc.
   ↓
5. User clicks suggestion OR continues typing
   ↓
6. Search executed with selected/typed query
   ↓
7. Search automatically saved to history
```

### Flow 2: View & Manage Search History

```
1. User clicks "Search History" sidebar
   ↓
2. GET /api/v1/search/history?limit=50
   ↓
3. Display chronological list of searches
   ↓
4. User hovers over unwanted search
   ↓
5. Click "×" delete button
   ↓
6. DELETE /api/v1/search/history/{search_id}
   ↓
7. Entry removed from list
   ↓
8. OR user clicks "Clear All History"
   ↓
9. DELETE /api/v1/search/history
   ↓
10. All searches cleared
```

### Flow 3: Analytics & Insights

```
1. User opens "Search Analytics" page
   ↓
2. GET /api/v1/search/analytics?days=30
   ↓
3. Display visualizations:
   - Total searches count
   - Breakdown by type (pie chart)
   - Searches over time (line chart)
   - Most used filters (bar chart)
   ↓
4. User can adjust time period (7, 30, 90 days)
   ↓
5. Charts update with new data
```

---

## ⚠️ Error Handling

```typescript
const handleSearchError = (error: any) => {
  switch (error.code) {
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to access search history');
      redirectToLogin();
      break;
      
    case 'INVALID_PREFIX':
      toast.error('Search query too short');
      break;
      
    case 'SEARCH_NOT_FOUND':
      toast.error('Search entry not found');
      break;
      
    case 'RATE_LIMIT_EXCEEDED':
      toast.error('Too many requests. Please wait a moment.');
      break;
      
    default:
      toast.error('Unable to access search history. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. Quick Re-Search
- User frequently searches "ethereum gas fees"
- Auto-suggestions show it immediately when typing "eth"
- One-click to execute previous search

### 2. Privacy-Conscious Users
- User wants to clear sensitive searches
- Individual delete or clear all
- Granular control by search type

### 3. Research Patterns
- User researching DeFi protocols
- Analytics show search trends
- Identify areas of interest

### 4. Power User Efficiency
- Popular searches widget on dashboard
- One-click access to frequent queries
- Streamlined workflow

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Search History & Discovery*  
*Backend Status: ✅ 100% Implemented (6 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
