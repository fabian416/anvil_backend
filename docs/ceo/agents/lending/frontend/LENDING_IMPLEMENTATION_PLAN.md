# Lending Implementation Plan

## Executive Summary

The backend fully supports lending and borrowing operations with **complete database persistence**. All lending transactions (supply, withdraw, borrow, repay, leverage loops) are automatically saved to the `transactions` table with comprehensive metadata.

## Current State ✅ FULLY IMPLEMENTED

### Backend (lending_workflow_agent.py) - ✅ COMPLETE

The backend **already implements** complete lending functionality:

- ✅ Morpho and Aave protocol integration
- ✅ Supply, withdraw, borrow, repay operations
- ✅ Leverage loop (multi-step) execution
- ✅ Health factor calculation and risk assessment
- ✅ APY tracking and display
- ✅ **Database persistence to `transactions` table**
- ✅ Complete metadata storage (protocol, action, APY, health_factor)
- ✅ Transaction type mapping (FUND/SEND/SWAP)

**Code location:** `src/app/presentation/http/controllers/chat/conversations_router.py` (lines 2069-2230)

### Frontend - REQUIRED CHANGES

The frontend needs to implement:

- ❌ Detect lending actions and show appropriate UI
- ❌ Execute supply/withdraw/borrow/repay with Privy
- ❌ Display health factor warnings
- ❌ Handle leverage loop multi-step execution
- ❌ Report completion to `/execute` API
- ❌ Show transaction history from database

---

## Database Persistence (Already Implemented)

### What Gets Saved

Every lending operation is automatically persisted to the `transactions` table:

```sql
INSERT INTO transactions (
  user_id,
  wallet_id,
  type,              -- FUND (supply/borrow) or SEND (withdraw/repay)
  chain,             -- 'base', 'ethereum', 'arbitrum'
  asset_in,          -- Asset symbol (USDC, ETH, etc.)
  amount_in,         -- Transaction amount
  tx_hash,           -- Blockchain transaction hash
  status,            -- SUCCESS
  dex_aggregator,    -- 'morpho_supply', 'aave_borrow', etc.
  tx_metadata,       -- Full JSON metadata
  created_at
) VALUES (
  123,               -- User ID
  1,                 -- Wallet ID
  'FUND',            -- Transaction type
  'base',            -- Chain
  'USDC',            -- Asset
  1000.00,           -- Amount
  '0x123...',        -- TX hash
  'SUCCESS',         -- Status
  'morpho_supply',   -- Protocol + action
  '{"action": "supply", "protocol": "morpho", "apy": "5.25", ...}',
  NOW()
);
```

### Metadata Structure

The `tx_metadata` JSONB field stores complete lending context:

```json
{
  "conversation_id": "uuid",
  "action": "supply",
  "protocol": "morpho",
  "asset": "USDC",
  "amount": "1000.00",
  "current_apy": "5.25",
  "health_factor": "2.5",
  "workflow_type": "lending",

  // For leverage loops
  "loop_id": "uuid",
  "step_completed": 1,
  "total_steps": 3,

  // Risk metrics
  "collateral_required": "500.00",
  "liquidation_threshold": "0.85"
}
```

### API Response Format

All `/execute` responses include database confirmation:

```json
{
  "message": "Supply transaction confirmed on morpho.",
  "metadata": {
    "action": "supply",
    "protocol": "morpho",
    "transaction_hash": "0x123...",
    "transaction_id": 43,        // ✅ Database ID
    "saved_to_db": true,         // ✅ Confirmation flag
    "current_apy": "5.25",
    "health_factor": "2.5",
    "status": "complete"
  }
}
```

---

## Complete Lending Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LENDING OPERATIONS FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

