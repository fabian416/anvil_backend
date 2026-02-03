# Portfolio Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **PORTFOLIO** agent provides portfolio analysis, optimization, and rebalancing recommendations for authenticated users on Anvil. It displays real wallet holdings with USD values and provides context-aware suggestions based on the user's balance.

### Key Differentiators

- **Real Data**: Uses actual on-chain portfolio data for authenticated users
- **Balance-Aware Suggestions**: Different recommendations for empty vs. funded portfolios
- **CoinGecko Integration**: Real-time token prices for accurate valuations
- **Modern Portfolio Theory**: MPT-based optimization recommendations
- **Multi-Chain Support**: Aggregates holdings across chains

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Chat patterns and multi-language support |

---

## Quick Start

### For Developers

1. Read `architecture.md` for the hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for chat integration

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test with empty and funded portfolios
3. Verify context-aware suggestions

---

## Key Features

### 1. Portfolio Display

| Scenario | Response |
|----------|----------|
| **Empty Portfolio** | Shows $0 balance with "buy crypto" and "receive crypto" suggestions |
| **Small Balance (<$100)** | Shows holdings + suggests "buy more", "swap", "earn yield" |
| **Funded Portfolio** | Shows holdings + suggests "swap", "earn yield" |

### 2. Data Sources

| Source | Data | Status |
|--------|------|--------|
| **On-Chain RPC** | Token balances, native token | ✅ Active |
| **CoinGecko API** | USD prices, 24h changes | ✅ Active |
| **Anvil Database** | Portfolio snapshots | ✅ Active |

### 3. Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| **View Holdings** | List tokens with balances and USD values | ✅ Complete |
| **Portfolio Value** | Total USD value across all holdings | ✅ Complete |
| **Top Holdings** | Ranked list of largest positions | ✅ Complete |
| **Real-time Prices** | CoinGecko integration for current prices | ✅ Complete |
| **MPT Optimization** | Modern Portfolio Theory recommendations | ✅ Complete |
| **Rebalancing** | Suggested trades to optimize allocation | ✅ Complete |
| **Risk Analysis** | Volatility, correlation, Sharpe ratio | ✅ Complete |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → PortfolioAgent
    ↓ (Data Sources)
External Systems
    - On-Chain RPC (balances)
    - CoinGecko API (prices)
    - Anvil Database (snapshots)
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PORTFOLIO AGENT FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "my portfolio"                                       │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: portfolio      │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    PortfolioAgent       │                               │
│  │                         │                               │
│  │  1. Extract user context│ → Wallet, portfolio data      │
│  │  2. Build context string│ → Holdings, suggestions       │
│  │  3. Fetch prices        │ → CoinGecko API               │
│  │  4. LLM enhancement     │ → Format response             │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    Formatted Response   │                               │
│  │  - Total balance        │                               │
│  │  - Token holdings       │                               │
│  │  - Suggestions          │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules

```python
# From authenticated_supervisor.py

4. PORTFOLIO (authenticated - REAL data):
   - "my portfolio", "my balance", "my holdings" → "portfolio" agent
   - "portfolio value", "total holdings" → "portfolio" agent

18. PORTFOLIO ANALYSIS (authenticated - use REAL data):
    - Portfolio rebalancing suggestions → "portfolio" + "hunter_ai"
    - Risk-adjusted recommendations → "portfolio" + "risk_analyzer"
    - "Should I rebalance my portfolio" → "portfolio" + "hunter_ai"
    - Allocation optimization → "portfolio" + "defi_yield"
```

### Routing Examples

| User Query | Agent(s) | Reason |
|------------|----------|--------|
| "my portfolio" | portfolio | Holdings query |
| "my balance" | portfolio | Balance query |
| "my holdings" | portfolio | Holdings query |
| "portfolio value" | portfolio | Value query |
| "should I rebalance" | portfolio + hunter_ai | Analysis query |
| "my wallet" | wallet | Wallet address query |

---

## Example Conversations

### Empty Portfolio

```
User: "my portfolio"

Agent:
**Total Balance:** $0.00

**🚀 Get Started:**

Your portfolio is empty. Add funds to get started:

• 💳 **Buy crypto** - Say "buy crypto" to purchase USDC with card/Apple Pay/Google Pay
• 📥 **Receive crypto** - Transfer tokens from another wallet (ask "my wallet address" for your address)

Once you have funds you can:
• 🔄 **Swap** - Trade between cryptocurrencies
• 💰 **Earn yield** - Deposit into DeFi protocols
```

### Funded Portfolio

