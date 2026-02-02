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

### 1. Hyperliquid Swaps

**Important:** Hyperliquid is NOT an EVM DEX. It uses a centralized order book on Hyperliquid L1. 
- No ERC-20 approvals needed
- No gas fees (Hyperliquid covers gas)
- No `balanceOf` calls on token addresses
- Uses Hyperliquid SDK directly

```typescript
import { HyperliquidClient } from "@hyperliquid/sdk";

async function executeHyperliquidSwap(
  execute: ExecutePayload,
  hyperliquidClient: HyperliquidClient
): Promise<SwapResult> {
  
  // DO NOT call balanceOf - Hyperliquid manages balances internally
  // DO NOT try to use from_token_address/to_token_address (they are null)
  
  const isBuying = execute.from_token === "USDC";
  
  if (isBuying) {
    // Buying meme token with USDC
    // Use sz (size) for the amount of token to receive
    const result = await hyperliquidClient.spotMarketOrder({
      coin: execute.to_token,  // e.g., "PURR"
      isBuy: true,
      sz: parseFloat(execute.quote_amount),  // Amount of PURR to receive
    });
    return result;
  } else {
    // Selling meme token for USDC
    const result = await hyperliquidClient.spotMarketOrder({
      coin: execute.from_token,  // e.g., "PURR"
      isBuy: false,
      sz: parseFloat(execute.amount),  // Amount of PURR to sell
    });
    return result;
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

## Summary

| Scenario | Token Addresses | Balance Check | Execution |
|----------|-----------------|---------------|-----------|
| Hyperliquid (USDC → PURR) | `null` | Skip | Hyperliquid SDK |
| Hyperliquid (PURR → USDC) | `null` | Skip | Hyperliquid SDK |
| 1inch (USDC → ETH) | Valid ERC-20 | `balanceOf()` | Privy + EVM tx |
| LiFi cross-chain | Valid ERC-20 | `balanceOf()` | Privy + EVM tx |

**Key Rule:** Always check `provider` or token addresses before calling any EVM contract methods.
