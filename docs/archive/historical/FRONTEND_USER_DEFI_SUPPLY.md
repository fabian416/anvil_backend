# FRONTEND_USER_DEFI_SUPPLY

## User Supply/Lend Module

**User Type:** Authenticated User  
**Module:** Supply (Lending)  
**Route:** `/earn/supply`  
**Platform:** Mobile (React Native) & Web  
**Version:** 2.0 (Enhanced with ML Risk + Protocol Comparison)

---

## 📋 Module Overview

### Title
**Supply V2** - Safe Lending with AI Risk Analysis

### Description
Enhanced lending interface with ML-powered risk analysis, protocol comparison, and real-time APY updates. Supply assets to earn yield while understanding and managing risk.

### New Capabilities (V2)
- ✅ **ML Risk Scores** for each protocol
- ✅ **Protocol Comparison** before supplying
- ✅ **Real-time APY updates** via WebSocket
- ✅ **Risk Warnings** for high-risk protocols
- ✅ **Alternative Suggestions** for safer options
- ✅ **Historical Risk Trends**
- ✅ **Safety Score** per position

---

## 🖼️ Views & Wireframes

### View 1: Enhanced Supply Markets

```
┌─────────────────────────────────────┐
│  [←]        Earn            [?][🎚️]│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Your Supplies                  ││
│  │                                 ││
│  │  Total Supplied    $15,230.00  ││
│  │  Avg APY                 4.2%  ││
│  │  Portfolio Risk    🟢 2.4/10   ││
│  │  Earned (All Time)     +$234   ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Your Positions                     │
│  ┌─────────────────────────────────┐│
│  │ ┌─────┐ USDC on Aave   🟢 2.1  ││
│  │ │ $   │ $10,000 supplied       ││
│  │ └─────┘ 4.2% APY  +$35 earned  ││
│  │         Risk: LOW  Confidence: 94%│
│  │                    [Withdraw]  ││
│  ├─────────────────────────────────┤│
│  │ ┌─────┐ ETH on Euler   🔴 7.8  ││
│  │ │ Ξ   │ $5,230 supplied  ⚠️    ││
│  │ └─────┘ 6.8% APY  +$52 earned  ││
│  │         Risk: HIGH Recent exploit│
│  │         [View Safer Options →] ││
│  │                    [Withdraw]  ││
│  └─────────────────────────────────┘│
│                                     │
│  Supply More (Sorted by Safety)     │
│  ┌─────────────────────────────────┐│
│  │ ASSET  PROTOCOL  APY  RISK  ACT ││
│  ├─────────────────────────────────┤│
│  │ USDC   Aave     4.2%  🟢2.1    ││
│  │  2,500.00 available   [Supply] ││
│  ├─────────────────────────────────┤│
│  │ ETH    Lido     3.8%  🟢2.3    ││
│  │  1.52 available       [Supply] ││
│  ├─────────────────────────────────┤│
│  │ DAI    Compound 4.5%  🟡3.2    ││
│  │  500.00 available     [Supply] ││
│  └─────────────────────────────────┘│
│                                     │
│  [Compare Protocols] [Risk Filter]  │
│                                     │
└─────────────────────────────────────┘
```

### View 2: Supply with Risk Analysis

```
┌─────────────────────────────────────┐
│  [←]     Supply USDC to Aave       │
│                                     │
│  🟢 SAFE PROTOCOL (Risk: 2.1/10)   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Amount to Supply               ││
│  │  ┌───────────────────────────┐  ││
│  │  │        1,000              │  ││
│  │  │ Balance: 2,500 USDC [MAX] │  ││
│  │  │ ≈ $1,000.00               │  ││
│  │  └───────────────────────────┘  ││
│  └─────────────────────────────────┘│
│                                     │
│  Supply Details                     │
│  ┌─────────────────────────────────┐│
│  │  Supply APY       🔴 4.2%      ││
│  │  Protocol         Aave V3      ││
│  │  Network          Ethereum     ││
│  │  TVL              $8.2B        ││
│  │  ───────────────────────────   ││
│  │  Est. Yearly        $42.00     ││
│  │  Est. Monthly       $3.50      ││
│  └─────────────────────────────────┘│
│                                     │
│  Risk Analysis (ML-Powered)         │
│  ┌─────────────────────────────────┐│
│  │  Overall Risk:   2.1/10  🟢    ││
│  │  Confidence:     94%            ││
│  │                                 ││
│  │  • TVL Stability:   🟢 Excellent││
│  │  • Audit History:   🟢 Strong   ││
│  │  • Track Record:    🟢 Clean    ││
│  │  • Network Position: 🟢 Central ││
│  │                                 ││
│  │  [View Full Analysis →]        ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Would you like to compare with  │
│     other protocols before supplying?│
│     [Compare Options]               │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [✓] Use as collateral         ││
│  │      Enable borrowing against  ││
│  └─────────────────────────────────┘│
│                                     │
│  [Confirm Supply] [Cancel]          │
│                                     │
└─────────────────────────────────────┘
```

