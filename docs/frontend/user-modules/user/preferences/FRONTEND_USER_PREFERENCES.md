# FRONTEND_USER_PREFERENCES

## User Preferences & Settings Module

**User Type:** Authenticated User  
**Module:** User Preferences - Risk, Chains, Search, Notifications, Favorites  
**Route:** `/users/me/preferences`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**User Preferences & Settings** - Comprehensive User Configuration Management

### Description
Complete user preference management system covering risk tolerance, blockchain preferences, search settings, notification preferences, saved searches, and protocol favorites.

### Key Capabilities
- ✅ Get complete user preferences
- ✅ Update risk tolerance (conservative/moderate/aggressive)
- ✅ Manage preferred blockchain chains
- ✅ Save and manage search presets
- ✅ Add/remove favorite protocols
- ✅ Configure notification settings
- ✅ Customize display preferences

---

## 🔌 API Integration

### 1. Get User Preferences

```typescript
// GET /api/v1/users/me/preferences
// Description: Retrieve complete user preferences
// Authentication: Required (Bearer token)

interface UserPreferencesResponse {
  user_id: string;
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  preferred_chains: string[]; // ["ethereum", "polygon", "arbitrum"]
  preferred_categories: string[]; // ["defi", "lending", "dex"]
  excluded_protocols: string[]; // Protocol IDs to exclude
  favorite_protocols: string[]; // Protocol IDs marked as favorites
  search_settings: SearchSettings;
  notification_settings: NotificationSettings;
  default_currency: string; // "USD", "EUR", etc.
  theme: 'light' | 'dark' | 'auto';
}

interface SearchSettings {
  default_similarity_threshold: number; // 0.0 - 1.0
  default_risk_filter: 'all' | 'low' | 'medium' | 'high';
  search_history_enabled: boolean;
}

interface NotificationSettings {
  risk_alerts_enabled: boolean;
  push_enabled: boolean;
  min_severity: 'low' | 'medium' | 'high' | 'critical';
}

const getUserPreferences = async (): Promise<UserPreferencesResponse> => {
  const response = await api.get('/api/v1/users/me/preferences', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "risk_tolerance": "moderate",
  "preferred_chains": ["ethereum", "polygon", "arbitrum", "optimism"],
  "preferred_categories": ["defi", "lending", "yield-farming"],
  "excluded_protocols": [],
  "favorite_protocols": [
    "aave-v3",
    "uniswap-v3",
    "compound-v3"
  ],
  "search_settings": {
    "default_similarity_threshold": 0.75,
    "default_risk_filter": "medium",
    "search_history_enabled": true
  },
  "notification_settings": {
    "risk_alerts_enabled": true,
    "push_enabled": true,
    "min_severity": "high"
  },
  "default_currency": "USD",
  "theme": "dark"
}

// Example Error Response (401 Unauthorized):
{
  "error": {
    "code": "AUTHENTICATION_REQUIRED",
    "message": "Valid authentication token required",
    "details": {}
  }
}
```

---

### 2. Update Risk Tolerance

```typescript
// PUT /api/v1/users/me/preferences/risk-tolerance
// Description: Update user's risk tolerance level
// Authentication: Required (Bearer token)

interface UpdateRiskToleranceRequest {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
}

const updateRiskTolerance = async (
  riskTolerance: 'conservative' | 'moderate' | 'aggressive'
): Promise<UserPreferencesResponse> => {
  const response = await api.put('/api/v1/users/me/preferences/risk-tolerance', {
    risk_tolerance: riskTolerance
  }, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "risk_tolerance": "aggressive"
}

// Example Response (200 OK):
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "risk_tolerance": "aggressive",
  // ... rest of preferences
}

// Risk Tolerance Levels:
// - conservative: Low risk, stable protocols, blue-chip assets
// - moderate: Balanced approach, vetted protocols, some yield
// - aggressive: High risk/reward, new protocols, maximum yield
```

---

### 3. Update Chain Preferences

