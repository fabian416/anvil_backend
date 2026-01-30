# Hunter AI Specification - Complete Index

> **Project:** Anvil DeFi Chat - Hunter AI Market Intelligence
> **Architecture:** Hexagonal (Clean Architecture)
> **Status:** ✅ Complete Implementation
> **Date:** 2026-01-29

---

## 📚 Document Overview

This specification suite contains comprehensive documentation for the **Hunter AI** agent, Anvil's market intelligence and price analysis specialist.

### Quick Navigation

| Category | Documents | Purpose |
|----------|-----------|---------|
| **Overview** | README.md, INDEX.md (this file) | Navigation and getting started |
| **Architecture** | architecture.md | System design and layers |
| **Implementation** | implementation.md | Code references and details |
| **Data Sources** | data_sources.md | External API integrations |
| **Shortcuts** | shortcuts.md | User interface patterns |

---

## 🏗️ Architecture Documents

### 1. [architecture.md](./architecture.md) - Hexagonal Architecture Design
**Priority:** Critical | **Read First**

Complete hexagonal architecture specification:

**Key Contents:**
- **Domain Layer**: AgentType.HUNTER_AI enum
- **Application Layer**: Supervisor routing integration
- **Infrastructure Layer**: HunterAIAgent implementation
- **External APIs**: CoinGecko, Hyperliquid integration

---

### 2. [implementation.md](./implementation.md) - Implementation Details
**Priority:** High | **Code Reference**

Detailed implementation with code locations:

**Key Contents:**
- File structure and locations
- Token extraction methods
- Swap pair detection
- LLM prompt engineering

---

### 3. [data_sources.md](./data_sources.md) - Data Sources
**Priority:** High | **API Reference**

External data source documentation:

**Key Contents:**
- CoinGecko API integration
- Hyperliquid Spot quotes
- Sentiment sources (RSS, Reddit, Twitter)
- Rate limits and caching

---

### 4. [shortcuts.md](./shortcuts.md) - Shortcut Configuration
**Priority:** High | **User Interface**

Configuration for Hunter AI shortcuts:

**Key Contents:**
- Pattern matching rules
- Multi-language support
- Agent routing configuration

---

## 🎯 Implementation Status

### Core Features (✅ Complete)

| Feature | Status | File |
|---------|--------|------|
| Hunter AI Agent | ✅ | hunter_ai_agent.py |
| CoinGecko Integration | ✅ | coingecko_client.py |
| Hyperliquid Integration | ✅ | hyperliquid_client.py |
| Token Extraction | ✅ | hunter_ai_agent.py |
| Swap Pair Detection | ✅ | hunter_ai_agent.py |
| Source Attribution | ✅ | hunter_ai_agent.py |

### Data Sources (Status)

| Source | Status | Type |
|--------|--------|------|
| CoinGecko | ✅ REAL | Prices & Market Data |
| Hyperliquid | ✅ REAL | Swap Quotes |
| RSS News | ✅ REAL | News Sentiment |
| Reddit | ⚠️ Fallback | Social Sentiment |
| Twitter | 🟡 Simulated | Social Sentiment |
| Discord | 🟡 Simulated | Social Sentiment |

### Supported Tokens (Sample)

| Category | Tokens | CoinGecko ID |
|----------|--------|--------------|
| Major | BTC, ETH, SOL | bitcoin, ethereum, solana |
| Stablecoins | USDC, USDT | usd-coin, tether |
| DeFi | AAVE, UNI, CRV | aave, uniswap, curve-dao-token |
| Meme | PEPE, TRUMP, DOGE | pepe, official-trump, dogecoin |

---

## 📊 Key Metrics

### Technical Metrics
- **Response Time**: <2s for price queries
- **API Rate Limits**: 10-50 calls/min (CoinGecko free tier)
- **Token Support**: 10,000+ via CoinGecko
- **Swap Quote Freshness**: 30 seconds (Hyperliquid)

### Accuracy Metrics
- **Price Accuracy**: Real-time from CoinGecko
- **Swap Rates**: Live from Hyperliquid or calculated
- **24h Change**: Accurate to 2 decimal places

---

## 🔗 Related Specifications

### Other Agent Documentation
- **Knowledge Agent**: DeFi explanations
- **Swap Workflow**: `/docs/ceo/agents/swap/` (if exists)
- **Lending Workflow**: `/docs/ceo/agents/lending/`
- **Transfer Workflow**: `/docs/ceo/agents/transfer/`

### Codebase Integration Points
- **Agent**: `src/app/infrastructure/adapters/agent_squad/agents/hunter_ai_agent.py`
- **CoinGecko Client**: `src/app/infrastructure/adapters/external/coingecko_client.py`
- **Hyperliquid Client**: `src/app/infrastructure/adapters/external/hyperliquid_client.py`
- **Supervisor**: `src/app/domain/services/agent_squad/authenticated_supervisor.py`

### Related Documentation
- **Data Sources Detail**: `/docs/HUNTER_AI_DATA_SOURCES.md`

---

## 🚀 Next Actions

1. **Documentation Complete** ✅
2. **Implementation Complete** ✅
3. **Testing Required**
   - Unit tests for token extraction
   - Integration tests for API calls
   - E2E tests for price queries

4. **Future Enhancements**
   - LunarCrush integration (social metrics)
   - Santiment integration (on-chain analytics)
   - CryptoPanic API (news aggregation)

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
