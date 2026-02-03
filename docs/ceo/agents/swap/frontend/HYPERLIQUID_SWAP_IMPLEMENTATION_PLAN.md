# Hyperliquid Swap Implementation Plan

## Executive Summary

The backend now supports **multi-step execution** for Hyperliquid swaps. The `execute_data` payload includes a `steps[]` array with smart detection of which steps are needed based on the user's Hyperliquid balances.

## Current State ✅ UPDATED

### Backend (swap_workflow_agent.py) - ✅ FULLY IMPLEMENTED

The backend **already sends** `execution_mode: "multi_step"` for all Hyperliquid swaps:

- ✅ Gets spot quotes from Hyperliquid API
- ✅ Returns quote data (price, amount, spread)
- ✅ Token addresses are `null` (Hyperliquid is not EVM)
- ✅ `get_spot_balance()` and `get_perps_balance()` in `hyperliquid_client.py`
- ✅ **Sends `execution_mode: "multi_step"`** in execute_data
- ✅ **Sends `steps[]` array** with deposit/transfer/swap steps
- ✅ Smart step detection (skips deposit/transfer if user has balance)
- ✅ Bridge contract addresses in `HYPERLIQUID_BRIDGE_CONTRACTS`

**Code location:** `_build_hyperliquid_execute_data()` in `swap_workflow_agent.py` (line ~1354)

### Frontend - REQUIRED CHANGES

When the frontend receives `execute.execution_mode === "multi_step"`:

- ❌ Detect multi-step mode and show step progress UI
- ❌ Execute steps in order: Deposit → Transfer → Swap  
- ❌ Use `@nktkas/hyperliquid` SDK for Hyperliquid operations
- ❌ Report step completion to `/execute` API
- ❌ Handle step errors and retry logic

---

## Complete Hyperliquid Swap Flow (Using LiFi Bridge)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HYPERLIQUID SWAP FLOW (LiFi Integration)                 │
└─────────────────────────────────────────────────────────────────────────────┘

