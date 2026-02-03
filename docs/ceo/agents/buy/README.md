# Buy Workflow Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Workflow (Multi-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **BUY_WORKFLOW** agent handles fiat-to-crypto purchases for authenticated users on Anvil. It provides a seamless on-ramp experience using **Privy SDK** with **MoonPay** and **Coinbase** as payment providers.

### Key Differentiators

- **USDC Only**: Currently only USDC is available for direct purchase
- **Multiple Payment Methods**: Card, Apple Pay, Google Pay
- **Privy Integration**: Native SDK integration for seamless UX
- **Smart Redirection**: Guides users to buy USDC then swap for other cryptos
- **Multi-language Support**: EN, ES, PT, ZH

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
2. Test with different amounts and currencies
3. Verify unsupported crypto redirection

---

## Key Features

### 1. Supported Assets

| Asset | Status | Notes |
|-------|--------|-------|
| **USDC** | ✅ Supported | Only available option |
| ETH | ❌ Redirect | Suggests buy USDC + swap |
| BTC | ❌ Redirect | Suggests buy USDC + swap |
| SOL | ❌ Redirect | Suggests buy USDC + swap |
| Other | ❌ Redirect | Suggests buy USDC + swap |

### 2. Supported Fiat Currencies

| Currency | Symbol | Supported |
|----------|--------|-----------|
| USD | $ | ✅ Yes |
| EUR | € | ✅ Yes |
| GBP | £ | ✅ Yes |
| CAD | C$ | ✅ Yes |
| AUD | A$ | ✅ Yes |

### 3. Multi-Step Workflow

```
Step 1: PARSE_REQUEST
  - Extract crypto, amount, fiat currency
  - Default to USDC if crypto not specified
  - Redirect if unsupported crypto requested

Step 2: FETCH_DATA (Validate)
  - Validate crypto is supported (USDC only)
  - Validate fiat currency
  - Build execute_data

Step 3: CONFIRM
  - Display purchase review
  - Wait for user confirmation

Step 4: EXECUTE
  - Generate execute_data for Privy modal
  - Frontend opens MoonPay/Coinbase
```

### 4. Payment Providers

| Provider | Methods | Status |
|----------|---------|--------|
| **MoonPay** | Card, Apple Pay, Google Pay | ✅ Active |
| **Coinbase** | Card, Bank Transfer | ✅ Active |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → BuyWorkflowAgent
    ↓ (Execute Data)
Frontend
    ↓ (Privy SDK)
Payment Providers
    - MoonPay
    - Coinbase
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     BUY WORKFLOW FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "buy $100 of crypto"                                 │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: buy_workflow   │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    BuyWorkflowAgent     │                               │
│  │                         │                               │
│  │  Step 1: Parse Request  │ → Default to USDC             │
│  │  Step 2: Validate       │ → Check USDC supported        │
│  │  Step 3: Build Review   │ → Show purchase details       │
│  │  Step 4: Execute Data   │ → Generate Privy payload      │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │    Frontend Privy       │                               │
│  │   MoonPay/Coinbase      │                               │
│  │   Payment Modal         │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules

```python
# From authenticated_supervisor.py

11. BUY CRYPTO EXECUTION (CRITICAL - Multi-step workflow):
    - "buy $100 of ETH", "purchase crypto", "buy USDC with card" → "buy_workflow"
    - The buy_workflow agent handles the COMPLETE multi-step purchase process
    - Use when user wants to BUY crypto with fiat (card, Apple Pay, etc.)
    - Examples: "buy $50 of ETH", "purchase 100 dollars of USDC", "buy crypto"
    - DO NOT combine with other agents - it handles everything internally
```

### Routing Examples

| User Query | Agent | Reason |
|------------|-------|--------|
| "buy $100 of ETH" | buy_workflow | Purchase request |
| "purchase 50 dollars of USDC" | buy_workflow | Purchase request |
| "buy crypto" | buy_workflow | Generic purchase |
| "buy USDC with card" | buy_workflow | Payment method specified |
| "I want to buy some crypto" | buy_workflow | Intent detected |
| "price of ETH" | hunter_ai | Information request |

