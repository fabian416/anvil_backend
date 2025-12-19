# FRONTEND_DASHBOARD

## Dashboard & Insights Module

**User Type:** Authenticated User  
**Module:** Dashboard - AI-Powered Insights & Portfolio Summary  
**Route:** `/dashboard`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Dashboard & Insights** - Personalized AI-Powered Financial Intelligence

### Description
Comprehensive dashboard providing AI-generated insights, portfolio summary, risk analysis, and actionable recommendations powered by advanced analytics and machine learning.

### Key Capabilities
- ✅ AI-powered personalized insights
- ✅ Portfolio value aggregation
- ✅ Risk score calculation
- ✅ 24-hour performance tracking
- ✅ Chain-level breakdown
- ✅ Position-level analytics
- ✅ Optimization opportunities
- ✅ Diversification suggestions

---

## 🔌 API Integration

### 1. Get Dashboard Insights

```typescript
// GET /api/v1/dashboard/insights
// Description: Get AI-powered personalized insights
// Authentication: Required (Bearer token)

interface DashboardInsight {
  id: string;
  type: 'risk_warning' | 'opportunity' | 'optimization' | 'diversification' | 'market_alert';
  title: string;
  message: string;
  action_label: string;
  action_url: string;
  severity: 'info' | 'warning' | 'critical';
  created_at: string;
}

interface DashboardInsightsResponse {
  insights: DashboardInsight[];
  personalized: boolean;
}

const getDashboardInsights = async (): Promise<DashboardInsightsResponse> => {
  const response = await api.get('/api/v1/dashboard/insights', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "insights": [
    {
      "id": "insight-123e4567",
      "type": "risk_warning",
      "title": "High Concentration Risk",
      "message": "80% of your portfolio is in Ethereum-based protocols. Consider diversifying across multiple chains to reduce smart contract risk.",
      "action_label": "View Diversification Options",
      "action_url": "/compare/protocols?chain=polygon,arbitrum",
      "severity": "warning",
      "created_at": "2025-12-01T12:00:00Z"
    },
    {
      "id": "insight-234e5678",
      "type": "opportunity",
      "title": "Higher Yield Opportunity",
      "message": "Morpho Blue offers 2.3% higher APY than your current Aave position with similar risk profile.",
      "action_label": "Compare Protocols",
      "action_url": "/compare/protocols?ids=aave-v3,morpho-blue",
      "severity": "info",
      "created_at": "2025-12-01T11:30:00Z"
    },
    {
      "id": "insight-345e6789",
      "type": "optimization",
      "title": "Gas Cost Optimization",
      "message": "Your USDC position could be moved to Polygon for lower gas fees while maintaining similar yield.",
      "action_label": "View Details",
      "action_url": "/markets/yields?token=USDC&chain=polygon",
      "severity": "info",
      "created_at": "2025-12-01T11:00:00Z"
    },
    {
      "id": "insight-456e7890",
      "type": "market_alert",
      "title": "Protocol Security Update",
      "message": "Compound V3 released a security patch. Your position is safe, but consider reviewing the update.",
      "action_label": "Read More",
      "action_url": "https://compound.finance/governance/proposals/123",
      "severity": "info",
      "created_at": "2025-12-01T10:30:00Z"
    }
  ],
  "personalized": true
}
```

---

### 2. Get Dashboard Summary

```typescript
// GET /api/v1/dashboard/summary
// Description: Get comprehensive portfolio summary
// Authentication: Required (Bearer token)

interface ChainBreakdown {
  chain: string;
  value_usd: number;
  percentage: number;
  position_count: number;
}

interface PositionBreakdown {
  protocol_name: string;
  protocol_id: string;
  position_type: 'supplied' | 'borrowed' | 'staked' | 'liquidity' | 'farmed';
  amount_usd: number;
  percentage: number;
  chain: string;
  apy?: number;
}

interface DashboardSummaryResponse {
  total_value_usd: number;
  change_24h_usd: number;
  change_24h_percent: number;
  risk_score: number; // 0-100
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  chain_breakdown: ChainBreakdown[];
  position_breakdown: PositionBreakdown[];
  last_updated: string;
}

const getDashboardSummary = async (): Promise<DashboardSummaryResponse> => {
  const response = await api.get('/api/v1/dashboard/summary', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "total_value_usd": 20200.00,
  "change_24h_usd": 450.25,
  "change_24h_percent": 2.28,
  "risk_score": 35,
  "risk_level": "medium",
  "chain_breakdown": [
    {
      "chain": "ethereum",
      "value_usd": 18200.00,
      "percentage": 90.1,
      "position_count": 2
    },
    {
      "chain": "polygon",
      "value_usd": 2000.00,
      "percentage": 9.9,
      "position_count": 1
    }
  ],
  "position_breakdown": [
    {
      "protocol_name": "Lido Finance",
      "protocol_id": "lido-uuid",
      "position_type": "staked",
      "amount_usd": 12000.00,
      "percentage": 59.4,
      "chain": "ethereum",
      "apy": 3.2
    },
    {
      "protocol_name": "Aave V3",
      "protocol_id": "aave-v3-uuid",
      "position_type": "supplied",
      "amount_usd": 6200.00,
      "percentage": 30.7,
      "chain": "ethereum",
      "apy": 4.5
    },
    {
      "protocol_name": "Uniswap V3",
      "protocol_id": "uniswap-v3-uuid",
      "position_type": "liquidity",
      "amount_usd": 2000.00,
      "percentage": 9.9,
      "chain": "polygon",
      "apy": 12.8
    }
  ],
  "last_updated": "2025-12-01T12:00:00Z"
}
```

