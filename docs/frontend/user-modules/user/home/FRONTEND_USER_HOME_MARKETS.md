# FRONTEND_USER_HOME_MARKETS

## User Markets Module

**User Type:** Authenticated User  
**Module:** Markets  
**Route:** `/markets`  
**Platform:** Mobile (React Native) & Web  
**Version:** 2.0 (Enhanced with ML + GraphRAG + WebSocket)

---

## 📋 Module Overview

### Title
**Markets V2** - Intelligent Token Prices & Risk Analysis

### Description
Enhanced market overview with ML-powered risk indicators, GraphRAG protocol recommendations, real-time WebSocket updates, and personalized insights based on user preferences.

### New Capabilities (V2)
- ✅ **ML Risk Scores** for each token/protocol
- ✅ **GraphRAG Protocol Search** within markets
- ✅ **Real-time price updates** via WebSocket
- ✅ **Risk-based filtering** (show only safe protocols)
- ✅ **Personalized recommendations** based on risk tolerance
- ✅ **Similar protocol suggestions** via GraphRAG
- ✅ **Historical risk trends** visualization

---

## 🖼️ Views & Wireframes

### View 1: Enhanced Markets Screen

```
┌─────────────────────────────────────┐
│  [←]       Markets          [🔍][🎚️]│
│                                     │
│  🔴 LIVE  Risk Filter: [All▼]      │
│                                     │
│  ┌─────────────────────────────────┐│
│  │ [Trending] [Top Gainers] [Losers]│
│  │ [Safest] [GraphRAG] [Your Prefs]│
│  └─────────────────────────────────┘│
│                                     │
│  Trending (with ML Risk)            │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ ETH            🟢 2.1  ││
│  │ │ Ξ   │ Ethereum       $2,510  ││
│  │ └─────┘        ↑ 2.4%   [View] ││
│  │         Risk: LOW  Confidence: 94%│
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ BTC            🟢 1.8  ││
│  │ │ ₿   │ Bitcoin       $43,250  ││
│  │ └─────┘        ↑ 1.8%   [View] ││
│  │         Risk: LOW  Confidence: 96%│
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ARB            🟡 4.2  ││
│  │ │ ◆   │ Arbitrum         $0.80 ││
│  │ └─────┘        ↑ 5.2%   [View] ││
│  │         Risk: MED  Confidence: 88%│
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ EULER          🔴 7.8  ││
│  │ │ ⚠️  │ Euler Finance    $2.10 ││
│  │ └─────┘        ↓ 4.2%   [View] ││
│  │         Risk: HIGH ⚠️ Recent exploit│
│  │         [View Alternatives →]    ││
│  └─────────────────────────────────┘│
│                                     │
│  💡 AI Insights                     │
│  ┌─────────────────────────────────┐│
│  │ 🎯 Based on your conservative   ││
│  │    risk profile, we recommend:  ││
│  │    • Aave V3 (Risk: 2.1)        ││
│  │    • Lido Finance (Risk: 2.3)   ││
│  │    [Explore →]                  ││
│  └─────────────────────────────────┘│
│                                     │
│  DeFi Yields (Risk-Adjusted)        │
│  ┌─────────────────────────────────┐│
│  │ 🏦 USDC Supply (Aave) 🟢 2.1   ││
│  │    4.2% APY  |  $8.2B TVL      ││
│  │ 🥩 ETH Staking (Lido) 🟢 2.3   ││
│  │    3.8% APY  |  $28.4B TVL     ││
│  │ 💰 DAI Supply (Compound) 🟢 2.5││
│  │    4.5% APY  |  $3.8B TVL      ││
│  └─────────────────────────────────┘│
│                                     │
├─────────────────────────────────────┤
│  🏠     💼     🤖     📊     👤    │
└─────────────────────────────────────┘
```

### View 2: Risk Filter & Search

```
┌─────────────────────────────────────┐
│  [←]  Risk Filter & Search    [×]   │
│                                     │
│  Filter by Risk Level               │
│  ┌─────────────────────────────────┐│
│  │ ☑ Low Risk (0-3)       245      ││
│  │ ☑ Medium Risk (3-5)    128      ││
│  │ ☐ High Risk (5-7)       42      ││
│  │ ☐ Critical Risk (7-10)   8      ││
│  └─────────────────────────────────┘│
│                                     │
│  Filter by Chain                    │
│  ┌─────────────────────────────────┐│
│  │ ☑ Ethereum           320        ││
│  │ ☑ Arbitrum            85        ││
│  │ ☑ Polygon             48        ││
│  │ ☐ Optimism            32        ││
│  └─────────────────────────────────┘│
│                                     │
│  Filter by Category                 │
│  ┌─────────────────────────────────┐│
│  │ ☑ Lending             65        ││
│  │ ☑ DEX                 89        ││
│  │ ☑ Staking             42        ││
│  │ ☐ Bridge              18        ││
│  └─────────────────────────────────┘│
│                                     │
│  Sort By                            │
│  ┌─────────────────────────────────┐│
│  │ ● Lowest Risk                   ││
│  │ ○ Highest APY                   ││
│  │ ○ Largest TVL                   ││
│  │ ○ Price Change                  ││
│  └─────────────────────────────────┘│
│                                     │
│  [Reset] [Apply Filters]            │
│                                     │
└─────────────────────────────────────┘
```

