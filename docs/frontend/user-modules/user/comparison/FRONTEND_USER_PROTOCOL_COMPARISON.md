# FRONTEND_USER_PROTOCOL_COMPARISON

## User Comparison - Protocol Side-by-Side Analysis Module

**User Type:** Authenticated User  
**Module:** Protocol Comparison - Multi-Dimensional Side-by-Side Analysis  
**Route:** `/comparison`, `/protocols/compare`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0

---

## 📋 Module Overview

### Title
**Protocol Comparison** - Intelligent Multi-Protocol Analysis & Recommendations

### Description
Comprehensive protocol comparison system that enables users to compare 2-5 protocols side-by-side across multiple dimensions (risk, yield, security, network activity). Provides visual comparison matrices, identifies tradeoffs, determines winners by category, and delivers AI-powered recommendations to help users make informed decisions.

### Key Capabilities
- ✅ Compare 2-5 protocols simultaneously
- ✅ Multi-dimensional analysis (risk, yield, security, network)
- ✅ Visual comparison matrices (tables, charts)
- ✅ ML-powered risk scoring
- ✅ Winner identification (safest, highest yield, most secure, most active, balanced)
- ✅ Tradeoff analysis (risk vs yield, size vs safety)
- ✅ AI-generated recommendations
- ✅ Historical comparison (trending)
- ✅ Export comparison report

---

## 👤 User Stories

### US-USER-COMPARE-001: Compare Multiple Protocols
**As a** user  
**I want to** compare multiple protocols side-by-side  
**So that** I can understand their relative strengths and weaknesses

**Acceptance Criteria:**
- Select 2-5 protocols to compare
- Choose comparison dimensions
- View comparison matrix
- See winner by dimension
- Get AI recommendation

---

### US-USER-COMPARE-002: View Tradeoffs
**As a** user  
**I want to** see key tradeoffs between protocols  
**So that** I can make informed decisions based on my priorities

**Acceptance Criteria:**
- Shows risk vs yield tradeoffs
- Shows TVL vs safety tradeoffs
- Clear explanations
- Visual indicators

---

### US-USER-COMPARE-003: Get AI Recommendation
**As a** user  
**I want to** receive an AI-powered recommendation  
**So that** I get expert guidance on which protocol is best for me

**Acceptance Criteria:**
- Recommends one protocol
- Explains reasoning
- Shows confidence score
- Suggests alternatives

---

### US-USER-COMPARE-004: Filter by Dimension
**As a** user  
**I want to** focus on specific comparison dimensions  
**So that** I can analyze what matters most to me

**Acceptance Criteria:**
- Select/deselect dimensions
- See filtered comparison
- Update recommendation

---

### US-USER-COMPARE-005: Export Comparison
**As a** user  
**I want to** export the comparison report  
**So that** I can review it later or share with others

**Acceptance Criteria:**
- Export as PDF/CSV
- Includes all comparison data
- Formatted for readability

---

## 🖼️ Wireframes

