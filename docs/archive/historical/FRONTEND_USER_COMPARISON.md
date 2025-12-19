# FRONTEND_USER_COMPARISON

## Protocol Comparison & Analysis Module

**User Type:** Authenticated User  
**Module:** Comparison - Side-by-Side Protocol Analysis  
**Route:** `/comparison`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Protocol Comparison & Analysis** - AI-Powered Multi-Protocol Analysis

### Description
Advanced protocol comparison tool enabling side-by-side analysis of up to 5 DeFi protocols across multiple dimensions including risk, yield, security, and network metrics with AI-powered recommendations.

### Key Capabilities
- ✅ Compare 2-5 protocols simultaneously
- ✅ Multi-dimensional analysis (risk, yield, security, network)
- ✅ AI-powered recommendations
- ✅ Trade-off identification
- ✅ Winner identification by dimension
- ✅ Comprehensive metrics matrix

---

## 🔌 API Integration

### 1. Compare Protocols

```typescript
// POST /api/v1/comparison/protocols
// Description: Compare multiple protocols side-by-side
// Authentication: Required (Bearer token)

interface CompareProtocolsRequest {
  protocol_ids: string[]; // 2-5 protocol IDs (UUIDs)
  dimensions?: string[]; // Optional: ['risk', 'yield', 'security', 'network', 'all']
}

interface ProtocolMetrics {
  protocol_id: string;
  name: string;
  type: string; // "lending", "dex", "yield-farming", etc.
  chain: string;
  tvl: number;
  risk_score: number; // 0-100
  security_score: number; // 0-100
  apy: number; // Annual Percentage Yield
  volume_24h: number;
  users_count: number;
  audit_status: 'audited' | 'unaudited' | 'partially-audited';
  time_in_market_days: number;
}

interface DimensionComparison {
  dimension: 'risk' | 'yield' | 'security' | 'network';
  winner_id: string; // Protocol ID with best score
  scores: Record<string, number>; // protocol_id -> score
  insights: string; // AI-generated insight
}

interface TradeOff {
  higher_risk_protocol: string;
  lower_risk_protocol: string;
  risk_difference: number;
  yield_difference: number;
  recommendation: string;
}

interface ComparisonResponse {
  protocols: ProtocolMetrics[];
  comparison_matrix: DimensionComparison[];
  trade_offs: TradeOff[];
  overall_winner: {
    protocol_id: string;
    name: string;
    reasoning: string;
  };
  ai_recommendation: string;
  timestamp: string;
}

const compareProtocols = async (
  request: CompareProtocolsRequest
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', request, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

// Example Request:
{
  "protocol_ids": [
    "aave-v3-uuid",
    "compound-v3-uuid",
    "morpho-blue-uuid"
  ],
  "dimensions": ["risk", "yield", "security"]
}

// Example Response (200 OK):
{
  "protocols": [
    {
      "protocol_id": "aave-v3-uuid",
      "name": "Aave V3",
      "type": "lending",
      "chain": "ethereum",
      "tvl": 5200000000,
      "risk_score": 25,
      "security_score": 95,
      "apy": 3.5,
      "volume_24h": 150000000,
      "users_count": 125000,
      "audit_status": "audited",
      "time_in_market_days": 730
    },
    {
      "protocol_id": "compound-v3-uuid",
      "name": "Compound V3",
      "type": "lending",
      "chain": "ethereum",
      "tvl": 3100000000,
      "risk_score": 30,
      "security_score": 92,
      "apy": 4.2,
      "volume_24h": 95000000,
      "users_count": 85000,
      "audit_status": "audited",
      "time_in_market_days": 650
    },
    {
      "protocol_id": "morpho-blue-uuid",
      "name": "Morpho Blue",
      "type": "lending",
      "chain": "ethereum",
      "tvl": 450000000,
      "risk_score": 45,
      "security_score": 88,
      "apy": 5.8,
      "volume_24h": 12000000,
      "users_count": 15000,
      "audit_status": "audited",
      "time_in_market_days": 180
    }
  ],
  "comparison_matrix": [
    {
      "dimension": "risk",
      "winner_id": "aave-v3-uuid",
      "scores": {
        "aave-v3-uuid": 25,
        "compound-v3-uuid": 30,
        "morpho-blue-uuid": 45
      },
      "insights": "Aave V3 has the lowest risk score due to longer market presence and higher TVL providing stability."
    },
    {
      "dimension": "yield",
      "winner_id": "morpho-blue-uuid",
      "scores": {
        "aave-v3-uuid": 3.5,
        "compound-v3-uuid": 4.2,
        "morpho-blue-uuid": 5.8
      },
      "insights": "Morpho Blue offers highest yield at 5.8% APY, reflecting its newer market position and optimization strategies."
    },
    {
      "dimension": "security",
      "winner_id": "aave-v3-uuid",
      "scores": {
        "aave-v3-uuid": 95,
        "compound-v3-uuid": 92,
        "morpho-blue-uuid": 88
      },
      "insights": "Aave V3 leads in security with extensive audits, bug bounties, and battle-tested contracts over 2 years."
    }
  ],
  "trade_offs": [
    {
      "higher_risk_protocol": "morpho-blue-uuid",
      "lower_risk_protocol": "aave-v3-uuid",
      "risk_difference": 20,
      "yield_difference": 2.3,
      "recommendation": "Morpho Blue offers 2.3% higher yield but carries 20 points more risk. Consider for smaller allocations with higher risk tolerance."
    }
  ],
  "overall_winner": {
    "protocol_id": "compound-v3-uuid",
    "name": "Compound V3",
    "reasoning": "Best balance of security (92), moderate risk (30), and competitive yield (4.2%). Suitable for conservative to moderate risk profiles."
  },
  "ai_recommendation": "For conservative investors: Aave V3 offers maximum security and stability. For moderate risk tolerance: Compound V3 provides the best risk-reward balance. For aggressive yield seekers: Morpho Blue delivers highest returns but requires accepting higher risk and newer protocol status.",
  "timestamp": "2025-12-01T12:00:00Z"
}

// Example Error Response (400 Bad Request):
{
  "error": {
    "code": "INVALID_PROTOCOL_COUNT",
    "message": "Must provide between 2 and 5 protocols to compare",
    "details": {
      "provided": 1,
      "min": 2,
      "max": 5
    }
  }
}

// Example Error Response (404 Not Found):
{
  "error": {
    "code": "PROTOCOL_NOT_FOUND",
    "message": "One or more protocols not found",
    "details": {
      "missing_ids": ["invalid-uuid"]
    }
  }
}
```

