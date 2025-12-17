# User Modules - Master Flow Specification

**Version**: 1.0
**Date**: December 17, 2025
**Status**: ✅ Complete
**Methodology**: UX Design + CTO Framework
**Coverage**: 17 User Modules (69+ Endpoints)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [User Personas](#user-personas)
3. [Core Features Flows](#core-features-flows)
4. [Dashboard & Insights Flows](#dashboard--insights-flows)
5. [Advanced Features Flows](#advanced-features-flows)
6. [Utilities & System Flows](#utilities--system-flows)
7. [Cross-Module Integration Patterns](#cross-module-integration-patterns)
8. [Global Error Handling](#global-error-handling)
9. [Performance & Optimization](#performance--optimization)
10. [Accessibility Guidelines](#accessibility-guidelines)

---

## 🎯 Overview

### Purpose

This master specification documents complete user experience flows for ALL user-facing modules in the DeFi Multi-Agent Chat platform (excluding Chat module which has its own dedicated spec). It provides frontend developers with comprehensive guidance for implementing consistent, accessible, and delightful user experiences across 17 modules and 69+ endpoints.

### Scope

**Modules Covered:**

**Core Features (5 modules):**
- Authentication & Account Management
- User Preferences & Settings
- Search & Discovery
- Protocol Comparison
- Risk Alerts & Subscriptions

**Dashboard & Insights (3 modules):**
- Dashboard & Aggregation
- Markets & Data
- Portfolio Risk Analysis

**Advanced Features (4 modules):**
- GraphRAG & Analytics
- Projects & Workspaces
- Real-Time Communication (WebSocket)
- Chat GraphRAG Enhanced

**Utilities & System (5 modules):**
- Notifications
- Metrics & Analytics
- ML Prediction
- ML Network Analysis
- Location & Atlas Services

### Design Principles

- **Progressive Disclosure** - Reveal complexity gradually
- **Data-Driven Insights** - Surface actionable information
- **Contextual Assistance** - Smart, timely suggestions
- **Seamless Integration** - Modules work together naturally
- **Performance First** - Fast, responsive experiences
- **Accessibility Always** - WCAG 2.1 AA minimum

---

## 👥 User Personas

### Persona 1: Alex - The Active DeFi Investor

**Demographics:**
- Age: 32
- Role: Full-time DeFi investor
- Experience: Advanced
- Portfolio: $500K+ across 15+ protocols

**Goals:**
- Maximize yield while managing risk
- Stay informed about protocol changes
- React quickly to market opportunities
- Track portfolio performance in real-time

**Pain Points:**
- Scattered information across platforms
- Manual risk calculation
- Alert fatigue from too many notifications
- Difficulty comparing complex protocols

**Usage Patterns:**
- Checks dashboard 10+ times daily
- Sets up 20+ risk alerts
- Uses GraphRAG for protocol research
- Monitors real-time price feeds
- Reviews ML predictions regularly

**Key Flows:**
- Dashboard → Markets → Portfolio Risk → Alerts
- Search → GraphRAG → Protocol Comparison → Decision
- Real-time Feed → Alert → Action

---

### Persona 2: Jordan - The DeFi Researcher

**Demographics:**
- Age: 28
- Role: Blockchain analyst
- Experience: Expert
- Focus: Protocol security and risk analysis

**Goals:**
- Deep protocol analysis
- Risk pattern identification
- Network effect modeling
- Historical trend analysis

**Pain Points:**
- Limited analytical tools
- No graph visualization
- Manual data collection
- Lack of ML-powered insights

**Usage Patterns:**
- Uses GraphRAG extensively
- Runs ML network analysis
- Exports analytics data
- Compares protocol architectures
- Tracks metrics over time

**Key Flows:**
- GraphRAG Search → Network Analysis → Risk Prediction
- ML Analysis → Metrics Tracking → Report Export
- Protocol Comparison → Historical Data → Insights

---

### Persona 3: Sam - The Cautious Newcomer

**Demographics:**
- Age: 26
- Role: New to DeFi
- Experience: Beginner
- Portfolio: <$10K, 2-3 protocols

**Goals:**
- Learn DeFi safely
- Understand risks before investing
- Get guidance on protocol selection
- Avoid common mistakes

**Pain Points:**
- Overwhelming technical complexity
- Fear of losing money
- Uncertain what to trust
- Need for educational content

**Usage Patterns:**
- Uses search suggestions heavily
- Relies on AI recommendations
- Checks risk scores before actions
- Prefers simple, visual interfaces
- Needs frequent help/guidance

**Key Flows:**
- Search → Suggestions → Protocol Details
- Comparison → Risk Scores → Recommendations
- Dashboard → Simple View → Guided Actions

---

## 🗺️ Core Features Flows

### Flow 1: Authentication & Account Management

**Module**: `user/account/`
**Endpoints**: 8 endpoints
**Priority**: CRITICAL

#### Journey: New User Registration

```
START: User visits platform
  │
  ├─> 1. Registration Form
  │   User enters: email, password
  │   API: POST /api/v1/register
  │   Request: {
  │     email: "user@example.com",
  │     password: "secure_password123",
  │     terms_accepted: true
  │   }
  │
  │   Response: {
  │     user_id: "uuid",
  │     email: "user@example.com",
  │     email_verified: false,
  │     created_at: "2025-12-17T10:00:00Z"
  │   }
  │
  │   UI: Shows success message
  │       "Check your email to verify your account"
  │
  ├─> 2. Email Verification
  │   User: Clicks link in email
  │   API: POST /api/v1/verify-email
  │   Request: { token: "verification_token_from_email" }
  │
  │   Response: {
  │     success: true,
  │     message: "Email verified successfully"
  │   }
  │
  │   UI: Redirects to login page
  │       "Email verified! Please log in."
  │
  ├─> 3. Login
  │   User enters: email, password
  │   API: POST /api/v1/login
  │   Request: {
  │     email: "user@example.com",
  │     password: "secure_password123"
  │   }
  │
  │   Response: {
  │     access_token: "jwt_token_here",
  │     refresh_token: "refresh_token_here",
  │     user: {
  │       id: "uuid",
  │       email: "user@example.com",
  │       role: "user"
  │     }
  │   }
  │
  │   UI: Stores tokens in localStorage/sessionStorage
  │       Redirects to dashboard
  │
  ├─> 4. First-Time Setup (Optional)
  │   UI: Shows onboarding wizard
  │       "Let's personalize your experience"
  │
  │   Wizard Steps:
  │   a) Risk tolerance selection
  │   b) Chain preferences
  │   c) Favorite protocols
  │   d) Alert preferences
  │
  │   Each step calls relevant preference APIs
  │
  └─> END: User lands on personalized dashboard
```

#### Integration Pattern: Auth Context

```typescript
import { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          // Validate token and get user info
          const response = await fetch('/api/v1/user/me', {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            // Token invalid, clear storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
          }
        } catch (error) {
          console.error('Auth check failed:', error);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch('/api/v1/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();

    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);

    // Set user
    setUser(data.user);

    // Redirect to dashboard
    navigate('/dashboard');
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    navigate('/login');
  };

  const register = async (email: string, password: string) => {
    const response = await fetch('/api/v1/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, terms_accepted: true })
    });

    if (!response.ok) {
      throw new Error('Registration failed');
    }

    // Show success message
    // User needs to verify email before logging in
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        register
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Protected Route Component
export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return isAuthenticated ? <>{children}</> : null;
};
```

---

### Flow 2: User Preferences & Settings

**Module**: `user/preferences/`
**Endpoints**: 7 endpoints
**Priority**: HIGH

#### Journey: Personalizing Experience

```
START: User navigates to Settings
  │
  ├─> 1. Load Current Preferences
  │   API: GET /api/v1/user/preferences
  │
  │   Response: {
  │     risk_tolerance: "moderate",
  │     preferred_chains: ["ethereum", "polygon", "arbitrum"],
  │     favorite_protocols: ["aave", "uniswap", "curve"],
  │     saved_searches: [
  │       { query: "stablecoin pools", created_at: "..." },
  │       { query: "high yield ethereum", created_at: "..." }
  │     ],
  │     notification_preferences: {
  │       email: true,
  │       push: false,
  │       sms: false
  │     },
  │     theme: "dark",
  │     language: "en"
  │   }
  │
  │   UI: Renders Settings Page with current values
  │
  ├─> 2. Update Risk Tolerance
  │   User: Moves slider from "moderate" to "aggressive"
  │   API: PUT /api/v1/user/preferences/risk-tolerance
  │   Request: { risk_tolerance: "aggressive" }
  │
  │   Response: {
  │     risk_tolerance: "aggressive",
  │     updated_at: "2025-12-17T10:05:00Z"
  │   }
  │
  │   UI: Shows toast: "Risk tolerance updated"
  │       Updates slider position
  │       May trigger dashboard recalculation
  │
  ├─> 3. Update Chain Preferences
  │   User: Toggles "Optimism" on, "Polygon" off
  │   API: PUT /api/v1/user/preferences/chains
  │   Request: {
  │     preferred_chains: ["ethereum", "arbitrum", "optimism"]
  │   }
  │
  │   Response: {
  │     preferred_chains: ["ethereum", "arbitrum", "optimism"],
  │     updated_at: "2025-12-17T10:06:00Z"
  │   }
  │
  │   UI: Updates checkbox states
  │       Shows info: "Markets will now show Optimism protocols"
  │
  ├─> 4. Add Favorite Protocol
  │   User: Searches and selects "Compound V3"
  │   API: POST /api/v1/user/preferences/favorites
  │   Request: { protocol_id: "compound-v3" }
  │
  │   Response: {
  │     favorite_protocols: [
  │       "aave", "uniswap", "curve", "compound-v3"
  │     ],
  │     updated_at: "2025-12-17T10:07:00Z"
  │   }
  │
  │   UI: Adds "Compound V3" to favorites list
  │       Shows on dashboard quick access
  │
  ├─> 5. Save Search Query
  │   User: Types "high APY stablecoin farms" in search
  │   User: Clicks "Save this search"
  │   API: POST /api/v1/user/preferences/saved-searches
  │   Request: { query: "high APY stablecoin farms" }
  │
  │   Response: {
  │     saved_searches: [
  │       { id: "uuid", query: "high APY stablecoin farms", ... },
  │       // ... existing searches
  │     ]
  │   }
  │
  │   UI: Shows in "Saved Searches" section
  │       One-click access to run search again
  │
  └─> END: Settings saved, experience personalized
```

#### Integration Pattern: Preferences Hook

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface UserPreferences {
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive';
  preferred_chains: string[];
  favorite_protocols: string[];
  saved_searches: Array<{ id: string; query: string; created_at: string }>;
  notification_preferences: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  theme: 'light' | 'dark' | 'auto';
  language: string;
}

export const useUserPreferences = () => {
  const queryClient = useQueryClient();

  // Get preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['user', 'preferences'],
    queryFn: async () => {
      const response = await fetch('/api/v1/user/preferences', {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      return response.json() as Promise<UserPreferences>;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Update risk tolerance
  const updateRiskTolerance = useMutation({
    mutationFn: async (risk_tolerance: UserPreferences['risk_tolerance']) => {
      const response = await fetch('/api/v1/user/preferences/risk-tolerance', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ risk_tolerance })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      // Also invalidate dashboard/portfolio queries that depend on risk tolerance
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio', 'risk'] });
    }
  });

  // Update chains
  const updateChains = useMutation({
    mutationFn: async (preferred_chains: string[]) => {
      const response = await fetch('/api/v1/user/preferences/chains', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ preferred_chains })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
      queryClient.invalidateQueries({ queryKey: ['markets'] });
    }
  });

  // Add favorite protocol
  const addFavorite = useMutation({
    mutationFn: async (protocol_id: string) => {
      const response = await fetch('/api/v1/user/preferences/favorites', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ protocol_id })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
    }
  });

  // Save search
  const saveSearch = useMutation({
    mutationFn: async (query: string) => {
      const response = await fetch('/api/v1/user/preferences/saved-searches', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({ query })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'preferences'] });
    }
  });

  return {
    preferences,
    isLoading,
    updateRiskTolerance,
    updateChains,
    addFavorite,
    saveSearch
  };
};

// Settings Page Component
export const SettingsPage = () => {
  const {
    preferences,
    isLoading,
    updateRiskTolerance,
    updateChains,
    addFavorite
  } = useUserPreferences();

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      {/* Risk Tolerance Section */}
      <section>
        <h2>Risk Tolerance</h2>
        <RiskToleranceSlider
          value={preferences.risk_tolerance}
          onChange={(value) => updateRiskTolerance.mutate(value)}
        />
        {updateRiskTolerance.isPending && <Spinner />}
      </section>

      {/* Chain Preferences */}
      <section>
        <h2>Preferred Chains</h2>
        <ChainSelector
          selected={preferences.preferred_chains}
          onChange={(chains) => updateChains.mutate(chains)}
        />
      </section>

      {/* Favorite Protocols */}
      <section>
        <h2>Favorite Protocols</h2>
        <ProtocolList favorites={preferences.favorite_protocols} />
        <Button onClick={() => {/* Show add protocol modal */}}>
          Add Protocol
        </Button>
      </section>
    </div>
  );
};
```

---

### Flow 3: Search & Discovery

**Module**: `user/search/`
**Endpoints**: 6 endpoints
**Priority**: HIGH

#### Journey: Smart Protocol Discovery

```
START: User wants to find stablecoin yield opportunities
  │
  ├─> 1. Load Search Suggestions
  │   User: Clicks search input
  │   API: GET /api/v1/user/search/suggestions?type=protocol&limit=10
  │
  │   Response: {
  │     suggestions: [
  │       {
  │         query: "stablecoin yield",
  │         type: "protocol",
  │         popularity: 245,
  │         recent: true
  │       },
  │       {
  │         query: "USDC staking",
  │         type: "token",
  │         popularity: 189
  │       },
  │       // ... more suggestions
  │     ]
  │   }
  │
  │   UI: Shows dropdown with trending searches
  │       "🔥 Trending: stablecoin yield"
  │       "Recently searched: USDC staking"
  │
  ├─> 2. User Types Query
  │   User: Types "stable"
  │   System: Debounced autocomplete (300ms)
  │
  │   [Already covered in chat spec with autocomplete]
  │   Shows real-time suggestions
  │
  ├─> 3. Execute Search
  │   User: Types "stablecoin yield" and presses Enter
  │   API: GET /api/v1/user/search/history (to log search)
  │   API: POST /api/v1/user/search/history
  │   Request: { query: "stablecoin yield", search_type: "protocol" }
  │
  │   Response: {
  │     search_id: "uuid",
  │     query: "stablecoin yield",
  │     created_at: "2025-12-17T10:10:00Z"
  │   }
  │
  │   Then: Perform actual search (via GraphRAG or Markets endpoint)
  │   [Integration with GraphRAG module]
  │
  ├─> 4. View Search History
  │   User: Clicks "Recent Searches"
  │   API: GET /api/v1/user/search/history?limit=20&page=1
  │
  │   Response: {
  │     searches: [
  │       {
  │         id: "uuid",
  │         query: "stablecoin yield",
  │         search_type: "protocol",
  │         created_at: "2025-12-17T10:10:00Z"
  │       },
  │       {
  │         id: "uuid-2",
  │         query: "Aave risk",
  │         search_type: "risk",
  │         created_at: "2025-12-16T14:22:00Z"
  │       },
  │       // ... more history
  │     ],
  │     total: 47,
  │     page: 1,
  │     page_size: 20
  │   }
  │
  │   UI: Shows list of past searches
  │       One-click to re-run search
  │       Option to clear history
  │
  ├─> 5. Delete Search History Item
  │   User: Clicks delete on specific search
  │   API: DELETE /api/v1/user/search/history/{search_id}
  │
  │   Response: { success: true }
  │
  │   UI: Removes item from list
  │       Shows toast: "Search removed from history"
  │
  ├─> 6. Clear All History
  │   User: Clicks "Clear All History"
  │   UI: Shows confirmation dialog
  │       "Are you sure? This cannot be undone."
  │   User: Confirms
  │   API: DELETE /api/v1/user/search/history
  │
  │   Response: { success: true, deleted_count: 47 }
  │
  │   UI: Clears history list
  │       Shows: "All search history cleared"
  │
  └─> END: User finds relevant protocols, history managed
```

#### Integration Pattern: Search with History

```typescript
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDebounce } from './useDebounce';

interface SearchHistoryItem {
  id: string;
  query: string;
  search_type: string;
  created_at: string;
}

export const useSearch = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const debouncedQuery = useDebounce(query, 300);
  const queryClient = useQueryClient();

  // Get search suggestions
  const { data: suggestionsData } = useQuery({
    queryKey: ['search', 'suggestions'],
    queryFn: async () => {
      const response = await fetch(
        '/api/v1/user/search/suggestions?type=protocol&limit=10',
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      return response.json();
    },
    staleTime: 10 * 60 * 1000 // 10 minutes
  });

  // Get search history
  const { data: history } = useQuery({
    queryKey: ['search', 'history'],
    queryFn: async () => {
      const response = await fetch(
        '/api/v1/user/search/history?limit=20',
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      return response.json();
    }
  });

  // Log search
  const logSearch = useMutation({
    mutationFn: async (searchQuery: string) => {
      const response = await fetch('/api/v1/user/search/history', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          query: searchQuery,
          search_type: 'protocol'
        })
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'history'] });
    }
  });

  // Delete history item
  const deleteHistoryItem = useMutation({
    mutationFn: async (searchId: string) => {
      const response = await fetch(
        `/api/v1/user/search/history/${searchId}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${getToken()}` }
        }
      );
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'history'] });
    }
  });

  // Clear all history
  const clearHistory = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/v1/user/search/history', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['search', 'history'] });
    }
  });

  // Update suggestions based on input
  useEffect(() => {
    if (debouncedQuery) {
      // Filter suggestions based on query
      const filtered = suggestionsData?.suggestions
        .filter((s: any) =>
          s.query.toLowerCase().includes(debouncedQuery.toLowerCase())
        )
        .map((s: any) => s.query) || [];

      setSuggestions(filtered);
    } else {
      setSuggestions([]);
    }
  }, [debouncedQuery, suggestionsData]);

  const executeSearch = (searchQuery: string) => {
    // Log the search
    logSearch.mutate(searchQuery);

    // Perform actual search (integrate with GraphRAG or Markets)
    // This will trigger navigation or state update
  };

  return {
    query,
    setQuery,
    suggestions,
    history: history?.searches || [],
    executeSearch,
    deleteHistoryItem,
    clearHistory
  };
};

