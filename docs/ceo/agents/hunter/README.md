# Hunter AI Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete Implementation
**Author**: Claude Code (Senior Python Backend Engineer)

---

## Overview

This directory contains comprehensive documentation for the **Hunter AI** agent, Anvil's market intelligence specialist providing:

- **Real-time price data** from CoinGecko API
- **Swap rate quotes** via Hyperliquid Spot
- **Market sentiment analysis** (Twitter, Reddit, Discord, News)
- **Technical analysis** and price predictions
- **Fear & Greed Index** interpretation
- **Multi-token support** (10,000+ cryptocurrencies)

---

## Document Structure

### 1. [`architecture.md`](./architecture.md)

**Purpose**: Complete hexagonal architecture design for Hunter AI

**Contents**:
- Domain layer integration
- Data source adapters
- LLM integration
- Source attribution

### 2. [`implementation.md`](./implementation.md)

**Purpose**: Implementation details and code references

**Contents**:
- File locations and structure
- Key methods and classes
- Token extraction logic
- API integration

### 3. [`data_sources.md`](./data_sources.md)

**Purpose**: External data source documentation

**Contents**:
- CoinGecko integration
- Hyperliquid Spot quotes
- RSS news feeds
- Social sentiment sources

### 4. [`shortcuts.md`](./shortcuts.md)

**Purpose**: Shortcut configuration for Hunter AI intents

**Contents**:
- Pattern matching
- Multi-language support
- Agent routing

---

## Quick Start

### For Developers

1. **Read the architecture** (`architecture.md`) to understand the design
2. **Review data sources** (`data_sources.md`) for API integrations
3. **Check implementation** (`implementation.md`) for code locations

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test price accuracy against live CoinGecko data
3. Verify multi-token support

---

## Key Features

### 1. Real-Time Price Data

| Feature | Source | Status |
|---------|--------|--------|
| Token Prices | CoinGecko | ✅ Live |
| 24h Change | CoinGecko | ✅ Live |
| Market Cap | CoinGecko | ✅ Live |
| Volume | CoinGecko | ✅ Live |
| 7-Day Chart | CoinGecko | ✅ Live |

### 2. Swap Rate Quotes

| Feature | Source | Status |
|---------|--------|--------|
| Hyperliquid Spot | Hyperliquid API | ✅ Live |
| Calculated Rates | CoinGecko Prices | ✅ Live |
| Price Impact | Hyperliquid | ✅ Live |

### 3. Sentiment Analysis

| Source | Status | Type |
|--------|--------|------|
| CoinGecko | ✅ REAL | Prices & Market Data |
| RSS News | ✅ REAL | News Sentiment |
| Reddit | ⚠️ Fallback | Social Sentiment |
| Twitter | 🟡 Simulated | Social Sentiment |
| Discord | 🟡 Simulated | Social Sentiment |

### 4. Supported Tokens

| Category | Examples | Count |
|----------|----------|-------|
| Major Tokens | BTC, ETH, SOL, AVAX | 20+ |
| Stablecoins | USDC, USDT, DAI | 5+ |
| DeFi Tokens | AAVE, UNI, CRV, LINK | 15+ |
| Meme Tokens | PEPE, TRUMP, DOGE, SHIB | 20+ |

---

## Architecture Principles

### Hexagonal Architecture (Clean Architecture)

```
Domain Layer (AgentType.HUNTER_AI)
    ↓
Application Layer (Supervisor Routing)
    ↓
Infrastructure Layer (HunterAIAgent)
    ↓
External APIs (CoinGecko, Hyperliquid)
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      HunterAIAgent                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ CoinGecko       │  │ Hyperliquid     │  │ LLM Client  │ │
│  │ (Prices)        │  │ (Swap Quotes)   │  │ (Analysis)  │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │        │
│           ▼                    ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │      Context Aggregation: Market Data + Quotes          ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                              │
│                              ▼                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Response: Prices + Analysis + Sources                   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Routing Configuration

### Supervisor Routing Rules

```
13. PRICE/MARKET DATA:
    - Token prices → "hunter_ai"
    - Gas prices → "gas_optimizer"
    - Market sentiment → "hunter_ai"
    
16. ADVANCED MARKET ANALYSIS:
    - Historical patterns, bull/bear market cycles → "hunter_ai"
    - Market regime detection, cycle analysis → "hunter_ai"
    - Correlation analysis between tokens → "hunter_ai"
    - Liquidity depth, order book analysis → "hunter_ai"
    - Whale activity, large transactions → "hunter_ai"
```

### Example Mappings

| User Query | Agent | Description |
|------------|-------|-------------|
| "price of ETH" | hunter_ai | Get current ETH price |
| "BTC and ETH prices" | hunter_ai | Multiple token prices |
| "best swap rate ETH to USDC" | hunter_ai | Swap rate information |
| "market sentiment for ETH" | hunter_ai | Sentiment analysis |
| "whale activity for BTC" | hunter_ai | Large transaction analysis |

---

## Example Conversations

### Price Query

```
User: "What's the price of ETH?"

Agent:
📊 **ETH Market Data**

**Current Price:** $2,988.55
**24h Change:** -0.83%
**Market Cap:** $360.75B
**24h Volume:** $21.95B
**7-Day High:** $3,120.00
**7-Day Low:** $2,850.00

Sources:
- CoinGecko API (real-time)
```

### Multi-Token Query

```
User: "Show me BTC and ETH prices"

Agent:
📊 **Market Overview**

**BITCOIN:**
- Current Price: $92,619.00
- 24h Change: +1.25%
- Market Cap: $1.82T

**ETHEREUM:**
- Current Price: $2,988.55
- 24h Change: -0.83%
- Market Cap: $360.75B

Sources:
- CoinGecko API (real-time)
```

### Swap Rate Query

```
User: "Best swap rate for 1 ETH to USDC"

Agent:
🔄 **Swap Quote: 1 ETH → USDC**

**Via Hyperliquid Spot:**
- You receive: 2,988.55 USDC
- Rate: 1 ETH = $2,988.55 USDC
- Spread: 0.05 bps
- Zero gas fees

Quote valid for ~30 seconds.

Sources:
- Hyperliquid API (real-time)
```

---

## API Rate Limits

| API | Free Tier | Recommended |
|-----|-----------|-------------|
| CoinGecko | 10-50 calls/min | Use bulk endpoints |
| Hyperliquid | Unlimited | Standard usage |

---

## Testing Checklist

### Unit Tests
- [ ] Token extraction from messages
- [ ] Swap pair extraction
- [ ] Price formatting

### Integration Tests
- [ ] CoinGecko API calls
- [ ] Hyperliquid quote fetching
- [ ] Multi-token bulk pricing

### E2E Tests
- [ ] Complete price query flow
- [ ] Swap rate query flow
- [ ] Sentiment analysis flow

---

## Related Documentation

- **Data Sources Detail**: See [docs/HUNTER_AI_DATA_SOURCES.md](/docs/HUNTER_AI_DATA_SOURCES.md)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (if exists)
- **Knowledge Agent**: Handles DeFi explanations
- **Lending Workflow**: `/docs/ceo/agents/lending/`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**End of Hunter AI Specification**
