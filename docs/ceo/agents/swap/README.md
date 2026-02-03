# Swap Workflow Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Workflow (Multi-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **SWAP_WORKFLOW** agent handles complete token swap operations for authenticated users on Anvil. It uses **Hyperliquid Spot** as the primary swap provider, supporting meme tokens paired with USDC.

### Key Differentiators

- **Zero Gas Fees**: Hyperliquid has no gas fees for spot trading
- **0.02% Trading Fee**: Lower than most DEXs (Uniswap is 0.3%)
- **Sub-second Execution**: 20,000+ TPS on Hyperliquid L1
- **Real-time Order Book**: Native order book pricing, no slippage surprises
- **Balance Awareness**: Checks user funds before execution, recommends "buy crypto" if insufficient

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
2. Test with different token pairs
3. Verify balance-aware messaging

---

## Key Features

### 1. Token Support

| Category | Tokens | Status |
|----------|--------|--------|
| **Meme Tokens** | PURR, TRUMP, PEPE, HFUN, MOG, GMEOW + 50 more | ✅ Supported |
| **Quote Currency** | USDC | ✅ Required |
| **Major Tokens** | ETH, BTC, SOL, LINK, UNI, etc. | ❌ Not Supported |

### 2. Multi-Step Workflow

```
Step 1: PARSE_REQUEST
  - Extract from_token, to_token, amount
  - Interactive token selection if incomplete

Step 2: FETCH_DATA
  - Get quote from Hyperliquid Spot
  - Check user balance
  - Show funding recommendation if needed

Step 3: CONFIRM
  - Display quote details
  - Wait for user confirmation

Step 4: EXECUTE
  - Generate execute_data for frontend
  - Privy SDK handles wallet signing
```

### 3. Provider Routing

| Token Type | Provider | Route |
|------------|----------|-------|
| Meme + USDC | Hyperliquid Spot | Primary |
| Major tokens (fallback) | 1inch | Secondary |
| Cross-chain | LiFi | Tertiary |

### 4. Balance Awareness

```
User has $0 → "You'll need USDC first. Say 'buy crypto' to purchase with card."
User has $50, swapping $100 → "Swap amount exceeds your balance."
User has $200, swapping $100 → Proceed to quote
```

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → SwapWorkflowAgent
    ↓ (Adapters)
External APIs
    - Hyperliquid Spot (meme tokens)
    - CoinGecko (prices)
    - 1inch/LiFi (fallback)
```

### Component Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SWAP WORKFLOW FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "swap 100 USDC to PURR"                             │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: swap_workflow  │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   SwapWorkflowAgent     │                               │
│  │                         │                               │
│  │  Step 1: Parse Request  │ → Extract tokens, amount      │
│  │  Step 2: Check Balance  │ → User context validation     │
│  │  Step 3: Fetch Quote    │ → Hyperliquid Spot API        │
│  │  Step 4: Format Response│ → Quote + execute_data        │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │     Frontend Privy      │                               │
│  │   Wallet Signing Modal  │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules

```python
# From authenticated_supervisor.py

5. SWAP EXECUTION (CRITICAL - Multi-step workflow):
   - "swap X to Y", "exchange X for Y", "convert X to Y" → "swap_workflow"
   - The swap_workflow agent handles the COMPLETE process autonomously
   - Use when user wants to EXECUTE a swap (has specific amount)
   - Examples: "swap 1 ETH to USDC", "exchange 100 USDC for PURR"
   - DO NOT combine with other agents - it handles everything internally
```

### Routing Examples

| User Query | Agent | Reason |
|------------|-------|--------|
| "swap 100 USDC to PURR" | swap_workflow | Execution request |
| "exchange 50 USDC for TRUMP" | swap_workflow | Execution request |
| "convert 1000 PEPE to USDC" | swap_workflow | Execution request |
| "best swap rate ETH to USDC" | hunter_ai | Information request |
| "what tokens can I swap" | knowledge | Educational request |

---

## Example Conversations

### Successful Swap (Full Funds)

```
User: "swap 100 USDC to PURR"

Agent:
📊 **Swap Quote**

**100 USDC** → **1,234.56 PURR**

💰 **Your Balance:** ~$500.00 ✅
• Price Impact: 0.05%
• Network: HYPERLIQUID
• Aggregator: HYPERLIQUID

⛽ **Est. Gas:** ~$0.0000
💡 Hyperliquid has zero gas fees

[Execute_data card shown for wallet signing]
```

### Swap with Insufficient Funds

```
User: "swap 100 USDC to PURR"

Agent:
💡 **Heads up:** Your portfolio appears to have limited funds.

