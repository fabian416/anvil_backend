# DeFi Core Module Implementation Files

> **Complete TypeScript/React Implementation for DeFi Operations**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **DeFi Core** module provides users with access to core DeFi operations: lending (supply), borrowing, swapping, staking, earning, and bridging. These are the fundamental building blocks of DeFi participation.

### Key Capabilities
1. **Supply (Lending)**: Supply assets to Aave V3 to earn yield
2. **Borrow**: Borrow assets against collateral with health factor monitoring
3. **Swap**: Exchange tokens via Curve Finance with risk analysis
4. **Stake**: Stake assets in protocols for rewards
5. **Earn**: Discover yield farming opportunities
6. **Bridge**: Cross-chain asset transfers via LayerZero/Axelar

### Business Value
- **User Empowerment**: Direct access to DeFi protocols
- **Risk Management**: Built-in health factor monitoring and risk warnings
- **Yield Optimization**: Best rates discovery across protocols
- **Security**: Smart contract interactions with safety checks

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Users need safe, intuitive access to DeFi operations with clear risk visibility.

**Root Cause Analysis**:
- **Complexity Barrier**: DeFi protocols are complex and risky
- **Solution**: Simplified UI with clear risk indicators and health factor monitoring
- **Trust Issues**: Users fear smart contract interactions
- **Solution**: Clear previews, risk warnings, transaction simulation

**Design Decisions**:
1. **Safety-First**: Health factor prominently displayed, risk warnings before actions
2. **Progressive Disclosure**: Show basic info first, details on demand
3. **Real-Time Updates**: Live rates, health factor, position updates
4. **Transaction Preview**: Clear preview before confirmation

### Visual Design

#### Layout Structure (Supply Example)
```
┌─────────────────────────────────────────┐
│ Header: "Supply Assets" + Back Button   │
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐  │
│ │  Asset Selector                    │  │
│ │  [Select Asset ▼]                  │  │
│ └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐  │
│ │  Amount Input                      │  │
│ │  [Amount] [Max]                    │  │
│ │  Balance: 10,000 USDC              │  │
│ └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│ Market Info                            │
│ ┌────┐ ┌────┐ ┌────┐                 │
│ │APY │ │TVL │ │Util│                 │
│ │5.2%│ │$1B │ │45% │                 │
│ └────┘ └────┘ └────┘                 │
├─────────────────────────────────────────┤
│ Health Factor Impact                   │
│ Current: 2.5 → After: 2.8 ✅          │
│ [Visual Health Bar]                    │
├─────────────────────────────────────────┤
│ Transaction Preview                    │
│ Amount: 1,000 USDC                     │
│ Gas Estimate: ~$5                     │
│ Total: 1,005 USDC                     │
│ ┌───────────────────────────────────┐ │
│ │ [Confirm Supply]                    │ │
│ └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### Color Palette
- **Primary**: `#3B82F6` (Blue) - Trust, DeFi
- **Success**: `#10B981` (Green) - Safe operations, healthy positions
- **Warning**: `#F59E0B` (Amber) - Risk warnings, moderate health
- **Error**: `#EF4444` (Red) - Critical risk, liquidatable positions
- **Info**: `#3B82F6` (Blue) - Market info, rates

#### Component Specifications

##### Health Factor Display
```typescript
interface HealthFactorDisplayProps {
  current: string;  // Current health factor
  after: string;    // Health factor after operation
  riskLevel: 'safe' | 'moderate' | 'high' | 'critical' | 'liquidatable';
}
```

**Visual Design**:
- Large number display
- Color-coded by risk level
- Visual progress bar
- Risk level badge
- Warning message if risky

##### Transaction Preview Card
```typescript
interface TransactionPreviewProps {
  operation: 'supply' | 'borrow' | 'swap' | 'stake';
  asset: string;
  amount: number;
  gasEstimate: number;
  totalCost: number;
  onConfirm: () => void;
}
```

**Visual Design**:
- Clear operation type
- Asset and amount
- Gas estimate
- Total cost
- Confirm button (disabled if risky)

### Responsive Breakpoints

**Mobile** (< 640px):
- Full-screen form
- Stacked inputs
- Bottom sheet for preview
- Swipe to confirm

**Tablet** (640px - 1024px):
- Centered form (max-width: 600px)
- Side-by-side market info
- Modal for preview

