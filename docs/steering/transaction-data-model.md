# Transaction Data Model - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El modelo de datos de transacciones en Anvil Backend está diseñado para:

1. **On-Chain Transaction Logging**: Registro de transacciones enviadas desde el frontend vía Privy
2. **Dual Transaction Records**: Mismo tx_hash aparece en historial de sender y receiver
3. **Multi-Chain Support**: Ethereum, L2s (Arbitrum, Base, Optimism, Polygon), Bitcoin
4. **DEX/Swap Tracking**: Aggregator, route, slippage para operaciones de swap
5. **Transaction Confirmation**: Worker de Celery para confirmar transacciones pendientes
6. **Analytics**: Métricas de volumen, conteo por tipo/chain/status, usuarios activos

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                       TRANSACTION DATA MODEL                                             │
└─────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌────────────────┐
                                    │     Users      │
                                    └───────┬────────┘
                                            │ 1:N
                                            │
                           ┌────────────────┼────────────────┐
                           │                                 │
                           ▼                                 ▼
                    ┌─────────────┐                   ┌─────────────┐
                    │   Wallets   │                   │ Transactions│
                    └──────┬──────┘                   └──────┬──────┘
                           │                                 │
                           │ 1:N                             │
                           │                                 │
                           └─────────────────────────────────┘
                                    Wallet → Transactions

    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                    TRANSACTION UNIQUENESS                                  ║
    ╠═══════════════════════════════════════════════════════════════════════════╣
    ║  • tx_hash is NOT globally unique                                          ║
    ║  • Same on-chain tx can appear for BOTH sender and receiver               ║
    ║  • Uniqueness enforced by (user_id, tx_hash) constraint                    ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Core Entity

### Transaction Entity

**Location**: `src/app/domain/entities/transaction.py`

```python
@dataclass(eq=False, kw_only=True)
class Transaction(Entity[TransactionId]):
    """On-chain transaction entity."""
    
    # Core Fields (Relationships)
    user_id: UserId                      # User who initiated/received
    wallet_id: WalletId                  # Source wallet (sender's wallet)
    
    # Core Fields (Transaction Details)
    to_address: str | None               # Recipient address (0x...)
    type: TransactionType                # SEND, SWAP, APPROVE, etc.
    chain: ChainType                     # Blockchain network
    status: TransactionStatus            # PENDING, SUCCESS, FAILED
    tx_hash: str | None                  # On-chain transaction hash
    
    # Asset Details
    asset_in: str | None                 # Input token symbol (ETH, USDC)
    amount_in: Decimal | None            # Input amount
    asset_out: str | None                # Output token (for swaps)
    amount_out: Decimal | None           # Output amount (for swaps)
    
    # Fee Information
    fee: Decimal | None                  # Transaction fee (in token)
    fee_usd: Decimal | None              # Fee in USD
    
    # DEX/Swap Details
    dex_aggregator: str | None           # "1inch", "paraswap", "0x"
    dex_route: dict | None               # Swap route details (JSON)
    slippage: Decimal | None             # Slippage tolerance (%)
    
    # Confirmation Data
    block_number: int | None             # Confirmation block
    confirmed_at: datetime | None        # Confirmation timestamp
    error_message: str | None            # Error if failed
    
    # Analytics Fields (Mid-term)
    gas_used: int | None                 # Gas units consumed
    gas_price: int | None                # Gas price in wei
    tx_metadata: dict | None             # Additional context (JSON)
    
    created_at: CreatedAt
```

---

## Enumerations

### TransactionType

**Location**: `src/app/domain/enums/transaction_type.py`

```python
class TransactionType(Enum):
    SWAP = 0              # Token swap via DEX
    FUND = 1              # Funding operation
    EARN = 2              # Yield/staking deposit
    SAVE = 3              # Savings operation
    SUBSCRIPTION = 4      # Recurring payment
    SEND = 5              # Simple ETH/token transfer
    APPROVE = 6           # Token approval
    CONTRACT_CALL = 7     # Generic contract interaction
```

### TransactionStatus

**Location**: `src/app/domain/enums/transaction_status.py`

```python
class TransactionStatus(Enum):
    PENDING = 0           # Awaiting on-chain confirmation
    SUCCESS = 1           # Confirmed successfully
    FAILED = 2            # Transaction failed/reverted
```

### ChainType (Supported Chains)