// Search Component
export const SearchBar = () => {
  const {
    query,
    setQuery,
    suggestions,
    history,
    executeSearch,
    deleteHistoryItem
  } = useSearch();

  const [showHistory, setShowHistory] = useState(false);

  return (
    <div className="search-bar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setShowHistory(true)}
        onBlur={() => setTimeout(() => setShowHistory(false), 200)}
        placeholder="Search protocols, tokens, or strategies..."
        aria-label="Search"
      />

      {/* Suggestions Dropdown */}
      {query && suggestions.length > 0 && (
        <ul className="suggestions-dropdown" role="listbox">
          {suggestions.map((suggestion, index) => (
            <li
              key={index}
              role="option"
              onClick={() => {
                setQuery(suggestion);
                executeSearch(suggestion);
              }}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}

      {/* History Dropdown */}
      {showHistory && !query && history.length > 0 && (
        <div className="history-dropdown">
          <div className="history-header">Recent Searches</div>
          <ul>
            {history.slice(0, 5).map((item: SearchHistoryItem) => (
              <li key={item.id}>
                <button
                  onClick={() => {
                    setQuery(item.query);
                    executeSearch(item.query);
                  }}
                >
                  {item.query}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteHistoryItem.mutate(item.id);
                  }}
                  aria-label="Delete from history"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

---

### Flow 4: Protocol Comparison

**Module**: `user/comparison/`
**Endpoints**: 1 endpoint (powerful)
**Priority**: HIGH

#### Journey: Comparing DeFi Protocols

```
START: User wants to compare Aave, Compound, and Morpho
  │
  ├─> 1. Select Protocols for Comparison
  │   User: Searches and selects protocols
  │   UI: Shows protocol selection interface
  │       "Select 2-5 protocols to compare"
  │
  │   Selected:
  │   - Aave V3
  │   - Compound V3
  │   - Morpho Blue
  │
  ├─> 2. Execute Comparison
  │   API: POST /api/v1/user/protocols/compare
  │   Request: {
  │     protocol_ids: ["aave-v3", "compound-v3", "morpho-blue"],
  │     comparison_criteria: [
  │       "risk_score",
  │       "yield",
  │       "tvl",
  │       "security",
  │       "network_effects"
  │     ],
  │     include_recommendations: true
  │   }
  │
  │   Response: {
  │     comparison_id: "uuid",
  │     protocols: [
  │       {
  │         id: "aave-v3",
  │         name: "Aave V3",
  │         metrics: {
  │           risk_score: 7.5,
  │           yield_apy: 4.2,
  │           tvl_usd: 5800000000,
  │           security_score: 9.1,
  │           network_centrality: 0.85
  │         },
  │         strengths: [
  │           "High TVL and liquidity",
  │           "Multi-chain support",
  │           "Strong security record"
  │         ],
  │         weaknesses: [
  │           "Lower yields than competitors",
  │           "Higher gas costs"
  │         ]
  │       },
  │       {
  │         id: "compound-v3",
  │         name: "Compound V3",
  │         metrics: {
  │           risk_score: 7.8,
  │           yield_apy: 3.9,
  │           tvl_usd: 2100000000,
  │           security_score: 8.9,
  │           network_centrality: 0.78
  │         },
  │         strengths: [
  │           "Simple, focused design",
  │           "Lower risk profile"
  │         ],
  │         weaknesses: [
  │           "Limited asset support",
  │           "Lower yields"
  │         ]
  │       },
  │       {
  │         id: "morpho-blue",
  │         name: "Morpho Blue",
  │         metrics: {
  │           risk_score: 6.2,
  │           yield_apy: 5.7,
  │           tvl_usd: 450000000,
  │           security_score: 8.2,
  │           network_centrality: 0.45
  │         },
  │         strengths: [
  │           "Highest yields",
  │           "Optimized rate matching",
  │           "Lower gas costs"
  │         ],
  │         weaknesses: [
  │           "Smaller TVL",
  │           "Newer protocol"
  │         ]
  │       }
  │     ],
  │     ai_recommendation: {
  │       recommended_protocol: "morpho-blue",
  │       confidence: 0.82,
  │       reasoning: "For yield-focused investors with moderate risk tolerance, Morpho Blue offers the best risk-adjusted returns. While TVL is lower, the protocol has solid security and innovative rate optimization.",
  │       risk_considerations: [
  │         "Lower liquidity than Aave",
  │         "Less battle-tested than competitors"
  │       ],
  │       alternative_suggestion: "Aave V3 for maximum security"
  │     },
  │     comparison_matrix: {
  │       winner_by_metric: {
  │         risk_score: "morpho-blue",
  │         yield: "morpho-blue",
  │         tvl: "aave-v3",
  │         security: "aave-v3",
  │         network_effects: "aave-v3"
  │       }
  │     },
  │     created_at: "2025-12-17T10:15:00Z"
  │   }
  │
  ├─> 3. Visualize Comparison
  │   UI: Renders Comparison Dashboard
  │
  │   Layout:
  │   ┌────────────────────────────────────────────────────┐
  │   │  Protocol Comparison: 3 Protocols                  │
  │   ├────────────────────────────────────────────────────┤
  │   │                                                    │
  │   │  📊 Metrics Comparison (Radar Chart)              │
  │   │     - Risk Score                                   │
  │   │     - Yield APY                                    │
  │   │     - Security Score                               │
  │   │     - Network Effects                              │
  │   │                                                    │
  │   │  📋 Side-by-Side Table                            │
  │   │  ┌────────┬────────┬──────────┬─────────────┐   │
  │   │  │ Metric │ Aave   │ Compound │ Morpho Blue │   │
  │   │  ├────────┼────────┼──────────┼─────────────┤   │
  │   │  │ Risk   │ 7.5    │ 7.8      │ 6.2 🏆     │   │
  │   │  │ Yield  │ 4.2%   │ 3.9%     │ 5.7% 🏆    │   │
  │   │  │ TVL    │ $5.8B🏆│ $2.1B    │ $450M      │   │
  │   │  └────────┴────────┴──────────┴─────────────┘   │
  │   │                                                    │
  │   │  🤖 AI Recommendation                             │
  │   │  "For yield-focused investors..."                 │
  │   │  → Morpho Blue (82% confidence)                   │
  │   │                                                    │
  │   │  ✅ Strengths & ⚠️ Weaknesses (per protocol)     │
  │   │                                                    │
  │   │  [Export Report] [Save Comparison]                │
  │   └────────────────────────────────────────────────────┘
  │
  ├─> 4. Interactive Exploration
  │   User can:
  │   - Hover over metrics for details
  │   - Toggle metrics on/off
  │   - Adjust comparison criteria
  │   - View historical data
  │   - Export comparison as PDF/CSV
  │
  └─> END: User makes informed decision
```

#### Integration Pattern: Protocol Comparison

```typescript
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

interface ComparisonRequest {
  protocol_ids: string[];
  comparison_criteria: string[];
  include_recommendations: boolean;
}

interface ComparisonResult {
  comparison_id: string;
  protocols: Array<{
    id: string;
    name: string;
    metrics: {
      risk_score: number;
      yield_apy: number;
      tvl_usd: number;
      security_score: number;
      network_centrality: number;
    };
    strengths: string[];
    weaknesses: string[];
  }>;
  ai_recommendation: {
    recommended_protocol: string;
    confidence: number;
    reasoning: string;
    risk_considerations: string[];
    alternative_suggestion: string;
  };
  comparison_matrix: {
    winner_by_metric: Record<string, string>;
  };
  created_at: string;
}

export const useProtocolComparison = () => {
  const [selectedProtocols, setSelectedProtocols] = useState<string[]>([]);

  const compareProtocols = useMutation({
    mutationFn: async (request: ComparisonRequest) => {
      const response = await fetch('/api/v1/user/protocols/compare', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify(request)
      });
      return response.json() as Promise<ComparisonResult>;
    }
  });

  const executeComparison = () => {
    if (selectedProtocols.length < 2 || selectedProtocols.length > 5) {
      throw new Error('Please select 2-5 protocols');
    }

    compareProtocols.mutate({
      protocol_ids: selectedProtocols,
      comparison_criteria: [
        'risk_score',
        'yield',
        'tvl',
        'security',
        'network_effects'
      ],
      include_recommendations: true
    });
  };

  return {
    selectedProtocols,
    setSelectedProtocols,
    executeComparison,
    comparisonResult: compareProtocols.data,
    isComparing: compareProtocols.isPending,
    error: compareProtocols.error
  };
};

// Comparison Component
export const ProtocolComparison = () => {
  const {
    selectedProtocols,
    setSelectedProtocols,
    executeComparison,
    comparisonResult,
    isComparing
  } = useProtocolComparison();

  return (
    <div className="protocol-comparison">
      {/* Protocol Selection */}
      <ProtocolSelector
        selected={selectedProtocols}
        onChange={setSelectedProtocols}
        min={2}
        max={5}
      />

      <Button
        onClick={executeComparison}
        disabled={selectedProtocols.length < 2 || isComparing}
      >
        {isComparing ? 'Comparing...' : 'Compare Protocols'}
      </Button>

      {/* Comparison Results */}
      {comparisonResult && (
        <ComparisonResults result={comparisonResult} />
      )}
    </div>
  );
};

// Radar Chart Component for Metrics
export const MetricsRadarChart = ({ protocols }: { protocols: any[] }) => {
  // Uses Recharts or similar library
  const data = [
    {
      metric: 'Risk',
      ...protocols.reduce((acc, p) => ({
        ...acc,
        [p.name]: p.metrics.risk_score
      }), {})
    },
    {
      metric: 'Yield',
      ...protocols.reduce((acc, p) => ({
        ...acc,
        [p.name]: p.metrics.yield_apy
      }), {})
    },
    // ... more metrics
  ];

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="metric" />
        <PolarRadiusAxis />
        {protocols.map((protocol, index) => (
          <Radar
            key={protocol.id}
            name={protocol.name}
            dataKey={protocol.name}
            stroke={colors[index]}
            fill={colors[index]}
            fillOpacity={0.3}
          />
        ))}
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
};
```

---

### Flow 5: Risk Alerts & Subscriptions

**Module**: `user/alerts/`
**Endpoints**: 8 endpoints
**Priority**: HIGH

#### Journey: Setting Up Smart Alerts

```
START: User wants to monitor Aave V3 risk
  │
  ├─> 1. Browse Available Alerts
  │   API: GET /api/v1/user/alerts?status=active&page=1&limit=20
  │
  │   Response: {
  │     alerts: [
  │       {
  │         id: "alert-uuid-1",
  │         protocol_id: "uniswap-v3",
  │         alert_type: "price_volatility",
  │         severity: "high",
  │         threshold: 0.05,
  │         triggered_at: "2025-12-17T09:30:00Z",
  │         acknowledged: false,
  │         message: "UNI price volatility exceeded 5% threshold"
  │       },
  │       // ... more alerts
  │     ],
  │     total: 15,
  │     unacknowledged_count: 3
  │   }
  │
  │   UI: Shows alert dashboard
  │       Highlights unacknowledged alerts
  │       Groups by severity
  │
  ├─> 2. Create New Alert Subscription
  │   User: Clicks "Create Alert"
  │   User: Fills form:
  │     - Protocol: Aave V3
  │     - Alert Type: Risk Score Change
  │     - Threshold: >8.0 (high risk)
  │     - Channels: Email + Push notification
  │
  │   API: POST /api/v1/user/alerts/subscriptions
  │   Request: {
  │     protocol_id: "aave-v3",
  │     alert_type: "risk_score_change",
  │     threshold: 8.0,
  │     comparison_operator: "greater_than",
  │     notification_channels: ["email", "push"],
  │     frequency: "immediate",
  │     active: true
  │   }
  │
  │   Response: {
  │     subscription_id: "sub-uuid",
  │     protocol_id: "aave-v3",
  │     alert_type: "risk_score_change",
  │     threshold: 8.0,
  │     active: true,
  │     created_at: "2025-12-17T10:20:00Z"
  │   }
  │
  │   UI: Shows success message
  │       "Alert created! You'll be notified when Aave V3 risk exceeds 8.0"
  │       Adds to subscriptions list
  │
  ├─> 3. Manage Subscriptions
  │   API: GET /api/v1/user/alerts/subscriptions
  │
  │   Response: {
  │     subscriptions: [
  │       {
  │         id: "sub-uuid",
  │         protocol_id: "aave-v3",
  │         alert_type: "risk_score_change",
  │         threshold: 8.0,
  │         active: true,
  │         triggered_count: 0,
  │         last_triggered: null
  │       },
  │       {
  │         id: "sub-uuid-2",
  │         protocol_id: "uniswap-v3",
  │         alert_type: "price_volatility",
  │         threshold: 0.05,
  │         active: true,
  │         triggered_count: 12,
  │         last_triggered: "2025-12-17T09:30:00Z"
  │       },
  │       // ... more subscriptions
  │     ]
  │   }
  │
  │   UI: Shows subscription management dashboard
  │       Toggle active/inactive
  │       Edit thresholds
  │       Delete subscriptions
  │
  ├─> 4. Alert Triggered (Real-time)
  │   System: Detects Aave V3 risk score = 8.3
  │   Backend: Creates alert, sends notifications
  │
  │   WebSocket or Push:
  │   {
  │     type: "alert_triggered",
  │     alert: {
  │       id: "alert-uuid-new",
  │       protocol_id: "aave-v3",
  │       alert_type: "risk_score_change",
  │       severity: "high",
  │       message: "Aave V3 risk score increased to 8.3",
  │       current_value: 8.3,
  │       threshold: 8.0,
  │       triggered_at: "2025-12-17T11:05:00Z"
  │     }
  │   }
  │
  │   UI: Shows notification banner
  │       🚨 High Risk Alert: Aave V3 risk score now 8.3
  │       [View Details] [Acknowledge]
  │
  │   Email: Sends detailed alert email
  │   Push: Sends mobile push notification
  │
  ├─> 5. Acknowledge Alert
  │   User: Clicks "Acknowledge" on alert
  │   API: PUT /api/v1/user/alerts/{alert_id}/acknowledge
  │
  │   Response: {
  │     alert_id: "alert-uuid-new",
  │     acknowledged: true,
  │     acknowledged_at: "2025-12-17T11:10:00Z"
  │   }
  │
  │   UI: Marks alert as acknowledged
  │       Moves to "Acknowledged" section
  │       Reduces unacknowledged count
  │
  ├─> 6. Filter Alerts by Severity
  │   User: Selects "High severity only"
  │   API: GET /api/v1/user/alerts?severity=high
  │
  │   Response: {
  │     alerts: [...high severity alerts only...],
  │     total: 5
  │   }
  │
  │   UI: Updates alert list
  │       Shows only high-severity alerts
  │
  ├─> 7. Update Subscription Settings
  │   User: Wants to change threshold to 7.5
  │   API: PUT /api/v1/user/alerts/subscriptions/{subscription_id}
  │   Request: { threshold: 7.5 }
  │
  │   Response: {
  │     subscription_id: "sub-uuid",
  │     threshold: 7.5,
  │     updated_at: "2025-12-17T11:15:00Z"
  │   }
  │
  │   UI: Updates subscription display
  │       "Alert will now trigger at 7.5 instead of 8.0"
  │
  └─> END: User monitors risk proactively with smart alerts
```

#### Integration Pattern: Alerts & Subscriptions

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useWebSocket } from './useWebSocket';

interface Alert {
  id: string;
  protocol_id: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  threshold: number;
  triggered_at: string;
  acknowledged: boolean;
  message: string;
}

interface AlertSubscription {
  id: string;
  protocol_id: string;
  alert_type: string;
  threshold: number;
  comparison_operator: 'greater_than' | 'less_than' | 'equals';
  notification_channels: string[];
  active: boolean;
  triggered_count: number;
  last_triggered: string | null;
}

export const useAlerts = () => {
  const queryClient = useQueryClient();

  // Get active alerts
  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts', 'active'],
    queryFn: async () => {
      const response = await fetch(
        '/api/v1/user/alerts?status=active',
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      return response.json();
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  // Get subscriptions
  const { data: subscriptions } = useQuery({
    queryKey: ['alerts', 'subscriptions'],
    queryFn: async () => {
      const response = await fetch(
        '/api/v1/user/alerts/subscriptions',
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      return response.json();
    }
  });

  // Create subscription
  const createSubscription = useMutation({
    mutationFn: async (subscription: Partial<AlertSubscription>) => {
      const response = await fetch('/api/v1/user/alerts/subscriptions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify(subscription)
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscriptions'] });
    }
  });

  // Acknowledge alert
  const acknowledgeAlert = useMutation({
    mutationFn: async (alertId: string) => {
      const response = await fetch(
        `/api/v1/user/alerts/${alertId}/acknowledge`,
        {
          method: 'PUT',
          headers: { Authorization: `Bearer ${getToken()}` }
        }
      );
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'active'] });
    }
  });

  // Update subscription
  const updateSubscription = useMutation({
    mutationFn: async ({
      subscriptionId,
      updates
    }: {
      subscriptionId: string;
      updates: Partial<AlertSubscription>;
    }) => {
      const response = await fetch(
        `/api/v1/user/alerts/subscriptions/${subscriptionId}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${getToken()}`
          },
          body: JSON.stringify(updates)
        }
      );
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscriptions'] });
    }
  });

  // Delete subscription
  const deleteSubscription = useMutation({
    mutationFn: async (subscriptionId: string) => {
      const response = await fetch(
        `/api/v1/user/alerts/subscriptions/${subscriptionId}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${getToken()}` }
        }
      );
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'subscriptions'] });
    }
  });

  // Listen for real-time alerts via WebSocket
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('alert_triggered', (alert: Alert) => {
      // Show toast notification
      toast.warning(alert.message, {
        action: {
          label: 'View',
          onClick: () => {/* Navigate to alert */}
        }
      });

      // Invalidate queries to refresh alert list
      queryClient.invalidateQueries({ queryKey: ['alerts', 'active'] });
    });

    return unsubscribe;
  }, [subscribe, queryClient]);

  return {
    alerts: alerts?.alerts || [],
    unacknowledgedCount: alerts?.unacknowledged_count || 0,
    subscriptions: subscriptions?.subscriptions || [],
    isLoading,
    createSubscription,
    acknowledgeAlert,
    updateSubscription,
    deleteSubscription
  };
};

