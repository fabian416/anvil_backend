# Swap Frontend Documentation

This directory contains frontend specifications for implementing swap execution.

## Documents

| Document | Description |
|----------|-------------|
| [SWAP_EXECUTION_SPEC.md](./SWAP_EXECUTION_SPEC.md) | Complete specification for executing swaps with Privy |
| [HYPERLIQUID_SWAP_IMPLEMENTATION_PLAN.md](./HYPERLIQUID_SWAP_IMPLEMENTATION_PLAN.md) | Complete 3-step Hyperliquid swap flow with LiFi bridge |

## Quick Reference

### Provider Detection

```typescript
const isHyperliquidSwap = (execute) => {
  return execute.provider === "hyperliquid" || 
         execute.from_token_address === null;
};
```

### Execution Flow by Provider

#### Hyperliquid (3-Step Flow with LiFi)
```
User USDC on Ethereum/Base/Arbitrum
        │
        ▼
┌───────────────────────────────────────┐
│ Backend selects best_source_chain     │
│ (checks can_pay_gas in token_balances)│
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 1. LiFi Bridge (from best chain)      │  ← EVM tx (Privy)
│    Gas paid on source chain!          │
└───────────────────────────────────────┘
        │ (~30 seconds)
        ▼
┌───────────────────────────────────────┐
│ 2. Transfer to Spot                   │  ← Hyperliquid SDK
│    (Perps → Spot)                     │
└───────────────────────────────────────┘
        │ (instant)
        ▼
┌───────────────────────────────────────┐
│ 3. Execute Swap                       │  ← Hyperliquid SDK
│    (Market Order)                     │
└───────────────────────────────────────┘
        │
        ▼
User has PURR in Hyperliquid Spot
```

#### 1inch / LiFi (Standard EVM)
```
User USDC on Base
        │
        ▼
┌───────────────────────┐
│ 1. Approve Token      │  ← EVM tx (Privy)
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│ 2. Execute Swap       │  ← EVM tx (Privy)
└───────────────────────┘
        │
        ▼
User has ETH on Base
```

### NEW: Token Balances from Backend

The backend now provides `lifi_config.token_balances` with `can_pay_gas` flag:

```json
{
  "lifi_config": {
    "best_source_chain": "ethereum",
    "token_balances": {
      "ethereum": {
        "eth_balance": 0.00070785,
        "can_pay_gas": true,
        "usdc_balance": 2.80,
        "weth_balance": 0.00081710
      },
      "base": {
        "eth_balance": 0,
        "can_pay_gas": false,
        "usdc_balance": 0,
        "weth_balance": 0
      },
      "arbitrum": {
        "eth_balance": 0.00001372,
        "can_pay_gas": false,
        "usdc_balance": 0.20,
        "weth_balance": 0.00099750
      }
    },
    "gas_error": null
  }
}
```

**Key Points:**
- `can_pay_gas: true` = Chain has enough native ETH for gas
- WETH cannot pay gas! Only native ETH works
- `best_source_chain` = Backend pre-selected chain with gas
- `gas_error` = Set if no chain has enough gas

### Critical: Null Token Addresses

The backend returns `null` for token addresses on Hyperliquid swaps:

```json
{
  "provider": "hyperliquid",
  "from_token_address": null,
  "to_token_address": null,
  "gas_estimate": "0"
}
```

**Do NOT call `balanceOf()` when addresses are null!**

### Key Differences

| Feature | Hyperliquid | 1inch/LiFi |
|---------|-------------|------------|
| Token Addresses | `null` | Valid ERC-20 |
| Gas Fees | Zero on Hyperliquid | User pays on EVM |
| Bridge Gas | Paid on source chain (via LiFi) | N/A |
| Execution | 3 steps | 1-2 steps |
| Balance Check | `lifi_config.token_balances` | `balanceOf()` |
| SDK | `@nktkas/hyperliquid` + LiFi API | viem/ethers |
| Gas Check | Backend provides `can_pay_gas` | Frontend checks |
