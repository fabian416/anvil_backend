# Wallet Agent - Complete Index

> **Project:** Anvil DeFi Chat - Wallet Management
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **WALLET** agent, Anvil's wallet address display system for authenticated users.

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
- Application layer integration
- Infrastructure adapters
- Full address display requirement
- Balance-aware suggestions

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- User context extraction
- Wallet context building
- Response formatting

---

### 3. [shortcuts.md](./shortcuts.md) - Chat Integration
**Priority:** High | **User Interface**

Chat shortcut patterns and multi-language support:

**Key Contents:**
- Wallet query patterns
- Wallet vs Portfolio distinction
- Multi-language examples
- Supervisor routing

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Full Address Display | ✅ | Never truncates addresses |
| Primary Wallet Marking | ✅ | Shows which is primary |
| Multi-Wallet Support | ✅ | Lists all connected wallets |
| Balance-Aware Suggestions | ✅ | Context-based recommendations |
| Authentication Handling | ✅ | Guest user messaging |
| Source Attribution | ✅ | Database and LLM sources |

### Data Sources (✅ Complete)

| Source | Purpose | Status |
|--------|---------|--------|
| Anvil Database | Wallet info | ✅ Active |
| Vertex AI LLM | Response formatting | ✅ Active |

---

## 📊 Key Metrics

### Performance Targets

- **Context Extraction**: < 10ms
- **Context Building**: < 20ms
- **LLM Response**: < 800ms
- **Total Response**: < 1s

---

## 🔗 Related Specifications

### Other Agent Documentation

- **Portfolio Agent**: `/docs/ceo/agents/portfolio/` (balance/holdings)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (add funds)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (send to wallet)
- **Transaction History**: `/docs/ceo/agents/activity/` (activity)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/wallet_agent.py`

**Application Layer:**
- `src/app/application/chat/commands/send_message_with_supervisor.py`
- `src/app/application/chat/services/user_data_service.py`

**Domain Layer:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/enums/agent_type.py` (AgentType.WALLET)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_wallet_agent)

---

## 🚀 User Journey

### Authenticated User Flow

```
1. User says: "my wallet"
   → Supervisor routes to WalletAgent

2. WalletAgent extracts user context
   → Wallet address from conversation metadata

3. Build wallet context string
   → Full address, chain, provider

4. Get portfolio balance for suggestions
   → $0 → "buy crypto" suggestions
   → Funded → "swap", "earn yield" suggestions

5. LLM formats response
   → Concise, full address display

6. Return formatted wallet info
   → Address + suggestions
```

### Guest User Flow

```
1. User says: "my wallet"
   → Supervisor routes to WalletAgent

2. WalletAgent detects no authentication
   → user_context is None

3. Return auth required response
   → Explain how to sign in
```

---

## 🔑 Critical Rules

### Full Address Display

**NEVER truncate wallet addresses!**

```python
# ❌ WRONG - Never do this
address_display = f"{address[:6]}...{address[-4:]}"  # 0x742d...f44e

# ✅ CORRECT - Always show full address
address_display = f"`{address}`"  # 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
```

### Wallet vs Portfolio

| Query Type | Agent | Response |
|------------|-------|----------|
| Address queries | wallet | Full wallet address |
| Balance queries | portfolio | USD value, holdings |

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
