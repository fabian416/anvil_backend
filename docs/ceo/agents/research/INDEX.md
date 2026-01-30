# Research Agent - Complete Index

> **Project:** Anvil DeFi Chat - Deep Protocol Research
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **RESEARCH** agent, Anvil's deep protocol analysis and research system using Perplexity AI.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and research topics |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Perplexity MCP integration
- Citation extraction
- LLM fallback mechanism
- Off-topic handling

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Perplexity API calls
- Response building

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Research patterns and topics:

**Key Contents:**
- Supported query types
- Protocol analysis examples
- Comparison queries
- Off-topic handling

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Perplexity Integration | ✅ | Real-time web search |
| Citation Support | ✅ | Source URLs with relevance |
| LLM Fallback | ✅ | Vertex AI if Perplexity fails |
| Off-Topic Handling | ✅ | Decline non-crypto queries |
| Protocol Analysis | ✅ | Deep-dives into protocols |
| Source Attribution | ✅ | Citations + LLM sources |

### Perplexity Models (✅ Supported)

| Model | Status | Use Case |
|-------|--------|----------|
| sonar-small-online | ✅ | Quick lookups |
| sonar-medium-online | ✅ | General research (default) |
| sonar-large-online | ✅ | Complex analysis |

---

## 📊 Key Metrics

### Performance Targets

- **Perplexity API**: < 2000ms
- **LLM Fallback**: < 1500ms
- **Total Response**: < 3s

### Research Capabilities

- **Protocol Documentation**: Deep analysis
- **Smart Contracts**: Architecture review
- **Tokenomics**: Economic analysis
- **Comparisons**: Protocol vs protocol
- **Updates**: Latest changes

---

## 🔗 Related Specifications

### Agent Dependencies

- **Knowledge Agent**: For educational content
- **Risk Analyzer**: For risk assessment
- **Hunter AI**: For market analysis

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/research_agent_perplexity.py`

**MCP Server:**
- `src/app/infrastructure/mcp/servers/perplexity_mcp.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_research_agent)

---

## 🚀 Research Journey

### With Perplexity

```
1. User says: "Research Aave V3 protocol"
   → Supervisor routes to research

2. Check Perplexity availability
   → API key present ✓
   → MCP server enabled ✓

3. Call Perplexity API
   → Model: sonar-medium-online
   → Query: "Research Aave V3 protocol"

4. Extract response
   → Answer: Protocol analysis
   → Citations: [doc1.url, doc2.url, ...]

5. Build sources
   → Perplexity citations with URLs
   → LLM source

6. Return response
   → Content + citations
```

### Fallback (No Perplexity)

```
1. User says: "Research Aave V3 protocol"
   → Supervisor routes to research

2. Check Perplexity availability
   → API key missing ✗
   → Fallback to LLM

3. Call Vertex AI
   → System prompt with research expertise
   → User query

4. Return response
   → LLM-generated analysis
   → LLM source only
```

---

## 🔑 Critical Rules

### DeFi Focus Only

```python
# ONLY research DeFi, crypto, blockchain topics

# DECLINE:
- Cooking recipes
- General knowledge
- Non-crypto topics

# ACCEPT:
- DeFi protocols
- Smart contracts
- Tokenomics
- Blockchain technology
```

### Off-Topic Response

```
I'm specialized in DeFi and crypto research. I can't help with [topic], 
but I can research DeFi protocols, tokens, and blockchain technology.
```

---

## 📝 Document Maintenance

**Last Updated:** 2026-01-29
**Review Frequency:** Monthly

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**For questions or clarifications, refer to the README.md in this directory.**