// Alerts Dashboard Component
export const AlertsDashboard = () => {
  const {
    alerts,
    unacknowledgedCount,
    subscriptions,
    acknowledgeAlert,
    createSubscription
  } = useAlerts();

  const [showCreateModal, setShowCreateModal] = useState(false);

  return (
    <div className="alerts-dashboard">
      <header>
        <h1>Risk Alerts</h1>
        {unacknowledgedCount > 0 && (
          <Badge variant="warning">
            {unacknowledgedCount} unacknowledged
          </Badge>
        )}
        <Button onClick={() => setShowCreateModal(true)}>
          Create Alert
        </Button>
      </header>

      {/* Active Alerts */}
      <section>
        <h2>Active Alerts</h2>
        <AlertsList
          alerts={alerts}
          onAcknowledge={(id) => acknowledgeAlert.mutate(id)}
        />
      </section>

      {/* Subscriptions */}
      <section>
        <h2>Alert Subscriptions</h2>
        <SubscriptionsList subscriptions={subscriptions} />
      </section>

      {/* Create Alert Modal */}
      {showCreateModal && (
        <CreateAlertModal
          onClose={() => setShowCreateModal(false)}
          onCreate={(subscription) => {
            createSubscription.mutate(subscription);
            setShowCreateModal(false);
          }}
        />
      )}
    </div>
  );
};
```

---

## 📊 Dashboard & Insights Flows

### Flow 6: Dashboard & Aggregation

**Module**: `dashboard/`
**Endpoints**: 2 endpoints
**Priority**: CRITICAL

#### Journey: Daily Dashboard Check

```
START: User opens app in the morning
  │
  ├─> 1. Load Dashboard Overview
  │   API: GET /api/v1/user/dashboard
  │
  │   Response: {
  │     ai_insights: [
  │       {
  │         insight_type: "opportunity",
  │         title: "High yield opportunity detected",
  │         description: "Curve stETH/ETH pool APY increased to 8.2%",
  │         confidence: 0.89,
  │         action_recommended: "Consider increasing allocation",
  │         priority: "high"
  │       },
  │       {
  │         insight_type: "risk_warning",
  │         title: "Elevated risk on Aave V3",
  │         description: "Risk score increased from 6.5 to 8.3 due to market volatility",
  │         confidence: 0.92,
  │         action_recommended: "Review position or set stop-loss",
  │         priority: "high"
  │       },
  │       // ... more insights
  │     ],
  │     portfolio_summary: {
  │       total_value_usd: 125430.50,
  │       change_24h_usd: 2345.20,
  │       change_24h_percent: 1.9,
  │       active_positions: 12,
  │       protocols_used: 8
  │     },
  │     performance_metrics: {
  │       total_pnl_usd: 15670.30,
  │       total_pnl_percent: 14.3,
  │       best_performing_protocol: {
  │         name: "Curve Finance",
  │         pnl_percent: 22.5
  │       },
  │       worst_performing_protocol: {
  │         name: "Uniswap V3",
  │         pnl_percent: -3.2
  │       }
  │     },
  │     risk_overview: {
  │       overall_risk_score: 6.8,
  │       risk_level: "moderate",
  │       risk_distribution: {
  │         low_risk: 3,
  │         medium_risk: 6,
  │         high_risk: 3
  │       },
  │       recommendations: [
  │         "Reduce exposure to high-risk protocols",
  │         "Consider diversifying into stablecoins"
  │       ]
  │     },
  │     recent_activity: [
  │       {
  │         type: "deposit",
  │         protocol: "Aave V3",
  │         amount_usd: 5000,
  │         timestamp: "2025-12-17T08:30:00Z"
  │       },
  │       // ... more activity
  │     ]
  │   }
  │
  │   UI: Renders comprehensive dashboard
  │
  ├─> 2. Dashboard Layout
  │   ┌────────────────────────────────────────────────────────┐
  │   │  🏠 Dashboard                      Last updated: 1m ago│
  │   ├────────────────────────────────────────────────────────┤
  │   │                                                        │
  │   │  🤖 AI Insights (2 high priority)                     │
  │   │  ┌──────────────────────────────────────────────────┐ │
  │   │  │ 🟢 Opportunity: High yield detected              │ │
  │   │  │ Curve stETH/ETH pool APY → 8.2% (89% confidence)│ │
  │   │  │ [View Details] [Take Action]                     │ │
  │   │  └──────────────────────────────────────────────────┘ │
  │   │  ┌──────────────────────────────────────────────────┐ │
  │   │  │ 🔴 Risk Warning: Elevated risk on Aave V3        │ │
  │   │  │ Risk score: 6.5 → 8.3 (92% confidence)          │ │
  │   │  │ [Review Position] [Set Alert]                    │ │
  │   │  └──────────────────────────────────────────────────┘ │
  │   │                                                        │
  │   │  💰 Portfolio Summary                                 │
  │   │  ┌──────┬──────┬─────────┬──────────────┐           │
  │   │  │$125K │+1.9%│12 active│  8 protocols │           │
  │   │  │Total │24h  │positions│              │           │
  │   │  └──────┴──────┴─────────┴──────────────┘           │
  │   │                                                        │
  │   │  📊 Performance (Chart)                               │
  │   │  [Line chart showing 7-day performance]               │
  │   │                                                        │
  │   │  ⚠️ Risk Overview                                     │
  │   │  Overall Risk: 6.8/10 (Moderate)                     │
  │   │  ██████░░░░ Low: 3  Medium: 6  High: 3               │
  │   │                                                        │
  │   │  📜 Recent Activity                                   │
  │   │  • Deposited $5K to Aave V3 - 2h ago                 │
  │   │  • Claimed rewards from Curve - 4h ago               │
  │   │                                                        │
  │   └────────────────────────────────────────────────────────┘
  │
  ├─> 3. Interact with AI Insights
  │   User: Clicks "View Details" on high yield opportunity
  │
  │   Modal Opens:
  │   ┌────────────────────────────────────────────┐
  │   │  High Yield Opportunity                    │
  │   ├────────────────────────────────────────────┤
  │   │                                            │
  │   │  Protocol: Curve Finance                   │
  │   │  Pool: stETH/ETH                          │
  │   │  Current APY: 8.2% (↑ from 6.1%)         │
  │   │                                            │
  │   │  Why this is an opportunity:               │
  │   │  • APY 34% above historical average       │
  │   │  • Pool TVL stable ($850M)                │
  │   │  • Low impermanent loss risk (ETH/stETH)  │
  │   │                                            │
  │   │  Risk Assessment:                          │
  │   │  • Protocol Risk: Low (7.5/10)            │
  │   │  • Smart Contract Risk: Low               │
  │   │  • Market Risk: Moderate                  │
  │   │                                            │
  │   │  Recommended Action:                       │
  │   │  "Consider allocating 10-15% of ETH       │
  │   │   holdings to this pool"                  │
  │   │                                            │
  │   │  [Go to Pool] [Set Price Alert] [Dismiss] │
  │   └────────────────────────────────────────────┘
  │
  ├─> 4. Quick Actions
  │   User can:
  │   - Click on protocol → Navigate to details
  │   - Click on risk score → View full risk analysis
  │   - Click on PnL → View detailed breakdown
  │   - Refresh dashboard (pull-to-refresh on mobile)
  │
  └─> END: User informed and ready to take action
