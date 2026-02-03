# Wallets & Transactions - API Endpoints Documentation

**Last Updated**: 2026-01-26
**Module**: Wallets & Transactions
**Tech Stack**: FastAPI 0.116.1, Dishka 1.6.0, Pydantic 2.11.7

---

## Table of Contents

1. [Guest Endpoints](#guest-endpoints)
2. [User Endpoints](#user-endpoints)
   - [My Wallets](#my-wallets)
   - [Export Wallet](#export-wallet)
   - [Complete Swap](#complete-swap)
   - [Transaction Logging](#transaction-logging)
   - [Transaction History](#transaction-history)
3. [Admin Endpoints](#admin-endpoints)
   - [List Wallets](#list-wallets)
   - [Get Wallet Details](#get-wallet-details)
   - [Update Wallet](#update-wallet)
   - [Admin Transaction History](#admin-transaction-history)
4. [Error Responses](#error-responses)
5. [Integration Patterns](#integration-patterns)

---

## Guest Endpoints

Currently, there are **NO guest-accessible wallet or transaction endpoints**. All wallet and transaction operations require authentication.

**Rationale**: Wallets and transactions contain sensitive financial data that must be protected. Guest users can interact with chat features that may trigger wallet operations, but actual wallet access requires authentication.

---

## User Endpoints

### My Wallets

#### GET /api/v1/wallet/me

**Purpose**: Retrieve all wallets associated with the authenticated user from both local database and Privy API.

**Access Level**: Authenticated users (JWT required)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/wallet/my_wallets.py` (lines 127-182)
- **Handler**: `GetMyWalletsHandler` in `/src/app/infrastructure/auth/handlers/wallet_me.py` (lines 83-326)
- **Router**: `/src/app/presentation/http/controllers/wallet/router.py` (lines 15-38)

**Request Schema**:
```http
GET /api/v1/wallet/me HTTP/1.1
Authorization: Bearer <jwt_token>
```

**Response Schema** (`200 OK`):
```json
{
  "user_id": 123,
  "privy_user_id": "did:privy:abc123xyz",
  "wallets": [
    {
      "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "is_primary": true,
      "source": "privy",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "wallet_id": "imported:0xabcdef...",
      "address": "0xabcdef1234567890abcdef1234567890abcdef12",
      "chain_type": "ethereum",
      "wallet_type": "imported",
      "is_primary": false,
      "source": "local",
      "created_at": "2024-02-10T14:22:00Z"
    }
  ],
  "primary_wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "privy_connected": true,
  "message": null
}
```

**Response Fields**:
- `user_id`: Local database user ID
- `privy_user_id`: Privy DID (Decentralized Identifier)
- `wallets`: Array of wallet objects
  - `wallet_id`: Unique identifier (Privy wallet ID or synthetic for imported)
  - `address`: Blockchain address (0x... format)
  - `chain_type`: Blockchain network (ethereum, polygon, base, etc.)
  - `wallet_type`: `embedded` (Privy), `external` (MetaMask), `imported` (via private key)
  - `is_primary`: Whether this is the user's primary wallet
  - `source`: Data source - `privy` (live API), `local` (database cache), `both`
  - `created_at`: ISO 8601 timestamp
- `primary_wallet_address`: Address of the primary wallet
- `privy_connected`: Whether Privy API fetch succeeded
- `message`: Optional status message (e.g., if Privy unavailable)

**Business Logic**:

1. **Three-Source Aggregation**:
   - **Privy API**: Live wallet data for embedded and linked wallets
   - **Local DB (Imported)**: User-imported wallets (stored with `provider=IMPORTED`)
   - **Local DB (Cached Privy)**: Cached Privy wallets for offline capability

2. **Wallet Source Modes** (configured via `WALLETS_SOURCE_MODE` in `config/local/config.toml`):
   - `privy`: Prefer Privy API, use DB as cache/analytics store
   - `hybrid`: Use Privy when available, always persist to DB
   - `local`: DB-only mode for offline environments (no Privy calls)

3. **Deduplication**: Wallets are deduplicated by address (case-insensitive)

4. **Fallback Handling**: If Privy fetch fails, returns local data with warning message

5. **Primary Wallet Priority**: Primary wallet is always sorted first

**Handler Flow** (lines 129-326 in `wallet_me.py`):
```python
async def execute(self) -> WalletsResponse:
    # 1. Get current user
    user = await self._current_user_service.get_current_user()

    # 2. Fetch from Privy API (if not in local mode)
    if privy_user_id and self.should_call_privy:
        privy_wallets = await self._wallet_provider.list_user_wallets(privy_user_id)
        # In hybrid mode, persist to local DB
        if self.should_persist_to_db:
            await self._wallet_repository.upsert(...)

    # 3. Fetch imported wallets from local DB
    local_imported_wallets = await self._wallet_repository.get_by_user_and_provider(
        user_id, WalletProvider.IMPORTED
    )

    # 4. Fetch cached Privy wallets from DB (offline mode)
    if self.is_offline_mode or not privy_connected:
        local_privy_wallets = await self._wallet_repository.get_by_user_and_provider(
            user_id, WalletProvider.PRIVY
        )

    # 5. Deduplicate and sort (primary first)
    wallets.sort(key=lambda w: (not w.is_primary, w.address))

    return WalletsResponse(...)
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```bash
curl -X GET "https://api.anvil.com/api/v1/wallet/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

#### POST /api/v1/wallet/sync

**Purpose**: Sync the list of connected wallets from the frontend (Privy SDK) to the backend database.

**Access Level**: Authenticated users (JWT required)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/wallet/my_wallets.py` (lines 184-264)
- **Handler**: `SyncWalletsHandler` in `/src/app/infrastructure/auth/handlers/wallet_me.py` (lines 329-458)

**Request Schema**:
```json
{
  "wallets": [
    {
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "chain_type": "ethereum",
      "wallet_type": "embedded",
      "privy_wallet_id": "g1644aqvat8qxkfqsfzvpuq0"
    },
    {
      "address": "0xabcdef1234567890abcdef1234567890abcdef12",
      "chain_type": "polygon",
      "wallet_type": "imported",
      "privy_wallet_id": null
    }
  ]
}
```

**Legacy Format** (deprecated but still supported):
```json
{
  "wallet_addresses": [
    "0x1234567890abcdef1234567890abcdef12345678",
    "0xabcdef1234567890abcdef1234567890abcdef12"
  ]
}
```

**Request Fields**:
- `wallets` (preferred): Array of wallet objects with metadata
  - `address` (required): Wallet blockchain address
  - `chain_type` (optional, default: "ethereum"): Blockchain network
  - `wallet_type` (optional, default: "unknown"): Type of wallet
  - `privy_wallet_id` (optional): Privy wallet ID if available
- `wallet_addresses` (legacy): Array of wallet address strings

**Response Schema** (`200 OK`): Same as `GET /wallet/me`

**Business Logic**:

1. **Imported Wallet Persistence**: Wallets with `wallet_type=imported` are persisted to the local database with `provider=IMPORTED`

2. **Wallet ID Generation**:
   - Uses `privy_wallet_id` if provided
   - For imported wallets: generates synthetic ID `imported:<address>`
   - Otherwise: generates temporary ID `synced_<index>`

3. **Primary Wallet Detection**: First wallet in list is marked as primary if user has no primary wallet set

4. **Database Upsert**: Imported wallets are upserted (insert or update) to prevent duplicates

**Handler Flow** (lines 351-458 in `wallet_me.py`):
```python
async def execute(self, wallet_data: list[dict]) -> WalletsResponse:
    user = await self._current_user_service.get_current_user()

    for wallet_info in wallet_data:
        address = wallet_info["address"]
        wallet_type = wallet_info.get("wallet_type", "unknown")

        # Persist imported wallets to database
        if wallet_type == "imported":
            await self._wallet_repository.upsert(
                user_id=user_id,
                address=address,
                provider=WalletProvider.IMPORTED,
                privy_wallet_id=wallet_info.get("privy_wallet_id"),
                chain_type=wallet_info.get("chain_type", "ethereum")
            )

    return WalletsResponse(...)
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `503 Service Unavailable`: Database persistence failure

**Example Usage**:
```javascript
// Frontend (React + Privy SDK)
const { wallets } = useWallets();

await fetch('/api/v1/wallet/sync', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    wallets: wallets.map(w => ({
      address: w.address,
      chain_type: w.chainType,
      wallet_type: w.walletType,
      privy_wallet_id: w.id
    }))
  })
});
```

---

### Export Wallet

#### POST /api/v1/wallet/export

**Purpose**: Export the private key of an embedded wallet via Privy API. Uses HPKE (Hybrid Public Key Encryption) for secure key transfer.

**Access Level**: Authenticated users (JWT required)

**Security**: Only the wallet owner can export. Private keys are NEVER logged or persisted.

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/wallet/export_wallet.py` (lines 76-200)
- **Command**: `ExportWallet` in `/src/app/application/commands/wallet/export_wallet.py` (lines 41-140)
- **Privy Integration**: `/src/app/infrastructure/privy/client.py` and `/src/app/infrastructure/privy/hpke.py`

**Request Schema**:
```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "wallet_address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7"
}
```

**Request Fields**:
- `wallet_id` (required): The Privy wallet ID to export
- `wallet_address` (optional): Wallet address for verification

**Response Schema** (`200 OK`):
```json
{
  "wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "address": "0x19BFe2684Aedcbd57454bA80440C24a412CE04C7",
  "private_key": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "chain_type": "ethereum"
}
```

**Response Fields**:
- `wallet_id`: The Privy wallet ID
- `address`: Blockchain address
- `private_key`: **SENSITIVE** - Decrypted private key (hex-encoded)
- `chain_type`: Blockchain type

**Business Logic**:

1. **Authorization Verification**:
   - Validates user is authenticated
   - Verifies user has a linked Privy account
   - Fetches all user wallets from Privy
   - Confirms the requested wallet belongs to the user

2. **HPKE Encryption Flow**:
   - Generates ephemeral HPKE key pair on server
   - Sends public key to Privy API
   - Privy encrypts private key with public key
   - Server decrypts with private key
   - Returns decrypted private key to user

3. **Audit Trail**: Records `exported_at` timestamp in local database (best-effort)

**Security Considerations**:

⚠️ **CRITICAL SECURITY MEASURES**:
- Private keys are NEVER logged (even at DEBUG level)
- Private keys are NEVER persisted to database
- HPKE ensures end-to-end encryption during transfer
- Only wallet owner can export (verified via Privy API)
- Frontend should immediately encrypt/secure the private key after receiving it

**Controller Flow** (lines 95-200 in `export_wallet.py`):
```python
async def export_wallet(
    request: ExportWalletRequest,
    export_wallet_cmd: FromDishka[ExportWallet],
    current_user_service: FromDishka[CurrentUserService],
    wallet_provider: FromDishka[EmbeddedWalletProviderPort],
    wallet_repository: FromDishka[WalletRepository],
) -> ExportWalletResponse:
    # Step 1: Get authenticated user
    user = await current_user_service.get_current_user()
    privy_user_id = user.privy_user_id.value

    # Step 2: Verify wallet belongs to user
    user_wallets = await wallet_provider.list_user_wallets(privy_user_id)
    user_wallet_ids = {w.wallet_id for w in user_wallets}

    if request.wallet_id not in user_wallet_ids:
        raise HTTPException(403, "Wallet does not belong to authenticated user")

    # Step 3: Export via Privy + HPKE
    result = await export_wallet_cmd.execute(
        wallet_id=request.wallet_id,
        wallet_address=request.wallet_address
    )

    # Step 4: Record export timestamp (audit trail)
    await wallet_repository.mark_exported(request.wallet_id)

    return ExportWalletResponse.from_result(result)
```

**Command Flow** (lines 62-140 in `export_wallet.py`):
```python
async def execute(self, wallet_id: str, wallet_address: str | None) -> ExportWalletResult:
    # 1. Generate HPKE key pair
    decryptor = HPKEDecryptor()
    key_pair = decryptor.get_or_create_key_pair()

    # 2. Get wallet info from Privy (verification)
    wallet_info = await self._privy_client.get_wallet(wallet_id)
    actual_address = wallet_info["address"]

    if wallet_address and actual_address.lower() != wallet_address.lower():
        raise WalletExportError("Address mismatch")

    # 3. Call Privy API to export (encrypted)
    export_response = await self._privy_client.export_wallet(
        wallet_id=wallet_id,
        recipient_public_key_b64=key_pair.public_key_b64
    )

    # 4. Decrypt private key (NEVER logged)
    private_key = decryptor.decrypt(
        ciphertext_b64=export_response.ciphertext,
        encapsulated_key_b64=export_response.encapsulated_key
    )

    return ExportWalletResult(
        wallet_id=wallet_id,
        address=actual_address,
        private_key=private_key,
        chain_type=chain_type
    )
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`:
  - User does not have a linked Privy account
  - Wallet does not belong to the authenticated user
  - Privy account not found (deleted from Privy)
- `404 Not Found`: Wallet not found in Privy
- `500 Internal Server Error`:
  - Failed to verify wallet ownership
  - Privy API error
  - HPKE decryption failure

**Example Usage**:
```javascript
// Frontend (React + Privy SDK)
const exportWallet = async (walletId) => {
  const response = await fetch('/api/v1/wallet/export', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      wallet_id: walletId,
      wallet_address: '0x19BFe2684Aedcbd57454bA80440C24a412CE04C7'
    })
  });

  const { private_key } = await response.json();

  // IMPORTANT: Immediately secure the private key
  // - Display to user for copying
  // - Encrypt for storage
  // - Clear from memory after use
  return private_key;
};
```

---

### Complete Swap

#### POST /api/v1/wallet/swaps/complete

**Purpose**: Save a completed swap transaction to the database after successful execution via Privy + 0x Protocol.

**Access Level**: Authenticated users (JWT required)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/wallet/complete_swap.py` (lines 94-243)
- **Command Handler**: `SaveSwapTransactionHandler` in `/src/app/application/commands/wallet/save_swap_transaction.py` (lines 51-177)
- **Domain**: `Transaction` entity in `/src/app/domain/transactions/entities/transaction.py`

**Request Schema**:
```json
{
  "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "chain": "base",
  "from_token": "ETH",
  "to_token": "USDC",
  "from_amount": "0.9",
  "to_amount": "3000.00",
  "exchange_rate": "3333.33",
  "gas_fee_usd": "0.99",
  "slippage": "1.0",
  "conversation_id": "conv_abc123"
}
```

**Request Fields**:
- `tx_hash` (required): Transaction hash (0x... format, 66 chars)
- `chain` (required): Chain name (base, ethereum, polygon, arbitrum, optimism)
- `from_token` (required): Source token symbol (ETH, USDC, WETH, etc.)
- `to_token` (required): Destination token symbol
- `from_amount` (required): Amount swapped (in token units as string)
- `to_amount` (required): Amount received (in token units as string)
- `exchange_rate` (optional): Exchange rate (to_amount / from_amount)
- `gas_fee_usd` (optional): Gas fee in USD
- `slippage` (optional): Slippage percentage
- `conversation_id` (optional): Chat conversation ID (for context)

**Response Schema** (`201 Created`):
```json
{
  "success": true,
  "transaction_id": 42,
  "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "message": "Swap transaction saved successfully"
}
```

**Response Fields**:
- `success`: Boolean indicating success
- `transaction_id`: Database transaction ID
- `tx_hash`: Transaction hash (echoed back)
- `message`: Success message

**Business Logic**:

1. **Amount Validation**: Validates that `from_amount` and `to_amount` are positive decimals

2. **Chain Mapping**: Maps chain name to `ChainType` enum:
   - `ethereum` → ChainType.ETHEREUM
   - `base` → ChainType.BASE
   - `polygon` → ChainType.POLYGON
   - `arbitrum` → ChainType.ARBITRUM
   - `optimism` → ChainType.OPTIMISM
   - Default: ChainType.BASE

3. **Transaction Creation**:
   - Type: `TransactionType.SWAP`
   - Status: `TransactionStatus.SUCCESS` (swap already completed on-chain)
   - DEX Aggregator: "0x" (0x Protocol)
   - Metadata: Includes `conversation_id` and `exchange_rate`

4. **Wallet Resolution**: `wallet_id` is set to 0 temporarily and resolved by repository based on user

5. **Persistence**: Saves to `transactions` table via `TransactionRepository`

**Handler Flow** (lines 64-177 in `save_swap_transaction.py`):
```python
async def handle(self, command: SaveSwapTransactionCommand) -> SaveSwapTransactionResult:
    # 1. Validate amounts
    from_amount_decimal = Decimal(command.from_amount)
    to_amount_decimal = Decimal(command.to_amount)

    if from_amount_decimal <= 0 or to_amount_decimal <= 0:
        raise ValueError("Amounts must be positive")

    # 2. Parse chain
    chain = ChainType[command.chain.upper()]

    # 3. Build transaction metadata
    metadata = {
        "conversation_id": command.conversation_id,
        "exchange_rate": command.exchange_rate
    }

    # 4. Create transaction entity
    transaction = Transaction(
        id_=TransactionId(0),
        user_id=UserId(command.user_id),
        wallet_id=WalletId(0),  # Resolved by repository
        to_address=None,  # Not applicable for swaps
        type=TransactionType.SWAP,
        chain=chain,
        asset_in=command.from_token,
        amount_in=from_amount_decimal,
        asset_out=command.to_token,
        amount_out=to_amount_decimal,
        fee_usd=Decimal(command.gas_fee_usd) if command.gas_fee_usd else None,
        tx_hash=command.tx_hash,
        status=TransactionStatus.SUCCESS,
        dex_aggregator="0x",
        slippage=Decimal(command.slippage) if command.slippage else None,
        tx_metadata=metadata,
        created_at=CreatedAt.now()
    )

    # 5. Save to repository
    saved_transaction = await self._transaction_repository.save(transaction)

    return SaveSwapTransactionResult(
        transaction_id=saved_transaction.id_.value,
        tx_hash=saved_transaction.tx_hash
    )
```

**Error Responses**:
- `400 Bad Request`:
  - Invalid amounts (non-positive)
  - Invalid decimal format
  - Invalid chain name
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Database save failure

**Example Usage**:
```javascript
// Frontend (React + Privy + 0x)
const completeSwap = async (swapData) => {
  // 1. Execute swap via Privy + 0x
  const txHash = await privyProvider.sendTransaction(...);

  // 2. Wait for confirmation
  const receipt = await privyProvider.waitForTransaction(txHash);

  // 3. Save to backend database
  const response = await fetch('/api/v1/wallet/swaps/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tx_hash: txHash,
      chain: 'base',
      from_token: 'ETH',
      to_token: 'USDC',
      from_amount: '0.9',
      to_amount: '3000.00',
      exchange_rate: '3333.33',
      gas_fee_usd: receipt.gasUsed * receipt.gasPrice / 1e18 * ethPrice,
      slippage: '1.0',
      conversation_id: conversationId
    })
  });

  const { transaction_id } = await response.json();
  console.log('Swap saved with ID:', transaction_id);
};
```

---

### Transaction Logging

#### POST /api/v1/user/transactions

**Purpose**: Log a transaction sent from the frontend via Privy for history and auditing.

**Access Level**: Authenticated users (JWT required)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/transaction/router.py` (lines 194-258)
- **Handler**: `LogTransactionHandler` in `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 104-391)
- **Domain**: `Transaction` entity in `/src/app/domain/transactions/entities/transaction.py`

**Request Schema**:
```json
{
  "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "from_address": "0x1234567890abcdef1234567890abcdef12345678",
  "to_address": "0xabcdef1234567890abcdef1234567890abcdef12",
  "value": "1000000000000000000",
  "chain_id": 8453,
  "tx_type": "send",
  "asset_symbol": "ETH",
  "data": "0x"
}
```

**Request Fields**:
- `tx_hash` (required): Transaction hash (66 characters, 0x prefix)
- `from_address` (required): Sender wallet address (42 characters, 0x prefix)
- `to_address` (optional): Recipient address (null for contract creation)
- `value` (required): Transaction value in wei (string to preserve precision)
- `chain_id` (required): Blockchain chain ID (1=Ethereum, 8453=Base, 42161=Arbitrum, etc.)
- `tx_type` (optional, default: "send"): Transaction type (send, swap, approve, fund, etc.)
- `asset_symbol` (optional): Asset symbol being transferred (ETH, USDC, WETH, etc.)
- `data` (optional): Transaction data for contract calls

**Response Schema** (`201 Created`):
```json
{
  "id": 123,
  "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "status": "pending",
  "chain": "base",
  "tx_type": "send",
  "from_address": "0x1234567890abcdef1234567890abcdef12345678",
  "to_address": "0xabcdef1234567890abcdef1234567890abcdef12",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response Fields**:
- `id`: Database transaction ID
- `tx_hash`: Transaction hash (echoed)
- `status`: Initial status (always "pending")
- `chain`: Blockchain name (ethereum, base, arbitrum, etc.)
- `tx_type`: Transaction type
- `from_address`: Sender address
- `to_address`: Recipient address
- `created_at`: ISO 8601 timestamp

**Business Logic**:

1. **Duplicate Detection**: Checks if transaction already exists for the user (by `user_id` + `tx_hash`)

2. **Wallet Lookup**: Finds the wallet by address and user_id
   - First tries exact match: `user_id` + `from_address`
   - Falls back to address-only lookup
   - Raises error if wallet not found (user should sync wallets first)

3. **Chain ID Mapping**:
   ```python
   CHAIN_ID_MAP = {
       1: ChainType.ETHEREUM,
       10: ChainType.OPTIMISM,
       137: ChainType.POLYGON,
       8453: ChainType.BASE,
       42161: ChainType.ARBITRUM,
       11155111: ChainType.ETHEREUM,  # Sepolia testnet
       84532: ChainType.BASE,  # Base Sepolia
       0: ChainType.BITCOIN,  # Bitcoin mainnet
       -1: ChainType.BITCOIN_TESTNET
   }
   ```

4. **Transaction Type Mapping**:
   ```python
   TX_TYPE_MAP = {
       "send": TransactionType.SEND,
       "transfer": TransactionType.SEND,
       "swap": TransactionType.SWAP,
       "approve": TransactionType.APPROVE,
       "fund": TransactionType.FUND,
       "earn": TransactionType.EARN,
       "contract_call": TransactionType.CONTRACT_CALL
   }
   ```

5. **Value Conversion**: Converts Wei to ETH (divides by 10^18) for database storage

6. **Dual Transaction Logging**:
   - **Sender's Transaction**: Always created
   - **Receiver's Transaction**: Created if recipient is a registered user
   - Same `tx_hash` appears in both sender's and receiver's history
   - Receiver's transaction has `is_incoming=true` in metadata

**Handler Flow** (lines 122-280 in `transaction_log.py`):
```python
async def execute(self, input_data: LogTransactionInput) -> LogTransactionResult:
    user = await self._current_user_service.get_current_user()
    user_id = UserId(user.id_.value)

    # 1. Check for duplicates (for this user)
    existing = await self._transaction_repository.get_by_user_and_tx_hash(
        user_id=user_id,
        tx_hash=input_data.tx_hash
    )
    if existing:
        return LogTransactionResult(...)  # Return existing

    # 2. Find wallet by address and user
    wallet = await self._wallet_repository.get_by_user_and_address(
        user_id=user_id,
        address=input_data.from_address
    )

    if not wallet:
        raise WalletNotFoundForTransactionError("Please sync your wallets first")

    # 3. Map chain ID and transaction type
    chain = CHAIN_ID_MAP.get(input_data.chain_id, ChainType.ETHEREUM)
    tx_type = TX_TYPE_MAP.get(input_data.tx_type.lower(), TransactionType.SEND)

    # 4. Convert Wei to ETH
    wei_value = Decimal(input_data.value)
    amount_in = wei_value / Decimal("1000000000000000000")

    # 5. Create sender's transaction
    transaction = Transaction(
        id_=TransactionId(0),
        user_id=user_id,
        wallet_id=wallet.id_,
        to_address=input_data.to_address.lower() if input_data.to_address else None,
        type=tx_type,
        chain=chain,
        asset_in=input_data.asset_symbol or "ETH",
        amount_in=amount_in,
        tx_hash=input_data.tx_hash.lower(),
        status=TransactionStatus.PENDING,
        created_at=CreatedAt(datetime.now(UTC))
    )

    saved_tx = await self._transaction_repository.save(transaction)

    # 6. Also log for receiver (if registered user)
    await self._log_receiver_transaction(...)

    return LogTransactionResult(...)
```

**Receiver Transaction Logic** (lines 281-391 in `transaction_log.py`):
```python
async def _log_receiver_transaction(
    self, *, input_data, sender_user_id, to_address, chain, tx_type, amount_in
):
    if not to_address:
        return  # Skip if no recipient

    # Look up receiver's wallet
    receiver_wallet = await self._wallet_repository.get_by_address(to_address)

    if not receiver_wallet:
        return  # Receiver is not a registered user

    receiver_user_id = receiver_wallet.user_id

    # Don't create duplicate if sender == receiver
    if receiver_user_id.value == sender_user_id.value:
        return

    # Check if receiver already has this transaction
    existing_receiver_tx = await self._transaction_repository.get_by_user_and_tx_hash(
        user_id=receiver_user_id,
        tx_hash=input_data.tx_hash
    )
    if existing_receiver_tx:
        return

    # Create receiver's transaction
    receiver_tx = Transaction(
        id_=TransactionId(0),
        user_id=receiver_user_id,
        wallet_id=receiver_wallet.id_,
        to_address=to_address,
        type=tx_type,
        chain=chain,
        asset_in=input_data.asset_symbol or "ETH",
        amount_in=amount_in,
        tx_hash=input_data.tx_hash.lower(),
        status=TransactionStatus.PENDING,
        tx_metadata={
            "receiver_view": True,
            "from_address": input_data.from_address.lower()
        },
        created_at=CreatedAt(datetime.now(UTC))
    )

    await self._transaction_repository.save(receiver_tx)
```

**Error Responses**:
- `400 Bad Request`: Wallet not found for transaction sender (user should sync wallets)
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Database save failure
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```javascript
// Frontend (React + Privy SDK)
const sendTransaction = async (to, value) => {
  // 1. Send transaction via Privy
  const txHash = await privyProvider.sendTransaction({
    to: to,
    value: ethers.utils.parseEther(value)
  });

  // 2. Log transaction to backend
  await fetch('/api/v1/user/transactions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tx_hash: txHash,
      from_address: currentWalletAddress,
      to_address: to,
      value: ethers.utils.parseEther(value).toString(),
      chain_id: 8453,  // Base
      tx_type: 'send',
      asset_symbol: 'ETH',
      data: '0x'
    })
  });

  console.log('Transaction logged:', txHash);
};
```

---

### Transaction History

#### GET /api/v1/user/transactions

**Purpose**: Retrieve transaction history for the authenticated user with filtering and pagination.

**Access Level**: Authenticated users (JWT required)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/transaction/router.py` (lines 260-350)
- **Handler**: `GetTransactionHistoryHandler` in `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 454-575)
- **Repository**: `SqlaTransactionRepository` in `/src/app/infrastructure/adapters/transaction_repository_sqla.py`

**Request Schema**:
```http
GET /api/v1/user/transactions?limit=50&offset=0&chain=base&status=success&tx_type=swap HTTP/1.1
Authorization: Bearer <jwt_token>
```

**Query Parameters**:
- `limit` (optional, default: 50, range: 1-100): Maximum number of results
- `offset` (optional, default: 0, min: 0): Number of results to skip
- `chain` (optional): Filter by chain (ethereum, base, arbitrum, polygon, optimism)
- `status` (optional): Filter by status (pending, success, failed)
- `tx_type` (optional): Filter by type (send, swap, approve, fund, earn)

**Response Schema** (`200 OK`):
```json
{
  "user_id": 123,
  "transactions": [
    {
      "id": 1,
      "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "type": "swap",
      "chain": "base",
      "status": "success",
      "to_address": null,
      "asset_in": "ETH",
      "amount_in": "0.9",
      "asset_out": "USDC",
      "amount_out": "3000.00",
      "fee_usd": "0.99",
      "block_number": 18500000,
      "confirmed_at": "2024-01-15T10:30:30Z",
      "created_at": "2024-01-15T10:30:00Z",
      "explorer_url": "https://basescan.org/tx/0x1234...",
      "gas_used": 21000,
      "gas_price": 30000000000,
      "is_incoming": false,
      "from_address": null
    },
    {
      "id": 2,
      "tx_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
      "type": "send",
      "chain": "ethereum",
      "status": "pending",
      "to_address": "0xabcdef1234567890abcdef1234567890abcdef12",
      "asset_in": "ETH",
      "amount_in": "1.0",
      "asset_out": null,
      "amount_out": null,
      "fee_usd": "2.50",
      "block_number": null,
      "confirmed_at": null,
      "created_at": "2024-01-15T09:00:00Z",
      "explorer_url": "https://etherscan.io/tx/0xabcd...",
      "gas_used": null,
      "gas_price": null,
      "is_incoming": false,
      "from_address": null
    },
    {
      "id": 3,
      "tx_hash": "0x9876543210fedcba9876543210fedcba9876543210fedcba9876543210fedcba",
      "type": "send",
      "chain": "base",
      "status": "success",
      "to_address": "0x1234567890abcdef1234567890abcdef12345678",
      "asset_in": "USDC",
      "amount_in": "500.00",
      "asset_out": null,
      "amount_out": null,
      "fee_usd": "0.15",
      "block_number": 18499000,
      "confirmed_at": "2024-01-14T15:20:10Z",
      "created_at": "2024-01-14T15:20:00Z",
      "explorer_url": "https://basescan.org/tx/0x9876...",
      "gas_used": 21000,
      "gas_price": 20000000000,
      "is_incoming": true,
      "from_address": "0xsender123456789abcdef1234567890abcdef1234"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

**Response Fields**:

**Top-Level**:
- `user_id`: User ID
- `transactions`: Array of transaction objects
- `total`: Total matching transactions (for pagination)
- `limit`: Page size used
- `offset`: Page offset used

**Transaction Object**:
- `id`: Database transaction ID
- `tx_hash`: Blockchain transaction hash
- `type`: Transaction type (send, swap, approve, fund, etc.)
- `chain`: Blockchain name
- `status`: Transaction status (pending, success, failed)
- `to_address`: Recipient address (null for swaps/contract creation)
- `asset_in`: Input asset symbol
- `amount_in`: Input amount (in token units)
- `asset_out`: Output asset symbol (for swaps)
- `amount_out`: Output amount (for swaps)
- `fee_usd`: Fee in USD
- `block_number`: Block number where confirmed
- `confirmed_at`: Confirmation timestamp (ISO 8601)
- `created_at`: Creation timestamp (ISO 8601)
- `explorer_url`: Block explorer URL
- `gas_used`: Gas units consumed
- `gas_price`: Gas price in wei
- `is_incoming`: `true` if user is the receiver (incoming transaction)
- `from_address`: Sender address (only for incoming transactions)

**Block Explorer URLs**:
```python
EXPLORER_URLS = {
    ChainType.ETHEREUM: "https://etherscan.io/tx/{tx_hash}",
    ChainType.ARBITRUM: "https://arbiscan.io/tx/{tx_hash}",
    ChainType.BASE: "https://basescan.org/tx/{tx_hash}",
    ChainType.POLYGON: "https://polygonscan.com/tx/{tx_hash}",
    ChainType.OPTIMISM: "https://optimistic.etherscan.io/tx/{tx_hash}",
    ChainType.BITCOIN: "https://mempool.space/tx/{tx_hash}",
    ChainType.BITCOIN_TESTNET: "https://mempool.space/testnet/tx/{tx_hash}"
}
```

**Business Logic**:

1. **Dual Transaction Display**:
   - Outgoing transactions: `is_incoming=false`, `from_address=null`
   - Incoming transactions: `is_incoming=true`, `from_address` shows sender
   - Same on-chain transaction can appear twice (sender + receiver views)

2. **Filter Parsing**:
   - Chain: Validates against `ChainType` enum
   - Status: Maps to `TransactionStatus` enum (pending=0, success=1, failed=2)
   - Type: Maps via `TX_TYPE_MAP`

3. **Ordering**: Always ordered by `created_at DESC` (newest first)

4. **Pagination**: Uses `limit` and `offset` for cursor-based pagination

**Handler Flow** (lines 469-575 in `transaction_log.py`):
```python
async def execute(
    self, *, limit=50, offset=0, chain=None, status=None, tx_type=None
) -> TransactionHistoryResult:
    user = await self._current_user_service.get_current_user()
    user_id = UserId(user.id_.value)

    # Parse filters
    chain_filter = ChainType(chain.lower()) if chain else None
    status_filter = {"pending": 0, "success": 1, "failed": 2}.get(status.lower()) if status else None
    type_filter = TX_TYPE_MAP.get(tx_type.lower()) if tx_type else None

    # Get transactions
    transactions = await self._transaction_repository.get_by_user_id(
        user_id,
        limit=limit,
        offset=offset,
        chain=chain_filter,
        status=status_filter,
        tx_type=type_filter
    )

    # Get total count
    total = await self._transaction_repository.count_by_user_id(
        user_id,
        chain=chain_filter,
        status=status_filter,
        tx_type=type_filter
    )

    # Convert to response items
    items = []
    for tx in transactions:
        # Determine if incoming transaction
        is_incoming = bool(tx.tx_metadata and tx.tx_metadata.get("receiver_view"))
        from_address = tx.tx_metadata.get("from_address") if is_incoming else None

        items.append(TransactionHistoryItem(
            id=tx.id_.value,
            tx_hash=tx.tx_hash,
            type=tx.type.name.lower(),
            chain=tx.chain.value,
            status=tx.status.name.lower(),
            to_address=tx.to_address,
            asset_in=tx.asset_in,
            amount_in=str(tx.amount_in) if tx.amount_in else None,
            asset_out=tx.asset_out,
            amount_out=str(tx.amount_out) if tx.amount_out else None,
            fee_usd=str(tx.fee_usd) if tx.fee_usd else None,
            block_number=tx.block_number,
            confirmed_at=tx.confirmed_at.isoformat() if tx.confirmed_at else None,
            created_at=tx.created_at.value.isoformat(),
            explorer_url=get_explorer_url(tx.chain, tx.tx_hash),
            gas_used=tx.gas_used,
            gas_price=tx.gas_price,
            is_incoming=is_incoming,
            from_address=from_address
        ))

    return TransactionHistoryResult(
        user_id=user.id_.value,
        transactions=items,
        total=total,
        limit=limit,
        offset=offset
    )
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```javascript
// Frontend (React)
const fetchTransactionHistory = async (filters = {}) => {
  const params = new URLSearchParams({
    limit: filters.limit || 50,
    offset: filters.offset || 0,
    ...(filters.chain && { chain: filters.chain }),
    ...(filters.status && { status: filters.status }),
    ...(filters.tx_type && { tx_type: filters.tx_type })
  });

  const response = await fetch(`/api/v1/user/transactions?${params}`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  const data = await response.json();

  // Display transactions
  data.transactions.forEach(tx => {
    console.log(
      `${tx.is_incoming ? '📥 Received' : '📤 Sent'} ${tx.amount_in} ${tx.asset_in}`,
      `Status: ${tx.status}`,
      `Explorer: ${tx.explorer_url}`
    );
  });

  return data;
};

// Fetch all transactions
await fetchTransactionHistory();

// Fetch only successful swaps on Base
await fetchTransactionHistory({
  chain: 'base',
  status: 'success',
  tx_type: 'swap'
});

// Pagination
await fetchTransactionHistory({ offset: 50, limit: 50 });
```

---

## Admin Endpoints

### List Wallets

#### GET /api/v1/admin/wallets

**Purpose**: List all wallets with pagination, sorting, and search (admin-only).

**Access Level**: Admin users only (requires `UserRole.ADMIN`)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/admin/wallet/list_wallets.py` (lines 61-108)
- **Query Service**: `ListWalletsQueryService` in `/src/app/application/queries/list_wallets.py` (lines 49-124)
- **Gateway**: `WalletQueryGateway` (SQLAlchemy reader)

**Request Schema**:
```http
GET /api/v1/admin/wallets?limit=20&offset=0&sorting_field=created_at&sorting_order=desc&search=0x1234 HTTP/1.1
Authorization: Bearer <admin_jwt_token>
```

**Query Parameters**:
- `limit` (optional, default: 20, range: 1-100): Max wallets per page
- `offset` (optional, default: 0, min: 0): Number of wallets to skip
- `sorting_field` (optional, default: "created_at"): Field to sort by (id, address, provider, created_at)
- `sorting_order` (optional, default: "desc"): Sort direction (asc, desc)
- `search` (optional): Search term (matches address, email, user name, or wallet ID)

**Response Schema** (`200 OK`):
```json
{
  "wallets": [
    {
      "id": 1,
      "user_id": 123,
      "privy_wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
      "address": "0x1234567890abcdef1234567890abcdef12345678",
      "provider": "privy",
      "default_chain": "ethereum",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z",
      "user_email": "user@example.com",
      "user_name": "John Doe"
    }
  ],
  "total": 1543
}
```

**Response Fields**:

**Wallet Object**:
- `id`: Database wallet ID
- `user_id`: Owner user ID
- `privy_wallet_id`: Privy wallet ID (null for imported wallets)
- `address`: Blockchain address
- `provider`: Wallet provider (privy, external, imported)
- `default_chain`: Default blockchain (ethereum, base, etc.)
- `status`: Wallet status (active, inactive)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `user_email`: Owner's email
- `user_name`: Owner's name

**Top-Level**:
- `wallets`: Array of wallet objects
- `total`: Total wallets matching search (for pagination)

**Business Logic**:

1. **Authorization**: Only `UserRole.ADMIN` can access

2. **Search Functionality**: Searches across multiple fields:
   - Wallet address (partial match, case-insensitive)
   - User email (partial match, case-insensitive)
   - User name (partial match, case-insensitive)
   - Privy wallet ID (exact match)

3. **Sorting**: Supports sorting by:
   - `id`: Database ID
   - `address`: Wallet address
   - `provider`: Wallet provider
   - `created_at`: Creation timestamp (default)

4. **Pagination**: Uses `limit` and `offset`

**Query Service Flow** (lines 68-124 in `list_wallets.py`):
```python
async def execute(self, request_data: ListWalletsRequest) -> ListWalletsResponse:
    current_user = await self._current_user_service.get_current_user()

    # Only admins can list all wallets
    authorize(
        CanManageRole(),
        context=RoleManagementContext(
            subject=current_user,
            target_role=UserRole.USER
        )
    )

    wallet_list_params = WalletListParams(
        pagination=Pagination(
            limit=request_data.limit,
            offset=request_data.offset
        ),
        sorting=WalletListSorting(
            sorting_field=request_data.sorting_field,
            sorting_order=request_data.sorting_order
        ),
        search=request_data.search
    )

    wallets = await self._wallet_query_gateway.read_all(wallet_list_params)

    if wallets is None:
        raise SortingError("Invalid sorting field")

    total = await self._wallet_query_gateway.count_all(search=request_data.search)

    return ListWalletsResponse(wallets=wallets, total=total)
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: User is not an admin
- `400 Bad Request`: Invalid sorting field
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```bash
# List all wallets (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/wallets?limit=20&offset=0" \
  -H "Authorization: Bearer <admin_token>"

# Search for wallets by address
curl -X GET "https://api.anvil.com/api/v1/admin/wallets?search=0x1234" \
  -H "Authorization: Bearer <admin_token>"

# Sort by address ascending
curl -X GET "https://api.anvil.com/api/v1/admin/wallets?sorting_field=address&sorting_order=asc" \
  -H "Authorization: Bearer <admin_token>"
```

---

### Get Wallet Details

#### GET /api/v1/admin/wallets/{privy_wallet_id}

**Purpose**: Retrieve detailed wallet information for admin management, combining local database data with live Privy API data.

**Access Level**: Admin users only (requires `UserRole.ADMIN`)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/admin/wallet/get_wallet_details.py` (lines 136-175)
- **Query Service**: `GetPrivyWalletDetails` in `/src/app/application/queries/wallet/get_privy_wallet_details.py` (lines 97-265)
- **Privy Client**: `/src/app/infrastructure/privy/client.py`

**Request Schema**:
```http
GET /api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0 HTTP/1.1
Authorization: Bearer <admin_jwt_token>
```

**Path Parameters**:
- `privy_wallet_id` (required): The Privy wallet ID

**Response Schema** (`200 OK`):
```json
{
  "local_wallet_id": 42,
  "privy_wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain_type": "ethereum",
  "user_id": 123,
  "owner_type": "user",
  "owner_id": "did:privy:abc123xyz",
  "policy_ids": ["policy_123", "policy_456"],
  "additional_signers": [
    {
      "signer_id": "signer_789",
      "override_policy_ids": ["policy_999"]
    }
  ],
  "provider": "privy",
  "status": "active",
  "is_recoverable": true,
  "created_at": "2024-01-15T10:30:00Z",
  "exported_at": null,
  "imported_at": null,
  "last_privy_sync_at": "2026-01-26T12:00:00Z",
  "privy_raw_data": {
    "wallet_index": 0,
    "hd_wallet_index": 0
  }
}
```

**Response Fields**:

**Identification**:
- `local_wallet_id`: Local database wallet ID (null if not in local DB)
- `privy_wallet_id`: Privy wallet ID
- `address`: Blockchain wallet address
- `chain_type`: Blockchain type (ethereum, base, etc.)

**User Association**:
- `user_id`: Local user ID (null if not in local DB)
- `owner_type`: Owner type in Privy (user, authorization_key, etc.)
- `owner_id`: Owner ID in Privy (DID)

**Privy Configuration** (editable via admin):
- `policy_ids`: Array of policy IDs attached to this wallet
- `additional_signers`: Array of additional signer objects
  - `signer_id`: The signer ID
  - `override_policy_ids`: Override policy IDs for this signer

**Status**:
- `provider`: Wallet provider (privy, external, imported)
- `status`: Wallet status (active, inactive)
- `is_recoverable`: Whether the wallet is recoverable via Privy

**Timestamps**:
- `created_at`: When the wallet was created
- `exported_at`: When the wallet was last exported (null if never)
- `imported_at`: When the wallet was imported (null if embedded)
- `last_privy_sync_at`: Last time we synced with Privy API

**Debugging**:
- `privy_raw_data`: Raw Privy API response for debugging

**Business Logic**:

1. **Authorization**: Only admins can access

2. **Data Merging**:
   - Fetches local wallet data from database
   - Fetches live wallet data from Privy API
   - Merges data, preferring Privy for configuration fields
   - Updates local cache with latest Privy data

3. **Graceful Degradation**: If wallet exists locally but not in Privy, returns local data only

4. **Cache Update**: Automatically updates local database with latest Privy configuration

**Query Service Flow** (lines 125-265 in `get_privy_wallet_details.py`):
```python
async def execute(self, request: GetPrivyWalletDetailsRequest) -> AdminWalletDetailsDTO:
    # 1. Validate admin permissions
    current_user = await self._current_user_service.get_current_user()
    authorize(CanManageRole(), ...)

    # 2. Fetch local wallet data
    local_wallet = await self._wallet_repository.get_by_privy_wallet_id(
        request.privy_wallet_id
    )

    # 3. Fetch live Privy wallet data
    try:
        privy_wallet = await self._privy_client.get_wallet(request.privy_wallet_id)
    except PrivyWalletNotFoundError:
        if local_wallet is None:
            raise WalletNotFoundError(...)
        privy_wallet = None  # Wallet exists locally but not in Privy

    # 4. Build the DTO
    metadata = privy_wallet.metadata if privy_wallet else {}

    additional_signers = [
        AdditionalSignerDTO(
            signer_id=s.get("signer_id", ""),
            override_policy_ids=s.get("override_policy_ids")
        )
        for s in metadata.get("additional_signers", [])
        if isinstance(s, dict)
    ]

    dto = AdminWalletDetailsDTO(
        local_wallet_id=local_wallet.id_.value if local_wallet else None,
        privy_wallet_id=request.privy_wallet_id,
        address=privy_wallet.address if privy_wallet else local_wallet.address,
        chain_type=privy_wallet.chain_type.value if privy_wallet else local_wallet.default_chain.value,
        user_id=local_wallet.user_id.value if local_wallet else None,
        owner_type=metadata.get("owner_type") or (local_wallet.owner_type if local_wallet else None),
        owner_id=metadata.get("owner_id") or (local_wallet.owner_id if local_wallet else None),
        policy_ids=metadata.get("policy_ids", []) or (local_wallet.policy_ids if local_wallet else []),
        additional_signers=additional_signers,
        provider=local_wallet.provider.value if local_wallet else "privy",
        status=local_wallet.status.name.lower() if local_wallet else "active",
        is_recoverable=privy_wallet.is_recoverable if privy_wallet else True,
        created_at=privy_wallet.created_at if privy_wallet else local_wallet.created_at.value,
        exported_at=metadata.get("exported_at") or (local_wallet.exported_at if local_wallet else None),
        imported_at=metadata.get("imported_at") or (local_wallet.imported_at if local_wallet else None),
        last_privy_sync_at=datetime.now(UTC),
        privy_raw_data=metadata.get("raw", {})
    )

    # 5. Update local cache with Privy data
    if local_wallet and privy_wallet:
        local_wallet.policy_ids = metadata.get("policy_ids", [])
        local_wallet.owner_type = metadata.get("owner_type")
        local_wallet.owner_id = metadata.get("owner_id")
        local_wallet.additional_signers = [...]
        local_wallet.last_privy_sync_at = datetime.now(UTC)

        await self._wallet_repository.update(local_wallet)

    return dto
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: User is not an admin
- `404 Not Found`: Wallet not found in database or Privy
- `502 Bad Gateway`: Privy API error
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```bash
# Get wallet details (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0" \
  -H "Authorization: Bearer <admin_token>"
```

---

### Update Wallet

#### PATCH /api/v1/admin/wallets/{privy_wallet_id}

**Purpose**: Update wallet configuration in Privy (admin-only). Changes are synced to local database.

**Access Level**: Admin users only (requires `UserRole.ADMIN`)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/admin/wallet/update_wallet.py` (lines 161-227)
- **Command Service**: `UpdatePrivyWallet` in `/src/app/application/commands/wallet/update_privy_wallet.py`
- **Privy Client**: `/src/app/infrastructure/privy/client.py`

**Request Schema**:
```http
PATCH /api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0 HTTP/1.1
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "policy_ids": ["policy_123", "policy_456"],
  "owner_id": "did:privy:xyz789",
  "additional_signers": [
    {
      "signer_id": "signer_789",
      "override_policy_ids": ["policy_999"]
    }
  ]
}
```

**Path Parameters**:
- `privy_wallet_id` (required): The Privy wallet ID

**Request Fields** (all optional - only provided fields will be updated):
- `policy_ids`: Array of policy IDs to attach to this wallet
- `owner`: New owner object (e.g., `{"user_id": "did:privy:xxx"}`)
- `owner_id`: New owner ID (alternative to owner object)
- `additional_signers`: Array of additional signer objects
  - `signer_id` (required): The signer ID
  - `override_policy_ids` (optional): Override policy IDs for this signer

**Validation**:
- Cannot provide both `owner` and `owner_id` (validation error)

**Response Schema** (`200 OK`):
```json
{
  "success": true,
  "changes_applied": {
    "policy_ids": ["policy_123", "policy_456"],
    "owner_id": "did:privy:xyz789",
    "additional_signers": [
      {
        "signer_id": "signer_789",
        "override_policy_ids": ["policy_999"]
      }
    ]
  },
  "local_wallet_id": 42,
  "privy_wallet_id": "g1644aqvat8qxkfqsfzvpuq0",
  "address": "0x1234567890abcdef1234567890abcdef12345678",
  "chain_type": "ethereum",
  "user_id": 123,
  "owner_type": "user",
  "owner_id": "did:privy:xyz789",
  "policy_ids": ["policy_123", "policy_456"],
  "additional_signers": [
    {
      "signer_id": "signer_789",
      "override_policy_ids": ["policy_999"]
    }
  ],
  "provider": "privy",
  "status": "active",
  "is_recoverable": true,
  "created_at": "2024-01-15T10:30:00Z",
  "exported_at": null,
  "imported_at": null,
  "last_privy_sync_at": "2026-01-26T12:30:00Z"
}
```

**Response Fields**:

**Update Summary**:
- `success`: Whether the update was successful
- `changes_applied`: Dictionary of changes that were applied

**Updated Wallet Details**: Same as `GET /admin/wallets/{privy_wallet_id}` response

**Business Logic**:

1. **Authorization**: Only admins can update

2. **Partial Updates**: Only provided fields are updated (PATCH semantics)

3. **Privy API Integration**:
   - Sends update request to Privy API
   - Privy validates and applies changes
   - Returns updated wallet configuration

4. **Local Database Sync**:
   - Fetches updated wallet details from Privy
   - Updates local database with new configuration
   - Records `last_privy_sync_at` timestamp

5. **Change Tracking**: Returns dictionary of changes applied

**Controller Flow** (lines 185-227 in `update_wallet.py`):
```python
async def update_wallet(
    privy_wallet_id: str,
    request_body: UpdateWalletRequest,
    command_service: FromDishka[UpdatePrivyWallet]
) -> UpdateWalletResponse:
    # Convert request to command format
    additional_signers = None
    if request_body.additional_signers is not None:
        additional_signers = [
            {
                "signer_id": s.signer_id,
                "override_policy_ids": s.override_policy_ids
            }
            for s in request_body.additional_signers
        ]

    request = UpdatePrivyWalletRequest(
        privy_wallet_id=privy_wallet_id,
        policy_ids=request_body.policy_ids,
        owner=request_body.owner,
        owner_id=request_body.owner_id,
        additional_signers=additional_signers
    )

    result = await command_service.execute(request)

    return UpdateWalletResponse.from_result(
        success=result.success,
        wallet_details=result.wallet_details,
        changes_applied=result.changes_applied
    )
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: User is not an admin
- `404 Not Found`: Wallet not found in Privy
- `422 Unprocessable Entity`: Validation error (both owner and owner_id provided)
- `502 Bad Gateway`: Privy API error during update
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```bash
# Update wallet policy IDs (admin)
curl -X PATCH "https://api.anvil.com/api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_ids": ["policy_123", "policy_456"]
  }'

# Update wallet owner (admin)
curl -X PATCH "https://api.anvil.com/api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id": "did:privy:xyz789"
  }'

# Update additional signers (admin)
curl -X PATCH "https://api.anvil.com/api/v1/admin/wallets/g1644aqvat8qxkfqsfzvpuq0" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "additional_signers": [
      {
        "signer_id": "signer_789",
        "override_policy_ids": ["policy_999"]
      }
    ]
  }'
```

---

### Admin Transaction History

#### GET /api/v1/admin/transactions

**Purpose**: Get transaction history for any wallet or user (admin-only). Supports global view, wallet-scoped view, or user-scoped view.

**Access Level**: Admin users only (requires `UserRole.ADMIN`)

**Implementation**:
- **Controller**: `/src/app/presentation/http/controllers/admin/transactions_router.py` (lines 68-156)
- **Handler**: `GetAdminTransactionHistoryHandler` in `/src/app/infrastructure/auth/handlers/transaction_log.py` (lines 590-848)
- **Repository**: `SqlaTransactionRepository`

**Request Schema**:
```http
GET /api/v1/admin/transactions?wallet_address=0x1234...&limit=50&offset=0&chain=base&status=success HTTP/1.1
Authorization: Bearer <admin_jwt_token>
```

**Query Parameters**:

**Scoping** (choose one):
- `wallet_address` (optional): Filter by wallet address (recommended for specific wallet view)
- `user_id` (optional): Filter by user ID (aggregates across all user's wallets)
- *If neither provided*: Returns global transaction history (all transactions)

**Filtering**:
- `limit` (optional, default: 50, range: 1-100): Maximum number of results
- `offset` (optional, default: 0, min: 0): Number of results to skip
- `chain` (optional): Filter by chain (ethereum, base, arbitrum, polygon, optimism)
- `status` (optional): Filter by status (pending, success, failed)
- `tx_type` (optional): Filter by type (send, swap, approve, fund, earn)

**Response Schema** (`200 OK`):
```json
{
  "wallet_address": "0x1234567890abcdef1234567890abcdef12345678",
  "user_id": 123,
  "transactions": [
    {
      "id": 1,
      "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
      "type": "swap",
      "chain": "base",
      "status": "success",
      "to_address": null,
      "asset_in": "ETH",
      "amount_in": "0.9",
      "asset_out": "USDC",
      "amount_out": "3000.00",
      "fee_usd": "0.99",
      "block_number": 18500000,
      "confirmed_at": "2024-01-15T10:30:30Z",
      "created_at": "2024-01-15T10:30:00Z",
      "explorer_url": "https://basescan.org/tx/0x1234...",
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

**Response Fields**:

**Top-Level**:
- `wallet_address`: Wallet address used to scope the query (null if scoped by user_id or global)
- `user_id`: User ID used to scope the query (null if scoped by wallet_address or global)
- `transactions`: Array of transaction objects (same format as user transaction history)
- `total`: Total matching transactions
- `limit`: Page size used
- `offset`: Page offset used

**Transaction Object**: Same as user transaction history endpoint

**Business Logic**:

1. **Authorization**: Only `UserRole.ADMIN` can access

2. **Three Query Modes**:

   **A. Global View** (no wallet_address or user_id):
   - Returns all transactions across all users
   - Useful for admin dashboard overview

   **B. Wallet-Scoped View** (wallet_address provided):
   - Returns transactions for exact wallet only
   - Looks up wallet by address
   - Returns empty list if wallet not found

   **C. User-Scoped View** (user_id provided):
   - Returns transactions across all user's wallets
   - Aggregates from multiple wallets

3. **Dual Transaction Display**: Same as user endpoint (incoming/outgoing)

4. **Filtering**: Same as user endpoint (chain, status, tx_type)

5. **Pagination**: Uses limit and offset

**Handler Flow** (lines 607-848 in `transaction_log.py`):
```python
async def execute(
    self,
    *,
    wallet_address=None,
    user_id=None,
    limit=50,
    offset=0,
    chain=None,
    status=None,
    tx_type=None
) -> AdminTransactionHistoryResult:
    current_user = await self._current_user_service.get_current_user()

    # Verify admin access
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Admin access required")

    # Parse filters
    chain_filter = ChainType(chain.lower()) if chain else None
    status_filter = {...}.get(status.lower()) if status else None
    type_filter = TX_TYPE_MAP.get(tx_type.lower()) if tx_type else None

    normalized_wallet = wallet_address.lower() if wallet_address else None

    # MODE 1: Global scope (no filters)
    if not normalized_wallet and not user_id:
        transactions = await self._transaction_repository.get_all(
            limit=limit,
            offset=offset,
            chain=chain_filter,
            status=status_filter,
            tx_type=type_filter
        )
        total = await self._transaction_repository.count_all_filtered(...)

        return AdminTransactionHistoryResult(
            wallet_address=None,
            user_id=None,
            transactions=items,
            total=total,
            limit=limit,
            offset=offset
        )

    # MODE 2: Wallet-scoped
    if normalized_wallet:
        wallet = await self._wallet_repository.get_by_address(normalized_wallet)

        if not wallet:
            return AdminTransactionHistoryResult(
                wallet_address=normalized_wallet,
                user_id=None,
                transactions=[],
                total=0,
                limit=limit,
                offset=offset
            )

        transactions = await self._transaction_repository.get_by_wallet_id(
            wallet.id_,
            limit=limit,
            offset=offset,
            chain=chain_filter,
            status=status_filter,
            tx_type=type_filter
        )
        total = await self._transaction_repository.count_by_wallet_id(...)

        return AdminTransactionHistoryResult(
            wallet_address=normalized_wallet,
            user_id=wallet.user_id.value,
            transactions=items,
            total=total,
            limit=limit,
            offset=offset
        )

    # MODE 3: User-scoped (aggregates across wallets)
    user_id_vo = UserId(user_id)
    transactions = await self._transaction_repository.get_by_user_id(
        user_id_vo,
        limit=limit,
        offset=offset,
        chain=chain_filter,
        status=status_filter,
        tx_type=type_filter
    )
    total = await self._transaction_repository.count_by_user_id(...)

    return AdminTransactionHistoryResult(
        wallet_address=None,
        user_id=user_id_vo.value,
        transactions=items,
        total=total,
        limit=limit,
        offset=offset
    )
```

**Error Responses**:
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: User is not an admin
- `503 Service Unavailable`: Database connection failure

**Example Usage**:
```bash
# Global view: All transactions (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/transactions?limit=50" \
  -H "Authorization: Bearer <admin_token>"

# Wallet-scoped view: Transactions for specific wallet (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/transactions?wallet_address=0x1234567890abcdef1234567890abcdef12345678" \
  -H "Authorization: Bearer <admin_token>"

# User-scoped view: Transactions for specific user across all wallets (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/transactions?user_id=123" \
  -H "Authorization: Bearer <admin_token>"

# Filter: Only successful swaps on Base (admin)
curl -X GET "https://api.anvil.com/api/v1/admin/transactions?chain=base&status=success&tx_type=swap" \
  -H "Authorization: Bearer <admin_token>"
```

---

## Error Responses

### Common HTTP Status Codes

All endpoints use consistent error handling via `fastapi-error-map`:

**401 Unauthorized**:
```json
{
  "detail": "Could not validate credentials"
}
```
**Causes**: Invalid JWT token, expired token, missing Authorization header

**403 Forbidden**:
```json
{
  "detail": "Wallet does not belong to the authenticated user"
}
```
**Causes**:
- User attempting to access another user's wallet
- Non-admin attempting to access admin endpoints
- User without linked Privy account attempting wallet export

**404 Not Found**:
```json
{
  "detail": "Wallet g1644aqvat8qxkfqsfzvpuq0 not found"
}
```
**Causes**: Wallet ID does not exist in Privy or database

**400 Bad Request**:
```json
{
  "detail": "Wallet 0x1234... not found. Please sync your wallets first."
}
```
**Causes**:
- Wallet not synced to backend before logging transaction
- Invalid amounts (non-positive)
- Invalid chain name
- Invalid sorting field

**422 Unprocessable Entity**:
```json
{
  "detail": "Cannot provide both 'owner' and 'owner_id'"
}
```
**Causes**: Validation error in request body

**500 Internal Server Error**:
```json
{
  "detail": "Failed to save swap transaction"
}
```
**Causes**: Unexpected server error

**502 Bad Gateway**:
```json
{
  "detail": "Failed to fetch wallet from Privy: API error"
}
```
**Causes**: Privy API is down or returned an error

**503 Service Unavailable**:
```json
{
  "detail": "Database query failed"
}
```
**Causes**: Database connection failure, query timeout

---

## Integration Patterns

### Pattern 1: Wallet Connection Flow

**Frontend (React + Privy SDK)**:
```javascript
import { useWallets, useLogin } from '@privy-io/react-auth';

const WalletConnect = () => {
  const { wallets } = useWallets();
  const { login } = useLogin();

  // 1. User logs in with Privy
  const handleLogin = async () => {
    await login();
  };

  // 2. After login, sync wallets to backend
  const syncWallets = async (accessToken) => {
    await fetch('/api/v1/wallet/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        wallets: wallets.map(w => ({
          address: w.address,
          chain_type: w.chainType,
          wallet_type: w.walletType,
          privy_wallet_id: w.id
        }))
      })
    });
  };

  // 3. Fetch wallets from backend
  const fetchWallets = async (accessToken) => {
    const response = await fetch('/api/v1/wallet/me', {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    return await response.json();
  };
};
```

### Pattern 2: Transaction Execution Flow

**Frontend (React + Privy + 0x)**:
```javascript
import { usePrivy } from '@privy-io/react-auth';

const SwapExecution = () => {
  const { sendTransaction } = usePrivy();

  const executeSwap = async (swapData, conversationId) => {
    // 1. Get swap quote from 0x API
    const quote = await fetch('https://api.0x.org/swap/v1/quote', {
      params: {
        sellToken: 'ETH',
        buyToken: 'USDC',
        sellAmount: ethers.utils.parseEther('0.9').toString(),
        takerAddress: walletAddress
      }
    }).then(r => r.json());

    // 2. Execute swap via Privy
    const txHash = await sendTransaction({
      to: quote.to,
      data: quote.data,
      value: quote.value
    });

    // 3. Wait for confirmation
    const receipt = await provider.waitForTransaction(txHash);

    // 4. Save to backend
    await fetch('/api/v1/wallet/swaps/complete', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tx_hash: txHash,
        chain: 'base',
        from_token: 'ETH',
        to_token: 'USDC',
        from_amount: '0.9',
        to_amount: quote.buyAmount / 1e6,  // USDC has 6 decimals
        exchange_rate: (quote.buyAmount / 1e6) / 0.9,
        gas_fee_usd: calculateGasFeeUSD(receipt),
        slippage: '1.0',
        conversation_id: conversationId
      })
    });

    return { txHash, receipt };
  };
};
```

### Pattern 3: Transaction History Display

**Frontend (React)**:
```javascript
const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      const response = await fetch('/api/v1/user/transactions?limit=50', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      const data = await response.json();
      setTransactions(data.transactions);
      setLoading(false);
    };

    fetchHistory();
  }, [accessToken]);

  return (
    <div>
      {transactions.map(tx => (
        <TransactionRow key={tx.id} transaction={tx} />
      ))}
    </div>
  );
};