**Location**: `src/app/domain/enums/chain_type.py`

```python
class ChainType(Enum):
    # EVM Chains
    ETHEREUM = "ethereum"
    ARBITRUM = "arbitrum"
    BASE = "base"
    POLYGON = "polygon"
    OPTIMISM = "optimism"
    HYPERLIQUID = "hyperliquid"
    
    # Bitcoin Networks
    BITCOIN = "bitcoin"
    BITCOIN_TESTNET = "bitcoin_testnet"
```

---

## Database Schema

### Transactions Table

```sql
CREATE TABLE transactions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Core Transaction Details
    to_address VARCHAR(42),               -- Recipient address (0x...)
    type INTEGER NOT NULL,                -- TransactionType enum (0-7)
    chain VARCHAR(50) NOT NULL,           -- ChainType enum
    status INTEGER NOT NULL DEFAULT 0,    -- TransactionStatus enum (0-2)
    
    -- On-chain Data
    -- NOTE: tx_hash is NOT globally unique!
    -- Same tx can appear for sender and receiver
    tx_hash VARCHAR(66),
    
    -- Asset Details
    asset_in VARCHAR(20),
    amount_in NUMERIC(30, 18),            -- Up to 10^12 ETH with 18 decimals
    asset_out VARCHAR(20),
    amount_out NUMERIC(30, 18),
    
    -- Fees
    fee NUMERIC(30, 18),
    fee_usd NUMERIC(10, 2),
    
    -- DEX/Swap Details
    dex_aggregator VARCHAR(50),           -- "1inch", "paraswap", etc.
    dex_route JSONB,                      -- Swap route details
    slippage NUMERIC(5, 2),               -- e.g., 0.50 = 0.5%
    error_message TEXT,
    
    -- Confirmation Data
    block_number INTEGER,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Analytics Fields
    gas_used BIGINT,                      -- Gas units consumed
    gas_price BIGINT,                     -- Gas price in wei
    tx_metadata JSONB,                    -- Extra context
    
    -- Constraints
    CONSTRAINT uq_transactions_user_tx_hash UNIQUE (user_id, tx_hash)
);

-- Indexes
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX idx_transactions_to_address ON transactions(to_address);
CREATE INDEX idx_transactions_type ON transactions(type);
CREATE INDEX idx_transactions_chain ON transactions(chain);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
```

---

## Chain ID Mapping

**Location**: `src/app/infrastructure/auth/handlers/transaction_log.py`

```python
CHAIN_ID_MAP: dict[int, ChainType] = {
    # Mainnet
    1: ChainType.ETHEREUM,
    10: ChainType.OPTIMISM,
    137: ChainType.POLYGON,
    8453: ChainType.BASE,
    42161: ChainType.ARBITRUM,
    
    # Testnet
    11155111: ChainType.ETHEREUM,   # Sepolia
    84532: ChainType.BASE,          # Base Sepolia
    
    # Bitcoin (pseudo chain IDs)
    0: ChainType.BITCOIN,           # Bitcoin mainnet
    -1: ChainType.BITCOIN_TESTNET,  # Bitcoin testnet
}
```

---

## Block Explorer URLs

```python
EXPLORER_URLS: dict[ChainType, str] = {
    ChainType.ETHEREUM: "https://etherscan.io/tx/{tx_hash}",
    ChainType.ARBITRUM: "https://arbiscan.io/tx/{tx_hash}",
    ChainType.BASE: "https://basescan.org/tx/{tx_hash}",
    ChainType.POLYGON: "https://polygonscan.com/tx/{tx_hash}",
    ChainType.OPTIMISM: "https://optimistic.etherscan.io/tx/{tx_hash}",
    ChainType.BITCOIN: "https://mempool.space/tx/{tx_hash}",
    ChainType.BITCOIN_TESTNET: "https://mempool.space/testnet/tx/{tx_hash}",
}
```

---

## Repository Interface

### TransactionRepository

**Location**: `src/app/domain/ports/transaction/transaction_repository.py`

