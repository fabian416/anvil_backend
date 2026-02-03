# Money Market Execution Frontend Specification

## Overview

This document specifies how the frontend should execute money market operations based on the `execute` payload from the backend. Money market operations are simpler than lending (no collateral/borrowing) but support multi-protocol optimization.

## Supported Protocols

| Protocol | Type | Execution Method | Asset Addresses |
|----------|------|------------------|-----------------|
| `aave` | Money Market Pool | Privy + EVM Transaction | Valid ERC-20 addresses |
| `compound` | Money Market Pool | Privy + EVM Transaction | Valid ERC-20 addresses |
| `morpho` | Optimized Money Market | Privy + EVM Transaction | Valid ERC-20 addresses |

---

## Execute Payload Structure

```typescript
interface MoneyMarketExecutePayload {
  action_type: "money_market";
  action: "money_market_deposit" | "money_market_withdraw" | "rate_comparison" | "yield_optimization";
  protocol?: string;                // e.g., "aave", "compound", "morpho"
  chain: string;                    // e.g., "base", "ethereum", "arbitrum"

  // Asset info
  asset: string;                    // e.g., "USDC", "ETH"
  amount: string;                   // Amount (human readable)
  asset_address?: string;           // ERC-20 token address
  protocol_address?: string;        // Protocol contract address

  // Financial data
  value_usd: string;                       // USD value of transaction
  current_apy: string | null;              // Current APY
  projected_earnings_30d?: string;         // Expected earnings in 30 days
  projected_earnings_365d?: string;        // Expected earnings in 1 year

  // Gas & fees
  gas_estimate: string;             // Estimated gas units
  network_fee_usd: string | null;   // Estimated network fee in USD

  // Rate comparison (for rate_comparison action)
  rates?: RateComparison[];

  // Yield optimization (for yield_optimization action)
  execution_mode?: "single" | "multi_protocol";
  allocation?: AllocationStrategy[];
  weighted_apy?: string;
  steps?: MoneyMarketStep[];
}

interface RateComparison {
  protocol: string;
  apy: string;
  tvl: string;              // Total Value Locked
  risk_score: number;       // 0-100, higher is safer
  liquidity: string;        // Available liquidity
}

interface AllocationStrategy {
  protocol: string;
  amount: string;
  apy: string;
  percentage: number;       // % of total allocation
}

interface MoneyMarketStep {
  step: number;
  protocol: string;
  action: "money_market_deposit" | "money_market_withdraw";
  amount: string;
  apy: string;
  status: "pending" | "in_progress" | "completed" | "error";
}
```

---

## Action Type Mapping

The backend maps money market actions to transaction types:

```typescript
const ACTION_TO_TX_TYPE: Record<string, TransactionType> = {
  "money_market_deposit": "FUND",     // Deposit into protocol
  "money_market_withdraw": "SEND",    // Withdraw from protocol
  "rate_comparison": null,            // Read-only, no transaction
  "yield_optimization": "FUND",       // Multi-protocol deposits
};
```

---

## Execution Flow

### 1. Money Market Deposit - Single Protocol

**User deposits assets to earn yield**

```typescript
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { encodeFunctionData, erc20Abi, parseUnits } from "viem";

async function executeMoneyMarketDeposit(
  execute: MoneyMarketExecutePayload,
  wallet: any
): Promise<string> {

  const provider = await wallet.getEthereumProvider();
  await wallet.switchChain(getChainId(execute.chain));

  const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

  // 1. Approve token to protocol
  const approveTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.asset_address,
      data: encodeFunctionData({
        abi: erc20Abi,
        functionName: "approve",
        args: [execute.protocol_address as `0x${string}`, amountWei],
      }),
    }],
  });
  await waitForTransaction(provider, approveTx);

  // 2. Deposit to money market (using Aave as example)
  const depositTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: AAVE_MONEY_MARKET_ABI,
        functionName: "supply",
        args: [execute.asset_address, amountWei, wallet.address, 0],
      }),
    }],
  });

  return depositTx;
}
```