### View 1: Protocol Comparison Screen (Web - Desktop)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [←]    Protocol Comparison                         [Export PDF] [⚙️]│
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Comparing 3 Protocols                                                │
│  Dimensions: [✓Risk] [✓Yield] [✓Security] [ ]Network                │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │         │   Aave V3    │ Compound V3 │   Morpho    │           │ │
│  ├─────────┼──────────────┼─────────────┼─────────────┤           │ │
│  │ Logo    │     (🅰️)     │     (🧿)    │     (🦋)    │           │ │
│  │         │              │             │             │           │ │
│  │ Chain   │  Ethereum    │  Ethereum   │  Ethereum   │           │ │
│  │ Category│  Lending     │  Lending    │  Lending    │           │ │
│  │         │              │             │             │           │ │
│  ├─────────┴──────────────┴─────────────┴─────────────┤           │ │
│  │  RISK COMPARISON                                    │           │ │
│  ├─────────┬──────────────┬─────────────┬─────────────┤           │ │
│  │ Score   │  🟢 2.1 ✓   │  🟡 3.5     │  🟢 1.8 ★   │← Winner   │ │
│  │ Level   │  LOW         │  MEDIUM     │  LOW        │           │ │
│  │ Trend   │  ↓ Down      │  → Stable   │  ↓ Down     │           │ │
│  │ Confid. │  94%         │  89%        │  96%        │           │ │
│  │         │              │             │             │           │ │
│  ├─────────┴──────────────┴─────────────┴─────────────┤           │ │
│  │  YIELD COMPARISON                                   │           │ │
│  ├─────────┬──────────────┬─────────────┬─────────────┤           │ │
│  │ Supply  │  3.2% APY    │  4.1% APY ★ │  3.8% APY   │← Winner   │ │
│  │ Borrow  │  5.1% APY    │  5.8% APY   │  4.9% APY   │           │ │
│  │ Max APY │  5.1%        │  5.8% ★     │  4.9%       │           │ │
│  │         │              │             │             │           │ │
│  ├─────────┴──────────────┴─────────────┴─────────────┤           │ │
│  │  SECURITY COMPARISON                                │           │ │
│  ├─────────┬──────────────┬─────────────┬─────────────┤           │ │
│  │ Audits  │  8 audits ★  │  6 audits   │  4 audits   │← Winner   │ │
│  │ Auditors│  Trail of    │  OpenZep,   │  Spearbit,  │           │ │
│  │         │  Bits, Peck  │  Certik     │  Trail of   │           │ │
│  │ Vulns   │  2 (fixed)   │  1 (fixed)  │  0 ✓        │           │ │
│  │ Last    │  2 weeks ago │  1 month    │  3 weeks    │           │ │
│  │         │              │             │             │           │ │
│  ├─────────┴──────────────┴─────────────┴─────────────┤           │ │
│  │  TVL & ACTIVITY                                     │           │ │
│  ├─────────┬──────────────┬─────────────┬─────────────┤           │ │
│  │ TVL     │  $8.2B ★     │  $4.1B      │  $890M      │← Largest  │ │
│  │ 24h Chg │  +2.3%       │  -0.5%      │  +5.1%      │           │ │
│  │ Volume  │  $210M/day   │  $95M/day   │  $28M/day   │           │ │
│  └─────────┴──────────────┴─────────────┴─────────────┘           │ │
│                                                                     │ │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│  ┃  🏆 WINNERS BY DIMENSION                                      ┃ │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│  ┃  🛡️  Safest:        Morpho (1.8 risk score)                  ┃ │
│  ┃  💰 Highest Yield:  Compound V3 (5.8% APY)                   ┃ │
│  ┃  🔒 Most Secure:    Aave V3 (8 audits)                       ┃ │
│  ┃  ⚖️  Balanced Best:  Morpho (highest overall score)          ┃ │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                     │ │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│  ┃  ⚠️  KEY TRADEOFFS                                            ┃ │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│  ┃  Risk vs Yield:                                               ┃ │
│  ┃  Morpho is safest (1.8) but Compound offers higher yield     ┃ │
│  ┃  (5.8% APY vs 4.9%)                                           ┃ │
│  ┃                                                               ┃ │
│  ┃  Size vs Safety:                                              ┃ │
│  ┃  Aave has largest TVL ($8.2B) but Morpho is safer (1.8 vs    ┃ │
│  ┃  2.1 risk score)                                              ┃ │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                     │ │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│  ┃  🤖 AI RECOMMENDATION                                         ┃ │
│  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫ │
│  ┃  We recommend: Morpho                                         ┃ │
│  ┃  Confidence: 85%                                              ┃ │
│  ┃                                                               ┃ │
│  ┃  Reasoning:                                                   ┃ │
│  ┃  Morpho offers the best balance of safety (lowest risk at    ┃ │
│  ┃  1.8), competitive yield (4.9% APY), and zero known          ┃ │
│  ┃  vulnerabilities. While Compound offers slightly higher      ┃ │
│  ┃  yield, Morpho's superior risk profile makes it the safer    ┃ │
│  ┃  choice for most users.                                       ┃ │
│  ┃                                                               ┃ │
│  ┃  Alternatives to Consider:                                    ┃ │
│  ┃  • Aave V3 - if TVL size/liquidity is priority               ┃ │
│  ┃  • Compound V3 - if maximizing yield is priority             ┃ │
│  ┃                                                               ┃ │
│  ┃  [View Full Analysis]                                         ┃ │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                                                     │ │
└──────────────────────────────────────────────────────────────────────┘
```

---

### View 2: Comparison Setup (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Compare Protocols           │
├─────────────────────────────────────┤
│                                     │
│  Select Protocols (2-5)             │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ✓ Aave V3                      ││
│  │    Ethereum • Lending           ││
│  │    Risk: 🟢 2.1 • APY: 3.2%    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ✓ Compound V3                  ││
│  │    Ethereum • Lending           ││
│  │    Risk: 🟡 3.5 • APY: 4.1%    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ✓ Morpho                       ││
│  │    Ethereum • Lending           ││
│  │    Risk: 🟢 1.8 • APY: 3.8%    ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [ ] Curve Finance              ││
│  │      Ethereum • DEX             ││
│  │      Risk: 🟡 2.9 • TVL: $3.2B ││
│  └─────────────────────────────────┘│
│                                     │
│  Compare By:                        │
│  [✓Risk] [✓Yield] [✓Security]      │
│  [ ]Network [ ]Governance           │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Compare 3 Protocols]          ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Comparison Results (Mobile - Scrollable)

```
┌─────────────────────────────────────┐
│  [←]    Comparison Results    [⚙️]  │
├─────────────────────────────────────┤
│                                     │
│  🏆 AI Recommendation               │
│  ┌─────────────────────────────────┐│
│  │  Morpho                         ││
│  │  🟢 Best Overall (85% confident)││
│  │                                 ││
│  │  ✓ Lowest risk (1.8)            ││
│  │  ✓ Competitive yield (4.9%)     ││
│  │  ✓ Zero vulnerabilities         ││
│  │                                 ││
│  │  [View Details] →               ││
│  └─────────────────────────────────┘│
│                                     │
│  ═══════════════════════════════════ │
│                                     │
│  🛡️  RISK SCORES                    │
│  Swipe to see all →                 │
│                                     │
│  ╔═══════════════════════════════╗ │
│  ║  1. Morpho       1.8  🟢 ★    ║ │
│  ║     Trend: ↓ Decreasing       ║ │
│  ║     Confidence: 96%           ║ │
│  ╚═══════════════════════════════╝ │
│  ┌─────────────────────────────────┐│
│  │  2. Aave V3      2.1  🟢      ││
│  │     Trend: ↓ Decreasing       ││
│  │     Confidence: 94%           ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  3. Compound V3  3.5  🟡      ││
│  │     Trend: → Stable           ││
│  │     Confidence: 89%           ││
│  └─────────────────────────────────┘│
│                                     │
│  ═══════════════════════════════════ │
│                                     │
│  💰 YIELD (APY)                     │
│                                     │
│  ╔═══════════════════════════════╗ │
│  ║  1. Compound V3  5.8% ★       ║ │
│  ║     Supply: 4.1% Borrow: 5.8% ║ │
│  ╚═══════════════════════════════╝ │
│  ┌─────────────────────────────────┐│
│  │  2. Aave V3      5.1%         ││
│  │     Supply: 3.2% Borrow: 5.1% ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  3. Morpho       4.9%         ││
│  │     Supply: 3.8% Borrow: 4.9% ││
│  └─────────────────────────────────┘│
│                                     │
│  ═══════════════════════════════════ │
│                                     │
│  🔒 SECURITY                        │
│                                     │
│  ╔═══════════════════════════════╗ │
│  ║  1. Aave V3      8 audits ★   ║ │
│  ║     Trail of Bits, Peckshield ║ │
│  ║     Vulnerabilities: 2 (fixed)║ │
│  ╚═══════════════════════════════╝ │
│  ┌─────────────────────────────────┐│
│  │  2. Compound V3  6 audits     ││
│  │     OpenZeppelin, Certik      ││
│  │     Vulnerabilities: 1 (fixed)││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  3. Morpho       4 audits     ││
│  │     Spearbit, Trail of Bits   ││
│  │     Vulnerabilities: 0 ✓      ││
│  └─────────────────────────────────┘│
│                                     │
│  ═══════════════════════════════════ │
│                                     │
│  ⚠️  KEY TRADEOFFS                  │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Risk vs Yield                  ││
│  │                                 ││
│  │  Morpho is safest but Compound  ││
│  │  offers 18% higher yield.       ││
│  │                                 ││
│  │  Consider your risk tolerance.  ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  Size vs Safety                 ││
│  │                                 ││
│  │  Aave has 9x larger TVL but     ││
│  │  Morpho is 14% safer.           ││
│  │                                 ││
│  │  Larger doesn't always = safer. ││
│  └─────────────────────────────────┘│
│                                     │
│  [Export Report (PDF)]              │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Integration