---

## 🔗 React Hooks

### useDashboardInsights Hook

```typescript
export function useDashboardInsights() {
  return useQuery({
    queryKey: ['dashboard', 'insights'],
    queryFn: getDashboardInsights,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

// Usage:
const { data: insights, isLoading } = useDashboardInsights();
```

### useDashboardSummary Hook

```typescript
export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    refetchInterval: 30 * 1000, // 30 seconds
    staleTime: 10 * 1000, // 10 seconds
  });
}

// Usage:
const { data: summary, isLoading } = useDashboardSummary();
```

---

## 🎨 React Components

### DashboardOverview Component

```typescript
export function DashboardOverview() {
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: insights } = useDashboardInsights();
  
  if (isLoading) return <LoadingSpinner />;
  if (!summary) return <EmptyState />;
  
  return (
    <div className="dashboard-overview">
      <PortfolioValue summary={summary} />
      <InsightsPanel insights={insights?.insights} />
      <ChainBreakdown chains={summary.chain_breakdown} />
      <PositionsTable positions={summary.position_breakdown} />
    </div>
  );
}
```

### PortfolioValue Component

```typescript
export function PortfolioValue({ summary }: { summary: DashboardSummaryResponse }) {
  const isPositive = summary.change_24h_percent >= 0;
  
  return (
    <div className="portfolio-value-card">
      <div className="total">
        <span className="label">Total Portfolio Value</span>
        <span className="value">${formatNumber(summary.total_value_usd)}</span>
      </div>
      
      <div className={`change ${isPositive ? 'positive' : 'negative'}`}>
        <span className="amount">
          {isPositive ? '+' : ''} ${formatNumber(Math.abs(summary.change_24h_usd))}
        </span>
        <span className="percent">
          ({isPositive ? '+' : ''}{summary.change_24h_percent.toFixed(2)}%)
        </span>
        <span className="period">24h</span>
      </div>
      
      <RiskIndicator 
        score={summary.risk_score}
        level={summary.risk_level}
      />
    </div>
  );
}
```

### InsightsPanel Component

```typescript
export function InsightsPanel({ insights }: { insights?: DashboardInsight[] }) {
  if (!insights || insights.length === 0) {
    return <div className="insights-empty">No new insights</div>;
  }
  
  return (
    <div className="insights-panel">
      <h3>AI Insights</h3>
      {insights.map(insight => (
        <InsightCard key={insight.id} insight={insight} />
      ))}
    </div>
  );
}

function InsightCard({ insight }: { insight: DashboardInsight }) {
  const severityIcons = {
    info: 'ℹ️',
    warning: '⚠️',
    critical: '🔴'
  };
  
  return (
    <div className={`insight-card severity-${insight.severity}`}>
      <div className="header">
        <span className="icon">{severityIcons[insight.severity]}</span>
        <span className="type">{insight.type.replace('_', ' ')}</span>
      </div>
      
      <h4>{insight.title}</h4>
      <p>{insight.message}</p>
      
      <a href={insight.action_url} className="action-btn">
        {insight.action_label} →
      </a>
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: Morning Dashboard Check

```
1. User opens app
   ↓
2. GET /api/v1/dashboard/summary
   ↓
3. Display portfolio value, 24h change
   ↓
4. GET /api/v1/dashboard/insights
   ↓
5. Show AI insights at top
   ↓
6. User sees "High Yield Opportunity" insight
   ↓
7. Clicks "Compare Protocols"
   ↓
8. Navigates to comparison tool
```

### Flow 2: Risk Alert Response

```
1. Dashboard loads
   ↓
2. Critical insight appears: "High Concentration Risk"
   ↓
3. User clicks "View Diversification Options"
   ↓
4. Opens protocol comparison tool
   ↓
5. Filters by different chains
   ↓
6. User identifies suitable protocols
   ↓
7. Takes action to diversify
```

---

## ⚠️ Error Handling

```typescript
const handleDashboardError = (error: any) => {
  switch (error.code) {
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to view dashboard');
      redirectToLogin();
      break;
      
    case 'PORTFOLIO_NOT_FOUND':
      toast.info('Connect your wallet to see portfolio data');
      break;
      
    default:
      toast.error('Unable to load dashboard. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. Daily Portfolio Monitoring
- User checks dashboard every morning
- Views total value and 24h change
- Reviews AI insights for action items

### 2. Risk Management
- User receives concentration risk warning
- Takes action to diversify
- Risk score improves

### 3. Yield Optimization
- AI identifies higher yield opportunity
- User compares protocols
- Moves funds for better returns

### 4. Portfolio Rebalancing
- User reviews chain breakdown
- Identifies over-concentration
- Rebalances across chains

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Dashboard & Insights*  
*Backend Status: ✅ 100% Implemented (2 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
