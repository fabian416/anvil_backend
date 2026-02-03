# Lending Frontend Documentation

This directory contains frontend specifications for implementing lending and borrowing operations with Morpho and Aave protocols.

## Documents

| Document | Description |
|----------|-------------|
| [LENDING_EXECUTION_SPEC.md](./LENDING_EXECUTION_SPEC.md) | Complete specification for executing lending operations with Privy |
| [LENDING_IMPLEMENTATION_PLAN.md](./LENDING_IMPLEMENTATION_PLAN.md) | Complete implementation plan for lending features |

## Quick Reference

### Provider Detection

```typescript
const isLendingAction = (execute) => {
  return ["supply", "withdraw", "borrow", "repay", "liquidate",
          "leverage_loop", "loop_supply", "loop_borrow", "loop_swap"]
         .includes(execute.action);
};
```

### Execution Flow by Action

#### Supply (Deposit)
```
User's USDC on Base
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Approve Token                      │  ← EVM tx (Privy)
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 2. Supply to Protocol                 │  ← EVM tx (Privy)
│    (Morpho/Aave)                      │
└───────────────────────────────────────┘
        │
        ▼
User earns yield on supplied assets
```

#### Borrow
```
User has collateral in Protocol
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Borrow Asset                       │  ← EVM tx (Privy)
│    (Based on collateral)              │
└───────────────────────────────────────┘
        │
        ▼
User receives borrowed assets
```

#### Leverage Loop (Multi-Step)
```
User USDC on Base
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Supply USDC (Collateral)          │  ← EVM tx (Privy)
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 2. Borrow USDC (Against collateral)  │  ← EVM tx (Privy)
└───────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────┐
│ 3. Swap to Target Asset               │  ← EVM tx (Privy)
└───────────────────────────────────────┘
        │
        ▼
Repeat loop (3x-10x leverage)
```

### Supported Protocols

| Protocol | Type | Chains | Features |
|----------|------|--------|----------|
| `morpho` | Peer-to-peer lending optimizer | Base, Ethereum | Higher APY, lower liquidation risk |
| `aave` | Traditional lending pool | Multiple chains | Established, high liquidity |

### Supported Actions

| Action | Type | Description |
|--------|------|-------------|
| `supply` | FUND | Deposit assets to earn yield |
| `withdraw` | SEND | Withdraw supplied assets |
| `borrow` | FUND | Borrow against collateral |
| `repay` | SEND | Repay borrowed amount |
| `liquidate` | SEND | Liquidate undercollateralized position |
| `leverage_loop` | SWAP | Multi-step leveraged position |
| `loop_supply` | FUND | Supply step in leverage loop |
| `loop_borrow` | FUND | Borrow step in leverage loop |
| `loop_swap` | SWAP | Swap step in leverage loop |

### Key Differences from Swaps

| Feature | Lending | Swaps |
|---------|---------|-------|
| Transaction Type | FUND/SEND | SWAP |
| Multi-Step | Leverage loops | Bridge flows |
| Protocol | Morpho/Aave | 1inch/LiFi/Hyperliquid |
| Approval Required | Yes | Yes |
| Gas Fees | User pays | User pays (except Hyperliquid) |
| Collateral | Required for borrowing | Not applicable |
| Yield | Earns APY | No yield |

### Example Execute Payload

#### Supply Action
```json
{
  "action_type": "lending",
  "action": "supply",
  "protocol": "morpho",
  "chain": "base",
  "asset": "USDC",
  "amount": "1000.00",
  "asset_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "protocol_address": "0x...",
  "value_usd": "1000.00",
  "gas_estimate": "150000",
  "current_apy": "5.25",
  "health_factor": "2.5"
}
```

#### Borrow Action
```json
{
  "action_type": "lending",
  "action": "borrow",
  "protocol": "morpho",
  "chain": "base",
  "asset": "USDC",
  "amount": "500.00",
  "asset_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "protocol_address": "0x...",
  "value_usd": "500.00",
  "gas_estimate": "180000",
  "borrow_apy": "3.75",
  "health_factor_after": "1.8",
  "collateral_required": "1000.00"
}
```