```

#### Integration Pattern: Dashboard with Real-time Updates

```typescript
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

interface DashboardData {
  ai_insights: Array<{
    insight_type: string;
    title: string;
    description: string;
    confidence: number;
    action_recommended: string;
    priority: string;
  }>;
  portfolio_summary: {
    total_value_usd: number;
    change_24h_usd: number;
    change_24h_percent: number;
    active_positions: number;
    protocols_used: number;
  };
  performance_metrics: any;
  risk_overview: any;
  recent_activity: any[];
}

export const useDashboard = () => {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await fetch('/api/v1/user/dashboard', {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      return response.json() as Promise<DashboardData>;
    },
    refetchInterval: 60000, // Refresh every minute
    staleTime: 30000 // Consider stale after 30s
  });

  // Auto-refresh on window focus
  useEffect(() => {
    const handleFocus = () => {
      refetch();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refetch]);

  return {
    dashboard: data,
    isLoading,
    refetch
  };
};

// Dashboard Component
export const Dashboard = () => {
  const { dashboard, isLoading, refetch } = useDashboard();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="dashboard">
      {/* Header */}
      <header>
        <h1>Dashboard</h1>
        <button onClick={() => refetch()} aria-label="Refresh dashboard">
          <RefreshIcon />
        </button>
      </header>

      {/* AI Insights */}
      <section className="ai-insights">
        <h2>AI Insights</h2>
        {dashboard.ai_insights
          .filter(i => i.priority === 'high')
          .map((insight, index) => (
            <InsightCard key={index} insight={insight} />
          ))}
      </section>

      {/* Portfolio Summary */}
      <section className="portfolio-summary">
        <StatCard
          label="Total Value"
          value={`$${dashboard.portfolio_summary.total_value_usd.toLocaleString()}`}
          change={dashboard.portfolio_summary.change_24h_percent}
          trend={dashboard.portfolio_summary.change_24h_percent > 0 ? 'up' : 'down'}
        />
        {/* More stat cards */}
      </section>

      {/* Performance Chart */}
      <section className="performance">
        <h2>Performance</h2>
        <PerformanceChart data={dashboard.performance_metrics} />
      </section>

      {/* Risk Overview */}
      <section className="risk-overview">
        <h2>Risk Overview</h2>
        <RiskGauge score={dashboard.risk_overview.overall_risk_score} />
        <RiskDistribution data={dashboard.risk_overview.risk_distribution} />
      </section>

      {/* Recent Activity */}
      <section className="recent-activity">
        <h2>Recent Activity</h2>
        <ActivityTimeline activities={dashboard.recent_activity} />
      </section>
    </div>
  );
};

