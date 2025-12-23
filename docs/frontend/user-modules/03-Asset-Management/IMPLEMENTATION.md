# Wallet & Asset Management Module Implementation Files

> **Complete TypeScript/React Implementation for Wallet Modules**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)

## 📖 Module Overview

The **Wallet & Asset Management** module provides users with complete control over their crypto assets. It handles wallet operations, token transfers, transaction history, and NFT management.

### Key Capabilities
1. **Wallet Overview**: Multi-wallet management with portfolio aggregation
2. **Send Tokens**: Secure token transfers with gas estimation
3. **Receive Tokens**: QR codes and address sharing
4. **Token Details**: Deep dive into individual token holdings
5. **Transaction History**: Complete transaction log with filtering
6. **NFT Marketplace**: Browse and manage NFTs

### Business Value
- **User Control**: Complete asset management in one place
- **Security**: Secure transaction execution via Privy
- **Transparency**: Full transaction history and audit trail
- **Convenience**: Multi-wallet support, QR codes, easy transfers

---

## 🎨 UX/UI Specifications

### Design Principles (First Principles Analysis)

**Essential Problem**: Users need secure, intuitive control over their crypto assets across multiple wallets and chains.

**Root Cause Analysis**:
- **Complexity Barrier**: Multiple wallets, chains, tokens create confusion
- **Solution**: Unified interface with clear wallet selection and chain filtering
- **Security Concerns**: Users fear making mistakes in transactions
- **Solution**: Clear previews, gas estimation, confirmation steps

**Design Decisions**:
1. **Wallet-First**: Show wallet selection prominently
2. **Chain-Aware**: Clear chain indicators throughout
3. **Transaction Safety**: Multi-step confirmation with clear previews
4. **Real-Time Updates**: Show transaction status immediately

### Trade-off Analysis (Design Thinking)

**Key Design Decisions with Trade-offs**:

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Wallet-Centric Design** | Transaction-Centric | User Mental Model vs. Data Model | Users think in terms of wallets, not transactions |
| **Multi-Wallet Support** | Single Wallet | Complexity vs. Flexibility | Power users need multiple wallets, but adds UI complexity |
| **Security-First Approach** | Convenience-First | Security vs. UX Speed | Private keys are critical; security cannot be compromised |
| **Transaction History** | Summary Only | Completeness vs. Performance | Full history needed for audits, but can be slow with many transactions |
| **HPKE Encryption for Export** | Plain Text | Security vs. Simplicity | Private keys must be encrypted, even during export |

### Visual Design

#### Layout Structure
```
┌─────────────────────────────────────────┐
│ Header: Wallet Selector + Chain Filter  │
├─────────────────────────────────────────┤
│ ┌───────────────────────────────────┐  │
│ │  Wallet Overview Card              │  │
│ │  Address: 0x123...                 │  │
│ │  Total Value: $12,450.50          │  │
│ │  [Send] [Receive] [Details]       │  │
│ └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│ Token Holdings                          │
│ ┌────┐ ┌────┐ ┌────┐ ┌────┐         │
│ │ETH │ │USDC│ │DAI │ │... │         │
│ │2.5 │ │5K  │ │1K  │ │... │         │
│ └────┘ └────┘ └────┘ └────┘         │
├─────────────────────────────────────────┤
│ Recent Transactions                    │
│ [Transaction List]                     │
└─────────────────────────────────────────┘
```

#### Color Palette
- **Primary**: `#3B82F6` (Blue) - Trust, security
- **Success**: `#10B981` (Green) - Successful transactions
- **Warning**: `#F59E0B` (Amber) - Pending transactions
- **Error**: `#EF4444` (Red) - Failed transactions
- **Background**: `#FFFFFF` (White) / `#F9FAFB` (Gray-50)
- **Card Background**: `#FFFFFF` with shadow

#### Component Specifications

##### Wallet Card
```typescript
interface WalletCardProps {
  wallet: Wallet;
  totalValue: number;
  onSend: () => void;
  onReceive: () => void;
  onDetails: () => void;
}
```

**Visual Design**:
- Wallet address (truncated with copy button)
- Total value (large, prominent)
- Chain badge
- Action buttons (Send, Receive, Details)
- Hover: Show full address

##### Send Form
```typescript
interface SendFormProps {
  wallet: Wallet;
  onSend: (request: SendTokenRequest) => void;
  onCancel: () => void;
}
```

