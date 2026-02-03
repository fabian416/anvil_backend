# Money Market Frontend Documentation

This directory contains frontend specifications for implementing money market operations with Aave and other DeFi protocols.

## Documents

| Document | Description |
|----------|-------------|
| [MONEY_MARKET_EXECUTION_SPEC.md](./MONEY_MARKET_EXECUTION_SPEC.md) | Complete specification for executing money market operations with Privy |
| [MONEY_MARKET_IMPLEMENTATION_PLAN.md](./MONEY_MARKET_IMPLEMENTATION_PLAN.md) | Complete implementation plan for money market features |

## Quick Reference

### Action Detection

```typescript
const isMoneyMarketAction = (execute) => {
  return ["money_market_deposit", "money_market_withdraw",
          "rate_comparison", "yield_optimization"]
         .includes(execute.action);
};
```

### Execution Flow by Action

#### Money Market Deposit
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
│ 2. Deposit to Money Market            │  ← EVM tx (Privy)
│    (Aave Pool)                        │
└───────────────────────────────────────┘
        │
        ▼
User earns yield at current APY
```

#### Money Market Withdrawal
```
User has funds in Money Market
        │
        ▼
┌───────────────────────────────────────┐
│ 1. Withdraw from Money Market         │  ← EVM tx (Privy)
└───────────────────────────────────────┘
        │
        ▼
User receives principal + earned yield
```

#### Rate Comparison (Read-Only)
```
User queries best rates
        │
        ▼
┌───────────────────────────────────────┐
│ Backend queries all protocols         │
│ - Aave APY: 5.2%                      │
│ - Morpho APY: 5.8%                    │
│ - Compound APY: 4.9%                  │
└───────────────────────────────────────┘
        │
        ▼
Display ranked results to user
```

#### Yield Optimization (Multi-Protocol)
```
User has 10,000 USDC
        │
        ▼
┌───────────────────────────────────────┐
│ Algorithm finds optimal allocation:   │
│ - 60% Morpho (highest APY)            │
│ - 30% Aave (liquidity buffer)         │
│ - 10% Reserve (gas coverage)          │
└───────────────────────────────────────┘
        │
        ▼
