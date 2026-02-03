# Wallet Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the shortcut patterns, multi-language support, and supervisor routing for the **WALLET** agent.

---

## Primary Patterns

### Wallet Query Patterns

| Pattern | Example | Agent |
|---------|---------|-------|
| `my wallet` | "my wallet" | wallet |
| `my wallets` | "show my wallets" | wallet |
| `wallet address` | "what's my wallet address" | wallet |
| `show wallet` | "show my wallet" | wallet |
| `connected wallets` | "list connected wallets" | wallet |
| `wallet info` | "wallet info" | wallet |

### NOT Wallet Agent (Portfolio Instead)

| Pattern | Example | Agent | Reason |
|---------|---------|-------|--------|
| `my balance` | "my balance" | portfolio | Balance query |
| `my portfolio` | "my portfolio" | portfolio | Holdings query |
| `my holdings` | "my holdings" | portfolio | Holdings query |
| `portfolio value` | "portfolio value" | portfolio | Value query |

---

## Multi-Language Examples

### English (en)

```
Primary Commands:
• "my wallet"
• "my wallets"
• "show my wallet address"
• "wallet info"
• "connected wallets"
• "list wallets"

Response:
• Shows full wallet address
• Includes balance-aware suggestions
```

### Spanish (es)

```
Primary Commands:
• "mi cartera"
• "mis carteras"
• "mostrar mi dirección de cartera"
• "info de cartera"
• "carteras conectadas"

Response:
• Muestra la dirección completa
• Incluye sugerencias basadas en el saldo
```

### Portuguese (pt)

```
Primary Commands:
• "minha carteira"
• "minhas carteiras"
• "mostrar meu endereço de carteira"
• "info da carteira"
• "carteiras conectadas"

Response:
• Mostra o endereço completo
• Inclui sugestões baseadas no saldo
```

### Chinese (zh)

```
Primary Commands:
• "我的钱包"
• "我的钱包们"
• "显示我的钱包地址"
• "钱包信息"
• "已连接的钱包"

Response:
• 显示完整地址
• 包括基于余额的建议
```

---

## Supervisor Routing Configuration

### From authenticated_supervisor.py

```python
"""
2. WALLET QUERIES (authenticated - REAL data):
   - "my wallets", "connected wallets", "wallet address" → "wallet" agent (REAL wallet data)
   - "wallet info", "list wallets", "show wallets" → "wallet" agent
"""
```

### Routing Examples

```python
# Wallet queries → wallet agent
"my wallets" → {{"tasks":[{{"agent_type":"wallet","task_description":"Show user's connected wallets"}}]}}
"show my wallet address" → {{"tasks":[{{"agent_type":"wallet","task_description":"Display user's wallet addresses"}}]}}

# Balance queries → portfolio agent (NOT wallet)
"my balance" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's wallet balance"}}]}}
"my portfolio" → {{"tasks":[{{"agent_type":"portfolio","task_description":"Get user's real portfolio data"}}]}}
```

---

## Wallet vs Portfolio Distinction

### Key Difference

| Query Type | Agent | Response Content |
|------------|-------|------------------|
| **Address queries** | wallet | Full wallet address (0x...) |
| **Balance queries** | portfolio | USD value, token holdings |

### Routing Decision Tree

```
User Query
    │
    ├── Contains "wallet" or "address"? 
    │       ├── YES → wallet agent (show address)
    │       └── NO ↓
    │
    ├── Contains "balance", "portfolio", "holdings"?
    │       ├── YES → portfolio agent (show balance)
    │       └── NO ↓
    │
    └── Other → depends on context
```

### Examples

```python
# WALLET agent (address queries)
"my wallet" → wallet
"wallet address" → wallet
"show wallets" → wallet
"connected wallets" → wallet

# PORTFOLIO agent (balance queries)
"my balance" → portfolio
"my portfolio" → portfolio
"my holdings" → portfolio
"what do I own" → portfolio
"portfolio value" → portfolio
```

---

## API Response Examples

### Authenticated - Single Wallet (Empty Balance)

