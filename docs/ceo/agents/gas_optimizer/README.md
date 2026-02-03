# Gas Optimizer Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **GAS_OPTIMIZER** agent provides real-time gas price analysis, optimal transaction timing recommendations, and Layer 2 migration suggestions to help users minimize transaction costs across multiple blockchain networks.

### Key Differentiators

- **Real-Time Data**: Live gas prices from Web3Client (Alchemy/Infura)
- **Multi-Chain Support**: Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, BSC
- **Intelligent Timing**: Recommendations based on current gas levels
- **Layer 2 Guidance**: Cost-saving alternatives when gas is high
- **USD Estimates**: Human-readable cost projections

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and gas analysis topics |

---

## Quick Start

### For Users

**Example Commands:**
```
• "What are gas prices on Ethereum?"
• "Gas prices on Polygon"
• "When is the best time to send a transaction?"
• "Compare gas costs on Ethereum vs Arbitrum"
• "How can I reduce gas fees?"
• "Should I use Layer 2 for this transaction?"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for query patterns

---

## Key Features

### 1. Real-Time Gas Analysis

| Chain | Real-Time | Typical Gas | Typical Cost | Savings |
|-------|-----------|-------------|--------------|---------|
| **Ethereum** | ✅ Yes | 20-200 gwei | $1-50 | Baseline |
| **Polygon** | Guidance | 30-100 gwei | $0.01-0.05 | ~95% |
| **Arbitrum** | Guidance | 0.1-0.5 gwei | $0.10-0.50 | ~90% |
| **Optimism** | Guidance | 0.1-1 gwei | $0.10-1.00 | ~85% |
| **Base** | Guidance | 0.1-0.5 gwei | $0.10-0.50 | ~90% |
| **Avalanche** | Guidance | 25-30 nAVAX | $0.01-0.05 | Very cheap |
| **BSC** | Guidance | 3-5 gwei | $0.10-0.50 | Much cheaper |

### 2. Gas Price Tiers

| Tier | Description | Use Case |
|------|-------------|----------|
| **Slow** | Base fee only | Non-urgent transactions |
| **Standard** | Base fee + priority fee | Most transactions |
| **Fast** | Max fee | Time-sensitive transactions |

### 3. Timing Recommendations

| Gas Level | Threshold | Recommendation |
|-----------|-----------|----------------|
| **Low** | < 30 gwei | Execute now |
| **Moderate** | 30-100 gwei | Proceed with standard |
| **High** | > 100 gwei | Wait or use Layer 2 |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → GasOptimizerAgent
    ↓ (External Services)
External Systems
    - Web3Client (Alchemy/Infura RPC)
    - Vertex AI (LLM analysis)
```

### Gas Analysis Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  GAS OPTIMIZER FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "What are gas prices on Ethereum?"                   │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: gas query      │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  GasOptimizerAgent      │                               │
│  │                         │                               │
│  │  1. Detect chain        │ → Ethereum                    │
│  │  2. Fetch gas prices    │ → Web3Client                  │
│  │  3. Calculate tiers     │ → Slow/Standard/Fast          │
│  │  4. USD estimates       │ → $X for transfer             │
│  │  5. Timing advice       │ → Low/Moderate/High           │
│  │  6. L2 suggestions      │ → If gas high                 │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  Response with prices   │                               │
│  │  + recommendations      │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Classification

```python
# From intent_classifier.py

AGENT_MAPPING = {
    "optimize_gas": AgentType.GAS_OPTIMIZER,
    "gas_estimation": AgentType.GAS_OPTIMIZER,
}
```

### Routing Examples

```python
# Gas price queries
"what are gas prices on Ethereum?" → gas_optimizer
"gas prices on Polygon" → gas_optimizer
"when is the best time to execute Ethereum transactions" → gas_optimizer

# Combined queries (parallel execution)
"what is defi? also check gas prices" → knowledge + gas_optimizer (parallel)
"poem about gas + current price" → chat + gas_optimizer (sequential)
```

---

## Example Conversations

### Current Gas Prices

```
User: "What are gas prices on Ethereum?"

Agent:
**REAL-TIME GAS PRICES - ETHEREUM:**
- Slow: 25.3 gwei ($0.85 for standard transfer)
- Standard: 28.5 gwei ($0.95 for standard transfer)
- Fast: 35.2 gwei ($1.18 for standard transfer)
- Base Fee: 25.3 gwei
- Priority Fee: 3.2 gwei

💡 **Recommendation**: Gas prices are LOW - good time to send transactions

**Tips for Lower Fees:**
1. Wait for off-peak hours (weekends, late night UTC)
2. Consider Layer 2 for frequent transactions
3. Batch multiple operations when possible
```

