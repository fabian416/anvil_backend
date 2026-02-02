# Hyperliquid Swap Implementation Plan

## Executive Summary

The current implementation only provides **quotes** for Hyperliquid swaps but does NOT execute them. The frontend receives fake token addresses (`0x000...`) which cause `balanceOf` errors. This document outlines the complete implementation flow for Hyperliquid spot swaps using Privy.

## Current State

### Backend (swap_workflow_agent.py)
- ✅ Gets spot quotes from Hyperliquid API
- ✅ Returns quote data (price, amount, spread)
- ❌ Token addresses are `null` (fixed - was fake addresses)
- ❌ No execution capability - just quotes

### Frontend
- ❌ Tries to call `balanceOf()` on all swaps (fails for Hyperliquid)
- ❌ No Hyperliquid SDK integration
- ❌ No deposit/transfer flow for Hyperliquid

---

## Complete Hyperliquid Swap Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYPERLIQUID SWAP FLOW                               │
└─────────────────────────────────────────────────────────────────────────────┘

User has USDC on Base/Arbitrum (in Privy wallet)
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Deposit USDC to Hyperliquid                                         │
│ - Approve USDC to Hyperliquid Bridge contract                               │
│ - Call bridge.deposit(amount) via Privy sendTransaction                     │
│ - Wait for confirmation (~1-2 minutes)                                      │
│ - Funds arrive in Hyperliquid PERPS account                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Transfer to Spot Account                                            │
│ - Call client.exchange('SpotTransfer', {coin: 'USDC', amount: X})          │
│ - Signed by Privy wallet                                                    │
│ - Instant (no gas on Hyperliquid)                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Execute Spot Swap                                                   │
│ - Call client.exchange('SpotPlaceOrder', {coin: 'PURR', ...})              │
│ - Market order for instant execution                                        │
│ - Zero gas fees on Hyperliquid                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
User now has PURR in Hyperliquid Spot account
```

---

## Implementation Tasks

### Phase 1: Backend Changes (Optional - for backend execution)

If we want the backend to execute swaps (recommended for security):

```python
# src/app/infrastructure/adapters/external/hyperliquid_client.py

async def execute_spot_swap(
    self,
    from_token: str,
    to_token: str,
    amount: float,
    wallet_signer: Any,  # Privy wallet signer
) -> dict:
    """Execute a spot swap on Hyperliquid."""
    
    # 1. Check if funds are in Spot account
    balances = await self.get_spot_balances(wallet_signer.address)
    
    # 2. If funds in Perps, transfer to Spot first
    if balances.get(from_token, 0) < amount:
        await self.transfer_to_spot(from_token, amount, wallet_signer)
    
    # 3. Execute market order
    order_result = await self._place_spot_order(
        coin=to_token,
        is_buy=True,
        size=amount,  # USDC amount when buying
        order_type="market",
        wallet_signer=wallet_signer,
    )
    
    return order_result
```

### Phase 2: Frontend Changes (Required)

#### 2.1 Install Dependencies

```bash
npm install @nktkas/hyperliquid viem @privy-io/react-auth
```

#### 2.2 Hyperliquid Service

```typescript
// services/hyperliquid.ts

import * as hl from '@nktkas/hyperliquid';
import { createWalletClient, custom, parseUnits, encodeFunctionData } from 'viem';
import { base, arbitrum } from 'viem/chains';

// Contract addresses
const HYPERLIQUID_BRIDGE = {
  arbitrum: '0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7', // Arbitrum bridge
  base: '0x...', // Base bridge (if available)
};

const USDC_ADDRESS = {
  base: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
  arbitrum: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831',
};

export class HyperliquidService {
  private client: hl.ExchangeClient;
  private transport: hl.HttpTransport;
  
  constructor(isTestnet: boolean = false) {
    this.transport = new hl.HttpTransport({ isTestnet });
  }
  
  /**
   * Initialize with Privy wallet
   */
  async init(privyWallet: any) {
    const provider = await privyWallet.getEthereumProvider();
    const account = {
      address: privyWallet.address as `0x${string}`,
      signMessage: async ({ message }: { message: string }) => {
        return await provider.request({
          method: 'personal_sign',
          params: [message, privyWallet.address],
        });
      },
      signTypedData: async (typedData: any) => {
        return await provider.request({
          method: 'eth_signTypedData_v4',
          params: [privyWallet.address, JSON.stringify(typedData)],
        });
      },
    };
    
    this.client = new hl.ExchangeClient({
      transport: this.transport,
      wallet: account,
    });
  }
  