// Insight Card Component
const InsightCard = ({ insight }: { insight: any }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getIcon = (type: string) => {
    switch (type) {
      case 'opportunity': return '🟢';
      case 'risk_warning': return '🔴';
      case 'info': return '🔵';
      default: return '⚪';
    }
  };

  return (
    <div className={`insight-card priority-${insight.priority}`}>
      <div className="insight-header">
        <span className="insight-icon">{getIcon(insight.insight_type)}</span>
        <h3>{insight.title}</h3>
        <span className="confidence">{(insight.confidence * 100).toFixed(0)}%</span>
      </div>

      <p>{insight.description}</p>

      <div className="insight-actions">
        <Button onClick={() => setShowDetails(true)}>
          View Details
        </Button>
        <Button variant="secondary">
          {insight.action_recommended}
        </Button>
      </div>

      {showDetails && (
        <InsightDetailsModal
          insight={insight}
          onClose={() => setShowDetails(false)}
        />
      )}
    </div>
  );
};
```

---

### Flow 7: Markets & Data

**Module**: `markets/`
**Endpoints**: 4 endpoints
**Priority**: CRITICAL

#### Quick Flow: Market Overview

```typescript
// Get market overview with ML risk scores
const { data: markets } = useQuery({
  queryKey: ['markets', 'overview'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/markets/overview');
    return response.json();
  }
});