### Compare Protocols

```typescript
// POST /api/v1/comparison/protocols
interface CompareProtocolsRequest {
  protocol_ids: string[]; // 2-5 protocol UUIDs
  dimensions?: string[]; // Optional: ['risk', 'yield', 'security', 'network']
}

interface ComparisonResponse {
  protocols: ProtocolDetail[];
  comparison_matrix: ComparisonMatrix;
  winner_by_dimension: Winners;
  trade_offs: TradeOff[];
  recommendation: AIRecommendation;
}

interface ProtocolDetail {
  protocol_id: string;
  name: string;
  chain: string;
  category: string;
  logo_url: string | null;
  risk: {
    score: number; // 0-10
    level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    confidence: number; // 0-1
    trend: 'INCREASING' | 'DECREASING' | 'STABLE';
  };
  tvl: {
    current_usd: number;
    change_24h_percent: number;
    change_7d_percent: number;
  };
  yield: {
    supply_apy: number | null;
    borrow_apy: number | null;
    stake_apy: number | null;
  };
  security: {
    audit_count: number;
    auditors: string[];
    last_audit: string | null;
    vulnerabilities: number;
  };
  network: {
    users_24h: number | null;
    transactions_24h: number | null;
    centrality: number | null;
  };
  historical: {
    age_days: number;
    incidents: number;
  };
}

interface ComparisonMatrix {
  risk?: DimensionComparison;
  yield?: DimensionComparison;
  security?: DimensionComparison;
  network?: DimensionComparison;
}

interface DimensionComparison {
  metric: string;
  lower_is_better: boolean;
  values: ComparisonValue[];
  best: string; // Protocol name
  worst?: string;
}

interface ComparisonValue {
  protocol: string;
  value: number;
  label?: string;
  trend?: string;
  [key: string]: any; // Additional dimension-specific fields
}

interface Winners {
  safest?: string;
  highest_yield?: string;
  most_secure?: string;
  most_active?: string;
  balanced: string; // Overall best
}

interface TradeOff {
  dimension: string; // e.g., "Risk vs Yield"
  description: string;
}

interface AIRecommendation {
  recommended_protocol: string;
  reason: string;
  confidence: number; // 0-1
  alternatives: string[];
}

const compareProtocols = async (
  protocolIds: string[],
  dimensions?: string[]
): Promise<ComparisonResponse> => {
  const response = await api.post('/api/v1/comparison/protocols', {
    protocol_ids: protocolIds,
    dimensions,
  });
  return response.data;
};
```