  /**
   * Step 1: Deposit USDC from EVM chain to Hyperliquid
   */
  async depositToHyperliquid(
    privyWallet: any,
    amount: string,
    chain: 'base' | 'arbitrum' = 'arbitrum'
  ): Promise<string> {
    const provider = await privyWallet.getEthereumProvider();
    const chainConfig = chain === 'base' ? base : arbitrum;
    
    // Switch to correct chain
    await privyWallet.switchChain(chainConfig.id);
    
    const amountWei = parseUnits(amount, 6); // USDC has 6 decimals
    const bridgeAddress = HYPERLIQUID_BRIDGE[chain];
    const usdcAddress = USDC_ADDRESS[chain];
    
    // 1. Approve USDC
    const approveTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: privyWallet.address,
        to: usdcAddress,
        data: encodeFunctionData({
          abi: [{
            name: 'approve',
            type: 'function',
            inputs: [
              { name: 'spender', type: 'address' },
              { name: 'amount', type: 'uint256' },
            ],
            outputs: [{ type: 'bool' }],
          }],
          functionName: 'approve',
          args: [bridgeAddress, amountWei],
        }),
      }],
    });
    
    // Wait for approval
    await this.waitForTransaction(provider, approveTx);
    
    // 2. Deposit to bridge
    const depositTx = await provider.request({
      method: 'eth_sendTransaction',
      params: [{
        from: privyWallet.address,
        to: bridgeAddress,
        data: encodeFunctionData({
          abi: [{
            name: 'sendUSDC',
            type: 'function',
            inputs: [
              { name: 'amount', type: 'uint64' },
              { name: 'destination', type: 'address' },
            ],
            outputs: [],
          }],
          functionName: 'sendUSDC',
          args: [amountWei, privyWallet.address],
        }),
      }],
    });
    
    return depositTx;
  }
  
  /**
   * Step 2: Transfer from Perps to Spot account
   */
  async transferToSpot(coin: string, amount: number): Promise<any> {
    const result = await this.client.exchange('SpotTransfer', {
      destination: 'spot', // or use negative amount
      coin: coin,
      amount: amount.toString(),
    });
    return result;
  }
  
  /**
   * Step 3: Execute spot swap
   */
  async executeSpotSwap(
    fromToken: string,
    toToken: string,
    amount: number,
    isBuy: boolean = true
  ): Promise<any> {
    // Get spot asset info
    const spotMeta = await this.getSpotMeta();
    const tokenInfo = spotMeta.find(m => m.name.includes(toToken));
    
    if (!tokenInfo) {
      throw new Error(`Token ${toToken} not found on Hyperliquid Spot`);
    }
    
    // Place market order
    const result = await this.client.exchange('SpotOrder', {
      orders: [{
        asset: tokenInfo.index,
        isBuy: isBuy,
        limitPx: '0', // 0 for market order
        sz: amount.toString(),
        reduceOnly: false,
        orderType: { market: {} },
      }],
    });
    
    return result;
  }
  
  /**
   * Get spot balances
   */
  async getSpotBalances(): Promise<Record<string, number>> {
    const state = await this.client.info('spotClearinghouseState');
    const balances: Record<string, number> = {};
    
    for (const balance of state.balances || []) {
      balances[balance.coin] = parseFloat(balance.total);
    }
    
    return balances;
  }
  
  /**
   * Get spot market metadata
   */
  async getSpotMeta(): Promise<any[]> {
    const meta = await this.client.info('spotMeta');
    return meta.universe || [];
  }
  
  private async waitForTransaction(provider: any, txHash: string): Promise<void> {
    // Poll for transaction receipt
    let receipt = null;
    while (!receipt) {
      await new Promise(r => setTimeout(r, 2000));
      receipt = await provider.request({
        method: 'eth_getTransactionReceipt',
        params: [txHash],
      });
    }
  }
}
```

#### 2.3 React Hook for Hyperliquid Swaps

```typescript
// hooks/useHyperliquidSwap.ts

import { useState, useCallback } from 'react';
import { usePrivy, useWallets } from '@privy-io/react-auth';
import { HyperliquidService } from '../services/hyperliquid';

interface SwapStep {
  id: string;
  name: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  txHash?: string;
  error?: string;
}