### View 3: Token Detail with ML Insights

```
┌─────────────────────────────────────┐
│  [←]      Aave V3          [★][...]│
│                                     │
│  ┌─────┐                            │
│  │ 🔷  │ AAVE           $120.50    │
│  └─────┘        ↑ 3.2%   🟢 2.1    │
│                                     │
│  Risk Analysis (ML-Powered)         │
│  ┌─────────────────────────────────┐│
│  │ Overall Risk: 2.1/10  🟢 LOW   ││
│  │ Confidence: 92%                 ││
│  │                                 ││
│  │ Risk Breakdown:                 ││
│  │ • TVL Stability:    🟢 Excellent││
│  │ • Audit History:    🟢 Strong   ││
│  │ • Network Position: 🟢 Central  ││
│  │ • Historical Track: 🟢 Clean    ││
│  │                                 ││
│  │ 7-Day Forecast: ↔️ Stable       ││
│  │ [View Full Analysis →]          ││
│  └─────────────────────────────────┘│
│                                     │
│  Price & Volume (24h)               │
│  ┌─────────────────────────────────┐│
│  │ High:  $122.80                  ││
│  │ Low:   $118.20                  ││
│  │ Volume: $285M                   ││
│  │ Market Cap: $1.8B               ││
│  └─────────────────────────────────┘│
│                                     │
│  Similar Protocols (GraphRAG)       │
│  ┌─────────────────────────────────┐│
│  │ 🔷 Compound     2.5  |  97% sim││
│  │ 🔷 Euler         7.8  |  94% sim││
│  │ 🔷 Radiant       3.2  |  89% sim││
│  │ [View More →]                   ││
│  └─────────────────────────────────┘│
│                                     │
│  [Supply] [Borrow] [Add to Portfolio]│
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 Enhanced API Endpoints

### Get Markets with ML Risk

```typescript
// GET /api/v1/markets?risk_filter=LOW,MEDIUM&chain=Ethereum
interface GetMarketsResponse {
  success: true;
  data: {
    trending: EnhancedTokenPrice[];
    top_gainers: EnhancedTokenPrice[];
    top_losers: EnhancedTokenPrice[];
    safest: EnhancedTokenPrice[];  // NEW: Lowest risk
    defi_yields: DeFiYield[];
    personalized_recommendations?: EnhancedTokenPrice[];  // NEW
  };
}

interface EnhancedTokenPrice {
  // Original fields
  symbol: string;
  name: string;
  logo_url?: string;
  price_usd: number;
  change_24h_percent: number;
  volume_24h_usd: number;
  market_cap_usd: number;
  
  // NEW: ML Risk fields
  risk_score: number;  // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;  // 0-1
  risk_trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  
  // NEW: Protocol info
  protocol_id?: string;
  protocol_name?: string;
  chains: string[];
  categories: string[];
  
  // NEW: DeFi metrics
  tvl_usd?: number;
  tvl_change_24h_percent?: number;
}

interface DeFiYield {
  protocol: string;
  protocol_id: string;
  asset: string;
  apy: number;
  tvl_usd: number;
  risk_score: number;  // NEW
  risk_level: string;  // NEW
  chain: string;
}
```

### Get Token Detail with ML Insights

```typescript
// GET /api/v1/markets/:symbol/details
interface TokenDetailResponse {
  token: EnhancedTokenPrice;
  
  // ML Risk Analysis
  risk_analysis: {
    overall_risk: number;
    confidence: number;
    breakdown: {
      tvl_stability: { score: number; label: string };
      audit_history: { score: number; label: string };
      network_position: { score: number; label: string };
      historical_track: { score: number; label: string };
    };
    forecast_7d: 'INCREASING' | 'DECREASING' | 'STABLE';
    contributing_factors: Array<{
      feature: string;
      impact: number;
      explanation: string;
    }>;
  };
  
  // GraphRAG Similar Protocols
  similar_protocols: Array<{
    protocol_id: string;
    protocol_name: string;
    similarity_score: number;
    risk_score: number;
    tvl_usd: number;
  }>;
  
  // Historical data
  price_history_7d: Array<{ timestamp: number; price: number }>;
  risk_history_7d: Array<{ timestamp: number; risk_score: number }>;
}
```

### Search Markets (GraphRAG-powered)

```typescript
// POST /api/v1/markets/search
interface MarketSearchRequest {
  query: string;  // Natural language: "safe staking on Ethereum"
  filters?: {
    risk_levels?: string[];
    chains?: string[];
    categories?: string[];
    min_apy?: number;
    min_tvl?: number;
  };
  user_preferences?: boolean;  // Apply user risk tolerance
}