User's Privy Wallet on Base:
  - USDC: User's funds to swap
  - ETH: For gas fees
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Bridge USDC via LiFi (if requires_deposit = true)                  │
│ - Use LiFi SDK/API to get bridge quote                                      │
│ - Execute bridge transaction on Base (gas paid on Base!)                   │
│ - LiFi routes: Base USDC → Hyperliquid USDC (Perps)                        │
│ - Wait for confirmation (~30 seconds via Relay bridge)                     │
│ - Funds arrive in Hyperliquid PERPS account                                 │
│ - Report to backend: POST /execute with step_completed=1                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Transfer to Spot Account (if requires_transfer = true)             │
│ - Call client.exchange('SpotTransfer', {coin: 'USDC', amount: X})          │
│ - Signed by Privy wallet                                                    │
│ - Instant (no gas on Hyperliquid)                                          │
│ - Report to backend: POST /execute with step_completed=2                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Execute Spot Swap (always required)                                 │
│ - Call client.exchange('SpotPlaceOrder', {coin: 'PURR', ...})              │
│ - Market order for instant execution                                        │
│ - Zero gas fees on Hyperliquid                                             │
│ - Report to backend: POST /execute with step_completed=3                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
User now has PURR in Hyperliquid Spot account
```

### Key Improvement: LiFi Bridge

**User's Privy Wallet Setup:**
- ✅ User has USDC in Privy wallet
- ✅ User has ETH in Privy wallet for gas
- ✅ Both are on **Base** chain

**Previous flow (Arbitrum Bridge) - PROBLEM:**
- ❌ Required ETH on Arbitrum for gas
- ❌ User's ETH is on Base, not Arbitrum!
- ❌ Two EVM transactions (approve + deposit)
- ❌ 1-2 minute confirmation time

**New flow (LiFi Bridge) - SOLUTION:**
- ✅ Gas paid on **Base** using ETH in user's Privy wallet
- ✅ Single transaction via LiFi
- ✅ ~30 second confirmation via Relay bridge
- ✅ No need to have ETH on Arbitrum

---

## New Execute Payload Structure

### Multi-Step Execute Payload (from backend)

```json
{
  "action_type": "swap",
  "provider": "hyperliquid",
  "execution_mode": "multi_step",
  "chain": "hyperliquid",
  "from_token": "USDC",
  "to_token": "PURR",
  "amount": "100",
  "quote_amount": "7246.06",
  "min_amount_out": "7173.59",
  "price_impact": "0.05",
  "exchange_rate": "72.4606",
  "slippage": 1.0,
  "gas_estimate": "0",
  "network_fee_usd": "0",
  "value_usd": "100",
  "from_token_address": null,
  "to_token_address": null,
  
  "steps": [
    {
      "step": 1,
      "action": "lifi_bridge",
      "status": "pending",
      "description": "Bridge 100.00 USDC to Hyperliquid via LiFi",
      "source_chain": "base",
      "source_chain_id": 8453,
      "destination_chain": "hyperliquid",
      "destination_chain_id": 1337,
      "amount": "100.00",
      "token": "USDC",
      "source_token_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "destination_token_address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
      "bridge_provider": "lifi",
      "gas_paid_on": "base",
      "estimated_time": "~30 seconds"
    },
    {
      "step": 2,
      "action": "transfer_to_spot",
      "status": "pending",
      "description": "Transfer 100.00 USDC from Perps to Spot",
      "amount": "100.00",
      "token": "USDC",
      "estimated_time": "instant"
    },
    {
      "step": 3,
      "action": "spot_swap",
      "status": "pending",
      "description": "Swap 100 USDC → 7246.06 PURR",
      "from_token": "USDC",
      "to_token": "PURR",
      "amount": "100",
      "expected_output": "7246.06",
      "min_output": "7173.59",
      "estimated_time": "instant"
    }
  ],
  "current_step": 1,
  "total_steps": 3,
  
  "hyperliquid_balances": {
    "perps_usdc": 0,
    "spot_usdc": 0,
    "spot_from_token": 0
  },
  "requires_deposit": true,
  "requires_transfer": true,
  
  "lifi_config": {
    "source_chain": "ethereum",
    "source_chain_id": 1,
    "destination_chain": "hyperliquid",
    "destination_chain_id": 1337,
    "source_usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "destination_usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "lifi_quote_url": "https://li.quest/v1/quote",
    "supported_source_chains": {
      "ethereum": { "chain_id": 1, "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" },
      "base": { "chain_id": 8453, "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" },
      "arbitrum": { "chain_id": 42161, "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" }
    },
    "token_balances": {
      "ethereum": {
        "eth_balance": 0.00070785,
        "can_pay_gas": true,
        "usdc_balance": 2.80,
        "weth_balance": 0.00081710,
        "total_usd": 6.16
      },
      "base": {
        "eth_balance": 0,
        "can_pay_gas": false,
        "usdc_balance": 0,
        "weth_balance": 0,
        "total_usd": 0
      },
      "arbitrum": {
        "eth_balance": 0.00001372,
        "can_pay_gas": false,
        "usdc_balance": 0.20,
        "weth_balance": 0.00099750,
        "total_usd": 2.42
      }
    },
    "best_source_chain": "ethereum",
    "gas_info": {
      "chains_checked": {
        "ethereum": { "eth_balance": 0.00070785, "can_pay_gas": true, "has_enough": true },
        "base": { "eth_balance": 0, "can_pay_gas": false, "has_enough": false },
        "arbitrum": { "eth_balance": 0.00001372, "can_pay_gas": false, "has_enough": false }
      },
      "best_chain": "ethereum",
      "min_eth_required": 0.0002
    },
    "gas_error": null
  },
  
  "bridge_config": {
    "bridge": "0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7",
    "usdc": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
    "chain_id": 42161
  }
}
```

### Smart Step Detection

The backend automatically detects which steps are needed:

| User Balance State | Steps Generated |
|-------------------|-----------------|
| No Hyperliquid balance | 3 steps: Deposit → Transfer → Swap |
| Balance in Perps only | 2 steps: Transfer → Swap |
| Balance in Spot already | 1 step: Swap only |

---

## Frontend Implementation

### 1. Install Dependencies

```bash
npm install @nktkas/hyperliquid viem @privy-io/react-auth
```

### 2. Multi-Step Execution Hook

```typescript
// hooks/useHyperliquidMultiStepSwap.ts

