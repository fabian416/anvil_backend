# Lending Execution Frontend Specification

## Overview

This document specifies how the frontend should execute lending and borrowing transactions based on the `execute` payload from the backend. The system supports Morpho and Aave protocols with comprehensive risk management.

## Supported Protocols

| Protocol | Type | Execution Method | Asset Addresses |
|----------|------|------------------|-----------------|
| `morpho` | P2P Lending Optimizer | Privy + EVM Transaction | Valid ERC-20 addresses |
| `aave` | Traditional Lending Pool | Privy + EVM Transaction | Valid ERC-20 addresses |

---

## Execute Payload Structure

```typescript
interface LendingExecutePayload {
  action_type: "lending";
  action: "supply" | "withdraw" | "borrow" | "repay" | "liquidate" | "leverage_loop";
  protocol: "morpho" | "aave";
  chain: string;                    // e.g., "base", "ethereum", "arbitrum"

  // Asset info
  asset: string;                    // e.g., "USDC", "ETH"
  amount: string;                   // Amount (human readable)
  asset_address: string;            // ERC-20 token address
  protocol_address: string;         // Protocol contract address

  // Financial data
  value_usd: string;                // USD value of transaction
  current_apy: string | null;       // Current supply/borrow APY
  borrow_apy: string | null;        // Borrow APY (for borrow actions)

  // Risk metrics
  health_factor: string | null;            // Current health factor
  health_factor_after: string | null;      // Expected health factor after tx
  collateral_required: string | null;      // Minimum collateral required
  liquidation_threshold: string | null;    // Liquidation price/threshold

  // Gas & fees
  gas_estimate: string;             // Estimated gas units
  network_fee_usd: string | null;   // Estimated network fee in USD

  // Multi-step (for leverage loops)
  execution_mode?: "single" | "multi_step";
  loop_id?: string;                 // Unique ID for leverage loop
  steps?: LendingStep[];
  current_step?: number;
  total_steps?: number;
}

interface LendingStep {
  step: number;
  action: "loop_supply" | "loop_borrow" | "loop_swap";
  status: "pending" | "in_progress" | "completed" | "error";
  description: string;
  amount: string;
  asset: string;
  estimated_time: string;

  // Swap step fields (for loop_swap)
  from_token?: string;
  to_token?: string;
  expected_output?: string;
}
```

---

## Action Type Mapping

The backend maps lending actions to transaction types for database persistence:

```typescript
const ACTION_TO_TX_TYPE: Record<string, TransactionType> = {
  "supply": "FUND",           // Deposit into protocol
  "withdraw": "SEND",          // Withdraw from protocol
  "borrow": "FUND",            // Borrow funds
  "repay": "SEND",             // Repay debt
  "liquidate": "SEND",         // Liquidate position
  "leverage_loop": "SWAP",     // Multi-step leveraged position
  "loop_supply": "FUND",       // Supply step in loop
  "loop_borrow": "FUND",       // Borrow step in loop
  "loop_swap": "SWAP",         // Swap step in loop
};
```

---

## Execution Flow

### 1. Supply (Deposit) - Single Step

**User deposits assets to earn yield**

```typescript
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { encodeFunctionData, erc20Abi, parseUnits } from "viem";

async function executeSupply(
  execute: LendingExecutePayload,
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

  // 2. Supply to protocol
  const supplyTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: getProtocolAbi(execute.protocol, "supply"),
        functionName: "supply",
        args: [execute.asset_address, amountWei, wallet.address, 0],
      }),
    }],
  });

  return supplyTx;
}
```

### 2. Withdraw - Single Step

**User withdraws supplied assets**

```typescript
async function executeWithdraw(
  execute: LendingExecutePayload,
  wallet: any
): Promise<string> {

  const provider = await wallet.getEthereumProvider();
  await wallet.switchChain(getChainId(execute.chain));

  const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

  // No approval needed for withdraw - user is withdrawing their own supplied assets
  const withdrawTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: getProtocolAbi(execute.protocol, "withdraw"),
        functionName: "withdraw",
        args: [execute.asset_address, amountWei, wallet.address],
      }),
    }],
  });

  return withdrawTx;
}
```

### 3. Borrow - Single Step

**User borrows against collateral**

⚠️ **Important**: Always check `health_factor_after` before executing!

