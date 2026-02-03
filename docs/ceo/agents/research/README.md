# Research Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **RESEARCH** agent provides deep protocol analysis and research capabilities using Perplexity AI for real-time web search with citations. It specializes in DeFi protocol documentation, smart contract architecture, tokenomics analysis, and protocol comparisons.

### Key Differentiators

- **Perplexity Integration**: Real-time web search with citations
- **Deep Analysis**: Protocol mechanics, tokenomics, governance
- **Citation Support**: Links to source documentation
- **DeFi Focus**: Specialized in crypto/blockchain research
- **Fallback Support**: LLM-only mode if Perplexity unavailable

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Query patterns and research topics |

---

## Quick Start

### For Users

**Example Commands:**
```
• "Research Aave V3 protocol"
• "Explain Uniswap V4 hooks"
• "Compare Aave vs Compound governance"
• "Analyze MakerDAO tokenomics"
• "Latest updates on Ethereum L2s"
```

### For Developers

1. Read `architecture.md` for hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for query patterns

---

## Key Features

### 1. Research Capabilities

| Capability | Description | Data Source |
|------------|-------------|-------------|
| **Protocol Analysis** | Deep-dives into protocol mechanics | Perplexity + Docs |
| **Smart Contract Research** | Architecture and implementation | Perplexity + Code |
| **Tokenomics** | Supply, distribution, utility | Perplexity + Data |
| **Comparisons** | Protocol vs protocol analysis | Perplexity + LLM |
| **Latest Updates** | Recent protocol changes | Perplexity (real-time) |

### 2. Perplexity Models

| Model | Description | Use Case |
|-------|-------------|----------|
| `sonar-small-online` | Fast, basic search | Quick lookups |
| `sonar-medium-online` | Balanced (default) | General research |
| `sonar-large-online` | Deep, comprehensive | Complex analysis |

### 3. Citation Support

- Perplexity provides source citations with URLs
- Citations are included in `sources` field
- Each citation has relevance score

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → ResearchAgentPerplexity
    ↓ (External Services)
External Systems
    - Perplexity API (web search)
    - Vertex AI (LLM fallback)
```

### Research Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH AGENT FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "Research Aave V3 protocol"                          │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: research query │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  ResearchAgentPerplexity│                               │
│  │                         │                               │
│  │  1. Check Perplexity    │ → API key available?          │
│  │  2. Call Perplexity     │ → sonar-medium-online         │
│  │  3. Extract answer      │ → Protocol analysis           │
│  │  4. Extract citations   │ → Source URLs                 │
│  │  5. Build sources       │ → With relevance scores       │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  Response with analysis │                               │
│  │  + source citations     │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Intent Classification

```python
# From intent_classifier.py

AGENT_MAPPING = {
    "research_protocol": AgentType.RESEARCH,
}
```

### Routing Examples

```python
# Direct research queries
"research Aave V3 protocol" → research
"explain Uniswap mechanics" → research
"analyze MakerDAO tokenomics" → research

# Note: Simple protocol questions may go to knowledge agent
"what is Aave?" → knowledge (informational)
"research Aave V3 architecture" → research (deep analysis)
```

---

## Example Conversations

### Protocol Deep-Dive

```
User: "Research Aave V3 protocol"

Agent:
## Aave V3 Protocol Analysis

### Overview
Aave V3 is the third major iteration of the Aave decentralized lending protocol, 
launched in March 2022. It introduces significant improvements in capital efficiency, 
risk management, and cross-chain capabilities.

### Key Features

**1. Efficiency Mode (E-Mode)**
- Allows higher borrowing power (up to 97% LTV) for correlated assets
- Categories: Stablecoins, ETH-correlated, BTC-correlated
- Reduces capital requirements for low-risk positions

**2. Isolation Mode**
- New assets listed in isolation mode have limited borrowing capacity
- Only specific stablecoins can be borrowed against isolated collateral
- Reduces systemic risk from new, untested assets

**3. Portal**
- Cross-chain liquidity bridging
- aTokens can be seamlessly transferred between networks
- Enables unified liquidity across Ethereum, Polygon, Arbitrum, Optimism

**4. Risk Management**
- Supply and borrow caps per asset
- Granular risk parameters
- Improved oracle integration (Chainlink)