import { useState, useCallback } from 'react';
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { parseUnits, encodeFunctionData, erc20Abi } from 'viem';
import * as hl from '@nktkas/hyperliquid';

interface HyperliquidStep {
  step: number;
  action: 'lifi_bridge' | 'deposit' | 'transfer_to_spot' | 'spot_swap';
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  description: string;
  amount: string;
  token: string;
  estimated_time: string;
  // LiFi bridge step (NEW - preferred)
  source_chain?: string;
  source_chain_id?: number;
  destination_chain?: string;
  destination_chain_id?: number;
  source_token_address?: string;
  destination_token_address?: string;
  bridge_provider?: string;
  gas_paid_on?: string;
  // Legacy deposit step (Arbitrum bridge)
  chain?: string;
  chain_id?: number;
  bridge_contract?: string;
  usdc_contract?: string;
  // Swap step
  from_token?: string;
  to_token?: string;
  expected_output?: string;
}

interface TokenBalance {
  eth_balance: number;
  can_pay_gas: boolean;  // TRUE = has enough native ETH for gas
  usdc_balance: number;
  weth_balance: number;  // WETH cannot pay gas!
  total_usd: number;
}

interface GasInfo {
  chains_checked: Record<string, {
    eth_balance: number;
    can_pay_gas: boolean;
    has_enough: boolean;
  }>;
  best_chain: string | null;
  min_eth_required: number;
}

interface LiFiConfig {
  source_chain: string;           // Pre-selected by backend
  source_chain_id: number;
  destination_chain: string;
  destination_chain_id: number;
  source_usdc: string;
  destination_usdc: string;
  lifi_quote_url: string;
  supported_source_chains: Record<string, { chain_id: number; usdc: string }>;
  // NEW: Full token balances per chain from backend DB
  token_balances: Record<string, TokenBalance>;
  // NEW: Backend pre-selected best chain (has can_pay_gas=true)
  best_source_chain: string | null;
  // NEW: Detailed gas check info
  gas_info: GasInfo;
  // NEW: Error if no chain has gas
  gas_error: string | null;
}

interface HyperliquidExecutePayload {
  execution_mode: 'multi_step';
  steps: HyperliquidStep[];
  current_step: number;
  requires_deposit: boolean;
  requires_transfer: boolean;
  // NEW: LiFi bridge configuration with token_balances
  lifi_config: LiFiConfig;
  // LEGACY: Arbitrum bridge configuration (fallback)
  bridge_config: {
    bridge: string;
    usdc: string;
    chain_id: number;
  };
}

