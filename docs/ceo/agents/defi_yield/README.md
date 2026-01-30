# DeFi Yield Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **DEFI_YIELD** agent specializes in yield farming and APY optimization. It provides real-time yield opportunities from DeFiLlama, compares protocols, analyzes impermanent loss risks, and recommends risk-adjusted strategies.

### Key Differentiators

- **Real-Time APY Data**: Fetches live yield pools from DeFiLlama API
- **Protocol Comparison**: Compare Aave, Morpho, Compound, Curve rates
- **Risk-Adjusted Ranking**: APY with risk scores (0-100)
- **Impermanent Loss Analysis**: IL risk assessment for LP positions
- **Specific Numbers**: Provides concrete APY percentages, not generic advice

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and yield categories |

---

## Quick Start

### For Users

**Example Commands:**
```
• "Best yield for USDC"
• "Highest APY opportunities"
• "Compare Aave vs Morpho rates"
• "Low-risk yield farms"
• "What APY can I get on ETH?"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for query patterns

---

## Key Features

### 1. Yield Discovery

| Capability | Description | Data Source |
|------------|-------------|-------------|
| **Top Yields** | Highest APY pools sorted by rate | DeFiLlama |
| **Protocol Filter** | Filter by Aave, Morpho, Compound, Curve | DeFiLlama |
| **Chain Filter** | Filter by Ethereum, Polygon, Arbitrum | DeFiLlama |
| **Risk Score** | 0-100 risk assessment per pool | Calculated |

### 2. APY Breakdown

| Component | Description |
|-----------|-------------|
| **Base APY** | Lending/LP interest rate |
| **Reward APY** | Token incentives (governance tokens) |
| **Total APY** | Base + Reward combined |

### 3. Risk Indicators

| Factor | Weight | Description |
|--------|--------|-------------|
| **APY Level** | High | Very high APY (>1000%) = higher risk |
| **TVL** | Medium | Low TVL (<$100k) = higher risk |
| **IL Risk** | Medium | Impermanent loss for LP positions |
| **Protocol Age** | Low | Newer protocols = higher risk |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → DefiYieldAgent
    ↓ (External Services)
External Systems
    - DeFiLlama (yield data)
    - Vertex AI (LLM analysis)
```

### Yield Discovery Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DEFI YIELD AGENT FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Best yield for USDC"                                │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: yield query    │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    DefiYieldAgent       │                               │
│  │                         │                               │
│  │  1. Detect protocol     │ → None (general query)        │
│  │  2. Fetch DeFiLlama     │ → Top 10 yield pools          │
│  │  3. Sort by APY         │ → Highest first               │
│  │  4. Calculate risk      │ → 0-100 score                 │
│  │  5. Format table        │ → Markdown table              │
│  │  6. LLM analysis        │ → Recommendations             │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  Response with table    │                               │
│  │  + recommendations      │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Yield vs Swap Rate Distinction

```python
# CRITICAL DISTINCTION:

# Yield queries → defi_yield
"yield", "APY", "yield farms", "lending rates" → defi_yield

# Swap queries → hunter_ai (NOT defi_yield!)
"swap rate", "exchange rate", "convert X to Y" → hunter_ai
```

### Routing Examples

```python
# Direct yield queries
"best yield for USDC" → defi_yield
"highest APY" → defi_yield
"yield farming options" → defi_yield

# Combined with risk
"best yield for USDC" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["defi_yield"]}
]

# Combined with portfolio
"best yields and my balance" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "portfolio", "depends_on": []}
]
```

---

## Example Conversations

### Best Yield Query

```
User: "Best yield for USDC"

Agent:
**REAL-TIME APY DATA FROM DEFILLAMA:**

| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |
|----------|------|-------|---------|-----|-------------------|----------------------|
| Morpho | USDC | Ethereum | 8.50% | $245.3M | 35 | No |
| Aave V3 | USDC | Ethereum | 5.20% | $1.2B | 20 | No |
| Compound V3 | USDC | Ethereum | 4.80% | $890M | 25 | No |
| Curve | 3pool | Ethereum | 3.20% + 2.50% | $580M | 40 | Yes |
| Convex | crvUSD | Ethereum | 12.30% | $120M | 55 | Yes |

**Recommendations:**

For **low-risk, stable yield**:
- **Morpho USDC (8.50% APY)** - Best risk-adjusted return
- **Aave V3 USDC (5.20% APY)** - Largest TVL, battle-tested

For **higher yield with more risk**:
- **Convex crvUSD (12.30% APY)** - Higher risk, IL exposure
- **Curve 3pool (5.70% total APY)** - Moderate IL risk

**My Recommendation:**
Start with Morpho USDC for the best balance of yield and safety.
```

