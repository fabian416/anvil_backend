# Wallet Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **WALLET** agent provides wallet address display for authenticated users on Anvil. It shows the user's connected wallet addresses with full, non-truncated addresses so users can receive funds.

### Key Differentiators

- **Full Address Display**: Never truncates wallet addresses
- **Balance-Aware Suggestions**: Recommends actions based on portfolio balance
- **Authentication Required**: Only available for authenticated users
- **Complements Portfolio**: Wallet shows address, Portfolio shows balance

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
2. Test with authenticated users
3. Verify full address display (no truncation)

---

## Key Features

### 1. Wallet Display

| Feature | Description | Status |
|---------|-------------|--------|
| **Full Address** | Never truncates (shows complete 0x...) | ✅ Complete |
| **Primary Wallet** | Marks primary wallet | ✅ Complete |
| **Chain Type** | Shows chain (Base, Ethereum, etc.) | ✅ Complete |
| **Provider Info** | Shows provider (Privy, etc.) | ✅ Complete |

### 2. Balance-Aware Suggestions

| Balance State | Suggestions |
|---------------|-------------|
| **$0 Balance** | "buy crypto", "transfer from another wallet" |
| **Funded** | "swap", "earn yield", "portfolio" |

### 3. Wallet vs Portfolio Distinction

| Query | Agent | Response |
|-------|-------|----------|
| `my wallet` | wallet | Wallet address (full) |
| `wallet address` | wallet | Wallet address (full) |
| `my balance` | portfolio | USD balance, holdings |
| `my portfolio` | portfolio | Holdings, suggestions |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → WalletAgent
    ↓ (Data Sources)
External Systems
    - Anvil Database (wallet info)
    - Vertex AI LLM (formatting)
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    WALLET AGENT FLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "my wallet"                                          │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: wallet         │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │     WalletAgent         │                               │
│  │                         │                               │
│  │  1. Extract user context│ → Wallet address, chain       │
│  │  2. Build wallet context│ → Full address display        │
│  │  3. Add suggestions     │ → Based on balance            │
│  │  4. LLM format          │ → Concise response            │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    Response with        │                               │
│  │  FULL wallet address    │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules

```python
# From authenticated_supervisor.py

2. WALLET QUERIES (authenticated - REAL data):
   - "my wallets", "connected wallets", "wallet address" → "wallet" agent
   - "wallet info", "list wallets", "show wallets" → "wallet" agent
```

### Routing Examples

| User Query | Agent | Reason |
|------------|-------|--------|
| "my wallet" | wallet | Address query |
| "my wallet address" | wallet | Address query |
| "show my wallets" | wallet | Address query |
| "wallet info" | wallet | Address query |
| "my balance" | portfolio | Balance query |
| "my portfolio" | portfolio | Holdings query |

---

## Example Conversations

### Empty Portfolio Wallet

```
User: "my wallet"

Agent:
**Your Wallet:**
`0x742d35Cc6634C0532925a3b844Bc454e4438f44e`

**🚀 Get Started:**
Your wallet is ready! Add funds to start using Anvil:
• 💳 Say **"buy crypto"** to purchase USDC with card/Apple Pay
• 📥 Transfer crypto from another wallet to the address above
```

### Funded Portfolio Wallet

```
User: "show my wallet address"

Agent:
**Your Wallet:**
`0x742d35Cc6634C0532925a3b844Bc454e4438f44e`

**💰 Balance:** $1,234.56

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
• 📊 **Portfolio** - Say "my portfolio" for detailed holdings
```

### Multi-Wallet User

```
User: "list my wallets"

Agent:
**Connected Wallets: 2**

**Wallet 1 (PRIMARY):**
  - Address: `0x742d35Cc6634C0532925a3b844Bc454e4438f44e`
  - Chain: Base

**Wallet 2:**
  - Address: `0x1234567890abcdef1234567890abcdef12345678`
  - Chain: Ethereum
  - Provider: External

**💰 Balance:** $1,234.56

**💡 What you can do:**
• 🔄 **Swap** - Trade between different cryptocurrencies
• 💰 **Earn yield** - Deposit to DeFi protocols
```

### Guest User (No Auth)

```
User: "my wallet"

Agent:
**Wallet Access Requires Authentication**

To view your wallet information, balances, and connected addresses, 
you need to sign in to your Anvil account.

**How to Connect:**
1. Click "Sign In" or "Connect Wallet" in the app
2. Choose your preferred method (email, social, or wallet)
3. Once connected, I can show you:
   - All your connected wallets
   - Balances across chains
   - Transaction history
   - Portfolio overview

Would you like me to help you with something else, or are you ready to sign in?
```

---

## Authentication Requirement

The Wallet agent **requires authentication** to function properly:

| User Type | Behavior |
|-----------|----------|
| **Authenticated** | Shows full wallet address and suggestions |
| **Guest** | Explains authentication requirement |

---

## Critical Rule: Full Address Display

**NEVER truncate wallet addresses!**

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| `0x742d...f44e` | `0x742d35Cc6634C0532925a3b844Bc454e4438f44e` |
| `0x1234...5678` | `0x1234567890abcdef1234567890abcdef12345678` |

Users need the **complete address** to receive funds!

---

## Supported Languages

| Language | Wallet Query | Wallet Address Query |
|----------|--------------|---------------------|
| English | "my wallet", "my wallets" | "wallet address", "show address" |
| Spanish | "mi cartera", "mis carteras" | "dirección de cartera" |
| Portuguese | "minha carteira" | "endereço da carteira" |
| Chinese | "我的钱包" | "钱包地址" |

---

## Configuration

### Default Parameters

```python
# From wallet_agent.py

# LLM Configuration
model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.3           # Balanced
max_tokens = 1500

# Data Sources
- Anvil Database (wallet info)
- Vertex AI LLM (formatting)
```

### Response Structure

```python
AgentResponse(
    content="Wallet formatted response...",
    agent_type=AgentType.WALLET,
    tools_used=["llm_gateway", "wallet_repository"],
    sources=[
        SourceInfo(source_type="database", source_name="Anvil Database", ...),
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
    ],
    metadata={
        "tokens_used": 200,
        "latency_ms": 280,
        "model": "gemini-2.0-flash",
        "provider": "vertex_ai",
        "wallet_count": 1,
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] User context extraction (authenticated)
- [ ] User context extraction (guest)
- [ ] Wallet context building (single wallet)
- [ ] Wallet context building (multi-wallet)
- [ ] Full address display (no truncation)

### Integration Tests
- [ ] Complete wallet query flow
- [ ] Balance-aware suggestions
- [ ] Authentication required response
- [ ] Source attribution

### E2E Tests
- [ ] Authenticated user flow
- [ ] Guest user rejection
- [ ] Multi-wallet display
- [ ] Primary wallet marking

---

## Related Documentation

- **Portfolio Agent**: `/docs/ceo/agents/portfolio/` (balance/holdings)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (add funds)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (send to wallet)
- **Transaction History**: `/docs/ceo/agents/activity/` (activity)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added balance-aware suggestions |
| 1.0 | 2026-01-29 | Added full address requirement |

---

**End of Wallet Agent Specification**