---

## 🔗 React Hooks

### useProtocolComparison Hook

```typescript
export function useProtocolComparison() {
  return useMutation({
    mutationFn: compareProtocols,
    onError: (error) => {
      toast.error('Failed to compare protocols');
    },
  });
}

// Usage:
const comparison = useProtocolComparison();

comparison.mutate({
  protocol_ids: ['aave-v3', 'compound-v3', 'morpho-blue'],
  dimensions: ['risk', 'yield', 'security']
});
```

### useComparisonWithCache Hook

```typescript
export function useComparisonWithCache(
  protocolIds: string[],
  dimensions?: string[]
) {
  const cacheKey = useMemo(
    () => ['comparison', ...protocolIds.sort(), ...(dimensions || []).sort()],
    [protocolIds, dimensions]
  );
  
  return useQuery({
    queryKey: cacheKey,
    queryFn: () => compareProtocols({ protocol_ids: protocolIds, dimensions }),
    enabled: protocolIds.length >= 2 && protocolIds.length <= 5,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Usage:
const { data: comparison, isLoading } = useComparisonWithCache(
  ['aave-v3', 'compound-v3'],
  ['risk', 'yield']
);
```

---

## 🎨 React Components

### ProtocolComparisonTool Component

```typescript
export function ProtocolComparisonTool() {
  const [selectedProtocols, setSelectedProtocols] = useState<string[]>([]);
  const [dimensions, setDimensions] = useState<string[]>(['risk', 'yield', 'security']);
  const comparison = useProtocolComparison();
  
  const handleCompare = () => {
    if (selectedProtocols.length < 2) {
      toast.error('Select at least 2 protocols to compare');
      return;
    }
    
    comparison.mutate({
      protocol_ids: selectedProtocols,
      dimensions
    });
  };
  
  return (
    <div className="comparison-tool">
      <h2>Compare Protocols</h2>
      
      <ProtocolSelector
        selected={selectedProtocols}
        onChange={setSelectedProtocols}
        max={5}
      />
      
      <DimensionSelector
        selected={dimensions}
        onChange={setDimensions}
      />
      
      <button
        onClick={handleCompare}
        disabled={selectedProtocols.length < 2 || comparison.isPending}
      >
        {comparison.isPending ? 'Comparing...' : 'Compare Protocols'}
      </button>
      
      {comparison.data && (
        <ComparisonResults data={comparison.data} />
      )}
    </div>
  );
}
```

### ComparisonMatrix Component

