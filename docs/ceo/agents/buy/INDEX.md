# Buy Workflow - Complete Index

> **Project:** Anvil DeFi Chat - Fiat On-Ramp Operations
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **BUY_WORKFLOW** agent, Anvil's fiat-to-crypto on-ramp system using Privy SDK with MoonPay and Coinbase.

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
- Privy SDK integration
- USDC-only constraint handling

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- Amount parsing logic
- Error handling patterns

---

### 3. [shortcuts.md](./shortcuts.md) - Chat Integration
**Priority:** High | **User Interface**

Chat shortcut patterns and multi-language support:

**Key Contents:**
- Buy command patterns
- Amount formats
- Multi-language examples
- Supervisor routing

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| USDC Purchase | ✅ | Only supported crypto |
| Amount Parsing | ✅ | Multiple formats ($100, 100 dollars, €50) |
| Fiat Detection | ✅ | USD, EUR, GBP, CAD, AUD |
| Privy Integration | ✅ | MoonPay + Coinbase |
| Smart Redirection | ✅ | Suggests USDC for unsupported cryptos |
| Multi-language | ✅ | EN, ES, PT, ZH |
| Execute Data | ✅ | Frontend integration |
| Restart Detection | ✅ | Handles mid-flow restarts |

### Payment Provider Support (✅ Complete)

| Provider | Card | Apple Pay | Google Pay | Bank Transfer |
|----------|------|-----------|------------|---------------|
| MoonPay | ✅ | ✅ | ✅ | ❌ |
| Coinbase | ✅ | ❌ | ❌ | ✅ |

### Crypto Support

| Crypto | Direct Purchase | Workaround |
|--------|-----------------|------------|
| USDC | ✅ Yes | - |
| ETH | ❌ No | Buy USDC → Swap (not available on Hyperliquid) |
| BTC | ❌ No | Buy USDC → Swap (not available on Hyperliquid) |
| SOL | ❌ No | Buy USDC → Swap (not available on Hyperliquid) |
| Meme Tokens | ❌ No | Buy USDC → Swap on Hyperliquid Spot |

---

## 📊 Key Metrics

### Performance Targets
- **Parse Request**: < 100ms
- **Validation**: < 50ms
- **Total Response**: < 500ms

### Business Metrics
- **Minimum Purchase**: $30 USD
- **Maximum Purchase**: Provider-dependent
- **Supported Currencies**: 5 (USD, EUR, GBP, CAD, AUD)

---

## 🔗 Related Specifications

### Other Agent Documentation
- **Swap Workflow**: `/docs/ceo/agents/swap/` (swap USDC for meme tokens)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (send purchased crypto)
- **Portfolio Agent**: View purchased assets
- **Wallet Agent**: Check balance

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/workflows/buy_workflow_agent.py`

**Application Layer:**
- `src/app/application/chat/commands/send_message_with_supervisor.py`

**Domain Layer:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/enums/agent_type.py` (AgentType.BUY_WORKFLOW)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_buy_workflow_agent)

---

## 🚀 User Journey

### Typical User Flow

```
1. User says: "buy crypto" or "buy $100"
   → BuyWorkflowAgent activated

2. Agent defaults to USDC (only option)
   → Asks for amount if not provided

3. User provides amount: "100"
   → Agent shows purchase review with execute_data

4. Frontend displays Privy modal
   → User completes payment via MoonPay/Coinbase

5. USDC arrives in wallet
   → User can now swap for meme tokens

6. User says: "swap 100 USDC to PURR"
   → SwapWorkflowAgent handles meme token swap
```

### Unsupported Crypto Flow

```
1. User says: "buy ETH"
   → Agent detects unsupported crypto

2. Agent shows USDC-only message
   → Explains buy USDC then swap strategy

3. User provides amount: "$100"
   → Agent proceeds with USDC purchase

4. After purchase, user can:
   → Swap USDC for meme tokens on Hyperliquid
   → Note: ETH/BTC not available on Hyperliquid Spot
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
