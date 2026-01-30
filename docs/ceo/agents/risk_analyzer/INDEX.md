# Risk Analyzer Agent - Complete Index

> **Project:** Anvil DeFi Chat - Risk Assessment
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **RISK_ANALYZER** agent, Anvil's protocol and token risk assessment system.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and risk categories |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Two-layer risk system (agent + service)
- DeFiLlama integration
- Risk scoring algorithms
- Protocol classification

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- DeFiLlama data fetching
- Risk calculation logic

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Risk assessment patterns and categories:

**Key Contents:**
- Supported query types
- Risk score interpretation
- Protocol comparisons
- Recommendations

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Risk Scoring | ✅ | 0-100 scale with levels |
| DeFiLlama Integration | ✅ | Real-time TVL data |
| Protocol Detection | ✅ | Auto-detect from query |
| Size Classification | ✅ | TVL-based categories |
| LLM Analysis | ✅ | Vertex AI assessment |
| Source Attribution | ✅ | LLM + DeFiLlama |

### Risk Categories (✅ Complete)

| Category | Status | Weight |
|----------|--------|--------|
| Volatility | ✅ | 30% |
| Liquidity | ✅ | 25% |
| Smart Contract | ✅ | 25% |
| Correlation | ✅ | 20% |

---

## 📊 Key Metrics

### Performance Targets

- **DeFiLlama API**: < 500ms
- **LLM Analysis**: < 1000ms
- **Total Response**: < 1.5s

### Risk Scale

| Score | Level | Action |
|-------|-------|--------|
| 0-20 | Very Low | Standard position |
| 21-40 | Low | Standard position |
| 41-60 | Moderate | Reduce 30-50% |
| 61-80 | High | Reduce 50-70% |
| 81-100 | Critical | Avoid or <5% |

---

## 🔗 Related Specifications

### Two-Layer Architecture

**Layer 1: RiskAnalyzerAgent** (Agent Squad)
- `src/app/infrastructure/adapters/agent_squad/agents/risk_analyzer_agent.py`
- LLM-based qualitative analysis
- DeFiLlama TVL integration
- Used via supervisor routing

**Layer 2: RiskAnalyzer** (Application Service)
- `src/app/application/hunter/risk_analyzer.py`
- ML-based quantitative analysis
- Historical price analysis
- Used by Hunter AI

### Related Agents

- **Hunter AI**: Market analysis and predictions
- **Portfolio**: Risk-adjusted recommendations
- **DeFi Yield**: Yield opportunities with risk

---

## 🚀 Risk Assessment Journey

### Protocol Risk Flow

```
1. User says: "What's the risk of Aave?"
   → Supervisor routes to risk_analyzer

2. RiskAnalyzerAgent detects "aave"
   → Set protocol_filter = "aave"

3. Fetch DeFiLlama data
   → TVL: $12.4B
   → Chain distribution: 7 chains
   → 7-day change: +2.5%

4. Classify protocol size
   → Very Large (>$1B) = Lower risk

5. LLM generates assessment
   → Risk score: 15/100
   → Risk level: Very Low

6. Build response with recommendations
   → Sources: LLM + DeFiLlama
```

### Token Risk Flow

```
1. User says: "What's the risk of ETH?"
   → Supervisor routes to risk_analyzer

2. RiskAnalyzer service activated
   → Fetch historical prices

3. Analyze risk factors:
   → Volatility: Std dev, drawdowns
   → Liquidity: Volume, consistency
   → Smart Contract: Audit status
   → Correlation: Beta with BTC

4. Calculate weighted score
   → Score = 0.30×vol + 0.25×liq + 0.25×sc + 0.20×corr

5. Generate recommendation
   → Based on overall level
```

---

## 🔑 Critical Rules

### Risk Score Calculation

```python
# Protocol risk (DeFiLlama-based)
if tvl > 1_000_000_000:  # > $1B
    size_risk = "very_large"  # Lower risk
elif tvl > 100_000_000:  # > $100M
    size_risk = "large"  # Moderate risk
elif tvl > 10_000_000:  # > $10M
    size_risk = "medium"  # Higher risk
else:
    size_risk = "small"  # Highest risk
```

### Risk Level Mapping

```python
def _score_to_level(score: float) -> str:
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "extreme"
```

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-29
**Review Frequency:** Monthly

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**For questions or clarifications, refer to the README.md in this directory.**
