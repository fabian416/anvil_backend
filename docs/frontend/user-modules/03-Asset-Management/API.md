# Asset Management API Documentation

> **Complete API Documentation**  
> **Methodology**: CTO Engineering Framework (First Principles + Design Thinking + Systems Thinking)  
> **Base URL**: `/api/v1/wallet` and `/api/v1/user/transactions`

---

## 📋 Table of Contents

1. [Wallet Endpoints](#wallet-endpoints)
2. [Transaction Endpoints](#transaction-endpoints)
3. [NFT Endpoints](#nft-endpoints)
4. [Bitcoin Endpoints](#bitcoin-endpoints)
5. [WebSocket Connections](#websocket-connections)
6. [Request/Response Schemas](#requestresponse-schemas)
7. [Error Handling](#error-handling)

---

## 🔌 Wallet Endpoints

### 1. Get My Wallets

**Method**: `GET`  
**Endpoint**: `/api/v1/wallet/me`  
**Auth Required**: Yes (Bearer Token)

**Note**: This endpoint combines data from:
- Local database (primary wallet stored during login)
- Privy API (all linked wallets)

If Privy fetch fails, only local data is returned with a message.

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
  chain_type: string;            // "ethereum", "solana", etc.
  wallet_type: string;           // "embedded", "external", "server_controlled"
  is_primary: boolean;
  source: string;                // "privy", "local", "both"
  created_at: string | null;     // ISO 8601
}
```

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
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to load wallets" + Retry |

---

### 2. Sync Wallets

**Method**: `POST`  
**Endpoint**: `/api/v1/wallet/sync`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface SyncWalletsRequest {
  wallet_addresses?: string[];    // Deprecated: Use 'wallets' instead
  wallets?: SyncWalletItem[];
}

interface SyncWalletItem {
  address: string;                // Required: Wallet address (0x...)
  chain_type?: string;            // Optional: Default "ethereum"
  wallet_type?: string;           // Optional: Default "embedded"
  privy_wallet_id?: string;       // Optional: Privy wallet ID
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
| `400` | `ValidationError` | Invalid wallet data | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error toast + Retry |

---

### 3. Export Wallet

**Method**: `POST`  
**Endpoint**: `/api/v1/wallet/export`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Request Body
```typescript
interface ExportWalletRequest {
  wallet_id: string;              // Required: Privy wallet ID
  wallet_address?: string;        // Optional: Address for verification
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
  private_key: string;            // Decrypted private key (HPKE)
  chain_type: string;
}
```

**⚠️ Security Warning**: Private key is sensitive. Display only in secure context with user confirmation.

**JSON Example**:
```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7",
  "private_key": "0x...",
  "chain_type": "ethereum"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `403` | `ForbiddenError` | Wallet doesn't belong to user | Show error: "You don't have permission to export this wallet" |
| `404` | `NotFoundError` | Wallet not found | Show error: "Wallet not found" |
| `500` | `InternalServerError` | Export failed | Show error: "Export failed. Please try again." |

---

## 🔌 Transaction Endpoints

### 4. Log Transaction

**Method**: `POST`  
**Endpoint**: `/api/v1/user/transactions`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Headers
```http
Authorization: Bearer {access_token}
Content-Type: application/json
```

##### Request Body
```typescript
interface LogTransactionRequest {
  tx_hash: string;                // Required: Transaction hash (0x..., exactly 66 chars)
  from_address: string;           // Required: Sender address (0x..., exactly 42 chars)
  to_address: string | null;      // Optional: Recipient address (null for contract creation)
  value: string;                  // Required: Amount in Wei (as string)
  chain_id: number;               // Required: Chain ID (1=Mainnet, 8453=Base, etc.)
  tx_type?: string;                // Optional: Default "send"
  asset_symbol?: string;          // Optional: Token symbol (ETH, USDC, etc.)
  data?: string;                  // Optional: Transaction data (for contract calls)
}
```

**Request Schema**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `tx_hash` | `string` | **Yes** | Transaction hash | Exactly 66 chars, starts with 0x |
| `from_address` | `string` | **Yes** | Sender address | Exactly 42 chars, starts with 0x |
| `to_address` | `string \| null` | No | Recipient address | Valid 0x address or null |
| `value` | `string` | **Yes** | Amount in Wei | Valid number string |
| `chain_id` | `number` | **Yes** | Chain ID | Valid chain ID (1, 8453, 42161, etc.) |
| `tx_type` | `string` | No | Transaction type | "send", "swap", "approve", "fund", etc. |
| `asset_symbol` | `string` | No | Token symbol | "ETH", "USDC", "WETH", etc. |
| `data` | `string` | No | Transaction data | Hex string (for contract calls) |

**JSON Example**:
```json
{
  "tx_hash": "0xabc123def456...",
  "from_address": "0x1234567890abcdef1234567890abcdef12345678",
  "to_address": "0x9876543210fedcba9876543210fedcba98765432",
  "value": "1000000000000000000",
  "chain_id": 8453,
  "tx_type": "send",
  "asset_symbol": "ETH",
  "data": null
}
```

#### Response

##### Success Response (201 Created)
```typescript
interface LogTransactionResponse {
  id: number;                     // Database ID
  tx_hash: string;
  status: string;                 // "pending" | "success" | "failed"
  chain: string;                  // Blockchain name
  tx_type: string;
  from_address: string;
  to_address: string | null;
  created_at: string;             // ISO 8601
}
```

**JSON Example**:
```json
{
  "id": 123,
  "tx_hash": "0xabc123def456...",
  "status": "pending",
  "chain": "base",
  "tx_type": "send",
  "from_address": "0x1234567890abcdef1234567890abcdef12345678",
  "to_address": "0x9876543210fedcba9876543210fedcba98765432",
  "created_at": "2024-01-15T10:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `WalletNotFoundForTransactionError` | Wallet not found for user | Show error: "Wallet not found" |
| `400` | `ValidationError` | Invalid transaction data | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `500` | `TransactionLogError` | Failed to log transaction | Show error: "Failed to log transaction" + Retry |
| `503` | `DataMapperError` | Service unavailable | Show error: "Service temporarily unavailable" + Retry |

---

### 5. Get Transaction History

**Method**: `GET`  
**Endpoint**: `/api/v1/user/transactions`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |
| `chain` | `string` | No | Filter by chain | All chains |
| `status` | `string` | No | Filter by status | All statuses |
| `tx_type` | `string` | No | Filter by type | All types |

**Valid Chain Values**: `ethereum`, `base`, `arbitrum`, `polygon`, `optimism`, etc.  
**Valid Status Values**: `pending`, `success`, `failed`  
**Valid Type Values**: `send`, `swap`, `approve`, `fund`, etc.

#### Response

##### Success Response (200 OK)
```typescript
interface TransactionHistoryResponse {
  user_id: number;
  transactions: TransactionHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

interface TransactionHistoryItem {
  id: number;
  tx_hash: string | null;
  type: string;
  chain: string;
  status: string;
  to_address: string | null;
  asset_in: string | null;        // Input asset symbol
  amount_in: string | null;       // Input amount
  asset_out: string | null;       // Output asset symbol
  amount_out: string | null;      // Output amount
  fee_usd: string | null;         // Fee in USD
  block_number: number | null;    // Confirmation block
  confirmed_at: string | null;   // ISO 8601
  created_at: string;             // ISO 8601
  explorer_url: string | null;    // Block explorer URL
  gas_used: number | null;       // Gas units consumed
  gas_price: number | null;      // Gas price in wei
  is_incoming: boolean;          // True if user is receiver
  from_address: string | null;   // Sender address (for incoming)
}
```

**JSON Example**:
```json
{
  "user_id": 123,
  "transactions": [
    {
      "id": 1,
      "tx_hash": "0x1234...",
      "type": "send",
      "chain": "ethereum",
      "status": "success",
      "to_address": "0xabcd...",
      "asset_in": "ETH",
      "amount_in": "1.0",
      "asset_out": null,
      "amount_out": null,
      "fee_usd": "2.50",
      "block_number": 18500000,
      "confirmed_at": "2024-01-15T10:30:30Z",
      "created_at": "2024-01-15T10:30:00Z",
      "explorer_url": "https://etherscan.io/tx/0x1234...",
      "gas_used": 21000,
      "gas_price": 30000000000,
      "is_incoming": false,
      "from_address": null
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Note**: Transactions are returned in reverse chronological order (newest first).

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error: "Unable to load transaction history" + Retry |

#### Request

##### Request Body
```typescript
interface LogTransactionRequest {
  tx_hash: string;                // Required: Transaction hash (0x..., 66 chars)
  from_address: string;           // Required: Sender address
  to_address: string | null;      // Optional: Recipient address (null for contract creation)
  value: string;                  // Required: Amount in Wei (as string)
  chain_id: number;               // Required: Chain ID (1=Mainnet, 8453=Base, etc.)
  tx_type?: string;                // Optional: Default "send"
  asset_symbol?: string;          // Optional: Token symbol (ETH, USDC, etc.)
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
  status: string;                 // "pending", "confirmed", "failed"
  created_at: string;              // ISO 8601
}
```

**JSON Example**:
```json
{
  "transaction_id": "tx-123",
  "tx_hash": "0xabc123def456...",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValidationError` | Invalid transaction data | Show inline errors |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `409` | `ConflictError` | Transaction already logged | Ignore (idempotent) |
| `503` | `DataMapperError` | Service unavailable | Show error: "Failed to log transaction" |

---

## 🔌 NFT Endpoints

### 6. Get NFT Portfolio

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/portfolio/{address}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `address` | `string` | Yes | Wallet address (0x...) |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |
| `include_valuation` | `boolean` | No | Include floor price valuation | `true` |

#### Response

##### Success Response (200 OK)
```typescript
interface NFTPortfolioResponse {
  address: string;
  chain: string;
  nfts: NFTAsset[];
  total_count: number;
  collection_count: number;
  total_value_eth: string;
  total_value_usd: string;
  by_collection: CollectionValue[];
}

interface NFTAsset {
  token_id: string;
  contract_address: string;
  collection_slug: string;
  name: string;
  image_url: string;
  floor_price_eth?: string;
}

interface CollectionValue {
  slug: string;
  count: number;
  floor_price_eth: string;
  total_value_eth: string;
}
```

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `InvalidAddressError` | Invalid address format | Show error: "Invalid wallet address" |
| `429` | `RateLimitError` | Rate limit exceeded | Show error: "Rate limit exceeded. Please try again later." |
| `502` | `OpenSeaAPIError` | OpenSea API unavailable | Show error: "NFT service unavailable" + Retry |
| `500` | `NFTError` | Internal error | Show error + Retry |

---

### 7. Get Collection

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/collections/{slug}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `slug` | `string` | Yes | Collection slug (e.g., "boredapeyachtclub") |

#### Response

##### Success Response (200 OK)
```typescript
interface NFTCollectionResponse {
  slug: string;
  name: string;
  description: string;
  image_url: string;
  floor_price_eth: string;
  total_supply: number;
  owner_count: number;
}
```

---

### 8. Get Collection Stats

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/collections/{slug}/stats`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface CollectionStatsResponse {
  stats: {
    floor_price_eth: string;
    floor_price_usd: string;
    total_volume_eth: string;
    total_sales: number;
    owners: number;
    market_cap_eth: string;
  };
  market_sentiment: string;       // "bullish" | "bearish" | "neutral"
  floor_change_alert?: string;
}
```

---

### 9. Get NFT Details

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/assets/{contract_address}/{token_id}`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Path Parameters
| Parameter | Type | Required | Description |
|----------|------|----------|-------------|
| `contract_address` | `string` | Yes | NFT contract address |
| `token_id` | `string` | Yes | Token ID |

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `chain` | `string` | No | Blockchain | `ethereum` |

#### Response

##### Success Response (200 OK)
```typescript
interface NFTAssetResponse {
  token_id: string;
  contract_address: string;
  collection_slug: string;
  name: string;
  description: string;
  image_url: string;
  traits: NFTTrait[];
  last_sale_price_eth?: string;
  last_sale_date?: string;
}

interface NFTTrait {
  trait_type: string;
  value: string;
  rarity?: number;
}
```

---

### 10. Get Collection Listings

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/collections/{slug}/listings`  
**Auth Required**: Yes (Bearer Token)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |

#### Response

##### Success Response (200 OK)
```typescript
interface ListingsResponse {
  listings: NFTListing[];
  count: number;
  collection_slug: string;
}

interface NFTListing {
  token_id: string;
  price_eth: string;
  price_usd: string;
  seller_address: string;
  expiration_date: string;
}
```

---

### 11. Get Floor Price

**Method**: `GET`  
**Endpoint**: `/api/v1/opensea/collections/{slug}/floor`  
**Auth Required**: Yes (Bearer Token)

#### Response

##### Success Response (200 OK)
```typescript
interface FloorPriceResponse {
  collection_slug: string;
  floor_price_eth: string | null;
  floor_price_usd: string | null;
  last_updated: string;           // ISO 8601
}
```

---

## 🔌 Bitcoin Endpoints

> **⚠️ Note**: Bitcoin endpoints are currently **DISABLED** in the backend (`create_bitcoin_router()` is commented out in `api_v1_router.py`). The following documentation is provided for when Bitcoin support is re-enabled.

### 12. Log Bitcoin Transaction

**Method**: `POST`  
**Endpoint**: `/api/v1/user/bitcoin/transactions`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **DISABLED** (Not currently available)

#### Request

##### Request Body
```typescript
interface LogBitcoinTransactionRequest {
  tx_hash: string;                 // Required: Bitcoin transaction hash (64 hex chars)
  from_address: string;            // Required: Sender Bitcoin address
  to_address: string;              // Required: Recipient Bitcoin address
  amount_btc: string;              // Required: Amount in BTC (as string)
  fee_btc?: string;                // Optional: Transaction fee in BTC
  network?: string;                 // Optional: "bitcoin" | "bitcoin_testnet" (default: "bitcoin")
}
```

**Bitcoin Address Formats Supported**:
- Legacy (P2PKH): Starts with `1` or `m` (testnet)
- SegWit Compatible (P2SH): Starts with `3` or `2` (testnet)
- Native SegWit (Bech32): Starts with `bc1` or `tb1` (testnet)
- Taproot (Bech32m): Starts with `bc1p` (mainnet)

#### Response

##### Success Response (201 Created)
```typescript
interface LogBitcoinTransactionResponse {
  id: number;
  tx_hash: string;
  status: string;                  // "pending" | "success" | "failed"
  chain: string;                   // "bitcoin" | "bitcoin_testnet"
  from_address: string;
  to_address: string;
  amount_btc: string;
  created_at: string;              // ISO 8601
  explorer_url?: string;          // Mempool.space URL
}
```

---

### 13. Get Bitcoin Transaction History

**Method**: `GET`  
**Endpoint**: `/api/v1/user/bitcoin/transactions`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **DISABLED** (Not currently available)

#### Request

##### Query Parameters
| Parameter | Type | Required | Description | Default |
|----------|------|----------|-------------|---------|
| `limit` | `number` | No | Max results | `50` |
| `offset` | `number` | No | Pagination offset | `0` |
| `network` | `string` | No | Filter by network | All networks |
| `status` | `string` | No | Filter by status | All statuses |

#### Response

##### Success Response (200 OK)
```typescript
interface BitcoinTransactionHistoryResponse {
  user_id: number;
  transactions: BitcoinTransactionHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

interface BitcoinTransactionHistoryItem {
  id: number;
  tx_hash: string | null;
  chain: string;
  status: string;
  from_address: string | null;
  to_address: string | null;
  amount_btc: string | null;
  fee_btc: string | null;
  confirmed_at: string | null;   // ISO 8601
  created_at: string;             // ISO 8601
  explorer_url: string | null;
  is_incoming: boolean;
}
```

---

### 14. Create Bitcoin Wallet

**Method**: `POST`  
**Endpoint**: `/api/v1/user/bitcoin/wallets/create`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **DISABLED** (Not currently available)

#### Request

No request body required. Bitcoin wallets are created server-side via Privy API.

#### Response

##### Success Response (201 Created)
```typescript
interface CreateBitcoinWalletResponse {
  wallet_id: string;
  address: string;                  // Bitcoin SegWit address
  chain: string;                    // "bitcoin" | "bitcoin_testnet"
  privy_wallet_id: string;         // Privy wallet ID
  created_at: string;               // ISO 8601
}
```

**Note**: If user already has a Bitcoin wallet, returns the existing one.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `400` | `ValueError` | Invalid request | Show error: "Invalid request" |
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

### 15. Get My Bitcoin Wallet

**Method**: `GET`  
**Endpoint**: `/api/v1/user/bitcoin/wallets/me`  
**Auth Required**: Yes (Bearer Token)  
**Status**: ⚠️ **DISABLED** (Not currently available)

#### Response

##### Success Response (200 OK)
```typescript
interface GetBitcoinWalletResponse {
  exists: boolean;
  wallet?: {
    wallet_id: string;
    address: string;
    chain: string;
    privy_wallet_id: string;
    created_at: string;             // ISO 8601
  };
}
```

**Note**: Returns `exists: false` if user hasn't created a Bitcoin wallet yet.

##### Error Responses

| Status | Error Code | Description | UI Behavior |
|--------|------------|-------------|-------------|
| `401` | `AuthenticationError` | Invalid token | Redirect to login |
| `503` | `DataMapperError` | Service unavailable | Show error + Retry |

---

## 🔌 WebSocket Connections

### Asset Management WebSocket

**Status**: ⚠️ **Not Applicable**

The Asset Management module does not use WebSocket connections. All communication is via REST API:
- Wallet operations (GET, POST)
- Transaction logging (POST, GET)
- NFT portfolio (GET)
- Bitcoin operations (POST, GET)

**Note**: Real-time updates for transactions and portfolio changes are handled via polling or through the Dashboard WebSocket (`/api/v1/ws/graph`) for portfolio value updates.

---

## 🎯 API Design Trade-off Analysis (CTO Methodology)

### Key Design Decisions

| Decision | Alternative | Trade-off | Rationale |
|----------|------------|-----------|-----------|
| **Wallet Export with Encryption** | Plain text export | Security vs. Convenience | Encrypted export protects private keys, but requires password management |
| **Multi-Wallet Support** | Single wallet | Flexibility vs. Complexity | Multiple wallets enable diverse portfolios, but add management complexity |
| **NFT Portfolio Aggregation** | Per-collection queries | Performance vs. Accuracy | Aggregated portfolio reduces API calls, but may have stale data |
| **Transaction History Pagination** | Load all | Performance vs. Completeness | Pagination enables large histories, but requires client-side state management |
| **Bitcoin Module Disabled** | Full BTC support | Focus vs. Coverage | Disabling Bitcoin focuses on EVM chains, but limits user base |

### Risk Assessment

**Cognitive Limitations:**
- Wallet export security depends on user password strength
- Multi-wallet management may confuse users
- NFT valuation may be inaccurate if floor prices change rapidly

**Technical Debt:**
- Wallet encryption/decryption adds processing overhead
- NFT data synchronization requires external API reliability
- Transaction history queries may become slow with large datasets

**Validation Strategy:**
- ✅ Monitor wallet export operations (security audit)
- ✅ Track NFT API response times and error rates
- ✅ Alert on wallet operation failures
- ✅ Validate transaction history query performance
- ✅ Monitor external NFT API availability

---

## 📊 Error Handling Summary

### Common Error Patterns

1. **Authentication Errors (401)**
   - Invalid or expired token
   - **Action**: Refresh token, if fails → redirect to login

2. **Validation Errors (400)**
   - Invalid request data
   - **Action**: Show inline field errors

3. **Forbidden Errors (403)**
   - User doesn't own the wallet
   - **Action**: Show error message, prevent action

4. **Not Found Errors (404)**
   - Wallet or transaction not found
   - **Action**: Show error message

5. **Service Unavailable (503)**
   - Database or external service down
   - **Action**: Show error message + Retry button

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

---

## 🔗 Related Documentation

- **Backend Controller**: `src/app/presentation/http/controllers/wallet/my_wallets.py`
- **Backend Controller**: `src/app/presentation/http/controllers/wallet/export_wallet.py`
- **Backend Controller**: `src/app/presentation/http/controllers/transaction/router.py`
- **Domain Entities**: `src/app/domain/entities/wallet.py`
- **Application Interactors**: `src/app/application/commands/wallet/export_wallet.py`
- **Frontend Implementation**: `03-Asset-Management/IMPLEMENTATION.md`

---

**Last Updated**: 2024-01-01  
**API Version**: v1  
**Status**: Production Ready
