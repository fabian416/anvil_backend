# FRONTEND_USER_PORTFOLIO

## User Portfolio Module

**User Type:** Authenticated User  
**Module:** Portfolio - Complete Portfolio Management & Risk Monitoring  
**Route:** `/portfolio`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Portfolio** - Comprehensive Portfolio Management with ML Risk Analysis

### Description
Complete portfolio management system providing real-time portfolio tracking, risk analysis, protocol exposure breakdown, historical performance, and AI-powered optimization recommendations.

### Key Capabilities
- ✅ Real-time portfolio value tracking
- ✅ Multi-chain aggregation
- ✅ Protocol exposure breakdown
- ✅ ML-powered risk scoring per protocol
- ✅ Overall portfolio risk analysis
- ✅ Historical performance tracking
- ✅ Risk alerts and notifications
- ✅ Diversification analysis

---

## 🔌 API Integration

### Get User Portfolio

```typescript
// GET /api/v1/portfolio/
interface PortfolioResponse {
  user_id: string;
  total_value_usd: number;
  protocols: ProtocolExposure[];
  overall_risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  last_updated: string;
}

interface ProtocolExposure {
  protocol_id: string;
  protocol_name: string;
  chain: string;
  position_type: 'supplied' | 'borrowed' | 'staked' | 'lp';
  amount_usd: number;
  percentage_of_portfolio: number;
  risk_score: number; // ML-powered
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

const getPortfolio = async (): Promise<PortfolioResponse> => {
  const response = await api.get('/api/v1/portfolio/');
  return response.data;
};
```

### Get Portfolio Risk Analysis

```typescript
// GET /api/v1/portfolio/risk
interface PortfolioRiskResponse {
  overall_risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_factors: RiskFactor[];
  concentration_risk: number; // 0-10
  protocol_risks: ProtocolRisk[];
  recommendations: string[];
}

interface RiskFactor {
  factor: string;
  impact: 'low' | 'medium' | 'high';
  description: string;
}

interface ProtocolRisk {
  protocol_name: string;
  risk_score: number;
  exposure_usd: number;
  contribution_to_portfolio_risk: number; // 0-100%
}

const getPortfolioRisk = async (): Promise<PortfolioRiskResponse> => {
  const response = await api.get('/api/v1/portfolio/risk');
  return response.data;
};
```

---

## 🎨 React Hooks

### usePortfolio Hook

```typescript
export function usePortfolio() {
  const { data: portfolio, isLoading } = useQuery({
    queryKey: ['user-portfolio'],
    queryFn: async () => {
      const response = await api.get('/api/v1/portfolio/');
      return response.data;
    },
    refetchInterval: 60000, // Refetch every 60 seconds
  });
  
  const { data: risk } = useQuery({
    queryKey: ['portfolio-risk'],
    queryFn: async () => {
      const response = await api.get('/api/v1/portfolio/risk');
      return response.data;
    },
    refetchInterval: 300000, // Refetch every 5 minutes
  });
  
  return {
    portfolio,
    risk,
    isLoading,
    totalValue: portfolio?.total_value_usd || 0,
    overallRisk: portfolio?.overall_risk_score || 0,
  };
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Portfolio*  
*Backend Status: ✅ 100% Implemented (2 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
