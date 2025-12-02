# FRONTEND_USER_PORTFOLIO_RISK

## User Portfolio Risk Analysis Module

**User Type:** Authenticated User  
**Module:** Portfolio Risk Assessment  
**Route:** `/portfolio/risk`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0 - ML Powered

---

## 📋 Module Overview

### Title
**Portfolio Risk** - Comprehensive Portfolio Risk Analysis

### Description
Advanced portfolio risk assessment combining ML predictions, network analysis, and dependency mapping. Users get comprehensive understanding of their portfolio's risk profile with actionable recommendations for optimization.

### Key Capabilities
- Overall portfolio risk score
- Risk distribution by level
- Protocol-specific risks
- Dependency risk analysis
- Systemic risk assessment
- Concentration risk calculation
- Chain-specific risk distribution
- Cascade simulation
- Value at Risk (VaR) calculation
- Actionable recommendations

---

## 👤 User Stories

### US-USER-PORTFOLIO-RISK-001: View Overall Risk
**As a** user  
**I want to** see my portfolio's overall risk score  
**So that** I understand my aggregate risk exposure

**Acceptance Criteria:**
- Weighted risk score displayed
- Risk level classification
- Visual risk meter
- Comparison to benchmarks

---

### US-USER-PORTFOLIO-RISK-002: See Protocol Risks
**As a** user  
**I want to** see risk breakdown by protocol  
**So that** I can identify high-risk positions

**Acceptance Criteria:**
- List of protocols sorted by risk
- Individual risk scores
- Exposure amounts
- Risk trends
- Quick action buttons

---

### US-USER-PORTFOLIO-RISK-003: Understand Dependencies
**As a** user  
**I want to** see dependency risks in my portfolio  
**So that** I can understand systemic risks

**Acceptance Criteria:**
- Dependency map visualization
- Critical dependencies highlighted
- Impact if dependency fails
- Total exposure at risk

---

### US-USER-PORTFOLIO-RISK-004: Simulate Cascade
**As a** user  
**I want to** simulate protocol failure impact  
**So that** I can prepare for worst-case scenarios

**Acceptance Criteria:**
- Select protocol to simulate
- See cascade path
- Calculate potential loss
- Get action recommendations

---

## 🖼️ Views & Wireframes

### View 1: Portfolio Risk Dashboard (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Portfolio Risk      [Info] │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  OVERALL PORTFOLIO RISK         ││
│  │                                 ││
│  │       ╭───────────╮             ││
│  │      │   3.2/10   │             ││
│  │      │            │             ││
│  │      │  🟡 MEDIUM │             ││
│  │       ╰───────────╯             ││
│  │                                 ││
│  │  ████████░░░░░░░░░░              ││
│  │  0    3    5    7    10         ││
│  │                                 ││
│  │  Confidence: 89%                ││
│  │  Last Updated: 5 min ago        ││
│  └─────────────────────────────────┘│
│                                     │
│  📊 Risk Distribution               │
│  ┌─────────────────────────────────┐│
│  │  🟢 LOW      45% ████████████   ││
│  │  🟡 MEDIUM   35% █████████      ││
│  │  🟠 HIGH     15% ████           ││
│  │  🔴 CRITICAL  5% ██             ││
│  └─────────────────────────────────┘│
│                                     │
│  ⚠️ Protocols at Elevated Risk (3)  │
│  ┌─────────────────────────────────┐│
│  │  🔴 Euler Finance               ││
│  │     Risk: 7.8/10  |  $2,450 (5%)││
│  │     → [Review] [Reduce]         ││
│  ├─────────────────────────────────┤│
│  │  🟠 Frax Finance                ││
│  │     Risk: 5.2/10  |  $1,800 (4%)││
│  │     → [Monitor]                 ││
│  ├─────────────────────────────────┤│
│  │  🟡 Convex Finance              ││
│  │     Risk: 4.8/10  |  $3,200 (7%)││
│  │     → [Monitor]                 ││
│  └─────────────────────────────────┘│
│                                     │
│  📈 Key Metrics                     │
│  ┌─────────────────────────────────┐│
│  │  Systemic Risk:    4.1/10 🟡    ││
│  │  Concentration:    3.8/10 🟡    ││
│  │  Value at Risk:    $8,450 (18%) ││
│  └─────────────────────────────────┘│
│                                     │
│  [View Dependencies] [Simulate Loss]│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Dependency Risk Map