```json
{
  "agent_message": {
    "content": "**Your Wallet:**\n`0x742d35Cc6634C0532925a3b844Bc454e4438f44e`\n\n**🚀 Get Started:**\nYour wallet is ready! Add funds to start using Anvil:\n• 💳 Say **\"buy crypto\"** to purchase USDC with card/Apple Pay\n• 📥 Transfer crypto from another wallet to the address above",
    "role": "assistant",
    "agent_type": "wallet"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 100},
      {"agent_type": "wallet", "duration_ms": 650}
    ],
    "sources": [
      {
        "source_type": "database",
        "source_name": "Anvil Database",
        "citation_text": "Your wallet data from Anvil",
        "relevance_score": 1.0
      },
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "LLM formatting",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Authenticated - Funded Balance

```json
{
  "agent_message": {
    "content": "**Your Wallet:**\n`0x742d35Cc6634C0532925a3b844Bc454e4438f44e`\n\n**💰 Balance:** $1,234.56\n\n**💡 What you can do:**\n• 🔄 **Swap** - Trade between different cryptocurrencies\n• 💰 **Earn yield** - Deposit to DeFi protocols\n• 📊 **Portfolio** - Say \"my portfolio\" for detailed holdings",
    "role": "assistant",
    "agent_type": "wallet"
  },
  "execute_data": null,
  "enrichment": {...}
}
```

### Authenticated - Multi-Wallet

```json
{
  "agent_message": {
    "content": "**Connected Wallets: 2**\n\n**Wallet 1 (PRIMARY):**\n  - Address: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`\n  - Chain: Base\n\n**Wallet 2:**\n  - Address: `0x1234567890abcdef1234567890abcdef12345678`\n  - Chain: Ethereum\n  - Provider: External\n\n**💰 Balance:** $1,234.56\n\n**💡 What you can do:**\n• 🔄 **Swap** - Trade between different cryptocurrencies\n• 💰 **Earn yield** - Deposit to DeFi protocols",
    "role": "assistant",
    "agent_type": "wallet"
  },
  "execute_data": null,
  "enrichment": {...}
}
```

### Guest User

```json
{
  "agent_message": {
    "content": "**Wallet Access Requires Authentication**\n\nTo view your wallet information, balances, and connected addresses, you need to sign in to your Anvil account.\n\n**How to Connect:**\n1. Click \"Sign In\" or \"Connect Wallet\" in the app\n2. Choose your preferred method (email, social, or wallet)\n3. Once connected, I can show you:\n   - All your connected wallets\n   - Balances across chains\n   - Transaction history\n   - Portfolio overview\n\nWould you like me to help you with something else, or are you ready to sign in?",
    "role": "assistant",
    "agent_type": "wallet"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [...],
    "sources": [...]
  }
}
```

---

## JSON Shortcut Configuration

For the `/api/v1/chat/shortcuts` endpoint:

```json
{
  "category": "wallet",
  "shortcuts": [
    {
      "id": "wallet_address",
      "label": "My wallet",
      "patterns": {
        "en": ["my wallet", "wallet address", "show wallet"],
        "es": ["mi cartera", "dirección de cartera"],
        "pt": ["minha carteira", "endereço da carteira"],
        "zh": ["我的钱包", "钱包地址"]
      },
      "agent": "wallet",
      "description": "View your connected wallet address"
    },
    {
      "id": "list_wallets",
      "label": "List wallets",
      "patterns": {
        "en": ["my wallets", "list wallets", "connected wallets"],
        "es": ["mis carteras", "carteras conectadas"],
        "pt": ["minhas carteiras", "carteiras conectadas"],
        "zh": ["我的钱包们", "已连接的钱包"]
      },
      "agent": "wallet",
      "description": "List all your connected wallets"
    }
  ]
}
```

---

## Balance-Aware Suggestions

### Empty Portfolio ($0)

```
**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay
• 📥 Transfer crypto from another wallet to the address above
```

### Funded Portfolio (> $0)

```
**💰 Balance:** $X,XXX.XX

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for detailed holdings
```

---

## Common User Flows

### Flow 1: Check Wallet Address

```
User: "my wallet"
→ Supervisor routes to wallet agent
→ WalletAgent extracts user context
→ Builds wallet context with full address
→ Adds balance-aware suggestions
→ Returns formatted response
```

### Flow 2: Guest User

```
User: "my wallet"
→ Supervisor routes to wallet agent
→ WalletAgent detects no authentication
→ Returns auth required message
```

### Flow 3: User Asks About Balance

```
User: "my balance"
→ Supervisor routes to PORTFOLIO agent (not wallet)
→ PortfolioAgent shows holdings and USD value
```

---

## Critical Address Display Rule

**NEVER truncate wallet addresses!**

| Format | Allowed? | Reason |
|--------|----------|--------|
| `0x742d35Cc6634C0532925a3b844Bc454e4438f44e` | ✅ Yes | Full address, user can copy |
| `0x742d...f44e` | ❌ No | User can't copy for transfers |
| `0x742d35Cc...` | ❌ No | Incomplete address |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Wallet Agent Shortcuts**