**Visual Design**:
- Recipient input (with ENS/address validation)
- Amount input (with max button, balance display)
- Token selector
- Gas estimate display
- Preview section (shows total cost)
- Confirm button (disabled until valid)

##### QR Code Display
```typescript
interface QRCodeProps {
  address: string;
  amount?: number;
  token?: string;
}
```

**Visual Design**:
- Large QR code (200x200px minimum)
- Address below (with copy button)
- Share button
- Amount/token info (if specified)

### Responsive Breakpoints

**Mobile** (< 640px):
- Full-screen wallet view
- Bottom sheet for send form
- Full-screen QR code
- Swipe gestures for navigation

**Tablet** (640px - 1024px):
- Side-by-side wallet and tokens
- Modal for send form
- Centered QR code

**Desktop** (> 1024px):
- Three-column layout
- Inline send form
- Sidebar for transaction history

### Accessibility Requirements

1. **Screen Readers**:
   - Announce wallet addresses
   - Describe transaction status
   - Announce balance changes

2. **Keyboard Navigation**:
   - Tab through all inputs
   - Enter to submit forms
   - Escape to cancel

3. **Color Contrast**:
   - All text: 4.5:1 minimum
   - Transaction status: 4.5:1
   - QR code: High contrast

### Loading States

**Wallet Load**:
- Skeleton for wallet card
- Skeleton for token list

**Transaction Sending**:
- Loading spinner
- "Broadcasting transaction..."
- Disable form inputs

**Transaction Confirming**:
- Progress indicator
- "Waiting for confirmation..."
- Show block number

### Empty States

**No Wallets**:
- Illustration: Empty wallet
- Message: "Connect a wallet to get started"
- CTA: "Connect Wallet"

**No Transactions**:
- Message: "No transactions yet"
- CTA: "Send Tokens"

### Error States

**Transaction Failed**:
- Error message
- Transaction hash (for debugging)
- Retry button
- Support link

**Invalid Address**:
- Inline error below input
- Red border
- Error icon
- Help text

---

## 🔌 API Endpoints

### 1. Get My Wallets

**Method**: `GET`  
**Endpoint**: `/api/v1/wallet/me`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### Response

##### Success Response (200 OK)
```typescript
interface MyWalletsResponse {
  user_id: number;
  privy_user_id: string | null;
  wallets: Wallet[];
  primary_wallet_address: string | null;
  privy_connected: boolean;
  message: string | null;
}

interface Wallet {
  wallet_id: string;
  address: string;
  chain_type: string;  // "ethereum", "solana", etc.
  wallet_type: string;  // "embedded", "external", "server_controlled"
  is_primary: boolean;
  source: string;  // "privy", "local", "both"
  created_at: string | null;  // ISO 8601
}
```

**Response Schema**:
| Field | Type | Description |
|-------|------|-------------|
| `user_id` | `number` | Internal user ID |
| `privy_user_id` | `string \| null` | Privy user ID if linked |
| `wallets` | `Wallet[]` | Array of user wallets |
| `primary_wallet_address` | `string \| null` | Primary wallet address |
| `privy_connected` | `boolean` | Whether Privy data was fetched |
| `message` | `string \| null` | Optional status message |