**Desktop** (> 1024px):
- Two-column layout (form + market info)
- Inline preview
- Sidebar for position details

### Accessibility Requirements

1. **Screen Readers**:
   - Announce health factor changes
   - Describe risk levels
   - Announce transaction details

2. **Keyboard Navigation**:
   - Tab through all inputs
   - Enter to confirm
   - Escape to cancel

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Risk indicators: 4.5:1
   - Health factor: 4.5:1

### Loading States

**Market Data Load**:
- Skeleton for market cards
- Shimmer for rates

**Health Factor Calculation**:
- Loading spinner
- "Calculating impact..."

**Transaction Execution**:
- Progress steps
- "Signing transaction..."
- "Broadcasting..."
- "Confirming..."

### Empty States

**No Markets**:
- Message: "No markets available"
- CTA: "Refresh"

**No Position**:
- Message: "No active positions"
- CTA: "Start Supplying"

### Error States

**Insufficient Balance**:
- Inline error below amount
- Red border
- "Max" button to fix

**Health Factor Too Low**:
- Warning banner
- "Cannot borrow: Health factor would be < 1.0"
- Suggestion: "Supply more collateral first"

**Transaction Failed**:
- Error message
- Transaction hash
- Retry button

---

## 🔌 API Endpoints

### 1. Get Aave Markets (Supply Opportunities)

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/markets`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Query Parameters
| Parameter | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `asset` | `string` | No | Filter by asset symbol | `USDC` |
| `chain` | `string` | No | Blockchain (default: "ethereum") | `ethereum`, `polygon`, `arbitrum`, `optimism`, `avalanche`, `base` |
| `sort_by` | `string` | No | Sort field (default: "supply_apy") | `supply_apy`, `borrow_apy`, `tvl`, `utilization` |
| `limit` | `number` | No | Max results (default: 50, max: 100) | `50` |

#### Response

##### Success Response (200 OK)
```typescript
interface AaveMarketsResponse {
  markets: AaveMarket[];
  count: number;
  chain: string;
  total_supplied_usd: string;
  total_borrowed_usd: string;
}