```python
class TransactionRepository(Protocol):
    """Repository interface for transaction persistence."""
    
    # ============================================================
    # CRUD Operations
    # ============================================================
    
    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None
    async def get_by_tx_hash(self, tx_hash: str) -> Transaction | None
    async def get_by_user_and_tx_hash(
        self, user_id: UserId, tx_hash: str
    ) -> Transaction | None
    
    async def get_by_user_id(
        self, user_id: UserId, *,
        limit: int = 50, offset: int = 0,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[Transaction]
    
    async def get_by_wallet_id(
        self, wallet_id: WalletId, *,
        limit: int = 50, offset: int = 0,
        status: TransactionStatus | None = None,
    ) -> list[Transaction]
    
    async def get_pending_transactions(
        self, *, limit: int = 100, older_than_seconds: int | None = None
    ) -> list[Transaction]
    
    async def count_by_user_id(
        self, user_id: UserId, *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int
    
    async def save(self, transaction: Transaction) -> Transaction
    async def update(self, transaction: Transaction) -> Transaction
    async def update_status(
        self, transaction_id: TransactionId, status: TransactionStatus, *,
        block_number: int | None = None,
        confirmed_at: datetime | None = None,
        error_message: str | None = None,
    ) -> bool
    
    # ============================================================
    # Analytics Methods
    # ============================================================
    
    async def count_all(self) -> int
    async def count_by_status(self, status: TransactionStatus) -> int
    async def count_by_chain(self, chain: ChainType) -> int
    async def get_transaction_counts_by_status(self) -> dict[str, int]
    async def get_transaction_counts_by_chain(self) -> dict[str, int]
    async def get_transaction_counts_by_type(self) -> dict[str, int]
    async def count_transactions_in_range(
        self, start_date: datetime, end_date: datetime, *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        tx_type: TransactionType | None = None,
    ) -> int
    async def get_daily_transaction_counts(
        self, start_date: datetime, end_date: datetime, *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, int]]
    async def get_unique_user_count(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> int
    async def get_active_users_per_day(
        self, start_date: datetime, end_date: datetime
    ) -> list[tuple[datetime, int]]
    
    # ============================================================
    # Volume Analytics
    # ============================================================
    
    async def get_total_volume(
        self, *, chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> tuple[float, float]  # (total_volume, tx_count)
    
    async def get_volume_by_user(
        self, user_id: UserId, *,
        chain: ChainType | None = None,
        status: TransactionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float
    
    async def get_daily_volume(
        self, start_date: datetime, end_date: datetime, *,
        chain: ChainType | None = None,
        tx_type: TransactionType | None = None,
    ) -> list[tuple[datetime, float]]
    
    async def get_top_senders(
        self, *, limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[tuple[int, int, float]]  # (user_id, tx_count, volume)
```

---

## API Endpoints

### User Transaction History

```
GET /api/v1/transactions
Authorization: Bearer <token>

Query Parameters:
  - limit: int (default: 50, max: 100)
  - offset: int (default: 0)
  - chain: string (optional) - ethereum, arbitrum, base, etc.
  - status: string (optional) - pending, success, failed
  - tx_type: string (optional) - send, swap, approve, etc.

Response:
{
  "user_id": 123,
  "transactions": [
    {
      "id": 456,
      "tx_hash": "0x...",
      "type": "send",
      "chain": "ethereum",
      "status": "success",
      "to_address": "0x...",
      "asset_in": "ETH",
      "amount_in": "1.5",
      "fee_usd": "12.50",
      "block_number": 18500000,
      "confirmed_at": "2025-01-02T10:30:00Z",
      "created_at": "2025-01-02T10:29:00Z",
      "explorer_url": "https://etherscan.io/tx/0x...",
      "is_incoming": false,
      "from_address": null
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

### Log Transaction (from Frontend)

```
POST /api/v1/transactions
Authorization: Bearer <token>

Request Body:
{
  "tx_hash": "0x...",
  "from_address": "0x...",
  "to_address": "0x...",
  "value": "1500000000000000000",  // Wei as string
  "chain_id": 1,
  "tx_type": "send",
  "asset_symbol": "ETH"
}

Response:
{
  "id": 456,
  "tx_hash": "0x...",
  "status": "pending",
  "chain": "ethereum",
  "tx_type": "send",
  "from_address": "0x...",
  "to_address": "0x...",
  "created_at": "2025-01-02T10:29:00Z"
}
```

### Admin Transaction History

```
GET /api/v1/admin/transactions
Authorization: Bearer <admin_token>

Query Parameters:
  - wallet_address: string (optional) - Filter by wallet
  - user_id: int (optional) - Filter by user
  - limit, offset, chain, status, tx_type (same as user endpoint)

