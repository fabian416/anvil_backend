# Money Market Implementation Plan

## Executive Summary

The backend fully supports money market operations with **complete database persistence**. All money market transactions (deposits, withdrawals, rate comparisons, yield optimization) are automatically saved to the `transactions` table with comprehensive metadata.

## Current State ✅ FULLY IMPLEMENTED

### Backend (money_market_workflow_agent.py) - ✅ COMPLETE

The backend **already implements** complete money market functionality:

- ✅ Aave, Compound, and Morpho protocol integration
- ✅ Deposit and withdrawal operations
- ✅ Rate comparison across protocols
- ✅ Yield optimization with multi-protocol allocation
- ✅ APY tracking and projected earnings calculation
- ✅ **Database persistence to `transactions` table**
- ✅ Complete metadata storage (protocol, action, APY)
- ✅ Transaction type mapping (FUND/SEND)

**Code location:** `src/app/presentation/http/controllers/chat/conversations_router.py` (lines 2282-2420)

### Frontend - REQUIRED CHANGES

The frontend needs to implement:

- ❌ Detect money market actions and show appropriate UI
- ❌ Execute deposits/withdrawals with Privy
- ❌ Display rate comparisons across protocols
- ❌ Handle yield optimization multi-protocol execution
- ❌ Show projected earnings calculations
- ❌ Report completion to `/execute` API
- ❌ Show transaction history from database

---

## Database Persistence (Already Implemented)

### What Gets Saved

Every money market operation is automatically persisted to the `transactions` table:

```sql
INSERT INTO transactions (
  user_id,
  wallet_id,
  type,              -- FUND (deposits) or SEND (withdrawals)
  chain,             -- 'base', 'ethereum', 'arbitrum'
  asset_in,          -- Asset symbol (USDC, ETH, etc.)
  amount_in,         -- Transaction amount
  tx_hash,           -- Blockchain transaction hash
  status,            -- SUCCESS
  dex_aggregator,    -- 'aave_money_market', 'morpho_money_market', etc.
  tx_metadata,       -- Full JSON metadata
  created_at
) VALUES (
  123,               -- User ID
  1,                 -- Wallet ID
  'FUND',            -- Transaction type
  'base',            -- Chain
  'USDC',            -- Asset
  5000.00,           -- Amount
  '0xabc...',        -- TX hash
  'SUCCESS',         -- Status
  'aave_money_market',   -- Protocol + action
  '{"action": "money_market_deposit", "protocol": "aave", "apy": "5.25", ...}',
  NOW()
);
```

### Metadata Structure

The `tx_metadata` JSONB field stores complete money market context:

```json
{
  "conversation_id": "uuid",
  "action": "money_market_deposit",
  "protocol": "aave",
  "asset": "USDC",
  "amount": "5000.00",
  "apy": "5.25",
  "workflow_type": "money_market",

  // Projected earnings
  "projected_earnings_30d": "21.87",
  "projected_earnings_365d": "262.50",

  // For yield optimization
  "allocation_strategy": [
    {"protocol": "morpho", "amount": "3000", "percentage": 60},
    {"protocol": "aave", "amount": "2000", "percentage": 40}
  ],
  "weighted_apy": "5.48"
}
```

### API Response Format

All `/execute` responses include database confirmation:

```json
{
  "message": "Deposit confirmed on aave money market.",
  "metadata": {
    "action": "money_market_deposit",
    "protocol": "aave",
    "transaction_hash": "0xabc...",
    "transaction_id": 44,        // ✅ Database ID
    "saved_to_db": true,         // ✅ Confirmation flag
    "apy": "5.25",
    "projected_earnings_30d": "21.87",
    "projected_earnings_365d": "262.50",
    "status": "complete"
  }
}
```

---

## Complete Money Market Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MONEY MARKET OPERATIONS FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