export function useHyperliquidMultiStepSwap(conversationId: string) {
  const { wallets } = useWallets();
  const [steps, setSteps] = useState<HyperliquidStep[]>([]);
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize Hyperliquid client
  const initHyperliquidClient = async (wallet: any) => {
    const provider = await wallet.getEthereumProvider();
    const account = {
      address: wallet.address as `0x${string}`,
      signMessage: async ({ message }: { message: string }) => {
        return await provider.request({
          method: 'personal_sign',
          params: [message, wallet.address],
        });
      },
      signTypedData: async (typedData: any) => {
        return await provider.request({
          method: 'eth_signTypedData_v4',
          params: [wallet.address, JSON.stringify(typedData)],
        });
      },
    };

    const transport = new hl.HttpTransport({ isTestnet: false });
    return new hl.ExchangeClient({ transport, wallet: account });
  };

  // Report step completion to backend
  const reportStepComplete = async (
    transactionHash: string,
    stepNumber: number,
    action: string
  ) => {
    const response = await fetch(
      `/api/v1/conversations/${conversationId}/execute`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`,
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
    return await response.json();
  };

  // Execute all steps
  const executeSwap = useCallback(async (execute: HyperliquidExecutePayload) => {
    if (wallets.length === 0) {
      throw new Error('Wallet not connected');
    }

    const wallet = wallets[0];
    setSteps(execute.steps);
    setCurrentStep(execute.current_step);
    setIsLoading(true);
    setError(null);

    try {
      for (const step of execute.steps) {
        // Update step status to in_progress
        setSteps(prev => prev.map(s =>
          s.step === step.step ? { ...s, status: 'in_progress' } : s
        ));
        setCurrentStep(step.step);

        let txHash: string;

        switch (step.action) {
          case 'lifi_bridge':
            // NEW: Use LiFi for bridging (gas paid on source chain)
            txHash = await executeLiFiBridgeStep(wallet, step, execute.lifi_config);
            // Wait for bridge to be confirmed on Hyperliquid
            await waitForHyperliquidDeposit(wallet.address, parseFloat(step.amount));
            break;
            
          case 'deposit':
            // LEGACY: Direct Arbitrum bridge (requires ETH on Arbitrum)
            txHash = await executeDepositStep(wallet, step, execute.bridge_config);
            // Wait for deposit to be confirmed on Hyperliquid
            await waitForHyperliquidDeposit(wallet.address, parseFloat(step.amount));
            break;

          case 'transfer_to_spot':
            const hlClient = await initHyperliquidClient(wallet);
            await hlClient.exchange('SpotTransfer', {
              destination: 'spot',
              coin: step.token,
              amount: step.amount,
            });
            txHash = `hl_transfer_${Date.now()}`;
            break;

          case 'spot_swap':
            const client = await initHyperliquidClient(wallet);
            const isBuy = step.from_token === 'USDC';
            const result = await client.exchange('SpotOrder', {
              orders: [{
                coin: isBuy ? step.to_token : step.from_token,
                isBuy: isBuy,
                limitPx: '0',
                sz: step.amount,
                reduceOnly: false,
                orderType: { market: {} },
              }],
            });
            txHash = result?.orderId || `hl_swap_${Date.now()}`;
            break;

          default:
            throw new Error(`Unknown action: ${step.action}`);
        }

        // Report to backend
        await reportStepComplete(txHash, step.step, step.action);

        // Update step status to completed
        setSteps(prev => prev.map(s =>
          s.step === step.step ? { ...s, status: 'completed' } : s
        ));
      }

      return { success: true };

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      setError(errorMessage);

      // Mark current step as error
      setSteps(prev => prev.map(s =>
        s.step === currentStep ? { ...s, status: 'error' } : s
      ));

      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [wallets, conversationId]);

  return {
    executeSwap,
    steps,
    currentStep,
    isLoading,
    error,
  };
}

// Helper: Execute LiFi bridge step (replaces old Arbitrum deposit)
async function executeLiFiBridgeStep(
  wallet: any,
  step: HyperliquidStep,
  lifiConfig: {
    source_chain: string;
    source_chain_id: number;
    source_usdc: string;
    destination_usdc: string;
  }
): Promise<string> {
  const provider = await wallet.getEthereumProvider();

  // Switch to source chain (Base)
  await wallet.switchChain(lifiConfig.source_chain_id);

  const amountWei = parseUnits(step.amount, 6); // USDC = 6 decimals

  // 1. Get LiFi quote with transaction data
  const quoteResponse = await fetch(
    `https://li.quest/v1/quote?` +
    `fromChain=${lifiConfig.source_chain_id}` +
    `&toChain=1337` + // Hyperliquid chain ID
    `&fromToken=${lifiConfig.source_usdc}` +
    `&toToken=${lifiConfig.destination_usdc}` +
    `&fromAmount=${amountWei.toString()}` +
    `&fromAddress=${wallet.address.toLowerCase()}`
  );
  const quote = await quoteResponse.json();

  if (!quote.transactionRequest) {
    throw new Error('LiFi quote failed: ' + (quote.message || 'Unknown error'));
  }

  // 2. Execute the LiFi transaction (includes approval if needed)
  const tx = quote.transactionRequest;
  const bridgeTx = await provider.request({
    method: 'eth_sendTransaction',
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

// Legacy helper for backward compatibility (Arbitrum direct bridge)
async function executeDepositStep(
  wallet: any,
  step: HyperliquidStep,
  bridgeConfig: { bridge: string; usdc: string; chain_id: number }
): Promise<string> {
  const provider = await wallet.getEthereumProvider();

  // Switch to Arbitrum
  await wallet.switchChain(bridgeConfig.chain_id);

  const amountWei = parseUnits(step.amount, 6); // USDC = 6 decimals

  // 1. Approve USDC to bridge
  const approveTx = await provider.request({
    method: 'eth_sendTransaction',
    params: [{
      from: wallet.address,
      to: bridgeConfig.usdc,
      data: encodeFunctionData({
        abi: erc20Abi,
        functionName: 'approve',
        args: [bridgeConfig.bridge as `0x${string}`, amountWei],
      }),
    }],
  });
  await waitForTransaction(provider, approveTx);

  // 2. Deposit to Hyperliquid bridge
  const BRIDGE_ABI = [{
    name: 'sendUSDC',
    type: 'function',
    inputs: [
      { name: 'amount', type: 'uint64' },
      { name: 'destination', type: 'address' },
    ],
    outputs: [],
  }] as const;

  const depositTx = await provider.request({
    method: 'eth_sendTransaction',
    params: [{
      from: wallet.address,
      to: bridgeConfig.bridge,
      data: encodeFunctionData({
        abi: BRIDGE_ABI,
        functionName: 'sendUSDC',
        args: [amountWei, wallet.address as `0x${string}`],
      }),
    }],
  });

  return depositTx;
}

// Helper: Wait for transaction confirmation
async function waitForTransaction(provider: any, txHash: string): Promise<void> {
  let receipt = null;
  while (!receipt) {
    await new Promise(r => setTimeout(r, 2000));
    receipt = await provider.request({
      method: 'eth_getTransactionReceipt',
      params: [txHash],
    });
  }
}

// Helper: Wait for deposit to appear on Hyperliquid
async function waitForHyperliquidDeposit(
  address: string,
  expectedAmount: number,
  maxWaitMs: number = 180000 // 3 minutes
): Promise<void> {
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWaitMs) {
    try {
      const response = await fetch('https://api.hyperliquid.xyz/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'clearinghouseState',
          user: address,
        }),
      });
      const data = await response.json();
      const withdrawable = parseFloat(data?.withdrawable || '0');
      
      if (withdrawable >= expectedAmount * 0.99) { // 1% tolerance
        return;
      }
    } catch (e) {
      // Continue polling
    }
    
    await new Promise(r => setTimeout(r, 5000)); // Poll every 5s
  }
  
  throw new Error('Deposit timeout - funds not reflected on Hyperliquid');
}
```

### 3. Step Progress UI Component

```typescript
// components/HyperliquidSwapProgress.tsx

