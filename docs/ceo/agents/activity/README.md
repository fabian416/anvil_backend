# Activity / Transaction History Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete Implementation
**Author**: Claude Code (Senior Python Backend Engineer)

---

## Overview

This directory contains comprehensive documentation for the **Activity/Transaction History** feature, enabling authenticated users to view and analyze their transaction history with:

- **Real-time transaction data** from blockchain
- **Balance-aware messaging** (different responses for $0 vs funded wallets)
- **Multi-language support** (en, es, pt, zh)
- **Transaction analytics** (volume, most active chain)
- **Status tracking** (success, pending, failed)

---

## Document Structure

### 1. [`architecture.md`](./architecture.md)

**Purpose**: Complete hexagonal architecture design for transaction history

**Contents**:
- Domain layer entities and value objects
- Application layer integration
- Infrastructure adapters
- User data service integration
- Multi-agent coordination

### 2. [`implementation.md`](./implementation.md)

**Purpose**: Implementation details and code references

**Contents**:
- File locations and structure
- Key methods and classes
- Dependency injection configuration
- API integration

### 3. [`shortcuts.md`](./shortcuts.md)

**Purpose**: Shortcut configuration for activity intents

**Contents**:
- Pattern matching
- Multi-language examples
- Agent routing

---

## Quick Start

### For Developers

1. **Read the architecture** (`architecture.md`) to understand the design
2. **Check implementation** (`implementation.md`) for code locations
3. **Review shortcuts** (`shortcuts.md`) for routing patterns

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test multi-language support
3. Verify balance-aware responses

---

## Key Features

### 1. Transaction History Viewing

| Feature | Description |
|---------|-------------|
| Recent Transactions | Last 10 transactions with details |
| Volume Analytics | 30-day transaction volume |
| Chain Analysis | Most active chain identification |
| Status Tracking | Success, Pending, Failed indicators |

### 2. Balance-Aware Responses

| User State | Response |
|------------|----------|
| $0 Balance | Recommends buy crypto or receive tokens |
| Has Balance, No Transactions | Recommends swap, lend, or send |
| Has Transactions | Shows transaction history and analytics |

### 3. Transaction Types Supported

| Type | Emoji | Description |
|------|-------|-------------|
| SWAP | 🔄 | Token exchange via DEX |
| TRANSFER | 📤 | Send tokens to another address |
| APPROVE | ✅ | Authorize contract to spend tokens |
| DEPOSIT | 💰 | DeFi protocol deposits |
| WITHDRAW | 📥 | DeFi protocol withdrawals |
| STAKE | 🥩 | Staking operations |

### 4. Transaction Status

| Status | Emoji | Description |
|--------|-------|-------------|
| Success | ✅ | Confirmed on blockchain |
| Pending | ⏳ | Awaiting confirmation |
| Failed | ❌ | Transaction reverted |

---

## Architecture Principles

### Hexagonal Architecture (Clean Architecture)

```
Domain Layer (Transaction Data Models)
    ↓
Application Layer (User Data Service)
    ↓
Infrastructure Layer (Transaction History Agent)
    ↓
Presentation Layer (Chat Endpoints)
```

### Agent-Based Design

The transaction history feature uses a specialized agent:

- **TransactionHistoryAgent**: Handles all activity/transaction queries
- **Integration**: Receives real transaction data from UserDataService
- **Output**: Formatted, user-friendly transaction summaries

---

## Routing Configuration

### Supervisor Routing Rules

```
3. TRANSACTION HISTORY (authenticated - REAL data):
   - "my transactions", "transaction history", "recent activity" → "transaction_history" agent
   - "show transactions", "past swaps", "activity summary" → "transaction_history" agent
   - "my activity", "show activity", "what have I done" → "transaction_history" agent
```

### Example Mappings

| User Query | Agent | Description |
|------------|-------|-------------|
| "my activity" | transaction_history | Show activity feed |
| "my transactions" | transaction_history | Show transaction list |
| "recent activity" | transaction_history | Show recent transactions |
| "what have I done" | transaction_history | Show transaction summary |

---

## Example Conversations

### User With Empty Balance

```
User: "My activity"

Agent: 
Your balance: $0.00

• 💳 **Buy crypto** - Say "buy crypto" to purchase USDC with card/Apple Pay/Google Pay
• 📥 **Receive crypto** - Transfer tokens from another wallet (ask "my wallet address" for your address)
```

### User With Balance But No Transactions

```
User: "My activity"

Agent: 
Your balance: ~$500.00

No transaction history yet - you're ready to start! Try:

• 🔄 **Swap tokens** - Say "swap USDC to ETH" to trade
• 💰 **Earn yield** - Say "deposit 100 USDC" to start earning
• 📤 **Send tokens** - Say "send 10 USDC to 0x..." to transfer

Your transactions will appear here automatically! 🚀
```

### User With Transaction History

```
User: "My activity"

Agent:
**Transaction Summary:**
- Total Transactions: 15
- 30-Day Volume: $2,450.00
- Most Active Chain: Base

**Recent Transactions (5 shown):**

**1. SWAP** ✅
   - Hash: `0x7a2b3...`
   - Chain: Base
   - Amount: 100 USDC → 0.032 ETH
   - Status: Success
   - Date: 2026-01-28 14:30

**2. TRANSFER** ✅
   - Hash: `0x8c3d4...`
   - Chain: Base
   - Amount: 50 USDC
   - Status: Success
   - Date: 2026-01-27 10:15
...
```

---

## Supported Languages

| Code | Language | Example Phrase |
|------|----------|----------------|
| `en` | English | "my activity" |
| `es` | Spanish | "mi actividad" |
| `pt` | Portuguese | "minha atividade" |
| `zh` | Chinese | "我的活动" |

---

## Testing Checklist

### Unit Tests
- [ ] TransactionHistoryAgent response formatting
- [ ] Balance-aware message generation
- [ ] Transaction context building

### Integration Tests
- [ ] Supervisor routing to transaction_history
- [ ] User data service integration
- [ ] Multi-language support

### E2E Tests
- [ ] Complete activity flow for authenticated users
- [ ] Empty state handling
- [ ] Transaction display formatting

---

## Related Documentation

- **Portfolio Agent**: `/docs/ceo/agents/portfolio/` (if exists)
- **Wallet Agent**: Handles wallet address queries
- **Lending Workflow**: `/docs/ceo/agents/lending/`
- **Transfer Workflow**: `/docs/ceo/agents/transfer/`

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial complete specification |

---

**End of Activity/Transaction History Specification**
