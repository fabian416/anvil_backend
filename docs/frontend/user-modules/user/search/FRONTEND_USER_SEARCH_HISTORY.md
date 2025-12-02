# FRONTEND_USER_SEARCH_HISTORY

## User Search - History & Suggestions Module

**User Type:** Authenticated User  
**Module:** Search History - Smart Search Tracking & Personalized Suggestions  
**Route:** `/search`, `/search/history`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Search History** - Intelligent Search Tracking, Autocomplete & Analytics

### Description
Comprehensive search history system that tracks all user searches (GraphRAG, protocols, tokens, general), provides intelligent autocomplete suggestions, identifies popular queries, and delivers personalized search analytics to enhance user discovery and efficiency.

### Key Capabilities
- ✅ Automatic search history tracking (all search types)
- ✅ Recent searches (last 10-100 entries)
- ✅ Smart autocomplete suggestions (based on user's history)
- ✅ Popular queries (frequency-based)
- ✅ Search type filtering (GraphRAG, protocol, token, general)
- ✅ Quick re-run past searches (one tap)
- ✅ Delete individual search entries
- ✅ Clear all history (with confirmation)
- ✅ Search analytics (by type, filters, results)
- ✅ Privacy-focused (user's data only)

---

## 👤 User Stories

### US-USER-SEARCH-001: View Recent Searches
**As a** user  
**I want to** see my recent search queries  
**So that** I can quickly re-run or reference past searches

**Acceptance Criteria:**
- Shows last 10 searches by default
- Sorted newest first
- Displays search type (GraphRAG, protocol, etc.)
- Shows result count for each search
- One-tap to re-run search

---

### US-USER-SEARCH-002: Get Smart Autocomplete
**As a** user  
**I want to** get search suggestions as I type  
**So that** I can find what I'm looking for faster

**Acceptance Criteria:**
- Suggestions appear after 1+ characters
- Shows up to 5 relevant suggestions
- Matches against user's past searches
- Sorted by frequency (most used first)
- Tap to complete query

---

### US-USER-SEARCH-003: View Popular Queries
**As a** user  
**I want to** see my most frequent searches  
**So that** I can understand my search patterns and access common queries quickly

**Acceptance Criteria:**
- Shows top 5-10 most searched queries
- Displays frequency count
- Configurable time period (7d, 30d, 90d)
- One-tap to execute

---

### US-USER-SEARCH-004: Delete Search History
**As a** user  
**I want to** delete individual or all search entries  
**So that** I can maintain privacy and clean up my history

**Acceptance Criteria:**
- Swipe to delete individual entries
- "Clear All" button with confirmation
- Filter by type (clear only GraphRAG, etc.)
- Immediate UI update

---

### US-USER-SEARCH-005: Filter by Search Type
**As a** user  
**I want to** filter history by search type  
**So that** I can find specific past searches quickly

**Acceptance Criteria:**
- Filter chips: All, GraphRAG, Protocol, Token, General
- Real-time filtering
- Shows count per type
- Persists filter selection

---

### US-USER-SEARCH-006: View Search Analytics
**As a** user  
**I want to** see analytics about my search behavior  
**So that** I can understand how I use the platform

**Acceptance Criteria:**
- Total searches in period
- Breakdown by type (pie chart)
- Average results per search
- Most common filters used
- Temporal trends (line chart)

---

## 🖼️ Wireframes

### View 1: Search History Screen (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Search History        [⚙️] │
├─────────────────────────────────────┤
│                                     │
│  [All] [GraphRAG] [Protocol] [Token]│
│                                     │
│  Recent Searches (28)               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "Aave V3 security analysis" ││
│  │      GraphRAG • 12 results      ││
│  │      2 minutes ago         [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "best yield farming pools"  ││
│  │      Protocol • 8 results       ││
│  │      1 hour ago             [↻] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "ETH"                       ││
│  │      Token • 1 result           ││
│  │      3 hours ago            [↻] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "stablecoin risks"          ││
│  │      General • 15 results       ││
│  │      Yesterday              [↻] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "Compound vs Aave"          ││
│  │      Protocol • 2 results       ││
│  │      Yesterday              [↻] ││
│  └─────────────────────────────────┘│
│                                     │
│  [Load More (23 more searches)]     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Clear All History]            ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Smart Autocomplete (In Search Bar)

```
┌─────────────────────────────────────┐
│  Search: "aave"_                    │
├─────────────────────────────────────┤
│                                     │
│  💡 Suggestions from your history:  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🔍 "Aave V3 security analysis" ││
│  │      Used 3 times               ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  🔍 "Aave lending rates"        ││
│  │      Used 2 times               ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  🔍 "Aave risk score"           ││
│  │      Used 1 time                ││
│  └─────────────────────────────────┘│
│                                     │
│  ─────────── OR ────────────        │
│                                     │
│  [Search "aave" now] →              │
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Popular Queries

```
┌─────────────────────────────────────┐
│  [←]    Popular Searches            │
├─────────────────────────────────────┤
│                                     │
│  Your Most Searched Queries         │
│  Last 30 days                       │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  1. "Aave V3 security"          ││
│  │     🔥 Searched 12 times        ││
│  │     Last: 2 hours ago      [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  2. "yield farming"             ││
│  │     🔥 Searched 8 times         ││
│  │     Last: Yesterday        [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  3. "stablecoin risks"          ││
│  │     🔥 Searched 6 times         ││
│  │     Last: 2 days ago       [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  4. "Curve Finance"             ││
│  │     🔥 Searched 5 times         ││
│  │     Last: 3 days ago       [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  5. "ETH gas fees"              ││
│  │     🔥 Searched 4 times         ││
│  │     Last: 1 week ago       [↻]  ││
│  └─────────────────────────────────┘│
│                                     │
│  Time Period: [7d] [30d] [90d]      │
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Search Analytics

```
┌─────────────────────────────────────┐
│  [←]    Search Analytics            │
├─────────────────────────────────────┤
│                                     │
│  Last 30 Days                       │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Total Searches                 ││
│  │                                 ││
│  │       156                       ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  By Type                        ││
│  │                                 ││
│  │     ╭─────────────╮             ││
│  │    ╱ GraphRAG 45% ╲            ││
│  │   │  Protocol 30%  │           ││
│  │    ╲ Token 15%    ╱            ││
│  │     ╰─────────────╯             ││
│  │      General 10%                ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Average Results                ││
│  │                                 ││
│  │       8.3 results/search        ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Most Used Filters              ││
│  │                                 ││
│  │  • risk:HIGH (23 times)         ││
│  │  • chain:ethereum (18 times)    ││
│  │  • category:lending (12 times)  ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Search Trend (Last 30d)        ││
│  │                                 ││
│  │  Searches                       ││
│  │   15├──╱╲─╱╲───╱╲──╱╲─         ││
│  │   10│ ╱  ╲   ╲ ╱  ╲ ╱  ╲        ││
│  │    5├╱    ╲───╱    ╲    ╲─      ││
│  │    0└────────────────────────    ││
│  │      Week 1  2  3  4            ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 5: Clear History Confirmation

```
┌─────────────────────────────────────┐
│                                     │
│          ⚠️  Clear History?         │
│                                     │
│  This will permanently delete       │
│  your search history.               │
│                                     │
│  You have 28 search entries.        │
│                                     │
│  Options:                           │
│  ┌─────────────────────────────────┐│
│  │  ( ) Clear all (28 entries)     ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ( ) Clear GraphRAG only (12)   ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  ( ) Clear Protocol only (8)    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Clear Selected History]       ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Cancel]                       ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Integration

### Get Search History

```typescript
// GET /api/v1/search/history?limit=10&search_type=graphrag
interface SearchHistoryResponse {
  history: SearchHistoryEntry[];
  total: number;
}

interface SearchHistoryEntry {
  id: string;
  query: string;
  type: 'graphrag' | 'protocol' | 'token' | 'general';
  results_count: number;
  filters: Record<string, any>;
  created_at: string;
}

const getSearchHistory = async (
  filters?: {
    limit?: number;
    search_type?: string;
  }
): Promise<SearchHistoryResponse> => {
  const response = await api.get('/api/v1/search/history', { 
    params: filters 
  });
  return response.data;
};
```

### Get Search Suggestions (Autocomplete)

```typescript
// GET /api/v1/search/suggestions?prefix=aave&limit=5
interface SearchSuggestionsResponse {
  suggestions: string[];
  prefix: string;
}

const getSearchSuggestions = async (
  prefix: string,
  limit: number = 5
): Promise<string[]> => {
  const response = await api.get('/api/v1/search/suggestions', {
    params: { prefix, limit },
  });
  return response.data.suggestions;
};
```

### Get Popular Queries

```typescript
// GET /api/v1/search/popular?limit=5&days=30
interface PopularQuery {
  query: string;
  count: number;
}

interface PopularQueriesResponse {
  popular_queries: PopularQuery[];
  period_days: number;
}

const getPopularQueries = async (
  limit: number = 5,
  days: number = 30
): Promise<PopularQuery[]> => {
  const response = await api.get('/api/v1/search/popular', {
    params: { limit, days },
  });
  return response.data.popular_queries;
};
```

### Delete Search Entry

```typescript
// DELETE /api/v1/search/history/:search_id
const deleteSearchEntry = async (searchId: string): Promise<void> => {
  await api.delete(`/api/v1/search/history/${searchId}`);
};
```

### Clear All History

```typescript
// DELETE /api/v1/search/history/clear?search_type=graphrag
interface ClearHistoryResponse {
  cleared: number;
  message: string;
}

const clearSearchHistory = async (
  searchType?: string
): Promise<ClearHistoryResponse> => {
  const response = await api.delete('/api/v1/search/history/clear', {
    params: searchType ? { search_type: searchType } : undefined,
  });
  return response.data;
};
```

### Get Search Analytics

```typescript
// GET /api/v1/search/analytics?days=30
interface SearchAnalytics {
  total_searches: number;
  by_type: Record<string, number>;
  average_results: number;
  most_common_filters: Array<{
    filter: string;
    count: number;
  }>;
}

const getSearchAnalytics = async (
  days: number = 30
): Promise<SearchAnalytics> => {
  const response = await api.get('/api/v1/search/analytics', {
    params: { days },
  });
  return response.data;
};
```

---

## 🎨 Motion Design

### Search History List Animation (Framer Motion)

```typescript
import { motion, AnimatePresence } from 'framer-motion';

function SearchHistoryList({ entries, onReRun, onDelete }: SearchHistoryListProps) {
  return (
    <div className="space-y-2">
      <AnimatePresence mode="popLayout">
        {entries.map((entry, index) => (
          <motion.div
            key={entry.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20, height: 0 }}
            transition={{ delay: index * 0.05 }}
            layout
          >
            <SearchHistoryCard
              entry={entry}
              onReRun={onReRun}
              onDelete={onDelete}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
```

### Autocomplete Dropdown Animation

```typescript
function AutocompleteDropdown({ suggestions, onSelect }: AutocompleteProps) {
  return (
    <AnimatePresence>
      {suggestions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="absolute top-full left-0 right-0 bg-white rounded-lg shadow-xl mt-2 overflow-hidden z-50"
        >
          {suggestions.map((suggestion, idx) => (
            <motion.div
              key={idx}
              whileHover={{ backgroundColor: '#F3F4F6' }}
              onClick={() => onSelect(suggestion)}
              className="px-4 py-3 cursor-pointer border-b last:border-b-0"
            >
              <div className="flex items-center gap-2">
                <span className="text-gray-400">🔍</span>
                <span className="text-gray-900">{suggestion}</span>
              </div>
            </motion.div>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Clear History Modal Animation

```typescript
function ClearHistoryModal({ isOpen, onClose, onConfirm }: ClearModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-xl p-6 max-w-sm mx-4 shadow-2xl"
          >
            <div className="text-center mb-4">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="text-6xl mb-3"
              >
                ⚠️
              </motion.div>
              <h3 className="text-xl font-bold">Clear History?</h3>
              <p className="text-gray-600 mt-2">
                This will permanently delete your search history.
              </p>
            </div>
            
            <div className="space-y-2">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onConfirm}
                className="w-full bg-red-600 text-white py-3 rounded-lg font-semibold"
              >
                Clear All History
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onClose}
                className="w-full bg-gray-100 text-gray-700 py-3 rounded-lg font-semibold"
              >
                Cancel
              </motion.button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

---

## 🎨 React Native Motion (Reanimated)

### Swipe to Delete Search Entry

```typescript
import Animated, {
  useAnimatedGestureHandler,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { PanGestureHandler } from 'react-native-gesture-handler';

function SearchHistoryCard({ entry, onDelete }: SearchCardProps) {
  const translateX = useSharedValue(0);
  const opacity = useSharedValue(1);
  const deleteThreshold = -100;
  
  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      // Only allow left swipe (negative translateX)
      if (event.translationX < 0) {
        translateX.value = event.translationX;
        
        // Fade out as approaching delete threshold
        const progress = Math.abs(event.translationX) / Math.abs(deleteThreshold);
        opacity.value = Math.max(0.3, 1 - progress * 0.7);
      }
    },
    onEnd: (event) => {
      if (event.translationX < deleteThreshold) {
        // Delete
        translateX.value = withTiming(-400, {}, () => {
          runOnJS(onDelete)(entry.id);
        });
        opacity.value = withTiming(0);
      } else {
        // Snap back
        translateX.value = withSpring(0);
        opacity.value = withSpring(1);
      }
    },
  });
  
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
    opacity: opacity.value,
  }));
  
  const deleteIndicatorStyle = useAnimatedStyle(() => ({
    opacity: translateX.value < -20 ? 1 : 0,
  }));
  
  return (
    <View style={styles.cardContainer}>
      <Animated.View style={[styles.deleteIndicator, deleteIndicatorStyle]}>
        <Text style={styles.deleteText}>🗑️ Delete</Text>
      </Animated.View>
      
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View style={[styles.card, animatedStyle]}>
          <SearchEntryContent entry={entry} />
        </Animated.View>
      </PanGestureHandler>
    </View>
  );
}
```

---

## 📱 Component Specifications

### SearchHistoryScreen Component

```typescript
interface SearchHistoryScreenProps {
  navigation: any;
}

function SearchHistoryScreen({ navigation }: SearchHistoryScreenProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const { history, deleteEntry, clearHistory } = useSearchHistory();
  
  const filteredHistory = selectedType
    ? history.filter((entry) => entry.type === selectedType)
    : history;
  
  return (
    <div className="p-4">
      {/* Filter chips */}
      <div className="flex gap-2 mb-4 overflow-x-auto">
        <FilterChip
          label="All"
          count={history.length}
          active={!selectedType}
          onPress={() => setSelectedType(null)}
        />
        <FilterChip
          label="GraphRAG"
          count={history.filter((e) => e.type === 'graphrag').length}
          active={selectedType === 'graphrag'}
          onPress={() => setSelectedType('graphrag')}
        />
        <FilterChip
          label="Protocol"
          count={history.filter((e) => e.type === 'protocol').length}
          active={selectedType === 'protocol'}
          onPress={() => setSelectedType('protocol')}
        />
        {/* More filter chips */}
      </div>
      
      {/* History list */}
      <SearchHistoryList
        entries={filteredHistory}
        onReRun={(entry) => navigation.navigate('Search', { query: entry.query })}
        onDelete={deleteEntry}
      />
      
      {/* Clear all button */}
      {history.length > 0 && (
        <button
          onClick={() => clearHistory()}
          className="mt-6 w-full py-3 text-red-600 font-semibold"
        >
          Clear All History
        </button>
      )}
    </div>
  );
}
```

### SearchAutocomplete Component

```typescript
interface SearchAutocompleteProps {
  query: string;
  onSelect: (suggestion: string) => void;
}

function SearchAutocomplete({ query, onSelect }: SearchAutocompleteProps) {
  const { suggestions, isLoading } = useSearchSuggestions(query);
  
  if (!query || query.length < 1 || suggestions.length === 0) {
    return null;
  }
  
  return (
    <AutocompleteDropdown
      suggestions={suggestions}
      onSelect={onSelect}
      isLoading={isLoading}
    />
  );
}
```

### PopularQueriesWidget Component

```typescript
function PopularQueriesWidget() {
  const { popularQueries } = usePopularQueries(5, 30);
  
  if (popularQueries.length === 0) return null;
  
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm">
      <h3 className="font-bold text-lg mb-3">Your Popular Searches</h3>
      <div className="space-y-2">
        {popularQueries.map((query, idx) => (
          <div
            key={idx}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">🔥</span>
              <div>
                <div className="font-medium">{query.query}</div>
                <div className="text-xs text-gray-500">
                  Searched {query.count} times
                </div>
              </div>
            </div>
            <button className="text-blue-600">↻</button>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔗 React Hooks

### useSearchHistory Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useSearchHistory(filters?: { type?: string; limit?: number }) {
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useQuery({
    queryKey: ['search-history', filters],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/history', {
        params: filters,
      });
      return response.data;
    },
  });
  
  const deleteEntry = useMutation({
    mutationFn: async (searchId: string) => {
      await api.delete(`/api/v1/search/history/${searchId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
      toast.success('Search deleted');
    },
  });
  
  const clearHistory = useMutation({
    mutationFn: async (searchType?: string) => {
      const response = await api.delete('/api/v1/search/history/clear', {
        params: searchType ? { search_type: searchType } : undefined,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['search-history'] });
      toast.success(`Cleared ${data.cleared} search entries`);
    },
  });
  
  return {
    history: data?.history || [],
    total: data?.total || 0,
    isLoading,
    deleteEntry: deleteEntry.mutate,
    clearHistory: clearHistory.mutate,
  };
}
```

### useSearchSuggestions Hook

```typescript
export function useSearchSuggestions(prefix: string, limit: number = 5) {
  const { data, isLoading } = useQuery({
    queryKey: ['search-suggestions', prefix, limit],
    queryFn: async () => {
      if (!prefix || prefix.length < 1) return { suggestions: [], prefix };
      
      const response = await api.get('/api/v1/search/suggestions', {
        params: { prefix, limit },
      });
      return response.data;
    },
    enabled: prefix.length >= 1,
    staleTime: 30000, // 30 seconds
  });
  
  return {
    suggestions: data?.suggestions || [],
    isLoading,
  };
}
```

### usePopularQueries Hook

```typescript
export function usePopularQueries(limit: number = 5, days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['popular-queries', limit, days],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/popular', {
        params: { limit, days },
      });
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
  
  return {
    popularQueries: data?.popular_queries || [],
    periodDays: data?.period_days || days,
    isLoading,
  };
}
```

### useSearchAnalytics Hook

```typescript
export function useSearchAnalytics(days: number = 30) {
  const { data, isLoading } = useQuery({
    queryKey: ['search-analytics', days],
    queryFn: async () => {
      const response = await api.get('/api/v1/search/analytics', {
        params: { days },
      });
      return response.data;
    },
    staleTime: 600000, // 10 minutes
  });
  
  return {
    analytics: data,
    isLoading,
  };
}
```

---

## 🎭 User Flows

### Flow 1: Quick Re-Run Past Search

```
1. User opens Search History screen
   ↓