### Protocol Comparison

```
User: "Compare Aave vs Morpho rates"

Agent:
**Aave vs Morpho Comparison (Real-Time Data)**

| Asset | Aave V3 APY | Morpho APY | Difference |
|-------|-------------|------------|------------|
| USDC | 5.20% | 8.50% | +3.30% (Morpho) |
| ETH | 2.80% | 4.20% | +1.40% (Morpho) |
| DAI | 4.50% | 6.80% | +2.30% (Morpho) |

**Analysis:**
- **Morpho** consistently offers higher rates (1-3% above Aave)
- **Aave** has larger TVL and longer track record
- **Morpho** optimizes peer-to-peer matching for better rates

**Recommendation:**
- For maximum yield: Morpho
- For maximum safety: Aave
- For balanced approach: Split between both
```

### Low-Risk Yields

```
User: "Low-risk yield opportunities"

Agent:
**Low-Risk Yield Opportunities (Risk Score < 40)**

| Protocol | Pool | Chain | APY | TVL | Risk |
|----------|------|-------|-----|-----|------|
| Aave V3 | USDC | Ethereum | 5.20% | $1.2B | 20 |
| Aave V3 | USDT | Ethereum | 4.80% | $850M | 22 |
| Compound V3 | USDC | Base | 4.50% | $450M | 28 |
| Morpho | USDC | Ethereum | 8.50% | $245M | 35 |

**Why These Are Low-Risk:**
✅ Large TVL (>$200M) - deep liquidity
✅ No impermanent loss - single asset lending
✅ Audited protocols - multiple security audits
✅ Long track record - 2+ years operational

**Recommendation:**
Start with Aave V3 USDC for the lowest risk, or Morpho USDC for higher yield with slightly more risk.
```

---

## Data Sources

### DeFiLlama Integration

| Data Type | Endpoint | Update Frequency |
|-----------|----------|------------------|
| Yield Pools | `/pools` | Real-time |
| Protocol Yields | `/pools?protocol={name}` | Real-time |
| Chain Yields | `/pools?chain={name}` | Real-time |

### Risk Score Calculation

```python
# Base risk score
risk_score = 50

# APY-based adjustments
if apy > 10000:  # > 10,000% APY
    risk_score = 95  # Likely unsustainable
elif apy > 1000:  # > 1,000% APY
    risk_score = 85  # Very high risk
elif apy > 100:  # > 100% APY
    risk_score = 70  # High risk

# TVL-based adjustments
if tvl_usd < 100_000:  # Low TVL
    risk_score = min(100, risk_score + 10)
```

---

## Configuration

### Default Parameters

```python
# From defi_yield_agent.py

model = "gemini-2.0-flash"
temperature = 0.3  # Balanced
max_tokens = 1500
```

### Response Format

```python
AgentResponse(
    content="APY table + recommendations...",
    agent_type=AgentType.DEFI_YIELD,
    tools_used=["llm_gateway", "defillama_api"],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="api", source_name="DeFiLlama", ...),
    ],
    metadata={
        "tokens_used": 500,
        "latency_ms": 1100,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] Protocol detection (Aave, Morpho, Compound, Curve)
- [ ] Risk score calculation
- [ ] APY formatting (base + reward)
- [ ] TVL formatting (K, M, B)

### Integration Tests
- [ ] DeFiLlama API integration
- [ ] Yield pool fetching
- [ ] Source attribution

### E2E Tests
- [ ] Complete yield query flow
- [ ] Protocol comparison
- [ ] Combined queries (yield + risk)

---

## Related Documentation

- **Risk Analyzer**: `/docs/ceo/agents/risk_analyzer/` (risk assessment)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (deposit execution)
- **Money Market**: `/docs/ceo/agents/money_market/` (rate comparison)
- **Portfolio**: `/docs/ceo/agents/portfolio/` (allocation optimization)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added DeFiLlama integration |
| 1.0 | 2026-01-29 | Added risk score calculation |

---

**End of DeFi Yield Agent Specification**