### 2. Money Market Withdrawal

**User withdraws deposited assets + earned yield**

```typescript
async function executeMoneyMarketWithdraw(
  execute: MoneyMarketExecutePayload,
  wallet: any
): Promise<string> {

  const provider = await wallet.getEthereumProvider();
  await wallet.switchChain(getChainId(execute.chain));

  const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

  // No approval needed for withdraw
  const withdrawTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: AAVE_MONEY_MARKET_ABI,
        functionName: "withdraw",
        args: [
          execute.asset_address,
          amountWei,
          wallet.address
        ],
      }),
    }],
  });

  return withdrawTx;
}
```

### 3. Rate Comparison - Read-Only

**Display APYs across protocols (no transaction)**

```typescript
interface RateComparisonDisplayProps {
  rates: RateComparison[];
  asset: string;
}

export function RateComparisonDisplay({ rates, asset }: RateComparisonDisplayProps) {
  // Sort by APY descending
  const sortedRates = [...rates].sort((a, b) => parseFloat(b.apy) - parseFloat(a.apy));

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-lg">Best {asset} Rates</h3>

      {sortedRates.map((rate, index) => (
        <div
          key={rate.protocol}
          className="p-4 bg-gray-800 rounded-lg border border-gray-700"
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              {index === 0 && <span className="text-yellow-400">🏆</span>}
              <span className="font-semibold text-white">
                {rate.protocol.toUpperCase()}
              </span>
            </div>
            <span className="text-2xl font-bold text-green-400">
              {rate.apy}%
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm text-gray-400">
            <div>
              <span className="block">TVL</span>
              <span className="text-white">${formatNumber(rate.tvl)}</span>
            </div>
            <div>
              <span className="block">Risk Score</span>
              <span className={`font-semibold ${
                rate.risk_score >= 90 ? 'text-green-400' :
                rate.risk_score >= 70 ? 'text-yellow-400' :
                'text-orange-400'
              }`}>
                {rate.risk_score}/100
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 4. Yield Optimization - Multi-Protocol

**Allocate funds across multiple protocols for optimal yield**

```typescript
async function executeYieldOptimization(
  execute: MoneyMarketExecutePayload,
  wallet: any,
  conversationId: string,
  onStepUpdate: (stepId: number, status: string) => void
): Promise<void> {

  if (execute.execution_mode !== "multi_protocol" || !execute.steps) {
    throw new Error("Invalid yield optimization configuration");
  }

  for (const step of execute.steps) {
    onStepUpdate(step.step, "in_progress");

    try {
      let txHash: string;

      if (step.action === "money_market_deposit") {
        txHash = await executeMoneyMarketDeposit({
          ...execute,
          action: "money_market_deposit",
          protocol: step.protocol,
          amount: step.amount,
        }, wallet);

        // Report step completion to backend
        await reportStepComplete(conversationId, {
          transaction_hash: txHash,
          metadata: {
            action: step.action,
            protocol: step.protocol,
            amount: step.amount,
            apy: step.apy,
            step_completed: step.step,
          },
        });
      }

      onStepUpdate(step.step, "completed");

    } catch (error) {
      onStepUpdate(step.step, "error");
      throw error;
    }
  }
}
```

---

## Protocol ABIs

### Aave V3 Money Market ABI

```typescript
const AAVE_MONEY_MARKET_ABI = [
  {
    name: "supply",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "onBehalfOf", type: "address" },
      { name: "referralCode", type: "uint16" }
    ],
    outputs: [],
  },
  {
    name: "withdraw",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "to", type: "address" }
    ],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;
