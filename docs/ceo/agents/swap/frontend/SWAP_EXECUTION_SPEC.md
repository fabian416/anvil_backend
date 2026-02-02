# Swap Execution Frontend Specification

## Overview

This document specifies how the frontend should execute swap transactions based on the `execute` payload from the backend. The system supports multiple swap providers, each requiring different execution logic.

## Supported Providers

| Provider | Type | Execution Method | Token Addresses |
|----------|------|------------------|-----------------|
| `hyperliquid` | Centralized Order Book (Hyperliquid L1) | Hyperliquid SDK | `null` (not EVM) |
| `1inch` | DEX Aggregator (EVM) | Privy + EVM Transaction | Valid ERC-20 addresses |
| `lifi` | Cross-chain Bridge + DEX | Privy + EVM Transaction | Valid ERC-20 addresses |

---

## Execute Payload Structure

```typescript
interface ExecutePayload {
  action_type: "swap";
  provider: "hyperliquid" | "1inch" | "lifi";
  chain: string;                    // e.g., "base", "ethereum", "arbitrum"
  
  // Token info
  from_token: string;               // e.g., "USDC"
  to_token: string;                 // e.g., "PURR"
  amount: string;                   // Amount to swap (human readable)
  
  // Quote data
  quote_amount: string;             // Expected output amount
  min_amount_out: string | null;    // Minimum output (slippage protected)
  exchange_rate: string;            // Rate used for quote
  slippage: number;                 // Slippage tolerance (e.g., 1.0 = 1%)
  
  // Token addresses (NULL for Hyperliquid!)
  from_token_address: string | null;
  to_token_address: string | null;
  
  // Price data
  from_token_price_usd: string | null;
  to_token_price_usd: string | null;
  value_usd: string | null;
  
  // Gas & fees
  gas_estimate: string;             // "0" for Hyperliquid
  network_fee_usd: string | null;
  price_impact: string | null;
  
  // Cross-chain (LiFi only)
  to_chain: string | null;
}
```

---

## Provider Detection

```typescript
const getSwapProvider = (execute: ExecutePayload): SwapProvider => {
  // Primary check: provider field
  if (execute.provider === "hyperliquid") {
    return "hyperliquid";
  }
  
  // Fallback: check if token addresses are null (Hyperliquid indicator)
  if (execute.from_token_address === null || execute.to_token_address === null) {
    return "hyperliquid";
  }
  
  // Cross-chain detection
  if (execute.to_chain && execute.to_chain !== execute.chain) {
    return "lifi";
  }
  
  // Default to provider field
  return execute.provider;
};

const isHyperliquidSwap = (execute: ExecutePayload): boolean => {
  return getSwapProvider(execute) === "hyperliquid";
};

const isEVMSwap = (execute: ExecutePayload): boolean => {
  return ["1inch", "lifi"].includes(getSwapProvider(execute));
};
```

---

## Execution Flow

### 1. Hyperliquid Swaps (Multi-Step)

**Important:** Hyperliquid is NOT an EVM DEX. It uses a centralized order book on Hyperliquid L1.

**Key Changes (NEW):**
- Backend now returns `execution_mode: "multi_step"` with `steps[]` array
- Frontend must execute steps in order: Deposit → Transfer → Swap
- Skip completed steps based on `hyperliquid_balances`

#### Multi-Step Execute Payload

