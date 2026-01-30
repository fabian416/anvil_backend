# Tax Optimizer Agent Architecture

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Implemented
**Architecture**: Hexagonal (Clean Architecture)

---

## Executive Summary

This document defines the **Hexagonal Architecture** implementation for the **TAX_OPTIMIZER** agent, which provides tax-loss harvesting strategies, capital gains calculations, and tax optimization guidance.

### Key Components

- **TaxOptimizerAgent**: Agent Squad implementation
- **LLM Client**: Vertex AI for tax reasoning
- **Source Helpers**: Database and LLM source attribution

---

## Hexagonal Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   TAX OPTIMIZER ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────────────┐
                    │   Presentation Layer     │
                    │  (HTTP Controllers)      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Supervisor             │
                    │  (Intent Routing)        │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   TaxOptimizerAgent      │
                    │    (Infrastructure)      │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Transaction        │ │    Vertex AI    │ │  Source Helpers │
│  History (TODO)     │ │  (LLM Reasoning)│ │  (Attribution)  │
└─────────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Domain Layer

### Agent Type

**File**: `src/app/domain/enums/agent_type.py`

```python
class AgentType(Enum):
    # Core Agents
    TAX_OPTIMIZER = "tax_optimizer"  # Tax optimization
```

### Intent Classification

**File**: `src/app/domain/services/agent_squad/intent_classifier.py`

```python
intent_to_agent = {
    "tax_optimization": AgentType.TAX_OPTIMIZER,
    "tax_loss_harvesting": AgentType.TAX_OPTIMIZER,
}
```

---

## Infrastructure Layer

### TaxOptimizerAgent

**File**: `src/app/infrastructure/adapters/agent_squad/agents/tax_optimizer_agent.py`
**Lines**: ~156

```python
class TaxOptimizerAgent:
    """
    Tax Optimizer Agent implementation.
    
    Implements: AgentGateway
    
    Purpose: Tax-loss harvesting & tax optimization
    
    Capabilities:
    - Tax-loss harvesting opportunities
    - Capital gains calculation (short-term, long-term)
    - Tax-efficient timing (hold 366 days)
    - Wash sale rule compliance
    - Tax reporting (Form 8949, Schedule D)
    - FIFO/LIFO/HIFO cost basis selection
    
    Model: gemini-2.0-flash (Vertex AI, complex tax reasoning)
    Temperature: 0.2 (factual, precise)
    """
```

### Key Methods

| Method | Lines | Purpose |
|--------|-------|---------|
| `__init__` | 35-46 | Initialize with LLM client |
| `agent_type` | 48-51 | Return AgentType.TAX_OPTIMIZER |
| `execute` | 53-116 | Main entry point |
| `is_available` | 118-120 | Availability check |
| `_get_system_prompt` | 122-156 | Tax expertise prompt |

### Dependencies

```python
def __init__(
    self,
    llm_client: LLMClientGateway,      # Vertex AI / DeepInfra
    model: str = "gemini-2.0-flash",
    temperature: float = 0.2,           # Factual, precise
    max_tokens: int = 1500,             # Detailed analysis
):
```

---

## System Prompt Design

### Core Expertise Areas

```python
def _get_system_prompt(self) -> str:
    return """You are the Tax Optimizer, Anvil's tax strategy specialist.

Your expertise:
- Tax-loss harvesting opportunities
- Capital gains calculation (short-term vs long-term)
- Tax-efficient timing strategies
- Wash sale rule compliance (30-day rule)
- Cost basis selection (FIFO, LIFO, HIFO)
- Tax reporting (Form 8949, Schedule D)
- Year-end tax optimization
```

### Analysis Output Requirements

```python
For tax analysis, provide:
- Capital gains breakdown (ST/LT)
- Tax-loss harvesting opportunities
- Potential tax savings
- Timing recommendations
- Wash sale warnings
- Estimated tax liability
```

### Tax Rate Reference

```python
Tax Rates (US):
- Short-term: Ordinary income (10%-37%)
- Long-term: 0%, 15%, 20% (based on income)
- Hold period: >365 days for long-term
```

### Required Elements

```python
Always include:
- Quantitative analysis (gains, losses, savings)
- Timing recommendations
- Compliance warnings (wash sale)
- Disclaimer: "Consult a tax professional"

Note: Tax laws vary by jurisdiction. Recommendations are general guidance.
```

---

## Source Attribution

### Database Source

```python
from app.infrastructure.adapters.agent_squad.agents.source_helpers import (
    create_llm_source,
    create_database_source,
)

# Transaction history source
sources.append(create_database_source(
    citation_text="Your transaction history from Anvil",
    fetched_at=fetched_at,
    metadata={"query_type": "transaction_history"},
))
```

### LLM Source