Execute deposits across protocols
```

### Supported Protocols

| Protocol | Type | Chains | Features |
|----------|------|--------|----------|
| `aave` | Money Market Pool | Multiple chains | High liquidity, stable rates |
| `compound` | Money Market Pool | Ethereum, Base | Established, governance tokens |
| `morpho` | Optimized Money Market | Base, Ethereum | Higher APY, P2P matching |

### Supported Actions

| Action | Type | Description |
|--------|------|-------------|
| `money_market_deposit` | FUND | Deposit assets to earn yield |
| `money_market_withdraw` | SEND | Withdraw deposited assets + yield |
| `rate_comparison` | READ | Compare APYs across protocols |
| `yield_optimization` | MULTI | Allocate funds to maximize yield |

### Key Differences from Lending

| Feature | Money Market | Lending |
|---------|--------------|---------|
| Purpose | Simple yield on deposits | Borrowing against collateral |
| Collateral | Not required | Required for borrowing |
| Risk | Lower (no liquidation) | Higher (liquidation risk) |
| Complexity | Simple deposits | Complex (borrow, health factor) |
| Transaction Type | FUND/SEND | FUND/SEND/SWAP |
| Multi-Protocol | Yes (optimization) | Usually single protocol |

### Example Execute Payload

#### Money Market Deposit
```json
{
  "action_type": "money_market",
  "action": "money_market_deposit",
  "protocol": "aave",
  "chain": "base",
  "asset": "USDC",
  "amount": "5000.00",
  "asset_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "protocol_address": "0x...",
  "value_usd": "5000.00",
  "gas_estimate": "120000",
  "current_apy": "5.25",
  "projected_earnings_30d": "21.87",
  "projected_earnings_365d": "262.50"
}
```

#### Rate Comparison
```json
{
  "action_type": "money_market",
  "action": "rate_comparison",
  "asset": "USDC",
  "chain": "base",
  "rates": [
    {
      "protocol": "morpho",
      "apy": "5.8",
      "tvl": "50000000",
      "risk_score": 85
    },
    {
      "protocol": "aave",
      "apy": "5.2",
      "tvl": "1000000000",
      "risk_score": 95
    },
    {
      "protocol": "compound",
      "apy": "4.9",
      "tvl": "500000000",
      "risk_score": 90
    }
  ]
}
```

#### Yield Optimization
```json
{
  "action_type": "money_market",
  "action": "yield_optimization",
  "asset": "USDC",
  "amount": "10000.00",
  "chain": "base",
  "execution_mode": "multi_protocol",
  "allocation": [
    {
      "protocol": "morpho",
      "amount": "6000.00",
      "apy": "5.8",
      "percentage": 60
    },
    {
      "protocol": "aave",
      "amount": "3000.00",
      "apy": "5.2",
      "percentage": 30
    },
    {
      "protocol": "reserve",
      "amount": "1000.00",
      "apy": "0",
      "percentage": 10
    }
  ],
  "weighted_apy": "5.48",
  "steps": [
    {
      "step": 1,
      "protocol": "morpho",
      "action": "money_market_deposit",
      "amount": "6000.00"
    },
    {
      "step": 2,
      "protocol": "aave",
      "action": "money_market_deposit",
      "amount": "3000.00"
    }
  ]
}
```

### Database Persistence

All money market operations are automatically saved to the `transactions` table:

**Fields Saved:**
- `tx_hash`: Blockchain transaction hash
- `action`: Money market action type
- `protocol`: Protocol name (aave, morpho, compound)
- `asset`: Asset symbol (USDC, ETH, etc.)
- `amount`: Transaction amount
- `chain`: Blockchain network
- `type`: Transaction type (FUND for deposits, SEND for withdrawals)
- `tx_metadata`: Full JSON metadata including APY, projected earnings

**Example Database Record:**
```sql
INSERT INTO transactions (
  user_id, wallet_id, type, chain,
  asset_in, amount_in, tx_hash, status,
  dex_aggregator, tx_metadata, created_at
) VALUES (
  123, 1, 'FUND', 'base',
  'USDC', 5000.00, '0xabc...', 'SUCCESS',
  'aave_money_market', '{"action": "money_market_deposit", "apy": "5.25", ...}', NOW()
);
```

### API Response Format

```json
{
  "message": "Deposit confirmed on aave money market.",
  "metadata": {
    "action": "money_market_deposit",
    "protocol": "aave",
    "transaction_hash": "0xabc...",
    "transaction_id": 44,
    "saved_to_db": true,
    "apy": "5.25",
    "status": "complete",
    "projected_earnings_30d": "21.87",
    "projected_earnings_365d": "262.50"
  }
}
```

### APY Comparison Table

| Protocol | USDC APY | ETH APY | Risk Level | TVL |
|----------|----------|---------|------------|-----|
| Morpho | 5.8% | 3.2% | Medium | $50M |
| Aave | 5.2% | 2.9% | Low | $1B+ |
| Compound | 4.9% | 2.7% | Low | $500M |

*APYs are variable and change based on market conditions*

### Gas Estimation

| Action | Estimated Gas | USD Cost (Base) |
|--------|---------------|-----------------|
| Deposit | 100,000-150,000 | ~$0.20-0.30 |
| Withdraw | 120,000-180,000 | ~$0.25-0.35 |
| Rate Comparison | 0 (read-only) | $0 |
| Yield Optimization (2 protocols) | ~300,000 total | ~$0.60-0.75 |

### Error Handling

Common errors and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| `Insufficient balance` | Not enough assets | Check wallet balance |
| `Allowance too low` | ERC20 not approved | Approve token first |
| `Pool liquidity low` | Protocol has low liquidity | Try different protocol |
| `Minimum deposit not met` | Amount too small | Increase deposit amount |

### Benefits Over Traditional Lending

✅ **Simpler**: No collateral management
✅ **Lower Risk**: No liquidation risk
✅ **Flexible**: Withdraw anytime (subject to protocol liquidity)
✅ **Optimized**: Multi-protocol allocation for best yields
✅ **Transparent**: Real-time APY comparison

### Testing Checklist

- [ ] Deposit 5000 USDC to Aave money market
- [ ] Verify APY display (e.g., 5.25%)
- [ ] Check projected earnings calculation
- [ ] Withdraw deposited assets + yield
- [ ] Compare rates across protocols
- [ ] Execute yield optimization (multi-protocol)
- [ ] Verify all transactions saved to database
- [ ] Check transaction_id in API response

### Important Notes

⚠️ **APY Variability**: Money market APYs change based on supply/demand
⚠️ **Liquidity Risk**: Large withdrawals may face liquidity constraints
⚠️ **Protocol Risk**: Smart contract risk varies by protocol
✅ **No Liquidation**: Unlike lending, no collateral means no liquidation risk

### References

- [Aave V3 Docs](https://docs.aave.com/developers/)
- [Compound Docs](https://docs.compound.finance/)
- [Morpho Docs](https://docs.morpho.org/)
- [MONEY_MARKET_EXECUTION_SPEC.md](./MONEY_MARKET_EXECUTION_SPEC.md) - Complete frontend spec
- [MONEY_MARKET_IMPLEMENTATION_PLAN.md](./MONEY_MARKET_IMPLEMENTATION_PLAN.md) - Implementation guide
