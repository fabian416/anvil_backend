# Tax Optimizer Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, tax strategies, and example responses for the **TAX_OPTIMIZER** agent.

---

## Query Patterns

### Tax-Loss Harvesting

| Query | Intent | Description |
|-------|--------|-------------|
| "Find tax-loss harvesting opportunities" | tax_loss_harvesting | Identify losses to offset gains |
| "What losses can I harvest?" | tax_loss_harvesting | Show harvestable losses |
| "Help me reduce my tax bill" | tax_optimization | General tax optimization |
| "Which coins should I sell at a loss?" | tax_loss_harvesting | Specific harvesting advice |

### Capital Gains Analysis

| Query | Intent | Description |
|-------|--------|-------------|
| "What are my capital gains this year?" | tax_optimization | YTD capital gains summary |
| "Calculate my gains and losses" | tax_optimization | Full gain/loss breakdown |
| "How much tax do I owe on crypto?" | tax_optimization | Tax liability estimate |
| "Short-term vs long-term gains" | tax_optimization | Holding period analysis |

### Timing Optimization

| Query | Intent | Description |
|-------|--------|-------------|
| "Should I sell now or wait?" | tax_optimization | Timing recommendation |
| "When will my ETH be long-term?" | tax_optimization | Holding period check |
| "How long until I pay less tax?" | tax_optimization | Long-term threshold |
| "Best time to sell for taxes" | tax_optimization | Timing strategy |

### Wash Sale Compliance

| Query | Intent | Description |
|-------|--------|-------------|
| "What is the wash sale rule?" | tax_optimization | Rule explanation |
| "Can I buy back ETH after selling?" | tax_optimization | Wash sale guidance |
| "How to avoid wash sales?" | tax_optimization | Compliance advice |
| "30-day rule for crypto" | tax_optimization | Wash sale timing |

### Cost Basis Selection

| Query | Intent | Description |
|-------|--------|-------------|
| "FIFO vs LIFO for crypto taxes" | tax_optimization | Cost basis comparison |
| "Which cost basis method is best?" | tax_optimization | Method recommendation |
| "How does HIFO work?" | tax_optimization | HIFO explanation |
| "Change my cost basis method" | tax_optimization | Method selection |

### Tax Reporting

| Query | Intent | Description |
|-------|--------|-------------|
| "Help with Form 8949" | tax_optimization | Form guidance |
| "Schedule D crypto reporting" | tax_optimization | Reporting guidance |
| "How to report crypto taxes" | tax_optimization | General reporting |
| "Export transactions for TurboTax" | tax_optimization | Export guidance |

---

## Example Conversations

### Tax-Loss Harvesting

```
User: "Find tax-loss harvesting opportunities"

Agent:
📊 **Tax-Loss Harvesting Analysis**

Based on your portfolio, here are potential harvesting opportunities:

**Unrealized Losses:**
| Asset | Cost Basis | Current Value | Unrealized Loss |
|-------|-----------|---------------|-----------------|
| ETH | $4,000 | $2,500 | -$1,500 |
| LINK | $25 | $15 | -$500 |
| UNI | $30 | $12 | -$900 |

**Total Harvestable Loss:** -$2,900

**If you have short-term gains:**
- Gains: $5,000
- After harvesting: $2,100
- Tax savings (at 30%): $870

**⚠️ Wash Sale Warning:**
If you sell any of these assets, you cannot repurchase substantially 
identical assets within 30 days, or the loss will be disallowed.

**Recommendation:**
1. Consider selling ETH to harvest the largest loss
2. Wait 31 days before repurchasing
3. Or buy a similar asset (e.g., stETH) as an alternative

📌 *Consult a tax professional for personalized advice.*
```

### Capital Gains Breakdown

```
User: "What are my capital gains this year?"

Agent:
📈 **2026 Capital Gains Summary**

**Short-Term Gains (≤365 days):**
| Asset | Gain/Loss | Holding Period |
|-------|-----------|----------------|
| BTC | +$3,500 | 120 days |
| SOL | +$800 | 90 days |
| AVAX | -$400 | 60 days |
| **Subtotal** | **+$3,900** | |

**Long-Term Gains (>365 days):**
| Asset | Gain/Loss | Holding Period |
|-------|-----------|----------------|
| ETH | +$5,000 | 450 days |
| **Subtotal** | **+$5,000** | |

**Tax Implications (estimated):**
- Short-term (30% rate): ~$1,170
- Long-term (15% rate): ~$750
- **Total estimated tax:** ~$1,920

**Optimization Tip:**
You have unrealized losses in LINK (-$500) that could offset your 
short-term gains if harvested before year-end.

📌 *Consult a tax professional for personalized advice.*
```

### Timing Recommendation

