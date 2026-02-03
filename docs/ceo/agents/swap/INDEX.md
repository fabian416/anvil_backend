# Swap Workflow - Complete Index

> **Project:** Anvil DeFi Chat - Token Swap Operations
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **SWAP_WORKFLOW** agent, Anvil's multi-step token swap system using Hyperliquid Spot.

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
- Provider routing logic
- Balance awareness implementation

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Token configuration
- Error handling patterns

---

### 3. [shortcuts.md](./shortcuts.md) - Chat Integration
**Priority:** High | **User Interface**

Chat shortcut patterns and multi-language support:

**Key Contents:**
- Swap command patterns
- Token selection flow
- Multi-language examples
- Supervisor routing

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| Hyperliquid Integration | ✅ | Primary swap provider |
| Token Parsing | ✅ | LLM + regex extraction |
| Quote Fetching | ✅ | Real-time order book |
| Balance Awareness | ✅ | Funding recommendations |
| Token Selection | ✅ | Interactive numbered list |
| Unsupported Token Handling | ✅ | Clear error messages |
| Multi-language | ✅ | EN, ES, PT, ZH |
| Execute Data | ✅ | Frontend integration |

### Provider Support (✅ Complete)

| Provider | Token Type | Status |
|----------|------------|--------|
| Hyperliquid Spot | Meme tokens | ✅ Primary |
| 1inch | Major tokens (fallback) | ✅ Fallback |
| LiFi | Cross-chain | ✅ Fallback |
| CoinGecko | Price enrichment | ✅ Active |

### Balance Awareness (✅ Complete)

| Scenario | Behavior |
|----------|----------|
| Empty portfolio | Show funding recommendation, quote for reference |
| Insufficient balance | Warning message, suggest smaller amount |
| Sufficient balance | Proceed to execution with ✅ indicator |

---

## 📊 Key Metrics

### Performance Targets
- **Quote Fetch**: < 500ms
- **Total Response**: < 2s
- **Token Selection**: < 100ms

### Trading Metrics
- **Gas Fees**: $0 (Hyperliquid)
- **Trading Fee**: 0.02%
- **Slippage**: < 1% default

### Token Coverage
- **Meme Tokens**: 50+ supported
- **Quote Currency**: USDC only
- **Major Tokens**: Not supported (redirected)

---

## 🔗 Related Specifications

### Other Agent Documentation
- **Hunter AI**: `/docs/ceo/agents/hunter/` (price queries)
- **Buy Workflow**: For fiat on-ramp when user needs funds
- **Transfer Workflow**: `/docs/ceo/agents/transfer/`
- **Portfolio Agent**: Balance display

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/swap_workflow_agent.py`
- `src/app/infrastructure/adapters/external/hyperliquid_client.py`
- `src/app/infrastructure/adapters/external/oneinch_client.py`
- `src/app/infrastructure/adapters/external/lifi_client.py`
- `src/app/infrastructure/adapters/external/coingecko_client.py`

**Application Layer:**
- `src/app/application/chat/commands/send_message_with_supervisor.py`

**Domain Layer:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/enums/agent_type.py` (AgentType.SWAP_WORKFLOW)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_swap_workflow_agent)

**Knowledge Base:**
- `anvil_knowledge/features/swap.json`

---

## 🚀 Next Actions

1. **Documentation Complete** ✅
2. **Implementation Complete** ✅
3. **Testing**
   - Unit tests for token parsing
   - Integration tests with Hyperliquid
   - E2E tests for complete flows

4. **Future Enhancements**
   - Cross-chain meme token swaps
   - More DEX integrations
   - Advanced slippage controls
   - Limit orders

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