// Markets response includes:
// - Protocol yields (APY, TVL, risk scores)
// - Token prices and 24h changes
// - ML-powered risk predictions
// - Multi-chain data aggregation
```

**Key Integration**: Connects to Dashboard, Portfolio Risk, and GraphRAG for comprehensive market intelligence.

---

### Flow 8: Portfolio Risk Analysis

**Module**: `portfolio/`
**Endpoints**: 2 endpoints
**Priority**: CRITICAL

#### Quick Flow: Risk Assessment

```typescript
// Get comprehensive portfolio risk analysis
const { data: riskAnalysis } = useQuery({
  queryKey: ['portfolio', 'risk'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/portfolio/risk');
    return response.json();
  }
});

// Risk analysis includes:
// - Overall risk score (0-10)
// - Protocol-level breakdown
// - Dependency risk analysis
// - Cascade failure simulation
// - Systemic risk assessment
// - Actionable recommendations
```

**Key Integration**: Powers Dashboard insights and Risk Alerts.

---

## 🔬 Advanced Features Flows

### Flow 9: GraphRAG & Analytics

**Module**: `graph/`
**Endpoints**: 8 endpoints
**Priority**: HIGH

#### Journey: Intelligent Protocol Discovery

```
START: User wants to find protocols similar to Aave
  │
  ├─> 1. Hybrid Search
  │   API: POST /api/v1/user/graph/hybrid-search
  │   Request: {
  │     query: "lending protocols like Aave",
  │     limit: 10,
  │     use_graph: true,
  │     use_semantic: true
  │   }
  │
  │   Response: {
  │     results: [
  │       {
  │         protocol_id: "compound-v3",
  │         name: "Compound V3",
  │         similarity_score: 0.89,
  │         match_type: "graph_semantic",
  │         reasoning: "Similar lending mechanism and collateral types"
  │       },
  │       // ... more results
  │     ],
  │     search_metadata: {
  │       graph_results: 7,
  │       semantic_results: 8,
  │       hybrid_score: 0.92
  │     }
  │   }
  │
  ├─> 2. Similar Protocols Discovery
  │   API: POST /api/v1/user/graph/similar-protocols
  │   Request: {
  │     protocol_id: "aave-v3",
  │     limit: 5,
  │     similarity_threshold: 0.7
  │   }
  │
  │   Response: {
  │     similar_protocols: [
  │       {
  │         protocol_id: "morpho-blue",
  │         similarity_score: 0.85,
  │         shared_features: ["lending", "overcollateralized", "liquidations"],
  │         key_differences: ["rate_optimization", "vault_structure"]
  │       },
  │       // ... more similar protocols
  │     ]
  │   }
  │
  ├─> 3. Graph Analytics
  │   API: GET /api/v1/user/graph/analytics
  │
  │   Response: {
  │     node_count: 1247,
  │     edge_count: 5892,
  │     avg_degree: 4.7,
  │     clustering_coefficient: 0.34,
  │     network_density: 0.0038
  │   }
  │
  └─> END: User discovers similar protocols with graph insights
```

**Integration Pattern**:

```typescript
export const useGraphRAGSearch = () => {
  const hybridSearch = useMutation({
    mutationFn: async (query: string) => {
      const response = await fetch('/api/v1/user/graph/hybrid-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          query,
          limit: 10,
          use_graph: true,
          use_semantic: true
        })
      });
      return response.json();
    }
  });

  const findSimilar = useMutation({
    mutationFn: async (protocolId: string) => {
      const response = await fetch('/api/v1/user/graph/similar-protocols', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          protocol_id: protocolId,
          limit: 5,
          similarity_threshold: 0.7
        })
      });
      return response.json();
    }
  });

  return { hybridSearch, findSimilar };
};
```

---

### Flow 10: Projects & Workspaces

**Module**: `projects/`
**Endpoints**: 5 endpoints
**Priority**: MEDIUM

#### Quick Flow: Project Management

```typescript
// Get assigned projects
const { data: projects } = useQuery({
  queryKey: ['projects', 'assigned'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/projects/assigned');
    return response.json();
  }
});