interface AaveMarket {
  asset_address: string;
  symbol: string;
  name: string;
  chain: string;
  supply_apy: string;  // Decimal (e.g., "0.052" = 5.2%)
  total_supplied: string;
  total_supplied_usd: string;
  borrow_apy_variable: string;
  borrow_apy_stable: string;
  total_borrowed: string;
  total_borrowed_usd: string;
  utilization_rate: string;
  liquidity_available: string;
  ltv: string;  // Loan-to-value (e.g., "0.80" = 80%)
  liquidation_threshold: string;
  liquidation_bonus: string;
  is_active: boolean;
  can_use_as_collateral: boolean;
  can_borrow: boolean;
  price_usd: string;
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| `markets` | `AaveMarket[]` | Array of market data |
| `count` | `number` | Number of markets returned |
| `chain` | `string` | Blockchain name |
| `total_supplied_usd` | `string` | Total TVL supplied |
| `total_borrowed_usd` | `string` | Total borrowed |

**JSON Example**:
```json
{
  "markets": [
    {
      "asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "symbol": "USDC",
      "name": "USD Coin",
      "chain": "ethereum",
      "supply_apy": "0.052",
      "total_supplied": "1000000000",
      "total_supplied_usd": "1000000000",
      "borrow_apy_variable": "0.04",
      "borrow_apy_stable": "0.06",
      "total_borrowed": "450000000",
      "total_borrowed_usd": "450000000",
      "utilization_rate": "0.45",
      "liquidity_available": "550000000",
      "ltv": "0.80",
      "liquidation_threshold": "0.85",
      "liquidation_bonus": "0.05",
      "is_active": true,
      "can_use_as_collateral": true,
      "can_borrow": true,
      "price_usd": "1.00"
    }
  ],
  "count": 1,
  "chain": "ethereum",
  "total_supplied_usd": "5000000000",
  "total_borrowed_usd": "2250000000"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `UnsupportedChainError` | Invalid chain parameter | Reset to default chain, show error toast |
| `404` | `MarketNotFoundError` | Asset not listed | Show error: "Asset not available on this chain" |
| `502` | `AaveAPIError` | Aave API unavailable | Show error: "Aave service temporarily unavailable" + Retry |
| `500` | `AaveError` | Internal error | Show error: "Failed to load markets" + Retry |

### 2. Get User Position

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_address` | `string` | Yes | User wallet address (0x...) |

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `chain` | `string` | No | Blockchain (default: "ethereum") |

#### Response

##### Success Response (200 OK)
```typescript
interface AavePositionResponse {
  user_address: string;
  chain: string;
  total_collateral_usd: string;
  total_debt_usd: string;
  available_borrow_usd: string;
  net_worth_usd: string;
  health_factor: string;  // "∞" if no debt
  current_ltv: string;
  is_healthy: boolean;
  is_at_risk: boolean;  // True if 1 < HF < 1.5
  is_liquidatable: boolean;  // True if HF < 1
  supplies: AaveSupplyPosition[];
  borrows: AaveBorrowPosition[];
}

interface AaveSupplyPosition {
  asset_address: string;
  symbol: string;
  balance: string;
  balance_usd: string;
  apy: string;
  is_collateral: boolean;
}

interface AaveBorrowPosition {
  asset_address: string;
  symbol: string;
  balance: string;
  balance_usd: string;
  apy: string;
  borrow_type: string;  // "variable" or "stable"
}
```

**JSON Example**:
```json
{
  "user_address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain": "ethereum",
  "total_collateral_usd": "3000.00",
  "total_debt_usd": "1200.00",
  "available_borrow_usd": "1275.00",
  "net_worth_usd": "1800.00",
  "health_factor": "2.0625",
  "current_ltv": "0.40",
  "is_healthy": true,
  "is_at_risk": false,
  "is_liquidatable": false,
  "supplies": [
    {
      "asset_address": "0x...",
      "symbol": "ETH",
      "balance": "1.5",
      "balance_usd": "3000.00",
      "apy": "0.03",
      "is_collateral": true
    }
  ],
  "borrows": [
    {
      "asset_address": "0x...",
      "symbol": "USDC",
      "balance": "1200.00",
      "balance_usd": "1200.00",
      "apy": "0.04",
      "borrow_type": "variable"
    }
  ]
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `InvalidAddressError` | Invalid user address | Show error: "Invalid wallet address" |
| `404` | `PositionNotFoundError` | User has no position | Show empty state: "No active positions" |
| `502` | `AaveAPIError` | Aave API unavailable | Show error: "Unable to load position" + Retry |

### 3. Get Health Factor

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}/health`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface HealthFactorResponse {
  value: string;  // "∞" if no debt
  collateral_usd: string;
  debt_usd: string;
  risk_level: string;  // "safe", "moderate", "high", "critical", "liquidatable"
  is_liquidatable: boolean;
  distance_to_liquidation: string;  // Percentage above threshold
  max_withdrawable_pct: string;
  max_borrowable_pct: string;
}
```

### 4. Calculate Health Factor (Simulation)

**Method**: `POST`  
**Endpoint**: `/api/v1/defi/aave/calculate/health-factor`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface CalculateHealthFactorRequest {
  collateral_usd: number;  // Required: > 0
  debt_usd: number;  // Required: >= 0
  liquidation_threshold?: number;  // Optional: Default 0.825 (82.5%)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `collateral_usd` | `number` | **Yes** | Total collateral in USD | > 0 |
| `debt_usd` | `number` | **Yes** | Total debt in USD | >= 0 |
| `liquidation_threshold` | `number` | No | Liquidation threshold | 0 < value <= 1, default 0.825 |

**JSON Example**:
```json
{
  "collateral_usd": 1000.0,
  "debt_usd": 500.0,
  "liquidation_threshold": 0.825
}
```

#### Response

##### Success Response (200 OK)
Returns `HealthFactorResponse` (same as GET /health)

### 5. Get Available to Borrow

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/aave/positions/{user_address}/borrow-capacity/{asset}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `user_address` | `string` | Yes | User wallet address |
| `asset` | `string` | Yes | Asset symbol (e.g., "USDC") |

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `chain` | `string` | No | Blockchain (default: "ethereum") |

#### Response

##### Success Response (200 OK)
```typescript
interface AvailableToBorrowResponse {
  asset: string;
  chain: string;
  max_borrowable: string;
  max_borrowable_usd: string;
  current_debt: string;
  collateral_usd: string;
  health_factor_after_max_borrow: string;
}
```

**JSON Example**:
```json
{
  "asset": "USDC",
  "chain": "ethereum",
  "max_borrowable": "1000.00",
  "max_borrowable_usd": "1000.00",
  "current_debt": "0",
  "collateral_usd": "3000.00",
  "health_factor_after_max_borrow": "2.475"
}
```

### 6. Get Swap Quote (Curve)

**Method**: `POST`  
**Endpoint**: `/api/v1/defi/curve/quote`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SwapQuoteRequest {
  from_token: string;  // Required: Token address or symbol
  to_token: string;  // Required: Token address or symbol
  amount: string;  // Required: Amount in smallest unit (wei)
  chain: string;  // Required: Blockchain name
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `from_token` | `string` | **Yes** | Source token address or symbol | Valid address or symbol |
| `to_token` | `string` | **Yes** | Destination token address or symbol | Valid address or symbol |
| `amount` | `string` | **Yes** | Amount in smallest unit | Valid number string |
| `chain` | `string` | **Yes** | Blockchain name | Valid chain name |

**JSON Example**:
```json
{
  "from_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "to_token": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "amount": "1000000000",
  "chain": "ethereum"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface SwapQuoteResponse {
  from_token: string;
  to_token: string;
  amount_in: string;
  amount_out: string;
  price_impact: string;  // Percentage (e.g., "0.5" = 0.5%)
  route: SwapRoute[];
  gas_estimate: string;
  risk_warnings: string[];
  min_amount_out: string;  // For slippage protection
}

interface SwapRoute {
  pool_address: string;
  pool_name: string;
  token_in: string;
  token_out: string;
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `InvalidTokenError` | Invalid token | Show error: "Invalid token" |
| `400` | `NoRouteFoundError` | No swap route found | Show error: "No swap route available" |
| `404` | `PoolNotFoundError` | Pool not found | Show error: "Pool not available" |
| `502` | `CurveAPIError` | Curve API unavailable | Show error: "Swap service unavailable" + Retry |

### 7. Get Curve Pools

**Method**: `GET`  
**Endpoint**: `/api/v1/defi/curve/pools`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `chain` | `string` | No | Blockchain (default: "ethereum") |
| `sort_by` | `string` | No | Sort field (default: "tvl") | `tvl`, `apy`, `volume` |
| `limit` | `number` | No | Max results (default: 50, max: 200) |
| `min_tvl` | `number` | No | Minimum TVL filter (USD) |

#### Response

##### Success Response (200 OK)
```typescript
interface PoolsResponse {
  pools: Pool[];
  count: number;
  chain: string;
}

interface Pool {
  id: string;
  name: string;
  address: string;
  chain: string;
  tvl_usd: number;
  apy: number;
  volume_24h_usd: number;
  tokens: string[];
}
```

---

## 🔄 User Flows & Use Cases

### Use Case 1: Supply Assets to Aave

**Actor**: Authenticated User  
**Goal**: Supply assets to earn yield  
**Preconditions**: User has wallet with balance, authenticated

#### Flow Steps

1. **Entry Point**: User navigates to `/defi/supply` or taps "Supply" from dashboard
2. **Initial State**: 
   - Load markets via `GET /api/v1/defi/aave/markets`
   - Load user position via `GET /api/v1/defi/aave/positions/{address}`
   - Display market list sorted by APY
3. **User Action**: User selects asset (e.g., USDC)
4. **System Response**:
   - Show asset details (APY, TVL, utilization)
   - Pre-fill user balance
   - Show current health factor
5. **User Action**: User enters amount
6. **System Response**:
   - Real-time validation (balance check)
   - Calculate health factor impact via `POST /api/v1/defi/aave/calculate/health-factor`
   - Show preview: "Health Factor: 2.5 → 2.8"
7. **User Action**: User taps "Confirm Supply"
8. **System Response**:
   - Show transaction preview
   - Show gas estimate
   - Request Privy signature
9. **Success Path**:
   - Transaction signed and broadcast
   - Show success message
   - Update position data
   - Navigate to position view
10. **Error Path**:
    - If insufficient balance: Show error + Max button
    - If health factor too low: Show warning + suggestion
    - If transaction fails: Show error + Retry

#### Flow Diagram
```
[User] → [Supply Screen]
         ↓
    [Select Asset]
         ↓
    [Enter Amount]
         ↓
    [Calculate Impact]
         ↓
    ┌────────────┐
    │ Safe?      │ → No → [Warning] → [Cancel/Adjust]
    └────────────┘
         ↓ Yes
    [Confirm]
         ↓
    [Privy Sign]
         ↓
    ┌────────────┐
    │ Success?   │ → Yes → [Update Position] → [Success]
    └────────────┘
         ↓ No
    [Error] → [Retry]
```

#### Success Criteria
- [ ] User can supply in < 60 seconds
- [ ] Health factor impact is clear
- [ ] Transaction succeeds
- [ ] Position updates correctly

### Use Case 2: Borrow Against Collateral

**Actor**: Authenticated User  
**Goal**: Borrow assets using supplied collateral  
**Preconditions**: User has supplied collateral, authenticated

#### Flow Steps

1. **Entry Point**: User navigates to `/defi/borrow`
2. **Initial State**: 
   - Load borrow markets
   - Load user position
   - Show current health factor
3. **User Action**: User selects asset to borrow
4. **System Response**:
   - Call `GET /api/v1/defi/aave/positions/{address}/borrow-capacity/{asset}`
   - Show max borrowable amount
   - Show health factor after max borrow
5. **User Action**: User enters borrow amount
6. **System Response**:
   - Validate amount (not exceeding max)
   - Calculate health factor impact
   - Show risk warning if HF < 1.5
7. **User Action**: User confirms borrow
8. **System Response**:
   - Show transaction preview
   - Request Privy signature
   - Execute transaction
9. **Success Path**:
   - Transaction succeeds
   - Update position
   - Show success message
10. **Error Path**:
    - If no collateral: Show "Supply collateral first"
    - If health factor too low: Show warning + prevent borrow
    - If transaction fails: Show error + Retry

#### Success Criteria
- [ ] Borrow amount is validated
- [ ] Health factor warnings are clear
- [ ] Transaction succeeds
- [ ] Position updates correctly

### Use Case 3: Swap Tokens via Curve

**Actor**: Authenticated User  
**Goal**: Exchange one token for another  
**Preconditions**: User has source token balance

#### Flow Steps

1. **Entry Point**: User navigates to `/defi/swap`
2. **Initial State**: 
   - Show swap form
   - Load user balances
3. **User Action**: User selects from/to tokens
4. **System Response**:
   - Show token balances
   - Enable amount input
5. **User Action**: User enters amount
6. **System Response**:
   - Call `POST /api/v1/defi/curve/quote`
   - Show quote (amount out, price impact, route)
   - Show risk warnings (if any)
   - Show gas estimate
7. **User Action**: User confirms swap
8. **System Response**:
   - Request Privy signature
   - Execute swap transaction
9. **Success Path**:
   - Transaction succeeds
   - Update balances
   - Show success message
10. **Error Path**:
    - If no route: Show "No swap route available"
    - If price impact too high: Show warning + require confirmation
    - If transaction fails: Show error + Retry

#### Success Criteria
- [ ] Quote loads in < 2 seconds
- [ ] Price impact is clear
- [ ] Swap succeeds
- [ ] Balances update correctly

---

## 📁 File Structure

```
src/modules/defi/
├── supply/
│   ├── Supply.tsx
│   ├── Supply.types.ts
│   ├── Supply.hooks.ts
│   ├── Supply.service.ts
│   └── components/
├── borrow/
│   ├── Borrow.tsx
│   ├── Borrow.types.ts
│   ├── Borrow.hooks.ts
│   ├── Borrow.service.ts
│   └── components/
├── swap/
│   ├── Swap.tsx
│   ├── Swap.types.ts
│   ├── Swap.hooks.ts
│   ├── Swap.service.ts
│   └── components/
├── stake/
│   ├── Stake.tsx
│   ├── Stake.types.ts
│   ├── Stake.hooks.ts
│   └── Stake.service.ts
├── earn/
│   ├── Earn.tsx
│   ├── Earn.types.ts
│   ├── Earn.hooks.ts
│   └── Earn.service.ts
└── bridge/
    ├── Bridge.tsx
    ├── Bridge.types.ts
    ├── Bridge.hooks.ts
    └── Bridge.service.ts
```

## 🔑 Key Implementation Files

### 1. Supply (Lending)

#### `Supply.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { SupplyRequest, SupplyResponse } from './Supply.types';

export const supplyService = {
  async supply(request: SupplyRequest): Promise<SupplyResponse> {
    const response = await apiClient.post<SupplyResponse>(
      '/api/v1/aave/supply',
      request
    );
    return response.data;
  },
  
  async calculateHealthFactor(
    request: HealthFactorRequest
  ): Promise<HealthFactorResponse> {
    const response = await apiClient.post(
      '/api/v1/aave/calculate/health-factor',
      request
    );
    return response.data;
  },
  
  async getSupplyRates(): Promise<SupplyRatesResponse> {
    const response = await apiClient.get('/api/v1/aave/supply-rates');
    return response.data;
  },
};
```

#### `Supply.types.ts`
```typescript
export interface SupplyRequest {
  asset: string;
  amount: string;
  on_behalf_of?: string;
}

export interface SupplyResponse {
  transaction_hash: string;
  status: 'pending' | 'confirmed' | 'failed';
  health_factor: string;
}

export interface HealthFactorRequest {
  asset: string;
  amount: string;
}

export interface HealthFactorResponse {
  health_factor: string;
  health_factor_after_supply: string;
  can_supply: boolean;
}
```

#### `Supply.tsx`
```typescript
'use client';

import React, { useState } from 'react';
import { useSupply, useCalculateHealthFactor } from './Supply.hooks';
import { SupplyForm } from './components/SupplyForm';
import { HealthFactorDisplay } from './components/HealthFactorDisplay';
import { TransactionStatus } from './components/TransactionStatus';

export const Supply: React.FC = () => {
  const [asset, setAsset] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  
  const supplyMutation = useSupply();
  const { data: healthFactor } = useCalculateHealthFactor(
    asset && amount ? { asset, amount } : null
  );

  const handleSupply = async () => {
    await supplyMutation.mutateAsync({
      asset,
      amount,
    });
  };

  return (
    <div className="supply-container">
      <h1>Supply Assets</h1>
      
      <SupplyForm
        asset={asset}
        amount={amount}
        onAssetChange={setAsset}
        onAmountChange={setAmount}
        onSubmit={handleSupply}
        loading={supplyMutation.isPending}
      />
      
      {healthFactor && (
        <HealthFactorDisplay
          current={healthFactor.health_factor}
          after={healthFactor.health_factor_after_supply}
        />
      )}
      
      {supplyMutation.data && (
        <TransactionStatus transaction={supplyMutation.data} />
      )}
    </div>
  );
};
```

### 2. Borrow

#### `Borrow.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { BorrowRequest, BorrowResponse } from './Borrow.types';

export const borrowService = {
  async borrow(request: BorrowRequest): Promise<BorrowResponse> {
    const response = await apiClient.post<BorrowResponse>(
      '/api/v1/aave/borrow',
      request
    );
    return response.data;
  },
  
  async getBorrowRates(): Promise<BorrowRatesResponse> {
    const response = await apiClient.get('/api/v1/aave/borrow-rates');
    return response.data;
  },
  
  async getHealthFactor(): Promise<HealthFactorResponse> {
    const response = await apiClient.get('/api/v1/aave/health');
    return response.data;
  },
};
```

### 3. Swap

#### `Swap.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { SwapRequest, SwapResponse } from './Swap.types';

export const swapService = {
  async getQuote(request: SwapQuoteRequest): Promise<SwapQuote> {
    const response = await apiClient.post('/api/v1/swap/quote', request);
    return response.data;
  },
  
  async executeSwap(request: SwapRequest): Promise<SwapResponse> {
    const response = await apiClient.post<SwapResponse>(
      '/api/v1/swap/execute',
      request
    );
    return response.data;
  },
};
```

## 📝 Complete File List

### Supply
- [x] `Supply.service.ts` - Service structure
- [x] `Supply.types.ts` - Types structure
- [x] `Supply.tsx` - Component structure
- [ ] `Supply.hooks.ts` - Hooks
- [ ] `components/SupplyForm.tsx`
- [ ] `components/HealthFactorDisplay.tsx`
- [ ] `components/TransactionStatus.tsx`
- [ ] `__tests__/Supply.test.tsx`

### Borrow
- [x] `Borrow.service.ts` - Service structure
- [ ] `Borrow.tsx` - Main component
- [ ] `Borrow.types.ts` - Types
- [ ] `Borrow.hooks.ts` - Hooks
- [ ] `components/BorrowForm.tsx`
- [ ] `__tests__/Borrow.test.tsx`

### Swap
- [x] `Swap.service.ts` - Service structure
- [ ] `Swap.tsx` - Main component
- [ ] `Swap.types.ts` - Types
- [ ] `Swap.hooks.ts` - Hooks
- [ ] `components/SwapForm.tsx`
- [ ] `components/TokenSelector.tsx`
- [ ] `components/SwapQuote.tsx`
- [ ] `__tests__/Swap.test.tsx`

### Stake
- [ ] `Stake.tsx`
- [ ] `Stake.types.ts`
- [ ] `Stake.hooks.ts`
- [ ] `Stake.service.ts`

### Earn
- [ ] `Earn.tsx`
- [ ] `Earn.types.ts`
- [ ] `Earn.hooks.ts`
- [ ] `Earn.service.ts`

### Bridge
- [ ] `Bridge.tsx`
- [ ] `Bridge.types.ts`
- [ ] `Bridge.hooks.ts`
- [ ] `Bridge.service.ts`

---

## 🧪 Testing Requirements

### Unit Tests

**Supply Component**:
- [ ] Renders asset selector correctly
- [ ] Validates amount (balance check)
- [ ] Calculates health factor impact
- [ ] Handles Privy integration
- [ ] Shows risk warnings

**Borrow Component**:
- [ ] Validates borrow capacity
- [ ] Prevents borrow if HF < 1.0
- [ ] Shows health factor warnings
- [ ] Handles transaction execution

**Swap Component**:
- [ ] Gets swap quote correctly
- [ ] Displays price impact
- [ ] Shows risk warnings
- [ ] Handles route selection

### Integration Tests

**DeFi Operations Flow**:
- [ ] Supply → Position update
- [ ] Borrow → Health factor update
- [ ] Swap → Balance update
- [ ] Health factor monitoring

### E2E Tests

**Complete DeFi Journey**:
- [ ] Supply assets
- [ ] Borrow against collateral
- [ ] Monitor health factor
- [ ] Swap tokens
- [ ] Handle liquidation warnings

### Performance Tests

- [ ] Market data loads in < 2 seconds
- [ ] Health factor calculation in < 1 second
- [ ] Swap quote in < 2 seconds
- [ ] Transaction execution in < 30 seconds

### Accessibility Tests

- [ ] Screen reader announces health factor
- [ ] Keyboard navigation works
- [ ] Risk warnings are accessible
- [ ] Color contrast meets WCAG 2.1 AA

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Liquidation Risk**
   - **Risk**: Users don't understand health factor dynamics
   - **Mitigation**: Clear warnings, visual indicators, educational content
   - **Validation**: User testing, monitor liquidation events

2. **Smart Contract Risk**
   - **Risk**: Protocol vulnerabilities or exploits
   - **Mitigation**: Risk analysis, protocol selection, warnings
   - **Validation**: Monitor protocol security, audit status

3. **Slippage Risk**
   - **Risk**: Large swaps have high price impact
   - **Mitigation**: Slippage protection, warnings, route optimization
   - **Validation**: Test with various swap sizes

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Health Factor Monitoring**
   - **Debt**: Users can't track position risk
   - **Cost**: Liquidations, poor UX
   - **Prevention**: Real-time health factor updates

2. **Hardcoded Protocol Addresses**
   - **Debt**: New protocols require code changes
   - **Cost**: Maintenance burden
   - **Prevention**: Dynamic protocol configuration

### Validation & Testing Strategy

**Success Criteria**:
- ✅ DeFi operations success rate > 99%
- ✅ Zero liquidations due to UI issues
- ✅ Health factor accuracy > 99.9%
- ✅ Average transaction time < 30 seconds

**Failure Detection**:
- Monitor health factor changes
- Track transaction failures
- Alert on liquidation events
- Log all DeFi operations

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/defi/aave_router.py`
- **Backend Controller**: `src/app/presentation/http/controllers/defi/curve_router.py`
- **Backend Schemas**: `src/app/presentation/http/controllers/defi/aave_schemas.py`
- **Backend Schemas**: `src/app/presentation/http/controllers/defi/curve_schemas.py`
- **Domain Entity**: `src/app/domain/entities/lending/aave_market.py`
- **Domain Entity**: `src/app/domain/entities/lending/aave_position.py`
- **Application Interactor**: `src/app/application/commands/curve/get_swap_quote.py`
- **Related Modules**: 
  - Wallet (source of funds)
  - Dashboard (position overview)
  - Chat (DeFi advice)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