### Layer 2 Comparison

```
User: "Compare gas costs on Ethereum vs Arbitrum"

Agent:
## Gas Cost Comparison: Ethereum vs Arbitrum

### Ethereum (L1)
- Current: ~30 gwei (~$1.00 per transfer)
- DeFi operations: $5-50+
- Peak times: Can exceed 100 gwei

### Arbitrum (L2)
- Current: ~0.1-0.5 gwei (~$0.20 per transfer)
- DeFi operations: $0.50-2.00
- Consistent low fees

### Savings with Arbitrum
- **~90% cheaper than Ethereum**
- Same security (inherits Ethereum's security)
- Most major DeFi protocols available
- Easy bridging from Ethereum

### Recommendation
For frequent transactions or smaller amounts, Arbitrum offers significant savings.
Bridge your assets to Arbitrum to reduce costs by 90%.
```

### Optimal Timing

```
User: "When should I send this transaction?"

Agent:
## Optimal Transaction Timing

**Current Status**: Gas prices are MODERATE (45 gwei)

### Best Times to Transact
1. **Weekends**: 20-40% lower gas prices
2. **Late night UTC** (00:00-06:00): Lowest activity
3. **Avoid**: Monday-Friday 14:00-18:00 UTC (peak trading)

### Current Recommendation
Gas prices are reasonable. If transaction is:
- **Urgent**: Execute now at Standard tier (45 gwei)
- **Can wait**: Wait for <30 gwei (typically weekends)
- **Non-critical**: Use Slow tier or Layer 2

### Layer 2 Alternative
Consider Arbitrum or Base for 90% cheaper transactions with similar speed.
```

---

## Configuration

### Default Parameters

```python
# From gas_optimizer_agent.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.2           # Factual
max_tokens = 1000
```

### Environment Variables

```bash
# Required for real-time Ethereum gas prices
ALCHEMY_API_KEY=your_alchemy_key
# or
INFURA_API_KEY=your_infura_key

# Also accepted (from .secrets.toml export)
RPC_ALCHEMY_API_KEY=your_key
RPC_INFURA_API_KEY=your_key
```

### Response Structure

```python
AgentResponse(
    content="Gas price analysis with recommendations...",
    agent_type=AgentType.GAS_OPTIMIZER,
    tools_used=["llm_gateway", "web3_client"],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="blockchain", source_name="Ethereum", 
                   citation_text="Real-time gas prices from Ethereum network", ...),
    ],
    metadata={
        "tokens_used": 400,
        "latency_ms": 800,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
    },
)
```

---

## Use Cases

### Primary Use Cases

1. **Check gas prices** before sending transactions
2. **Find optimal timing** for large transactions
3. **Compare costs** before choosing a chain
4. **Get recommendations** for Layer 2 migration
5. **Learn gas optimization** strategies
6. **Estimate transaction costs** in USD

### Combined Queries

| Query | Agents Used | Execution |
|-------|-------------|-----------|
| "what is DeFi? also check gas prices" | knowledge + gas_optimizer | Parallel |
| "poem about gas + current price" | gas_optimizer → chat | Sequential |
| "best yields and gas prices" | defi_yield + gas_optimizer | Parallel |

---

## Testing Checklist

### Unit Tests
- [ ] Chain detection from message
- [ ] Gas price fetching
- [ ] Tier calculation (Slow/Standard/Fast)
- [ ] USD cost estimation
- [ ] Recommendation logic

### Integration Tests
- [ ] Web3Client integration
- [ ] LLM response formatting
- [ ] Source attribution

### E2E Tests
- [ ] Complete gas analysis flow
- [ ] Multi-chain comparison
- [ ] Timing recommendations

---

## Related Documentation

- **Hunter AI**: `/docs/ceo/agents/hunter/` (market prices)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (transaction execution)
- **Execution Agent**: `/docs/ceo/agents/execution/` (transaction handling)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added multi-chain support |
| 1.0 | 2026-01-29 | Added Web3Client integration |
| 1.0 | 2026-01-29 | Added Layer 2 recommendations |

---

**End of Gas Optimizer Agent Specification**