**JSON Example**:
```json
{
  "user_id": 42,
  "privy_user_id": "did:privy:abc123",
  "wallets": [
    {
      "wallet_id": "wallet_xyz",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "is_primary": true,
      "source": "privy",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "primary_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "privy_connected": true,
  "message": null
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Database unavailable | Show error: "Unable to load wallets" + Retry |

### 2. Sync Wallets

**Method**: `POST`  
**Endpoint**: `/api/v1/wallet/sync`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SyncWalletsRequest {
  wallet_addresses?: string[];  // Deprecated: Use 'wallets' instead
  wallets?: SyncWalletItem[];
}

interface SyncWalletItem {
  address: string;  // Required: Wallet address (0x...)
  chain_type?: string;  // Optional: Default "ethereum"
  wallet_type?: string;  // Optional: Default "embedded"
  privy_wallet_id?: string;  // Optional: Privy wallet ID
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `wallet_addresses` | `string[]` | No | Deprecated: List of addresses | Valid 0x addresses |
| `wallets` | `SyncWalletItem[]` | No | Preferred: List of wallet details | - |
| `wallets[].address` | `string` | **Yes** | Wallet address | Valid 0x address |
| `wallets[].chain_type` | `string` | No | Blockchain type | "ethereum", "polygon", "base", etc. |
| `wallets[].wallet_type` | `string` | No | Wallet type | "embedded", "external", "imported" |
| `wallets[].privy_wallet_id` | `string` | No | Privy wallet ID | - |

**JSON Example**:
```json
{
  "wallets": [
    {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "privy_wallet_id": "wallet_abc123"
    }
  ]
}
```

#### Response

##### Success Response (200 OK)
Returns `MyWalletsResponse` (same as GET /me)

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `400` | `ValidationError` | Invalid wallet data | Show inline errors |
| `503` | `DataMapperError` | Database unavailable | Show error toast + Retry |

### 3. Export Wallet

**Method**: `POST`  
**Endpoint**: `/api/v1/wallet/export`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ExportWalletRequest {
  wallet_id: string;  // Required: Privy wallet ID
  wallet_address?: string;  // Optional: Address for verification
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `wallet_id` | `string` | **Yes** | Privy wallet ID | Valid wallet ID |
| `wallet_address` | `string` | No | Wallet address for verification | Valid 0x address |

**JSON Example**:
```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "wallet_address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7"
}
```

#### Response

##### Success Response (200 OK)
```typescript
interface ExportWalletResponse {
  wallet_id: string;
  address: string;
  private_key: string;  // Decrypted private key (HPKE)
  chain_type: string;
}
```

**⚠️ Security Warning**: Private key is sensitive. Display only in secure context with user confirmation.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `ForbiddenError` | Wallet doesn't belong to user | Show error: "You don't have permission to export this wallet" |
| `404` | `NotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `500` | `InternalServerError` | Export failed | Show error: "Export failed. Please try again." |

### 4. Get Portfolio (Wallet Overview)

**Method**: `GET`  
**Endpoint**: `/api/v1/user/portfolio/me`  
**Auth Required**: Yes (Bearer Token)

*See Dashboard module documentation for complete API specification.*

### 5. Log Transaction