```typescript
export function ComparisonMatrix({ data }: { data: ComparisonResponse }) {
  return (
    <div className="comparison-matrix">
      <h3>Comparison Matrix</h3>
      
      <table>
        <thead>
          <tr>
            <th>Dimension</th>
            {data.protocols.map(p => (
              <th key={p.protocol_id}>{p.name}</th>
            ))}
            <th>Winner</th>
          </tr>
        </thead>
        <tbody>
          {data.comparison_matrix.map(dim => (
            <tr key={dim.dimension}>
              <td className="dimension">{dim.dimension}</td>
              {data.protocols.map(p => (
                <td
                  key={p.protocol_id}
                  className={dim.winner_id === p.protocol_id ? 'winner' : ''}
                >
                  {dim.scores[p.protocol_id]}
                  {dim.winner_id === p.protocol_id && ' 🏆'}
                </td>
              ))}
              <td className="winner">
                {data.protocols.find(p => p.protocol_id === dim.winner_id)?.name}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <div className="insights">
        {data.comparison_matrix.map(dim => (
          <div key={dim.dimension} className="insight">
            <strong>{dim.dimension}:</strong> {dim.insights}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### TradeOffAnalysis Component

```typescript
export function TradeOffAnalysis({ tradeOffs }: { tradeOffs: TradeOff[] }) {
  return (
    <div className="trade-off-analysis">
      <h3>Risk/Reward Trade-offs</h3>
      
      {tradeOffs.map((tradeOff, i) => (
        <div key={i} className="trade-off-card">
          <div className="comparison">
            <div className="high-risk">
              <span className="label">Higher Risk</span>
              <span className="protocol">{tradeOff.higher_risk_protocol}</span>
              <span className="yield">+{tradeOff.yield_difference.toFixed(2)}% yield</span>
            </div>
            
            <div className="arrow">⚖️</div>
            
            <div className="low-risk">
              <span className="label">Lower Risk</span>
              <span className="protocol">{tradeOff.lower_risk_protocol}</span>
              <span className="risk">-{tradeOff.risk_difference} risk points</span>
            </div>
          </div>
          
          <div className="recommendation">
            <strong>Recommendation:</strong> {tradeOff.recommendation}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## 🎭 User Flows

### Flow 1: Quick Protocol Comparison

```
1. User browsing protocols
   ↓
2. Selects "Compare" on Aave V3
   ↓
3. Comparison tool opens with Aave pre-selected
   ↓
4. User adds Compound V3 and Morpho Blue
   ↓
5. Selects dimensions: Risk, Yield, Security
   ↓
6. Clicks "Compare Protocols"
   ↓
7. POST /api/v1/comparison/protocols
   ↓
8. View comprehensive comparison matrix
   ↓
9. Review AI recommendations
   ↓
10. Make informed decision
```

### Flow 2: Investment Decision Making

```
1. User researching lending protocols
   ↓
2. Shortlists 4 protocols for comparison
   ↓
3. Runs full comparison (all dimensions)
   ↓
4. Reviews trade-off analysis
   ↓
5. Identifies Compound V3 as best balance
   ↓
6. Checks AI recommendation (confirms choice)
   ↓
7. Proceeds to invest in Compound V3
```

---

## ⚠️ Error Handling

```typescript
const handleComparisonError = (error: any) => {
  switch (error.code) {
    case 'INVALID_PROTOCOL_COUNT':
      toast.error('Select between 2 and 5 protocols to compare');
      break;
      
    case 'PROTOCOL_NOT_FOUND':
      toast.error('One or more selected protocols not found');
      break;
      
    case 'AUTHENTICATION_REQUIRED':
      toast.error('Please log in to compare protocols');
      redirectToLogin();
      break;
      
    case 'RATE_LIMIT_EXCEEDED':
      toast.error('Too many comparisons. Please wait a moment.');
      break;
      
    default:
      toast.error('Failed to compare protocols. Please try again.');
  }
};
```

---

## 🌍 Use Cases

### 1. Due Diligence
- User evaluating 3 lending protocols
- Side-by-side metrics comparison
- Risk vs. yield analysis
- Informed decision making

### 2. Portfolio Diversification
- Compare protocols across different risk levels
- Identify complementary protocols
- Balance risk/reward across portfolio

### 3. Yield Optimization
- Find highest yield for risk tolerance
- Compare similar protocols
- Trade-off analysis

### 4. Risk Management
- Compare security scores
- Audit status verification
- Time-in-market analysis

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Protocol Comparison & Analysis*  
*Backend Status: ✅ 100% Implemented (1 endpoint)*  
*Frontend Status: ✅ Ready for Implementation*