```typescript
interface TokenBalance {
  eth_balance: number;       // Native ETH balance
  can_pay_gas: boolean;      // TRUE = has enough native ETH for gas
  usdc_balance: number;      // USDC balance
  weth_balance: number;      // WETH balance (CANNOT pay gas!)
  total_usd: number;         // Total USD value
}

interface LiFiConfig {
  source_chain: string;           // Pre-selected by backend (has gas)
  source_chain_id: number;
  destination_chain: string;
  destination_chain_id: number;
  source_usdc: string;
  destination_usdc: string;
  lifi_quote_url: string;
  supported_source_chains: Record<string, { chain_id: number; usdc: string }>;
  
  // NEW: Full token balances from backend DB
  token_balances: Record<string, TokenBalance>;
  
  // NEW: Backend pre-selected best chain
  best_source_chain: string | null;
  
  // NEW: Gas check details
  gas_info: {
    chains_checked: Record<string, { eth_balance: number; can_pay_gas: boolean; has_enough: boolean }>;
    best_chain: string | null;
    min_eth_required: number;
  };
  
  // NEW: Error if no chain has gas
  gas_error: string | null;
}

interface HyperliquidExecutePayload extends ExecutePayload {
  execution_mode: "multi_step";
  
  // Step execution
  steps: HyperliquidStep[];
  current_step: number;
  total_steps: number;
  
  // Balance info (to determine which steps needed)
  hyperliquid_balances: {
    perps_usdc: number;   // USDC in Perps account
    spot_usdc: number;    // USDC in Spot account
    spot_from_token: number;  // From token in Spot
  };
  
  // Step requirements
  requires_deposit: boolean;   // Need to bridge via LiFi?
  requires_transfer: boolean;  // Need to transfer Perps → Spot?
  
  // NEW: LiFi bridge config (preferred method)
  lifi_config: LiFiConfig;
  
  // LEGACY: Arbitrum direct bridge config (fallback)
  bridge_config: {
    bridge: string;      // "0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7"
    usdc: string;        // "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    chain_id: number;    // 42161 (Arbitrum)
  };
}

interface HyperliquidStep {
  step: number;
  action: "lifi_bridge" | "deposit" | "transfer_to_spot" | "spot_swap";
  status: "pending" | "in_progress" | "completed" | "error";
  description: string;
  amount: string;
  token: string;
  estimated_time: string;
  
  // LiFi bridge step fields (NEW - preferred)
  source_chain?: string;         // e.g., "ethereum"
  source_chain_id?: number;      // e.g., 1
  destination_chain?: string;    // "hyperliquid"
  destination_chain_id?: number; // 1337
  source_token_address?: string;
  destination_token_address?: string;
  bridge_provider?: string;      // "lifi"
  gas_paid_on?: string;          // Which chain pays gas
  
  // Legacy deposit step fields (Arbitrum direct bridge)
  chain?: string;
  chain_id?: number;
  bridge_contract?: string;
  usdc_contract?: string;
  
  // Swap step fields
  from_token?: string;
  to_token?: string;
  expected_output?: string;
  min_output?: string;
}
```

#### Multi-Step Execution Logic