```
User: "Should I sell my BTC now or wait?"

Agent:
⏰ **BTC Holding Period Analysis**

**Your BTC Position:**
- Purchase Date: August 15, 2025
- Current Hold Time: 167 days
- Long-term Threshold: 366 days
- Days Until Long-term: 199 days (August 17, 2026)

**Tax Rate Comparison:**

| Scenario | Rate | Tax on $5,000 gain |
|----------|------|-------------------|
| Sell now (short-term) | 30% | $1,500 |
| Wait until Aug 17 (long-term) | 15% | $750 |
| **Savings by waiting** | | **$750** |

**Recommendation:**
If you can wait ~6.5 months, you'll save approximately $750 in taxes 
on your current unrealized gain.

**Considerations:**
- Market volatility could affect the gain amount
- Long-term rates may vary based on income bracket
- Other tax obligations may influence timing

📌 *Consult a tax professional for personalized advice.*
```

### Wash Sale Warning

```
User: "Can I buy back ETH after selling at a loss?"

Agent:
⚠️ **Wash Sale Rule Explanation**

**The 30-Day Rule:**
You cannot claim a tax loss if you buy "substantially identical" 
securities within 30 days before or after the sale.

**Your Scenario:**
If you sell ETH at a loss on January 15:
- ❌ Cannot buy ETH: Dec 16 - Feb 14
- ✅ Can buy ETH: Feb 15 or later

**Timeline:**
```
Dec 16 ──── Jan 15 ──── Feb 14 ──── Feb 15+
   │          │           │            │
   30 days    SELL        30 days      OK to buy
   before              after        (loss allowed)
```

**Workarounds:**
1. **Wait 31 days**: Simplest approach
2. **Buy similar asset**: stETH, wETH, or ETH on different chain 
   (consult tax professional - may still be "substantially identical")
3. **Different token**: Buy a different crypto entirely

**If Wash Sale Occurs:**
- The loss is disallowed for the current year
- The disallowed loss is added to your cost basis of the new purchase
- You'll recover the loss when you eventually sell (deferred, not lost)

📌 *Consult a tax professional for personalized advice.*
```

### Cost Basis Methods

```
User: "Which cost basis method should I use?"

Agent:
📊 **Cost Basis Method Comparison**

**Available Methods:**

| Method | Description | Best For |
|--------|-------------|----------|
| **FIFO** | First In, First Out | Default, conservative |
| **LIFO** | Last In, First Out | Short-term loss harvesting |
| **HIFO** | Highest In, First Out | Minimizing current gains |

**Example: Selling 1 ETH (bought at different prices)**

| Lot | Purchase Price | Method Used |
|-----|---------------|-------------|
| Lot 1 | $1,500 | FIFO selects this |
| Lot 2 | $4,000 | HIFO selects this |
| Lot 3 | $2,500 | LIFO selects this |

**If current price is $3,000:**

| Method | Cost Basis | Gain/Loss | Tax (30%) |
|--------|-----------|-----------|-----------|
| FIFO | $1,500 | +$1,500 | $450 |
| LIFO | $2,500 | +$500 | $150 |
| HIFO | $4,000 | -$1,000 | $0 (loss) |

**Recommendation:**
- Use **HIFO** to minimize current year taxes
- Use **FIFO** for simplest record-keeping
- Use **LIFO** when recent purchases are higher

**Important:**
- Choose method before selling
- Apply consistently (or per-lot selection if available)
- Keep detailed records

📌 *Consult a tax professional for personalized advice.*
```

---

## API Response Examples

### Tax-Loss Harvesting Query

```json
{
  "agent_message": {
    "content": "📊 **Tax-Loss Harvesting Analysis**\n\nBased on your portfolio, here are potential harvesting opportunities...",
    "role": "assistant",
    "agent_type": "tax_optimizer"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 60},
      {"agent_type": "tax_optimizer", "duration_ms": 1200}
    ],
    "sources": [
      {
        "source_type": "database",
        "source_name": "Anvil Database",
        "citation_text": "Your transaction history from Anvil",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Generated by gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

---

## Tax Concepts Quick Reference

### Capital Gains Rates (US)

| Type | Holding Period | Tax Rate |
|------|----------------|----------|
| Short-term | ≤ 365 days | 10% - 37% (ordinary income) |
| Long-term | > 365 days | 0%, 15%, or 20% |

### Wash Sale Rule

- **Window**: 30 days before AND after sale
- **Total period**: 61-day window
- **Substantially identical**: Same crypto asset
- **Consequence**: Loss disallowed (added to new cost basis)

### Cost Basis Methods

| Method | Description |
|--------|-------------|
| FIFO | Oldest purchases sold first |
| LIFO | Newest purchases sold first |
| HIFO | Highest cost purchases sold first |
| Specific ID | Choose specific lots |

### Year-End Strategies

1. **Harvest losses** before Dec 31
2. **Defer gains** to next year if possible
3. **Check holding periods** for long-term threshold
4. **Avoid wash sales** - wait until January if needed

---

## Disclaimer

**Important**: All tax guidance is general information only.

- Tax laws vary by jurisdiction
- Individual circumstances differ
- Always consult a qualified tax professional
- Keep detailed transaction records
- This is not tax advice

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Tax Optimizer Agent Shortcuts**
