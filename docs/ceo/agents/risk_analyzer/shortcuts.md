# Risk Analyzer Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, risk categories, and response formats for the **RISK_ANALYZER** agent.

---

## Query Patterns

### Protocol Risk Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Risk of {protocol} | "What's the risk of Aave?" | Protocol risk analysis |
| Is {protocol} safe | "Is Compound safe?" | Safety assessment |
| Analyze {protocol} | "Analyze risk for Morpho" | Detailed analysis |
| {protocol} TVL | "What's the TVL of Curve?" | TVL data |
| Compare {A} vs {B} | "Compare Aave vs Compound" | Risk comparison |

### Token Risk Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Risk of {token} | "What's the risk of ETH?" | Token risk analysis |
| Is {token} safe | "Is SOL safe to invest?" | Safety assessment |
| Analyze {token} | "Analyze risk for BTC" | Multi-factor analysis |
| Volatility of {token} | "How volatile is DOGE?" | Volatility focus |

### Combined Queries

| Pattern | Example | Agents |
|---------|---------|--------|
| Yield + Risk | "Best yield for USDC" | defi_yield + risk_analyzer |
| Arbitrage + Risk | "Find arbitrage opportunities" | hunter_ai + risk_analyzer |
| Portfolio + Risk | "Risk-adjusted recommendations" | portfolio + risk_analyzer |

---

## Supported Protocols

### Auto-Detected Protocols

| Protocol | Keywords |
|----------|----------|
| Aave | aave |
| Morpho | morpho |
| Compound | compound |
| Curve | curve |
| Uniswap | uniswap |

### Other Protocols

All protocols in DeFiLlama are supported (100+). The agent fetches TVL data for any mentioned protocol.

---

## Risk Score Scale

### Protocol Risk (TVL-Based)

| Score | Level | TVL Range | Description |
|-------|-------|-----------|-------------|
| 0-20 | Very Low | > $1B | Large, established |
| 21-40 | Low | > $100M | Well-established |
| 41-60 | Moderate | > $10M | Medium-sized |
| 61-80 | High | < $10M | Small or new |
| 81-100 | Critical | Minimal | Experimental |

### Token Risk (Multi-Factor)

| Score | Level | Recommendation |
|-------|-------|----------------|
| 0-25 | Low | Standard position sizing |
| 26-50 | Medium | Standard or slightly reduced |
| 51-75 | High | Reduce 50-70% |
| 76-100 | Extreme | Minimal (<5%) or avoid |

---

## Risk Categories

### 1. Volatility Risk (30%)

**Metrics:**
- Historical volatility (std dev of returns)
- Average daily range
- Maximum drawdown
- Sharp movements (>5% daily)

**Interpretation:**
- Low (0-25): Stable price action
- Medium (26-50): Moderate swings
- High (51-75): Significant volatility
- Extreme (76-100): Highly volatile

### 2. Liquidity Risk (25%)

**Metrics:**
- Average daily volume
- Volume consistency
- Bid-ask spread
- Slippage risk

**Interpretation:**
- Low (0-25): High volume, easy to trade
- Medium (26-50): Moderate volume
- High (51-75): Low volume, slippage risk
- Extreme (76-100): Very illiquid

### 3. Smart Contract Risk (25%)

**Metrics:**
- Audit status (complete, partial, none)
- Bug bounty program (active, limited, none)
- Code quality (high, medium, low)
- Centralization risk (low, medium, high)

**Major Tokens (BTC, ETH, etc.):**
- Complete audits
- Active bug bounty
- High code quality
- Low centralization

### 4. Correlation Risk (20%)

**Metrics:**
- Correlation with BTC
- Beta (sensitivity to market)
- Systemic risk exposure

**Interpretation:**
- High correlation (>0.7): High systemic risk
- Moderate (0.4-0.7): Moderate systemic risk
- Low (<0.4): Lower systemic risk

---

## API Response Examples

### Protocol Risk Assessment

