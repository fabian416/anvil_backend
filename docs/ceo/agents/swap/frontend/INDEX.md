# Swap Frontend Documentation

This directory contains frontend specifications for implementing swap execution.

## Documents

| Document | Description |
|----------|-------------|
| [SWAP_EXECUTION_SPEC.md](./SWAP_EXECUTION_SPEC.md) | Complete specification for executing swaps with Privy, covering Hyperliquid, 1inch, and LiFi |

## Quick Reference

### Provider Detection

```typescript
const isHyperliquidSwap = (execute) => {
  return execute.provider === "hyperliquid" || 
         execute.from_token_address === null;
};
```

### Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Execute Payload                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Check Provider  │
                    └─────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ hyperliquid  │ │    1inch     │ │    lifi      │
      └──────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │ Hyperliquid  │ │   Privy +    │ │   Privy +    │
      │     SDK      │ │   EVM Tx     │ │   EVM Tx     │
      └──────────────┘ └──────────────┘ └──────────────┘
              │               │               │
              ▼               ▼               ▼
      ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
      │  Order ID    │ │   Tx Hash    │ │   Tx Hash    │
      └──────────────┘ └──────────────┘ └──────────────┘
```

### Critical Fix

The backend now returns `null` for token addresses on Hyperliquid swaps:

```json
{
  "provider": "hyperliquid",
  "from_token_address": null,
  "to_token_address": null
}
```

**Do NOT call `balanceOf()` when addresses are null!**