```typescript
async function executeBorrow(
  execute: LendingExecutePayload,
  wallet: any
): Promise<string> {

  // Safety check: health factor
  if (execute.health_factor_after && parseFloat(execute.health_factor_after) < 1.2) {
    throw new Error(
      `⚠️ DANGER: Health factor after borrow would be ${execute.health_factor_after}. ` +
      `This is too risky! Recommended minimum: 1.5`
    );
  }

  const provider = await wallet.getEthereumProvider();
  await wallet.switchChain(getChainId(execute.chain));

  const amountWei = parseUnits(execute.amount, getDecimals(execute.asset));

  // Borrow from protocol
  const borrowTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: getProtocolAbi(execute.protocol, "borrow"),
        functionName: "borrow",
        args: [
          execute.asset_address,
          amountWei,
          2, // Variable rate (1 = stable, 2 = variable)
          0, // Referral code
          wallet.address
        ],
      }),
    }],
  });

  return borrowTx;
}
```

### 4. Repay - Single Step

**User repays borrowed amount**

```typescript
async function executeRepay(
  execute: LendingExecutePayload,
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

  // 2. Repay debt
  const repayTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: execute.protocol_address,
      data: encodeFunctionData({
        abi: getProtocolAbi(execute.protocol, "repay"),
        functionName: "repay",
        args: [
          execute.asset_address,
          amountWei,
          2, // Variable rate
          wallet.address
        ],
      }),
    }],
  });

  return repayTx;
}
```

### 5. Leverage Loop - Multi-Step

**User creates leveraged position (3x-10x)**

```typescript
async function executeLeverageLoop(
  execute: LendingExecutePayload,
  wallet: any,
  conversationId: string,
  onStepUpdate: (stepId: number, status: string) => void
): Promise<void> {

  if (execute.execution_mode !== "multi_step" || !execute.steps) {
    throw new Error("Invalid leverage loop configuration");
  }

  for (const step of execute.steps) {
    onStepUpdate(step.step, "in_progress");

    let txHash: string;

    try {
      switch (step.action) {
        case "loop_supply":
          // Supply collateral
          txHash = await executeSupply({
            ...execute,
            action: "supply",
            amount: step.amount,
          }, wallet);
          break;

        case "loop_borrow":
          // Borrow against collateral
          txHash = await executeBorrow({
            ...execute,
            action: "borrow",
            amount: step.amount,
          }, wallet);
          break;

        case "loop_swap":
          // Swap borrowed asset
          txHash = await executeSwap({
            ...execute,
            action_type: "swap",
            from_token: step.from_token!,
            to_token: step.to_token!,
            amount: step.amount,
          }, wallet);
          break;

        default:
          throw new Error(`Unknown action: ${step.action}`);
      }

      // Report step completion to backend
      await reportStepComplete(conversationId, {
        transaction_hash: txHash,
        metadata: {
          loop_id: execute.loop_id,
          step_completed: step.step,
          action: step.action,
        },
      });

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

### Morpho ABI (Simplified)

```typescript
const MORPHO_ABI = [
  {
    name: "supply",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "onBehalf", type: "address" },
      { name: "maxIterations", type: "uint256" }
    ],
    outputs: [{ name: "supplied", type: "uint256" }],
  },
  {
    name: "withdraw",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "receiver", type: "address" }
    ],
    outputs: [{ name: "withdrawn", type: "uint256" }],
  },
  {
    name: "borrow",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "onBehalf", type: "address" },
      { name: "receiver", type: "address" },
      { name: "maxIterations", type: "uint256" }
    ],
    outputs: [{ name: "borrowed", type: "uint256" }],
  },
  {
    name: "repay",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "onBehalf", type: "address" }
    ],
    outputs: [{ name: "repaid", type: "uint256" }],
  },
] as const;
```

### Aave V3 ABI (Simplified)

```typescript
const AAVE_V3_ABI = [
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
  {
    name: "borrow",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "interestRateMode", type: "uint256" },
      { name: "referralCode", type: "uint16" },
      { name: "onBehalfOf", type: "address" }
    ],
    outputs: [],
  },
  {
    name: "repay",
    type: "function",
    inputs: [
      { name: "asset", type: "address" },
      { name: "amount", type: "uint256" },
      { name: "interestRateMode", type: "uint256" },
      { name: "onBehalfOf", type: "address" }
    ],
    outputs: [{ name: "", type: "uint256" }],
  },
] as const;
```

---

## Chain Configuration

```typescript
const LENDING_CHAIN_CONFIG = {
  base: {
    chainId: 8453,
    rpc: "https://mainnet.base.org",
    morpho: "0x...", // Morpho contract address
    aave: "0x...",   // Aave V3 Pool address
    usdc: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  },
  ethereum: {
    chainId: 1,
    rpc: "https://eth.llamarpc.com",
    morpho: "0x...",
    aave: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2", // Aave V3 Pool
    usdc: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  },
  arbitrum: {
    chainId: 42161,
    rpc: "https://arb1.arbitrum.io/rpc",
    morpho: "0x...",
    aave: "0x794a61358D6845594F94dc1DB02A252b5b4814aD", // Aave V3 Pool
    usdc: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
  },
};
```

---

## Health Factor Display

### Health Factor Component

```typescript
interface HealthFactorProps {
  currentHealthFactor: string | null;
  healthFactorAfter: string | null;
}