interface MarketSearchResponse {
  results: EnhancedTokenPrice[];
  filters_applied: {
    risk_tolerance: string;
    chains: string[];
    categories: string[];
  };
}
```

---

## 🔌 WebSocket Integration

### Real-Time Price Updates

```typescript
// Connect to markets WebSocket
const ws = new WebSocket(`wss://api.anvil.com/ws/markets`);

// Subscribe to price updates
ws.send(JSON.stringify({
  type: 'subscribe:markets',
  symbols: ['ETH', 'BTC', 'AAVE'],
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'price:update') {
    // { symbol, price_usd, change_24h_percent }
    updateTokenPrice(data);
  }
  
  if (data.type === 'risk:update') {
    // { protocol_id, risk_score, risk_level }
    updateRiskIndicator(data);
  }
};

// React Hook Example
function useMarketsPrices(symbols: string[]) {
  const [prices, setPrices] = useState<Record<string, number>>({});
  
  useEffect(() => {
    const ws = connectMarketsWebSocket();
    
    ws.send(JSON.stringify({
      type: 'subscribe:markets',
      symbols,
    }));
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'price:update') {
        setPrices(prev => ({
          ...prev,
          [data.symbol]: data.price_usd,
        }));
      }
    };
    
    return () => ws.close();
  }, [symbols]);
  
  return prices;
}
```

---

## 🎨 Motion Design

### Risk Indicator Animations

```typescript
// Framer Motion: Risk badge entrance
<motion.div
  initial={{ scale: 0, opacity: 0 }}
  animate={{ scale: 1, opacity: 1 }}
  transition={{ type: 'spring', stiffness: 260, damping: 20 }}
>
  <RiskBadge score={2.1} />
</motion.div>

// React Native Reanimated: Risk color pulse
const riskPulse = useSharedValue(1);

useEffect(() => {
  if (riskLevel === 'HIGH' || riskLevel === 'CRITICAL') {
    riskPulse.value = withRepeat(
      withTiming(1.1, { duration: 1000 }),
      -1,
      true
    );
  }
}, [riskLevel]);

const animatedStyle = useAnimatedStyle(() => ({
  transform: [{ scale: riskPulse.value }],
}));
```

### Real-Time Price Update Animation

```typescript
// Price change flash
const [priceFlash, setPriceFlash] = useState('none');

useEffect(() => {
  if (price > previousPrice) {
    setPriceFlash('green');
  } else if (price < previousPrice) {
    setPriceFlash('red');
  }
  
  const timer = setTimeout(() => setPriceFlash('none'), 300);
  return () => clearTimeout(timer);
}, [price]);

<motion.div
  animate={{
    backgroundColor: 
      priceFlash === 'green' ? '#10b98120' :
      priceFlash === 'red' ? '#ef444420' :
      'transparent'
  }}
  transition={{ duration: 0.3 }}
>
  ${price.toFixed(2)}
</motion.div>
```

---

## 🎨 Component Specifications

```typescript
interface MarketsScreenProps {
  initialTab?: 'trending' | 'gainers' | 'losers' | 'safest';
  riskFilter?: RiskLevel[];
}

interface TokenListItemProps {
  token: EnhancedTokenPrice;
  showRisk?: boolean;
  showSimilar?: boolean;
  onPress: (token: EnhancedTokenPrice) => void;
}

interface RiskBadgeProps {
  score: number;
  level: RiskLevel;
  confidence?: number;
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
}

interface TokenDetailModalProps {
  symbol: string;
  onClose: () => void;
  onSupply?: () => void;
  onBorrow?: () => void;
}

interface MarketSearchBarProps {
  onSearch: (query: string) => void;
  onFilterPress: () => void;
  placeholder?: string;
}
```

---

## ⚠️ Error Handling

```typescript
const marketsErrors = {
  MARKETS_001: 'Failed to load market data',
  MARKETS_002: 'Risk data unavailable',
  MARKETS_003: 'WebSocket connection lost',
  MARKETS_004: 'Invalid risk filter',
  MARKETS_005: 'Search failed',
};

// Error recovery
try {
  const markets = await fetchMarkets();
} catch (error) {
  // Fallback to cached data
  const cached = await getCachedMarkets();
  if (cached) {
    showNotification('Using cached data', 'warning');
    return cached;
  }
  // Show error state
  showError(marketsErrors.MARKETS_001);
}
```

---

## 🔒 Security & Privacy

- ✅ No wallet addresses exposed
- ✅ Personalized recommendations opt-in
- ✅ Risk data from verified ML models
- ✅ Real-time updates encrypted (WSS)

---

## ♿ Accessibility

- ✅ Risk levels with color + text
- ✅ Screen reader support for all metrics
- ✅ High contrast risk indicators
- ✅ Keyboard navigation for web
- ✅ Voice control compatible

---

*Document Version: 2.0*  
*Last Updated: December 1, 2025*  
*Module: Markets (Enhanced)*  
*Features: ML Risk + GraphRAG + WebSocket*
