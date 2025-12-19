# Frontend Migration Guide - API Path Updates

**Date:** December 19, 2025  
**Status:** ⚠️ Frontend updates required

## Overview

All backend user endpoints have been updated to use the `/api/v1/user/` prefix. The frontend codebase needs to be updated to reflect these changes.

## Required Frontend Updates

### 1. Update API Configuration

**File:** `anvil_frontend/src/setup/config/api.ts`

Update the following endpoints:

```typescript
export const ENDPOINTS = {
  // ... existing auth endpoints (unchanged)
  
  // ❌ OLD - Remove these
  transactions: {
    list: '/api/v1/transactions',  // ❌
    detail: (id: number) => `/api/v1/transactions/${id}`,  // ❌
  },
  portfolio: {
    me: '/api/v1/portfolio/me',  // ❌
    byAddress: (walletAddress: string) => `/api/v1/portfolio/${walletAddress}`,  // ❌
  },
  
  // ✅ NEW - Add these
  transactions: {
    list: '/api/v1/user/transactions',  // ✅
    detail: (id: number) => `/api/v1/user/transactions/${id}`,  // ✅
  },
  portfolio: {
    me: '/api/v1/user/portfolio/me',  // ✅
    byAddress: (walletAddress: string) => `/api/v1/user/portfolio/${walletAddress}`,  // ✅
  },
  
  // ✅ NEW - Add user endpoints
  graph: {
    analytics: '/api/v1/user/graph/analytics/overview',
    search: {
      hybrid: '/api/v1/user/graph/search/hybrid',
      similar: '/api/v1/user/graph/search/similar',
      contextual: '/api/v1/user/graph/search/contextual',
    },
  },
  ml: {
    prediction: (protocolId: string) => `/api/v1/user/ml/prediction/${protocolId}`,
    batch: '/api/v1/user/ml/prediction/batch',
    network: {
      pagerank: '/api/v1/user/ml/network/pagerank',
      communities: '/api/v1/user/ml/network/communities',
      centrality: '/api/v1/user/ml/network/centrality',
    },
  },
  alerts: {
    risk: '/api/v1/user/alerts/risk',
    acknowledge: (alertId: string) => `/api/v1/user/alerts/risk/${alertId}/acknowledge`,
    subscription: '/api/v1/user/alerts/subscription',
  },
  dashboard: {
    insights: '/api/v1/user/dashboard/insights',
    summary: '/api/v1/user/dashboard/summary',
  },
  comparison: {
    protocols: '/api/v1/user/comparison/protocols',
  },
  markets: {
    overview: '/api/v1/user/markets/overview',
    token: (symbol: string) => `/api/v1/user/markets/tokens/${symbol}`,
    yields: '/api/v1/user/markets/yields',
  },
  bitcoin: {
    transactions: '/api/v1/user/bitcoin/transactions',
    wallets: {
      create: '/api/v1/user/bitcoin/wallets/create',
      me: '/api/v1/user/bitcoin/wallets/me',
    },
  },
  search: {
    history: '/api/v1/user/search/history',
  },
  preferences: {
    get: '/api/v1/user/preferences',
    update: '/api/v1/user/preferences',
  },
  hunter: {
    patterns: {
      chart: (token: string) => `/api/v1/user/hunter/patterns/chart/${token}`,
      candlestick: (token: string) => `/api/v1/user/hunter/patterns/candlestick/${token}`,
    },
    signals: {
      generate: (token: string) => `/api/v1/user/hunter/signals/generate/${token}`,
    },
    // ... add more hunter endpoints as needed
  },
  ultra: {
    flashLoans: {
      protocols: '/api/v1/user/ultra/flash-loans/protocols',
      bestProtocol: '/api/v1/user/ultra/flash-loans/best-protocol',
    },
    arbitrage: {
      discover: '/api/v1/user/ultra/arbitrage/discover',
      opportunities: '/api/v1/user/ultra/arbitrage/opportunities',
    },
    mev: {
      execute: '/api/v1/user/ultra/mev/execute',
      statistics: '/api/v1/user/ultra/mev/statistics',
    },
  },
  projects: {
    list: '/api/v1/user/projects/',
    available: '/api/v1/user/projects/available',
    join: (projectId: string) => `/api/v1/user/projects/${projectId}/join`,
  },
} as const;
```

### 2. Search and Replace in Frontend Code

Search for these patterns and update:

```bash
# Find all old endpoint references
grep -r "/api/v1/graph" src/
grep -r "/api/v1/ml" src/
grep -r "/api/v1/alerts" src/
grep -r "/api/v1/dashboard" src/
grep -r "/api/v1/comparison" src/
grep -r "/api/v1/markets" src/
grep -r "/api/v1/transactions" src/
grep -r "/api/v1/bitcoin" src/
grep -r "/api/v1/portfolio" src/
grep -r "/api/v1/hunter" src/
grep -r "/api/v1/ultra" src/
grep -r "/api/v1/projects" src/
grep -r "/api/v1/search" src/
grep -r "/api/v1/users/me/preferences" src/
```

### 3. Update API Service Files

Check and update any service files that make direct API calls:

- `src/services/graphService.ts` (if exists)
- `src/services/mlService.ts` (if exists)
- `src/services/alertsService.ts` (if exists)
- `src/services/dashboardService.ts` (if exists)
- `src/services/marketsService.ts` (if exists)
- `src/services/portfolioService.ts` (if exists)
- `src/services/hunterService.ts` (if exists)
- `src/services/ultraService.ts` (if exists)

### 4. Update API Documentation

Update any frontend documentation that references API endpoints:

- Component documentation
- API integration guides
- README files
- Type definitions

## Migration Checklist

- [ ] Update `api.ts` configuration file
- [ ] Search and replace all old endpoint paths
- [ ] Update API service files
- [ ] Update component API calls
- [ ] Update documentation
- [ ] Test all API calls
- [ ] Update TypeScript types if needed
- [ ] Update API mock data for tests

## Testing

After updating, test the following:

1. **Authentication** - Ensure all authenticated endpoints work
2. **Graph endpoints** - Test graph search and analytics
3. **ML endpoints** - Test prediction and network analysis
4. **Alerts** - Test alert creation and management
5. **Dashboard** - Test dashboard data loading
6. **Portfolio** - Test portfolio endpoints
7. **Markets** - Test market data endpoints
8. **Hunter AI** - Test all hunter endpoints
9. **ULTRA** - Test flash loans, arbitrage, MEV
10. **Projects** - Test project management

## Backward Compatibility

⚠️ **No backward compatibility** - All old paths have been removed. Frontend must be updated before deployment.

## Support

If you encounter issues:
1. Check the backend logs for 404 errors
2. Verify the endpoint path matches the new structure
3. Ensure authentication tokens are being sent
4. Check the [ENDPOINT_PATH_MAPPING.md](./ENDPOINT_PATH_MAPPING.md) for complete endpoint list