User's Privy Wallet on Base:
  - USDC: User's funds
  - ETH: For gas fees
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ SUPPLY: Deposit assets to earn yield                                        │
│                                                                              │
│ 1. User approves USDC to Morpho contract                                    │
│ 2. User supplies 1000 USDC to Morpho                                        │
│ 3. Backend saves to DB: type=FUND, action=supply, apy=5.25%                │
│ 4. User starts earning 5.25% APY on supplied USDC                           │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ BORROW: Borrow against collateral                                           │
│                                                                              │
│ 1. Check health factor (must be > 1.5 recommended)                          │
│ 2. User borrows 500 USDC against 1000 USDC collateral                      │
│ 3. Backend saves to DB: type=FUND, action=borrow, health_factor=2.0        │
│ 4. User receives 500 USDC, pays 3.75% APY                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ REPAY: Pay back borrowed amount                                             │
│                                                                              │
│ 1. User approves USDC to Morpho                                             │
│ 2. User repays 500 USDC                                                     │
│ 3. Backend saves to DB: type=SEND, action=repay                             │
│ 4. Debt cleared, health factor improves                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ WITHDRAW: Withdraw supplied assets                                          │
│                                                                              │
│ 1. User withdraws 1000 USDC from Morpho                                     │
│ 2. Backend saves to DB: type=SEND, action=withdraw                          │
│ 3. User receives original deposit + earned yield                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Leverage Loop Flow (Multi-Step)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEVERAGE LOOP (3x Leverage)                              │
└─────────────────────────────────────────────────────────────────────────────┘

User starts with 1000 USDC, targets 3x leverage on ETH
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LOOP 1                                                                       │
│ Step 1: Supply 1000 USDC as collateral                                      │
│         DB: type=FUND, action=loop_supply, step=1/9                         │
│ Step 2: Borrow 750 USDC (75% LTV)                                          │
│         DB: type=FUND, action=loop_borrow, step=2/9, health_factor=2.5     │
│ Step 3: Swap 750 USDC → ETH                                                │
│         DB: type=SWAP, action=loop_swap, step=3/9                          │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LOOP 2                                                                       │
│ Step 4: Supply ETH as collateral                                            │
│ Step 5: Borrow 562.5 USDC (75% of 750)                                     │
│ Step 6: Swap 562.5 USDC → ETH                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LOOP 3                                                                       │
│ Step 7: Supply ETH as collateral                                            │
│ Step 8: Borrow 421.87 USDC                                                  │
│ Step 9: Swap 421.87 USDC → ETH                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
Final Position:
- Total ETH exposure: ~3000 USDC worth
- Effective leverage: 3x
- Health Factor: 1.8 (safe)
- All 9 steps saved to database with loop_id
```

---

## Frontend Implementation

### 1. Install Dependencies

```bash
npm install @privy-io/react-auth viem
```

### 2. Lending Execution Hook

```typescript
// hooks/useLendingExecution.ts

import { useState, useCallback } from 'react';
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { parseUnits, encodeFunctionData, erc20Abi } from 'viem';