export function useHyperliquidSwap() {
  const { authenticated } = usePrivy();
  const { wallets } = useWallets();
  const [steps, setSteps] = useState<SwapStep[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  const executeSwap = useCallback(async (
    fromToken: string,
    toToken: string,
    amount: string,
    sourceChain: 'base' | 'arbitrum' = 'arbitrum'
  ) => {
    if (!authenticated || wallets.length === 0) {
      throw new Error('Wallet not connected');
    }
    
    const wallet = wallets[0];
    const service = new HyperliquidService();
    await service.init(wallet);
    
    setIsLoading(true);
    setSteps([
      { id: 'deposit', name: 'Deposit to Hyperliquid', status: 'pending' },
      { id: 'transfer', name: 'Transfer to Spot', status: 'pending' },
      { id: 'swap', name: 'Execute Swap', status: 'pending' },
    ]);
    
    try {
      // Step 1: Deposit
      setSteps(prev => prev.map(s => 
        s.id === 'deposit' ? { ...s, status: 'loading' } : s
      ));
      
      const depositTx = await service.depositToHyperliquid(
        wallet,
        amount,
        sourceChain
      );
      
      setSteps(prev => prev.map(s => 
        s.id === 'deposit' ? { ...s, status: 'success', txHash: depositTx } : s
      ));
      
      // Wait for deposit to be reflected on Hyperliquid (can take 1-2 min)
      await new Promise(r => setTimeout(r, 60000)); // TODO: Poll instead
      
      // Step 2: Transfer to Spot
      setSteps(prev => prev.map(s => 
        s.id === 'transfer' ? { ...s, status: 'loading' } : s
      ));
      
      await service.transferToSpot(fromToken, parseFloat(amount));
      
      setSteps(prev => prev.map(s => 
        s.id === 'transfer' ? { ...s, status: 'success' } : s
      ));
      
      // Step 3: Execute swap
      setSteps(prev => prev.map(s => 
        s.id === 'swap' ? { ...s, status: 'loading' } : s
      ));
      
      const swapResult = await service.executeSpotSwap(
        fromToken,
        toToken,
        parseFloat(amount),
        true // isBuy
      );
      
      setSteps(prev => prev.map(s => 
        s.id === 'swap' ? { ...s, status: 'success' } : s
      ));
      
      return swapResult;
      
    } catch (error) {
      const failedStep = steps.find(s => s.status === 'loading');
      if (failedStep) {
        setSteps(prev => prev.map(s => 
          s.id === failedStep.id 
            ? { ...s, status: 'error', error: String(error) } 
            : s
        ));
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [authenticated, wallets]);
  
  return {
    executeSwap,
    steps,
    isLoading,
  };
}
```

---

## Execute Data Changes

### Current Execute Payload (from backend)

```json
{
  "action_type": "swap",
  "provider": "hyperliquid",
  "chain": "base",
  "from_token": "USDC",
  "to_token": "PURR",
  "amount": "0.5",
  "quote_amount": "7.246062",
  "from_token_address": null,
  "to_token_address": null,
  "gas_estimate": "0"
}
```

### Frontend Detection

```typescript
const isHyperliquidSwap = (execute: ExecutePayload): boolean => {
  return execute.provider === 'hyperliquid' ||
         execute.from_token_address === null ||
         execute.to_token_address === null;
};

// In swap execution
if (isHyperliquidSwap(execute)) {
  // Use HyperliquidService (3-step flow)
  const { executeSwap } = useHyperliquidSwap();
  await executeSwap(
    execute.from_token,
    execute.to_token,
    execute.amount,
    'arbitrum' // or 'base'
  );
} else {
  // Standard EVM swap via 1inch/LiFi
  await executeEVMSwap(execute);
}
```

---

## Important Notes

### 1. Deposit Source Chain
- **Arbitrum**: Primary supported chain for Hyperliquid deposits
- **Base**: May require bridging to Arbitrum first (check Hyperliquid docs)

### 2. Timing
- Deposit confirmation: 1-2 minutes
- Transfer to Spot: Instant
- Swap execution: Instant

### 3. Fees
- Bridge deposit: Gas on source chain (Arbitrum/Base)
- Hyperliquid operations: Zero gas (Hyperliquid covers)
- Trading fee: 0.02% (maker) / 0.05% (taker)

### 4. Security
- Never expose private keys to frontend
- Use Privy's secure signing
- Consider backend execution for sensitive operations

---

## Testing Checklist

- [ ] Deposit USDC from Arbitrum to Hyperliquid
- [ ] Transfer USDC from Perps to Spot account
- [ ] Execute USDC → PURR swap
- [ ] Execute PURR → USDC swap (reverse)
- [ ] Handle insufficient balance errors
- [ ] Handle deposit timeout/failure
- [ ] Show proper step progress UI
- [ ] Test with testnet first (`isTestnet: true`)

---

## References

- [Privy + Hyperliquid Guide](https://docs.privy.io/recipes/hyperliquid-guide)
- [Hyperliquid API Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)
- [@nktkas/hyperliquid SDK](https://github.com/nktkas/hyperliquid)
- [Hyperliquid Bridge Contract](https://arbiscan.io/address/0x2Df1c51E09aECF9cacB7bc98cB1742757f163dF7)