export function HealthFactorDisplay({ currentHealthFactor, healthFactorAfter }: HealthFactorProps) {
  const current = parseFloat(currentHealthFactor || "0");
  const after = parseFloat(healthFactorAfter || "0");

  const getRiskLevel = (hf: number) => {
    if (hf >= 2.0) return { label: "Safe", color: "text-green-400" };
    if (hf >= 1.5) return { label: "Good", color: "text-blue-400" };
    if (hf >= 1.2) return { label: "Moderate", color: "text-yellow-400" };
    if (hf >= 1.0) return { label: "Risky", color: "text-orange-400" };
    return { label: "Liquidation!", color: "text-red-400" };
  };

  const currentRisk = getRiskLevel(current);
  const afterRisk = getRiskLevel(after);

  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h4 className="font-semibold mb-2">Health Factor</h4>

      <div className="flex items-center justify-between mb-2">
        <span className="text-gray-400">Current:</span>
        <span className={`font-bold ${currentRisk.color}`}>
          {current.toFixed(2)} ({currentRisk.label})
        </span>
      </div>

      {healthFactorAfter && (
        <div className="flex items-center justify-between">
          <span className="text-gray-400">After transaction:</span>
          <span className={`font-bold ${afterRisk.color}`}>
            {after.toFixed(2)} ({afterRisk.label})
          </span>
        </div>
      )}

      {after < 1.5 && (
        <div className="mt-3 p-2 bg-yellow-900/30 border border-yellow-600 rounded text-yellow-400 text-sm">
          ⚠️ Warning: Low health factor increases liquidation risk!
        </div>
      )}

      {after < 1.0 && (
        <div className="mt-3 p-2 bg-red-900/30 border border-red-600 rounded text-red-400 text-sm font-semibold">
          🚨 DANGER: This transaction will result in liquidation!
        </div>
      )}
    </div>
  );
}
```

---

## Backend API: /execute Endpoint

### Request

```typescript
interface LendingExecuteRequest {
  transaction_hash: string;
  metadata: {
    action: string;              // "supply", "borrow", etc.
    protocol: string;            // "morpho", "aave"
    asset: string;               // "USDC", "ETH"
    amount: string;              // Transaction amount
    chain: string;               // "base", "ethereum"

    // For leverage loops
    loop_id?: string;
    step_completed?: number;

    // Risk metrics
    health_factor?: string;
    apy?: string;
  };
}
```

### Response

```typescript
interface LendingExecuteResponse {
  message: string;
  metadata: {
    action: string;
    protocol: string;
    transaction_hash: string;
    transaction_id: number;       // Database ID
    saved_to_db: boolean;         // Persistence confirmation

    // Multi-step tracking
    loop_id?: string;
    step_completed?: number;
    total_steps?: number;
    status: "in_progress" | "complete";

    // Risk metrics
    health_factor?: string;
    current_apy?: string;
  };
}
```

### Example: Supply Transaction

```bash
POST /api/v1/conversations/{conversation_id}/execute

Request:
{
  "transaction_hash": "0x123...",
  "metadata": {
    "action": "supply",
    "protocol": "morpho",
    "asset": "USDC",
    "amount": "1000",
    "chain": "base",
    "apy": "5.25"
  }
}