```
User: "my portfolio"

Agent:
**Portfolio Value:** $1,234.56
**Token Count:** 4
**Chains:** Base, Ethereum

**Top Holdings:**
- USDC: 500.00 ($500.00)
- ETH: 0.25 ($450.00)
- PURR: 10,000.00 ($234.56)
- TRUMP: 500.00 ($50.00)

**💡 What you can do:**
• 💰 **Earn yield** - Say "deposit USDC" or "compare USDC rates" to earn interest
• 🔄 **Swap** - Say "swap" to trade between cryptocurrencies
```

### Small Balance Portfolio

```
User: "my balance"

Agent:
**Portfolio Value:** $45.00
**Token Count:** 1

**Top Holdings:**
- USDC: 45.00 ($45.00)

**💡 What you can do:**
• 💰 **Earn yield** - Say "deposit USDC" or "compare USDC rates" to earn interest
• 🔄 **Swap** - Say "swap" to trade between cryptocurrencies
• 💳 **Buy more** - Say "buy crypto" to add funds
```

### Portfolio Analysis Request

```
User: "Should I rebalance my portfolio?"

Agent:
Based on your current portfolio:

**Current Allocation:**
- ETH: 60% ($600)
- USDC: 30% ($300)
- PURR: 10% ($100)

**Analysis:**
- Your portfolio is moderately diversified
- High exposure to ETH (volatile asset)
- USDC provides stability

**Recommendation:**
Consider reducing ETH to 40-50% if you want lower volatility.
You could:
• 🔄 **Swap 10-20% of ETH to USDC** for more stability
• 💰 **Deposit USDC to earn yield** (currently ~4% APY on Aave)
```

---

## Authentication Requirement

The Portfolio agent **requires authentication** to function properly:

| User Type | Behavior |
|-----------|----------|
| **Authenticated** | Shows real portfolio data with holdings and USD values |
| **Guest** | Informs user to sign in to view portfolio |

### Guest User Response

```
User: "my portfolio"

Agent:
To view your portfolio and holdings, please sign in or create an account.

Portfolio features require authentication to access your wallet data.

👉 **Sign up** to connect your wallet and view your holdings!
```

---

## Supported Languages

| Language | Portfolio Query | Balance Query |
|----------|-----------------|---------------|
| English | "my portfolio", "my holdings" | "my balance" |
| Spanish | "mi portafolio", "mis tenencias" | "mi saldo" |
| Portuguese | "meu portfólio", "minhas posições" | "meu saldo" |
| Chinese | "我的投资组合", "我的持仓" | "我的余额" |

---

## Configuration

### Default Parameters

```python
# From portfolio_agent.py

# LLM Configuration
model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.3           # Balanced (analytical)
max_tokens = 2000

# Data Sources
- CoinGecko for real-time prices
- On-chain RPC for balances
- Anvil database for snapshots
```

### Response Structure

```python
AgentResponse(
    content="Portfolio formatted response...",
    agent_type=AgentType.PORTFOLIO,
    tools_used=["llm_gateway", "coingecko_api", "portfolio_repository"],
    sources=[
        SourceInfo(source_type="database", source_name="Anvil Database", ...),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="api", source_name="CoinGecko", ...),
    ],
    metadata={
        "tokens_used": 450,
        "latency_ms": 320,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
        "is_authenticated": True,
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] Empty portfolio context building
- [ ] Funded portfolio context building
- [ ] User context extraction
- [ ] CoinGecko price fetching
- [ ] System prompt selection (auth vs guest)

### Integration Tests
- [ ] Complete portfolio query flow
- [ ] Real-time price integration
- [ ] Multi-chain aggregation
- [ ] Source attribution

### E2E Tests
- [ ] Authenticated user flow
- [ ] Guest user rejection
- [ ] Balance-aware suggestions
- [ ] Portfolio analysis with hunter_ai

---

## Related Documentation

- **Wallet Agent**: `/docs/ceo/agents/wallet/` (wallet address, not balance)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (add funds)
- **Swap Workflow**: `/docs/ceo/agents/swap/` (trade tokens)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (earn yield)
- **Hunter AI**: `/docs/ceo/agents/hunter/` (price queries, analysis)

---

## Differentiation from Wallet Agent

| Query | Agent | Response |
|-------|-------|----------|
| "my portfolio" | portfolio | Holdings, USD values, suggestions |
| "my balance" | portfolio | Total USD value |
| "my wallet" | wallet | Wallet address only |
| "my wallet address" | wallet | Full wallet address |

**Key Rule**: Portfolio shows **balances and value**, Wallet shows **address only**.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added balance-aware suggestions |
| 1.0 | 2026-01-29 | Added CoinGecko integration |

---

**End of Portfolio Agent Specification**
