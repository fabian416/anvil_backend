# Wallet Data Model - Anvil Backend

**Version**: 1.0  
**Date**: January 2, 2026  
**Status**: Production Ready ✅

---

## Executive Summary

El modelo de datos de wallets en Anvil Backend está diseñado para:

1. **Multi-Chain Support**: Ethereum, L2s (Arbitrum, Optimism, Base, Polygon), Solana, Bitcoin
2. **Multiple Providers**: Privy embedded, External (MetaMask), Imported wallets
3. **Policy Management**: Privy policies para control de transacciones
4. **Transaction Tracking**: Historial completo con analytics
5. **Audit Trail**: Timestamps de export, import, y sync

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WALLET DATA MODEL                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐       1:N        ┌──────────────┐       1:N        ┌──────────────┐
│    Users     │─────────────────►│   Wallets    │─────────────────►│ Transactions │
└──────────────┘                  └──────────────┘                  └──────────────┘
       │                                 │                                 │
       │                                 │                                 │
       │                          ┌──────┴──────┐                          │
       │                          │             │                          │
       │                          ▼             ▼                          │
       │                   ┌─────────────┐ ┌─────────────┐                 │
       │                   │   Policies  │ │   Chain     │                 │
       │                   │             │ │  Addresses  │                 │
       │                   └─────────────┘ └─────────────┘                 │
       │                                                                    │
       └────────────────────────────────────────────────────────────────────┘
                              User owns all entities
```

---

## Core Entities

### 1. Wallet Entity

**Location**: `src/app/domain/entities/wallet.py`

```python
@dataclass(eq=False, kw_only=True)
class Wallet(Entity[WalletId]):
    # Core Fields
    user_id: UserId                      # Owner user
    privy_wallet_id: str | None          # Privy ID (null for imported)
    address: str                         # Blockchain address (normalized lowercase)
    provider: WalletProvider             # PRIVY, EXTERNAL, IMPORTED
    default_chain: ChainType             # Default network
    status: WalletStatus                 # ACTIVE, INACTIVE, DELETED
    created_at: CreatedAt
    updated_at: UpdatedAt
    
    # Privy Configuration Fields
    policy_ids: list[str]                # Attached policy IDs
    owner_type: str | None               # "user" or "authorization_key"
    owner_id: str | None                 # Owner identifier
    additional_signers: list[AdditionalSigner]  # Multi-sig signers
    
    # Audit Fields
    exported_at: datetime | None         # When private key was exported
    imported_at: datetime | None         # When wallet was imported
    last_privy_sync_at: datetime | None  # Last Privy API sync
```

### 2. Transaction Entity

**Location**: `src/app/domain/entities/transaction.py`

```python
@dataclass(eq=False, kw_only=True)
class Transaction(Entity[TransactionId]):
    # Core Fields
    user_id: UserId                      # User who initiated
    wallet_id: WalletId                  # Source wallet
    to_address: str | None               # Recipient (EOA, contract, or None)
    type: TransactionType                # SEND, SWAP, APPROVE, etc.
    chain: ChainType                     # Blockchain network
    status: TransactionStatus            # PENDING, SUCCESS, FAILED
    
    # Asset Details
    asset_in: str | None                 # Input token symbol
    amount_in: Decimal | None            # Input amount
    asset_out: str | None                # Output token symbol
    amount_out: Decimal | None           # Output amount
    
    # Fee Information
    fee: Decimal | None                  # Transaction fee
    fee_usd: Decimal | None              # Fee in USD
    
    # On-chain Data
    tx_hash: str | None                  # Transaction hash
    block_number: int | None             # Confirmation block
    confirmed_at: datetime | None        # Confirmation timestamp
    
    # DEX/Swap Details
    dex_aggregator: str | None           # e.g., "1inch", "paraswap"
    dex_route: dict | None               # Swap route details
    slippage: Decimal | None             # Slippage tolerance
    error_message: str | None            # Error if failed
    
    # Analytics Fields
    gas_used: int | None                 # Gas units consumed
    gas_price: int | None                # Gas price in wei
    tx_metadata: dict | None             # Additional context
    
    created_at: CreatedAt
