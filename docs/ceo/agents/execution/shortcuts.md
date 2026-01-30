# Execution Agent Shortcuts

**Version**: 1.0
**Date**: 2026-01-29
**Status**: Complete

---

## Overview

This document defines the transaction types, intent patterns, and confirmation flows for the **EXECUTION** agent.

---

## Supported Actions

### Action Types

| Action | Description | Example |
|--------|-------------|---------|
| `swap` | Token-to-token exchange | "swap 1 ETH for USDC" |
| `transfer` | Send tokens to address | "transfer 0.5 ETH to 0x..." |
| `approve` | Token spending approval | "approve USDC for Uniswap" |
| `wrap` | ETH → WETH conversion | "wrap 1 ETH" |
| `unwrap` | WETH → ETH conversion | "unwrap 1 WETH" |

---

## Intent Patterns

### Swap Patterns

| Pattern | Example | Parsed Intent |
|---------|---------|---------------|
| swap X for Y | "swap 1 ETH for USDC" | swap, ETH, USDC, 1.0 |
| swap X to Y | "swap 0.5 ETH to USDC" | swap, ETH, USDC, 0.5 |
| exchange X for Y | "exchange 100 USDC for ETH" | swap, USDC, ETH, 100 |
| convert X to Y | "convert 1000 USDT to USDC" | swap, USDT, USDC, 1000 |

### Transfer Patterns

| Pattern | Example | Parsed Intent |
|---------|---------|---------------|
| transfer X to addr | "transfer 0.5 ETH to 0x123..." | transfer, ETH, 0.5, 0x123... |
| send X to addr | "send 100 USDC to 0xabc..." | transfer, USDC, 100, 0xabc... |

### Wrap/Unwrap Patterns

| Pattern | Example | Parsed Intent |
|---------|---------|---------------|
| wrap X ETH | "wrap 1 ETH" | wrap, ETH, 1.0 |
| unwrap X WETH | "unwrap 1 WETH" | unwrap, WETH, 1.0 |

---

## Modern Workflow Routing

### Workflow Agent Preference

Most transactions are now routed to specialized workflow agents:

| User Query | Agent | Reason |
|------------|-------|--------|
| "swap 1 ETH for USDC" | swap_workflow | Multi-step with balance checks |
| "buy 100 USDC" | buy_workflow | MoonPay/Privy integration |
| "send 0.5 ETH to 0x..." | transfer_workflow | Safety checks, address validation |
| "deposit 1000 USDC to Morpho" | lending_workflow | Morpho vault integration |

### When EXECUTION is Used

| Scenario | Routing |
|----------|---------|
| Legacy intent classifier | EXECUTION |
| Direct "execute" commands | EXECUTION |
| Generic transaction requests | EXECUTION |
| 1inch quote for info only | EXECUTION |

---

## Informational vs Execution

### Informational Queries (No Execution)

| Query | Response Type |
|-------|---------------|
| "what type of swaps can I do?" | Swap capabilities info |
| "what swaps are supported?" | Aggregators and tokens |
| "how do swaps work?" | Swap process explanation |

### Execution Queries (Requires Confirmation)

| Query | Response Type |
|-------|---------------|
| "swap 1 ETH for USDC" | Quote + confirmation request |
| "transfer 0.5 ETH to 0x..." | Transfer details + confirmation |
| "wrap 1 ETH" | Wrap details + confirmation |

---

## Confirmation Flow

### User Confirmation Required

All transactions require explicit user confirmation:

