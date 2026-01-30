# Risk Analyzer Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **RISK_ANALYZER** agent provides comprehensive risk assessment and scoring for DeFi protocols and crypto tokens. It analyzes protocol TVL, smart contract risks, market volatility, and provides quantitative risk scores (0-100) with actionable recommendations.

### Key Differentiators

- **Real-Time TVL Data**: Fetches protocol data from DeFiLlama API
- **Quantitative Scoring**: 0-100 risk scale with clear risk levels
- **Multi-Factor Analysis**: Volatility, liquidity, smart contract, correlation
- **Protocol Comparison**: Compare risk across multiple protocols
- **Data-Driven**: Combines real data with LLM analysis

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and risk categories |

---

## Quick Start

### For Users

**Example Commands:**
```
• "What's the risk of Aave?"
• "Analyze risk for Morpho"
• "Is Compound safe?"
• "Compare risk of Aave vs Compound"
• "What's the TVL of Curve?"
• "Protocol risk analysis for Uniswap"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for query patterns

---

## Key Features

### 1. Risk Scoring (0-100 Scale)

| Score Range | Level | Description |
|-------------|-------|-------------|
| 0-20 | Very Low | Large, established protocols (>$1B TVL) |
| 21-40 | Low | Well-established protocols (>$100M TVL) |
| 41-60 | Moderate | Medium-sized protocols (>$10M TVL) |
| 61-80 | High | Small or new protocols (<$10M TVL) |
| 81-100 | Critical | Experimental or unaudited protocols |

### 2. Risk Categories

| Category | Weight | Description |
|----------|--------|-------------|
| **Volatility** | 30% | Price stability and drawdowns |
| **Liquidity** | 25% | Trading volume and consistency |
| **Smart Contract** | 25% | Audit status, code quality |
| **Correlation** | 20% | Systemic risk with BTC |

### 3. Protocol Size Classification

| Size | TVL Threshold | Risk Indicator |
|------|---------------|----------------|
| Very Large | > $1B | Lower risk |
| Large | > $100M | Moderate risk |
| Medium | > $10M | Higher risk |
| Small | < $10M | Highest risk |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → RiskAnalyzerAgent
    ↓ (External Services)
External Systems
    - DeFiLlama (TVL data)
    - Vertex AI (LLM analysis)
```

### Two-Layer Risk System

**Layer 1: RiskAnalyzerAgent (Agent Squad)**
- Uses LLM for risk assessment
- Fetches DeFiLlama TVL data
- Provides qualitative analysis
- Used via supervisor routing

**Layer 2: RiskAnalyzer (Application Service)**
- ML-based quantitative analysis
- Volatility, liquidity, correlation
- Used for Hunter AI predictions
- Historical price analysis

---

## Supervisor Routing

### Authenticated User

```python
# From authenticated_supervisor.py

# Direct risk queries
"Protocol risk → risk_analyzer"

# Combined queries with yield
"best yield for USDC" → defi_yield + risk_analyzer
"suggest low-risk DeFi yield" → defi_yield + risk_analyzer

# Combined queries with market analysis
"find arbitrage opportunities" → hunter_ai + risk_analyzer
"risk-adjusted recommendations" → portfolio + risk_analyzer
```

### Guest User

```python
# From guest_supervisor.py

# Risk/TVL analysis
"Risk/TVL analysis → risk_analyzer"
```

---

## Example Conversations

### Protocol Risk Query

```
User: "What's the risk of Aave?"

Agent:
**Aave Protocol Risk Assessment**

**PROTOCOL DATA FROM DEFILLAMA:**
**AAVE Protocol:**
- Total TVL: $12,450,000,000
- Size: Very Large (Lower risk due to scale)
- Chain Distribution: 7 chains
  - Ethereum: $8,200,000,000
  - Polygon: $1,800,000,000
  - Arbitrum: $1,500,000,000

**Risk Score: 15/100 (Very Low Risk)**

**Risk Category Breakdown:**
- Protocol Size: Low risk (Top 5 by TVL)
- Smart Contract: Low risk (Multiple audits, active bug bounty)
- Liquidity: Low risk (High trading volume)
- Market: Moderate risk (High correlation with market)

**Key Risk Factors:**
✅ Established protocol with 4+ years history
✅ Multiple security audits by top firms
✅ Active bug bounty program ($1M+)
✅ Multi-chain presence reduces single-chain risk

**Recommendation:**
Low risk profile. Suitable for conservative portfolios with standard position sizing.
```

