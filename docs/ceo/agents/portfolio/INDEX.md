# Portfolio Agent - Complete Index

> **Project:** Anvil DeFi Chat - Portfolio Management
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **PORTFOLIO** agent, Anvil's core portfolio analysis and optimization system.

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
- Data source integration
- Context-aware suggestions

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Core classes and methods
- User context extraction
- CoinGecko integration
- Response formatting

---

### 3. [shortcuts.md](./shortcuts.md) - Chat Integration
**Priority:** High | **User Interface**

Chat shortcut patterns and multi-language support:

**Key Contents:**
- Portfolio query patterns
- Balance query patterns
- Multi-language examples
- Supervisor routing

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | Description |
|---------|--------|-------------|
| View Holdings | ✅ | List tokens with balances |
| Portfolio Value | ✅ | Total USD value |
| Real-time Prices | ✅ | CoinGecko integration |
| Balance-Aware Suggestions | ✅ | Context-based recommendations |
| Multi-Chain Support | ✅ | Aggregate across chains |
| Guest User Handling | ✅ | Authentication requirement |
| Source Attribution | ✅ | Database, API, LLM sources |

### Data Sources (✅ Complete)

| Source | Purpose | Status |
|--------|---------|--------|
| On-Chain RPC | Token balances | ✅ Active |
| CoinGecko API | USD prices | ✅ Active |
| Anvil Database | Portfolio snapshots | ✅ Active |
| Vertex AI LLM | Response formatting | ✅ Active |

### Analytics Capabilities (✅ Complete)

| Capability | Status | Model |
|------------|--------|-------|
| MPT Optimization | ✅ | gemini-2.0-flash |
| Risk Analysis | ✅ | gemini-2.0-flash |
| Rebalancing Suggestions | ✅ | gemini-2.0-flash |
| Correlation Analysis | ✅ | gemini-2.0-flash |

---

## 📊 Key Metrics

### Performance Targets

- **Context Building**: < 50ms
- **CoinGecko Fetch**: < 300ms
- **LLM Response**: < 1s
- **Total Response**: < 1.5s

### Data Accuracy

- **Balance Precision**: Real-time on-chain
- **Price Precision**: CoinGecko (30s cache)
- **USD Calculation**: token_amount × current_price

---

## 🔗 Related Specifications

### Other Agent Documentation

- **Wallet Agent**: For wallet address (not balance)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (add funds)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (trade tokens)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (earn yield)
- **Hunter AI**: `/docs/ceo/agents/hunter/` (price analysis)

### Codebase Integration Points

**Infrastructure Layer:**
- `src/app/infrastructure/adapters/agent_squad/agents/portfolio_agent.py`
- `src/app/infrastructure/adapters/external/coingecko_client.py`

**Application Layer:**
- `src/app/application/chat/commands/send_message_with_supervisor.py`
- `src/app/application/chat/services/user_data_service.py`

**Domain Layer:**
- `src/app/domain/services/agent_squad/authenticated_supervisor.py`
- `src/app/domain/enums/agent_type.py` (AgentType.PORTFOLIO)

**DI Configuration:**
- `src/app/setup/ioc/agent_squad_infrastructure.py` (provide_portfolio_agent)

---

## 🚀 User Journey

### Authenticated User Flow

```
1. User says: "my portfolio"
   → Supervisor routes to PortfolioAgent

2. PortfolioAgent extracts user context
   → Wallet address, portfolio data from conversation context

3. Build portfolio context string
   → Holdings, USD values, suggestions based on balance

4. Fetch real-time prices (optional)
   → CoinGecko for mentioned tokens

5. LLM formats response
   → Concise, actionable format

6. Return formatted portfolio
   → Balance, holdings, suggestions
```

### Guest User Flow

```
1. User says: "my portfolio"
   → Supervisor routes to PortfolioAgent

2. PortfolioAgent detects no authentication
   → is_authenticated = False

3. Return authentication prompt
   → "Please sign in to view your portfolio"
```

---

## 📈 Context-Aware Suggestions

### Suggestion Matrix

| Portfolio State | Total Value | Suggestions |
|-----------------|-------------|-------------|
| **Empty** | $0 | "buy crypto", "receive crypto" |
| **Small** | < $100 | "earn yield", "swap", "buy more" |
| **Medium** | $100 - $10,000 | "earn yield", "swap" |
| **Large** | > $10,000 | "earn yield", "swap", "rebalance" |

### Stablecoin Detection

If user has USDC, USDT, or DAI:
- Suggest "deposit USDC" or "compare rates" for yield

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
