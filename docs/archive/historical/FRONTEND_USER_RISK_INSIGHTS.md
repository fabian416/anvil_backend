# FRONTEND_USER_RISK_INSIGHTS

## User ML Risk Insights Module

**User Type:** Authenticated User  
**Module:** AI-Powered Risk Analysis  
**Route:** `/risk`, `/protocols/:id/risk`  
**Platform:** Mobile (React Native) & Web  
**Version:** 1.0 - ML Powered

---

## 📋 Module Overview

### Title
**Risk Insights** - AI-Powered Protocol Risk Analysis

### Description
Machine learning-powered risk analysis providing predictions, anomaly detection, risk forecasting, and contributing factor analysis. Users get comprehensive risk intelligence to make informed DeFi decisions.

### Key Capabilities
- ML risk prediction (0-10 scale)
- Anomaly detection alerts
- Risk trend forecasting
- Contributing factor breakdown
- Confidence scoring
- Historical risk tracking
- Comparative risk analysis
- Actionable recommendations

---

## 👤 User Stories

### US-USER-RISK-001: View Risk Predictions
**As a** user  
**I want to** see AI-predicted risk scores for protocols  
**So that** I can assess safety before investing

**Acceptance Criteria:**
- Risk score (0-10) displayed
- Risk level classification
- Confidence percentage
- Visual risk meter

---

### US-USER-RISK-002: See Anomaly Alerts
**As a** user  
**I want to** be alerted to unusual protocol behavior  
**So that** I can investigate potential issues

**Acceptance Criteria:**
- Anomaly detection notifications
- Metric deviations shown
- Z-score indicators
- Investigation recommendations

---

### US-USER-RISK-003: Forecast Risk Trajectory
**As a** user  
**I want to** see predicted risk trends  
**So that** I can anticipate future risks

**Acceptance Criteria:**
- Risk forecast chart
- Trend direction (↑↓→)
- Confidence interval
- 7-day and 30-day projections

---

### US-USER-RISK-004: Understand Risk Factors
**As a** user  
**I want to** understand what drives risk scores  
**So that** I can assess validity

**Acceptance Criteria:**
- Top contributing factors listed
- Impact quantification (+/- points)
- Factor explanations
- Historical context

---

## 🖼️ Views & Wireframes

### View 1: Risk Dashboard (Mobile)

```
┌─────────────────────────────────────┐
│  [←]    Risk Analysis       [Info] │
│                                     │
│  Aave V3                            │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ML RISK PREDICTION             ││
│  │                                 ││
│  │       ╭─────────╮               ││
│  │      │  2.1/10  │               ││
│  │      │         │               ││
│  │      │  🟢 LOW  │               ││
│  │       ╰─────────╯               ││
│  │                                 ││
│  │  ████░░░░░░░░░░░░░░              ││
│  │  0    3    5    7    10         ││
│  │                                 ││
│  │  Confidence: 92%                ││
│  │  Last Updated: 2 min ago        ││
│  │                                 ││
│  │  Trend: → STABLE                ││
│  └─────────────────────────────────┘│
│                                     │
│  📊 Risk Breakdown                  │
│  ┌─────────────────────────────────┐│
│  │  Graph Topology        -0.8 🟢  ││
│  │  High importance, low cascade   ││
│  │  ─────────────────────────────  ││
│  │  Market Metrics        -0.5 🟢  ││
│  │  Stable TVL, good liquidity     ││
│  │  ─────────────────────────────  ││
│  │  Historical Risk       -0.3 🟢  ││
│  │  No recent incidents, audited   ││
│  │  ─────────────────────────────  ││
│  │  Audit Coverage        +0.2 🟡  ││
│  │  Last audit 6 months ago        ││
│  │  ─────────────────────────────  ││
│  │  Volatility            +0.1 🟡  ││
│  │  Slight TVL fluctuations        ││
│  └─────────────────────────────────┘│
│                                     │
│  🛡️ Recommendations                 │
│  • Continue monitoring              │
│  • Review new audit when available  │
│  • Maintain current position        │
│                                     │
│  [View Forecast] [Compare Protocols]│
│                                     │
└─────────────────────────────────────┘
```

---

### View 2: Anomaly Alert