```
┌─────────────────────────────────────┐
│  [←]    Dependency Risks            │
│                                     │
│  Critical Dependencies (2)          │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ⚠️ Chainlink                   ││
│  │                                 ││
│  │  Affects 3 of your protocols:   ││
│  │  • Aave V3 ($8,200)             ││
│  │  • Compound ($3,400)            ││
│  │  • Synthetix ($1,200)           ││
│  │                                 ││
│  │  Impact if Fails: 🔴 CRITICAL   ││
│  │  Total at Risk: $12,800 (26%)   ││
│  │  Dependency Risk: 6.2/10        ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │     Chainlink ●           │  ││
│  │  │     /    |    \           │  ││
│  │  │  Aave  Comp  Synth        │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  [Simulate Failure] [Diversify] ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  🟡 USDC                        ││
│  │                                 ││
│  │  Affects 5 of your protocols:   ││
│  │  • Aave ($8,200)                ││
│  │  • Curve ($2,800)               ││
│  │  • ... (+3 more)                ││
│  │                                 ││
│  │  Impact if Depeg: 🟠 HIGH       ││
│  │  Total at Risk: $18,400 (38%)   ││
│  │  Dependency Risk: 5.5/10        ││
│  │                                 ││
│  │  [Simulate Depeg] [Hedge]       ││
│  └─────────────────────────────────┘│
│                                     │
│  [View All Dependencies (8)]        │
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Cascade Simulation

```
┌─────────────────────────────────────┐
│  [←]    Cascade Simulation          │
│                                     │
│  Simulate: Chainlink Failure        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  SIMULATION RESULTS             ││
│  │                                 ││
│  │  Origin: Chainlink              ││
│  │  Scenario: Complete failure     ││
│  │  Cascade Probability: 68%       ││
│  │                                 ││
│  │  ┌───────────────────────────┐  ││
│  │  │  Cascade Map:             │  ││
│  │  │                           │  ││
│  │  │    [CHAINLINK] 💥         │  ││
│  │  │     ↙   ↓   ↘             │  ││
│  │  │  Aave Comp Synth          │  ││
│  │  │    ↓    ↓    ↓            │  ││
│  │  │  Curve Yearn ...          │  ││
│  │  │                           │  ││
│  │  │  Direct: 3 protocols      │  ││
│  │  │  Indirect: 8 protocols    │  ││
│  │  └───────────────────────────┘  ││
│  │                                 ││
│  │  Directly Affected:             ││
│  │  • Aave V3 ($8,200)             ││
│  │  • Compound ($3,400)            ││
│  │  • Synthetix ($1,200)           ││
│  │                                 ││
│  │  Indirectly Affected:           ││
│  │  • Curve ($2,800)               ││
│  │  • Balancer ($2,200)            ││
│  │  • ... (+6 more)                ││
│  │                                 ││
│  │  ─────────────────────────────  ││
│  │                                 ││
│  │  Worst Case Loss: $12,800       ││
│  │  % of Portfolio: 26%            ││
│  │  Time to Impact: Immediate      ││
│  └─────────────────────────────────┘│
│                                     │
│  🛡️ Recommended Actions:            │
│  ┌─────────────────────────────────┐│
│  │  Exit Immediately:              ││
│  │  • None (indirect exposure)     ││
│  │                                 ││
│  │  Reduce Exposure:               ││
│  │  • Aave V3 (50% reduction)      ││
│  │  • Compound (50% reduction)     ││
│  │  • Synthetix (full exit)        ││
│  │                                 ││
│  │  Safe Protocols (keep):         ││
│  │  • Lido Finance ✓               ││
│  │  • Rocket Pool ✓                ││
│  │  • Uniswap V3 ✓                 ││
│  └─────────────────────────────────┘│
│                                     │
│  [Run Different Scenario]           │
│  [Export Report]                    │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Portfolio Risk

