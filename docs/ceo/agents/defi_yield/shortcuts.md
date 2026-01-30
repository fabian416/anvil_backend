# DeFi Yield Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, yield categories, and response formats for the **DEFI_YIELD** agent.

---

## Query Patterns

### Yield Discovery Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Best yield for {token} | "Best yield for USDC" | Find top APY |
| Highest APY | "Highest APY opportunities" | Top yields |
| Best yield farms | "Best yield farms" | All opportunities |
| Yield on {protocol} | "Yield on Aave" | Protocol-specific |
| {token} APY | "What's the ETH APY?" | Token-specific |

### Protocol Comparison Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Compare {A} vs {B} | "Compare Aave vs Morpho" | Rate comparison |
| {protocol} rates | "Morpho rates" | Protocol rates |
| Lending rates | "Best lending rates" | All lending APY |

### Risk-Filtered Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Low-risk yields | "Low-risk yield opportunities" | Risk < 40 |
| Safe yield farms | "Safe yield farms" | Low risk only |
| Stable yields | "Stable yield options" | Low volatility |

---

## CRITICAL: Yield vs Swap Distinction

### Common Mistake to Avoid

```python
# ❌ WRONG ROUTING
"best swap rate for ETH to USDC" → defi_yield

# ✅ CORRECT ROUTING
"best swap rate for ETH to USDC" → hunter_ai
```

### Classification Rules

| Query Type | Keywords | Agent |
|------------|----------|-------|
| **Yield** | yield, APY, lending rates, farms | defi_yield |
| **Swap** | swap rate, exchange rate, convert | hunter_ai |

### Examples

```python
# Yield queries → defi_yield
"best yield for USDC" → defi_yield ✅
"highest APY" → defi_yield ✅
"yield farming options" → defi_yield ✅
"lending rates" → defi_yield ✅

# Swap queries → hunter_ai
"best swap rate for ETH to USDC" → hunter_ai ✅
"convert ETH to USDC" → hunter_ai ✅
"exchange rate ETH USDC" → hunter_ai ✅
```

---

## Supported Protocols

### Auto-Detected Protocols

| Protocol | Keywords | Yield Type |
|----------|----------|------------|
| Aave | "aave" | Lending |
| Morpho | "morpho" | Lending |
| Compound | "compound" | Lending |
| Curve | "curve" | LP + Lending |
| Convex | "convex" | Yield Aggregator |

### General Queries

For queries without specific protocol mentions, the agent fetches top yields across all protocols from DeFiLlama.

---

## Risk Score Categories

### Score Interpretation

| Score | Level | Description | Recommendation |
|-------|-------|-------------|----------------|
| 0-30 | Low | Safe, established | Full position |
| 31-50 | Moderate | Acceptable risk | Standard position |
| 51-70 | High | Elevated risk | Reduce position |
| 71-90 | Very High | Significant risk | Small position only |
| 91-100 | Extreme | Likely unsustainable | Avoid |

### Risk Factors

| Factor | Impact | Threshold |
|--------|--------|-----------|
| Very High APY | +45 | > 10,000% |
| High APY | +35 | > 1,000% |
| Elevated APY | +20 | > 100% |
| Low TVL | +10 | < $100,000 |

---

## Yield Table Format

### Standard Table

```markdown
| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |
|----------|------|-------|---------|-----|-------------------|----------------------|
| Morpho | USDC | Ethereum | 8.50% | $245.3M | 35 | No |
| Aave V3 | USDC | Ethereum | 5.20% | $1.2B | 20 | No |
| Curve | 3pool | Ethereum | 3.20% + 2.50% | $580M | 40 | Yes |
```

### APY Breakdown

- **Base APY**: Interest from lending/LP
- **Reward APY**: Token incentives
- **Total APY**: Base + Reward

### TVL Formatting

| Value | Format |
|-------|--------|
| >= $1B | "$1.50B" |
| >= $1M | "$250.00M" |
| >= $1K | "$50.00K" |
| < $1K | "$500" |

---

## API Response Examples

### Best Yield Query