const TransactionRow = ({ transaction }) => {
  const direction = transaction.is_incoming ? '📥 Received' : '📤 Sent';
  const status = {
    'pending': '🕐 Pending',
    'success': '✅ Success',
    'failed': '❌ Failed'
  }[transaction.status];

  return (
    <div>
      <span>{direction}</span>
      <span>{transaction.amount_in} {transaction.asset_in}</span>
      {transaction.asset_out && (
        <span>→ {transaction.amount_out} {transaction.asset_out}</span>
      )}
      <span>{status}</span>
      <a href={transaction.explorer_url}>View on Explorer</a>
    </div>
  );
};
```

### Pattern 4: Admin Wallet Management

**Frontend (Admin Dashboard)**:
```javascript
const AdminWalletManagement = () => {
  const [wallets, setWallets] = useState([]);
  const [search, setSearch] = useState('');

  // Fetch wallets with search
  const fetchWallets = async (searchTerm) => {
    const params = new URLSearchParams({
      limit: 20,
      offset: 0,
      sorting_field: 'created_at',
      sorting_order: 'desc',
      ...(searchTerm && { search: searchTerm })
    });

    const response = await fetch(`/api/v1/admin/wallets?${params}`, {
      headers: {
        'Authorization': `Bearer ${adminToken}`
      }
    });

    const data = await response.json();
    setWallets(data.wallets);
  };

  // Get wallet details
  const getWalletDetails = async (privyWalletId) => {
    const response = await fetch(
      `/api/v1/admin/wallets/${privyWalletId}`,
      {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      }
    );

    return await response.json();
  };

  // Update wallet configuration
  const updateWallet = async (privyWalletId, updates) => {
    const response = await fetch(
      `/api/v1/admin/wallets/${privyWalletId}`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${adminToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      }
    );

    return await response.json();
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Search wallets..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          fetchWallets(e.target.value);
        }}
      />

      {wallets.map(wallet => (
        <WalletRow
          key={wallet.id}
          wallet={wallet}
          onDetails={() => getWalletDetails(wallet.privy_wallet_id)}
          onUpdate={(updates) => updateWallet(wallet.privy_wallet_id, updates)}
        />
      ))}
    </div>
  );
};
```

---

## Summary

The Wallets & Transactions module provides a comprehensive API for managing blockchain wallets and transactions with:

**User Features**:
- Multi-source wallet aggregation (Privy + Local DB)
- Secure private key export (HPKE encryption)
- Transaction logging and history
- Swap transaction persistence
- Real-time transaction status updates

**Admin Features**:
- Global wallet management
- Detailed wallet configuration
- Transaction monitoring across all users
- Search and filtering capabilities

**Architecture Highlights**:
- Hexagonal architecture with clear layer separation
- CQRS pattern for read/write separation
- Port-adapter pattern for Privy integration
- Dishka dependency injection
- Comprehensive error handling
- Dual transaction logging (sender + receiver views)

**Security Measures**:
- JWT authentication on all endpoints
- Role-based authorization (user vs admin)
- Wallet ownership verification
- HPKE encryption for private key export
- Audit trail for sensitive operations

For more details on services, Celery tasks, and database architecture, see:
- `services.md` - Service layer documentation
- `celery.md` - Background task documentation
- `README.md` - Navigation and overview