export function useLendingExecution(conversationId: string) {
  const { wallets } = useWallets();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeSupply = useCallback(async (execute: LendingExecutePayload) => {
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

    // 2. Supply
    const supplyTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: wallet.address,
        to: execute.protocol_address,
        data: encodeFunctionData({
          abi: getProtocolAbi(execute.protocol, 'supply'),
          functionName: 'supply',
          args: [execute.asset_address, amountWei, wallet.address, 0],
        }),
      }],
    });

    return supplyTx;
  }, [wallets]);

  const executeBorrow = useCallback(async (execute: LendingExecutePayload) => {
    if (wallets.length === 0) throw new Error('Wallet not connected');

    // Safety check
    if (execute.health_factor_after && parseFloat(execute.health_factor_after) < 1.2) {
      throw new Error('Health factor too low - transaction blocked for safety');
    }

    const wallet = wallets[0];
    const provider = await wallet.getEthereumProvider();
    await wallet.switchChain(getChainId(execute.chain));

    const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

    const borrowTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: wallet.address,
        to: execute.protocol_address,
        data: encodeFunctionData({
          abi: getProtocolAbi(execute.protocol, 'borrow'),
          functionName: 'borrow',
          args: [execute.asset_address, amountWei, 2, 0, wallet.address],
        }),
      }],
    });

    return borrowTx;
  }, [wallets]);

  const executeAction = useCallback(async (execute: LendingExecutePayload) => {
    setIsLoading(true);
    setError(null);

    try {
      let txHash: string;

      switch (execute.action) {
        case 'supply':
          txHash = await executeSupply(execute);
          break;
        case 'borrow':
          txHash = await executeBorrow(execute);
          break;
        // ... other actions
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
  }, [wallets, conversationId, executeSupply, executeBorrow]);

  return {
    executeAction,
    isLoading,
    error,
  };
}
```

### 3. Health Factor Component

```typescript
// components/HealthFactorDisplay.tsx

interface HealthFactorDisplayProps {
  currentHealthFactor: string | null;
  healthFactorAfter: string | null;
}

export function HealthFactorDisplay({
  currentHealthFactor,
  healthFactorAfter
}: HealthFactorDisplayProps) {
  const current = parseFloat(currentHealthFactor || '0');
  const after = parseFloat(healthFactorAfter || '0');

  const getRiskLevel = (hf: number) => {
    if (hf >= 2.0) return { label: 'Safe', color: 'bg-green-900/30 border-green-600 text-green-400' };
    if (hf >= 1.5) return { label: 'Good', color: 'bg-blue-900/30 border-blue-600 text-blue-400' };
    if (hf >= 1.2) return { label: 'Moderate', color: 'bg-yellow-900/30 border-yellow-600 text-yellow-400' };
    if (hf >= 1.0) return { label: 'Risky', color: 'bg-orange-900/30 border-orange-600 text-orange-400' };
    return { label: 'Liquidation!', color: 'bg-red-900/30 border-red-600 text-red-400' };
  };

  const currentRisk = getRiskLevel(current);
  const afterRisk = getRiskLevel(after);

  return (
    <div className="p-4 bg-gray-900 rounded-lg mb-4">
      <h4 className="font-semibold text-gray-200 mb-3">⚠️ Health Factor</h4>

      {/* Current Health Factor */}
      <div className={`p-3 border rounded-lg mb-2 ${currentRisk.color}`}>
        <div className="flex items-center justify-between">
          <span className="text-sm">Current:</span>
          <span className="font-bold text-lg">{current.toFixed(2)}</span>
        </div>
        <div className="text-xs mt-1">{currentRisk.label}</div>
      </div>

      {/* Health Factor After Transaction */}
      {healthFactorAfter && (
        <div className={`p-3 border rounded-lg ${afterRisk.color}`}>
          <div className="flex items-center justify-between">
            <span className="text-sm">After transaction:</span>
            <span className="font-bold text-lg">{after.toFixed(2)}</span>
          </div>
          <div className="text-xs mt-1">{afterRisk.label}</div>
        </div>
      )}

      {/* Warnings */}
      {after < 1.5 && after >= 1.2 && (
        <div className="mt-3 p-2 bg-yellow-900/30 border border-yellow-600 rounded text-yellow-400 text-sm">
          ⚠️ Warning: Lower health factor increases liquidation risk.
        </div>
      )}

      {after < 1.2 && after >= 1.0 && (
        <div className="mt-3 p-2 bg-orange-900/30 border border-orange-600 rounded text-orange-400 text-sm font-semibold">
          🚨 High Risk: This transaction significantly increases liquidation risk!
        </div>
      )}

      {after < 1.0 && (
        <div className="mt-3 p-2 bg-red-900/30 border border-red-600 rounded text-red-400 text-sm font-bold">
          🛑 BLOCKED: This transaction would result in immediate liquidation!
        </div>
      )}

      {/* Info */}
      <div className="mt-3 text-xs text-gray-400">
        <p>• Health Factor &gt; 1.5: Safe position</p>
        <p>• Health Factor 1.2-1.5: Moderate risk</p>
        <p>• Health Factor &lt; 1.2: High liquidation risk</p>
        <p>• Health Factor &lt; 1.0: Will be liquidated</p>
      </div>
    </div>
  );
}
```

### 4. Main Lending Execute Component

```typescript
// components/LendingExecuteButton.tsx

import { useLendingExecution } from '../hooks/useLendingExecution';
import { HealthFactorDisplay } from './HealthFactorDisplay';

interface Props {
  execute: LendingExecutePayload;
  conversationId: string;
  onSuccess: () => void;
  onError: (error: string) => void;
}

export function LendingExecuteButton({
  execute,
  conversationId,
  onSuccess,
  onError
}: Props) {
  const { executeAction, isLoading, error } = useLendingExecution(conversationId);

  const handleExecute = async () => {
    try {
      await executeAction(execute);
      onSuccess();
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    }
  };

  // Block dangerous transactions
  const isDangerous = execute.health_factor_after &&
                      parseFloat(execute.health_factor_after) < 1.0;

  return (
    <div>
      {/* Health Factor Display */}
      {(execute.health_factor || execute.health_factor_after) && (
        <HealthFactorDisplay
          currentHealthFactor={execute.health_factor}
          healthFactorAfter={execute.health_factor_after}
        />
      )}

      {/* APY Display */}
      {execute.current_apy && (
        <div className="p-3 bg-green-900/20 border border-green-600 rounded-lg mb-4">
          <div className="text-sm text-gray-400">Current APY</div>
          <div className="text-2xl font-bold text-green-400">
            {execute.current_apy}%
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900/30 text-red-400 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Execute Button */}
      <button
        onClick={handleExecute}
        disabled={isLoading || isDangerous}
        className={`w-full py-3 rounded-lg font-semibold transition-colors ${
          isDangerous
            ? 'bg-red-600 cursor-not-allowed opacity-50'
            : 'bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600'
        }`}
      >
        {isDangerous ? '🛑 Transaction Blocked (Liquidation Risk)' :
         isLoading ? 'Executing...' :
         `Execute ${execute.action} (${execute.protocol})`}
      </button>

      {/* Protocol Info */}
      <div className="mt-2 text-xs text-gray-400 text-center">
        Protocol: {execute.protocol} | Chain: {execute.chain}
      </div>
    </div>
  );
}
```

---

## Database Query Examples

### Get User's Lending History

```sql
-- All lending transactions for a user
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
  AND tx_metadata->>'workflow_type' = 'lending'
ORDER BY created_at DESC;
```

### Get Active Leverage Loops

```sql
-- All steps in a leverage loop
SELECT
  id,
  tx_metadata->>'action' as action,
  tx_metadata->>'step_completed' as step,
  tx_metadata->>'total_steps' as total_steps,
  amount_in,
  tx_hash,
  created_at
FROM transactions
WHERE user_id = 123
  AND tx_metadata->>'loop_id' = 'uuid-123'
ORDER BY created_at ASC;
```

### Calculate Total Supplied/Borrowed

```sql
-- Total supplied by protocol
SELECT
  tx_metadata->>'protocol' as protocol,
  SUM(amount_in) as total_supplied,
  COUNT(*) as transaction_count
FROM transactions
WHERE user_id = 123
  AND tx_metadata->>'action' = 'supply'
GROUP BY tx_metadata->>'protocol';
```

---

## Testing Checklist

### Single Actions
- [ ] Supply 1000 USDC to Morpho on Base
- [ ] Verify APY display (e.g., 5.25%)
- [ ] Borrow 500 USDC against collateral
- [ ] Check health factor display (should show > 1.5)
- [ ] Repay 500 USDC
- [ ] Withdraw 1000 USDC + earned yield
- [ ] Verify all transactions saved to database
- [ ] Check transaction_id in API response

### Risk Management
- [ ] Block borrow if health_factor_after < 1.0
- [ ] Show warning if health_factor_after < 1.5
- [ ] Display "Safe" for health_factor > 2.0
- [ ] Handle insufficient collateral error

### Leverage Loop
- [ ] Execute 3x leverage loop (9 steps)
- [ ] Verify each step reports to backend
- [ ] Check all steps have same loop_id in database
- [ ] Verify final leverage position

### Error Handling
- [ ] Handle insufficient balance error
- [ ] Handle approval failure
- [ ] Handle insufficient collateral
- [ ] Handle network errors

---

## Important Notes

### 1. Safety First
- Always check health factor before borrowing
- Block transactions if health_factor_after < 1.2
- Show clear warnings for risky positions
- Never allow transactions that guarantee liquidation

### 2. Database Persistence
- All operations automatically save to database
- No additional frontend code needed for persistence
- API response includes `transaction_id` and `saved_to_db` flag
- Query database for user transaction history

### 3. Gas Costs
- Supply: ~$0.30-0.40 on Base
- Borrow: ~$0.35-0.50 on Base
- Leverage loop (3x): ~$1.20-1.50 total

### 4. Protocol Differences

| Feature | Morpho | Aave |
|---------|--------|------|
| APY | Higher (optimized) | Standard |
| Liquidation | Lower risk | Standard risk |
| Gas | Slightly higher | Standard |
| Chains | Base, Ethereum | Multiple chains |

---

## References

- [Morpho Protocol Docs](https://docs.morpho.org/)
- [Aave V3 Docs](https://docs.aave.com/developers/)
- [Privy Docs](https://docs.privy.io/)
- [LENDING_EXECUTION_SPEC.md](./LENDING_EXECUTION_SPEC.md) - Complete frontend spec