```typescript
// PUT /api/v1/users/me/preferences/chains
// Description: Update user's preferred blockchain chains
// Authentication: Required (Bearer token)

interface UpdateChainPreferencesRequest {
  preferred_chains: string[];
}

const updateChainPreferences = async (
  chains: string[]
): Promise<UserPreferencesResponse> => {
  const response = await api.put('/api/v1/users/me/preferences/chains', {
    preferred_chains: chains
  }, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "preferred_chains": [
    "ethereum",
    "polygon",
    "arbitrum",
    "optimism",
    "base"
  ]
}

// Example Response (200 OK):
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "preferred_chains": ["ethereum", "polygon", "arbitrum", "optimism", "base"],
  // ... rest of preferences
}

// Supported Chains:
// - ethereum, polygon, arbitrum, optimism, base
// - bsc, avalanche, fantom, gnosis
// - zksync, linea, scroll, mantle
```

---

### 4. Save Search Preset

```typescript
// POST /api/v1/users/me/preferences/search/saved
// Description: Save a search configuration as a preset
// Authentication: Required (Bearer token)

interface SaveSearchRequest {
  name: string;
  query: string;
  filters: Record<string, any>;
}

interface SavedSearchResponse {
  id: string;
  name: string;
  query: string;
  filters: Record<string, any>;
  created_at: string; // ISO 8601 timestamp
}

const saveSearch = async (
  request: SaveSearchRequest
): Promise<SavedSearchResponse> => {
  const response = await api.post('/api/v1/users/me/preferences/search/saved', request, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "name": "High Yield Stable Pools",
  "query": "stablecoin yield farming",
  "filters": {
    "min_apy": 10,
    "chains": ["ethereum", "arbitrum"],
    "risk": "low",
    "categories": ["lending", "yield-farming"]
  }
}

// Example Response (201 Created):
{
  "id": "search-123e4567",
  "name": "High Yield Stable Pools",
  "query": "stablecoin yield farming",
  "filters": {
    "min_apy": 10,
    "chains": ["ethereum", "arbitrum"],
    "risk": "low",
    "categories": ["lending", "yield-farming"]
  },
  "created_at": "2025-12-01T12:00:00Z"
}
```

---

### 5. Delete Saved Search

```typescript
// DELETE /api/v1/users/me/preferences/search/saved/{search_id}
// Description: Delete a saved search preset
// Authentication: Required (Bearer token)

const deleteSavedSearch = async (searchId: string): Promise<void> => {
  await api.delete(`/api/v1/users/me/preferences/search/saved/${searchId}`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
};

// Example Request:
// DELETE /api/v1/users/me/preferences/search/saved/search-123e4567

// Example Response (204 No Content):
// (Empty response body)

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "SEARCH_NOT_FOUND",
    "message": "Saved search not found or does not belong to user",
    "details": {
      "search_id": "search-123e4567"
    }
  }
}
```

---

### 6. Add Favorite Protocol

```typescript
// POST /api/v1/users/me/preferences/favorites/protocols/{protocol_id}
// Description: Add a protocol to user's favorites
// Authentication: Required (Bearer token)

const addFavoriteProtocol = async (protocolId: string): Promise<{success: boolean}> => {
  const response = await api.post(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`,
    {},
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  return response.data;
};

// Example Request:
// POST /api/v1/users/me/preferences/favorites/protocols/aave-v3

// Example Response (200 OK):
{
  "success": true
}

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "PROTOCOL_NOT_FOUND",
    "message": "Protocol not found",
    "details": {
      "protocol_id": "aave-v3"
    }
  }
}
```

---

### 7. Remove Favorite Protocol

```typescript
// DELETE /api/v1/users/me/preferences/favorites/protocols/{protocol_id}
// Description: Remove a protocol from user's favorites
// Authentication: Required (Bearer token)

const removeFavoriteProtocol = async (protocolId: string): Promise<void> => {
  await api.delete(
    `/api/v1/users/me/preferences/favorites/protocols/${protocolId}`,
    {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
};

// Example Request:
// DELETE /api/v1/users/me/preferences/favorites/protocols/aave-v3

// Example Response (204 No Content):
// (Empty response body)
```

---

## 🔗 React Hooks

### useUserPreferences Hook

```typescript
export function useUserPreferences() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: getUserPreferences,
  });
  
  return {
    preferences: data,
    isLoading,
    error,
    refetch,
  };
}

