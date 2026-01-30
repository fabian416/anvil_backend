# Execution Agent Specification

**Version**: 1.0
**Date**: 2026-01-29
**Status**: ✅ Complete Implementation
**Agent Type**: Core Agent (Single-Step)
**Architecture**: Hexagonal (Clean Architecture)

---

## Overview

The **EXECUTION** agent handles transaction execution using Privy embedded wallets. It provides secure, user-confirmed transaction capabilities for swaps, transfers, and token approvals with safety features like transaction limits, slippage protection, and pre-flight simulation.

### Key Differentiators

- **Privy Integration**: Uses Privy embedded wallets for secure signing
- **1inch Quotes**: Real-time swap quotes from 1inch API
- **Safety First**: Transaction limits, slippage protection, simulation
- **User Confirmation**: All transactions require explicit user confirmation
- **Multi-Action Support**: Swaps, transfers, approvals, wrap/unwrap

---

## Document Structure

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start (this file) |
| `INDEX.md` | Navigation and status tracking |
| `architecture.md` | Hexagonal architecture design |
| `implementation.md` | Code references and key methods |
| `shortcuts.md` | Chat patterns and transaction types |

---

## Quick Start

### For Developers

1. Read `architecture.md` for the hexagonal design
2. Review `implementation.md` for code locations
3. Check `shortcuts.md` for transaction types

### For QA Engineers

1. Review test scenarios in `architecture.md`
2. Test transaction confirmation flows
3. Verify safety limits are enforced

---

## Key Features

### 1. Supported Actions

| Action | Description | Status |
|--------|-------------|--------|
| **swap** | Token-to-token swaps via 1inch | ✅ Complete |
| **transfer** | Send tokens to address | ✅ Complete |
| **approve** | Approve token spending | ✅ Complete |
| **wrap** | Wrap ETH to WETH | ✅ Complete |
| **unwrap** | Unwrap WETH to ETH | ✅ Complete |

### 2. Safety Features

| Feature | Description | Default |
|---------|-------------|---------|
| **Transaction Limit** | Max transaction value | $10,000 USD |
| **Slippage Protection** | Price slippage limit | 1% |
| **Pre-flight Simulation** | Simulate before execution | Always |
| **User Confirmation** | Require explicit approval | Always |
| **Gas Estimation** | Estimate gas before signing | Always |

### 3. Integrations

| Service | Purpose | Status |
|---------|---------|--------|
| **Privy** | Embedded wallet signing | ✅ Active |
| **1inch** | Swap quotes and routing | ✅ Active |
| **Vertex AI** | Intent parsing | ✅ Active |

---

## Architecture Principles

### Hexagonal Architecture

```
Presentation Layer
    ↓ (HTTP Controllers)
Application Layer
    ↓ (Supervisor Coordinator)
Infrastructure Layer → ExecutionAgentPrivy
    ↓ (External Services)
External Systems
    - Privy (wallet)
    - 1inch (quotes)
    - Blockchain (execution)
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION AGENT FLOW                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User: "swap 1 ETH for USDC"                                │
│                ↓                                            │
│  ┌─────────────────────────┐                               │
│  │ Supervisor Coordinator  │                               │
│  │ Detects: swap_tokens    │                               │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │   ExecutionAgentPrivy   │                               │
│  │                         │                               │
│  │  1. Parse intent (LLM)  │ → action, tokens, amount      │
│  │  2. Get 1inch quote     │ → Rate, gas, routing          │
│  │  3. Validate limits     │ → < $10k, slippage ok         │
│  │  4. Build response      │ → Quote + confirmation        │
│  │  5. (User confirms)     │ → Frontend handles            │
│  │  6. Sign via Privy      │ → Embedded wallet             │
│  │  7. Submit transaction  │ → Blockchain                  │
│  └───────────┬─────────────┘                               │
│              ↓                                              │
│  ┌─────────────────────────┐                               │
│  │  Response with quote    │                               │
│  │  + confirmation request │                               │
│  └─────────────────────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Supervisor Routing

### Routing Rules (Legacy)

```python
# From intent_classifier.py

"swap_tokens": AgentType.EXECUTION,
"execute_transaction": AgentType.EXECUTION,
```

### Modern Routing (Workflow Agents)

**Note**: Most transaction execution is now handled by specialized workflow agents:

| Transaction Type | Agent | Reason |
|------------------|-------|--------|
| Token swaps | `swap_workflow` | Multi-step with balance checks |
| Crypto purchases | `buy_workflow` | MoonPay/Privy integration |
| Token transfers | `transfer_workflow` | Safety checks, address validation |
| Lending deposits | `lending_workflow` | Morpho vault integration |
| Money market | `money_market_workflow` | Protocol rate comparison |

The EXECUTION agent is still used for:
- Direct transaction parsing and intent extraction
- 1inch quote fetching
- Generic transaction execution requests
- Integration with legacy intent classifier

---

## Example Conversations

### Swap Quote

```
User: "swap 1 ETH for USDC"

Agent:
I can help you swap 1.0 ETH for USDC.

**REAL-TIME SWAP QUOTE FROM 1INCH:**
- Swap: 1.0000 ETH → 2,456.7800 USDC
- Expected Output: 2,456.7800 USDC
- Estimated Gas: 185,000 gas units
- Price Impact: 0.03%
- Routing: 3 protocol(s) involved