2. Sees recent searches (newest first)
   ↓
3. Taps "↻" button on desired search
   ↓
4. Navigates to Search screen with pre-filled query
   ↓
5. Results load immediately
   ↓
6. User reviews results (same as original search)
```

### Flow 2: Autocomplete Search

```
1. User starts typing in search bar ("aav")
   ↓
2. After 1+ characters, suggestions appear (< 200ms)
   ↓
3. Sees personalized suggestions from history
   ↓
4. Taps preferred suggestion ("Aave V3 security")
   ↓
5. Query auto-completes in search bar
   ↓
6. User taps Search or Enter
   ↓
7. Results load
```

### Flow 3: Clear Search History

```
1. User navigates to Search History
   ↓
2. Scrolls to bottom
   ↓
3. Taps "Clear All History"
   ↓
4. Modal appears with options (All, by type)
   ↓
5. Selects "Clear GraphRAG only (12 entries)"
   ↓
6. Taps "Clear Selected History"
   ↓
7. Modal closes, history updates
   ↓
8. Toast: "Cleared 12 search entries"
   ↓
9. GraphRAG entries removed, others remain
```

---

## ⚠️ Error Handling

```typescript
const searchHistoryErrors = {
  SEARCH_001: 'Failed to load search history',
  SEARCH_002: 'Failed to delete search entry',
  SEARCH_003: 'Failed to clear history',
  SEARCH_004: 'Search entry not found',
  SEARCH_005: 'Not your search entry',
  SEARCH_006: 'Invalid search type filter',
};