```typescript
import * as hl from "@nktkas/hyperliquid";
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { parseUnits } from "viem";

async function executeHyperliquidMultiStep(
  execute: HyperliquidExecutePayload,
  wallet: any,
  onStepUpdate: (stepId: number, status: string) => void
): Promise<SwapResult> {
  
  const hlService = new HyperliquidService();
  await hlService.init(wallet);
  
  // Check for gas error before starting
  if (execute.lifi_config.gas_error) {
    throw new Error(execute.lifi_config.gas_error);
  }
  
  for (const step of execute.steps) {
    onStepUpdate(step.step, "in_progress");
    
    try {
      switch (step.action) {
        case "lifi_bridge":
          // Step 1 (NEW): Bridge via LiFi - gas paid on source chain
          await executeLiFiBridgeStep(step, wallet, execute.lifi_config);
          // Wait for deposit to be confirmed on Hyperliquid (~30 sec)
          await waitForHyperliquidDeposit(wallet.address, parseFloat(step.amount));
          break;
          
        case "deposit":
          // LEGACY: Direct Arbitrum bridge (requires ETH on Arbitrum)
          await executeDepositStep(step, wallet, execute.bridge_config);
          await waitForHyperliquidDeposit(wallet.address, parseFloat(step.amount));
          break;
          
        case "transfer_to_spot":
          // Step 2: Transfer from Perps to Spot account
          await hlService.transferToSpot(step.token, parseFloat(step.amount));
          break;
          
        case "spot_swap":
          // Step 3: Execute spot swap
          const isBuy = step.from_token === "USDC";
          return await hlService.executeSpotSwap(
            step.from_token!,
            step.to_token!,
            parseFloat(step.amount),
            isBuy
          );
      }
      
      onStepUpdate(step.step, "completed");
    } catch (error) {
      onStepUpdate(step.step, "error");
      throw error;
    }
  }
  
  throw new Error("No swap step found");
}

// NEW: Execute LiFi bridge step (preferred method)
async function executeLiFiBridgeStep(
  step: HyperliquidStep,
  wallet: any,
  lifiConfig: LiFiConfig
): Promise<string> {
  const provider = await wallet.getEthereumProvider();
  
  // Use backend's pre-selected source chain (has gas)
  const sourceChain = lifiConfig.best_source_chain || step.source_chain;
  const sourceChainId = lifiConfig.supported_source_chains[sourceChain!].chain_id;
  const sourceUsdc = lifiConfig.supported_source_chains[sourceChain!].usdc;
  
  // Switch to source chain
  await wallet.switchChain(sourceChainId);
  
  const amountWei = parseUnits(step.amount, 6); // USDC = 6 decimals
  
  // 1. Get LiFi quote with transaction data
  const quoteResponse = await fetch(
    `${lifiConfig.lifi_quote_url}?` +
    `fromChain=${sourceChainId}` +
    `&toChain=${lifiConfig.destination_chain_id}` +
    `&fromToken=${sourceUsdc}` +
    `&toToken=${lifiConfig.destination_usdc}` +
    `&fromAmount=${amountWei.toString()}` +
    `&fromAddress=${wallet.address.toLowerCase()}`
  );
  const quote = await quoteResponse.json();
  
  if (!quote.transactionRequest) {
    throw new Error("LiFi quote failed: " + (quote.message || "Unknown error"));
  }
  
  // 2. Execute the LiFi transaction
  const tx = quote.transactionRequest;
  const bridgeTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: tx.to,
      data: tx.data,
      value: tx.value,
      gasLimit: tx.gasLimit,
    }],
  });
  
  return bridgeTx;
}

// LEGACY: Direct Arbitrum bridge (fallback)
async function executeDepositStep(
  step: HyperliquidStep,
  wallet: any,
  bridgeConfig: { bridge: string; usdc: string; chain_id: number }
): Promise<string> {
  const provider = await wallet.getEthereumProvider();
  
  // Switch to Arbitrum
  await wallet.switchChain(bridgeConfig.chain_id);
  
  const amountWei = parseUnits(step.amount, 6); // USDC = 6 decimals
  
  // 1. Approve USDC to bridge
  const approveTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: bridgeConfig.usdc,
      data: encodeFunctionData({
        abi: erc20Abi,
        functionName: "approve",
        args: [bridgeConfig.bridge, amountWei],
      }),
    }],
  });
  await waitForTransaction(provider, approveTx);
  
  // 2. Deposit to Hyperliquid bridge
  const depositTx = await provider.request({
    method: "eth_sendTransaction",
    params: [{
      from: wallet.address,
      to: bridgeConfig.bridge,
      data: encodeFunctionData({
        abi: HYPERLIQUID_BRIDGE_ABI,
        functionName: "sendUSDC",
        args: [amountWei, wallet.address],
      }),
    }],
  });
  
  return depositTx;
}
```

#### Simple Swap (If Already on Hyperliquid)

If `requires_deposit` and `requires_transfer` are both `false`, there's only one step:

```typescript
async function executeHyperliquidSwap(
  execute: ExecutePayload,
  hlClient: HyperliquidClient
): Promise<SwapResult> {
  
  // Check if multi-step
  if (execute.execution_mode === "multi_step") {
    return await executeHyperliquidMultiStep(execute, wallet, onStepUpdate);
  }
  
  // Simple swap - user already has funds on Hyperliquid Spot
  const isBuying = execute.from_token === "USDC";
  
  if (isBuying) {
    return await hlClient.spotMarketOrder({
      coin: execute.to_token,
      isBuy: true,
      sz: parseFloat(execute.quote_amount),
    });
  } else {
    return await hlClient.spotMarketOrder({
      coin: execute.from_token,
      isBuy: false,
      sz: parseFloat(execute.amount),
    });
  }
}
```

### 2. EVM Swaps (1inch / LiFi) with Privy

**Standard EVM flow:** Approval → Swap Transaction