#### Leverage Loop Action
```json
{
  "action_type": "lending",
  "action": "leverage_loop",
  "protocol": "morpho",
  "chain": "base",
  "asset": "USDC",
  "amount": "1000.00",
  "target_leverage": "3.0",
  "execution_mode": "multi_step",
  "loop_id": "uuid-123",
  "steps": [
    {
      "step": 1,
      "action": "loop_supply",
      "amount": "1000.00",
      "description": "Supply 1000 USDC as collateral"
    },
    {
      "step": 2,
      "action": "loop_borrow",
      "amount": "750.00",
      "description": "Borrow 750 USDC against collateral"
    },
    {
      "step": 3,
      "action": "loop_swap",
      "amount": "750.00",
      "from_token": "USDC",
      "to_token": "ETH",
      "description": "Swap borrowed USDC to ETH"
    }
  ],
  "current_step": 1,
  "total_steps": 3
}
```

### Database Persistence

All lending operations are automatically saved to the `transactions` table:

**Fields Saved:**
- `tx_hash`: Blockchain transaction hash
- `action`: Lending action type (supply, borrow, etc.)
- `protocol`: Protocol name (morpho, aave)
- `asset`: Asset symbol (USDC, ETH, etc.)
- `amount`: Transaction amount
- `chain`: Blockchain network
- `type`: Transaction type (FUND, SEND, SWAP)
- `tx_metadata`: Full JSON metadata including loop_id, health_factor, APY

**Example Database Record:**
```sql
INSERT INTO transactions (
  user_id, wallet_id, type, chain,
  asset_in, amount_in, tx_hash, status,
  dex_aggregator, tx_metadata, created_at
) VALUES (
  123, 1, 'FUND', 'base',
  'USDC', 1000.00, '0x123...', 'SUCCESS',
  'morpho_supply', '{"action": "supply", "protocol": "morpho", ...}', NOW()
);
```

### API Response Format

```json
{
  "message": "Supply transaction confirmed on morpho.",
  "metadata": {
    "action": "supply",
    "protocol": "morpho",
    "transaction_hash": "0x123...",
    "transaction_id": 43,
    "loop_id": "uuid-here",
    "step_completed": 1,
    "total_steps": 3,
    "status": "in_progress",
    "saved_to_db": true,
    "current_apy": "5.25",
    "health_factor": "2.5"
  }
}
```

### Health Factor Warning

⚠️ **Important**: Always check `health_factor` before borrowing!

- **Health Factor > 1.5**: Safe position
- **Health Factor 1.2-1.5**: Moderate risk
- **Health Factor < 1.2**: High liquidation risk
- **Health Factor < 1.0**: Position will be liquidated

### Gas Estimation

| Action | Estimated Gas | USD Cost (Base) |
|--------|---------------|-----------------|
| Supply | 150,000-200,000 | ~$0.30-0.40 |
| Withdraw | 180,000-230,000 | ~$0.35-0.45 |
| Borrow | 180,000-250,000 | ~$0.35-0.50 |
| Repay | 150,000-200,000 | ~$0.30-0.40 |
| Leverage Loop (3 steps) | ~600,000 total | ~$1.20-1.50 |

### Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Insufficient collateral` | Not enough collateral for borrow | Supply more assets first |
| `Health factor too low` | Borrowing would risk liquidation | Reduce borrow amount |
| `Allowance too low` | ERC20 not approved | Approve token first |
| `Liquidation threshold reached` | Position undercollateralized | Repay debt or add collateral |

### Testing Checklist

- [ ] Supply USDC to Morpho on Base
- [ ] Withdraw supplied assets
- [ ] Borrow against collateral
- [ ] Repay borrowed amount
- [ ] Execute 3x leverage loop
- [ ] Handle insufficient collateral error
- [ ] Display health factor warnings
- [ ] Report to `/execute` endpoint
- [ ] Verify database persistence

### References

- [Morpho Protocol Docs](https://docs.morpho.org/)
- [Aave V3 Docs](https://docs.aave.com/developers/)
- [LENDING_EXECUTION_SPEC.md](./LENDING_EXECUTION_SPEC.md) - Complete frontend spec
- [LENDING_IMPLEMENTATION_PLAN.md](./LENDING_IMPLEMENTATION_PLAN.md) - Implementation guide
