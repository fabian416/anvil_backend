# Research Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the query patterns, research topics, and response formats for the **RESEARCH** agent.

---

## Query Patterns

### Protocol Research

| Pattern | Example | Action |
|---------|---------|--------|
| Research {protocol} | "Research Aave V3 protocol" | Deep protocol analysis |
| Explain {protocol} | "Explain Uniswap V4 hooks" | Technical explanation |
| How does {protocol} work | "How does Compound work?" | Mechanics overview |
| {protocol} architecture | "Curve architecture analysis" | Technical deep-dive |

### Comparison Queries

| Pattern | Example | Action |
|---------|---------|--------|
| Compare {A} vs {B} | "Compare Aave vs Compound" | Protocol comparison |
| {A} vs {B} governance | "Aave vs Compound governance" | Governance comparison |
| Difference between | "Difference between L1 and L2" | Concept comparison |

### Tokenomics Research

| Pattern | Example | Action |
|---------|---------|--------|
| {token} tokenomics | "Analyze AAVE tokenomics" | Token analysis |
| {token} supply | "What is ETH supply?" | Supply analysis |
| {token} distribution | "UNI token distribution" | Distribution analysis |

### Latest Updates

| Pattern | Example | Action |
|---------|---------|--------|
| Latest {topic} | "Latest Ethereum updates" | Recent changes |
| {protocol} updates | "Aave V3 updates" | Protocol news |
| Recent {topic} | "Recent DeFi innovations" | Current trends |

---

## Research Topics

### Supported Topics (DeFi/Crypto Only)

| Category | Examples |
|----------|----------|
| **Protocols** | Aave, Uniswap, Compound, Curve, MakerDAO, Lido |
| **Smart Contracts** | Architecture, audits, vulnerabilities |
| **Tokenomics** | Supply, distribution, utility, governance |
| **Blockchain** | Ethereum, L2s, consensus, scaling |
| **DeFi Concepts** | AMMs, lending, staking, yield farming |
| **Security** | Audits, exploits, best practices |

### Off-Topic Topics (Decline)

| Category | Examples | Response |
|----------|----------|----------|
| **Cooking** | Recipes, food | "I'm specialized in DeFi..." |
| **General Knowledge** | History, science | "I can only research crypto..." |
| **Entertainment** | Movies, games | "Let me help with DeFi instead..." |
| **Personal** | Relationships, advice | "I focus on DeFi research..." |

---

## API Response Examples

### Protocol Deep-Dive

```json
{
  "agent_message": {
    "content": "## Aave V3 Protocol Analysis\n\n### Overview\nAave V3 is the third major iteration of the Aave decentralized lending protocol...\n\n### Key Features\n\n**1. Efficiency Mode (E-Mode)**\n- Allows higher borrowing power (up to 97% LTV) for correlated assets...\n\n**2. Isolation Mode**\n- New assets listed in isolation mode have limited borrowing capacity...\n\n### Sources\n[1] Aave V3 Documentation - https://docs.aave.com",
    "role": "assistant",
    "agent_type": "research"
  },
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 80},
      {"agent_type": "research", "duration_ms": 2000}
    ],
    "sources": [
      {
        "source_type": "api",
        "source_name": "Perplexity AI",
        "url": "https://docs.aave.com",
        "citation_text": "Aave V3 Documentation",
        "relevance_score": 0.5
      },
      {
        "source_type": "api",
        "source_name": "Perplexity AI",
        "url": "https://governance.aave.com",
        "citation_text": "Aave Governance Forum",
        "relevance_score": 0.5
      },
      {
        "source_type": "llm",
        "source_name": "sonar-medium-online",
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
    "content": "## Governance Comparison: Aave vs Compound\n\n### Aave Governance\n\n**Model**: Token-weighted voting with delegation\n**Token**: AAVE (+ stkAAVE for stakers)\n**Proposal Threshold**: 80,000 AAVE\n...\n\n### Compound Governance\n\n**Model**: Token-weighted with delegation\n**Token**: COMP\n**Proposal Threshold**: 65,000 COMP\n...\n\n### Key Differences\n\n| Aspect | Aave | Compound |\n|--------|------|----------|\n| Staking Bonus | Yes | No |",
    "role": "assistant",
    "agent_type": "research"
  }
}
```

### Off-Topic Rejection