Response: Same structure as user endpoint
```

---

## Transaction Handlers

### LogTransactionHandler

**Location**: `src/app/infrastructure/auth/handlers/transaction_log.py`

Logs transactions from frontend when user sends via Privy.

**Key Features**:
1. **Duplicate Detection**: Checks if tx_hash already exists for this user
2. **Wallet Lookup**: Finds sender's wallet by address
3. **Wei to ETH Conversion**: Converts value from Wei to ETH (÷ 10^18)
4. **Dual Record Creation**: Creates records for both sender AND receiver

```python
class LogTransactionHandler:
    async def execute(self, input_data: LogTransactionInput) -> LogTransactionResult:
        # 1. Check duplicate for this user
        existing = await self._transaction_repository.get_by_user_and_tx_hash(
            user_id=user_id, tx_hash=input_data.tx_hash
        )
        if existing:
            return existing
        
        # 2. Find sender's wallet
        wallet = await self._wallet_repository.get_by_user_and_address(
            user_id=user_id, address=input_data.from_address
        )
        
        # 3. Create sender's transaction record
        transaction = Transaction.create(...)
        saved_tx = await self._transaction_repository.save(transaction)
        
        # 4. Create receiver's transaction record (if registered user)
        await self._log_receiver_transaction(...)
        
        return LogTransactionResult(...)