```typescript
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { encodeFunctionData, erc20Abi } from "viem";

async function executeEVMSwap(
  execute: ExecutePayload,
  walletClient: WalletClient,
  publicClient: PublicClient
): Promise<SwapResult> {
  
  const userAddress = walletClient.account.address;
  
  // 1. Check balance (only for EVM swaps with valid addresses)
  if (execute.from_token_address) {
    const balance = await publicClient.readContract({
      address: execute.from_token_address as `0x${string}`,
      abi: erc20Abi,
      functionName: "balanceOf",
      args: [userAddress],
    });
    
    const requiredAmount = parseUnits(execute.amount, getDecimals(execute.from_token));
    if (balance < requiredAmount) {
      throw new Error(`Insufficient ${execute.from_token} balance`);
    }
  }
  
  // 2. Check and set approval (if needed)
  const spenderAddress = getSpenderAddress(execute.provider, execute.chain);
  await ensureApproval(
    execute.from_token_address,
    spenderAddress,
    execute.amount,
    walletClient,
    publicClient
  );
  
  // 3. Execute swap transaction
  if (execute.provider === "1inch") {
    return await execute1inchSwap(execute, walletClient);
  } else if (execute.provider === "lifi") {
    return await executeLiFiSwap(execute, walletClient);
  }
  
  throw new Error(`Unknown provider: ${execute.provider}`);
}
```

### 3. Privy Integration

```typescript
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { createWalletClient, custom } from "viem";
import { base } from "viem/chains";

function useSwapExecution() {
  const { authenticated } = usePrivy();
  const { wallets } = useWallets();
  
  const executeSwap = async (execute: ExecutePayload) => {
    if (!authenticated || wallets.length === 0) {
      throw new Error("Wallet not connected");
    }
    
    const wallet = wallets[0];
    await wallet.switchChain(getChainId(execute.chain));
    
    const provider = await wallet.getEthereumProvider();
    const walletClient = createWalletClient({
      chain: getChain(execute.chain),
      transport: custom(provider),
      account: wallet.address as `0x${string}`,
    });
    
    // Route to correct execution method
    if (isHyperliquidSwap(execute)) {
      // Hyperliquid uses its own SDK, not EVM
      return await executeHyperliquidSwap(execute, hyperliquidClient);
    } else {
      return await executeEVMSwap(execute, walletClient, publicClient);
    }
  };
  
  return { executeSwap };
}
```

---

## Critical: Handling Null Token Addresses

The most important change is handling `null` token addresses for Hyperliquid:

```typescript
// ❌ WRONG - Will crash on Hyperliquid swaps
const balance = await contract.balanceOf(execute.from_token_address);

// ✅ CORRECT - Check provider first
if (isHyperliquidSwap(execute)) {
  // Skip balance check - Hyperliquid manages balances internally
  // Proceed to Hyperliquid SDK execution
} else if (execute.from_token_address) {
  // EVM swap - check balance
  const balance = await contract.balanceOf(execute.from_token_address);
}
```

---

## Chain Configuration

```typescript
const CHAIN_CONFIG = {
  base: {
    chainId: 8453,
    rpc: "https://mainnet.base.org",
    usdc: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  },
  ethereum: {
    chainId: 1,
    rpc: "https://eth.llamarpc.com",
    usdc: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  },
  arbitrum: {
    chainId: 42161,
    rpc: "https://arb1.arbitrum.io/rpc",
    usdc: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
  },
};

// Spender addresses for approvals
const SPENDER_ADDRESSES = {
  "1inch": {
    base: "0x1111111254EEB25477B68fb85Ed929f73A960582",
    ethereum: "0x1111111254EEB25477B68fb85Ed929f73A960582",
  },
  lifi: {
    base: "0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE",
    ethereum: "0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE",
  },
};
```

---

## Error Handling

```typescript
enum SwapError {
  WALLET_NOT_CONNECTED = "WALLET_NOT_CONNECTED",
  INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE",
  APPROVAL_FAILED = "APPROVAL_FAILED",
  SWAP_FAILED = "SWAP_FAILED",
  UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER",
  HYPERLIQUID_ERROR = "HYPERLIQUID_ERROR",
}

function handleSwapError(error: unknown, execute: ExecutePayload): SwapError {
  const message = error instanceof Error ? error.message : String(error);
  
  // Hyperliquid-specific errors
  if (isHyperliquidSwap(execute)) {
    if (message.includes("insufficient")) {
      return SwapError.INSUFFICIENT_BALANCE;
    }
    return SwapError.HYPERLIQUID_ERROR;
  }
  
  // EVM errors
  if (message.includes("balanceOf")) {
    // This should NOT happen if provider detection is correct
    console.error("balanceOf called on Hyperliquid swap - check provider detection");
    return SwapError.UNSUPPORTED_PROVIDER;
  }
  
  if (message.includes("insufficient") || message.includes("balance")) {
    return SwapError.INSUFFICIENT_BALANCE;
  }
  
  return SwapError.SWAP_FAILED;
}
```