### Risk Comparison

```
User: "Compare risk of Aave vs Morpho"

Agent:
**Protocol Risk Comparison**

| Factor | Aave | Morpho |
|--------|------|--------|
| TVL | $12.4B | $1.8B |
| Risk Score | 15/100 | 28/100 |
| Risk Level | Very Low | Low |
| Audits | Multiple | Multiple |
| Bug Bounty | $1M+ | Active |
| Age | 4+ years | 2+ years |

**Analysis:**
- Both protocols are well-established and low risk
- Aave has larger TVL and longer track record
- Morpho offers higher yields with slightly higher risk
- Both suitable for conservative portfolios

**Recommendation:**
For lower risk: Aave
For higher yield with acceptable risk: Morpho
```

### Token Risk Analysis

```
User: "What's the risk of investing in SOL?"

Agent:
**SOL Token Risk Assessment**

**Risk Score: 45/100 (Moderate Risk)**

**Risk Factor Breakdown:**
1. **Volatility Risk: 55/100 (High)**
   - Historical volatility: 4.2% daily
   - Max drawdown (30d): -18%
   - Sharp movements: 8 (in 30 days)

2. **Liquidity Risk: 20/100 (Low)**
   - Avg daily volume: $2.1B
   - Volume consistency: 0.85
   - Bid-ask spread: ~0.1%

3. **Smart Contract Risk: 25/100 (Low)**
   - Audit status: Complete
   - Bug bounty: Active
   - Code quality: High

4. **Correlation Risk: 72/100 (High)**
   - Correlation with BTC: 0.72
   - Beta: 1.4
   - Systemic risk: High

**Recommendation:**
Moderate risk profile with high volatility. Use tighter stop-losses and reduce position size by 30-50%.
```

---

## Data Sources

### DeFiLlama Integration

| Data Type | Endpoint | Update Frequency |
|-----------|----------|------------------|
| Protocol TVL | `/protocol/{name}` | Real-time |
| All Protocols | `/protocols` | Real-time |
| Chain TVLs | `/chains` | Real-time |
| 7-day Change | `/protocol/{name}` | Daily |

### LLM Analysis

| Model | Provider | Temperature |
|-------|----------|-------------|
| gemini-2.0-flash | Vertex AI | 0.2 |
| Fallback | DeepInfra | 0.2 |

---

## Configuration

### Default Parameters

```python
# From risk_analyzer_agent.py

model = "gemini-2.0-flash"
temperature = 0.2  # Low for precision
max_tokens = 1500
```

### Risk Thresholds

```python
# From RiskConfig (application layer)

volatility_window = 30  # days
high_volatility_threshold = 0.05  # 5% daily
min_daily_volume_usd = 1_000_000  # $1M
correlation_window = 90  # days
```

---

## Response Structure

### AgentResponse

```python
AgentResponse(
    content="Risk assessment with score and recommendations...",
    agent_type=AgentType.RISK_ANALYZER,
    tools_used=["llm_gateway", "defillama_api"],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="api", source_name="DeFiLlama", ...),
    ],
    metadata={
        "tokens_used": 450,
        "latency_ms": 1200,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] Risk score calculation (0-100)
- [ ] Protocol size classification
- [ ] DeFiLlama data parsing
- [ ] Risk level mapping

### Integration Tests
- [ ] DeFiLlama API integration
- [ ] LLM response handling
- [ ] Source attribution

### E2E Tests
- [ ] Complete risk assessment flow
- [ ] Multi-protocol comparison
- [ ] Combined queries (yield + risk)

---

## Related Documentation

- **Hunter AI**: `/docs/ceo/agents/hunter/` (market analysis)
- **Portfolio**: `/docs/ceo/agents/portfolio/` (portfolio optimization)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (deposit risks)
- **Money Market**: `/docs/ceo/agents/money_market/` (rate comparison)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added DeFiLlama integration |
| 1.0 | 2026-01-29 | Added ML-based risk analysis |

---

**End of Risk Analyzer Agent Specification**