```typescript
// GET /api/v1/portfolio/risk
interface PortfolioRiskResponse {
  user_id: string;
  overall_risk_score: number; // 0-10, weighted by exposure
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  protocols_at_risk: Array<{
    protocol_id: string;
    protocol_name: string;
    exposure_usd: number;
    exposure_percentage: number;
    risk_score: number;
    risk_level: string;
    risk_trend: string;
    contributing_factors: string[];
    value_at_risk_usd: number;
  }>;
  dependency_risks: Array<{
    dependency_protocol_id: string;
    dependency_protocol_name: string;
    dependent_protocols: string[];
    impact_if_failure: string;
    total_exposure_usd: number;
    risk_score: number;
  }>;
  systemic_risk_score: number;
  concentration_risk: number;
  chain_risk_distribution: Record<string, number>;
  recommendations: string[];
  total_value_at_risk_usd: number;
  last_updated: string;
}
```

---

### Simulate Cascade

```typescript
// POST /api/v1/portfolio/risk/simulate-cascade
interface CascadeSimulationRequest {
  origin_protocol_id: string;
}

interface CascadeSimulationResponse {
  user_id: string;
  cascade_impacts: Array<{
    origin_protocol_id: string;
    origin_protocol_name: string;
    directly_affected: string[];
    indirectly_affected: string[];
    total_exposure_at_risk_usd: number;
    cascade_probability: number;
    time_to_impact: string; // "immediate" | "hours" | "days"
  }>;
  worst_case_loss_usd: number;
  worst_case_loss_percentage: number;
  protocols_to_exit: string[];
  protocols_to_reduce: string[];
  safe_protocols: string[];
}
```

---

## 🎬 Motion Design

```typescript
const portfolioRiskAnimations = {
  // Risk score reveal
  riskScoreReveal: {
    initial: { scale: 0, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 20
    }
  },
  
  // Distribution bars
  distributionBars: {
    initial: { scaleX: 0 },
    animate: { scaleX: 1 },
    transition: {
      duration: 0.8,
      delay: 'stagger',
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Cascade animation
  cascadeFlow: {
    animate: {
      pathLength: [0, 1],
      opacity: [0, 1, 0.5],
      transition: {
        duration: 2,
        ease: "easeInOut"
      }
    }
  },
  
  // Warning pulse
  warningPulse: {
    animate: {
      scale: [1, 1.05, 1],
      transition: {
        duration: 1.5,
        repeat: Infinity
      }
    }
  }
};
```

---

## 🎨 Component Specifications

```typescript
interface PortfolioRiskDashboardProps {
  userId: string;
  refreshInterval?: number; // Auto-refresh in ms
}

interface RiskDistributionChartProps {
  distribution: Record<string, number>;
  totalValue: number;
}

interface ProtocolRiskCardProps {
  protocol: {
    id: string;
    name: string;
    exposure_usd: number;
    exposure_percentage: number;
    risk_score: number;
    risk_level: string;
  };
  onReview: () => void;
  onReduce: () => void;
}

interface DependencyRiskMapProps {
  dependencies: Array<{
    id: string;
    name: string;
    dependents: string[];
    impact: string;
    exposure: number;
  }>;
  onSimulate: (id: string) => void;
}

interface CascadeSimulatorProps {
  protocolId: string;
  onComplete: (result: CascadeSimulationResponse) => void;
}
```

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: Portfolio Risk Analysis*
