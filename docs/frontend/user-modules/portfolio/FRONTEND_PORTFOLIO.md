# FRONTEND_PORTFOLIO

## Portfolio Risk Analysis Module

**User Type:** Authenticated User  
**Module:** Portfolio - Risk Analysis & Cascade Simulation  
**Route:** `/portfolio`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Portfolio Risk Analysis** - Advanced Risk Assessment & Cascade Simulation

### Description
Comprehensive portfolio risk analysis using ML-powered risk scoring, dependency mapping, systemic risk assessment, and cascade failure simulation for proactive portfolio protection.

### Key Capabilities
- ✅ Overall portfolio risk scoring
- ✅ Protocol-level risk breakdown
- ✅ Dependency risk analysis
- ✅ Systemic risk assessment
- ✅ Concentration risk evaluation
- ✅ Cascade failure simulation
- ✅ Actionable recommendations

---

## 🔌 API Integration

### 1. Get Portfolio Risk

```typescript
// GET /api/v1/portfolio/risk
// Description: Get comprehensive risk analysis
// Authentication: Required (Bearer token)

interface PortfolioRiskResponse {
  user_id: string;
  overall_risk_score: number; // 0-100
  risk_distribution: Record<string, number>; // { low: 20, medium: 50, high: 30 }
  protocols_at_risk: ProtocolRisk[];
  dependency_risks: DependencyRisk[];
  systemic_risk_score: number;
  concentration_risk: number;
  chain_risk_distribution: Record<string, number>;
  recommendations: string[];
  total_value_at_risk_usd: number;
  last_updated: string;
}

interface ProtocolRisk {
  protocol_id: string;
  protocol_name: string;
  exposure_usd: number;
  exposure_percentage: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_trend: 'increasing' | 'stable' | 'decreasing';
  contributing_factors: string[];
  value_at_risk_usd: number;
}

interface DependencyRisk {
  dependency_protocol_id: string;
  dependency_protocol_name: string;
  dependent_protocols: string[];
  impact_if_failure: string;
  total_exposure_usd: number;
  risk_score: number;
}

const getPortfolioRisk = async (): Promise<PortfolioRiskResponse> => {
  const response = await api.get('/api/v1/portfolio/risk', {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "overall_risk_score": 42,
  "risk_distribution": {
    "low": 30,
    "medium": 50,
    "high": 15,
    "critical": 5
  },
  "protocols_at_risk": [
    {
      "protocol_id": "euler-uuid",
      "protocol_name": "Euler Finance",
      "exposure_usd": 2450,
      "exposure_percentage": 23.1,
      "risk_score": 78,
      "risk_level": "high",
      "risk_trend": "increasing",
      "contributing_factors": [
        "Low liquidity relative to TVL",
        "Recent governance changes",
        "Dependency on external oracle"
      ],
      "value_at_risk_usd": 1225
    }
  ],
  "dependency_risks": [
    {
      "dependency_protocol_id": "chainlink-uuid",
      "dependency_protocol_name": "Chainlink",
      "dependent_protocols": ["aave-v3", "compound-v3", "euler"],
      "impact_if_failure": "All lending positions at risk due to oracle failure",
      "total_exposure_usd": 18650,
      "risk_score": 25
    }
  ],
  "systemic_risk_score": 35,
  "concentration_risk": 68,
  "chain_risk_distribution": {
    "ethereum": 90,
    "polygon": 10
  },
  "recommendations": [
    "Reduce exposure to Euler Finance (high risk)",
    "Diversify across more chains to reduce concentration",
    "Consider reducing dependency on Chainlink-dependent protocols"
  ],
  "total_value_at_risk_usd": 4250,
  "last_updated": "2025-12-01T12:00:00Z"
}
```

### 2. Simulate Cascade Failure

```typescript
// POST /api/v1/portfolio/risk/simulate-cascade
// Description: Simulate protocol failure cascade
// Authentication: Required (Bearer token)

interface CascadeSimulationRequest {
  origin_protocol_id: string; // Protocol that fails
}

interface CascadeSimulationResponse {
  user_id: string;
  cascade_impacts: CascadeImpact[];
  worst_case_loss_usd: number;
  worst_case_loss_percentage: number;
  protocols_to_exit: string[];
  protocols_to_reduce: string[];
  safe_protocols: string[];
}

interface CascadeImpact {
  origin_protocol_id: string;
  origin_protocol_name: string;
  directly_affected: string[];
  indirectly_affected: string[];
  total_exposure_at_risk_usd: number;
  cascade_probability: number; // 0-1
  time_to_impact: string; // "immediate", "hours", "days"
}

const simulateCascade = async (
  originProtocolId: string
): Promise<CascadeSimulationResponse> => {
  const response = await api.post('/api/v1/portfolio/risk/simulate-cascade', {
    origin_protocol_id: originProtocolId
  }, {
    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
  });
  return response.data;
};

// Example Response (200 OK):
{
  "user_id": "123e4567",
  "cascade_impacts": [
    {
      "origin_protocol_id": "euler-uuid",
      "origin_protocol_name": "Euler Finance",
      "directly_affected": ["euler-positions"],
      "indirectly_affected": ["aave-v3", "compound-v3"],
      "total_exposure_at_risk_usd": 6450,
      "cascade_probability": 0.65,
      "time_to_impact": "immediate"
    }
  ],
  "worst_case_loss_usd": 6450,
  "worst_case_loss_percentage": 60.8,
  "protocols_to_exit": ["euler-finance"],
  "protocols_to_reduce": ["aave-v3"],
  "safe_protocols": ["lido-finance"]
}
```

---

## 🔗 React Hooks

```typescript
export function usePortfolioRisk() {
  return useQuery({
    queryKey: ['portfolio', 'risk'],
    queryFn: getPortfolioRisk,
    refetchInterval: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCascadeSimulation() {
  return useMutation({
    mutationFn: simulateCascade,
  });
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Portfolio Risk Analysis*  
*Backend Status: ✅ 100% Implemented (2 endpoints)*  
*Frontend Status: ✅ Ready for Implementation*
