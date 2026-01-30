# Portfolio Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the shortcut patterns, multi-language support, and supervisor routing for the **PORTFOLIO** agent.

---

## Primary Patterns

### Portfolio Query Patterns

| Pattern | Example | Agent |
|---------|---------|-------|
| `my portfolio` | "my portfolio" | portfolio |
| `my holdings` | "show my holdings" | portfolio |
| `my balance` | "what's my balance" | portfolio |
| `portfolio value` | "what's my portfolio value" | portfolio |
| `total holdings` | "show total holdings" | portfolio |
| `what do I own` | "what crypto do I own" | portfolio |

### Analysis Patterns (Multi-Agent)

| Pattern | Example | Agents | Reason |
|---------|---------|--------|--------|
| `should I rebalance` | "should I rebalance my portfolio" | portfolio + hunter_ai | Analysis needed |
| `portfolio and price` | "my portfolio and price of BTC" | portfolio + hunter_ai | Parallel queries |
| `best yields and balance` | "best yields and my balance" | defi_yield + portfolio | Parallel queries |

### NOT Portfolio Agent

| Pattern | Example | Agent | Reason |
|---------|---------|-------|--------|
| `my wallet` | "show my wallet" | wallet | Address query |
| `wallet address` | "what's my wallet address" | wallet | Address query |
| `price of ETH` | "price of ETH" | hunter_ai | Price query |

---

## Multi-Language Examples

### English (en)

```
Primary Commands:
• "my portfolio"
• "my holdings"
• "my balance"
• "show my portfolio"
• "what do I own"
• "portfolio value"

Analysis Queries:
• "should I rebalance my portfolio"
• "is my portfolio well diversified"
• "analyze my holdings"
```

### Spanish (es)

```
Primary Commands:
• "mi portafolio"
• "mis tenencias"
• "mi saldo"
• "mostrar mi portafolio"
• "qué tengo"
• "valor del portafolio"

Analysis Queries:
• "debería rebalancear mi portafolio"
• "está bien diversificado mi portafolio"
• "analiza mis tenencias"
```

### Portuguese (pt)

```
Primary Commands:
• "meu portfólio"
• "minhas posições"
• "meu saldo"
• "mostrar meu portfólio"
• "o que eu tenho"
• "valor do portfólio"

Analysis Queries:
• "devo rebalancear meu portfólio"
• "meu portfólio está diversificado"
• "analise minhas posições"
```

### Chinese (zh)

```
Primary Commands:
• "我的投资组合"
• "我的持仓"
• "我的余额"
• "显示我的投资组合"
• "我有什么"
• "投资组合价值"

Analysis Queries:
• "我应该重新平衡吗"
• "我的投资组合多元化吗"
• "分析我的持仓"
```

---

## Supervisor Routing Configuration

### From authenticated_supervisor.py

```python
"""
4. PORTFOLIO (authenticated - REAL data):
   - "my portfolio", "my balance", "my holdings" → "portfolio" agent (returns REAL data)
   - "portfolio value", "total holdings" → "portfolio" agent

18. PORTFOLIO ANALYSIS (authenticated - use REAL data):
    - Portfolio rebalancing suggestions → "portfolio" + "hunter_ai"
    - Risk-adjusted recommendations → "portfolio" + "risk_analyzer"
    - "Should I rebalance my portfolio" → "portfolio" + "hunter_ai"
    - Allocation optimization → "portfolio" + "defi_yield"
"""
```

### Routing Examples

```python
# Simple queries → portfolio only
"my portfolio" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's real portfolio data","depends_on":[]}}]}}
"my balance" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's wallet balance","depends_on":[]}}]}}

# Parallel queries → multiple agents
"my portfolio and price of BTC" → {{"tasks":[
    {{"agent_type":"portfolio","task_description":"Get user's real portfolio data","depends_on":[]}},
    {{"agent_type":"hunter_ai","task_description":"Get current BTC price","depends_on":[]}}
]}}

"best yields and my balance" → {{"tasks":[
    {{"agent_type":"defi_yield","task_description":"Find best yield opportunities","depends_on":[]}},
    {{"agent_type":"portfolio","task_description":"Get user's wallet balance","depends_on":[]}}
]}}

# Sequential queries → depends_on
"I have 70% ETH and 30% BTC. Should I rebalance?" → {{"tasks":[
    {{"agent_type":"portfolio","task_description":"Analyze current portfolio allocation","depends_on":[]}},
    {{"agent_type":"hunter_ai","task_description":"Provide market-based rebalancing recommendation","depends_on":["portfolio"]}}
]}}
```

---

## Differentiation from Wallet Agent

### Key Distinction

| Query Type | Agent | Response |
|------------|-------|----------|
| **Balance/Holdings** | portfolio | USD values, token amounts, suggestions |
| **Wallet Address** | wallet | Wallet address (0x...) |

### Examples

```python
# Portfolio Agent
"my portfolio" → {{"agent_type":"portfolio"}}
"my balance" → {{"agent_type":"portfolio"}}
"my holdings" → {{"agent_type":"portfolio"}}
"what do I own" → {{"agent_type":"portfolio"}}

# Wallet Agent (NOT Portfolio)
"my wallet" → {{"agent_type":"wallet"}}
"wallet address" → {{"agent_type":"wallet"}}
"show my address" → {{"agent_type":"wallet"}}
```