User's Privy Wallet on Base:
  - USDC: 10,000 (user's funds)
  - ETH: 0.001 (for gas fees)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: RATE COMPARISON (Read-Only)                                         │
│                                                                              │
│ Backend queries all protocols:                                              │
│ - Morpho: 5.8% APY, $50M TVL, Risk: 85/100                                 │
│ - Aave: 5.2% APY, $1B TVL, Risk: 95/100                                    │
│ - Compound: 4.9% APY, $500M TVL, Risk: 90/100                              │
│                                                                              │
│ Frontend displays ranked results, no transaction                            │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: YIELD OPTIMIZATION ALLOCATION                                       │
│                                                                              │
│ User chooses: "Optimize my 10,000 USDC"                                     │
│ Backend calculates optimal allocation:                                      │
│ - 60% Morpho (6,000 USDC) at 5.8% APY                                      │
│ - 30% Aave (3,000 USDC) at 5.2% APY                                        │
│ - 10% Reserve (1,000 USDC) for gas/liquidity                               │
│ Weighted APY: 5.48%                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: EXECUTE DEPOSITS (Multi-Protocol)                                   │
│                                                                              │
│ Step 3a: Deposit to Morpho                                                  │
│ 1. Approve 6,000 USDC to Morpho contract                                   │
│ 2. Deposit 6,000 USDC to Morpho                                            │
│ 3. Backend saves: type=FUND, protocol=morpho, apy=5.8%                     │
│ 4. Report to /execute endpoint                                              │
│                                                                              │
│ Step 3b: Deposit to Aave                                                    │
│ 1. Approve 3,000 USDC to Aave contract                                     │
│ 2. Deposit 3,000 USDC to Aave                                              │
│ 3. Backend saves: type=FUND, protocol=aave, apy=5.2%                       │
│ 4. Report to /execute endpoint                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RESULT: User's Optimized Position                                           │
│                                                                              │
│ - Total Deposited: 9,000 USDC (90% of funds)                               │
│ - Weighted APY: 5.48%                                                       │
│ - Projected Earnings (30d): ~$40.11                                         │
│ - Projected Earnings (365d): ~$493.20                                       │
│ - Reserve: 1,000 USDC (for future gas/opportunities)                       │
│                                                                              │
│ All transactions saved to database with complete metadata                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Withdrawal Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MONEY MARKET WITHDRAWAL FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

User has funds deposited in multiple protocols
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ WITHDRAW FROM MORPHO                                                         │
│                                                                              │
│ 1. User requests withdrawal of 3,000 USDC from Morpho                      │
│ 2. Check available balance (principal + earned yield)                       │
│ 3. Execute withdraw transaction (no approval needed)                        │
│ 4. Backend saves: type=SEND, action=money_market_withdraw                  │
│ 5. User receives: 3,000 USDC + 23.50 USDC earned yield                     │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ WITHDRAW FROM AAVE                                                           │
│                                                                              │
│ 1. User requests withdrawal of 2,000 USDC from Aave                        │
│ 2. Execute withdraw transaction                                              │
│ 3. Backend saves: type=SEND, protocol=aave                                  │
│ 4. User receives: 2,000 USDC + 8.67 USDC earned yield                      │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
Total Withdrawn: 5,000 USDC principal + 32.17 USDC yield
```

---

## Frontend Implementation

### 1. Install Dependencies

```bash
npm install @privy-io/react-auth viem
```

### 2. Money Market Execution Hook

```typescript
// hooks/useMoneyMarketExecution.ts

import { useState, useCallback } from 'react';
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { parseUnits, encodeFunctionData, erc20Abi } from 'viem';

export function useMoneyMarketExecution(conversationId: string) {
  const { wallets } = useWallets();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeDeposit = useCallback(async (execute: MoneyMarketExecutePayload) => {
    if (wallets.length === 0) throw new Error('Wallet not connected');

    const wallet = wallets[0];
    const provider = await wallet.getEthereumProvider();
    await wallet.switchChain(getChainId(execute.chain));

    const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

    // 1. Approve
    const approveTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: wallet.address,
        to: execute.asset_address,
        data: encodeFunctionData({
          abi: erc20Abi,
          functionName: 'approve',
          args: [execute.protocol_address as `0x${string}`, amountWei],
        }),
      }],
    });
    await waitForTransaction(provider, approveTx);

    // 2. Deposit
    const depositTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: wallet.address,
        to: execute.protocol_address,
        data: encodeFunctionData({
          abi: getMoneyMarketAbi(execute.protocol),
          functionName: 'supply',
          args: [execute.asset_address, amountWei, wallet.address, 0],
        }),
      }],
    });

    return depositTx;
  }, [wallets]);

  const executeWithdraw = useCallback(async (execute: MoneyMarketExecutePayload) => {
    if (wallets.length === 0) throw new Error('Wallet not connected');

    const wallet = wallets[0];
    const provider = await wallet.getEthereumProvider();
    await wallet.switchChain(getChainId(execute.chain));

    const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

    // No approval needed for withdraw
    const withdrawTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: wallet.address,
        to: execute.protocol_address,
        data: encodeFunctionData({
          abi: getMoneyMarketAbi(execute.protocol),
          functionName: 'withdraw',
          args: [execute.asset_address, amountWei, wallet.address],
        }),
      }],
    });

    return withdrawTx;
  }, [wallets]);

  const executeAction = useCallback(async (execute: MoneyMarketExecutePayload) => {
    setIsLoading(true);
    setError(null);

    try {
      let txHash: string;

      switch (execute.action) {
        case 'money_market_deposit':
          txHash = await executeDeposit(execute);
          break;
        case 'money_market_withdraw':
          txHash = await executeWithdraw(execute);
          break;
        default:
          throw new Error(`Unknown action: ${execute.action}`);
      }

      // Report to backend
      const response = await fetch(
        `/api/v1/conversations/${conversationId}/execute`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`,
          },
          body: JSON.stringify({
            transaction_hash: txHash,
            metadata: {
              action: execute.action,
              protocol: execute.protocol,
              asset: execute.asset,
              amount: execute.amount,
              apy: execute.current_apy,
              chain: execute.chain,
            },
          }),
        }
      );

      const data = await response.json();
      return data;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [wallets, conversationId, executeDeposit, executeWithdraw]);

  return {
    executeAction,
    isLoading,
    error,
  };
}
```

### 3. Rate Comparison Component

```typescript
// components/RateComparison.tsx

interface RateComparisonProps {
  rates: Array<{
    protocol: string;
    apy: string;
    tvl: string;
    risk_score: number;
  }>;
  asset: string;
}

export function RateComparison({ rates, asset }: RateComparisonProps) {
  const sortedRates = [...rates].sort((a, b) =>
    parseFloat(b.apy) - parseFloat(a.apy)
  );

  return (
    <div className="p-4 bg-gray-900 rounded-lg">
      <h3 className="text-xl font-semibold mb-4">
        Best {asset} Rates Across Protocols
      </h3>

      <div className="space-y-3">
        {sortedRates.map((rate, index) => (
          <div
            key={rate.protocol}
            className={`p-4 rounded-lg border ${
              index === 0
                ? 'bg-green-900/20 border-green-600'
                : 'bg-gray-800 border-gray-700'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                {index === 0 && <span className="text-xl">🏆</span>}
                <span className="font-bold text-lg text-white">
                  {rate.protocol.toUpperCase()}
                </span>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-400">
                  {rate.apy}%
                </div>
                <div className="text-xs text-gray-400">APY</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-3 text-sm">
              <div>
                <div className="text-gray-400">Total Value Locked</div>
                <div className="text-white font-semibold">
                  ${formatTVL(rate.tvl)}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Risk Score</div>
                <div className={`font-bold ${
                  rate.risk_score >= 90 ? 'text-green-400' :
                  rate.risk_score >= 70 ? 'text-yellow-400' :
                  'text-orange-400'
                }`}>
                  {rate.risk_score}/100
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-blue-900/20 border border-blue-600 rounded-lg text-sm text-gray-300">
        💡 Tip: Higher APY protocols may have lower TVL and higher risk.
        Consider diversifying across multiple protocols.
      </div>
    </div>
  );
}

function formatTVL(tvl: string): string {
  const num = parseFloat(tvl);
  if (num >= 1e9) return `${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`;
  return num.toFixed(0);
}
```

### 4. Projected Earnings Component

```typescript
// components/ProjectedEarnings.tsx

interface ProjectedEarningsProps {
  amount: string;
  apy: string;
  asset: string;
}

export function ProjectedEarnings({ amount, apy, asset }: ProjectedEarningsProps) {
  const principal = parseFloat(amount);
  const annualRate = parseFloat(apy) / 100;

  const calculateEarnings = (days: number) => {
    return (principal * annualRate * days) / 365;
  };

  const periods = [
    { label: '30 days', days: 30 },
    { label: '90 days', days: 90 },
    { label: '180 days', days: 180 },
    { label: '1 year', days: 365 },
  ];

  return (
    <div className="p-4 bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-600 rounded-lg">
      <h4 className="font-semibold text-green-400 mb-3 flex items-center gap-2">
        <span>💰</span>
        <span>Projected Earnings</span>
      </h4>

      <div className="space-y-2">
        {periods.map((period) => {
          const earnings = calculateEarnings(period.days);
          return (
            <div
              key={period.label}
              className={`flex items-center justify-between py-2 ${
                period.days === 365 ? 'border-t border-gray-700 pt-3' : ''
              }`}
            >
              <span className="text-gray-400">{period.label}:</span>
              <span className={`font-bold ${
                period.days === 365 ? 'text-xl text-green-400' : 'text-white'
              }`}>
                +{earnings.toFixed(2)} {asset}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-gray-400">
        ⚠️ Based on current APY of {apy}%. Rates are variable and may change.
        Earnings shown are estimates and not guaranteed.
      </div>
    </div>
  );
}
```

### 5. Yield Optimization Component

```typescript
// components/YieldOptimization.tsx

interface AllocationStrategy {
  protocol: string;
  amount: string;
  apy: string;
  percentage: number;
}

interface YieldOptimizationProps {
  allocation: AllocationStrategy[];
  totalAmount: string;
  weightedAPY: string;
  asset: string;
  onExecute: () => void;
  isLoading: boolean;
}

export function YieldOptimization({
  allocation,
  totalAmount,
  weightedAPY,
  asset,
  onExecute,
  isLoading
}: YieldOptimizationProps) {
  return (
    <div className="space-y-4">
      {/* Weighted APY Banner */}
      <div className="p-4 bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-600 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-gray-400 text-sm">Optimized Weighted APY</div>
            <div className="text-3xl font-bold text-green-400">{weightedAPY}%</div>
          </div>
          <div className="text-right">
            <div className="text-gray-400 text-sm">Total Allocation</div>
            <div className="text-2xl font-bold text-white">
              {totalAmount} {asset}
            </div>
          </div>
        </div>
      </div>

      {/* Allocation Strategy */}
      <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
        <h4 className="font-semibold text-white mb-3">📊 Allocation Strategy</h4>

        <div className="space-y-3">
          {allocation.map((alloc, index) => (
            <div key={alloc.protocol} className="p-3 bg-gray-800 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${
                    index === 0 ? 'bg-green-400' :
                    index === 1 ? 'bg-blue-400' :
                    index === 2 ? 'bg-purple-400' :
                    'bg-gray-400'
                  }`} />
                  <span className="font-semibold text-white">
                    {alloc.protocol.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm font-semibold text-green-400">
                  {alloc.apy}% APY
                </span>
              </div>

              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-gray-400">{alloc.percentage}% allocation</span>
                <span className="font-bold text-white">
                  {alloc.amount} {asset}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    index === 0 ? 'bg-green-400' :
                    index === 1 ? 'bg-blue-400' :
                    index === 2 ? 'bg-purple-400' :
                    'bg-gray-400'
                  }`}
                  style={{ width: `${alloc.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Execute Button */}
      <button
        onClick={onExecute}
        disabled={isLoading}
        className="w-full py-4 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-600 rounded-lg font-bold text-lg transition-all"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin">⏳</span>
            Executing Optimization...
          </span>
        ) : (
          `🚀 Execute Optimal Allocation`
        )}
      </button>

      {/* Info */}
      <div className="text-xs text-gray-400 text-center">
        This will deposit your funds across {allocation.length} protocols for optimal yield
      </div>
    </div>
  );
}
```

---

## Database Query Examples

### Get User's Money Market History

```sql
-- All money market transactions for a user
SELECT
  id,
  type,
  chain,
  asset_in,
  amount_in,
  tx_hash,
  dex_aggregator,
  tx_metadata->>'action' as action,
  tx_metadata->>'protocol' as protocol,
  tx_metadata->>'apy' as apy,
  created_at
FROM transactions
WHERE user_id = 123
  AND tx_metadata->>'workflow_type' = 'money_market'
ORDER BY created_at DESC;
```

### Calculate Total Deposits by Protocol

```sql
-- Total deposited per protocol
SELECT
  tx_metadata->>'protocol' as protocol,
  SUM(amount_in) as total_deposited,
  AVG(CAST(tx_metadata->>'apy' AS DECIMAL)) as avg_apy,
  COUNT(*) as transaction_count
FROM transactions
WHERE user_id = 123
  AND tx_metadata->>'action' = 'money_market_deposit'
GROUP BY tx_metadata->>'protocol';
```

### Track Yield Optimization Strategies

```sql
-- Get yield optimization allocations
SELECT
  id,
  tx_metadata->>'protocol' as protocol,
  amount_in,
  tx_metadata->>'apy' as apy,
  tx_metadata->'allocation_strategy' as strategy,
  tx_metadata->>'weighted_apy' as weighted_apy,
  created_at
FROM transactions
WHERE user_id = 123
  AND tx_metadata->>'action' = 'yield_optimization'
ORDER BY created_at DESC;
```

---

## Testing Checklist

### Single Protocol Operations
- [ ] Deposit 5,000 USDC to Aave on Base
- [ ] Verify APY display (e.g., 5.25%)
- [ ] Check projected earnings calculations
- [ ] Withdraw 5,000 USDC + yield from Aave
- [ ] Verify database persistence with transaction_id

### Rate Comparison
- [ ] Display rates from 3+ protocols
- [ ] Sort by APY (highest first)
- [ ] Show TVL and risk scores
- [ ] Verify no database record (read-only)

### Yield Optimization
- [ ] Execute multi-protocol allocation (2-3 protocols)
- [ ] Verify each deposit reports to backend
- [ ] Check all deposits saved with same optimization ID
- [ ] Verify weighted APY calculation

### Error Handling
- [ ] Handle insufficient balance error
- [ ] Handle low liquidity warning
- [ ] Handle approval failure
- [ ] Handle minimum deposit not met

---

## Important Notes

### 1. Simplicity vs Lending
- **No Collateral**: Money markets don't require collateral management
- **No Liquidation**: No liquidation risk unlike lending/borrowing
- **Lower Complexity**: Simpler UX, fewer risk warnings needed
- **Flexible Withdrawals**: Can withdraw anytime (subject to liquidity)

### 2. APY Variability
- Money market APYs change frequently based on supply/demand
- Display "APY is variable" warnings
- Projected earnings are estimates, not guarantees
- Consider showing historical APY trends

### 3. Multi-Protocol Benefits
- **Diversification**: Spread risk across protocols
- **Optimization**: Maximize yield through smart allocation
- **Liquidity**: Maintain some funds in reserve
- **Gas Efficiency**: Batch transactions where possible

### 4. Gas Costs

| Operation | Estimated Cost (Base) |
|-----------|----------------------|
| Single deposit | ~$0.20-0.30 |
| Single withdraw | ~$0.25-0.35 |
| Yield optimization (2 protocols) | ~$0.60-0.75 |
| Yield optimization (3 protocols) | ~$0.90-1.10 |

### 5. Protocol Comparison

| Protocol | Best For | APY Range | Risk Level |
|----------|----------|-----------|------------|
| Morpho | Highest APY | 5-8% | Medium |
| Aave | Liquidity & Safety | 4-6% | Low |
| Compound | Balance | 4-6% | Low-Medium |

---

## References

- [Aave V3 Docs](https://docs.aave.com/developers/)
- [Compound Docs](https://docs.compound.finance/)
- [Morpho Docs](https://docs.morpho.org/)
- [Privy Docs](https://docs.privy.io/)
- [MONEY_MARKET_EXECUTION_SPEC.md](./MONEY_MARKET_EXECUTION_SPEC.md) - Complete frontend spec