---

## 🎨 Motion Design

### Comparison Matrix Animation (Framer Motion)

```typescript
import { motion } from 'framer-motion';

function ComparisonMatrix({ matrix, dimension }: ComparisonMatrixProps) {
  const comparison = matrix[dimension];
  
  return (
    <div className="space-y-3">
      <h3 className="font-bold text-lg uppercase">{dimension} Comparison</h3>
      
      {comparison.values.map((value, idx) => {
        const isWinner = value.protocol === comparison.best;
        
        return (
          <motion.div
            key={value.protocol}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`p-4 rounded-lg ${
              isWinner ? 'bg-green-50 border-2 border-green-500' : 'bg-gray-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl font-bold text-gray-400">
                  {idx + 1}.
                </span>
                <div>
                  <div className="font-semibold">{value.protocol}</div>
                  <div className="text-sm text-gray-600">
                    {value.label || value.trend}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: idx * 0.1 + 0.2, type: 'spring' }}
                  className="text-2xl font-bold"
                >
                  {value.value}
                </motion.span>
                {isWinner && (
                  <motion.span
                    initial={{ rotate: -180, scale: 0 }}
                    animate={{ rotate: 0, scale: 1 }}
                    transition={{ delay: idx * 0.1 + 0.3, type: 'spring' }}
                    className="text-2xl"
                  >
                    ★
                  </motion.span>
                )}
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
```

### AI Recommendation Reveal Animation

```typescript
function AIRecommendationCard({ recommendation }: AIRecommendationProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.8, type: 'spring', stiffness: 100 }}
      className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-6 border-2 border-blue-200 shadow-lg"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 1, type: 'spring', stiffness: 200 }}
        className="flex items-center gap-3 mb-4"
      >
        <span className="text-4xl">🤖</span>
        <div>
          <h3 className="font-bold text-xl">AI Recommendation</h3>
          <div className="text-sm text-gray-600">
            Confidence: {Math.round(recommendation.confidence * 100)}%
          </div>
        </div>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
      >
        <div className="text-2xl font-bold mb-2">
          {recommendation.recommended_protocol}
        </div>
        <p className="text-gray-700 mb-4">{recommendation.reason}</p>
        
        {recommendation.alternatives.length > 0 && (
          <div className="text-sm text-gray-600">
            <div className="font-semibold mb-1">Alternatives:</div>
            <div className="space-y-1">
              {recommendation.alternatives.map((alt) => (
                <div key={alt}>• {alt}</div>
              ))}
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
```

---

## 📱 Component Specifications

### ComparisonScreen Component

```typescript
interface ComparisonScreenProps {
  selectedProtocols: string[];
  onBack: () => void;
}

function ComparisonScreen({ selectedProtocols, onBack }: ComparisonScreenProps) {
  const [dimensions, setDimensions] = useState(['risk', 'yield', 'security']);
  const { comparison, isLoading } = useProtocolComparison(
    selectedProtocols,
    dimensions
  );
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  return (
    <div className="p-4">
      <header className="flex items-center justify-between mb-6">
        <button onClick={onBack}>←</button>
        <h1 className="text-2xl font-bold">Comparison Results</h1>
        <button onClick={() => exportComparison(comparison)}>
          Export PDF
        </button>
      </header>
      
      {/* AI Recommendation */}
      <AIRecommendationCard recommendation={comparison.recommendation} />
      
      {/* Winners Summary */}
      <WinnersSummary winners={comparison.winner_by_dimension} />
      
      {/* Comparison Matrices */}
      {dimensions.map((dimension) => (
        <ComparisonMatrix
          key={dimension}
          matrix={comparison.comparison_matrix}
          dimension={dimension}
        />
      ))}
      
      {/* Tradeoffs */}
      <TradeoffsList tradeoffs={comparison.trade_offs} />
    </div>
  );
}
```

---

## 🔗 React Hooks

### useProtocolComparison Hook

```typescript
import { useQuery } from '@tanstack/react-query';

export function useProtocolComparison(
  protocolIds: string[],
  dimensions?: string[]
) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['protocol-comparison', protocolIds, dimensions],
    queryFn: async () => {
      const response = await api.post('/api/v1/comparison/protocols', {
        protocol_ids: protocolIds,
        dimensions,
      });
      return response.data;
    },
    enabled: protocolIds.length >= 2 && protocolIds.length <= 5,
    staleTime: 300000, // 5 minutes
  });
  
  return {
    comparison: data,
    isLoading,
    error,
  };
}
```

---

## 🎭 User Flows

### Flow 1: Compare Protocols

```
1. User selects "Compare" on protocol page
   ↓
