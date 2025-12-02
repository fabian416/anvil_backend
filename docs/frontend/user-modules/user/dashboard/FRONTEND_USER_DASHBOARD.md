# FRONTEND_USER_DASHBOARD

## User Dashboard Module

**User Type:** Authenticated User  
**Module:** Dashboard - AI-Powered Portfolio Insights & Summary  
**Route:** `/dashboard`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Dashboard** - AI-Powered Portfolio Intelligence with Personalized Insights

### Description
Comprehensive dashboard providing AI-generated insights, portfolio summary, risk analysis, and actionable recommendations. Aggregates data across all protocols and chains to give users a complete picture of their DeFi positions.

### Key Capabilities
- ✅ AI-powered personalized insights
- ✅ Portfolio value summary with 24h change
- ✅ Overall risk score calculation
- ✅ Chain breakdown (multi-chain portfolio)
- ✅ Protocol position breakdown
- ✅ Actionable recommendations
- ✅ Risk warnings and opportunities
- ✅ Diversification suggestions

---

## 🔌 API Integration

### Get AI Dashboard Insights

```typescript
// GET /api/v1/dashboard/insights
interface DashboardInsightsResponse {
  insights: AIInsight[];
  personalized: boolean;
}

interface AIInsight {
  id: string;
  type: 'risk_warning' | 'optimization' | 'diversification' | 'opportunity';
  title: string;
  message: string;
  action_label: string | null;
  action_url: string | null;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
}

const getDashboardInsights = async (): Promise<AIInsight[]> => {
  const response = await api.get('/api/v1/dashboard/insights');
  return response.data.insights;
};
```

### Get Dashboard Summary

```typescript
// GET /api/v1/dashboard/summary
interface DashboardSummaryResponse {
  total_value_usd: number;
  change_24h_usd: number;
  change_24h_percent: number;
  overall_risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  chains: ChainBreakdown[];
  positions: PositionBreakdown[];
}

interface ChainBreakdown {
  chain: string;
  value_usd: number;
  percentage: number;
  protocol_count: number;
}

interface PositionBreakdown {
  protocol_name: string;
  chain: string;
  position_type: 'supplied' | 'borrowed' | 'staked' | 'lp';
  amount_usd: number;
  percentage: number;
}

const getDashboardSummary = async (): Promise<DashboardSummaryResponse> => {
  const response = await api.get('/api/v1/dashboard/summary');
  return response.data;
};
```

---

## 🎨 React Hooks

### useDashboard Hook

```typescript
export function useDashboard() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: async () => {
      const response = await api.get('/api/v1/dashboard/summary');
      return response.data;
    },
    refetchInterval: 60000, // Refetch every 60 seconds
  });
  
  const { data: insights, isLoading: insightsLoading } = useQuery({
    queryKey: ['dashboard-insights'],
    queryFn: async () => {
      const response = await api.get('/api/v1/dashboard/insights');
      return response.data.insights;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });
  
  return {
    summary,
    insights: insights || [],
    isLoading: summaryLoading || insightsLoading,
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Dashboard*  
*Backend Status: ✅ 100% Implemented (2 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