---

## Example Conversations

### Direct USDC Purchase

```
User: "buy $100 of USDC"

Agent:
💳 **Review Your Purchase**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Buying:** USDC 💵
💵 **Amount:** $100 USD
🌐 **Network:** Base

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Payment Options:**
• Credit/Debit Card
• Apple Pay / Google Pay

[Execute_data card shown for payment]
```

### Unsupported Crypto (Redirected)

```
User: "buy $100 of ETH"

Agent:
💡 **USDC Only Available**

I see you want to buy **ETH**, but currently only **USDC** is available 
for direct purchase.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Here's a tip:** You can buy USDC first, then swap it for ETH instantly!

Would you like to buy USDC instead?

💬 Just tell me how much (e.g., "$100" or "500 dollars")
```

### Generic "Buy Crypto" Request

```
User: "buy crypto"

Agent:
💵 **Buy USDC**

How much USDC would you like to buy?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**USDC** is a stablecoin pegged 1:1 to the US Dollar - perfect for:
• 🔄 Swapping to other cryptos (ETH, BTC, SOL...)
• 💰 Earning yield in DeFi
• 📤 Sending to friends

💬 Enter the amount in USD (e.g., "100" or "$500")

💡 *Minimum: $30*

User: "100"

Agent:
💳 **Review Your Purchase**

💰 **Buying:** USDC 💵
💵 **Amount:** $100 USD
🌐 **Network:** Base

[Execute_data card shown]
```

### Modification Flow

```
User: "buy $100 of USDC"

Agent: [Shows $100 review]

User: "change to $200"

Agent:
💳 **Review Your Purchase**

💰 **Buying:** USDC 💵
💵 **Amount:** $200 USD
🌐 **Network:** Base

[Updated execute_data card shown]
```

---

## Supported Languages

| Language | Buy Command | Confirm | Cancel |
|----------|-------------|---------|--------|
| English | "buy", "purchase" | "yes", "confirm" | "cancel", "no" |
| Spanish | "comprar" | "sí", "confirmar" | "cancelar", "no" |
| Portuguese | "comprar" | "sim", "confirmar" | "cancelar", "não" |
| Chinese | "购买" | "是", "确认" | "取消", "不" |

---

## Configuration

### Default Parameters

```python
# From buy_workflow_agent.py

# Minimum purchase amount
MINIMUM_AMOUNT = 30  # USD

# Default network
DEFAULT_NETWORK = "Base"

# Supported cryptos (USDC only)
SUPPORTED_CRYPTOS = {
    "usdc": {"symbol": "USDC", "name": "USD Coin", "emoji": "💵"},
}

# Supported fiat currencies
SUPPORTED_FIATS = {"USD", "EUR", "GBP", "CAD", "AUD"}
```

### Execute Data Structure

```python
execute_data = {
    "action_type": "buy",
    "provider": "privy",
    "chain": "base",
    "to_token": "USDC",      # Crypto being purchased
    "amount": "100",          # Fiat amount
    "from_token": "USD",      # Fiat currency
    "recipient": "0x...",     # Destination wallet
    "quote_id": "buy-usdc-100",
}
```

---

## Testing Checklist

### Unit Tests
- [ ] Amount parsing (various formats: $100, 100 dollars, €50)
- [ ] Fiat currency detection
- [ ] Unsupported crypto detection
- [ ] Confirmation/cancellation parsing
- [ ] Modification parsing

### Integration Tests
- [ ] Complete buy flow (USDC)
- [ ] Unsupported crypto redirection
- [ ] Amount modification
- [ ] Multi-language responses

### E2E Tests
- [ ] Privy modal integration
- [ ] MoonPay flow
- [ ] Coinbase flow
- [ ] Restart detection

---

## Related Documentation

- **Swap Workflow**: `/docs/ceo/agents/swap/` (swap after buying)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (send crypto)
- **Portfolio Agent**: View purchased crypto
- **Wallet Agent**: Check balance after purchase

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added USDC-only constraint |
| 1.0 | 2026-01-29 | Added smart redirection for unsupported cryptos |

---

**End of Buy Workflow Specification**
