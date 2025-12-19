# FRONTEND_MARKETS

## Markets & Data Module

**User Type:** Authenticated User  
**Module:** Markets - Real-Time Market Data & Analytics  
**Route:** `/markets`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Markets & Data** - Comprehensive DeFi Market Intelligence

### Description
Real-time market data aggregation providing token prices, protocol yields, trending protocols, and ML-powered risk analysis across multiple blockchain networks.

### Key Capabilities
- ✅ Market overview with trend analysis
- ✅ Protocol yield aggregation
- ✅ Token price data with ML risk scores
- ✅ Historical price charts
- ✅ Multi-chain support
- ✅ Risk-adjusted metrics

---

## 🔌 API Integration

### 1. Get Market Overview

```typescript
// GET /api/v1/markets/overview
// Description: Get comprehensive market overview
// Authentication: Required (Bearer token)

interface MarketOverviewResponse {
  top_tokens: TokenMarketData[];
  trending_protocols: TrendingProtocol[];
  market_trends: MarketTrend;
  recommendations: Recommendation[];
}

const getMarketOverview = async (chains?: string[], riskFilter?: string[]): Promise<MarketOverviewResponse> => {
  const params = new URLSearchParams();
  if (chains) params.append('chains', chains.join(','));
  if (riskFilter) params.append('risk_filter', riskFilter.join(','));
  
  const response = await api.get(`/api/v1/markets/overview?${params}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 2. Get Protocol Yields

```typescript
// GET /api/v1/markets/yields
// Description: Get aggregated protocol yields
// Authentication: Required (Bearer token)

interface ProtocolYield {
  protocol_name: string;
  protocol_id: string;
  chain: string;
  category: 'lending' | 'staking' | 'farming';
  apy: number;
  tvl: number;
  risk_score: number;
  risk_adjusted_apy: number;
}

const getProtocolYields = async (filters: {
  chains?: string[];
  categories?: string[];
  min_apy?: number;
  max_risk?: number;
}): Promise<{yields: ProtocolYield[]}> => {
  const params = new URLSearchParams();
  if (filters.chains) params.append('chains', filters.chains.join(','));
  if (filters.categories) params.append('categories', filters.categories.join(','));
  if (filters.min_apy) params.append('min_apy', filters.min_apy.toString());
  if (filters.max_risk) params.append('max_risk', filters.max_risk.toString());
  
  const response = await api.get(`/api/v1/markets/yields?${params}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 3. Get Token Details

```typescript
// GET /api/v1/markets/tokens/{token_symbol}
// Description: Get detailed token market data
// Authentication: Required (Bearer token)

interface TokenDetails {
  symbol: string;
  name: string;
  price_usd: number;
  market_cap: number;
  volume_24h: number;
  change_24h_percent: number;
  risk_score: number;
  risk_factors: string[];
}

const getTokenDetails = async (tokenSymbol: string): Promise<TokenDetails> => {
  const response = await api.get(`/api/v1/markets/tokens/${tokenSymbol.toUpperCase()}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};
```

### 4. Get Token Price History

```typescript
// GET /api/v1/markets/tokens/{token_symbol}/history
// Description: Get historical price data
// Authentication: Required (Bearer token)

interface PricePoint {
  timestamp: string;
  price: number;
  volume: number;
}

const getTokenHistory = async (
  tokenSymbol: string,
  timeframe: '1h' | '24h' | '7d' | '30d' = '7d'
): Promise<{history: PricePoint[]}> => {
  const response = await api.get(
    `/api/v1/markets/tokens/${tokenSymbol.toUpperCase()}/history?timeframe=${timeframe}`,
    { headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` } }
  );
  return response.data;
};
```

---

## 🔗 React Hooks

```typescript
export function useMarketOverview(chains?: string[], riskFilter?: string[]) {
  return useQuery({
    queryKey: ['markets', 'overview', chains, riskFilter],
    queryFn: () => getMarketOverview(chains, riskFilter),
    refetchInterval: 60000, // 1 minute
  });
}

export function useProtocolYields(filters: any) {
  return useQuery({
    queryKey: ['markets', 'yields', filters],
    queryFn: () => getProtocolYields(filters),
    staleTime: 30000,
  });
}

export function useTokenDetails(symbol: string) {
  return useQuery({
    queryKey: ['markets', 'token', symbol],
    queryFn: () => getTokenDetails(symbol),
    enabled: !!symbol,
  });
}

export function useTokenHistory(symbol: string, timeframe: string = '7d') {
  return useQuery({
    queryKey: ['markets', 'token', symbol, 'history', timeframe],
    queryFn: () => getTokenHistory(symbol, timeframe as any),
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Markets & Data*  
*Backend Status: ✅ 100% Implemented (4 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