---

## API Response Examples

### Authenticated - Empty Portfolio

```json
{
  "agent_message": {
    "content": "**Total Balance:** $0.00\n\n**🚀 Get Started:**\n\nYour portfolio is empty. Add funds to get started:\n\n• 💳 **Buy crypto** - Say \"buy crypto\" to purchase USDC\n• 📥 **Receive crypto** - Transfer tokens from another wallet\n\nOnce you have funds you can:\n• 🔄 **Swap** - Trade between cryptocurrencies\n• 💰 **Earn yield** - Deposit into DeFi protocols",
    "role": "assistant",
    "agent_type": "portfolio"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 120},
      {"agent_type": "portfolio", "duration_ms": 850}
    ],
    "sources": [
      {
        "source_type": "database",
        "source_name": "Anvil Database",
        "citation_text": "Your portfolio data from Anvil",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "LLM analysis",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Authenticated - Funded Portfolio

```json
{
  "agent_message": {
    "content": "**Portfolio Value:** $1,234.56\n**Token Count:** 4\n**Chains:** Base, Ethereum\n\n**Top Holdings:**\n- USDC: 500.00 ($500.00)\n- ETH: 0.25 ($450.00)\n- PURR: 10,000.00 ($234.56)\n- TRUMP: 500.00 ($50.00)\n\n**💡 What you can do:**\n• 💰 **Earn yield** - Say \"deposit USDC\" or \"compare USDC rates\"\n• 🔄 **Swap** - Say \"swap\" to trade between cryptocurrencies",
    "role": "assistant",
    "agent_type": "portfolio"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [...],
    "sources": [
      {"source_type": "database", "source_name": "Anvil Database", ...},
      {"source_type": "llm", "source_name": "gemini-2.0-flash", ...},
      {"source_type": "api", "source_name": "CoinGecko", ...}
    ]
  }
}
```

### Guest User

```json
{
  "agent_message": {
    "content": "To view your portfolio and holdings, please sign in or create an account.\n\nPortfolio features require authentication to access your wallet data.\n\n👉 **Sign up** to connect your wallet and view your holdings!",
    "role": "assistant",
    "agent_type": "portfolio"
  },
  "execute_data": null,
  "enrichment": {...}
}
```

---

## JSON Shortcut Configuration

For the `/api/v1/chat/shortcuts` endpoint:

```json
{
  "category": "portfolio",
  "shortcuts": [
    {
      "id": "portfolio_view",
      "label": "View portfolio",
      "patterns": {
        "en": ["my portfolio", "my holdings", "show portfolio"],
        "es": ["mi portafolio", "mis tenencias"],
        "pt": ["meu portfólio", "minhas posições"],
        "zh": ["我的投资组合", "我的持仓"]
      },
      "agent": "portfolio",
      "description": "View your crypto holdings and USD value"
    },
    {
      "id": "portfolio_balance",
      "label": "Check balance",
      "patterns": {
        "en": ["my balance", "portfolio value", "total value"],
        "es": ["mi saldo", "valor del portafolio"],
        "pt": ["meu saldo", "valor do portfólio"],
        "zh": ["我的余额", "投资组合价值"]
      },
      "agent": "portfolio",
      "description": "Check your total portfolio value in USD"
    }
  ]
}
```

---

## Context-Aware Suggestions

### Empty Portfolio Suggestions

```
• 💳 **Buy crypto** - Say "buy crypto" to purchase USDC
• 📥 **Receive crypto** - Transfer tokens from another wallet
```

### Small Balance Suggestions (<$100)

```
• 💰 **Earn yield** - Say "deposit USDC" or "compare USDC rates"
• 🔄 **Swap** - Say "swap" to trade between cryptocurrencies
• 💳 **Buy more** - Say "buy crypto" to add funds
```

### Funded Portfolio Suggestions (Has Stablecoins)

```
• 💰 **Earn yield** - Say "deposit USDC" or "compare USDC rates"
• 🔄 **Swap** - Say "swap" to trade between cryptocurrencies
```

### Funded Portfolio Suggestions (No Stablecoins)

```
• 🔄 **Swap** - Say "swap" to trade between cryptocurrencies
```

---

## Common User Flows

### Flow 1: Check Portfolio

```
User: "my portfolio"
→ Supervisor routes to portfolio
→ PortfolioAgent extracts user context
→ Builds context with holdings and suggestions
→ Returns formatted portfolio
```

### Flow 2: Portfolio Analysis

```
User: "should I rebalance my portfolio"
→ Supervisor creates 2 tasks:
   1. portfolio (analyze current allocation)
   2. hunter_ai (market recommendation, depends_on: portfolio)
→ PortfolioAgent runs first
→ HunterAI runs with portfolio context
→ Combined response with recommendation
```

### Flow 3: Parallel Query

```
User: "my portfolio and price of BTC"
→ Supervisor creates 2 parallel tasks:
   1. portfolio (get holdings)
   2. hunter_ai (get BTC price)
→ Both run simultaneously
→ Combined response
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Portfolio Agent Shortcuts**