```

### 3. Policy Entity

**Location**: `src/app/infrastructure/persistence_sqla/mappings/policy.py`

Policies control transaction permissions in Privy wallets.

```python
class Policy:
    id: str                              # Privy policy ID (primary key)
    name: str                            # Human-readable name
    version: str                         # Policy version
    chain_type: str                      # Blockchain network
    owner_id: str | None                 # Policy owner
    rules: list[dict]                    # JSON array of rules
    privy_raw: dict | None               # Raw Privy response
    metadata_: dict                      # Custom app metadata
    
    # Sync & Audit
    last_privy_sync_at: datetime | None
    is_deleted: bool
    created_by_user_id: int | None
    updated_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
```

---

## Enumerations

### WalletProvider

**Location**: `src/app/domain/enums/wallet_provider.py`

```python
class WalletProvider(Enum):
    PRIVY = "privy"           # Privy embedded wallet
    EXTERNAL = "external"     # Browser extension (MetaMask, etc.)
    IMPORTED = "imported"     # Imported via private key
```

### WalletStatus

**Location**: `src/app/domain/enums/wallet_status.py`

```python
class WalletStatus(Enum):
    INACTIVE = 0    # Wallet disabled
    ACTIVE = 1      # Normal operation
    DELETED = 2     # Soft deleted
```

### ChainType

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

### TransactionType

**Location**: `src/app/domain/enums/transaction_type.py`

```python
class TransactionType(Enum):
    SWAP = 0              # Token swap via DEX
    FUND = 1              # Funding operation
    EARN = 2              # Yield/staking
    SAVE = 3              # Savings operation
    SUBSCRIPTION = 4      # Recurring payment
    SEND = 5              # Simple transfer
    APPROVE = 6           # Token approval
    CONTRACT_CALL = 7     # Generic contract interaction
```

### TransactionStatus

**Location**: `src/app/domain/enums/transaction_status.py`

```python
class TransactionStatus(Enum):
    PENDING = 0     # Awaiting confirmation
    SUCCESS = 1     # Confirmed on-chain
    FAILED = 2      # Transaction failed
```

---

## Database Schema

### Wallets Table

```sql
CREATE TABLE wallets (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Core Fields
    privy_wallet_id VARCHAR(255) UNIQUE,  -- Can be NULL for imported
    address VARCHAR(42) NOT NULL,
    provider VARCHAR(50) NOT NULL DEFAULT 'privy',
    default_chain VARCHAR(50) DEFAULT 'arbitrum',
    status INTEGER NOT NULL DEFAULT 1,
    
    -- Privy Configuration
    policy_ids JSONB DEFAULT NULL,              -- ["policy_id_1", "policy_id_2"]
    owner_type VARCHAR(50) DEFAULT NULL,        -- "user" or "authorization_key"
    owner_id VARCHAR(255) DEFAULT NULL,
    additional_signers JSONB DEFAULT NULL,      -- [{signer_id, override_policy_ids}]
    
    -- Audit Timestamps
    exported_at TIMESTAMP WITH TIME ZONE,
    imported_at TIMESTAMP WITH TIME ZONE,
    last_privy_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Standard Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_user_wallet_address UNIQUE (user_id, address)
);

-- Indexes
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_privy_wallet_id ON wallets(privy_wallet_id);
```

### Chain Addresses Table

Tracks balances per chain for multi-chain wallets.

```sql
CREATE TABLE chain_addresses (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Chain Details
    chain VARCHAR(50) NOT NULL,  -- ChainType enum
    address VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Balance Tracking
    balance_usd NUMERIC(20, 2) DEFAULT 0.00,
    last_balance_update TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_wallet_chain UNIQUE (wallet_id, chain)
);

