# Gas Optimizer Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, chain-specific analysis, and response formats for the **GAS_OPTIMIZER** agent.

---

## Query Patterns

### Gas Price Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Gas prices on {chain} | "Gas prices on Ethereum" | Real-time gas analysis |
| What are gas prices | "What are gas prices?" | Default Ethereum |
| Current gas | "Current gas on Polygon" | Chain-specific |
| Gas fees | "Gas fees on Arbitrum" | L2 analysis |

### Comparison Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Compare {A} vs {B} gas | "Compare Ethereum vs Arbitrum gas" | Side-by-side |
| {chain} vs {chain} | "Polygon vs Optimism" | Cost comparison |
| Cheapest chain | "Which chain is cheapest?" | All chains |

### Timing Queries

| Pattern | Example | Action |
|---------|---------|--------|
| When to send | "When should I send this transaction?" | Timing advice |
| Best time | "Best time to execute transactions" | Optimal timing |
| Should I wait | "Should I wait for lower gas?" | Recommendation |

### Optimization Queries

| Pattern | Example | Action |
|---------|---------|--------|
| How to reduce | "How can I reduce gas costs?" | Strategies |
| Optimize gas | "Optimize gas for my transaction" | Tips |
| Layer 2 | "Should I use Layer 2?" | L2 recommendation |

---

## Supported Chains

### Chain Detection Keywords

| Chain | Keywords |
|-------|----------|
| Ethereum | ethereum, eth, mainnet |
| Polygon | polygon, matic |
| Arbitrum | arbitrum, arb |
| Optimism | optimism, op |
| Base | base, base network |
| Avalanche | avalanche, avax |
| BSC | bsc, binance, bnb |
| Solana | solana, sol |

### Chain Capabilities

| Chain | Real-Time | Typical Cost | Savings |
|-------|-----------|--------------|---------|
| **Ethereum** | ✅ Yes | $1-50 | Baseline |
| **Polygon** | Guidance | $0.01-0.05 | ~95% |
| **Arbitrum** | Guidance | $0.10-0.50 | ~90% |
| **Optimism** | Guidance | $0.10-1.00 | ~85% |
| **Base** | Guidance | $0.10-0.50 | ~90% |
| **Avalanche** | Guidance | $0.01-0.05 | Very cheap |
| **BSC** | Guidance | $0.10-0.50 | Much cheaper |
| **Solana** | Guidance | $0.0001-0.001 | Very cheap |

---

## API Response Examples

### Current Gas Prices