### View 3: Risk Warning & Alternatives

```
┌─────────────────────────────────────┐
│  [×]     ⚠️ High Risk Detected      │
│                                     │
│  🔴 Euler Finance (Risk: 7.8/10)   │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⚠️ WARNING                     ││
│  │                                 ││
│  │  This protocol has HIGH risk:  ││
│  │  • Recent security exploit      ││
│  │  • TVL decreased 65% (30d)     ││
│  │  • Confidence: 89%              ││
│  │                                 ││
│  │  You're about to supply:        ││
│  │  1,000 USDC ≈ $1,000           ││
│  │                                 ││
│  └─────────────────────────────────┘│
│                                     │
│  Safer Alternatives (GraphRAG)      │
│  ┌─────────────────────────────────┐│
│  │  ✅ Aave V3        4.2%  🟢2.1 ││
│  │     Similar lending, safer     ││
│  │     [Use This Instead]         ││
│  ├─────────────────────────────────┤│
│  │  ✅ Compound       4.5%  🟢2.5 ││
│  │     Alternative lending        ││
│  │     [Use This Instead]         ││
│  ├─────────────────────────────────┤│
│  │  ✅ Radiant        4.8%  🟡3.2 ││
│  │     Higher yield, medium risk  ││
│  │     [Use This Instead]         ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  I understand the risk         ││
│  │  [Proceed Anyway]              ││
│  └─────────────────────────────────┘│
│                                     │
│  [Go Back]                          │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 Enhanced API Endpoints

### Get Supply Markets with Risk

```typescript
// GET /api/v1/defi/supply/markets
interface GetSupplyMarketsResponse {
  success: true;
  data: {
    user_summary: {
      total_supplied_usd: number;
      avg_apy: number;
      total_earned_usd: number;
      portfolio_risk_score: number;  // NEW
      portfolio_risk_level: string;  // NEW
    };
    positions: EnhancedSupplyPosition[];
    available_markets: EnhancedSupplyMarket[];
  };
}

interface EnhancedSupplyPosition {
  id: string;
  token: TokenInfo;
  protocol: string;
  protocol_id: string;  // NEW
  chain: string;
  supplied_amount: string;
  supplied_usd: number;
  apy: number;
  earned_usd: number;
  is_collateral: boolean;
  
  // NEW: ML Risk fields
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  risk_trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  
  // NEW: Alerts
  has_alerts: boolean;
  alert_count: number;
}

interface EnhancedSupplyMarket {
  token: TokenInfo;
  protocol: string;
  protocol_id: string;  // NEW
  chain: string;
  apy: number;
  total_supplied_usd: number;
  available_balance: string;
  available_balance_usd: number;
  
  // NEW: ML Risk fields
  risk_score: number;
  risk_level: string;
  confidence: number;
  tvl_usd: number;
  tvl_change_7d_percent: number;
}
```

### Supply with Risk Check

```typescript
// POST /api/v1/defi/supply
interface SupplyRequest {
  token: string;
  amount: string;
  protocol_id: string;  // Changed from protocol name to ID
  chain: string;
  use_as_collateral: boolean;
  risk_acknowledged?: boolean;  // NEW: Required if risk > 5.0
}

interface SupplyResponse {
  success: boolean;
  transaction_hash?: string;
  
  // NEW: Risk check
  risk_check: {
    risk_score: number;
    risk_level: string;
    requires_acknowledgment: boolean;
    warnings: string[];
    alternatives?: Array<{
      protocol_id: string;
      protocol_name: string;
      apy: number;
      risk_score: number;
      similarity_score: number;
    }>;
  };
}
```

### Compare Supply Protocols

```typescript
// POST /api/v1/defi/supply/compare
interface CompareSupplyProtocolsRequest {
  token: string;
  amount: string;
  protocol_ids: string[];  // 2-5 protocols
}