```
┌─────────────────────────────────────┐
│  [←]    Anomaly Detected     [⚠️]  │
│                                     │
│  🔴 UNUSUAL ACTIVITY DETECTED        │
│                                     │
│  Protocol: Euler Finance            │
│  Detected: 5 minutes ago            │
│  Severity: HIGH                     │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  ANOMALOUS METRICS              ││
│  │                                 ││
│  │  TVL Change Rate                ││
│  │  Current: -15%/hour             ││
│  │  Expected: ±2%/hour             ││
│  │  Z-Score: 4.2σ ⚠️                ││
│  │  ─────────────────────────────  ││
│  │  Withdrawal Volume              ││
│  │  Current: $45M/hour             ││
│  │  Expected: $5M/hour             ││
│  │  Z-Score: 5.1σ ⚠️                ││
│  │  ─────────────────────────────  ││
│  │  Transaction Count              ││
│  │  Current: 2,400/hour            ││
│  │  Expected: 800/hour             ││
│  │  Z-Score: 3.8σ ⚠️                ││
│  └─────────────────────────────────┘│
│                                     │
│  💡 Analysis:                       │
│  Unusually high withdrawal activity │
│  detected across multiple metrics.  │
│  This pattern is consistent with:   │
│  • Large position exit              │
│  • Potential security concern       │
│  • Market-wide deleveraging         │
│                                     │
│  🛡️ Recommended Actions:            │
│  1. Monitor official channels       │
│  2. Review security updates         │
│  3. Consider reducing exposure      │
│  4. Set up price alerts             │
│                                     │
│  💼 Your Exposure: $2,450 (5%)      │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  [Check Protocol Status]        ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [View Alternatives]            ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  [Reduce Position]              ││
│  └─────────────────────────────────┘│
│                                     │
└─────────────────────────────────────┘
```

---

### View 3: Risk Forecast

```
┌─────────────────────────────────────┐
│  [←]    Risk Forecast               │
│                                     │
│  Lido Finance                       │
│  Current Risk: 2.3/10 🟢            │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  RISK FORECAST (30 DAYS)        ││
│  │                                 ││
│  │  4.0┤                            ││
│  │     │                  ╭──╮      ││
│  │  3.0┤              ╭───╯  ╰──    ││
│  │     │          ╭───╯             ││
│  │  2.0┤──────────╯                 ││
│  │     │  ▓▓▓▓▓▓▓ Confidence        ││
│  │  1.0┤                            ││
│  │     │                            ││
│  │  0.0┼────────────────────────▶   ││
│  │     Now  7d   14d  21d  30d     ││
│  │                                 ││
│  │  Forecast: ↗ INCREASING         ││
│  │  Predicted: 3.4/10 (30d)        ││
│  │  Confidence: 76%                ││
│  └─────────────────────────────────┘│
│                                     │
│  📈 Trend Analysis:                 │
│  • Short-term (7d): → STABLE        │
│  • Medium-term (30d): ↗ INCREASING  │
│  • Volatility: LOW                  │
│                                     │
│  🔍 Driving Factors:                │
│  • Upcoming protocol upgrade        │
│  • Increased market volatility      │
│  • New competitor launch            │
│                                     │
│  🛡️ Recommendations:                │
│  • Monitor position over next 30d   │
│  • Set risk alert at 3.5/10         │
│  • Review alternatives if >4.0      │
│                                     │
│  [Set Alert] [View Alternatives]    │
│                                     │
└─────────────────────────────────────┘
```

---

### View 4: Contributing Factors Deep Dive

```
┌─────────────────────────────────────┐
│  [←]    Risk Factors                │
│                                     │
│  Compound V3                        │
│  Risk Score: 2.5/10 🟢              │
│                                     │
│  Top Contributing Factors           │
│  (Sorted by Impact)                 │
│                                     │
│  ┌─────────────────────────────────┐│
│  │  1. High TVL Stability   -1.2🟢 ││
│  │                                 ││
│  │  TVL has been stable at $3.8B   ││
│  │  for 90+ days with <5% variance.││
│  │  Strong indicator of protocol   ││
│  │  health and user confidence.    ││
│  │                                 ││
│  │  Impact: -1.2 points (reduces)  ││
│  │  Confidence: 95%                ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  2. Strong Audit History -0.9🟢 ││
│  │                                 ││
│  │  18 audits by top firms         ││
│  │  including OpenZeppelin, Trail  ││
│  │  of Bits. No critical issues in ││
│  │  past 12 months.                ││
│  │                                 ││
│  │  Impact: -0.9 points (reduces)  ││
│  │  Confidence: 98%                ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  3. High Network Centrality +0.6🟡││
│  │                                 ││
│  │  Critical node in DeFi network. ││
│  │  127 protocols depend on it.    ││
│  │  Failure would cascade widely.  ││
│  │                                 ││
│  │  Impact: +0.6 points (increases)││
│  │  Confidence: 89%                ││
│  └─────────────────────────────────┘│
│                                     │
│  ┌─────────────────────────────────┐│
│  │  4. Mature Protocol Age  -0.5🟢 ││
│  │                                 ││
│  │  Established 2020 (5 years).    ││
│  │  Battle-tested through multiple ││
│  │  market cycles and stress tests.││
│  │                                 ││
│  │  Impact: -0.5 points (reduces)  ││
│  │  Confidence: 92%                ││
│  └─────────────────────────────────┘│
│                                     │
│  [View All 12 Factors]              │
│                                     │
└─────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Get Risk Prediction

```typescript
// GET /api/v1/ml/prediction/:protocol_id
interface RiskPredictionResponse {
  protocol_id: string;
  protocol_name: string;
  risk_score: number; // 0-10
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number; // 0-1
  risk_trend: 'DECREASING' | 'STABLE' | 'INCREASING' | 'VOLATILE';
  contributing_factors: Array<{
    feature: string;
    impact: number; // -1 to +1
    explanation: string;
  }>;
  recommendations: string[];
  model_version: string;
  predicted_at: string;
}
```

---

### Detect Anomalies

```typescript
// GET /api/v1/ml/prediction/:protocol_id/anomalies
interface AnomalyDetectionResponse {
  protocol_id: string;
  protocol_name: string;
  is_anomalous: boolean;
  confidence: number;
  anomalies: Array<{
    feature: string;
    current_value: number;
    expected_value: number;
    deviation: number;
    z_score: number; // Standard deviations
    is_anomalous: boolean;
    severity: 'LOW' | 'MEDIUM' | 'HIGH';
  }>;
  overall_severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendations: string[];
  detected_at: string;
}
```

---

### Forecast Risk

```typescript
// GET /api/v1/ml/prediction/:protocol_id/forecast?days=30
interface RiskForecastResponse {
  protocol_id: string;
  protocol_name: string;
  current_risk: number;
  forecasts: Array<{
    days_ahead: number;
    predicted_risk: number;
    confidence_lower: number;
    confidence_upper: number;
    trend: 'DECREASING' | 'STABLE' | 'INCREASING';
  }>;
  overall_trend: 'DECREASING' | 'STABLE' | 'INCREASING' | 'VOLATILE';
  driving_factors: string[];
  recommendations: string[];
  forecast_generated_at: string;
}
```

---

### Batch Risk Prediction

```typescript
// POST /api/v1/ml/prediction/batch
interface BatchRiskRequest {
  protocol_ids: string[];
}