```

### GetTransactionHistoryHandler

Returns paginated transaction history for current user with filtering.

### GetAdminTransactionHistoryHandler

Admin-only handler with scope by wallet address or user ID.

---

## Transaction Confirmation Worker

### Celery Task

**Location**: `src/app/infrastructure/celery/tasks/transaction_confirmation_tasks.py`

```python
@shared_task(
    name="confirm_pending_transactions",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def confirm_pending_transactions_task(
    self,
    limit: int = 50,
    older_than_seconds: int = 10,
    use_testnet: bool | None = None,
) -> dict[str, Any]:
    """
    Confirm pending transactions on-chain.
    
    1. Query DB for pending transactions with tx_hash
    2. Check status on-chain via RPC
    3. Update status to SUCCESS or FAILED
    4. Update block_number, confirmed_at, gas_used, gas_price
    """
```

### Confirmation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Celery    │────►│  Database   │────►│   RPC Node  │────►│  Database   │
│    Beat     │     │   Query     │     │   Check     │     │   Update    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                    SELECT * FROM        eth_getTransaction   UPDATE
                    transactions         Receipt              transactions
                    WHERE status=0                            SET status=1,
                    AND tx_hash IS NOT                        block_number=X,
                    NULL                                      confirmed_at=NOW()
```

---

## Data Flow Examples

### 1. Frontend Transaction Logging

```
User                     Frontend                    Backend
  │                         │                           │
  │  Send ETH via Privy     │                           │
  │ ───────────────────────►│                           │
  │                         │                           │
  │                         │  Privy signs & submits    │
  │                         │  tx to blockchain         │
  │                         │                           │
  │                         │  POST /transactions       │
  │                         │  {tx_hash, from, to, ...} │
  │                         │ ─────────────────────────►│
  │                         │                           │
  │                         │                           │  Create sender record
  │                         │                           │  Create receiver record
  │                         │                           │  (if registered user)
  │                         │                           │
  │                         │◄───────────────────────── │
  │                         │  {id, status: "pending"}  │
  │◄─────────────────────── │                           │
  │  Transaction logged     │                           │
```

### 2. Transaction Confirmation Flow

```
Celery                  Database                   Ethereum RPC
   │                       │                           │
   │  Every 30 seconds     │                           │
   │                       │                           │
   │  Query pending txs    │                           │
   │ ─────────────────────►│                           │
   │                       │                           │
   │◄── [{tx_hash: "0x..", │                           │
   │      id: 123}, ...]   │                           │
   │                       │                           │
   │  For each tx_hash:    │                           │
   │  getTransactionReceipt│                           │
   │ ──────────────────────────────────────────────────►
   │                       │                           │
   │◄── {status: 1,        │                           │
   │     blockNumber: X,   │                           │
   │     gasUsed: Y}       │                           │
   │                       │                           │
   │  UPDATE transactions  │                           │
   │  SET status=1, ...    │                           │
   │ ─────────────────────►│                           │
```

### 3. Dual Transaction Record (Sender + Receiver)

```
Alice (sender)                              Bob (receiver)
     │                                           │
     │  Sends 1 ETH to Bob                       │
     │                                           │
     ▼                                           ▼
┌────────────────┐                      ┌────────────────┐
│  Transaction   │                      │  Transaction   │
│  id: 100       │                      │  id: 101       │
│  user_id: 1    │  Same tx_hash!       │  user_id: 2    │
│  tx_hash: 0x.. │◄────────────────────►│  tx_hash: 0x.. │
│  wallet_id: 10 │                      │  wallet_id: 20 │
│  to_address:   │                      │  to_address:   │
│    Bob's addr  │                      │    Bob's addr  │
│  is_incoming:  │                      │  is_incoming:  │
│    false       │                      │    true        │
│  tx_metadata:  │                      │  tx_metadata:  │
│    null        │                      │    {receiver_  │
│                │                      │     view: true,│
│                │                      │     from: Alice}
└────────────────┘                      └────────────────┘
```

---

## Analytics Queries

### Transaction Counts

```python
# Total transactions
total = await tx_repo.count_all()

# By status
by_status = await tx_repo.get_transaction_counts_by_status()
# {"PENDING": 50, "SUCCESS": 1000, "FAILED": 25}

# By chain
by_chain = await tx_repo.get_transaction_counts_by_chain()
# {"ethereum": 500, "arbitrum": 300, "base": 200}

# By type
by_type = await tx_repo.get_transaction_counts_by_type()
# {"SEND": 600, "SWAP": 350, "APPROVE": 50}
```

### Volume Analytics

```python
# Total volume (all time, successful transactions)
volume, count = await tx_repo.get_total_volume(
    status=TransactionStatus.SUCCESS
)
# (1500.5, 1000)  = 1500.5 ETH from 1000 transactions

# Daily volume for charts
daily = await tx_repo.get_daily_volume(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
)
# [(2025-01-01, 50.5), (2025-01-02, 75.2), ...]

# Top senders (leaderboard)
top = await tx_repo.get_top_senders(limit=10)
# [(user_id=5, tx_count=150, volume=500.0), ...]
```

### User Activity

```python
# Unique active users in date range
unique_users = await tx_repo.get_unique_user_count(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
)
# 500

# Daily active users
dau = await tx_repo.get_active_users_per_day(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31),
)
# [(2025-01-01, 25), (2025-01-02, 30), ...]
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Entity** | `domain/entities/transaction.py` | Transaction entity |
| **Enums** | `domain/enums/transaction_type.py` | Transaction types |
| | `domain/enums/transaction_status.py` | Status codes |
| **Port** | `domain/ports/transaction/transaction_repository.py` | Repository interface |
| **Adapter** | `infrastructure/adapters/transaction_repository_sqla.py` | SQLAlchemy impl |
| **Mapping** | `infrastructure/persistence_sqla/mappings/transaction.py` | DB schema |
| **Handlers** | `infrastructure/auth/handlers/transaction_log.py` | Log/History handlers |
| **Celery** | `infrastructure/celery/tasks/transaction_confirmation_tasks.py` | Confirmation worker |
| **Controller** | `presentation/http/controllers/admin/transactions_router.py` | Admin API |

---

## Best Practices

### Transaction Hash Normalization

```python
# Always normalize to lowercase
tx_hash = input_data.tx_hash.lower()
to_address = input_data.to_address.lower() if input_data.to_address else None
```

### Wei to ETH Conversion

```python
# Convert Wei to ETH for amount_in storage
# Database column NUMERIC(30, 18) supports up to 10^12 ETH
wei_value = Decimal(value_string)
amount_in = wei_value / Decimal("1000000000000000000")  # ÷ 10^18
```

### Duplicate Detection

```python
# Check per-user uniqueness (not global)
existing = await repo.get_by_user_and_tx_hash(
    user_id=user_id,
    tx_hash=tx_hash,
)
if existing:
    return existing  # Don't create duplicate
```

### Confirmation Retry Logic

```python
# Only process transactions older than N seconds
# Avoids race conditions with blockchain
pending = await repo.get_pending_transactions(
    limit=50,
    older_than_seconds=10,  # Wait 10 seconds before first check
)
```

---

**Last Updated**: January 2, 2026