```
┌──────────────────────────────────────────────────────────────┐
│                    CONFIRMATION FLOW                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User: "swap 1 ETH for USDC"                              │
│                                                              │
│  2. Agent Response:                                          │
│     - Real-time quote from 1inch                             │
│     - Expected output amount                                 │
│     - Gas estimation                                         │
│     - Safety features                                        │
│     - "Would you like to proceed?"                           │
│                                                              │
│  3. User confirms (frontend button)                          │
│     → Privy wallet opens                                     │
│     → User signs transaction                                 │
│                                                              │
│  4. Transaction submitted                                    │
│     → Return tx hash                                         │
│     → Wait for confirmation                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## API Response Examples

### Swap Quote Response

```json
{
  "agent_message": {
    "content": "I can help you swap 1.0 ETH for USDC.\n\n**REAL-TIME SWAP QUOTE FROM 1INCH:**\n- Swap: 1.0000 ETH → 2,456.7800 USDC\n- Expected Output: 2,456.7800 USDC\n- Estimated Gas: 185,000 gas units\n- Price Impact: 0.03%\n- Routing: 3 protocol(s) involved\n\n**Next Steps:**\n1. Review the quote above\n2. Confirm the swap details\n3. Sign the transaction with your wallet\n4. Transaction will be submitted to the blockchain\n\n**Safety Features:**\n- Transaction limits: Max $10000 per transaction\n- Slippage protection: 1% default\n- Gas estimation included\n- Pre-flight simulation before execution\n\nWould you like to proceed with this swap?",
    "role": "assistant",
    "agent_type": "execution"
  },
  "execute_data": null,
  "enrichment": {
    "agent_timings": [
      {"agent_type": "supervisor", "duration_ms": 100},
      {"agent_type": "execution", "duration_ms": 1100}
    ],
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "citation_text": "Intent parsing via Vertex AI",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "1inch",
        "citation_text": "1inch swap quote: ETH → USDC",
        "relevance_score": 1.0
      },
      {
        "source_type": "api",
        "source_name": "Privy",
        "citation_text": "Wallet connection and transaction signing via Privy",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Informational Response

```json
{
  "agent_message": {
    "content": "**Token Swaps on Anvil**\n\nAnvil supports token swaps through multiple DEX aggregators:\n\n**Supported Aggregators:**\n- **1inch**: Leading DEX aggregator with smart routing across 100+ liquidity sources\n- **Hyperliquid**: High-performance perpetual futures exchange (20,000+ TPS, no gas fees)\n- **UniswapX**: Dutch auction-based swap protocol with automatic routing\n- **LiFi**: Cross-chain bridge and swap aggregator\n\n**Supported Tokens:**\n- Major tokens: BTC, ETH, USDC, USDT, DAI, SOL, MATIC, AVAX, LINK\n- 100+ tokens across multiple chains\n\n**Supported Chains:**\n- Ethereum, Base, Arbitrum, Polygon, Optimism\n\n**To get a swap quote**, provide specific details:\n- \"swap 100 USDC for ETH\"\n- \"swap 0.5 BTC to SOL\"\n- \"exchange 1000 USDT for USDC\"\n\nI'll provide real-time quotes with rates, gas costs, and execution details.",
    "role": "assistant",
    "agent_type": "execution"
  },
  "execute_data": null,
  "enrichment": {
    "sources": [
      {
        "source_type": "llm",
        "source_name": "gemini-2.0-flash",
        "relevance_score": 1.0
      }
    ]
  }
}
```

### Transfer Response (Needs More Info)

```json
{
  "agent_message": {
    "content": "I understand you want to transfer ETH.\n\nHowever, I need more information to proceed. Please provide:\n- Exact amount to transfer\n- Recipient wallet (if transfer)\n- Any other relevant details\n\nOnce I have all details, I'll prepare the transaction for your confirmation.",
    "role": "assistant",
    "agent_type": "execution"
  }
}
```

---

## Safety Features

### Transaction Limits

```
Maximum per transaction: $10,000 USD
```

### Slippage Protection

```
Default slippage: 1%
User can customize in settings
```

### Pre-flight Simulation

```
All transactions simulated before execution
Prevents failed transactions and wasted gas
```

### User Confirmation

```
All transactions require explicit user approval
Wallet signing via Privy
Cannot auto-execute
```

---

## Supported Tokens

### Ethereum Mainnet

| Token | Address |
|-------|---------|
| ETH | Native (0xEeee...) |
| WETH | 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 |
| USDC | 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 |
| USDT | 0xdAC17F958D2ee523a2206206994597C13D831ec7 |
| DAI | 0x6B175474E89094C44Da98b954EedeAC495271d0F |
| WBTC | 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599 |

### Supported Chains

- Ethereum
- Base
- Arbitrum
- Polygon
- Optimism

---

## Multi-Language Support

### English

```
Commands:
• "swap 1 ETH for USDC"
• "exchange 100 USDC for ETH"
• "transfer 0.5 ETH to 0x..."
• "wrap 1 ETH"
```

### Spanish

```
Commands:
• "intercambiar 1 ETH por USDC"
• "cambiar 100 USDC por ETH"
• "transferir 0.5 ETH a 0x..."
```

### Portuguese

```
Commands:
• "trocar 1 ETH por USDC"
• "transferir 0.5 ETH para 0x..."
```

---

## Error Handling

### Common Errors

| Error | User Message |
|-------|--------------|
| Unknown token | "Token not recognized. Please use supported tokens." |
| Insufficient balance | "Insufficient balance. You have X but need Y." |
| Transaction limit | "Transaction exceeds $10,000 limit." |
| Quote failed | "Unable to get swap quote. Please try again." |
| Network error | "Network error. Please check connection." |

---

## Common User Flows

### Flow 1: Swap with Quote

```
User: "swap 1 ETH for USDC"
→ Parse intent (action=swap, from=ETH, to=USDC, amount=1.0)
→ Fetch 1inch quote
→ Build response with quote + confirmation
→ User confirms in frontend
→ Sign with Privy wallet
→ Submit transaction
```

### Flow 2: Informational Query

```
User: "what swaps can I do?"
→ Parse intent (no specific tokens)
→ Detect informational query
→ Return swap capabilities info
→ No confirmation needed
```

### Flow 3: Transfer

```
User: "transfer 0.5 ETH to 0x1234..."
→ Parse intent (action=transfer, token=ETH, amount=0.5, recipient=0x1234...)
→ Build confirmation message
→ User confirms
→ Execute transfer
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-29 | Initial specification |

---

**End of Execution Agent Shortcuts**
