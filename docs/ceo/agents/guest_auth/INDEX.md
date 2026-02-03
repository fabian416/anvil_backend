# Guest Auth Agent - Complete Index

> **Project:** Anvil DeFi Chat - Guest Authentication Prompts
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **GUEST_AUTH** agent, Anvil's system for handling authentication requirements for guest users attempting restricted actions.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and components |
| **Implementation** | implementation.md | Code references and details |
| **Shortcuts** | shortcuts.md | Auth prompts and templates |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- Feature detection logic
- Knowledge integration
- LLM contextual generation
- Multi-language support

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Translation system
- Knowledge injector usage

---

### 3. [shortcuts.md](./shortcuts.md) - Auth Prompts
**Priority:** High | **User Interface**

Authentication prompts and templates:

**Key Contents:**
- Message templates by feature
- Multi-language examples
- CTA messages
- Fallback behavior

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Feature Detection | ✅ | Identify restricted action |
| Knowledge Integration | ✅ | Load relevant knowledge |
| Contextual Generation | ✅ | LLM-based messages |
| Multi-Language | ✅ | EN, ES, PT, ZH |
| Fallback Messages | ✅ | Static templates |
| Source Attribution | ✅ | Knowledge + LLM sources |

### Supported Features

| Feature | Detection | Template |
|---------|-----------|----------|
| Portfolio | ✅ | portfolio_access |
| Balance | ✅ | wallet_access |
| Activity | ✅ | transaction_history |
| Receive | ✅ | wallet_address |
| Buy | ✅ | buy_crypto |
| Send | ✅ | send_crypto |
| Lending | ✅ | execute_deposit |

---

## 📊 Key Metrics

### Performance Targets

- **Contextual (LLM)**: < 500ms
- **Fallback (static)**: < 50ms
- **Knowledge loading**: < 100ms

### Language Support

| Language | Code | Status |
|----------|------|--------|
| English | en | ✅ |
| Spanish | es | ✅ |
| Portuguese | pt | ✅ |
| Mandarin | zh | ✅ |

---

## 🔗 Related Specifications

### Agent Dependencies

- **KnowledgeInjector**: For feature-specific context
- **LLM Client**: Vertex AI for contextual generation
- **Translations**: i18n message templates

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/guest_auth_agent.py`

**Application Layer:**
- `src/app/application/guest/i18n/translations.py`
- `src/app/application/chat/services/knowledge_injector.py`

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_guest_auth_agent)

**Supervisor Routing:**
- `src/app/domain/services/agent_squad/guest_supervisor.py`

---

## 🚀 Guest Auth Journey

### Context-Aware Flow

```
1. Guest says: "Supply 1000 USDC to Morpho"
   → Guest supervisor routes to guest_auth

2. Detect knowledge intent
   → LENDING_MORPHO

3. Load knowledge
   → lending_morpho.json

4. Format knowledge context
   → Feature description, capabilities

5. Generate contextual message (LLM)
   → "To supply USDC to Morpho vaults..."

6. Add CTA
   → "👉 Sign Up Free"

7. Return response
   → Context-aware registration prompt
```

### Fallback Flow

```
1. Guest says: "my balance"
   → Guest supervisor routes to guest_auth

2. Knowledge loading fails (or not available)

3. Detect restricted feature
   → "balance"

4. Get static template
   → wallet_access template

5. Add CTA
   → "👉 Sign Up Free"

6. Return response
   → Static registration prompt
```

---

## 🔑 Critical Rules

### Guest-Only Agent

```python
# This agent is ONLY used in guest supervisor flow
# Authenticated users use the actual feature agents instead

# Guest supervisor routes to guest_auth for:
- Transaction actions (swap, send, lend, buy)
- Wallet queries (balance, portfolio, address)
- Transaction history
```

### CTA Format

```python
# Always end with CTA

message = f"{registration_message}\n\n👉 {cta}"

# CTA is localized:
# EN: "Sign Up Free"
# ES: "Regístrate Gratis"
# PT: "Cadastre-se Grátis"
# ZH: "免费注册"
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