```json
{
  "agent_message": {
    "content": "**REAL-TIME APY DATA FROM DEFILLAMA:**\n\n| Protocol | Pool | Chain | APY (%) | TVL | Risk Score (0-100) | Impermanent Loss Risk |\n|----------|------|-------|---------|-----|-------------------|----------------------|\n| Morpho | USDC | Ethereum | 8.50% | $245.3M | 35 | No |\n| Aave V3 | USDC | Ethereum | 5.20% | $1.2B | 20 | No |\n| Compound V3 | USDC | Ethereum | 4.80% | $890M | 25 | No |\n\n**Recommendations:**\n\nFor low-risk, stable yield:\n- **Morpho USDC (8.50% APY)** - Best risk-adjusted return\n- **Aave V3 USDC (5.20% APY)** - Largest TVL, battle-tested",
    "role": "assistant",
    "agent_type": "defi_yield"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 80},
      {"agent_type": "defi_yield", "duration_ms": 1100}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Yield analysis via Vertex AI",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "DeFiLlama",
        "url": "https://defillama.com/yields",
        "endpoint": "/pools",
        "citation_text": "Real-time APY data from DeFiLlama",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Protocol Comparison

```json
{
  "agent_message": {
    "content": "**Aave vs Morpho Comparison (Real-Time Data)**\n\n| Asset | Aave V3 APY | Morpho APY | Difference |\n|-------|-------------|------------|------------|\n| USDC | 5.20% | 8.50% | +3.30% (Morpho) |\n| ETH | 2.80% | 4.20% | +1.40% (Morpho) |\n| DAI | 4.50% | 6.80% | +2.30% (Morpho) |\n\n**Analysis:**\n- Morpho consistently offers higher rates\n- Aave has larger TVL and longer track record\n\n**Recommendation:**\n- For maximum yield: Morpho\n- For maximum safety: Aave",
    "role": "assistant",
    "agent_type": "defi_yield"
  }
}
```

### Low-Risk Yields

```json
{
  "agent_message": {
    "content": "**Low-Risk Yield Opportunities (Risk Score < 40)**\n\n| Protocol | Pool | Chain | APY | TVL | Risk |\n|----------|------|-------|-----|-----|------|\n| Aave V3 | USDC | Ethereum | 5.20% | $1.2B | 20 |\n| Aave V3 | USDT | Ethereum | 4.80% | $850M | 22 |\n| Compound V3 | USDC | Base | 4.50% | $450M | 28 |\n| Morpho | USDC | Ethereum | 8.50% | $245M | 35 |\n\n**Why These Are Low-Risk:**\n✅ Large TVL (>$200M)\n✅ No impermanent loss\n✅ Audited protocols\n✅ Long track record",
    "role": "assistant",
    "agent_type": "defi_yield"
  }
}
```

---

## Supervisor Routing Examples

### Authenticated User

```python
# Direct yield queries
"best yield for USDC" → defi_yield

# Combined with risk
"best yield for USDC" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["defi_yield"]}
]

# Combined with portfolio
"my portfolio and best yields" → [
    {"agent_type": "portfolio", "depends_on": []},
    {"agent_type": "defi_yield", "depends_on": []}
]

# Allocation optimization
"allocation optimization" → [
    {"agent_type": "portfolio", "depends_on": []},
    {"agent_type": "defi_yield", "depends_on": []}
]
```

### Guest User

```python
# Yield queries
"best yield farms" → defi_yield
"highest APY" → defi_yield
```

---

## Multi-Language Support

### English

```
Commands:
• "Best yield for USDC"
• "Highest APY opportunities"
• "Compare Aave vs Morpho"
• "Low-risk yield farms"
```

### Spanish

```
Commands:
• "Mejor rendimiento para USDC"
• "Oportunidades de mayor APY"
• "Comparar Aave vs Morpho"
```

### Portuguese

```
Commands:
• "Melhor rendimento para USDC"
• "Oportunidades de maior APY"
• "Comparar Aave vs Morpho"
```

---

## Impermanent Loss Risk

### IL Categories

| Risk Level | Description | Pool Type |
|------------|-------------|-----------|
| **No** | No IL risk | Single-asset lending |
| **Low** | Minimal IL | Stablecoin pairs |
| **Medium** | Moderate IL | Major token pairs |
| **High** | Significant IL | Volatile token pairs |
| **Yes** | Has IL risk | General LP pools |

### IL-Free Opportunities

- Single-asset lending (Aave, Compound, Morpho)
- Stablecoin-only pools (3pool, Curve stables)

---

## Common Questions

### Q: What's the difference between yield and swap rates?
**A:** Yield is interest earned on deposits (APY). Swap rate is the exchange price between tokens.

### Q: How are risk scores calculated?
**A:** Based on APY level (very high APY = high risk) and TVL (low TVL = higher risk).

### Q: What's impermanent loss?
**A:** IL occurs in liquidity pools when token prices change. Single-asset lending has no IL.

### Q: Which protocols are safest?
**A:** Aave, Compound, and Morpho for single-asset lending (no IL, large TVL, audited).

---

## Error Handling

### Common Errors

| Error | User Message |
|-------|--------------|
| API unavailable | "Unable to fetch yield data. Using cached rates." |
| No yields found | "No yield opportunities found for this criteria." |
| Protocol not found | "Protocol not found. Try Aave, Morpho, Compound, or Curve." |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of DeFi Yield Agent Shortcuts**