---

## Complete Example

```typescript
// components/SwapExecuteButton.tsx

import { useState } from "react";
import { usePrivy, useWallets } from "@privy-io/react-auth";

interface SwapExecuteButtonProps {
  execute: ExecutePayload;
  onSuccess: (txHash: string) => void;
  onError: (error: string) => void;
}

export function SwapExecuteButton({ execute, onSuccess, onError }: SwapExecuteButtonProps) {
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
      const provider = getSwapProvider(execute);
      
      if (provider === "hyperliquid") {
        // Hyperliquid: Use SDK directly (no EVM)
        const result = await executeHyperliquidSwap(execute);
        onSuccess(result.orderId);
      } else {
        // EVM: Use Privy wallet
        const wallet = wallets[0];
        const result = await executeEVMSwap(execute, wallet);
        onSuccess(result.hash);
      }
    } catch (error) {
      const errorType = handleSwapError(error, execute);
      onError(getErrorMessage(errorType));
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <button 
      onClick={handleExecute} 
      disabled={isLoading}
      className="swap-execute-button"
    >
      {isLoading ? "Executing..." : "Execute Swap"}
    </button>
  );
}
```

---

---

## Important: How to Get execute_data

### ❌ WRONG: Calling /execute to start a swap

```typescript
// This is WRONG - /execute is for REPORTING completed steps
POST /api/v1/conversations/{id}/execute
{ action_type: "swap", from_token: "USDC", ... }  // ❌ Wrong payload
```

### ✅ CORRECT: Get execute_data from chat response

The `execute_data` comes from the **chat message response**, not from `/execute`:

```typescript
// 1. User sends swap message via chat
POST /api/v1/conversations/{id}/messages
{ content: "swap 1 USDC to PURR", language: "en" }

// 2. Backend returns execute_data in the response
{
  "conversation_id": "...",
  "message_id": "...",
  "agent_message": { "content": "Ready to swap..." },
  "execute": {  // ← THIS is your execute_data
    "action_type": "swap",
    "provider": "hyperliquid",
    "execution_mode": "multi_step",
    "steps": [...],
    ...
  }
}

// 3. Frontend uses execute_data to perform the swap locally
// 4. After each step, report to /execute
```

---

## Backend API: /execute Endpoint (Step Reporting)

**Purpose:** Report completion of each step AFTER executing it locally.

**NOT for:** Starting a swap or getting execute_data.

### Endpoint

```
POST /api/v1/conversations/{conversation_id}/execute
```

### Request

```typescript
interface ExecuteRequest {
  // Transaction hash of the COMPLETED step (required)
  transaction_hash: string;
  
  // Metadata for multi-step workflows
  metadata?: {
    // For Hyperliquid multi-step swaps
    swap_id?: string;           // Swap execution ID
    step_completed?: number;     // Which step was just completed (1, 2, or 3)
    action?: string;            // "deposit" | "transfer_to_spot" | "spot_swap"
    
    // For leverage loops
    loop_id?: string;
    
    // User wallet
    wallet_address?: string;
  };
}
```

### Response

```typescript
interface ExecuteResponse {
  // Status message
  message: string;
  
  // Next step's execute_data (if workflow continues)
  execute_data: ExecutePayload | null;
  
  // Additional metadata
  metadata: {
    status: "in_progress" | "completed" | "error";
    step_completed?: number;
    next_step?: number;
    total_steps?: number;
    transaction_hash?: string;
  };
}
```

### Example: Hyperliquid Multi-Step Flow