To complete this swap, you'll need **USDC** in your wallet.

**Get started:**
• 💳 Say **"buy crypto"** to purchase with card/Apple Pay/Google Pay
• 📥 Or transfer USDC from another wallet

📊 **Swap Quote**
**100 USDC** → **1,234.56 PURR**
[Quote shown for reference, no execute_data]
```

### Token Selection Flow

```
User: "swap 100 USDC"

Agent:
🔄 **Swap 100 USDC**

**What is Hyperliquid Spot?**
Trade meme tokens with zero gas fees and 0.02% trading fee.

💰 **Your Balance:** ~$500.00 ✅

**Select a meme token to receive:**

**1.** PURR • $0.081234
**2.** TRUMP • $0.151000
**3.** PEPE • $0.000012
**4.** HFUN • $0.005678
**5.** MOG • $0.000001
...

**Reply with:**
• A number (1-10) to select
• Or type the token name (e.g., PURR)

User: "1"

Agent: [Shows PURR swap quote]
```

### Unsupported Token

```
User: "swap 100 USDC to ETH"

Agent:
❌ **Swap not supported: USDC → ETH**

Anvil uses **Hyperliquid Spot** for swaps, which only supports 
**meme tokens paired with USDC**.

**Tokens like ETH are not available for swaps.**

---

**✅ What you CAN do on Anvil:**

**Meme Token Swaps** (via Hyperliquid Spot):
• `swap 100 USDC to PURR`
• `swap 50 USDC to TRUMP`
• `swap 1000 USDC to PEPE`

---

**💡 For major tokens (ETH), you can:**

• **Check prices:** "what's the price of ETH?"
• **Track portfolio:** "show my portfolio"
• **Buy crypto:** "buy ETH" (fiat on-ramp via MoonPay)
• **Use external DEXs:** Uniswap, 1inch, or other DEX aggregators
```

---

## Supported Languages

| Language | Swap Command | Confirm | Cancel |
|----------|--------------|---------|--------|
| English | "swap", "exchange", "convert" | "yes", "confirm" | "cancel", "no" |
| Spanish | "cambiar", "intercambiar" | "sí", "confirmar" | "cancelar", "no" |
| Portuguese | "trocar", "cambiar" | "sim", "confirmar" | "cancelar", "não" |
| Chinese | "兑换", "交换" | "是", "确认" | "取消", "不" |

---

## Configuration

### Default Parameters

```python
# From swap_workflow_agent.py

# Trading fees
HYPERLIQUID_FEE = 0.02%  # 0.02%
ONEINCH_FEE = varies     # Depends on pool

# Slippage
DEFAULT_SLIPPAGE = 1.0%  # 1%

# Token decimals
USDC = 6
ETH = 18
WETH = 18
```

### Supported Meme Tokens

```python
HYPERLIQUID_SPOT_TOKENS = {
    "USDC",  # Quote currency
    "PURR", "HFUN", "TRUMP", "PEPE", "MOG", "POINTS", "JEFF",
    "GMEOW", "LICK", "MANLET", "SIX", "WAGMI", "CAPPY",
    "XULIAN", "RUG", "CZ", "BAGS", "ANSEM", "TATE", "FUN",
    "BIGBEN", "KOBE", "VEGAS", "PUMP", "SCHIZO", "CATNIP",
    "HAPPY", "SELL", "HBOOST", "GPT", "PANDA", "HODL", "RAGE",
    "ASI", "LEAP", "VAPOR", "X", "PILL", "CAT", "HPEPE",
    "MBAPPE", "MAGA", "OMNIX", "COKE", "MEOW", "ANT", "NEIRO",
}
```

---

## Testing Checklist

### Unit Tests
- [ ] Token parsing (valid/invalid symbols)
- [ ] Amount parsing (integers, decimals, USD notation)
- [ ] Hyperliquid swap detection
- [ ] Unsupported token handling
- [ ] Balance validation

### Integration Tests
- [ ] Hyperliquid quote fetching
- [ ] CoinGecko price enrichment
- [ ] 1inch/LiFi fallback
- [ ] Multi-language responses

### E2E Tests
- [ ] Complete swap flow (meme token)
- [ ] Token selection flow
- [ ] Insufficient balance flow
- [ ] Unsupported token flow
- [ ] Restart detection

---

## Related Documentation

- **Hunter AI**: `/docs/ceo/agents/hunter/` (price checking)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (fiat on-ramp)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (token transfers)
- **Knowledge Agent**: Educational swap information

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added balance awareness |
| 1.0 | 2026-01-29 | Added unsupported token handling |

---

**End of Swap Workflow Specification**