### Tokenomics
- **Token**: AAVE
- **Total Supply**: 16 million AAVE
- **Governance**: Snapshot + on-chain execution
- **Staking**: Safety Module (stkAAVE) for protocol insurance

### Security
- Multiple audits: OpenZeppelin, Trail of Bits, Sigma Prime
- Bug bounty program: Up to $250,000
- Formal verification of core contracts

### Sources
[1] Aave V3 Documentation - https://docs.aave.com
[2] Aave Governance Forum - https://governance.aave.com
[3] DeFiLlama - https://defillama.com/protocol/aave
```

### Protocol Comparison

```
User: "Compare Aave vs Compound governance"

Agent:
## Governance Comparison: Aave vs Compound

### Aave Governance

**Model**: Token-weighted voting with delegation
**Token**: AAVE (+ stkAAVE for stakers)
**Voting Power**: 1 AAVE = 1 vote
**Proposal Threshold**: 80,000 AAVE
**Quorum**: 320,000 AAVE (short executor)

**Process**:
1. Snapshot off-chain vote (temperature check)
2. ARC (Aave Request for Comments)
3. On-chain proposal
4. 3-day voting period
5. 1-day timelock (short) or 7-day (long)

### Compound Governance

**Model**: Token-weighted with delegation
**Token**: COMP
**Voting Power**: 1 COMP = 1 vote
**Proposal Threshold**: 65,000 COMP
**Quorum**: 400,000 COMP

**Process**:
1. Governance forum discussion
2. On-chain proposal
3. 2-day voting delay
4. 3-day voting period
5. 2-day timelock

### Key Differences

| Aspect | Aave | Compound |
|--------|------|----------|
| Staking Bonus | Yes (stkAAVE) | No |
| Off-chain Voting | Snapshot | No |
| Executor Types | Short + Long | Single |
| Risk Parameters | More granular | Simpler |
| Multi-chain | Separate governance | Single chain |

### Sources
[1] Aave Governance Docs
[2] Compound Governance Docs
```

### Off-Topic Handling

```
User: "How to make a cake"

Agent:
I'm specialized in DeFi and crypto research. I can't help with cooking recipes, 
but I can research DeFi protocols, tokens, and blockchain technology.

Would you like me to research:
- DeFi protocols (Aave, Compound, Uniswap)
- Token analysis and tokenomics
- Smart contract architecture
- Protocol comparisons
- Blockchain technology
```

---

## Configuration

### Default Parameters

```python
# From research_agent_perplexity.py

model = "gemini-2.0-flash"  # LLM fallback
temperature = 0.2            # Factual, precise
max_tokens = 2000

# Perplexity model (when available)
perplexity_model = "sonar-medium-online"
```

### Environment Variables

```bash
# Required for Perplexity integration
PERPLEXITY_API_KEY=your_api_key

# MCP settings (optional)
MCP_PERPLEXITY_ENABLED=true
```

### Response Structure

```python
AgentResponse(
    content="Research analysis with citations...",
    agent_type=AgentType.RESEARCH,
    tools_used=["openai_api", "perplexity_api"],
    sources=[
        SourceInfo(source_type="api", source_name="Perplexity AI", 
                   url="https://docs.aave.com", 
                   citation_text="Aave V3 Documentation", ...),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
    ],
    metadata={
        "tokens_used": 800,
        "latency_ms": 1500,
        "model": "sonar-medium-online",
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] Perplexity client initialization
- [ ] Citation extraction
- [ ] Off-topic detection
- [ ] LLM fallback

### Integration Tests
- [ ] Perplexity API integration
- [ ] Citation URL handling
- [ ] Source attribution

### E2E Tests
- [ ] Complete research flow
- [ ] Protocol comparison
- [ ] Off-topic rejection

---

## Related Documentation

- **Knowledge Agent**: `/docs/ceo/agents/knowledge/` (educational content)
- **Hunter AI**: `/docs/ceo/agents/hunter/` (market analysis)
- **Risk Analyzer**: `/docs/ceo/agents/risk_analyzer/` (risk assessment)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added Perplexity MCP integration |
| 1.0 | 2026-01-29 | Added citation support |

---

**End of Research Agent Specification**
