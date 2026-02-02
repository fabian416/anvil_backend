# Swap Frontend Documentation

This directory contains frontend specifications for implementing swap execution.

## Documents

| Document | Description |
|----------|-------------|
| [SWAP_EXECUTION_SPEC.md](./SWAP_EXECUTION_SPEC.md) | Complete specification for executing swaps with Privy |
| [HYPERLIQUID_SWAP_IMPLEMENTATION_PLAN.md](./HYPERLIQUID_SWAP_IMPLEMENTATION_PLAN.md) | **NEW** - Complete 3-step Hyperliquid swap flow with code |

## Quick Reference

### Provider Detection

```typescript
const isHyperliquidSwap = (execute) => {
  return execute.provider === "hyperliquid" || 
         execute.from_token_address === null;
};
```

### Execution Flow by Provider

#### Hyperliquid (3-Step Flow)
```
User USDC on Base/Arbitrum
        │
        ▼
┌───────────────────────┐
│ 1. Deposit to Bridge  │  ← EVM tx (Privy)
│    (Approve + Send)   │
└───────────────────────┘
        │ (~1-2 min)
        ▼
┌───────────────────────┐
│ 2. Transfer to Spot   │  ← Hyperliquid SDK
│    (Perps → Spot)     │
└───────────────────────┘
        │ (instant)
        ▼
┌───────────────────────┐
│ 3. Execute Swap       │  ← Hyperliquid SDK
│    (Market Order)     │
└───────────────────────┘
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
| Gas Fees | Zero on Hyperliquid | User pays |
| Execution | 3 steps | 1-2 steps |
| Balance Check | Hyperliquid API | `balanceOf()` |
| SDK | `@nktkas/hyperliquid` | viem/ethers |