```python
# LLM analysis source
model_name = response.get("model", "Unknown")
sources.append(create_llm_source(
    model=model_name,
    fetched_at=fetched_at,
))
```

---

## DI Registration

### Provider Method

```python
# From agent_squad_infrastructure.py

@provide
def provide_tax_optimizer_agent(
    self, llm_client: LLMClientGateway
) -> TaxOptimizerAgent:
    """Provide Tax Optimizer agent."""
    return TaxOptimizerAgent(llm_client=llm_client)
```

### Agent Registry

```python
# Agent type mapping
AgentType.TAX_OPTIMIZER: tax_optimizer_agent,
```

---

## Tax Analysis Flow

### Current Implementation

```
1. User Query: "Find tax-loss harvesting opportunities"
   ↓
2. Intent Classification
   → tax_optimization / tax_loss_harvesting
   ↓
3. Supervisor Routes to tax_optimizer
   ↓
4. TaxOptimizerAgent.execute()
   ↓
5. Build LLM Prompt
   - System prompt with tax expertise
   - User query
   ↓
6. LLM Analysis (Vertex AI)
   - Capital gains calculation
   - Harvesting opportunities
   - Compliance warnings
   ↓
7. Source Attribution
   - Database: Transaction history
   - LLM: Tax reasoning
   ↓
8. Return AgentResponse
```

### Future Enhancement (TODO)

```
1. User Query: "Find tax-loss harvesting opportunities"
   ↓
2. Load Transaction History
   → Real on-chain transaction data
   ↓
3. Calculate Actual Gains/Losses
   → Per-asset cost basis tracking
   ↓
4. Identify Harvesting Opportunities
   → Algorithm-based analysis
   ↓
5. LLM Contextualization
   → Explain findings in natural language
   ↓
6. Generate Recommendations
   → Specific, actionable advice
```

---

## Tax Concepts

### Capital Gains Classification

| Type | Holding Period | US Tax Rate |
|------|----------------|-------------|
| Short-term | ≤ 365 days | 10% - 37% (ordinary income) |
| Long-term | > 365 days | 0%, 15%, or 20% |

### Tax-Loss Harvesting

**Definition**: Selling assets at a loss to offset capital gains.

**Example**:
```
Before Harvesting:
- BTC gain: +$10,000 (taxable)
- Tax at 30%: $3,000

With Harvesting:
- BTC gain: +$10,000
- ETH loss: -$4,000 (realized by selling)
- Net gain: $6,000 (taxable)
- Tax at 30%: $1,800
- Savings: $1,200
```

### Wash Sale Rule

**30-Day Rule**: Cannot claim loss if substantially identical asset is purchased within 30 days before or after sale.

```
Timeline Example:
Day -30 to Day 0: No purchase allowed
Day 0: Sell ETH at loss
Day 0 to Day +30: No purchase allowed
Day 31+: Can repurchase ETH
```

### Cost Basis Methods

| Method | Description | Best Use Case |
|--------|-------------|---------------|
| **FIFO** | First In, First Out | Standard, conservative |
| **LIFO** | Last In, First Out | Short-term loss harvesting |
| **HIFO** | Highest In, First Out | Minimize current gains |

---

## Response Structure

```python
return AgentResponse(
    content=response["content"],
    agent_type=self.agent_type,
    tools_used=["llm_gateway"],  # TODO: Add tax calculation tools
    sources=sources,
    metadata={
        "tokens_used": response.get("tokens_used"),
        "latency_ms": latency_ms,
        "model": response.get("model"),
    },
)
```

---

## Future Enhancements

### TODO Items

```python
# TODO: Integrate with user transaction history
# TODO: Calculate real capital gains
# TODO: Identify tax-loss harvesting opportunities
# TODO: Add tax calculation API sources when integrated
```

### Planned Features

1. **Transaction History Integration**
   - Load user's actual transactions
   - Track cost basis per lot
   - Calculate unrealized gains/losses

2. **Real-Time Tax Calculations**
   - Automatic gain/loss calculation
   - Year-to-date tax estimates
   - Holding period tracking

3. **Tax Report Generation**
   - Form 8949 generation
   - Schedule D summary
   - CSV export for TurboTax/TaxBit

4. **Multi-Jurisdiction Support**
   - US tax rules (current)
   - EU regulations
   - UK crypto taxes
   - Country-specific guidance

---

## Performance

### Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| LLM reasoning | < 2s | Vertex AI |
| Total | < 2s | All combined |

### Future Targets

| Operation | Target | Implementation |
|-----------|--------|----------------|
| Transaction loading | < 500ms | Database query |
| Gain calculation | < 200ms | Algorithm |
| LLM contextualization | < 1s | Vertex AI |
| Total | < 2s | All combined |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Initial implementation |
| 2026-01-29 | Added system prompt with tax expertise |
| 2026-01-29 | Added source attribution |
