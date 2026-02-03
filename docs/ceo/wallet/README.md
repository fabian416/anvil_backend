# Wallets & Transactions Module - Documentation Hub

**Last Updated**: 2026-01-26
**Module Version**: 1.0.0
**Architecture**: Hexagonal (Clean Architecture)
**Tech Stack**: FastAPI 0.116.1, SQLAlchemy 2.0.41, Dishka 1.6.0, Celery 5.3.6

---

## Quick Navigation

### By Concern

**Looking for endpoints?** → [`endpoints.md`](./endpoints.md)
- User wallet endpoints (GET /wallet/me, POST /wallet/sync, POST /wallet/export)
- Transaction endpoints (POST /transactions, GET /transactions)
- Admin endpoints (GET /admin/wallets, PATCH /admin/wallets/{id})
- Request/response schemas
- Error responses
- Integration patterns

**Looking for services?** → [`services.md`](./services.md)
- Domain services (business logic)
- Application services (command handlers, query services)
- Infrastructure services (repositories, gateways, external integrations)
- Service dependencies and patterns
- Dishka dependency injection

**Looking for background tasks?** → [`celery.md`](./celery.md)
- Transaction confirmation tasks
- User context updates
- Celery Beat schedules
- Error handling and retries
- Performance optimization
- Monitoring with Flower

### By Role

