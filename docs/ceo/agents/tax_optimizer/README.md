# Tax Optimizer Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Implemented (Enhancement Planned)
**Agent Type**: Core Agent
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **TAX_OPTIMIZER** agent provides tax-loss harvesting strategies, capital gains calculations, and tax optimization guidance for DeFi users. It helps users minimize their tax liability through intelligent timing and strategic asset management.

### Key Differentiators

- **Tax-Loss Harvesting**: Identify opportunities to offset gains
- **Capital Gains Calculation**: Short-term vs long-term analysis
- **Wash Sale Compliance**: 30-day rule enforcement
- **Cost Basis Selection**: FIFO, LIFO, HIFO strategies
- **Tax Reporting**: Form 8949 and Schedule D guidance

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and tax strategies |

---

## Quick Start

### For Users

**Tax Optimization Queries:**
```
• "What are my capital gains this year?"
• "Find tax-loss harvesting opportunities"
• "Should I sell now or wait for long-term gains?"
• "Calculate my estimated tax liability"
• "How do I avoid wash sales?"
• "Which cost basis method should I use?"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for query patterns

---

## Key Features

### 1. Tax-Loss Harvesting

Identify opportunities to sell assets at a loss to offset capital gains:

```
Example:
- ETH bought at $4,000, now at $2,500 = -$1,500 loss
- Use this loss to offset BTC gains of $3,000
- Net taxable gain: $1,500 (vs $3,000 without harvesting)
- Potential tax savings: $450 (at 30% rate)
```

### 2. Capital Gains Analysis

| Holding Period | Classification | Tax Rate (US) |
|----------------|----------------|---------------|
| ≤ 365 days | Short-term | 10% - 37% (ordinary income) |
| > 365 days | Long-term | 0%, 15%, or 20% |

### 3. Wash Sale Rule Compliance

**30-Day Rule**: Cannot claim loss if you repurchase substantially identical asset within 30 days before or after the sale.

```
⚠️ Wash Sale Warning:
- Sold ETH at loss on Jan 15
- Repurchased ETH on Jan 30 (within 30 days)
- Loss DISALLOWED for tax purposes
```

### 4. Cost Basis Methods

| Method | Description | Best For |
|--------|-------------|----------|
| **FIFO** | First In, First Out | Standard, most conservative |
| **LIFO** | Last In, First Out | Short-term loss harvesting |
| **HIFO** | Highest In, First Out | Minimize gains |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Routing)
Infrastructure Layer → TaxOptimizerAgent
    ↓
External Systems
    - Transaction History (Database)
    - Vertex AI (LLM reasoning)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  TAX OPTIMIZER FLOW                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "What are my tax-loss harvesting opportunities?"     │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │   Supervisor            │                               │
│  │   Detects: tax query    │                               │
│  │   → routes to tax_opt   │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   TaxOptimizerAgent     │                               │
│  │                         │                               │
│  │  1. Load transaction    │ → Anvil Database             │
│  │     history (TODO)      │                               │
│  │  2. Calculate gains     │ → Cost basis logic           │
│  │  3. Find opportunities  │ → LLM analysis               │
│  │  4. Generate advice     │ → Tax strategies             │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  Response: Tax optimization recommendations                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Detection

```python
# From intent_classifier.py
intent_to_agent = {
    "tax_optimization": AgentType.TAX_OPTIMIZER,
    "tax_loss_harvesting": AgentType.TAX_OPTIMIZER,
}
```

### Agent Classification

```
- tax_optimizer: Tax strategies
```

---

## Tax Concepts

### Capital Gains Types

| Type | Holding Period | US Tax Rate |
|------|----------------|-------------|
| Short-term | ≤ 365 days | 10% - 37% |
| Long-term | > 365 days | 0% / 15% / 20% |

### Tax-Loss Harvesting

**Strategy**: Sell assets at a loss to offset capital gains.

**Example Calculation**:
```
Portfolio:
- BTC: +$5,000 gain (short-term)
- ETH: -$2,000 loss (unrealized)
- LINK: -$500 loss (unrealized)

Tax-Loss Harvesting:
- Sell ETH and LINK to realize -$2,500 loss
- Offset against BTC gain: $5,000 - $2,500 = $2,500 taxable
- Tax saved (at 30%): $750
```

### Wash Sale Rule

**30-Day Window**: Cannot repurchase substantially identical asset.

```
Timeline:
Day 0: Sell ETH at $1,500 loss
Day 1-30: CANNOT buy ETH (wash sale)
Day 31+: Can buy ETH, loss is deductible
```

**Workaround**: Buy similar but not identical assets (e.g., sell ETH, buy MATIC).

---

## Configuration

### Default Parameters

```python
# From tax_optimizer_agent.py

model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.2           # Factual, precise
max_tokens = 1500           # Detailed analysis
```

### Response Structure

```python
AgentResponse(
    content="Tax analysis and recommendations...",
    agent_type=AgentType.TAX_OPTIMIZER,
    tools_used=["llm_gateway"],  # TODO: Add tax calculation tools
    sources=[
        SourceInfo(source_type="database", source_name="Anvil Database",
                   citation_text="Your transaction history from Anvil"),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash",
                   citation_text="Generated by gemini-2.0-flash"),
    ],
    metadata={
        "tokens_used": 500,
        "latency_ms": 600,
        "model": "gemini-2.0-flash",
    },
)
```

---

## Future Enhancements (TODO)

### 1. Transaction History Integration

```python
# TODO: Integrate with user transaction history
# TODO: Calculate real capital gains
# TODO: Identify tax-loss harvesting opportunities
```

### 2. Real-Time Tax Calculations

- Integration with on-chain transaction data
- Automatic cost basis tracking
- Real-time gain/loss calculations

### 3. Tax Report Generation

- Form 8949 (Sales and Dispositions of Capital Assets)
- Schedule D (Capital Gains and Losses)
- CSV export for tax software

### 4. Multi-Jurisdiction Support

- US tax rules (current)
- EU tax regulations
- UK crypto tax rules
- Other jurisdictions

---

## Disclaimer

**Important**: This agent provides general tax guidance only. Users should:

1. Consult a qualified tax professional
2. Verify calculations independently
3. Keep detailed records of all transactions
4. Consider jurisdiction-specific rules

---

## Testing Checklist

### Unit Tests
- [ ] Capital gains calculation (ST/LT)
- [ ] Wash sale detection
- [ ] Cost basis selection
- [ ] Tax rate application

### Integration Tests
- [ ] Transaction history loading
- [ ] LLM response generation
- [ ] Source attribution

### E2E Tests
- [ ] Complete tax analysis flow
- [ ] Multi-asset portfolio
- [ ] Year-end optimization

---

## Related Documentation

- **Portfolio Agent**: `/docs/ceo/agents/portfolio/` (asset tracking)
- **Transaction History**: `/docs/ceo/agents/activity/` (transaction records)
- **Execution Agent**: `/docs/ceo/agents/execution/` (trade execution)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Tax Optimizer Agent Specification**