// Handle delete error
try {
  await deleteSearchEntry(searchId);
} catch (error) {
  if (error.code === 'SEARCH_005') {
    toast.error('You can only delete your own searches');
  } else if (error.code === 'SEARCH_004') {
    toast.error('Search entry not found');
  } else {
    toast.error('Failed to delete search. Please try again.');
  }
}
```

---

## ♿ Accessibility

### ARIA Labels

```typescript
<button
  aria-label={`Re-run search: ${entry.query}. This search returned ${entry.results_count} results ${formatRelativeTime(entry.created_at)}`}
  onClick={() => onReRun(entry)}
>
  ↻
</button>
```

### Screen Reader Support

```typescript
<div role="list" aria-label="Search history">
  {history.map((entry) => (
    <div
      key={entry.id}
      role="listitem"
      aria-label={`${entry.query}, ${entry.type} search, ${entry.results_count} results, ${formatRelativeTime(entry.created_at)}`}
    >
      <SearchHistoryCard entry={entry} />
    </div>
  ))}
</div>
```

---

## 🔒 Security

### History Ownership Validation

```typescript
// Backend validates history entry belongs to user
if (search_entry.user_id !== currentUser.id) {
  throw new UnauthorizedError('Not your search entry');
}
```

### Query Sanitization

```typescript
// Sanitize search queries before storing
const sanitizeQuery = (query: string): string => {
  return query
    .trim()
    .replace(/[<>]/g, '') // Remove angle brackets
    .substring(0, 500); // Limit length
};
```

---

## 🧪 Testing

```typescript
describe('SearchHistory', () => {
  it('displays recent searches', () => {
    const { getByText } = render(
      <SearchHistoryScreen history={mockHistory} />
    );
    
    expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
    expect(getByText('12 results')).toBeInTheDocument();
  });
  
  it('filters by search type', async () => {
    const { getByText, queryByText } = render(
      <SearchHistoryScreen history={mockHistory} />
    );
    
    fireEvent.click(getByText('GraphRAG'));
    
    await waitFor(() => {
      expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
      expect(queryByText('ETH')).not.toBeInTheDocument(); // Token search hidden
    });
  });
  
  it('provides autocomplete suggestions', async () => {
    const { getByPlaceholderText, getByText } = render(
      <SearchWithAutocomplete />
    );
    
    const input = getByPlaceholderText('Search...');
    fireEvent.change(input, { target: { value: 'aav' } });
    
    await waitFor(() => {
      expect(getByText('Aave V3 security analysis')).toBeInTheDocument();
    });
  });
});
```

---

## 📊 Analytics Integration

### Track Search Actions

```typescript
// Track when user re-runs a search
analytics.track('search_history_rerun', {
  original_query: entry.query,
  search_type: entry.type,
  time_since_original: Date.now() - new Date(entry.created_at).getTime(),
});

// Track autocomplete usage
analytics.track('search_autocomplete_used', {
  prefix: prefix,
  selected_suggestion: suggestion,
  suggestion_rank: suggestions.indexOf(suggestion) + 1,
});

// Track history clearing
analytics.track('search_history_cleared', {
  entries_cleared: response.cleared,
  filter_type: searchType || 'all',
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Search History*  
*Backend Status: ✅ 100% Implemented (6 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