// Select active project
const selectProject = useMutation({
  mutationFn: async (projectId: string) => {
    const response = await fetch(`/api/v1/user/projects/${projectId}/select`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken()}` }
    });
    return response.json();
  },
  onSuccess: () => {
    // Refresh dashboard and preferences
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    queryClient.invalidateQueries({ queryKey: ['preferences'] });
  }
});
```

---

### Flow 11: Notifications

**Module**: `notifications/`
**Endpoints**: 1 endpoint
**Priority**: MEDIUM

#### Quick Flow: Notification Center

```typescript
// Paginated notifications
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ['notifications'],
  queryFn: async ({ pageParam = 1 }) => {
    const response = await fetch(
      `/api/v1/user/notifications?page=${pageParam}&page_size=20`
    );
    return response.json();
  },
  getNextPageParam: (lastPage) =>
    lastPage.page < Math.ceil(lastPage.total / lastPage.page_size)
      ? lastPage.page + 1
      : undefined
});

// Infinite scroll implementation
<InfiniteScroll
  dataLength={data?.pages.flatMap(p => p.items).length || 0}
  next={fetchNextPage}
  hasMore={hasNextPage}
  loader={<Spinner />}
>
  {data?.pages.flatMap(page => page.items).map(notification => (
    <NotificationCard key={notification.id} notification={notification} />
  ))}
</InfiniteScroll>
```

---

## 🛠️ Utilities & System Flows

### Flow 12: Metrics & Analytics

**Module**: `metrics/`
**Endpoints**: 5 endpoints
**Priority**: MEDIUM

#### Quick Flow: Event Tracking

```typescript
// Track user events
const trackEvent = async (eventType: string, metadata?: object) => {
  await fetch('/api/v1/user/metrics/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${getToken()}`
    },
    body: JSON.stringify({
      event_type: eventType,
      metadata: metadata || {},
      timestamp: new Date().toISOString()
    })
  });
};

// Usage
trackEvent('protocol_viewed', { protocol_id: 'aave-v3' });
trackEvent('search_performed', { query: 'stablecoin yield' });
trackEvent('comparison_created', { protocols: ['aave', 'compound'] });

// Get analytics summary
const { data: analytics } = useQuery({
  queryKey: ['metrics', 'summary'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/metrics/summary');
    return response.json();
  }
});
```

---

### Flow 13: ML Prediction

**Module**: `ml/`
**Endpoints**: 4 endpoints
**Priority**: HIGH

#### Quick Flow: Risk Prediction

```typescript
// Single protocol risk prediction
const predictRisk = useMutation({
  mutationFn: async (protocolId: string) => {
    const response = await fetch('/api/v1/user/ml/predict/risk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`
      },
      body: JSON.stringify({ protocol_id: protocolId })
    });
    return response.json();
  }
});

// Response includes:
// {
//   protocol_id: "aave-v3",
//   risk_score: 7.2,
//   confidence: 0.87,
//   factors: [
//     { factor: "tvl_volatility", impact: 0.3 },
//     { factor: "smart_contract_risk", impact: 0.15 }
//   ],
//   forecast_7d: [7.3, 7.1, 7.0, ...],
//   anomalies_detected: false
// }

// Batch risk prediction
const { data: batchPredictions } = useQuery({
  queryKey: ['ml', 'risk', 'batch', protocolIds],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/ml/predict/risk/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        protocol_ids: protocolIds,
        include_forecast: true
      })
    });
    return response.json();
  },
  enabled: protocolIds.length > 0
});
```

---

### Flow 14: ML Network Analysis

**Module**: `ml/` (network)
**Endpoints**: 4 endpoints
**Priority**: MEDIUM

#### Quick Flow: Network Intelligence

```typescript
// PageRank analysis
const { data: pagerank } = useQuery({
  queryKey: ['ml', 'network', 'pagerank'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/ml/network/pagerank');
    return response.json();
  }
});

// Community detection
const { data: communities } = useQuery({
  queryKey: ['ml', 'network', 'communities'],
  queryFn: async () => {
    const response = await fetch('/api/v1/user/ml/network/communities');
    return response.json();
  }
});