// Usage:
const { preferences, isLoading } = useUserPreferences();
```

### useUpdateRiskTolerance Hook

```typescript
export function useUpdateRiskTolerance() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateRiskTolerance,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Risk tolerance updated');
    },
  });
}

// Usage:
const updateRisk = useUpdateRiskTolerance();
updateRisk.mutate('aggressive');
```

### useUpdateChainPreferences Hook

```typescript
export function useUpdateChainPreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateChainPreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Chain preferences updated');
    },
  });
}

// Usage:
const updateChains = useUpdateChainPreferences();
updateChains.mutate(['ethereum', 'polygon']);
```

### useSavedSearches Hook

```typescript
export function useSavedSearches() {
  const { preferences } = useUserPreferences();
  const queryClient = useQueryClient();
  
  const saveSearch = useMutation({
    mutationFn: saveSearchMutation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Search saved');
    },
  });
  
  const deleteSearch = useMutation({
    mutationFn: deleteSavedSearch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Search deleted');
    },
  });
  
  return {
    savedSearches: preferences?.saved_searches || [],
    saveSearch,
    deleteSearch,
  };
}
```

### useFavoriteProtocols Hook

```typescript
export function useFavoriteProtocols() {
  const { preferences } = useUserPreferences();
  const queryClient = useQueryClient();
  
  const addFavorite = useMutation({
    mutationFn: addFavoriteProtocol,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Added to favorites');
    },
  });
  
  const removeFavorite = useMutation({
    mutationFn: removeFavoriteProtocol,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      toast.success('Removed from favorites');
    },
  });
  
  const isFavorite = (protocolId: string) => {
    return preferences?.favorite_protocols?.includes(protocolId) || false;
  };
  
  return {
    favoriteProtocols: preferences?.favorite_protocols || [],
    addFavorite,
    removeFavorite,
    isFavorite,
  };
}
```

---

## 🎨 React Components

### RiskToleranceSelector Component

```typescript
export function RiskToleranceSelector() {
  const { preferences } = useUserPreferences();
  const updateRisk = useUpdateRiskTolerance();
  
  const riskLevels = [
    {
      value: 'conservative',
      label: 'Conservative',
      description: 'Low risk, stable protocols',
      icon: '🛡️'
    },
    {
      value: 'moderate',
      label: 'Moderate',
      description: 'Balanced approach',
      icon: '⚖️'
    },
    {
      value: 'aggressive',
      label: 'Aggressive',
      description: 'High risk/reward',
      icon: '🚀'
    }
  ];
  
  return (
    <div className="risk-selector">
      <h3>Risk Tolerance</h3>
      <div className="options">
        {riskLevels.map(level => (
          <button
            key={level.value}
            className={preferences?.risk_tolerance === level.value ? 'active' : ''}
            onClick={() => updateRisk.mutate(level.value as any)}
            disabled={updateRisk.isPending}
          >
            <span className="icon">{level.icon}</span>
            <span className="label">{level.label}</span>
            <span className="description">{level.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

### ChainPreferencesSelector Component

```typescript
export function ChainPreferencesSelector() {
  const { preferences } = useUserPreferences();
  const updateChains = useUpdateChainPreferences();
  const [selected, setSelected] = useState<string[]>([]);
  
  useEffect(() => {
    if (preferences?.preferred_chains) {
      setSelected(preferences.preferred_chains);
    }
  }, [preferences]);
  
  const chains = [
    { id: 'ethereum', name: 'Ethereum', icon: 'Ξ' },
    { id: 'polygon', name: 'Polygon', icon: '◊' },
    { id: 'arbitrum', name: 'Arbitrum', icon: '◈' },
    { id: 'optimism', name: 'Optimism', icon: '○' },
    { id: 'base', name: 'Base', icon: '■' },
  ];
  
  const toggleChain = (chainId: string) => {
    const newSelected = selected.includes(chainId)
      ? selected.filter(id => id !== chainId)
      : [...selected, chainId];
    setSelected(newSelected);
  };
  
  const saveChanges = () => {
    updateChains.mutate(selected);
  };
  
  return (
    <div className="chain-selector">
      <h3>Preferred Chains</h3>
      <div className="chains">
        {chains.map(chain => (
          <label key={chain.id} className="chain-option">
            <input
              type="checkbox"
              checked={selected.includes(chain.id)}
              onChange={() => toggleChain(chain.id)}
            />
            <span className="icon">{chain.icon}</span>
            <span className="name">{chain.name}</span>
          </label>
        ))}
      </div>
      <button onClick={saveChanges} disabled={updateChains.isPending}>
        Save Changes
      </button>
    </div>
  );
}
```

### FavoriteProtocolButton Component

```typescript
export function FavoriteProtocolButton({ protocolId }: { protocolId: string }) {
  const { isFavorite, addFavorite, removeFavorite } = useFavoriteProtocols();
  const favorite = isFavorite(protocolId);
  
  const handleToggle = () => {
    if (favorite) {
      removeFavorite.mutate(protocolId);
    } else {
      addFavorite.mutate(protocolId);
    }
  };
  
  return (
    <button
      onClick={handleToggle}
      className={`favorite-btn ${favorite ? 'active' : ''}`}
      disabled={addFavorite.isPending || removeFavorite.isPending}
    >
      {favorite ? '★' : '☆'}
    </button>
  );
}
```

---

## 🎭 User Flows

### Flow 1: Initial Setup - User Onboarding

```
1. User completes registration
   ↓
2. Shown onboarding wizard
   ↓
3. Select risk tolerance (conservative/moderate/aggressive)
   PUT /api/v1/users/me/preferences/risk-tolerance
   ↓
4. Select preferred chains (Ethereum, Polygon, etc.)
   PUT /api/v1/users/me/preferences/chains
   ↓
5. Preferences saved
   GET /api/v1/users/me/preferences (verify)
   ↓
6. User directed to dashboard with personalized content
```

### Flow 2: Save Search Preset

```
1. User performs complex search
   ↓
2. Finds useful results
   ↓
3. Clicks "Save Search" button
   ↓
4. Modal opens: Enter name for preset
   ↓
5. POST /api/v1/users/me/preferences/search/saved
   ↓
6. Search saved to "Saved Searches" sidebar
   ↓
7. Quick access for future searches
```

### Flow 3: Manage Favorite Protocols

```
1. User browses protocols
   ↓
2. Finds interesting protocol (e.g., Aave V3)
   ↓
3. Clicks star icon
   ↓
4. POST /api/v1/users/me/preferences/favorites/protocols/aave-v3
   ↓
5. Star fills, protocol added to favorites
   ↓
6. Protocol appears in "Favorites" section
   ↓
7. Click star again to remove:
   DELETE /api/v1/users/me/preferences/favorites/protocols/aave-v3
```

---

## ⚠️ Error Handling

```typescript
const handlePreferencesError = (error: any) => {
  switch (error.code) {
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to update preferences');
      redirectToLogin();
      break;
      
    case 'INVALID_RISK_TOLERANCE':
      toast.error('Invalid risk tolerance level selected');
      break;
      
    case 'INVALID_CHAIN':
      toast.error('One or more selected chains are not supported');
      break;
      
    case 'SEARCH_NOT_FOUND':
      toast.error('Saved search not found');
      break;
      
    case 'PROTOCOL_NOT_FOUND':
      toast.error('Protocol not found');
      break;
      
    case 'DUPLICATE_FAVORITE':
      toast.info('Protocol already in favorites');
      break;
      
    default:
      toast.error('Unable to update preferences. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. Risk-Based Content Filtering
- User sets risk tolerance to "conservative"
- Dashboard shows only low-risk, established protocols
- Filters out high-risk, experimental protocols

### 2. Multi-Chain Portfolio Management
- User selects Ethereum, Polygon, Arbitrum
- Protocol search filtered to selected chains
- Portfolio aggregates data from preferred chains only

### 3. Power User Search Presets
- User creates "Stable Yield" search preset
- Saves filters: min_apy: 10%, risk: low, stablecoins
- One-click access to recurring searches

### 4. Favorite Protocol Tracking
- User favorites Aave, Compound, Uniswap
- Dedicated "Favorites" dashboard widget
- Real-time updates for favorited protocols

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: User Preferences & Settings*  
*Backend Status: ✅ 100% Implemented (7 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