```json
{
  "agent_message": {
    "content": "**Aave Protocol Risk Assessment**\n\n**PROTOCOL DATA FROM DEFILLAMA:**\n**AAVE Protocol:**\n- Total TVL: $12,450,000,000\n- Size: Very Large (Lower risk due to scale)\n- Chain Distribution: 7 chains\n  - Ethereum: $8,200,000,000\n  - Polygon: $1,800,000,000\n  - Arbitrum: $1,500,000,000\n\n**Risk Score: 15/100 (Very Low Risk)**\n\n**Risk Category Breakdown:**\n- Protocol Size: Low risk (Top 5 by TVL)\n- Smart Contract: Low risk (Multiple audits, active bug bounty)\n- Liquidity: Low risk (High trading volume)\n- Market: Moderate risk (High correlation with market)\n\n**Recommendation:**\nLow risk profile. Suitable for conservative portfolios.",
    "role": "assistant",
    "agent_type": "risk_analyzer"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 80},
      {"agent_type": "risk_analyzer", "duration_ms": 1200}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Risk analysis via Vertex AI",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "DeFiLlama",
        "url": "https://defillama.com/",
        "citation_text": "Protocol TVL and risk data from DeFiLlama",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Token Risk Assessment

```json
{
  "agent_message": {
    "content": "**SOL Token Risk Assessment**\n\n**Risk Score: 45/100 (Moderate Risk)**\n\n**Risk Factor Breakdown:**\n1. **Volatility Risk: 55/100 (High)**\n   - Historical volatility: 4.2% daily\n   - Max drawdown (30d): -18%\n   - Sharp movements: 8\n\n2. **Liquidity Risk: 20/100 (Low)**\n   - Avg daily volume: $2.1B\n   - Volume consistency: 0.85\n\n3. **Smart Contract Risk: 25/100 (Low)**\n   - Audit status: Complete\n   - Bug bounty: Active\n\n4. **Correlation Risk: 72/100 (High)**\n   - Correlation with BTC: 0.72\n   - Beta: 1.4\n   - Systemic risk: High\n\n**Recommendation:**\nModerate risk with high volatility. Use tighter stop-losses and reduce position size by 30-50%.",
    "role": "assistant",
    "agent_type": "risk_analyzer"
  }
}
```

### Risk Comparison

```json
{
  "agent_message": {
    "content": "**Protocol Risk Comparison**\n\n| Factor | Aave | Morpho |\n|--------|------|--------|\n| TVL | $12.4B | $1.8B |\n| Risk Score | 15/100 | 28/100 |\n| Risk Level | Very Low | Low |\n| Audits | Multiple | Multiple |\n| Bug Bounty | $1M+ | Active |\n| Age | 4+ years | 2+ years |\n\n**Analysis:**\n- Both protocols are well-established and low risk\n- Aave has larger TVL and longer track record\n- Morpho offers higher yields with slightly higher risk\n\n**Recommendation:**\nFor lower risk: Aave\nFor higher yield with acceptable risk: Morpho",
    "role": "assistant",
    "agent_type": "risk_analyzer"
  }
}
```

---

## Supervisor Routing Examples

### Authenticated User

```python
# Direct risk queries
"What's the risk of Aave?" → risk_analyzer

# Combined with yield
"best yield for USDC" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["defi_yield"]}
]

# Combined with arbitrage
"find arbitrage opportunities between ETH and Polygon" → [
    {"agent_type": "hunter_ai", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["hunter_ai"]}
]

# Combined with portfolio
"suggest low-risk DeFi yield opportunities" → [
    {"agent_type": "defi_yield", "depends_on": []},
    {"agent_type": "risk_analyzer", "depends_on": ["defi_yield"]}
]
```

### Guest User

```python
# Risk/TVL analysis
"Risk/TVL analysis" → risk_analyzer

# Protocol safety
"Is Aave safe?" → risk_analyzer
```

---

## Multi-Language Support

### English

```
Commands:
• "What's the risk of Aave?"
• "Is Compound safe?"
• "Analyze risk for Morpho"
• "Compare Aave vs Compound"
```

### Spanish

```
Commands:
• "¿Cuál es el riesgo de Aave?"
• "¿Es seguro Compound?"
• "Analiza el riesgo de Morpho"
```

### Portuguese

```
Commands:
• "Qual é o risco do Aave?"
• "O Compound é seguro?"
• "Analise o risco do Morpho"
```

---

## Risk Recommendations

### By Risk Level

| Level | Position Size | Stop-Loss | Monitoring |
|-------|--------------|-----------|------------|
| Very Low | 100% | Standard | Weekly |
| Low | 100% | Standard | Weekly |
| Moderate | 50-70% | Tighter | Daily |
| High | 30-50% | Very tight | Continuous |
| Extreme | <5% or avoid | Minimal | Continuous |

### By Factor

| Factor Issue | Mitigation |
|--------------|------------|
| High Volatility | Tighter stop-losses |
| Low Liquidity | Smaller positions, limit orders |
| SC Concerns | Thorough research, diversify |
| High Correlation | Diversify across uncorrelated assets |

---

## Common Questions

### Q: How are risk scores calculated?
**A:** Risk scores (0-100) are calculated using multiple factors:
- Protocol risk: Based on TVL size from DeFiLlama
- Token risk: Weighted average of volatility (30%), liquidity (25%), smart contract (25%), and correlation (20%)

### Q: What does TVL mean?
**A:** TVL (Total Value Locked) is the total value of assets deposited in a protocol. Higher TVL generally indicates lower risk due to scale and proven track record.

### Q: Which protocols are safest?
**A:** Protocols with very large TVL (>$1B) like Aave, Uniswap, and Compound typically have the lowest risk scores (0-20).

### Q: How often is data updated?
**A:** TVL data is fetched in real-time from DeFiLlama API when you ask about a protocol.

---

## Error Handling

### Common Errors

| Error | User Message |
|-------|--------------|
| Protocol not found | "Protocol not found in DeFiLlama. Please check the name." |
| API unavailable | "Unable to fetch risk data. Using cached analysis." |
| Insufficient data | "Insufficient historical data for complete analysis." |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Risk Analyzer Agent Shortcuts**
