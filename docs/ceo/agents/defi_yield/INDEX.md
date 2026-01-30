# DeFi Yield Agent - Complete Index

> **Project:** Anvil DeFi Chat - Yield Optimization
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **DEFI_YIELD** agent, Anvil's yield farming and APY optimization system.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Query patterns and yield categories |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- DeFiLlama integration
- Yield pool fetching
- Risk score calculation
- APY formatting

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Protocol detection
- Response building

---

### 3. [shortcuts.md](./shortcuts.md) - Query Patterns
**Priority:** High | **User Interface**

Yield query patterns and categories:

**Key Contents:**
- Supported query types
- Yield vs swap distinction
- Protocol comparisons
- Risk-adjusted recommendations

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Yield Discovery | ✅ | Top APY opportunities |
| DeFiLlama Integration | ✅ | Real-time yield data |
| Protocol Filter | ✅ | Aave, Morpho, Compound, Curve |
| Risk Scoring | ✅ | 0-100 risk assessment |
| APY Breakdown | ✅ | Base + reward rates |
| IL Risk | ✅ | Impermanent loss flags |
| Source Attribution | ✅ | LLM + DeFiLlama |

### Supported Protocols (✅ Auto-Detected)

| Protocol | Detection | Status |
|----------|-----------|--------|
| Aave | "aave" | ✅ |
| Morpho | "morpho" | ✅ |
| Compound | "compound" | ✅ |
| Curve | "curve" | ✅ |

---

## 📊 Key Metrics

### Performance Targets

- **DeFiLlama API**: < 500ms
- **LLM Analysis**: < 800ms
- **Total Response**: < 1.5s

### Yield Data

- **Pools Fetched**: Top 10 by APY
- **Data Points**: APY, TVL, Risk, IL
- **Update Frequency**: Real-time

---

## 🔗 Related Specifications

### Agent Dependencies

- **Risk Analyzer**: Risk assessment for yield opportunities
- **Lending Workflow**: Execute deposits based on yield recommendations
- **Portfolio**: Allocation optimization with yield consideration

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/defi_yield_agent.py`

**External Clients:**
- `src/app/infrastructure/adapters/external/defillama_client.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_defi_yield_agent)

---

## 🚀 Yield Discovery Journey

### Query Flow

```
1. User says: "Best yield for USDC"
   → Supervisor routes to defi_yield

2. DefiYieldAgent detects no specific protocol
   → Fetch all yield pools

3. Fetch DeFiLlama data
   → /pools endpoint
   → Sort by APY (highest first)
   → Take top 10

4. Calculate risk scores
   → Based on APY level
   → Based on TVL size
   → Flag IL risk

5. Format markdown table
   → Protocol, Pool, Chain, APY, TVL, Risk, IL

6. LLM generates recommendations
   → Risk-adjusted suggestions
   → Protocol comparison

7. Build response with sources
   → Sources: LLM + DeFiLlama
```

### Combined Query Flow

```
1. User says: "Best yield for USDC" (with risk)
   → Supervisor creates 2 tasks:
     - defi_yield (no dependencies)
     - risk_analyzer (depends on defi_yield)

2. defi_yield executes first
   → Returns yield opportunities

3. risk_analyzer executes second
   → Adds detailed risk analysis

4. Results combined
   → Yield table + risk assessment
```

---

## 🔑 Critical Rules

### Yield vs Swap Distinction

```python
# CRITICAL: Don't confuse these!

# Yield queries → defi_yield
"yield", "APY", "yield farms", "lending rates"

# Swap queries → hunter_ai (NOT defi_yield!)
"swap rate", "exchange rate", "convert X to Y"

# Example of WRONG routing:
"best swap rate for ETH to USDC" → ❌ defi_yield
"best swap rate for ETH to USDC" → ✅ hunter_ai
```

### Response Requirements

```python
# MUST include real-time data table
# MUST provide specific APY percentages
# MUST NOT say "need real-time data"
# MUST NOT say "hypothetical"
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