```

### Compound Money Market ABI (cToken)

```typescript
const COMPOUND_MONEY_MARKET_ABI = [
  {
    name: "mint",
    type: "function",
    inputs: [
      { name: "mintAmount", type: "uint256" }
    ],
    outputs: [{ name: "", type: "uint256" }],
  },
  {
    name: "redeem",
    type: "function",
    inputs: [
      { name: "redeemTokens", type: "uint256" }
    ],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;
```

---

## Chain Configuration

```typescript
const MONEY_MARKET_CHAIN_CONFIG = {
  base: {
    chainId: 8453,
    rpc: "https://mainnet.base.org",
    protocols: {
      aave: "0x...",         // Aave V3 Pool
      morpho: "0x...",       // Morpho contract
    },
    usdc: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  },
  ethereum: {
    chainId: 1,
    rpc: "https://eth.llamarpc.com",
    protocols: {
      aave: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
      compound: "0x...",     // Compound cUSDC
      morpho: "0x...",
    },
    usdc: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  },
};
```

---

## Projected Earnings Display

```typescript
interface EarningsProjectionProps {
  amount: string;
  apy: string;
  asset: string;
}

export function EarningsProjection({ amount, apy, asset }: EarningsProjectionProps) {
  const principal = parseFloat(amount);
  const annualRate = parseFloat(apy) / 100;

  const earnings30d = (principal * annualRate * 30) / 365;
  const earnings90d = (principal * annualRate * 90) / 365;
  const earnings365d = principal * annualRate;

  return (
    <div className="p-4 bg-gradient-to-br from-green-900/20 to-blue-900/20 border border-green-600 rounded-lg">
      <h4 className="font-semibold text-green-400 mb-3">💰 Projected Earnings</h4>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">30 days:</span>
          <span className="font-bold text-white">
            +{earnings30d.toFixed(2)} {asset}
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-gray-400">90 days:</span>
          <span className="font-bold text-white">
            +{earnings90d.toFixed(2)} {asset}
          </span>
        </div>

        <div className="flex items-center justify-between border-t border-gray-700 pt-2">
          <span className="text-gray-400">1 year:</span>
          <span className="text-xl font-bold text-green-400">
            +{earnings365d.toFixed(2)} {asset}
          </span>
        </div>
      </div>

      <div className="mt-3 text-xs text-gray-400">
        Based on current APY of {apy}%. Rates are variable and may change.
      </div>
    </div>
  );
}
```

---

## Allocation Strategy Display

```typescript
interface AllocationDisplayProps {
  allocation: AllocationStrategy[];
  totalAmount: string;
  asset: string;
}

export function AllocationStrategyDisplay({
  allocation,
  totalAmount,
  asset
}: AllocationDisplayProps) {
  return (
    <div className="p-4 bg-gray-900 rounded-lg border border-gray-700">
      <h4 className="font-semibold mb-3">📊 Optimal Allocation Strategy</h4>

      <div className="space-y-3">
        {allocation.map((alloc, index) => (
          <div key={alloc.protocol} className="p-3 bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  index === 0 ? 'bg-green-400' :
                  index === 1 ? 'bg-blue-400' :
                  'bg-purple-400'
                }`} />
                <span className="font-semibold text-white">
                  {alloc.protocol.toUpperCase()}
                </span>
              </div>
              <span className="text-sm text-green-400 font-semibold">
                {alloc.apy}% APY
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-400">
                {alloc.percentage}% allocation
              </span>
              <span className="font-bold text-white">
                {alloc.amount} {asset}
              </span>
            </div>

            {/* Progress bar */}
            <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  index === 0 ? 'bg-green-400' :
                  index === 1 ? 'bg-blue-400' :
                  'bg-purple-400'
                }`}
                style={{ width: `${alloc.percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 p-3 bg-green-900/20 border border-green-600 rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Weighted APY:</span>
          <span className="text-xl font-bold text-green-400">
            {calculateWeightedAPY(allocation)}%
          </span>
        </div>
      </div>
    </div>
  );
}

function calculateWeightedAPY(allocation: AllocationStrategy[]): string {
  const weightedSum = allocation.reduce((sum, alloc) => {
    return sum + (parseFloat(alloc.apy) * alloc.percentage / 100);
  }, 0);
  return weightedSum.toFixed(2);
}
```

---

## Backend API: /execute Endpoint

### Request

```typescript
interface MoneyMarketExecuteRequest {
  transaction_hash: string;
  metadata: {
    action: string;              // "money_market_deposit", "money_market_withdraw"
    protocol: string;            // "aave", "compound", "morpho"
    asset: string;               // "USDC", "ETH"
    amount: string;              // Transaction amount
    apy: string;                 // Current APY
    chain: string;               // "base", "ethereum"

    // For yield optimization
    step_completed?: number;
    total_steps?: number;
  };
}
```

### Response

```typescript
interface MoneyMarketExecuteResponse {
  message: string;
  metadata: {
    action: string;
    protocol: string;
    transaction_hash: string;
    transaction_id: number;       // Database ID
    saved_to_db: boolean;         // Persistence confirmation

    // Financial data
    apy: string;
    projected_earnings_30d?: string;
    projected_earnings_365d?: string;

    // Multi-step tracking
    step_completed?: number;
    total_steps?: number;
    status: "in_progress" | "complete";
  };
}
```

### Example: Deposit Transaction

```bash
POST /api/v1/conversations/{conversation_id}/execute

Request:
{
  "transaction_hash": "0xabc...",
  "metadata": {
    "action": "money_market_deposit",
    "protocol": "aave",
    "asset": "USDC",
    "amount": "5000",
    "apy": "5.25",
    "chain": "base"
  }
}

Response:
{
  "message": "Deposit confirmed on aave money market.",
  "metadata": {
    "action": "money_market_deposit",
    "protocol": "aave",
    "transaction_hash": "0xabc...",
    "transaction_id": 44,
    "saved_to_db": true,
    "apy": "5.25",
    "projected_earnings_30d": "21.87",
    "projected_earnings_365d": "262.50",
    "status": "complete"
  }
}
```

---

## Error Handling

```typescript
enum MoneyMarketError {
  INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE",
  LIQUIDITY_LOW = "LIQUIDITY_LOW",
  ALLOWANCE_FAILED = "ALLOWANCE_FAILED",
  TRANSACTION_FAILED = "TRANSACTION_FAILED",
  MINIMUM_NOT_MET = "MINIMUM_NOT_MET",
}

function handleMoneyMarketError(
  error: unknown,
  execute: MoneyMarketExecutePayload
): MoneyMarketError {
  const message = error instanceof Error ? error.message : String(error);

  if (message.includes("insufficient balance")) {
    return MoneyMarketError.INSUFFICIENT_BALANCE;
  }

  if (message.includes("liquidity")) {
    return MoneyMarketError.LIQUIDITY_LOW;
  }

  if (message.includes("allowance") || message.includes("approve")) {
    return MoneyMarketError.ALLOWANCE_FAILED;
  }

  if (message.includes("minimum")) {
    return MoneyMarketError.MINIMUM_NOT_MET;
  }

  return MoneyMarketError.TRANSACTION_FAILED;
}

function getErrorMessage(error: MoneyMarketError): string {
  switch (error) {
    case MoneyMarketError.INSUFFICIENT_BALANCE:
      return "Insufficient balance. Please check your wallet.";
    case MoneyMarketError.LIQUIDITY_LOW:
      return "Protocol liquidity is low. Try a smaller amount or different protocol.";
    case MoneyMarketError.ALLOWANCE_FAILED:
      return "Token approval failed. Please try again.";
    case MoneyMarketError.MINIMUM_NOT_MET:
      return "Deposit amount below protocol minimum. Please increase amount.";
    default:
      return "Transaction failed. Please try again.";
  }
}
```

---

## Complete Example

```typescript
// components/MoneyMarketExecuteButton.tsx

import { useState } from "react";
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { EarningsProjection } from "./EarningsProjection";
import { RateComparisonDisplay } from "./RateComparisonDisplay";
import { AllocationStrategyDisplay } from "./AllocationStrategyDisplay";

interface MoneyMarketExecuteButtonProps {
  execute: MoneyMarketExecutePayload;
  conversationId: string;
  onSuccess: (txHash: string) => void;
  onError: (error: string) => void;
}

export function MoneyMarketExecuteButton({
  execute,
  conversationId,
  onSuccess,
  onError
}: MoneyMarketExecuteButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { authenticated } = usePrivy();
  const { wallets } = useWallets();

  const handleExecute = async () => {
    if (!authenticated || wallets.length === 0) {
      onError("Please connect your wallet");
      return;
    }

    setIsLoading(true);

    try {
      const wallet = wallets[0];
      let txHash: string;

      switch (execute.action) {
        case "money_market_deposit":
          txHash = await executeMoneyMarketDeposit(execute, wallet);
          break;

        case "money_market_withdraw":
          txHash = await executeMoneyMarketWithdraw(execute, wallet);
          break;

        case "yield_optimization":
          await executeYieldOptimization(execute, wallet, conversationId, onStepUpdate);
          return; // Multi-step returns in the loop

        case "rate_comparison":
          // Read-only, no transaction
          return;

        default:
          throw new Error(`Unknown action: ${execute.action}`);
      }

      // Report to backend
      await reportToExecute(conversationId, {
        transaction_hash: txHash,
        metadata: {
          action: execute.action,
          protocol: execute.protocol,
          asset: execute.asset,
          amount: execute.amount,
          apy: execute.current_apy,
          chain: execute.chain,
        },
      });

      onSuccess(txHash);
    } catch (error) {
      const errorType = handleMoneyMarketError(error, execute);
      onError(getErrorMessage(errorType));
    } finally {
      setIsLoading(false);
    }
  };

  // Rate comparison - no execution button
  if (execute.action === "rate_comparison" && execute.rates) {
    return <RateComparisonDisplay rates={execute.rates} asset={execute.asset} />;
  }

  // Yield optimization - show allocation strategy
  if (execute.action === "yield_optimization" && execute.allocation) {
    return (
      <div>
        <AllocationStrategyDisplay
          allocation={execute.allocation}
          totalAmount={execute.amount}
          asset={execute.asset}
        />
        <button
          onClick={handleExecute}
          disabled={isLoading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold mt-4"
        >
          {isLoading ? "Executing..." : "Execute Optimal Allocation"}
        </button>
      </div>
    );
  }

  // Standard deposit/withdraw
  return (
    <div>
      {/* Projected Earnings */}
      {execute.current_apy && execute.action === "money_market_deposit" && (
        <EarningsProjection
          amount={execute.amount}
          apy={execute.current_apy}
          asset={execute.asset}
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

      {/* Execute Button */}
      <button
        onClick={handleExecute}
        disabled={isLoading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold"
      >
        {isLoading ? "Executing..." :
         `Execute ${execute.action.replace("money_market_", "")} (${execute.protocol})`}
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

## Summary

| Action | Steps | Approval Required | Complexity | Database Type |
|--------|-------|-------------------|------------|---------------|
| Deposit | 2 (approve + deposit) | Yes | Simple | FUND |
| Withdraw | 1 | No | Simple | SEND |
| Rate Comparison | 0 (read-only) | No | None | N/A |
| Yield Optimization | 4-6 (multi-protocol) | Yes (per protocol) | Medium | FUND |

**Key Rules:**
1. Money market operations are simpler than lending (no collateral management)
2. No liquidation risk - user can always withdraw (subject to protocol liquidity)
3. APYs are variable and change based on market conditions
4. Multi-protocol optimization requires sequential deposits
5. All transactions persist to database automatically
6. Rate comparison is read-only (no transaction, no database record)
7. Use protocol-specific ABIs for contract calls
8. Show projected earnings to help users understand yield