interface BatchRiskResponse {
  predictions: Array<RiskPredictionResponse>;
  summary: {
    average_risk: number;
    highest_risk: {
      protocol_id: string;
      protocol_name: string;
      risk_score: number;
    };
    lowest_risk: {
      protocol_id: string;
      protocol_name: string;
      risk_score: number;
    };
  };
}
```

---

## 🎬 Motion Design

```typescript
const riskAnimations = {
  // Risk meter fill
  riskMeterFill: {
    initial: { width: 0 },
    animate: { width: 'percentage%' },
    transition: {
      duration: 1.2,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  
  // Risk score count up
  riskScoreCounter: {
    initial: { value: 0 },
    animate: { value: 'targetValue' },
    transition: {
      duration: 1,
      ease: "easeOut"
    }
  },
  
  // Anomaly shake
  anomalyShake: {
    animate: {
      x: [0, -5, 5, -5, 5, 0],
      transition: {
        duration: 0.5,
        repeat: 2
      }
    }
  },
  
  // Factor card reveal
  factorReveal: {
    initial: { x: -20, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    transition: {
      duration: 0.3,
      delay: 'stagger' // 0.1s per card
    }
  },
  
  // Trend arrow animation
  trendArrow: {
    animate: {
      y: 'direction === "up" ? [-3, 0] : [3, 0]',
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  },
  
  // Confidence bar
  confidenceBar: {
    initial: { scaleX: 0 },
    animate: { scaleX: 1 },
    transition: { duration: 0.8 }
  },
  
  // Forecast line draw
  forecastLineDraw: {
    initial: { pathLength: 0 },
    animate: { pathLength: 1 },
    transition: {
      duration: 1.5,
      ease: "easeInOut"
    }
  }
};
```

---

## 🎨 Component Specifications

```typescript
// Risk meter gauge
interface RiskMeterProps {
  riskScore: number; // 0-10
  riskLevel: string;
  confidence: number;
  showLabel?: boolean;
  size?: 'small' | 'medium' | 'large';
}

// Factor card
interface FactorCardProps {
  factor: {
    feature: string;
    impact: number;
    explanation: string;
  };
  isExpanded?: boolean;
  onToggle?: () => void;
}

// Anomaly indicator
interface AnomalyIndicatorProps {
  anomaly: {
    feature: string;
    current_value: number;
    expected_value: number;
    z_score: number;
    severity: string;
  };
}

// Forecast chart
interface ForecastChartProps {
  forecasts: Array<{
    days_ahead: number;
    predicted_risk: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  currentRisk: number;
  width: number;
  height: number;
}

// Risk comparison
interface RiskComparisonProps {
  protocols: Array<{
    id: string;
    name: string;
    risk_score: number;
  }>;
  highlightProtocolId?: string;
}
```

---

## ⚠️ Error Handling

```typescript
const riskErrors = {
  RISK_001: 'Risk prediction failed',
  RISK_002: 'Insufficient data for prediction',
  RISK_003: 'ML service unavailable',
  RISK_004: 'Protocol not found',
  
  ANOMALY_001: 'Anomaly detection failed',
  ANOMALY_002: 'No anomalies detected',
  
  FORECAST_001: 'Forecast generation failed',
  FORECAST_002: 'Insufficient historical data',
};
```

---

## 🔒 Data Privacy

- Risk predictions cached locally
- No user-specific data in ML models
- Historical data anonymized
- Predictions not shared publicly

---

*Document Version: 1.0*  
*Last Updated: December 1, 2025*  
*Module: ML Risk Insights*