```json
{
  "agent_message": {
    "content": "**REAL-TIME GAS PRICES - ETHEREUM:**\n- Slow: 25.3 gwei ($0.85 for standard transfer)\n- Standard: 28.5 gwei ($0.95 for standard transfer)\n- Fast: 35.2 gwei ($1.18 for standard transfer)\n- Base Fee: 25.3 gwei\n- Priority Fee: 3.2 gwei\n\n💡 **Recommendation**: Gas prices are LOW - good time to send transactions\n\n**Tips for Lower Fees:**\n1. Wait for off-peak hours (weekends, late night UTC)\n2. Consider Layer 2 for frequent transactions\n3. Batch multiple operations when possible",
    "role": "assistant",
    "agent_type": "gas_optimizer"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 80},
      {"agent_type": "gas_optimizer", "duration_ms": 800}
    ],
    "sources": [
      {
        "source_type": "blockchain",
        "source_name": "Ethereum",
        "citation_text": "Real-time gas prices from Ethereum network",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Chain Comparison

```json
{
  "agent_message": {
    "content": "## Gas Cost Comparison: Ethereum vs Arbitrum\n\n### Ethereum (L1)\n- Current: ~30 gwei (~$1.00 per transfer)\n- DeFi operations: $5-50+\n- Peak times: Can exceed 100 gwei\n\n### Arbitrum (L2)\n- Current: ~0.1-0.5 gwei (~$0.20 per transfer)\n- DeFi operations: $0.50-2.00\n- Consistent low fees\n\n### Savings with Arbitrum\n- **~90% cheaper than Ethereum**\n- Same security (inherits Ethereum's security)\n- Most major DeFi protocols available\n- Easy bridging from Ethereum\n\n### Recommendation\nFor frequent transactions or smaller amounts, Arbitrum offers significant savings.",
    "role": "assistant",
    "agent_type": "gas_optimizer"
  }
}
```

### Optimal Timing

```json
{
  "agent_message": {
    "content": "## Optimal Transaction Timing\n\n**Current Status**: Gas prices are MODERATE (45 gwei)\n\n### Best Times to Transact\n1. **Weekends**: 20-40% lower gas prices\n2. **Late night UTC** (00:00-06:00): Lowest activity\n3. **Avoid**: Monday-Friday 14:00-18:00 UTC (peak trading)\n\n### Current Recommendation\nGas prices are reasonable. If transaction is:\n- **Urgent**: Execute now at Standard tier (45 gwei)\n- **Can wait**: Wait for <30 gwei (typically weekends)\n- **Non-critical**: Use Slow tier or Layer 2\n\n### Layer 2 Alternative\nConsider Arbitrum or Base for 90% cheaper transactions with similar speed.",
    "role": "assistant",
    "agent_type": "gas_optimizer"
  }
}
```

### High Gas Warning

```json
{
  "agent_message": {
    "content": "**REAL-TIME GAS PRICES - ETHEREUM:**\n- Slow: 120.5 gwei ($4.05 for standard transfer)\n- Standard: 135.2 gwei ($4.55 for standard transfer)\n- Fast: 150.0 gwei ($5.05 for standard transfer)\n\n⚠️ **Recommendation**: Gas prices are HIGH - consider waiting or using Layer 2 (Arbitrum, Optimism, Base)\n\n### Layer 2 Alternatives (90% Cheaper)\n\n**Arbitrum:**\n- ~0.1-0.5 gwei (~$0.20-0.50 per transaction)\n- Most DeFi protocols available\n\n**Base:**\n- ~0.1-0.5 gwei (~$0.10-0.50 per transaction)\n- Growing ecosystem\n\n**Optimism:**\n- ~0.1-1 gwei (~$0.10-1.00 per transaction)\n- Strong DeFi presence\n\n### What to Do\n1. **Wait**: Gas often drops on weekends\n2. **Bridge to L2**: Use official bridges\n3. **Batch**: Combine multiple operations",
    "role": "assistant",
    "agent_type": "gas_optimizer"
  }
}
```

---

## Gas Price Tiers

### EIP-1559 Model (Ethereum)

| Tier | Calculation | Description |
|------|-------------|-------------|
| **Slow** | Base fee only | Cheapest, slowest confirmation |
| **Standard** | Base fee + priority fee | Balanced |
| **Fast** | Max fee | Fastest confirmation |

### Recommendation Thresholds

| Level | Gwei Range | Recommendation |
|-------|------------|----------------|
| **Low** | < 30 gwei | "Good time to send transactions" |
| **Moderate** | 30-100 gwei | "Standard transactions should work well" |
| **High** | > 100 gwei | "Consider waiting or using Layer 2" |

---

## Multi-Language Support

### English

```
Commands:
• "What are gas prices on Ethereum?"
• "Compare gas costs on Ethereum vs Arbitrum"
• "When is the best time to send a transaction?"
• "How can I reduce gas fees?"
```

### Spanish

```
Commands:
• "¿Cuáles son los precios de gas en Ethereum?"
• "Comparar costos de gas Ethereum vs Arbitrum"
• "¿Cuándo es el mejor momento para enviar?"
• "¿Cómo puedo reducir las tarifas de gas?"
```

### Portuguese

```
Commands:
• "Quais são os preços de gás no Ethereum?"
• "Comparar custos de gás Ethereum vs Arbitrum"
• "Quando é o melhor momento para enviar?"
• "Como posso reduzir as taxas de gás?"
```

---

## Error Handling

### Common Errors

| Error | User Message |
|-------|--------------|
| Web3Client unavailable | "Using typical gas price guidance. Real-time data unavailable." |
| RPC timeout | "Gas price fetch timed out. Based on recent trends..." |
| Chain not supported | "I provide detailed guidance for Ethereum, Polygon, Arbitrum, Optimism, Base, Avalanche, and BSC." |

### Fallback Behavior

```python
# If Web3Client fails, use typical guidance
if not gas_price_context:
    # Fall back to LLM-only with general knowledge
    response = await self._llm_client.chat(
        messages=[
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ],
        model=self._model,
    )
```

---

## Combined Query Patterns

### Supervisor Routing

| Query | Agents Used | Execution |
|-------|-------------|-----------|
| "what is defi? also check gas prices" | knowledge + gas_optimizer | Parallel |
| "poem about gas + current price" | gas_optimizer → chat | Sequential |
| "best yields and gas prices" | defi_yield + gas_optimizer | Parallel |
| "swap ETH to USDC" + gas check | swap_workflow (has own gas estimates) | Single |

### Examples from Supervisor

```python
# Parallel execution
"what is defi? also check gas prices" → {
    "tasks": [
        {"agent_type": "knowledge", "task_description": "Explain DeFi concepts", "depends_on": []},
        {"agent_type": "gas_optimizer", "task_description": "Get current gas prices", "depends_on": []}
    ]
}

# Sequential execution (poem needs gas data first)
"haceme un poema con el gas fee eth" → {
    "tasks": [
        {"agent_type": "gas_optimizer", "task_description": "Get current ETH gas fees", "depends_on": []},
        {"agent_type": "chat", "task_description": "Write a poem about ETH gas fees", "depends_on": ["gas_optimizer"]}
    ]
}
```

---

## Optimization Tips Format

### Standard Optimization Response

```markdown
## How to Reduce Gas Costs

### 1. Timing Strategy
- **Weekends**: 20-40% lower gas prices
- **Late night UTC** (00:00-06:00): Lowest network activity
- **Avoid peak hours**: Monday-Friday 14:00-18:00 UTC

### 2. Layer 2 Migration
| Chain | Savings | DeFi Support |
|-------|---------|--------------|
| Arbitrum | ~90% | Excellent |
| Optimism | ~85% | Good |
| Base | ~90% | Growing |
| Polygon | ~95% | Excellent |

### 3. Batch Transactions
- Combine multiple swaps into one transaction
- Use multicall contracts
- Aggregate approvals when possible

### 4. Gas-Efficient Protocols
- Choose protocols with gas-optimized contracts
- Use aggregators that optimize gas
- Consider gasless transactions (meta-transactions)

### 5. Transaction Settings
- Use "Slow" tier for non-urgent transactions
- Set custom gas limits based on operation type
- Avoid peak congestion times
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Gas Optimizer Agent Shortcuts**