-- Indexes
CREATE INDEX idx_chain_addresses_wallet_id ON chain_addresses(wallet_id);
CREATE INDEX idx_chain_addresses_chain ON chain_addresses(chain);
CREATE INDEX idx_chain_addresses_address ON chain_addresses(address);
CREATE INDEX idx_chain_addresses_is_active ON chain_addresses(is_active);
```

### Transactions Table

```sql
CREATE TABLE transactions (
    -- Primary Key
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    
    -- Core Fields
    to_address VARCHAR(42),
    type INTEGER NOT NULL,           -- TransactionType enum
    chain VARCHAR(50) NOT NULL,      -- ChainType enum
    status INTEGER NOT NULL DEFAULT 0, -- TransactionStatus enum
    
    -- Asset Details
    asset_in VARCHAR(20),
    amount_in NUMERIC(30, 18),
    asset_out VARCHAR(20),
    amount_out NUMERIC(30, 18),
    
    -- Fees
    fee NUMERIC(30, 18),
    fee_usd NUMERIC(10, 2),
    
    -- On-chain Data
    tx_hash VARCHAR(66),
    block_number INTEGER,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    
    -- DEX Details
    dex_aggregator VARCHAR(50),
    dex_route JSONB,
    slippage NUMERIC(5, 2),
    error_message TEXT,
    
    -- Analytics Fields
    gas_used BIGINT,
    gas_price BIGINT,
    tx_metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints (same tx can appear for sender and receiver)
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

### Policies Table

```sql
CREATE TABLE policies (
    -- Privy policy ID as primary key
    id VARCHAR(255) PRIMARY KEY,
    
    -- Core Fields
    name VARCHAR(255) NOT NULL,
    version VARCHAR(32) NOT NULL,
    chain_type VARCHAR(32) NOT NULL,
    owner_id VARCHAR(255),
    
    -- Privy Data
    rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    privy_raw JSONB,
    
    -- Custom Metadata
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Sync Tracking
    last_privy_sync_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    
    -- Audit
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_policies_name ON policies(name);
CREATE INDEX idx_policies_chain_type ON policies(chain_type);
CREATE INDEX idx_policies_owner_id ON policies(owner_id);
CREATE INDEX idx_policies_is_deleted ON policies(is_deleted);
CREATE INDEX idx_policies_created_by_user_id ON policies(created_by_user_id);
CREATE INDEX idx_policies_last_privy_sync_at ON policies(last_privy_sync_at);
```

### Policy Audit Events Table

```sql
CREATE TABLE policy_audit_events (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    policy_id VARCHAR(255) NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Event Details
    action VARCHAR(64) NOT NULL,  -- CREATE, UPDATE, DELETE, SYNC
    payload JSONB,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_policy_audit_policy_id ON policy_audit_events(policy_id);
CREATE INDEX idx_policy_audit_actor ON policy_audit_events(actor_user_id);
CREATE INDEX idx_policy_audit_action ON policy_audit_events(action);
CREATE INDEX idx_policy_audit_created_at ON policy_audit_events(created_at);
```

---

## Value Objects

### WalletId

```python
@dataclass(frozen=True, repr=False)
class WalletId(ValueObject):
    value: int
```

### TransactionId

```python
@dataclass(frozen=True, repr=False)
class TransactionId(ValueObject):
    value: int
```

### AdditionalSigner

```python
@dataclass(frozen=True)
class AdditionalSigner:
    signer_id: str
    override_policy_ids: list[str] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        result = {"signer_id": self.signer_id}
        if self.override_policy_ids is not None:
            result["override_policy_ids"] = self.override_policy_ids
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "AdditionalSigner":
        return cls(
            signer_id=data.get("signer_id", ""),
            override_policy_ids=data.get("override_policy_ids"),
        )
```

---

## Repository Interfaces

### WalletRepository

**Location**: `src/app/domain/ports/wallet/wallet_repository.py`

```python
class WalletRepository(Protocol):
    # CRUD Operations
    async def get_by_id(self, wallet_id: WalletId) -> Wallet | None
    async def get_by_address(self, address: str) -> Wallet | None
    async def get_by_privy_wallet_id(self, privy_id: str) -> Wallet | None
    async def get_by_user_id(self, user_id: UserId) -> list[Wallet]
    async def get_by_user_and_address(self, user_id: UserId, address: str) -> Wallet | None
    async def get_by_user_and_provider(self, user_id: UserId, provider: WalletProvider) -> list[Wallet]
    
    async def save(self, wallet: Wallet) -> Wallet
    async def update(self, wallet: Wallet) -> Wallet
    async def upsert(self, user_id: UserId, address: str, provider: WalletProvider, ...) -> Wallet
    async def delete(self, wallet_id: WalletId) -> bool
    async def delete_by_user_and_address(self, user_id: UserId, address: str) -> bool
    
    # Audit
    async def mark_exported(self, privy_wallet_id: str) -> bool
    
    # Analytics
    async def count_all(self) -> int
    async def count_by_provider(self, provider: WalletProvider) -> int
    async def count_active_wallets(self) -> int
    async def get_wallet_counts_by_provider(self) -> dict[str, int]
    async def get_wallets_created_in_range(self, start: datetime, end: datetime) -> list[Wallet]
    async def count_wallets_created_in_range(self, start: datetime, end: datetime) -> int
    async def get_daily_wallet_counts(self, start: datetime, end: datetime) -> list[tuple[datetime, int]]
```

### TransactionRepository

**Location**: `src/app/domain/ports/transaction/transaction_repository.py`

```python
class TransactionRepository(Protocol):
    # CRUD Operations
    async def get_by_id(self, transaction_id: TransactionId) -> Transaction | None
    async def get_by_tx_hash(self, tx_hash: str) -> Transaction | None
    async def get_by_user_id(self, user_id: UserId, limit: int, offset: int) -> list[Transaction]
    async def get_by_wallet_id(self, wallet_id: WalletId, limit: int, offset: int) -> list[Transaction]
    
    async def save(self, transaction: Transaction) -> Transaction
    async def update(self, transaction: Transaction) -> Transaction
    async def update_status(self, tx_id: TransactionId, status: TransactionStatus) -> bool
    
    # Queries
    async def get_pending_transactions(self) -> list[Transaction]
    async def count_by_user(self, user_id: UserId) -> int
    async def count_by_status(self, status: TransactionStatus) -> int
```

---

## Factory Methods

### Wallet Creation

```python
# Create Privy embedded wallet
wallet = Wallet.create(
    user_id=UserId(123),
    address="0x1234567890abcdef1234567890abcdef12345678",
    provider=WalletProvider.PRIVY,
    default_chain=ChainType.ETHEREUM,
    privy_wallet_id="wallet_xyz",
    policy_ids=["policy_123"],
)

# Create imported wallet
wallet = Wallet.create_imported(
    user_id=UserId(123),
    address="0xabcdef1234567890abcdef1234567890abcdef12",
    default_chain=ChainType.ARBITRUM,
)
```

### Transaction Creation

```python
# Create SEND transaction
transaction = Transaction.create(
    user_id=UserId(123),
    wallet_id=WalletId(456),
    type=TransactionType.SEND,
    chain=ChainType.ETHEREUM,
    to_address="0xrecipient...",
)

# Create SWAP transaction
transaction = Transaction.create(
    user_id=UserId(123),
    wallet_id=WalletId(456),
    type=TransactionType.SWAP,
    chain=ChainType.ARBITRUM,
)
transaction.asset_in = "ETH"
transaction.amount_in = Decimal("1.5")
transaction.asset_out = "USDC"
transaction.amount_out = Decimal("3500")
transaction.dex_aggregator = "1inch"
```

---

## Data Flow Examples

### 1. Wallet Sync from Frontend

```
Frontend                    Backend                     Database
   │                           │                           │
   │  POST /wallet/sync        │                           │
   │  {wallets: [...]}     ───►│                           │
   │                           │  upsert(user_id,         │
   │                           │         address,          │
   │                           │         provider)     ───►│
   │                           │                           │
   │                           │◄─── Return wallet         │
   │◄───────────────────────────                           │
   │  {wallets: [...]}         │                           │
```

### 2. Transaction Logging

```
Frontend                    Backend                     Database
   │                           │                           │
   │  1. Send tx via Privy     │                           │
   │                           │                           │
   │  2. POST /transactions    │                           │
   │  {tx_hash, amount, ...}──►│                           │
   │                           │  save(transaction)    ───►│
   │                           │                           │
   │                           │◄─── Return tx_id          │
   │◄─── {id, status: PENDING} │                           │
   │                           │                           │
   │     [Later: Celery job]   │                           │
   │                           │  update_status(           │
   │                           │    tx_id, SUCCESS)    ───►│
```

### 3. Wallet Export Flow

```
Backend                     Privy API                   Database
   │                           │                           │
   │  Generate HPKE keys       │                           │
   │                           │                           │
   │  POST /wallets/{id}/export│                           │
   │  {recipient_public_key}──►│                           │
   │                           │                           │
   │◄─── {ciphertext,          │                           │
   │      encapsulated_key}    │                           │
   │                           │                           │
   │  Decrypt with HPKE        │                           │
   │                           │                           │
   │  mark_exported(wallet_id) ─────────────────────────►│
   │                           │                           │
   │  Return private_key       │                           │
```

---

## Analytics Queries

### Wallet Statistics

```python
# Total wallets
total = await wallet_repo.count_all()

# By provider
by_provider = await wallet_repo.get_wallet_counts_by_provider()
# {"privy": 150, "external": 50, "imported": 30}

# Active wallets
active = await wallet_repo.count_active_wallets()

# Daily creation counts
daily = await wallet_repo.get_daily_wallet_counts(start_date, end_date)
# [(2025-01-01, 10), (2025-01-02, 15), ...]
```

### Transaction Analytics

```python
# Pending transactions
pending = await tx_repo.get_pending_transactions()

# User transaction count
user_count = await tx_repo.count_by_user(user_id)

# By status
success_count = await tx_repo.count_by_status(TransactionStatus.SUCCESS)
failed_count = await tx_repo.count_by_status(TransactionStatus.FAILED)
```

---

## Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| **Entities** | `domain/entities/wallet.py` | Wallet entity |
| | `domain/entities/transaction.py` | Transaction entity |
| **Enums** | `domain/enums/wallet_provider.py` | Provider types |
| | `domain/enums/wallet_status.py` | Status codes |
| | `domain/enums/chain_type.py` | Blockchain networks |
| | `domain/enums/transaction_type.py` | Transaction types |
| | `domain/enums/transaction_status.py` | Transaction status |
| **Ports** | `domain/ports/wallet/wallet_repository.py` | Repository interface |
| | `domain/ports/transaction/transaction_repository.py` | Repository interface |
| **Adapters** | `infrastructure/adapters/wallet_repository_sqla.py` | SQLAlchemy impl |
| | `infrastructure/adapters/transaction_repository_sqla.py` | SQLAlchemy impl |
| **Mappings** | `infrastructure/persistence_sqla/mappings/wallet.py` | DB mapping |
| | `infrastructure/persistence_sqla/mappings/transaction.py` | DB mapping |
| | `infrastructure/persistence_sqla/mappings/policy.py` | Policy mapping |

---

## Best Practices

### Address Normalization

```python
# Always normalize addresses to lowercase
wallet.address = address.lower()
```

### Wallet ID for Imported Wallets

```python
# Generate synthetic ID for imported wallets
if provider == WalletProvider.IMPORTED:
    privy_wallet_id = f"imported:{address.lower()}"
```

### Transaction Uniqueness

```python
# Same tx_hash can appear for both sender and receiver
# Uniqueness is (user_id, tx_hash)
```

### Policy Sync

```python
# Always update last_privy_sync_at after Privy API calls
wallet.last_privy_sync_at = datetime.now(UTC)
```

---

**Last Updated**: January 2, 2026