// Contagion simulation
const simulateContagion = useMutation({
  mutationFn: async (params: {
    source_protocol: string;
    contagion_type: 'liquidity' | 'price' | 'exploit';
    intensity: number;
  }) => {
    const response = await fetch('/api/v1/user/ml/network/contagion', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`
      },
      body: JSON.stringify(params)
    });
    return response.json();
  }
});

// Use case: Simulate Aave exploit contagion
simulateContagion.mutate({
  source_protocol: 'aave-v3',
  contagion_type: 'exploit',
  intensity: 0.8
});
```

---

## 🔄 Cross-Module Integration Patterns

### Pattern 1: Dashboard-Driven Workflow

User journey spanning multiple modules:

```
Dashboard → Alerts → Markets → Portfolio → GraphRAG → Comparison → Decision
```

**Implementation**:

```typescript
const DashboardWorkflow = () => {
  // 1. Load dashboard (Flow 6)
  const { data: dashboard } = useDashboard();

  // 2. Check high-priority alerts (Flow 5)
  const { alerts, unacknowledgedCount } = useAlerts();

  // 3. Load market data for alerted protocols (Flow 7)
  const alertedProtocols = alerts
    .filter(a => a.severity === 'high')
    .map(a => a.protocol_id);

  const { data: markets } = useQuery({
    queryKey: ['markets', alertedProtocols],
    queryFn: () => fetchMarketData(alertedProtocols),
    enabled: alertedProtocols.length > 0
  });

  // 4. Trigger portfolio risk analysis (Flow 8)
  const { data: riskAnalysis } = useQuery({
    queryKey: ['portfolio', 'risk'],
    queryFn: fetchPortfolioRisk
  });

  // 5. If high risk detected, search for safer alternatives (Flow 9)
  const { hybridSearch } = useGraphRAGSearch();

  const handleFindAlternatives = async (protocol: string) => {
    const results = await hybridSearch.mutateAsync(
      `safer alternatives to ${protocol}`
    );
    // 6. Compare alternatives (Flow 4)
    navigateToComparison(results.map(r => r.protocol_id));
  };

  return (
    <div>
      <DashboardOverview data={dashboard} />
      <AlertsSummary alerts={alerts} count={unacknowledgedCount} />
      <MarketSnapshot data={markets} />
      <RiskGauge risk={riskAnalysis} onFindAlternatives={handleFindAlternatives} />
    </div>
  );
};
```

---

### Pattern 2: Real-time Data Synchronization

WebSocket + React Query integration:

```typescript
const useRealtimeSync = () => {
  const queryClient = useQueryClient();
  const { subscribe } = useWebSocket();

  useEffect(() => {
    // Subscribe to various real-time events
    const unsubscribeAlerts = subscribe('alert_triggered', (alert) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      queryClient.setQueryData(['alerts', 'latest'], alert);
    });

    const unsubscribeMarkets = subscribe('market_update', (update) => {
      queryClient.setQueryData(
        ['markets', 'overview'],
        (old: any) => ({
          ...old,
          protocols: old.protocols.map((p: any) =>
            p.id === update.protocol_id
              ? { ...p, ...update.data }
              : p
          )
        })
      );
    });

    const unsubscribePortfolio = subscribe('portfolio_update', () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    });

    return () => {
      unsubscribeAlerts();
      unsubscribeMarkets();
      unsubscribePortfolio();
    };
  }, [subscribe, queryClient]);
};
```

---

### Pattern 3: Unified Search Experience

Combining Search + GraphRAG + Markets:

```typescript
const UnifiedSearch = () => {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  // 1. Search history (Flow 3)
  const { executeSearch } = useSearch();

  // 2. GraphRAG hybrid search (Flow 9)
  const { hybridSearch } = useGraphRAGSearch();

  // 3. Market data for results (Flow 7)
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = async (searchQuery: string) => {
    // Log search
    executeSearch(searchQuery);

    // Perform hybrid search
    const results = await hybridSearch.mutateAsync(searchQuery);

    // Enrich with market data
    const enrichedResults = await enrichWithMarketData(results);

    setSearchResults(enrichedResults);
  };

  const enrichWithMarketData = async (results: any[]) => {
    const protocolIds = results.map(r => r.protocol_id);
    const marketData = await fetchMarketData(protocolIds);

    return results.map(result => ({
      ...result,
      market_data: marketData.find(m => m.protocol_id === result.protocol_id)
    }));
  };

  return (
    <div>
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
      />
      <SearchResults results={searchResults} />
    </div>
  );
};
```

---

## ⚠️ Global Error Handling

### Error Handling Strategy

```typescript
// Global error handler
export const globalErrorHandler = (error: Error) => {
  if (error instanceof NetworkError) {
    toast.error('Network connection lost. Retrying...');
    // Implement retry logic
  } else if (error instanceof AuthenticationError) {
    // Clear tokens and redirect to login
    logout();
  } else if (error instanceof RateLimitError) {
    toast.warning('Rate limit exceeded. Please wait a moment.');
  } else if (error instanceof ValidationError) {
    toast.error(`Validation failed: ${error.message}`);
  } else {
    // Generic error
    toast.error('Something went wrong. Please try again.');
    // Log to error tracking service
    logError(error);
  }
};

// React Query global error handler
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      onError: globalErrorHandler,
      retry: (failureCount, error) => {
        // Don't retry on auth errors
        if (error instanceof AuthenticationError) return false;
        // Retry up to 3 times on network errors
        if (error instanceof NetworkError) return failureCount < 3;
        return failureCount < 1;
      }
    },
    mutations: {
      onError: globalErrorHandler
    }
  }
});

// Error boundary
export class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    return this.props.children;
  }
}
```

---

## 🚀 Performance & Optimization

### Optimization Strategies

**1. Code Splitting**

```typescript
// Lazy load heavy modules
const Dashboard = lazy(() => import('./pages/Dashboard'));
const GraphRAG = lazy(() => import('./pages/GraphRAG'));
const Analytics = lazy(() => import('./pages/Analytics'));

// Route-based code splitting
<Routes>
  <Route path="/dashboard" element={
    <Suspense fallback={<LoadingSpinner />}>
      <Dashboard />
    </Suspense>
  } />
</Routes>
```

**2. Data Prefetching**

```typescript
// Prefetch likely next pages
const prefetchDashboard = () => {
  queryClient.prefetchQuery({
    queryKey: ['dashboard'],
    queryFn: fetchDashboard
  });
};

// Prefetch on hover
<Link to="/dashboard" onMouseEnter={prefetchDashboard}>
  Dashboard
</Link>
```

**3. Optimistic Updates**

```typescript
const updatePreferences = useMutation({
  mutationFn: savePreferences,
  onMutate: async (newPreferences) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['preferences'] });

    // Snapshot current value
    const previous = queryClient.getQueryData(['preferences']);

    // Optimistically update
    queryClient.setQueryData(['preferences'], newPreferences);

    return { previous };
  },
  onError: (err, newPreferences, context) => {
    // Rollback on error
    queryClient.setQueryData(['preferences'], context?.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['preferences'] });
  }
});
```

**4. Virtual Scrolling**

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

const VirtualList = ({ items }: { items: any[] }) => {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // Estimated item height
    overscan: 5 // Render 5 extra items above/below viewport
  });

  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: 'relative' }}>
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`
            }}
          >
            <ItemCard item={items[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
};
```

**5. Memoization**

```typescript
// Expensive computations
const MemoizedComponent = React.memo(({ data }) => {
  const processedData = useMemo(() => {
    return expensiveCalculation(data);
  }, [data]);

  const handleClick = useCallback(() => {
    // Handle click
  }, []);

  return <div onClick={handleClick}>{processedData}</div>;
});
```

---

## ♿ Accessibility Guidelines

### WCAG 2.1 AA Compliance

**1. Semantic HTML**

```typescript
// Good
<nav role="navigation" aria-label="Main navigation">
  <ul>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

<main id="main-content">
  <h1>Dashboard</h1>
  <section aria-labelledby="alerts-heading">
    <h2 id="alerts-heading">Alerts</h2>
  </section>
</main>

// Bad
<div className="nav">
  <div className="link">Dashboard</div>
</div>
```

**2. Keyboard Navigation**

```typescript
const KeyboardAccessible = () => {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        handleClick();
        break;
      case 'Escape':
        handleClose();
        break;
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleClick}
      aria-label="Close dialog"
    >
      Close
    </div>
  );
};
```

**3. Screen Reader Support**

```typescript
// Live regions for dynamic content
<div role="status" aria-live="polite" aria-atomic="true">
  {isLoading && 'Loading...'}
  {error && `Error: ${error.message}`}
  {data && 'Data loaded successfully'}
</div>

// Alerts for urgent updates
<div role="alert" aria-live="assertive">
  {criticalAlert && `Critical: ${criticalAlert.message}`}
</div>

// Hidden text for screen readers only
<span className="sr-only">
  Loading dashboard data, please wait
</span>
```

**4. Focus Management**

```typescript
const Modal = ({ isOpen, onClose }: ModalProps) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Store current focus
      previousFocus.current = document.activeElement as HTMLElement;

      // Focus first element in modal
      const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();

      // Trap focus within modal
      const handleTabKey = (e: KeyboardEvent) => {
        const focusableElements = modalRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements?.[0];
        const lastElement = focusableElements?.[focusableElements.length - 1];

        if (e.key === 'Tab') {
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement?.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement?.focus();
          }
        }
      };

      document.addEventListener('keydown', handleTabKey);
      return () => document.removeEventListener('keydown', handleTabKey);
    } else {
      // Restore focus
      previousFocus.current?.focus();
    }
  }, [isOpen]);

  return isOpen ? (
    <div ref={modalRef} role="dialog" aria-modal="true">
      {/* Modal content */}
    </div>
  ) : null;
};
```

**5. Color Contrast**

```css
/* Ensure WCAG AA contrast ratios */
:root {
  /* Text on white background - 4.5:1 minimum */
  --text-primary: #1a1a1a;      /* 20.8:1 ✓ */
  --text-secondary: #555555;    /* 8.6:1 ✓ */

  /* Interactive elements - 3:1 minimum for large text, UI components */
  --primary: #0056b3;           /* 7.2:1 ✓ */
  --success: #0f7b3d;           /* 4.6:1 ✓ */
  --warning: #856404;           /* 5.1:1 ✓ */
  --error: #c82333;             /* 5.5:1 ✓ */
}

/* Never rely on color alone */
.error-message {
  color: var(--error);
  /* Also use icon */
  &::before {
    content: "⚠️ ";
  }
}
```

---

## 📊 Implementation Checklist

### Module Implementation Order (Recommended)

**Phase 1: Foundation (Week 1)**
- [x] Authentication & Account
- [x] User Preferences
- [x] Dashboard Overview
- [ ] Markets & Data

**Phase 2: Core Features (Week 2)**
- [ ] Search & Discovery
- [ ] Portfolio Risk
- [ ] Risk Alerts
- [ ] Notifications

**Phase 3: Advanced Features (Week 3)**
- [ ] Protocol Comparison
- [ ] GraphRAG Search
- [ ] Chat Integration
- [ ] Analytics Dashboard

**Phase 4: Intelligence (Week 4)**
- [ ] ML Prediction
- [ ] ML Network Analysis
- [ ] Metrics Tracking
- [ ] Projects Management

**Phase 5: Polish & Optimize (Week 5)**
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] Cross-module integration
- [ ] Error handling refinement

---

## 🎯 Success Metrics

### Key Performance Indicators

**User Engagement:**
- Dashboard daily active users >60%
- Search usage >40% of sessions
- Alert interaction rate >70%
- GraphRAG adoption >30%

**Performance:**
- Initial load time <2s
- Time to interactive <3s
- API response time P95 <500ms
- WebSocket message latency <100ms

**Reliability:**
- Uptime >99.9%
- Error rate <0.1%
- Successful reconnection >98%
- Data consistency 100%

**Accessibility:**
- WCAG 2.1 AA compliance 100%
- Keyboard navigation coverage 100%
- Screen reader compatibility 100%

---

## 📚 Additional Resources

**Related Documentation:**
- [CHAT_ENDPOINT_FLOWS_SPECIFICATION.md](./chat/CHAT_ENDPOINT_FLOWS_SPECIFICATION.md) - Chat module flows
- [FRONTEND_API_COMPLETE_REFERENCE.md](../FRONTEND_API_COMPLETE_REFERENCE.md) - API reference
- [ERROR_CODES_REFERENCE.md](../ERROR_CODES_REFERENCE.md) - Error handling
- [USER_MODULES_INDEX.md](./USER_MODULES_INDEX.md) - Module index

**Integration Guides:**
- GraphRAG Integration
- WebSocket Real-time Updates
- ML Prediction Integration
- Multi-module Workflows

---

## 🔄 Version History

**v1.0** (December 17, 2025)
- Initial release
- Covers all 17 user modules
- Complete flow documentation
- TypeScript integration patterns
- Accessibility guidelines

**Coverage:**
- 6 detailed flows (Auth, Preferences, Search, Comparison, Alerts, Dashboard)
- 11 condensed flows (Markets, Portfolio, GraphRAG, Projects, Notifications, Metrics, ML x2)
- Cross-module patterns
- Global error handling
- Performance optimization
- Accessibility compliance

---

## ✅ Summary

This master specification provides **complete coverage** of all user-facing modules:

✅ **17 Modules Documented**
✅ **69+ Endpoints Covered**
✅ **Production-Ready Code Patterns**
✅ **TypeScript + React Integration**
✅ **Real-time WebSocket Patterns**
✅ **Cross-Module Workflows**
✅ **Global Error Handling**
✅ **Performance Optimization**
✅ **WCAG 2.1 AA Accessibility**

**Status**: Ready for frontend implementation 🚀

---

**Last Updated**: December 17, 2025
**Maintained By**: Frontend Team
**Version**: 1.0 - Complete