```json
{
  "agent_message": {
    "content": "I'm specialized in DeFi and crypto research. I can't help with cooking recipes, but I can research DeFi protocols, tokens, and blockchain technology.\n\nWould you like me to research:\n- DeFi protocols (Aave, Compound, Uniswap)\n- Token analysis and tokenomics\n- Smart contract architecture\n- Protocol comparisons\n- Blockchain technology",
    "role": "assistant",
    "agent_type": "research"
  }
}
```

### LLM Fallback (No Perplexity)

```json
{
  "agent_message": {
    "content": "## Uniswap V4 Hooks Analysis\n\n### Overview\nUniswap V4 introduces hooks, which are custom logic contracts that can be attached to liquidity pools...\n\n### Key Features\n1. Custom pool logic\n2. Dynamic fees\n3. Oracle integration\n...",
    "role": "assistant",
    "agent_type": "research"
  },
  "enrichment": {
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

---

## Perplexity Models

### Available Models

| Model | Speed | Quality | Use Case |
|-------|-------|---------|----------|
| `sonar-small-online` | Fast | Good | Quick lookups |
| `sonar-medium-online` | Medium | Better | General research (default) |
| `sonar-large-online` | Slow | Best | Complex analysis |

### Model Selection

```python
# Default model for research
perplexity_result = await self._perplexity_client._search(
    query=message.value,
    model="sonar-medium-online",  # Balanced choice
    max_tokens=self._max_tokens,
)
```

---

## Citation Format

### With Citations

```
## Protocol Analysis

[Content from research...]

### Sources
[1] Protocol Documentation - https://docs.protocol.com
[2] Governance Forum - https://forum.protocol.com
[3] DeFiLlama - https://defillama.com/protocol/name
```

### Source Metadata

```python
create_api_source(
    source_name="Perplexity AI",
    url=citation_url,
    citation_text=citation_title,
    fetched_at=datetime.now(UTC),
    provider="Perplexity API",
    relevance_score=1.0 / num_citations,
    metadata={"citation_index": idx},
)
```

---

## Research vs Knowledge Agent

### When to Use Research

| Query Type | Agent | Reason |
|------------|-------|--------|
| Deep protocol analysis | RESEARCH | Needs web search |
| Latest updates | RESEARCH | Real-time data |
| Technical architecture | RESEARCH | Needs documentation |
| Protocol comparison | RESEARCH | Comprehensive analysis |

### When to Use Knowledge

| Query Type | Agent | Reason |
|------------|-------|--------|
| What is DeFi? | KNOWLEDGE | Educational |
| Basic concepts | KNOWLEDGE | Static knowledge |
| Anvil features | KNOWLEDGE | Platform info |
| How-to guides | KNOWLEDGE | Pre-written content |

---

## Multi-Language Support

### English

```
Commands:
• "Research Aave V3 protocol"
• "Explain Uniswap mechanics"
• "Compare Aave vs Compound"
• "Analyze AAVE tokenomics"
```

### Spanish

```
Commands:
• "Investigar protocolo Aave V3"
• "Explicar mecánicas de Uniswap"
• "Comparar Aave vs Compound"
```

### Portuguese

```
Commands:
• "Pesquisar protocolo Aave V3"
• "Explicar mecânicas do Uniswap"
• "Comparar Aave vs Compound"
```

---

## Error Handling

### Common Errors

| Error | User Message |
|-------|--------------|
| Perplexity unavailable | "Using cached research. Results may not include latest updates." |
| API rate limit | "Research service busy. Please try again in a moment." |
| No results | "Could not find research on this topic. Try a more specific query." |
| Off-topic | "I'm specialized in DeFi and crypto research..." |

### Fallback Behavior

```python
# If Perplexity fails, use LLM-only
if not perplexity_result or perplexity_result.get("error"):
    # Fallback to Vertex AI LLM
    response = await self._llm_client.chat(
        messages=[
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": message.value},
        ],
        model=self._model,
    )
```

---

## Comprehensive Analysis Format

### Standard Research Output

```markdown
## [Topic] Analysis

### Overview
[High-level summary]

### Key Features
1. **Feature 1**: Description
2. **Feature 2**: Description
3. **Feature 3**: Description

### How It Works
[Technical mechanics]

### Tokenomics (if applicable)
- **Token**: [Symbol]
- **Supply**: [Total/Circulating]
- **Distribution**: [Breakdown]
- **Utility**: [Use cases]

### Governance
[Governance model details]

### Security
[Audit status, vulnerabilities, bug bounties]

### Risks and Limitations
[Potential issues]

### Recent Updates
[Latest changes]

### Sources
[1] [Title] - [URL]
[2] [Title] - [URL]
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Research Agent Shortcuts**