2. Opens protocol selector
   ↓
3. Checks 2-5 protocols to compare
   ↓
4. Selects comparison dimensions
   ↓
5. Taps "Compare Protocols"
   ↓
6. Loading indicator (2-3 seconds)
   ↓
7. Results screen appears
   ↓
8. Views AI recommendation at top
   ↓
9. Scrolls through comparison matrices
   ↓
10. Reviews tradeoffs
   ↓
11. Makes decision or exports report
```

---

## ⚠️ Error Handling

```typescript
const comparisonErrors = {
  COMPARE_001: 'Must compare 2-5 protocols',
  COMPARE_002: 'Protocol not found',
  COMPARE_003: 'Failed to fetch comparison data',
  COMPARE_004: 'Invalid comparison dimension',
};

try {
  const comparison = await compareProtocols(protocolIds);
} catch (error) {
  if (error.code === 'COMPARE_001') {
    toast.error('Please select 2-5 protocols to compare');
  } else {
    toast.error('Comparison failed. Please try again.');
  }
}
```

---

## ♿ Accessibility

```typescript
<table role="table" aria-label="Protocol comparison matrix">
  <thead>
    <tr role="row">
      <th role="columnheader">Metric</th>
      {protocols.map((p) => (
        <th key={p.id} role="columnheader">{p.name}</th>
      ))}
    </tr>
  </thead>
  <tbody>
    {/* Comparison rows */}
  </tbody>
</table>
```

---

## 🧪 Testing

```typescript
describe('ProtocolComparison', () => {
  it('compares multiple protocols', async () => {
    const { getByText } = render(
      <ComparisonScreen selectedProtocols={['aave', 'compound']} onBack={jest.fn()} />
    );
    
    await waitFor(() => {
      expect(getByText('AI Recommendation')).toBeInTheDocument();
      expect(getByText('Aave V3')).toBeInTheDocument();
      expect(getByText('Compound V3')).toBeInTheDocument();
    });
  });
});
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Protocol Comparison*  
*Backend Status: ✅ 100% Implemented (1 endpoint)*  
*Frontend Status: ✅ Ready for Implementation*