interface StepProgressProps {
  steps: HyperliquidStep[];
  currentStep: number;
}

export function HyperliquidSwapProgress({ steps, currentStep }: StepProgressProps) {
  return (
    <div className="swap-progress p-4 bg-gray-900 rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Swap Progress</h3>
      
      {steps.map((step, index) => (
        <div
          key={step.step}
          className={`flex items-center gap-3 p-3 rounded-lg mb-2 ${
            step.status === 'completed' ? 'bg-green-900/30' :
            step.status === 'in_progress' ? 'bg-blue-900/30' :
            step.status === 'error' ? 'bg-red-900/30' :
            'bg-gray-800/50'
          }`}
        >
          {/* Step indicator */}
          <div className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-700">
            {step.status === 'completed' && '✅'}
            {step.status === 'in_progress' && (
              <div className="animate-spin">⏳</div>
            )}
            {step.status === 'pending' && <span className="text-gray-400">{step.step}</span>}
            {step.status === 'error' && '❌'}
          </div>
          
          {/* Step content */}
          <div className="flex-1">
            <div className="font-medium">
              {getActionLabel(step.action)}
            </div>
            <div className="text-sm text-gray-400">
              {step.description}
            </div>
            <div className="text-xs text-gray-500">
              ~{step.estimated_time}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function getActionLabel(action: string): string {
  switch (action) {
    case 'deposit': return '🌉 Bridge to Hyperliquid';
    case 'transfer_to_spot': return '📤 Transfer to Spot';
    case 'spot_swap': return '🔄 Execute Swap';
    default: return action;
  }
}
```

### 4. Main Swap Execution Component

```typescript
// components/SwapExecuteButton.tsx

import { useHyperliquidMultiStepSwap } from '../hooks/useHyperliquidMultiStepSwap';
import { HyperliquidSwapProgress } from './HyperliquidSwapProgress';

interface Props {
  execute: any; // ExecutePayload from backend
  conversationId: string;
  onSuccess: () => void;
  onError: (error: string) => void;
}

export function SwapExecuteButton({ execute, conversationId, onSuccess, onError }: Props) {
  const isMultiStep = execute.execution_mode === 'multi_step';
  const { executeSwap, steps, currentStep, isLoading, error } = useHyperliquidMultiStepSwap(conversationId);

  const handleExecute = async () => {
    try {
      if (isMultiStep) {
        await executeSwap(execute);
      } else {
        // Standard EVM swap
        await executeEVMSwap(execute);
      }
      onSuccess();
    } catch (err) {
      onError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div>
      {/* Show progress for multi-step swaps */}
      {isMultiStep && steps.length > 0 && (
        <HyperliquidSwapProgress steps={steps} currentStep={currentStep} />
      )}

      {/* Error display */}
      {error && (
        <div className="p-3 bg-red-900/30 text-red-400 rounded-lg mb-4">
          {error}
        </div>
      )}

      {/* Execute button */}
      <button
        onClick={handleExecute}
        disabled={isLoading}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 rounded-lg font-semibold"
      >
        {isLoading ? 'Executing...' : `Execute Swap (${execute.total_steps || 1} step${execute.total_steps > 1 ? 's' : ''})`}
      </button>
    </div>
  );
}
```

---

## Backend API: /execute Endpoint

Report each step completion to the backend:

```
POST /api/v1/conversations/{conversation_id}/execute

Request:
{
  "transaction_hash": "0x...",
  "metadata": {
    "step_completed": 1,
    "action": "deposit",
    "wallet_address": "0x..."
  }
}

Response:
{
  "message": "Step 1 completed. Ready for next step.",
  "execute_data": { ... next step data ... },
  "metadata": {
    "status": "in_progress",
    "step_completed": 1,
    "next_step": 2,
    "total_steps": 3
  }
}
```

---

## Important Notes

### 1. Bridge Method (LiFi vs Legacy)
- **LiFi (Preferred)**: Bridge from any chain (Base, Ethereum, Arbitrum) to Hyperliquid
  - Gas paid on source chain (no ETH on Arbitrum needed!)
  - Uses Relay bridge (~30 seconds)
  - Single transaction
- **Legacy (Arbitrum Bridge)**: Direct bridge from Arbitrum only
  - Requires ETH on Arbitrum for gas
  - Two transactions (approve + deposit)
  - 1-2 minute confirmation

### 2. Timing
- LiFi bridge: ~30 seconds
- Transfer to Spot: Instant
- Swap execution: Instant

### 3. Fees
- LiFi bridge: ~$0.35 on source chain (Base) + ~$0.03 LiFi fee
- Hyperliquid operations: Zero gas (Hyperliquid covers)
- Trading fee: 0.02% (maker) / 0.05% (taker)

### 4. Security
- Never expose private keys to frontend
- Use Privy's secure signing
- All transactions require user approval

---

## Gas Check Before Bridge (Backend Does This Now!)

### Backend Pre-Selection (Recommended)

The backend now queries the `token_balances` table and pre-selects the best chain based on `can_pay_gas=true`. The frontend receives this in `lifi_config`:

```json
{
  "lifi_config": {
    "best_source_chain": "ethereum",      // Backend selected this!
    "source_chain": "ethereum",           // Pre-configured for use
    "source_chain_id": 1,
    "token_balances": {
      "ethereum": { "eth_balance": 0.00070785, "can_pay_gas": true, ... },
      "base": { "eth_balance": 0, "can_pay_gas": false, ... },
      "arbitrum": { "eth_balance": 0.00001372, "can_pay_gas": false, ... }
    },
    "gas_error": null   // Will be set if NO chain has gas
  }
}
```

### Frontend Logic (Simplified)

```typescript
// Use backend's pre-selected chain - no RPC calls needed!
function getSourceChainConfig(lifiConfig: LiFiConfig): {
  chain: string;
  chainId: number;
  usdcAddress: string;
  hasGas: boolean;
} | null {
  // Backend already selected the best chain
  if (lifiConfig.best_source_chain && !lifiConfig.gas_error) {
    const chain = lifiConfig.best_source_chain;
    const chainConfig = lifiConfig.supported_source_chains[chain];
    return {
      chain,
      chainId: chainConfig.chain_id,
      usdcAddress: chainConfig.usdc,
      hasGas: true,
    };
  }
  
  // No chain has gas - show error
  return null;
}

// Check if user has gas on ANY chain (for display)
function hasGasOnAnyChain(lifiConfig: LiFiConfig): boolean {
  return Object.values(lifiConfig.token_balances).some(b => b.can_pay_gas);
}

// Get chains with gas for display
function getChainsWithGas(lifiConfig: LiFiConfig): string[] {
  return Object.entries(lifiConfig.token_balances)
    .filter(([_, balance]) => balance.can_pay_gas)
    .map(([chain, _]) => chain);
}
```

### Fallback: On-Chain Check (If Needed)

If backend data is stale, frontend can verify on-chain:

```typescript
async function verifyGasOnChain(
  wallet: any, 
  chainId: number
): Promise<{ hasGas: boolean; ethBalance: bigint }> {
  const provider = await wallet.getEthereumProvider();
  await wallet.switchChain(chainId);
  
  const ethBalance = await provider.request({
    method: 'eth_getBalance',
    params: [wallet.address, 'latest'],
  });
  
  const MIN_ETH = BigInt("200000000000000"); // 0.0002 ETH (~$0.40)
  
  return {
    hasGas: BigInt(ethBalance) >= MIN_ETH,
    ethBalance: BigInt(ethBalance),
  };
}
```

### Updated Execute Flow (Using Backend's Pre-Selected Chain)

```typescript
export function SwapExecuteButton({ execute, conversationId, onSuccess, onError }: Props) {
  const { wallets } = useWallets();
  const wallet = wallets[0];
  
  // Backend already selected the best chain - no RPC calls needed!
  const lifiConfig = execute.lifi_config;
  const hasGasError = lifiConfig?.gas_error !== null;
  const bestChain = lifiConfig?.best_source_chain;
  
  // Show error if backend couldn't find a chain with gas
  if (hasGasError || !bestChain) {
    const tokenBalances = lifiConfig?.token_balances || {};
    
    return (
      <div className="p-4 bg-yellow-900/30 border border-yellow-600 rounded-lg">
        <h4 className="font-semibold text-yellow-400 mb-2">
          ⚠️ Insufficient Gas for Bridge
        </h4>
        <p className="text-sm text-gray-300 mb-3">
          You need native ETH on one of these chains to pay for gas fees.
        </p>
        
        {/* Show balances per chain */}
        <div className="text-xs text-gray-400 space-y-1">
          {Object.entries(tokenBalances).map(([chain, balance]) => (
            <div key={chain} className="flex justify-between">
              <span>{chain}:</span>
              <span className={balance.can_pay_gas ? 'text-green-400' : 'text-red-400'}>
                {balance.eth_balance.toFixed(6)} ETH 
                {balance.can_pay_gas ? ' ✅' : ' ❌'}
              </span>
            </div>
          ))}
        </div>
        
        <p className="text-xs text-gray-500 mt-2">
          Required: ~0.0002 ETH (~$0.40) for gas fees
        </p>
        <p className="text-xs text-gray-500">
          Note: WETH cannot be used for gas. Only native ETH works.
        </p>
      </div>
    );
  }
  
  // Show which chain will be used
  const chainConfig = lifiConfig.supported_source_chains[bestChain];
  const tokenBalance = lifiConfig.token_balances[bestChain];
  
  // Execute with the backend's pre-selected chain
  const handleExecute = async () => {
    if (execute.requires_deposit) {
      // Use backend's pre-selected source chain
      const bridgeConfig = {
        source_chain: bestChain,
        source_chain_id: chainConfig.chain_id,
        source_usdc: chainConfig.usdc,
        destination_usdc: lifiConfig.destination_usdc,
      };
      
      console.log(`Bridging from ${bestChain} (ETH: ${tokenBalance.eth_balance})`);
      
      // Switch to the correct chain
      await wallet.switchChain(chainConfig.chain_id);
      
      // Execute LiFi bridge
      await executeLiFiBridgeStep(wallet, execute.steps[0], bridgeConfig);
    }
    // ... continue with other steps
  };
  
  return (
    <div>
      {/* Show selected chain info */}
      <div className="text-xs text-gray-400 mb-2">
        Bridging from <span className="text-blue-400">{bestChain}</span> 
        (ETH: {tokenBalance.eth_balance.toFixed(6)})
      </div>
      
      <button
        onClick={handleExecute}
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
      >
        Execute Swap ({execute.total_steps} steps)
      </button>
    </div>
  );
}
```

### Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `gas_error: "No chain has sufficient native ETH"` | Backend couldn't find a chain with gas | User needs ETH on Ethereum, Base, or Arbitrum |
| `can_pay_gas: false` on all chains | WETH doesn't count! | Need native ETH, not wrapped |
| "LiFi quote failed" | Bridge route unavailable | Try again or use fallback |
| "Insufficient balance" | Not enough USDC | User needs more USDC |

### Token Types for Gas

| Token | Can Pay Gas? | Notes |
|-------|-------------|-------|
| **ETH** (native) | ✅ Yes | Used for all EVM transaction fees |
| **WETH** (wrapped) | ❌ No | Must unwrap to ETH first |
| **USDC** | ❌ No | Only for swaps, not gas |

### Gas Cost Comparison

| Method | Gas Chain | Estimated Cost |
|--------|-----------|----------------|
| **LiFi (Ethereum → Hyperliquid)** | Ethereum | ~$0.50-1.00 |
| **LiFi (Base → Hyperliquid)** | Base | ~$0.35-0.40 |
| **LiFi (Arbitrum → Hyperliquid)** | Arbitrum | ~$0.15-0.20 |
| Legacy (Arbitrum Bridge) | Arbitrum | ~$0.15-0.20 |

**Key Benefit**: Backend automatically selects the chain where user has ETH!

---

## Testing Checklist

- [ ] Verify `execution_mode: "multi_step"` is detected correctly
- [ ] Deposit USDC from Arbitrum to Hyperliquid
- [ ] Wait for deposit confirmation (poll Hyperliquid API)
- [ ] Transfer USDC from Perps to Spot account
- [ ] Execute USDC → PURR swap
- [ ] Execute PURR → USDC swap (reverse)
- [ ] Handle insufficient balance errors
- [ ] Handle deposit timeout/failure
- [ ] Show proper step progress UI
- [ ] Report each step to `/execute` endpoint
- [ ] Test with user who already has Hyperliquid balance (fewer steps)

---

## References

- [Privy + Hyperliquid Guide](https://docs.privy.io/recipes/hyperliquid-guide)
- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [@nktkas/hyperliquid SDK](https://github.com/nktkas/hyperliquid)
- [Hyperliquid Bridge Contract](https://arbiscan.io/address/0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7)
- [SWAP_EXECUTION_SPEC.md](./SWAP_EXECUTION_SPEC.md) - Complete frontend spec