```typescript
// Step 1: User completes deposit (bridge tx)
const step1Response = await fetch(`/api/v1/conversations/${conversationId}/execute`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
  },
  body: JSON.stringify({
    transaction_hash: depositTxHash,
    metadata: {
      swap_id: execute.swap_id,
      step_completed: 1,
      action: "deposit",
      wallet_address: userAddress,
    },
  }),
});
const step1Data = await step1Response.json();
// step1Data.execute_data contains step 2 (transfer_to_spot)

// Step 2: User completes transfer (Hyperliquid SDK)
const step2Response = await fetch(`/api/v1/conversations/${conversationId}/execute`, {
  method: "POST",
  body: JSON.stringify({
    transaction_hash: "hl_transfer_" + Date.now(), // Hyperliquid internal ID
    metadata: {
      swap_id: execute.swap_id,
      step_completed: 2,
      action: "transfer_to_spot",
    },
  }),
});
const step2Data = await step2Response.json();
// step2Data.execute_data contains step 3 (spot_swap)

// Step 3: User completes swap (Hyperliquid SDK)
const step3Response = await fetch(`/api/v1/conversations/${conversationId}/execute`, {
  method: "POST",
  body: JSON.stringify({
    transaction_hash: swapOrderId,
    metadata: {
      swap_id: execute.swap_id,
      step_completed: 3,
      action: "spot_swap",
    },
  }),
});
const step3Data = await step3Response.json();
// step3Data.metadata.status === "completed"
```

### Frontend Integration Hook

```typescript
function useMultiStepSwap(conversationId: string) {
  const [currentStep, setCurrentStep] = useState(1);
  const [steps, setSteps] = useState<HyperliquidStep[]>([]);
  
  const reportStepComplete = async (
    transactionHash: string,
    stepNumber: number,
    action: string
  ) => {
    const response = await fetch(
      `/api/v1/conversations/${conversationId}/execute`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${getToken()}`,
        },
        body: JSON.stringify({
          transaction_hash: transactionHash,
          metadata: {
            step_completed: stepNumber,
            action: action,
          },
        }),
      }
    );
    
    const data = await response.json();
    
    // Update step status
    setSteps(prev => prev.map(s => 
      s.step === stepNumber ? { ...s, status: "completed" } : s
    ));
    
    // Move to next step if available
    if (data.execute_data) {
      setCurrentStep(data.metadata.next_step);
    }
    
    return data;
  };
  
  return { currentStep, steps, setSteps, reportStepComplete };
}
```

---

## Step Progress UI Component

```typescript
// components/HyperliquidSwapProgress.tsx

interface StepProgressProps {
  steps: HyperliquidStep[];
  currentStep: number;
}

export function HyperliquidSwapProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <div className="swap-progress">
      {steps.map((step) => (
        <div 
          key={step.step}
          className={`step ${step.status}`}
        >
          <div className="step-indicator">
            {step.status === "completed" && "✅"}
            {step.status === "in_progress" && "⏳"}
            {step.status === "pending" && "⏸️"}
            {step.status === "error" && "❌"}
          </div>
          <div className="step-content">
            <div className="step-title">
              Step {step.step}: {getActionLabel(step.action)}
            </div>
            <div className="step-description">{step.description}</div>
            <div className="step-time">~{step.estimated_time}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function getActionLabel(action: string): string {
  switch (action) {
    case "deposit": return "Bridge to Hyperliquid";
    case "transfer_to_spot": return "Transfer to Spot";
    case "spot_swap": return "Execute Swap";
    default: return action;
  }
}
```

---

## Summary

| Scenario | Token Addresses | Balance Check | Execution |
|----------|-----------------|---------------|-----------|
| Hyperliquid (needs deposit) | `null` | Skip (use `lifi_config.token_balances`) | 3-step: LiFi Bridge → Transfer → Swap |
| Hyperliquid (has balance) | `null` | Skip | 1-step: Swap only |
| 1inch (USDC → ETH) | Valid ERC-20 | `balanceOf()` | Privy + EVM tx |
| LiFi cross-chain | Valid ERC-20 | `balanceOf()` | Privy + EVM tx |

**Key Rules:**
1. Always check `provider` or `execution_mode` before calling any EVM contract methods
2. For `execution_mode: "multi_step"`, iterate through `steps[]` array
3. Never call `balanceOf()` when token addresses are `null`
4. **Use `lifi_config.best_source_chain`** - backend pre-selects chain with gas
5. Check `lifi_config.gas_error` before executing - show error if set
6. LiFi bridge requires ~30 seconds confirmation time
7. Transfer and Swap on Hyperliquid are instant (zero gas)

**Gas Check (NEW):**
- Backend queries `token_balances` table and sets `lifi_config.token_balances`
- Each chain has `can_pay_gas: true/false` based on native ETH balance
- WETH cannot pay gas! Only native ETH works
- `lifi_config.best_source_chain` is the chain with enough gas (pre-selected)