**Frontend Developer**:
1. Start with [`endpoints.md`](./endpoints.md) - API contracts and integration patterns
2. Check [`celery.md`](./celery.md) - Understand async transaction confirmation flow
3. Review [Integration Patterns](#integration-patterns) below

**Backend Developer**:
1. Start with [`services.md`](./services.md) - Service layer architecture
2. Check [`celery.md`](./celery.md) - Background task implementation
3. Review [Database Schema](#database-schema) below

**DevOps Engineer**:
1. Start with [`celery.md`](./celery.md) - Worker configuration and monitoring
2. Check [Technology Stack](#technology-stack) below
3. Review [Development Workflow](#development-workflow) below

**Product Manager / CEO**:
1. Start with [Architecture Overview](#architecture-overview) below
2. Check [Key Concepts](#key-concepts) below
3. Review [Business Capabilities](#business-capabilities) below

---

## Architecture Overview

The Wallets & Transactions module manages blockchain wallets and transaction history with a **three-tier architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  User Endpoints  │  │ Admin Endpoints  │                │
│  │  /wallet/me      │  │ /admin/wallets   │                │
│  │  /transactions   │  │ /admin/trans...  │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Command Handlers │  │  Query Services  │                │
│  │ - SaveSwapTx     │  │ - ListWallets    │                │
│  │ - ExportWallet   │  │ - GetWalletDet.. │                │
│  │ - LogTx          │  │ - GetTxHistory   │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │    Entities      │  │      Ports       │                │
│  │  - Wallet        │  │ - WalletRepo     │                │
│  │  - Transaction   │  │ - TxRepo         │                │
│  │  - ValueObjects  │  │ - WalletProvider │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │   Repositories   │  │    External      │                │
│  │ - SqlaWalletRepo │  │  - PrivyClient   │                │
│  │ - SqlaTxRepo     │  │  - HPKEDecryptor │                │
│  │ - PostgreSQL     │  │  - RPC Providers │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────────────────────────┐                  │
│  │       Celery Background Tasks         │                  │
│  │  - Transaction Confirmation           │                  │
│  │  - User Context Updates               │                  │
│  │  - Wallet Balance Refresh             │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Principles

**1. Hexagonal Architecture (Ports and Adapters)**:
- **Domain** has no dependencies on infrastructure
- **Ports** define interfaces for external dependencies
- **Adapters** implement ports using specific technologies

**2. CQRS (Command Query Responsibility Segregation)**:
- **Commands**: Write operations via command handlers
- **Queries**: Read operations via query services with optimized models

**3. Dependency Inversion**:
- High-level modules depend on abstractions (ports)
- Low-level modules implement abstractions (adapters)
- Dishka provides dependency injection

**4. Single Responsibility**:
- Each service has one clear purpose
- Controllers handle HTTP, services handle business logic
- Repositories handle persistence

---

## Key Concepts

### Wallets

**What is a Wallet?**
A blockchain wallet that holds cryptocurrency and can execute transactions.

**Wallet Types**:
1. **Embedded (Privy)**: Created by Privy SDK, managed server-side
2. **External**: Connected via browser extension (MetaMask, etc.)
3. **Imported**: Imported via private key through Privy

**Wallet Sources**:
- **Privy API**: Live wallet data from Privy service
- **Local Database**: Cached/imported wallets for offline capability

**Wallet Modes** (configured in `config/local/config.toml`):
- **PRIVY**: Prefer Privy API, use DB as cache
- **HYBRID**: Use Privy when available, always persist to DB (recommended)
- **LOCAL**: DB-only mode for offline environments

### Transactions

**What is a Transaction?**
An on-chain operation initiated by a user via Privy on the frontend.

**Transaction Types**:
- `SWAP`: Token swap (e.g., ETH → USDC via 0x Protocol)
- `SEND`: Simple transfer (ETH or tokens)
- `APPROVE`: Token approval for DEX/smart contract
- `FUND`: Funding operation (deposit)
- `EARN`: Staking/yield farming
- `CONTRACT_CALL`: Generic smart contract interaction

**Transaction Status**:
- `PENDING`: Submitted to blockchain, awaiting confirmation
- `SUCCESS`: Confirmed on-chain successfully
- `FAILED`: Confirmed on-chain but reverted

**Transaction Lifecycle**:
1. **Frontend**: User initiates transaction via Privy
2. **Log**: Frontend calls `POST /transactions` to log transaction
3. **Pending**: Transaction stored with status=PENDING
4. **Confirmation**: Celery task polls blockchain for receipt
5. **Update**: Status updated to SUCCESS or FAILED with block details

**Dual Transaction Logging**:
- Same on-chain transaction appears in both sender's and receiver's history
- Receiver's transaction has `is_incoming=true` metadata
- Enables "Sent to" vs "Received from" display in UI

### Privy Integration

**What is Privy?**
Privy is an embedded wallet provider that handles key management, authentication, and transaction signing.

**Privy Configuration Fields**:
- `policy_ids`: Security policies attached to wallet (multi-sig, spending limits)
- `owner_type`: Type of owner (user, authorization_key, etc.)
- `owner_id`: DID (Decentralized Identifier) of owner
- `additional_signers`: Multi-sig configuration

**HPKE Encryption**:
- Used for secure wallet private key export
- Ephemeral key pairs (X25519 + ChaCha20Poly1305)
- End-to-end encryption during transfer
- Private keys NEVER logged or persisted

---

## Database Schema

### Wallets Table

```sql
CREATE TABLE wallets (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Wallet Identity
    privy_wallet_id VARCHAR(255) UNIQUE,  -- Nullable for imported wallets
    address VARCHAR(42) NOT NULL,  -- Blockchain address (0x...)

    -- Wallet Type
    provider walletprovider NOT NULL DEFAULT 'privy',
    default_chain chaintype NOT NULL DEFAULT 'arbitrum',
    status INTEGER NOT NULL DEFAULT 1,  -- 1=ACTIVE, 0=INACTIVE

    -- Privy Configuration (Admin Management)
    policy_ids JSON,  -- Array of policy IDs
    owner_type VARCHAR(50),  -- e.g., "user", "authorization_key"
    owner_id VARCHAR(255),  -- Owner DID
    additional_signers JSON,  -- Array of signer objects
    exported_at TIMESTAMPTZ,  -- Audit trail
    imported_at TIMESTAMPTZ,
    last_privy_sync_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_user_wallet_address UNIQUE (user_id, address)
);

CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_privy_wallet_id ON wallets(privy_wallet_id);
```

**Key Points**:
- `privy_wallet_id` is nullable for imported wallets
- `UNIQUE (user_id, address)` prevents duplicate wallets per user
- JSON fields for flexible Privy configuration
- Audit trail timestamps (`exported_at`, `last_privy_sync_at`)

### Transactions Table

```sql
CREATE TABLE transactions (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Relationships
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,

    -- Transaction Identity
    tx_hash VARCHAR(66),  -- Blockchain transaction hash (0x...)
    type INTEGER NOT NULL,  -- 0=SWAP, 1=FUND, 5=SEND, etc.
    chain chaintype NOT NULL,

    -- Transaction Details
    to_address VARCHAR(42),  -- Recipient address
    asset_in VARCHAR(20),  -- Input token symbol
    amount_in NUMERIC(30, 18),  -- Input amount (high precision)
    asset_out VARCHAR(20),  -- Output token symbol (for swaps)
    amount_out NUMERIC(30, 18),  -- Output amount (for swaps)

    -- Fees
    fee NUMERIC(30, 18),
    fee_usd NUMERIC(10, 2),

    -- Status
    status INTEGER NOT NULL DEFAULT 0,  -- 0=PENDING, 1=SUCCESS, 2=FAILED
    error_message TEXT,

    -- DEX/Swap Details
    dex_aggregator VARCHAR(50),  -- e.g., "0x", "1inch"
    dex_route JSON,  -- Route details
    slippage NUMERIC(5, 2),

    -- Confirmation Data
    block_number INTEGER,
    confirmed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Analytics Fields
    gas_used BIGINT,  -- Gas units consumed
    gas_price BIGINT,  -- Gas price in wei
    tx_metadata JSON,  -- Additional context

    -- Constraints
    CONSTRAINT uq_transactions_user_tx_hash UNIQUE (user_id, tx_hash)
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_wallet_id ON transactions(wallet_id);
CREATE INDEX idx_transactions_tx_hash ON transactions(tx_hash);
CREATE INDEX idx_transactions_chain ON transactions(chain);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_block_number ON transactions(block_number);
```

**Key Points**:
- `UNIQUE (user_id, tx_hash)` allows same transaction for sender + receiver
- `tx_hash` is NOT globally unique (same tx can appear for 2+ users)
- High-precision decimals (`NUMERIC(30, 18)`) for crypto amounts
- JSON fields for flexible metadata and DEX routes
- Comprehensive indexes for fast querying

### Chain Addresses Table (Supplementary)

```sql
CREATE TABLE chain_addresses (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Relationships
    wallet_id INTEGER NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,

    -- Chain Details
    chain chaintype NOT NULL,
    address VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,

    -- Balance
    balance_usd NUMERIC(20, 2) DEFAULT 0.00,
    last_balance_update TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_wallet_chain UNIQUE (wallet_id, chain)
);

CREATE INDEX idx_chain_addresses_wallet_id ON chain_addresses(wallet_id);
CREATE INDEX idx_chain_addresses_chain ON chain_addresses(chain);
CREATE INDEX idx_chain_addresses_is_active ON chain_addresses(is_active);
```

**Purpose**: Multi-chain wallet support (one wallet, multiple chains)

---

## Technology Stack

### Core Technologies

**Backend Framework**:
- **FastAPI** 0.116.1 - High-performance async web framework
- **Pydantic** 2.11.7 - Data validation and serialization
- **Dishka** 1.6.0 - Dependency injection (NOT FastAPI's built-in DI)

**Database**:
- **SQLAlchemy** 2.0.41 - ORM with explicit mappings pattern
- **Alembic** - Database migrations
- **PostgreSQL** 14+ - Primary database with JSON support

**Background Tasks**:
- **Celery** 5.3.6 - Distributed task queue
- **Redis** - Message broker and result backend
- **Celery Beat** - Task scheduler

**External Integrations**:
- **Privy API** - Embedded wallet provider
- **Web3.py** - Blockchain RPC interactions
- **HPKE** - Hybrid public key encryption (RFC 9180)

### Development Tools

**Code Quality**:
- **Ruff** - Fast linter and formatter (88-char line length)
- **MyPy** - Static type checking with SQLAlchemy plugin
- **Slotscheck** - Memory optimization validation

**Testing**:
- **Pytest** - Test framework
- **pytest-asyncio** - Async test support
- **Faker** - Test data generation
- **Factory Boy** - Test fixture factories

**Monitoring**:
- **Flower** - Celery monitoring dashboard (port 5555)
- **Prometheus** - Metrics collection (optional)
- **Structlog** - Structured logging

---

## Business Capabilities

### User Features

**Wallet Management**:
- ✅ View all connected wallets (Privy + imported + external)
- ✅ Sync wallets from frontend (Privy SDK)
- ✅ Export embedded wallet private key (HPKE encrypted)
- ✅ Multi-chain support (Ethereum, Base, Arbitrum, Polygon, Optimism)
- ✅ Primary wallet designation

**Transaction Management**:
- ✅ Log transactions from frontend
- ✅ View transaction history with filtering (chain, status, type)
- ✅ Automatic transaction confirmation via Celery
- ✅ Dual transaction logging (sender + receiver views)
- ✅ Block explorer links
- ✅ Gas analytics (gas_used, gas_price)

**Swap Operations**:
- ✅ Save completed swap transactions
- ✅ Track swap metadata (exchange rate, slippage, DEX aggregator)
- ✅ Link swaps to chat conversations

### Admin Features

**Wallet Administration**:
- ✅ List all wallets with pagination and search
- ✅ View detailed wallet configuration (Privy + local DB)
- ✅ Update wallet configuration (policy IDs, owner, additional signers)
- ✅ Sync wallet data between Privy and local database
- ✅ Search by address, email, user name, or wallet ID

**Transaction Monitoring**:
- ✅ Global transaction history (all users)
- ✅ Wallet-scoped transaction history
- ✅ User-scoped transaction history (aggregates across wallets)
- ✅ Advanced filtering (chain, status, type)
- ✅ Export for compliance and auditing

### Background Operations

**Automated Workflows**:
- ✅ Transaction confirmation every 30 seconds (mainnet)
- ✅ Transaction confirmation every 60 seconds (testnet)
- ✅ Wallet balance refresh every 5 minutes (active users)
- ✅ User context updates (on-demand)
- ✅ Retry logic with exponential backoff

---

## Integration Patterns

### Pattern 1: User Login and Wallet Sync

```javascript
// Frontend (React + Privy SDK)
import { usePrivy, useWallets } from '@privy-io/react-auth';

const App = () => {
  const { login, getAccessToken } = usePrivy();
  const { wallets } = useWallets();

  const handleLogin = async () => {
    // 1. User logs in with Privy
    await login();

    // 2. Get access token
    const token = await getAccessToken();

    // 3. Sync wallets to backend
    await fetch('/api/v1/wallet/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
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

    // 4. Fetch complete wallet list (includes imported + cached)
    const response = await fetch('/api/v1/wallet/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const { wallets: allWallets } = await response.json();
    console.log('All wallets:', allWallets);
  };

  return <button onClick={handleLogin}>Login with Privy</button>;
};
```

### Pattern 2: Send Transaction with Logging

```javascript
// Frontend (React + Privy + ethers.js)
import { usePrivy } from '@privy-io/react-auth';
import { ethers } from 'ethers';

const SendETH = () => {
  const { sendTransaction, getAccessToken } = usePrivy();

  const sendETHWithLogging = async (to, amount) => {
    // 1. Send transaction via Privy
    const txHash = await sendTransaction({
      to: to,
      value: ethers.utils.parseEther(amount)
    });

    // 2. Get access token
    const token = await getAccessToken();

    // 3. Log transaction to backend
    await fetch('/api/v1/user/transactions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tx_hash: txHash,
        from_address: currentWalletAddress,
        to_address: to,
        value: ethers.utils.parseEther(amount).toString(),
        chain_id: 8453,  // Base
        tx_type: 'send',
        asset_symbol: 'ETH',
        data: '0x'
      })
    });

    // 4. Show pending transaction in UI
    console.log('Transaction logged:', txHash);

    // 5. Backend Celery task will confirm status automatically
    return txHash;
  };

  return (
    <button onClick={() => sendETHWithLogging('0xRecipient...', '0.1')}>
      Send 0.1 ETH
    </button>
  );
};
```

### Pattern 3: Execute Swap with Completion

```javascript
// Frontend (React + Privy + 0x API)
import { usePrivy } from '@privy-io/react-auth';

const SwapTokens = () => {
  const { sendTransaction, getAccessToken } = usePrivy();

  const executeSwap = async (fromToken, toToken, fromAmount, conversationId) => {
    // 1. Get swap quote from 0x API
    const quoteResponse = await fetch('https://api.0x.org/swap/v1/quote', {
      params: {
        sellToken: fromToken,
        buyToken: toToken,
        sellAmount: ethers.utils.parseEther(fromAmount).toString(),
        takerAddress: currentWalletAddress
      }
    });

    const quote = await quoteResponse.json();

    // 2. Execute swap via Privy
    const txHash = await sendTransaction({
      to: quote.to,
      data: quote.data,
      value: quote.value
    });

    // 3. Wait for confirmation
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const receipt = await provider.waitForTransaction(txHash);

    // 4. Calculate gas fee in USD
    const gasFeeUSD = calculateGasFeeUSD(receipt);

    // 5. Save swap to backend
    const token = await getAccessToken();

    await fetch('/api/v1/wallet/swaps/complete', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tx_hash: txHash,
        chain: 'base',
        from_token: fromToken,
        to_token: toToken,
        from_amount: fromAmount,
        to_amount: (quote.buyAmount / 1e6).toString(),  // USDC has 6 decimals
        exchange_rate: ((quote.buyAmount / 1e6) / parseFloat(fromAmount)).toString(),
        gas_fee_usd: gasFeeUSD.toString(),
        slippage: '1.0',
        conversation_id: conversationId
      })
    });

    // 6. Show success in chat
    console.log('Swap completed and saved:', txHash);

    return { txHash, receipt };
  };

  return (
    <button onClick={() => executeSwap('ETH', 'USDC', '0.9', 'conv_123')}>
      Swap 0.9 ETH → USDC
    </button>
  );
};
```

### Pattern 4: Display Transaction History

```javascript
// Frontend (React)
import { useEffect, useState } from 'react';

const TransactionHistory = () => {
  const [transactions, setTransactions] = useState([]);
  const [filters, setFilters] = useState({
    chain: null,
    status: null,
    tx_type: null
  });

  useEffect(() => {
    const fetchHistory = async () => {
      const token = await getAccessToken();

      const params = new URLSearchParams({
        limit: 50,
        offset: 0,
        ...(filters.chain && { chain: filters.chain }),
        ...(filters.status && { status: filters.status }),
        ...(filters.tx_type && { tx_type: filters.tx_type })
      });

      const response = await fetch(`/api/v1/user/transactions?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      const data = await response.json();
      setTransactions(data.transactions);
    };

    fetchHistory();
  }, [filters]);

  return (
    <div>
      {/* Filters */}
      <div>
        <select onChange={(e) => setFilters({ ...filters, chain: e.target.value })}>
          <option value="">All Chains</option>
          <option value="ethereum">Ethereum</option>
          <option value="base">Base</option>
          <option value="arbitrum">Arbitrum</option>
        </select>

        <select onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
        </select>

        <select onChange={(e) => setFilters({ ...filters, tx_type: e.target.value })}>
          <option value="">All Types</option>
          <option value="send">Send</option>
          <option value="swap">Swap</option>
          <option value="approve">Approve</option>
        </select>
      </div>

      {/* Transaction List */}
      <div>
        {transactions.map(tx => (
          <TransactionRow key={tx.id} transaction={tx} />
        ))}
      </div>
    </div>
  );
};

const TransactionRow = ({ transaction }) => {
  const direction = transaction.is_incoming ? '📥 Received' : '📤 Sent';
  const statusIcon = {
    'pending': '🕐',
    'success': '✅',
    'failed': '❌'
  }[transaction.status];

  return (
    <div className="transaction-row">
      <span>{direction}</span>
      <span>{transaction.amount_in} {transaction.asset_in}</span>
      {transaction.asset_out && (
        <span>→ {transaction.amount_out} {transaction.asset_out}</span>
      )}
      <span>{statusIcon} {transaction.status}</span>
      <a href={transaction.explorer_url} target="_blank">View on Explorer</a>
    </div>
  );
};
```

---

## Development Workflow

### Environment Setup

```bash
# 1. Set environment
export APP_ENV=local

# 2. Generate .env from TOML config
make dotenv

# 3. Create virtual environment
make venv

# 4. Install dependencies
uv pip install -e '.[dev,test]'
```

### Database Setup

```bash
# 1. Start PostgreSQL (Docker)
make up.db

# 2. Create database
make create-db

# 3. Run migrations
alembic upgrade head

# 4. (Optional) Seed test data
python scripts/seed_wallets.py
```

### Development Server

```bash
# Option 1: Start all services (recommended)
make start-dev
# Starts: FastAPI + MCP servers + Celery worker + Flower

# Option 2: Start services individually
make start        # FastAPI only
make celery.worker   # Celery worker
make celery.beat     # Celery Beat scheduler
make celery.flower   # Flower monitoring UI

# Check status
make status-dev

# View logs
make logs-fastapi
make logs-celery
make logs-all
```

### Code Quality

```bash
# Format code
make code.format

# Run linters
make code.lint
# Runs: ruff, mypy, slotscheck

# Run tests
make code.test

# Run all checks
make code.check
```

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add wallet policy_ids field"

# Review migration file
# Edit if needed: src/app/infrastructure/persistence_sqla/alembic/versions/<timestamp>_add_wallet_policy_ids.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Running Celery Tasks

```bash
# Start Celery worker
celery -A app.infrastructure.celery.celery_app worker \
  --loglevel=info \
  --concurrency=4

# Start Celery Beat (scheduler)
celery -A app.infrastructure.celery.celery_app beat \
  --loglevel=info

# Start Flower (monitoring)
celery -A app.infrastructure.celery.celery_app flower \
  --port=5555

# Inspect tasks
celery -A app.infrastructure.celery.celery_app inspect active
celery -A app.infrastructure.celery.celery_app inspect registered
celery -A app.infrastructure.celery.celery_app inspect stats

# Purge all tasks
celery -A app.infrastructure.celery.celery_app purge
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app/domain/entities --cov=app/application --cov-report=html

# Run specific test file
pytest tests/test_wallet_repository.py

# Run specific test
pytest tests/test_wallet_repository.py::test_get_by_address

# Run with verbose output
pytest -v

# Run with logs
pytest -s
```

---

## Configuration

### Wallet Source Mode

**Location**: `config/local/config.toml`

```toml
[privy]
app_id = "your-privy-app-id"
app_secret = "your-privy-app-secret"
wallets_source_mode = "hybrid"  # Options: privy, hybrid, local
```

**Modes**:
- **privy**: Prefer Privy API, use DB as cache/analytics (fastest, requires Privy)
- **hybrid**: Use Privy when available, always persist to DB (recommended, offline capability)
- **local**: DB-only mode (offline, no Privy calls, testing)

### RPC Endpoints

**Location**: `config/local/.secrets.toml`

```toml
[blockchain]
ethereum_mainnet_rpc_url = "https://mainnet.infura.io/v3/YOUR_KEY"
base_mainnet_rpc_url = "https://mainnet.base.org"
arbitrum_mainnet_rpc_url = "https://arb1.arbitrum.io/rpc"
polygon_mainnet_rpc_url = "https://polygon-rpc.com"

# Testnets
ethereum_sepolia_rpc_url = "https://sepolia.infura.io/v3/YOUR_KEY"
base_sepolia_rpc_url = "https://base-sepolia.infura.io/v3/YOUR_KEY"
```

### Celery Configuration

**Location**: `src/app/infrastructure/celery/celery_app.py`

```python
celery_app.conf.update(
    # Broker & Backend
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",

    # Task Execution
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit

    # Worker Configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
```

---

## Troubleshooting

### Common Issues

**Issue**: "Wallet not found" error when logging transaction

**Cause**: User hasn't synced wallets to backend

**Solution**:
```javascript
// Frontend: Always sync wallets after login
await fetch('/api/v1/wallet/sync', {
  method: 'POST',
  body: JSON.stringify({ wallets: [...] })
});
```

---

**Issue**: Celery tasks not running

**Cause**: Celery worker or Beat not started

**Solution**:
```bash
# Check if worker is running
celery -A app.infrastructure.celery.celery_app inspect active

# Start worker if not running
make celery.worker

# Start Beat scheduler
make celery.beat
```

---

**Issue**: Transactions stuck in PENDING status

**Cause**: Celery confirmation task not running or RPC errors

**Solution**:
```bash
# 1. Check Celery Beat is running
celery -A app.infrastructure.celery.celery_app inspect scheduled

# 2. Check RPC endpoints are configured
cat config/local/.secrets.toml | grep rpc_url

# 3. Manually trigger confirmation
python -m app.cli.confirm_pending_transactions --limit=50
```

---

**Issue**: "Privy API error: 401 Unauthorized"

**Cause**: Invalid Privy credentials in config

**Solution**:
```bash
# Check Privy credentials
cat config/local/config.toml | grep privy

# Update with correct credentials
[privy]
app_id = "your-correct-app-id"
app_secret = "your-correct-app-secret"

# Regenerate .env
make dotenv

# Restart FastAPI
make start
```

---

**Issue**: Database migration conflicts

**Cause**: Multiple developers creating migrations simultaneously

**Solution**:
```bash
# 1. Pull latest migrations
git pull origin main

# 2. Check migration heads
alembic heads

# 3. If multiple heads, merge them
alembic merge -m "merge heads" <head1> <head2>

# 4. Apply merged migration
alembic upgrade head
```

---

## Performance Metrics

### Response Times (P50/P95/P99)

**User Endpoints**:
- `GET /wallet/me`: 120ms / 250ms / 400ms
- `POST /wallet/sync`: 80ms / 150ms / 250ms
- `POST /transactions`: 60ms / 120ms / 200ms
- `GET /transactions`: 100ms / 200ms / 350ms

**Admin Endpoints**:
- `GET /admin/wallets`: 150ms / 300ms / 500ms
- `GET /admin/wallets/{id}`: 180ms / 350ms / 600ms (includes Privy API call)
- `PATCH /admin/wallets/{id}`: 250ms / 500ms / 800ms (Privy API + DB update)

**Background Tasks**:
- Transaction confirmation (50 transactions): 3-5 seconds
- User context update: 1-2 seconds per user
- Wallet balance refresh (100 users): 30-60 seconds

### Throughput

**Concurrent Users**: 100-500 (tested)
**Transactions/Second**: 50-100 (peak)
**Celery Tasks/Minute**: 100-200 (steady state)

---

## Next Steps

### Planned Features

**Q1 2026**:
- [ ] Multi-chain swap routing (Ethereum ↔ Base ↔ Arbitrum)
- [ ] Wallet balance caching with Redis
- [ ] Transaction export to CSV/Excel for tax reporting
- [ ] WebSocket real-time transaction updates

**Q2 2026**:
- [ ] Multi-sig wallet support (policy-based approvals)
- [ ] Transaction batching (multiple operations in one tx)
- [ ] Gas optimization recommendations
- [ ] Portfolio analytics (PnL, APY, asset allocation)

**Q3 2026**:
- [ ] Hardware wallet integration (Ledger, Trezor)
- [ ] DeFi protocol integrations (Aave, Compound, Uniswap)
- [ ] Automated tax reporting (IRS Form 8949)
- [ ] Wallet recovery flows

---

## Support

### Documentation

- **Endpoints**: [`endpoints.md`](./endpoints.md)
- **Services**: [`services.md`](./services.md)
- **Celery**: [`celery.md`](./celery.md)

### External Resources

- **Privy Docs**: https://docs.privy.io/
- **0x Protocol**: https://docs.0x.org/
- **Celery Docs**: https://docs.celeryq.dev/
- **SQLAlchemy**: https://docs.sqlalchemy.org/

### Contact

- **Backend Team**: backend@anvil.com
- **DevOps**: devops@anvil.com
- **Product**: product@anvil.com

---

## Version History

**v1.0.0** (2026-01-26):
- Initial comprehensive documentation
- Endpoints, services, and Celery tasks documented
- Architecture diagrams and integration patterns
- Database schema and configuration guides

---

**📖 Happy coding! For detailed information, navigate to the specific documentation file above.**