interface CompareSupplyProtocolsResponse {
  comparisons: Array<{
    protocol_id: string;
    protocol_name: string;
    apy: number;
    risk_score: number;
    risk_level: string;
    tvl_usd: number;
    estimated_yearly_earnings: number;
    pros: string[];
    cons: string[];
  }>;
  recommendation: {
    protocol_id: string;
    reason: string;
    confidence: number;
  };
}
```

---

## 🔌 WebSocket Integration

### Real-Time APY Updates

```typescript
// Subscribe to supply APY updates
ws.send(JSON.stringify({
  type: 'subscribe:supply',
  protocols: ['aave-v3', 'compound'],
  tokens: ['USDC', 'ETH'],
}));

// Receive APY updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'apy:update') {
    // { protocol_id, token, apy_supply, apy_borrow }
    updateAPY(data);
  }
  
  if (data.type === 'risk:update') {
    // { protocol_id, risk_score, risk_level }
    updateRiskIndicator(data);
  }
};
```

---

## 🎨 Motion Design

### Risk Warning Animation

```typescript
// High risk warning shake
<motion.div
  initial={{ x: 0 }}
  animate={{ 
    x: isHighRisk ? [-10, 10, -10, 10, 0] : 0 
  }}
  transition={{ 
    duration: 0.4,
    times: [0, 0.25, 0.5, 0.75, 1]
  }}
>
  <RiskWarning />
</motion.div>

// Risk badge pulse for critical
const riskPulse = useSharedValue(1);

useEffect(() => {
  if (riskLevel === 'CRITICAL') {
    riskPulse.value = withRepeat(
      withSequence(
        withTiming(1.2, { duration: 500 }),
        withTiming(1, { duration: 500 })
      ),
      -1
    );
  }
}, [riskLevel]);
```

---

## 🎨 Component Specifications

```typescript
interface SupplyMarketsProps {
  sortBy?: 'safety' | 'apy' | 'tvl';
  riskFilter?: RiskLevel[];
}

interface SupplyFormProps {
  token: string;
  protocol: Protocol;
  onSubmit: (data: SupplyRequest) => void;
  showRiskAnalysis?: boolean;
}

interface RiskWarningModalProps {
  protocol: Protocol;
  amount: string;
  alternatives: Protocol[];
  onProceed: () => void;
  onSelectAlternative: (protocolId: string) => void;
  onCancel: () => void;
}

interface ProtocolComparisonProps {
  protocols: Protocol[];
  token: string;
  amount: string;
  onSelect: (protocolId: string) => void;
}
```

---

## ⚠️ Error Handling & Risk Warnings

```typescript
const supplyErrors = {
  SUPPLY_001: 'Insufficient balance',
  SUPPLY_002: 'Amount below minimum',
  SUPPLY_003: 'Protocol risk too high',
  SUPPLY_004: 'Risk acknowledgment required',
  SUPPLY_005: 'Transaction failed',
};

// Risk threshold checks
if (riskScore > 7.0 && !risk_acknowledged) {
  throw new Error(supplyErrors.SUPPLY_004);
}

// Show alternatives for high risk
if (riskScore > 5.0) {
  const alternatives = await getAlternativeProtocols(protocol_id);
  showRiskWarningModal({ protocol, alternatives });
}
```

---

## 🔒 Safety Features

- ✅ Pre-transaction risk analysis
- ✅ Required acknowledgment for high-risk (>5.0)
- ✅ Automatic alternative suggestions
- ✅ Real-time risk monitoring
- ✅ Portfolio risk aggregation
- ✅ Transaction simulation before execution

---

## ♿ Accessibility

- ✅ Risk levels with color + text + icons
- ✅ Screen reader warnings for high risk
- ✅ High contrast risk indicators
- ✅ Clear error messages
- ✅ Keyboard navigation
- ✅ Voice control compatible

---

*Document Version: 2.0*  
*Last Updated: December 1, 2025*  
*Module: Supply/Lend (Enhanced)*  
*Features: ML Risk + Protocol Comparison + Real-Time*