Response:
{
  "message": "Supply transaction confirmed on morpho.",
  "metadata": {
    "action": "supply",
    "protocol": "morpho",
    "transaction_hash": "0x123...",
    "transaction_id": 43,
    "saved_to_db": true,
    "current_apy": "5.25",
    "status": "complete"
  }
}
```

---

## Error Handling

```typescript
enum LendingError {
  INSUFFICIENT_COLLATERAL = "INSUFFICIENT_COLLATERAL",
  HEALTH_FACTOR_TOO_LOW = "HEALTH_FACTOR_TOO_LOW",
  ALLOWANCE_FAILED = "ALLOWANCE_FAILED",
  TRANSACTION_FAILED = "TRANSACTION_FAILED",
  LIQUIDATION_RISK = "LIQUIDATION_RISK",
}

function handleLendingError(error: unknown, execute: LendingExecutePayload): LendingError {
  const message = error instanceof Error ? error.message : String(error);

  if (message.includes("insufficient collateral")) {
    return LendingError.INSUFFICIENT_COLLATERAL;
  }

  if (message.includes("health factor") || message.includes("liquidation")) {
    return LendingError.HEALTH_FACTOR_TOO_LOW;
  }

  if (message.includes("allowance") || message.includes("approve")) {
    return LendingError.ALLOWANCE_FAILED;
  }

  return LendingError.TRANSACTION_FAILED;
}

function getErrorMessage(error: LendingError): string {
  switch (error) {
    case LendingError.INSUFFICIENT_COLLATERAL:
      return "Insufficient collateral for this borrow. Please supply more assets first.";
    case LendingError.HEALTH_FACTOR_TOO_LOW:
      return "Health factor too low. This transaction would put you at risk of liquidation.";
    case LendingError.ALLOWANCE_FAILED:
      return "Token approval failed. Please try again.";
    case LendingError.LIQUIDATION_RISK:
      return "🚨 DANGER: This action will result in liquidation! Transaction blocked for your safety.";
    default:
      return "Transaction failed. Please try again.";
  }
}
```

---

## Complete Example

```typescript
// components/LendingExecuteButton.tsx

import { useState } from "react";
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { HealthFactorDisplay } from "./HealthFactorDisplay";

interface LendingExecuteButtonProps {
  execute: LendingExecutePayload;
  conversationId: string;
  onSuccess: (txHash: string) => void;
  onError: (error: string) => void;
}

export function LendingExecuteButton({
  execute,
  conversationId,
  onSuccess,
  onError
}: LendingExecuteButtonProps) {
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
        case "supply":
          txHash = await executeSupply(execute, wallet);
          break;
        case "withdraw":
          txHash = await executeWithdraw(execute, wallet);
          break;
        case "borrow":
          txHash = await executeBorrow(execute, wallet);
          break;
        case "repay":
          txHash = await executeRepay(execute, wallet);
          break;
        case "leverage_loop":
          await executeLeverageLoop(execute, wallet, conversationId, onStepUpdate);
          return; // Multi-step returns in the loop
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
          chain: execute.chain,
        },
      });

      onSuccess(txHash);
    } catch (error) {
      const errorType = handleLendingError(error, execute);
      onError(getErrorMessage(errorType));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      {/* Health Factor Display */}
      {(execute.health_factor || execute.health_factor_after) && (
        <HealthFactorDisplay
          currentHealthFactor={execute.health_factor}
          healthFactorAfter={execute.health_factor_after}
        />
      )}

      {/* Execute Button */}
      <button
        onClick={handleExecute}
        disabled={isLoading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold mt-4"
      >
        {isLoading ? "Executing..." : `Execute ${execute.action}`}
      </button>
    </div>
  );
}
```

---

## Summary

| Action | Steps | Approval Required | Risk Check | Database Type |
|--------|-------|-------------------|------------|---------------|
| Supply | 2 (approve + supply) | Yes | No | FUND |
| Withdraw | 1 | No | No | SEND |
| Borrow | 1 | No | Yes (health factor) | FUND |
| Repay | 2 (approve + repay) | Yes | No | SEND |
| Leverage Loop | 6-9 (3x loop) | Yes (per step) | Yes | SWAP/FUND |

**Key Rules:**
1. Always check health factor before borrowing
2. Block transactions if health_factor_after < 1.2
3. Show risk warnings for health_factor < 1.5
4. Report each step to `/execute` endpoint
5. All transactions persist to database automatically
6. Use protocol-specific ABIs for contract calls
7. Handle errors gracefully with user-friendly messages