**Next Steps:**
1. Review the quote above
2. Confirm the swap details
3. Sign the transaction with your wallet
4. Transaction will be submitted to the blockchain

**Safety Features:**
- Transaction limits: Max $10000 per transaction
- Slippage protection: 1% default
- Gas estimation included
- Pre-flight simulation before execution

Would you like to proceed with this swap?
```

### Informational Query

```
User: "what type of swaps can I do?"

Agent:
**Token Swaps on Anvil**

Anvil supports token swaps through multiple DEX aggregators:

**Supported Aggregators:**
- **1inch**: Leading DEX aggregator with smart routing across 100+ liquidity sources
- **Hyperliquid**: High-performance perpetual futures exchange (20,000+ TPS, no gas fees)
- **UniswapX**: Dutch auction-based swap protocol with automatic routing
- **LiFi**: Cross-chain bridge and swap aggregator

**Supported Tokens:**
- Major tokens: BTC, ETH, USDC, USDT, DAI, SOL, MATIC, AVAX, LINK
- 100+ tokens across multiple chains

**Supported Chains:**
- Ethereum, Base, Arbitrum, Polygon, Optimism

**To get a swap quote**, provide specific details:
- "swap 100 USDC for ETH"
- "swap 0.5 BTC to SOL"
- "exchange 1000 USDT for USDC"

I'll provide real-time quotes with rates, gas costs, and execution details.
```

### Transfer Request

```
User: "transfer 0.5 ETH to 0x1234..."

Agent:
I understand you want to transfer ETH.

However, I need more information to proceed. Please provide:
- Exact amount to transfer
- Recipient wallet (if transfer)
- Any other relevant details

Once I have all details, I'll prepare the transaction for your confirmation.
```

---

## Transaction Intent Parsing

### LLM Prompt

```python
prompt = """Parse the transaction intent from this message. Extract the action and token details.

Message: {message}

Identify and extract:
- action: MUST be one of "swap", "transfer", "approve", "wrap", "unwrap"
- from_token: Token symbol (e.g., "ETH", "USDC")
- to_token: Token symbol (if swap)
- amount: Numeric amount as string
- recipient: Wallet address (if transfer)

Examples:
- "swap 1 ETH for USDC" → {"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "1.0"}
- "I want to swap 0.5 ETH to USDC" → {"action": "swap", "from_token": "ETH", "to_token": "USDC", "amount": "0.5"}

Respond with ONLY valid JSON:
"""
```

### Fallback Extraction

If LLM parsing fails, regex-based extraction is used:

```python
# Simple extraction: "swap X for Y" or "swap X to Y"
swap_match = re.search(r'swap\s+(\d*\.?\d*)?\s*(\w+)\s+(?:for|to)\s+(\w+)', message_lower)
if swap_match:
    amount_str = swap_match.group(1) or "1.0"
    from_token = swap_match.group(2).upper()
    to_token = swap_match.group(3).upper()
```

---

## Configuration

### Default Parameters

```python
# From execution_agent_privy.py

# LLM Configuration
model = "gemini-2.0-flash"  # Vertex AI
temperature = 0.1           # Low for precision
max_tokens = 1000

# Transaction Limits
max_transaction_value_usd = Decimal("10000")

# Slippage
default_slippage = 1.0  # 1%
```

### Token Addresses (Ethereum)

```python
TOKEN_ADDRESSES = {
    "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
}
```

### Response Structure

```python
AgentResponse(
    content="Swap quote and confirmation request...",
    agent_type=AgentType.EXECUTION,
    tools_used=["privy_wallet", "llm_gateway", "1inch_api"],
    sources=[
        SourceInfo(source_type="llm", source_name="gemini-2.0-flash", ...),
        SourceInfo(source_type="api", source_name="1inch", ...),
        SourceInfo(source_type="api", source_name="Privy", ...),
    ],
    metadata={
        "latency_ms": 850,
        "transaction_intent": {
            "action": "swap",
            "from_token": "ETH",
            "to_token": "USDC",
            "amount": "1.0",
        },
        "requires_confirmation": True,
    },
)
```

---

## Testing Checklist

### Unit Tests
- [ ] Intent parsing (swap, transfer, approve)
- [ ] Fallback regex extraction
- [ ] Informational query detection
- [ ] Response building

### Integration Tests
- [ ] 1inch quote fetching
- [ ] Privy wallet integration
- [ ] Source attribution

### E2E Tests
- [ ] Complete swap flow with confirmation
- [ ] Transfer flow with address validation
- [ ] Transaction limit enforcement

---

## Related Documentation

- **Swap Workflow**: `/docs/ceo/agents/swap/` (multi-step swaps)
- **Buy Workflow**: `/docs/ceo/agents/buy/` (fiat-to-crypto)
- **Transfer Workflow**: `/docs/ceo/agents/transfer/` (token transfers)
- **Lending Workflow**: `/docs/ceo/agents/lending/` (Morpho deposits)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |
| 1.0 | 2026-01-29 | Added 1inch integration |
| 1.0 | 2026-01-29 | Added safety features |

---

**End of Execution Agent Specification**