**Method**: `POST`  
**Endpoint**: `/api/v1/user/transactions`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface LogTransactionRequest {
  tx_hash: string;  // Required: Transaction hash (0x..., 66 chars)
  from_address: string;  // Required: Sender address
  to_address: string | null;  // Optional: Recipient address (null for contract creation)
  value: string;  // Required: Amount in Wei (as string)
  chain_id: number;  // Required: Chain ID (1=Mainnet, 8453=Base, etc.)
  tx_type?: string;  // Optional: Default "send"
  asset_symbol?: string;  // Optional: Token symbol (ETH, USDC, etc.)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `tx_hash` | `string` | **Yes** | Transaction hash | 66 chars, starts with 0x |
| `from_address` | `string` | **Yes** | Sender address | Valid 0x address |
| `to_address` | `string \| null` | No | Recipient address | Valid 0x address or null |
| `value` | `string` | **Yes** | Amount in Wei | Valid number string |
| `chain_id` | `number` | **Yes** | Chain ID | Valid chain ID |
| `tx_type` | `string` | No | Transaction type | "send", "receive", "swap", etc. |
| `asset_symbol` | `string` | No | Token symbol | "ETH", "USDC", etc. |

**JSON Example**:
```json
{
  "tx_hash": "0xabc123def456...",
  "from_address": "0x1234567890abcdef1234567890abcdef12345678",
  "to_address": "0x9876543210fedcba9876543210fedcba98765432",
  "value": "1000000000000000000",
  "chain_id": 8453,
  "tx_type": "send",
  "asset_symbol": "ETH"
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface LogTransactionResponse {
  transaction_id: string;
  tx_hash: string;
  status: string;  // "pending", "confirmed", "failed"
  created_at: string;  // ISO 8601
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValidationError` | Invalid transaction data | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `409` | `ConflictError` | Transaction already logged | Ignore (idempotent) |
| `503` | `DataMapperError` | Database unavailable | Show error: "Failed to log transaction" |

---

## 🔄 User Flows & Use Cases

### Use Case 1: View Wallet Overview

**Actor**: Authenticated User  
**Goal**: View all wallets and their balances  
**Preconditions**: User is authenticated

#### Flow Steps

1. **Entry Point**: User navigates to `/wallet` or taps "Wallet" tab
2. **Initial State**: 
   - Show loading skeleton
   - Call `GET /api/v1/wallet/me`
   - Call `GET /api/v1/user/portfolio/me` (for primary wallet)
3. **System Response**:
   - Display wallet list
   - Show primary wallet with total value
   - Display token holdings
   - Show recent transactions
4. **User Action**: User selects different wallet
5. **System Response**:
   - Update portfolio data for selected wallet
   - Refresh token list
   - Refresh transaction history
6. **Success Path**:
   - All data displays correctly
   - User can interact with wallets
7. **Error Path**:
   - If no wallets: Show "Connect Wallet" CTA
   - If Privy disconnected: Show sync button
   - If API error: Show error + Retry

#### Flow Diagram
```
[User] → [Wallet Overview]
         ↓
    [Load Wallets]
         ↓
    ┌────────────┐
    │ Has Wallets?│ → No → [Connect Wallet CTA]
    └────────────┘
         ↓ Yes
    [Load Portfolio]
         ↓
    [Display Data]
         ↓
    [User Selects Wallet]
         ↓
    [Refresh Data]
```

#### Success Criteria
- [ ] Wallets load in < 2 seconds
- [ ] Portfolio data displays correctly
- [ ] Wallet switching is smooth
- [ ] Error states are clear

### Use Case 2: Send Tokens

**Actor**: Authenticated User  
**Goal**: Send tokens to another address  
**Preconditions**: User has wallet with balance

#### Flow Steps

1. **Entry Point**: User taps "Send" button on wallet card
2. **Initial State**: 
   - Open send form
   - Pre-fill wallet address
   - Show available balance
3. **User Action**: User enters recipient address
4. **System Response**:
   - Validate address (ENS/0x format)
   - Show validation feedback
5. **User Action**: User enters amount
6. **System Response**:
   - Validate amount (not exceeding balance)
   - Estimate gas (if backend supports)
   - Show total cost preview
7. **User Action**: User taps "Confirm"
8. **System Response**:
   - Show Privy signature prompt
   - User signs transaction
   - Privy broadcasts transaction
   - Receive `txHash`
9. **Success Path**:
   - Call `POST /api/v1/user/transactions` to log
   - Show success message
   - Navigate to transaction receipt
   - Update wallet balance
10. **Error Path**:
    - If invalid address: Show inline error
    - If insufficient balance: Show error + Max button
    - If transaction fails: Show error + Retry
    - If logging fails: Show warning (transaction still succeeded)

#### Flow Diagram
```
[User] → [Send Button]
         ↓
    [Send Form]
         ↓
    [Enter Recipient]
         ↓
    [Enter Amount]
         ↓
    [Estimate Gas]
         ↓
    [Confirm]
         ↓
    [Privy Sign]
         ↓
    ┌────────────┐
    │ Success?   │ → Yes → [Log Transaction] → [Receipt]
    └────────────┘
         ↓ No
    [Error] → [Retry]
```

#### Success Criteria
- [ ] Form validation is clear and immediate
- [ ] Gas estimation is accurate
- [ ] Transaction completes in < 30 seconds
- [ ] Transaction is logged successfully

### Use Case 3: Receive Tokens

**Actor**: Authenticated User  
**Goal**: Share wallet address to receive tokens  
**Preconditions**: User has wallet

#### Flow Steps

1. **Entry Point**: User taps "Receive" button
2. **Initial State**: 
   - Load wallet address
   - Generate QR code
3. **System Response**:
   - Display QR code
   - Display address with copy button
   - Show share options
4. **User Action**: User taps "Copy Address"
5. **System Response**:
   - Copy address to clipboard
   - Show "Copied!" toast
6. **User Action**: User taps "Share"
7. **System Response**:
   - Open native share dialog
   - User shares via preferred method

#### Success Criteria
- [ ] QR code displays correctly
- [ ] Address copies successfully
- [ ] Share functionality works
- [ ] QR code is scannable

---

## 📁 File Structure

```
src/modules/wallet/
├── overview/
│   ├── WalletOverview.tsx
│   ├── WalletOverview.types.ts
│   ├── WalletOverview.hooks.ts
│   ├── WalletOverview.service.ts
│   └── components/
├── send/
│   ├── SendTokens.tsx
│   ├── SendTokens.types.ts
│   ├── SendTokens.hooks.ts
│   ├── SendTokens.service.ts
│   └── components/
├── receive/
│   ├── ReceiveTokens.tsx
│   ├── ReceiveTokens.types.ts
│   └── components/
├── token/
│   ├── TokenDetail.tsx
│   ├── TokenDetail.types.ts
│   ├── TokenDetail.hooks.ts
│   └── TokenDetail.service.ts
├── transactions/
│   ├── TransactionHistory.tsx
│   ├── TransactionHistory.types.ts
│   ├── TransactionHistory.hooks.ts
│   └── TransactionHistory.service.ts
└── nft/
    ├── NFTMarketplace.tsx
    ├── NFTMarketplace.types.ts
    └── components/
```

## 🔑 Key Implementation Files

### 1. Wallet Overview

#### `WalletOverview.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { WalletResponse } from './WalletOverview.types';

export const walletService = {
  async getWalletOverview(): Promise<WalletResponse> {
    const response = await apiClient.get<WalletResponse>(
      '/api/v1/user/wallet/overview'
    );
    return response.data;
  },
  
  async getWallets(): Promise<WalletListResponse> {
    const response = await apiClient.get('/api/v1/user/wallets');
    return response.data;
  },
};
```

### 2. Send Tokens

#### `SendTokens.service.ts`
```typescript
import { apiClient } from '@/api/client';
import type { SendTokenRequest, SendTokenResponse } from './SendTokens.types';

export const sendTokensService = {
  async sendTokens(request: SendTokenRequest): Promise<SendTokenResponse> {
    const response = await apiClient.post<SendTokenResponse>(
      '/api/v1/user/wallet/send',
      request
    );
    return response.data;
  },
  
  async estimateGas(request: EstimateGasRequest): Promise<GasEstimate> {
    const response = await apiClient.post('/api/v1/user/wallet/estimate-gas', request);
    return response.data;
  },
};
```

### 3. Receive Tokens

#### `ReceiveTokens.tsx`
```typescript
'use client';

import React from 'react';
import { useWallet } from '../overview/WalletOverview.hooks';
import { QRCode } from './components/QRCode';
import { AddressDisplay } from './components/AddressDisplay';
import { CopyButton } from '@/design-system/components/CopyButton';

export const ReceiveTokens: React.FC = () => {
  const { data: wallet } = useWallet();

  if (!wallet) {
    return <div>Loading wallet...</div>;
  }

  return (
    <div className="receive-tokens-container">
      <h1>Receive Tokens</h1>
      <QRCode address={wallet.address} />
      <AddressDisplay address={wallet.address} />
      <CopyButton text={wallet.address} />
    </div>
  );
};
```

## 📝 Complete File List

### Wallet Overview
- [x] `WalletOverview.service.ts` - Service structure
- [ ] `WalletOverview.tsx` - Main component
- [ ] `WalletOverview.types.ts` - Types
- [ ] `WalletOverview.hooks.ts` - Hooks
- [ ] `components/WalletCard.tsx`
- [ ] `components/TokenBalance.tsx`
- [ ] `__tests__/WalletOverview.test.tsx`

### Send Tokens
- [x] `SendTokens.service.ts` - Service structure
- [ ] `SendTokens.tsx` - Main component
- [ ] `SendTokens.types.ts` - Types
- [ ] `SendTokens.hooks.ts` - Hooks
- [ ] `components/SendForm.tsx`
- [ ] `components/RecipientInput.tsx`
- [ ] `components/AmountInput.tsx`
- [ ] `components/TransactionPreview.tsx`
- [ ] `__tests__/SendTokens.test.tsx`

### Receive Tokens
- [x] `ReceiveTokens.tsx` - Component structure
- [ ] `ReceiveTokens.types.ts` - Types
- [ ] `components/QRCode.tsx`
- [ ] `components/AddressDisplay.tsx`
- [ ] `__tests__/ReceiveTokens.test.tsx`

### Token Detail
- [ ] `TokenDetail.tsx`
- [ ] `TokenDetail.types.ts`
- [ ] `TokenDetail.hooks.ts`
- [ ] `TokenDetail.service.ts`

### Transaction History
- [ ] `TransactionHistory.tsx`
- [ ] `TransactionHistory.types.ts`
- [ ] `TransactionHistory.hooks.ts`
- [ ] `TransactionHistory.service.ts`

### NFT Marketplace
- [ ] `NFTMarketplace.tsx`
- [ ] `NFTMarketplace.types.ts`

---

## 🧪 Testing Requirements

### Unit Tests

**Wallet Overview Component**:
- [ ] Renders wallet list correctly
- [ ] Displays portfolio data
- [ ] Handles wallet selection
- [ ] Shows loading states
- [ ] Displays error states

**Send Tokens Component**:
- [ ] Validates recipient address
- [ ] Validates amount (balance check)
- [ ] Estimates gas correctly
- [ ] Handles Privy integration
- [ ] Logs transaction after send

**Receive Tokens Component**:
- [ ] Generates QR code correctly
- [ ] Copies address to clipboard
- [ ] Shares address successfully

### Integration Tests

**Wallet Flow**:
- [ ] Load wallets
- [ ] Sync wallets from Privy
- [ ] Switch between wallets
- [ ] Send transaction (mock Privy)
- [ ] Log transaction

### E2E Tests

**Complete Wallet Journey**:
- [ ] View wallet overview
- [ ] Send tokens (with real Privy)
- [ ] Receive tokens (QR code scan)
- [ ] View transaction history

### Performance Tests

- [ ] Wallet load in < 2 seconds
- [ ] QR code generation in < 500ms
- [ ] Transaction logging in < 1 second
- [ ] Smooth wallet switching

### Accessibility Tests

- [ ] Screen reader announces wallet addresses
- [ ] Keyboard navigation works
- [ ] QR code is accessible
- [ ] Color contrast meets WCAG 2.1 AA

---

## 🔍 Risk Assessment (CTO Methodology)

### Cognitive Limitation Analysis

**Areas Where Analysis May Overlook Factors**:

1. **Private Key Exposure**
   - **Risk**: Export endpoint exposes sensitive data
   - **Mitigation**: HPKE encryption, user confirmation, audit logging
   - **Validation**: Security audit, penetration testing

2. **Transaction Replay**
   - **Risk**: Same transaction logged multiple times
   - **Mitigation**: Idempotent logging, transaction hash uniqueness
   - **Validation**: Test duplicate transaction handling

3. **Multi-Wallet Confusion**
   - **Risk**: Users send from wrong wallet
   - **Mitigation**: Clear wallet selection, confirmation dialogs
   - **Validation**: User testing with multiple wallets

### Technical Debt Assessment

**Rapid Implementation Compromises to Avoid**:

1. **No Transaction Caching**
   - **Debt**: Reload all transactions on mount
   - **Cost**: Slow initial load, poor UX
   - **Prevention**: Implement transaction caching with React Query

2. **Hardcoded Chain IDs**
   - **Debt**: New chains require code changes
   - **Cost**: Maintenance burden
   - **Prevention**: Dynamic chain configuration

### Validation & Testing Strategy

**Module-Specific Success Criteria**:
- ✅ Wallet operations success rate > 99% (sync, export, create)
- ✅ Transaction logging accuracy > 99.9% (verified against blockchain)
- ✅ Average send time < 30 seconds (end-to-end)
- ✅ Zero private key leaks (security audit required)
- ✅ Wallet sync time < 2 seconds (for 5 wallets)
- ✅ Transaction history load < 1 second (for 100 transactions)
- ✅ NFT portfolio load < 3 seconds (for 50 NFTs)
- ✅ Bitcoin transaction accuracy > 99.9% (when enabled)

**Module-Specific Test Requirements**:
- **Unit Tests**: Wallet validation, transaction parsing, NFT metadata processing
- **Integration Tests**: Wallet sync, transaction logging, NFT fetching, Bitcoin integration
- **E2E Tests**: Complete wallet flow (create → sync → send → history), NFT browsing
- **Security Tests**: Private key encryption, export security, transaction signing
- **Performance Tests**: Large transaction history (1000+), multiple wallets (10+), large NFT collections (100+)
- **Accessibility Tests**: Wallet selection, transaction forms, NFT gallery navigation

**Failure Detection & Monitoring**:
- Monitor transaction logging errors (alert if > 0.1%)
- Track wallet sync failures (alert if > 1%)
- Alert on ALL export operations (security audit trail)
- Log all wallet operations (for security audit)
- Monitor private key encryption/decryption operations
- Track transaction signing failures
- Alert on suspicious wallet activity patterns

---

## 📚 References

- **Backend Controller**: `src/app/presentation/http/controllers/wallet/my_wallets.py`
- **Backend Controller**: `src/app/presentation/http/controllers/wallet/export_wallet.py`
- **Backend Controller**: `src/app/presentation/http/controllers/portfolio/router.py`
- **Domain Entity**: `src/app/domain/entities/wallet.py`
- **Application Interactor**: `src/app/application/commands/wallet/export_wallet.py`
- **Related Modules**: 
  - Dashboard (portfolio data source)
  - DeFi Operations (uses wallet for transactions)

---

**Note**: These are implementation file structures. Actual files should be created in the frontend codebase repository.
