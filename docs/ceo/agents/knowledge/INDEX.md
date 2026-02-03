# Knowledge Agent - Complete Index

> **Project:** Anvil DeFi Chat - Educational Knowledge Agent
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **KNOWLEDGE** agent, Anvil's educational specialist for DeFi, crypto, blockchain, and platform knowledge.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Chat integration patterns |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Domain layer components
- Application layer integration (KnowledgeInjector)
- Infrastructure adapters (KnowledgeAgent)
- Knowledge base structure
- Intent detection system

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Intent detection logic
- Knowledge context formatting
- LLM message building

---

### 3. [shortcuts.md](./shortcuts.md) - Chat Integration
**Priority:** High | **User Interface**

Chat shortcut patterns and multi-language support:

**Key Contents:**
- Query patterns by topic
- Multi-language examples
- Protocol comparison patterns
- Supervisor routing

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Intent Detection | ✅ | 15+ intent categories |
| Knowledge Injection | ✅ | Dynamic JSON loading |
| Protocol Comparisons | ✅ | Aave vs Compound, etc. |
| Multi-Language | ✅ | EN, ES, PT, ZH |
| Direct Answers | ✅ | No clarification requests |
| Off-Topic Handling | ✅ | Polite redirection |

### Knowledge Base Files (✅ Complete)

| File | Topics | Status |
|------|--------|--------|
| `overview.json` | Anvil platform | ✅ Active |
| `swap.json` | Token swaps | ✅ Active |
| `hunter_ai.json` | Hunter AI | ✅ Active |
| `ultra.json` | ULTRA arbitrage | ✅ Active |
| `portfolio.json` | Portfolio management | ✅ Active |
| `wallet.json` | Wallet management | ✅ Active |
| `lending_morpho.json` | Morpho lending | ✅ Active |
| `money_market.json` | Money market rates | ✅ Active |
| `gas_optimizer.json` | Gas optimization | ✅ Active |
| `risk_analyzer.json` | Risk analysis | ✅ Active |
| `shortcuts.json` | Command shortcuts | ✅ Active |

---

## 📊 Key Metrics

### Performance Targets

- **Intent Detection**: < 5ms
- **Knowledge Loading**: < 50ms (cached)
- **Context Formatting**: < 20ms
- **LLM Response**: < 1s
- **Total Response**: < 1.5s

---

## 🔗 Related Specifications

### Other Agent Documentation

- **Hunter AI**: `/docs/ceo/agents/hunter/` (market data)
- **ULTRA**: `/docs/ceo/agents/ultra/` (arbitrage)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (swap execution)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (lending execution)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/knowledge_agent.py`

**Application Layer:**
- `src/app/application/chat/services/knowledge_injector.py`
- `src/app/application/chat/services/knowledge_compressor.py`

**Domain Layer:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/services/agent_squad/guest_supervisor.py`
- `src/app/domain/enums/agent_type.py` (AgentType.KNOWLEDGE)

**Knowledge Base:**
- `anvil_knowledge/features/*.json` (11 files)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_knowledge_agent)

---

## 🚀 User Journey

### Educational Query Flow

```
1. User says: "What is DeFi?"
   → Supervisor routes to KnowledgeAgent

2. KnowledgeAgent detects intent
   → "general_question" for DeFi topics

3. Load KnowledgeInjector (lazy)
   → Singleton instance

4. Get relevant knowledge from JSON
   → Based on intent and keywords

5. Format knowledge as context
   → Structured text for LLM

6. Build LLM messages
   → System prompt + knowledge + user query

7. Call Vertex AI (gemini-2.0-flash)
   → Educational response

8. Return formatted response
   → With sources and metadata
```

### Protocol Comparison Flow

```
1. User says: "Aave vs Compound"
   → Supervisor routes to KnowledgeAgent

2. KnowledgeAgent detects intent
   → "defi_protocol" for comparisons

3. Build comparison message
   → CRITICAL: Provide comparison, don't ask

4. LLM generates detailed comparison
   → Pros/cons, features, recommendations

5. Return comparison response
   → Structured with sources
```

---

## 🔑 Critical Rules

### Always Answer Directly

```python
# ❌ WRONG - Never do this
"What would you like to know about DeFi or crypto?"

# ✅ CORRECT - Always answer directly
"DeFi (Decentralized Finance) is a financial system built on blockchain..."
```

### Language Matching

```python
# User asks in Spanish
"¿Qué es Anvil?"

# ✅ CORRECT - Respond in Spanish
"Anvil es una plataforma DeFi integral..."

# ❌ WRONG - Don't mix languages
"Anvil is a comprehensive DeFi platform..." (English)
```

### Terminology for Lending

```python
# ❌ WRONG - Spanish
"Anvil soporta préstamos..."  # préstamos = loans/borrowing

# ✅ CORRECT - Spanish
"Anvil soporta suministro de activos..."  # supply assets
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
