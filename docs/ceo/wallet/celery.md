# Wallets & Transactions - Celery Background Tasks Documentation

**Last Updated**: 2026-01-26
**Module**: Wallets & Transactions
**Tech Stack**: Celery 5.3.6, Redis, PostgreSQL

---

## Table of Contents

1. [Overview](#overview)
2. [Task Registry](#task-registry)
3. [Transaction Confirmation Tasks](#transaction-confirmation-tasks)
4. [User Context Tasks](#user-context-tasks)
5. [Celery Beat Schedule](#celery-beat-schedule)
6. [Task Configuration](#task-configuration)
7. [Error Handling and Retries](#error-handling-and-retries)
8. [Performance Optimization](#performance-optimization)
9. [Monitoring and Observability](#monitoring-and-observability)

---

## Overview

The Wallets & Transactions module uses **Celery** for asynchronous background processing of blockchain-related tasks. These tasks handle:

1. **Transaction Confirmation**: Polling blockchain for transaction status updates
2. **User Context Updates**: Syncing wallet balances and transaction history
3. **Scheduled Jobs**: Periodic cleanup, analytics, health checks

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  (Receives transaction logs, triggers async tasks)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Enqueue Task
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Redis Message Broker                     │
│  (Task queue, result backend, distributed locks)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Dequeue Task
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Celery Workers                          │
│  - confirm_pending_transactions_task                        │
│  - update_user_context_task                                 │
│  - wallet_balance_refresh_task                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Read/Write
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   PostgreSQL Database                        │
│  (Wallets, Transactions, User Context)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ RPC Calls
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Blockchain RPC Nodes                        │
│  (Ethereum, Base, Arbitrum, Polygon, etc.)                  │
└─────────────────────────────────────────────────────────────┘
```

### Celery Configuration

**Broker**: Redis (localhost:6379/0)
**Result Backend**: Redis (localhost:6379/0)
**Task Serializer**: JSON
**Result Serializer**: JSON
**Accept Content**: JSON only (security)

**Location**: `/src/app/infrastructure/celery/celery_app.py`

```python
from celery import Celery

celery_app = Celery(
    "anvil_backend",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes (warning)
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True
)
```

---

## Task Registry

All Celery tasks for wallets and transactions:

| Task Name | Queue | Trigger | Frequency | Purpose |
|-----------|-------|---------|-----------|---------|
| `confirm_pending_transactions` | default | Beat schedule | Every 30 seconds | Confirm pending transactions |
| `confirm_pending_transactions_testnet` | default | Beat schedule | Every 60 seconds | Confirm testnet transactions |
| `confirm_pending_transactions_mainnet` | default | Beat schedule | Every 30 seconds | Confirm mainnet transactions |
| `update_user_context` | default | Event-driven | On-demand | Refresh user wallet balances |
| `wallet_balance_refresh` | low_priority | Beat schedule | Every 5 minutes | Batch wallet balance updates |

**Task Locations**:
- `transaction_confirmation_tasks.py`: Transaction confirmation logic
- `user_context_tasks.py`: User context and balance updates

---

## Transaction Confirmation Tasks

### Overview

Transaction confirmation tasks poll blockchain RPC nodes to update transaction status from `PENDING` to `SUCCESS` or `FAILED`.

**Location**: `/src/app/infrastructure/celery/tasks/transaction_confirmation_tasks.py`

### confirm_pending_transactions_task

**Purpose**: Main task to confirm pending transactions by querying blockchain RPC.

**Task Configuration**:
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
    Celery task to confirm pending transactions on-chain.

    Args:
        limit: Maximum transactions to process per batch (default: 50)
        older_than_seconds: Only process transactions older than this (default: 10)
        use_testnet: Override testnet setting (None uses config default)

    Returns:
        Dictionary with processing summary:
        - status: "success" or "error"
        - transactions_processed: Number of transactions checked
        - confirmed: Number confirmed as successful
        - failed: Number confirmed as failed
        - still_pending: Number still pending
        - duration_seconds: Total processing time
    """
```

**Business Logic Flow**:

1. **Import Core Logic**:
```python
# Lines 45-46: Import confirmation logic
from app.cli.confirm_pending_transactions import run_once
```

2. **Execute Async Function**:
```python
# Lines 54-61: Run async confirmation logic in event loop
result = asyncio.run(
    run_once(
        limit=limit,
        older_than_seconds=older_than_seconds,
        use_testnet=use_testnet,
    )
)
```

3. **Build Summary**:
```python
# Lines 63-71: Build summary dictionary
summary = {
    "status": "success",
    "transactions_processed": result.transactions_processed,
    "confirmed": result.confirmed,
    "failed": result.failed,
    "still_pending": result.still_pending,
    "duration_seconds": result.duration_seconds,
}
```

4. **Error Handling**:
```python
# Lines 80-82: Log and re-raise errors
except Exception as e:
    logger.error(f"[Celery] Transaction confirmation failed: {e}")
    raise
```

**Return Value Example**:
```json
{
  "status": "success",
  "transactions_processed": 25,
  "confirmed": 20,
  "failed": 2,
  "still_pending": 3,
  "duration_seconds": 4.2
}
```

**Trigger**: Celery Beat (scheduled every 30 seconds)

**Queue**: default

**Retry Policy**:
- Max retries: 3
- Retry delay: 60 seconds
- Backoff: Exponential (60s → 120s → 240s)
- Auto-retry on all exceptions

---

### confirm_pending_transactions_testnet_task

**Purpose**: Convenience task for testnet-only confirmation.

**Task Configuration**:
```python
@shared_task(name="confirm_pending_transactions_testnet")
def confirm_pending_transactions_testnet_task(
    limit: int = 50,
) -> dict[str, Any]:
    """
    Convenience task for testnet confirmation.

    Always uses testnet RPC endpoints (Sepolia, Base Sepolia).

    Args:
        limit: Maximum transactions to process (default: 50)

    Returns:
        Processing summary dictionary
    """
    return confirm_pending_transactions_task(
        limit=limit,
        use_testnet=True,
    )
```

**RPC Endpoints Used**:
- Ethereum Sepolia: `https://sepolia.infura.io/v3/...`
- Base Sepolia: `https://base-sepolia.infura.io/v3/...`

**Trigger**: Celery Beat (scheduled every 60 seconds)

**Queue**: default

---

### confirm_pending_transactions_mainnet_task

**Purpose**: Convenience task for mainnet-only confirmation.

**Task Configuration**:
```python
@shared_task(name="confirm_pending_transactions_mainnet")
def confirm_pending_transactions_mainnet_task(
    limit: int = 50,
) -> dict[str, Any]:
    """
    Convenience task for mainnet confirmation.

    Uses mainnet RPC endpoints (Ethereum, Base, etc.).

    Args:
        limit: Maximum transactions to process (default: 50)

    Returns:
        Processing summary dictionary
    """
    return confirm_pending_transactions_task(
        limit=limit,
        use_testnet=False,
    )
```

**RPC Endpoints Used**:
- Ethereum: `https://mainnet.infura.io/v3/...`
- Base: `https://mainnet.base.org`
- Arbitrum: `https://arb1.arbitrum.io/rpc`
- Polygon: `https://polygon-rpc.com`
- Optimism: `https://mainnet.optimism.io`

**Trigger**: Celery Beat (scheduled every 30 seconds)

**Queue**: default

---

### Core Confirmation Logic

The actual confirmation logic is in `/src/app/cli/confirm_pending_transactions.py`:

**Location**: `/src/app/cli/confirm_pending_transactions.py`

**Entry Point**:
```python
async def run_once(
    limit: int = 50,
    older_than_seconds: int = 10,
    use_testnet: bool | None = None,
) -> ConfirmationResult:
    """
    Confirm pending transactions once.

    Args:
        limit: Maximum transactions to process
        older_than_seconds: Only process transactions older than this
        use_testnet: Use testnet RPC endpoints if True

    Returns:
        ConfirmationResult with processing summary
    """
```

**Processing Flow**:

1. **Fetch Pending Transactions**:
```python
# Get pending transactions from database
transactions = await transaction_repository.get_pending_transactions(
    limit=limit,
    older_than_seconds=older_than_seconds
)

logger.info(f"Found {len(transactions)} pending transactions to confirm")
```

2. **Group by Chain**:
```python
# Group transactions by blockchain for batching
transactions_by_chain = {}
for tx in transactions:
    chain = tx.chain
    if chain not in transactions_by_chain:
        transactions_by_chain[chain] = []
    transactions_by_chain[chain].append(tx)
```

3. **Get RPC Providers**:
```python
# Get RPC provider for each chain
providers = {}
for chain in transactions_by_chain.keys():
    provider = get_rpc_provider(chain, use_testnet=use_testnet)
    providers[chain] = provider
```

4. **Check Transaction Status**:
```python
for chain, txs in transactions_by_chain.items():
    provider = providers[chain]

    for tx in txs:
        try:
            # Get transaction receipt from blockchain
            receipt = await provider.get_transaction_receipt(tx.tx_hash)

            if receipt is None:
                # Transaction not yet mined
                still_pending += 1
                continue

            # Update transaction status based on receipt
            if receipt.status == 1:
                # Success
                await transaction_repository.update_status(
                    transaction_id=tx.id_,
                    status=TransactionStatus.SUCCESS,
                    block_number=receipt.block_number,
                    confirmed_at=datetime.now(UTC),
                    gas_used=receipt.gas_used,
                    gas_price=receipt.effective_gas_price
                )
                confirmed += 1

            else:
                # Failed
                await transaction_repository.update_status(
                    transaction_id=tx.id_,
                    status=TransactionStatus.FAILED,
                    block_number=receipt.block_number,
                    confirmed_at=datetime.now(UTC),
                    error_message="Transaction reverted"
                )
                failed += 1

        except Exception as e:
            logger.error(f"Error confirming transaction {tx.id_.value}: {e}")
            errors += 1
```

5. **Return Summary**:
```python
return ConfirmationResult(
    transactions_processed=len(transactions),
    confirmed=confirmed,
    failed=failed,
    still_pending=still_pending,
    errors=errors,
    duration_seconds=time.time() - start_time
)
```

**RPC Provider Configuration**:
```python
# src/app/infrastructure/blockchain/rpc_providers.py

def get_rpc_provider(chain: ChainType, use_testnet: bool = False):
    """Get Web3 provider for blockchain RPC."""
    if use_testnet:
        rpc_urls = {
            ChainType.ETHEREUM: os.getenv("ETHEREUM_SEPOLIA_RPC_URL"),
            ChainType.BASE: os.getenv("BASE_SEPOLIA_RPC_URL"),
        }
    else:
        rpc_urls = {
            ChainType.ETHEREUM: os.getenv("ETHEREUM_MAINNET_RPC_URL"),
            ChainType.BASE: os.getenv("BASE_MAINNET_RPC_URL"),
            ChainType.ARBITRUM: os.getenv("ARBITRUM_MAINNET_RPC_URL"),
            ChainType.POLYGON: os.getenv("POLYGON_MAINNET_RPC_URL"),
            ChainType.OPTIMISM: os.getenv("OPTIMISM_MAINNET_RPC_URL"),
        }

    rpc_url = rpc_urls.get(chain)
    if not rpc_url:
        raise ValueError(f"No RPC URL configured for {chain}")

    return Web3(Web3.HTTPProvider(rpc_url))
```

**Performance Optimization**:
- **Batch Processing**: Processes up to 50 transactions per run
- **Age Filter**: Only processes transactions older than 10 seconds (avoids premature checks)
- **Chain Grouping**: Reuses RPC provider per chain
- **Async I/O**: Uses async/await for concurrent RPC calls
- **Rate Limiting**: Celery Beat interval prevents overwhelming RPC nodes

**Error Handling**:
- **Transaction-Level Errors**: Logged and counted, but don't stop batch processing
- **Provider Errors**: Logged and retried via Celery retry mechanism
- **Database Errors**: Rollback and retry

---

## User Context Tasks

### Overview

User context tasks refresh user-specific data like wallet balances and transaction summaries.

**Location**: `/src/app/infrastructure/celery/tasks/user_context_tasks.py`

### update_user_context_task

**Purpose**: Refresh user's wallet balances and transaction summary.

**Task Configuration**:
```python
@shared_task(
    name="update_user_context",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    autoretry_for=(Exception,),
)
def update_user_context_task(
    self,
    user_id: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Celery task to update user context.

    Args:
        user_id: User ID to refresh
        force_refresh: Force refresh even if recently updated

    Returns:
        Dictionary with update summary:
        - status: "success" or "error"
        - user_id: User ID
        - wallets_updated: Number of wallets updated
        - balances_refreshed: Number of balances refreshed
        - transactions_counted: Total transaction count
        - duration_seconds: Processing time
    """
```

**Business Logic Flow**:

1. **Fetch User Wallets**:
```python
# Get all wallets for user
wallets = await wallet_repository.get_by_user_id(UserId(user_id))

logger.info(f"Updating context for user {user_id}: {len(wallets)} wallets")
```

2. **Refresh Wallet Balances**:
```python
balances_refreshed = 0

for wallet in wallets:
    try:
        # Get balance from blockchain RPC
        provider = get_rpc_provider(wallet.default_chain)
        balance_wei = await provider.eth.get_balance(wallet.address)
        balance_eth = Web3.from_wei(balance_wei, 'ether')

        # Convert to USD (via price API)
        eth_price_usd = await get_token_price_usd("ETH")
        balance_usd = float(balance_eth) * eth_price_usd

        # Update wallet balance in database
        await wallet_balance_repository.upsert(
            wallet_id=wallet.id_,
            chain=wallet.default_chain,
            balance_usd=balance_usd,
            last_updated=datetime.now(UTC)
        )

        balances_refreshed += 1

    except Exception as e:
        logger.error(f"Error refreshing balance for wallet {wallet.id_.value}: {e}")
```

3. **Count Transactions**:
```python
# Count total transactions for user
transactions_count = await transaction_repository.count_by_user_id(
    UserId(user_id)
)
```

4. **Update User Context**:
```python
# Update user_contexts table with latest summary
await user_context_repository.upsert(
    user_id=user_id,
    total_wallets=len(wallets),
    total_transactions=transactions_count,
    last_updated=datetime.now(UTC)
)
```

5. **Return Summary**:
```python
return {
    "status": "success",
    "user_id": user_id,
    "wallets_updated": len(wallets),
    "balances_refreshed": balances_refreshed,
    "transactions_counted": transactions_count,
    "duration_seconds": time.time() - start_time
}
```

**Trigger**: Event-driven (called after user actions like wallet sync, transaction log)

**Queue**: default

**Retry Policy**:
- Max retries: 2
- Retry delay: 30 seconds
- Auto-retry on all exceptions

**Example Invocation**:
```python
# After user syncs wallets
update_user_context_task.delay(user_id=123)

# Force refresh
update_user_context_task.delay(user_id=123, force_refresh=True)
```

---

### wallet_balance_refresh_task

**Purpose**: Batch refresh wallet balances for all active users.

**Task Configuration**:
```python
@shared_task(
    name="wallet_balance_refresh",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
)
def wallet_balance_refresh_task(
    self,
    batch_size: int = 100,
) -> dict[str, Any]:
    """
    Batch refresh wallet balances.

    Args:
        batch_size: Number of users to process per batch (default: 100)

    Returns:
        Dictionary with processing summary:
        - status: "success" or "error"
        - users_processed: Number of users updated
        - wallets_refreshed: Total wallets refreshed
        - errors: Number of errors encountered
        - duration_seconds: Processing time
    """
```

**Business Logic Flow**:

1. **Get Active Users**:
```python
# Get users with recent activity (logged in within 30 days)
cutoff = datetime.now(UTC) - timedelta(days=30)
active_users = await user_repository.get_active_users(
    since=cutoff,
    limit=batch_size
)

logger.info(f"Refreshing balances for {len(active_users)} active users")
```

2. **Process Each User**:
```python
users_processed = 0
wallets_refreshed = 0
errors = 0

for user in active_users:
    try:
        # Trigger user context update
        result = await update_user_context_task.apply_async(
            args=[user.id_.value],
            kwargs={"force_refresh": False}
        )

        # Wait for completion
        task_result = result.get(timeout=60)

        users_processed += 1
        wallets_refreshed += task_result["wallets_updated"]

    except Exception as e:
        logger.error(f"Error processing user {user.id_.value}: {e}")
        errors += 1
```

3. **Return Summary**:
```python
return {
    "status": "success",
    "users_processed": users_processed,
    "wallets_refreshed": wallets_refreshed,
    "errors": errors,
    "duration_seconds": time.time() - start_time
}
```

**Trigger**: Celery Beat (scheduled every 5 minutes)

**Queue**: low_priority

**Performance Considerations**:
- **Batch Size**: Processes 100 users per run to avoid overloading RPC nodes
- **Low Priority Queue**: Uses separate queue to avoid blocking critical tasks
- **Activity Filter**: Only refreshes wallets for recently active users
- **Timeout**: 60-second timeout per user update

---

## Celery Beat Schedule

Celery Beat is a scheduler that triggers periodic tasks.

**Configuration Location**: `/src/app/infrastructure/celery/celery_app.py`

**Schedule**:

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Transaction Confirmation (Mainnet)
    "confirm-pending-transactions-mainnet": {
        "task": "confirm_pending_transactions_mainnet",
        "schedule": 30.0,  # Every 30 seconds
        "options": {
            "queue": "default",
            "priority": 9,  # High priority
        },
    },

    # Transaction Confirmation (Testnet)
    "confirm-pending-transactions-testnet": {
        "task": "confirm_pending_transactions_testnet",
        "schedule": 60.0,  # Every 60 seconds
        "options": {
            "queue": "default",
            "priority": 7,  # Medium-high priority
        },
    },

    # Wallet Balance Refresh
    "wallet-balance-refresh": {
        "task": "wallet_balance_refresh",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
        "options": {
            "queue": "low_priority",
            "priority": 3,  # Low priority
        },
    },

    # User Context Cleanup (hourly)
    "user-context-cleanup": {
        "task": "user_context_cleanup",
        "schedule": crontab(minute=0),  # Every hour
        "options": {
            "queue": "maintenance",
            "priority": 1,  # Lowest priority
        },
    },
}
```

**Schedule Types**:
- **Interval**: Fixed seconds (e.g., `30.0` = every 30 seconds)
- **Crontab**: Unix cron-style (e.g., `crontab(minute="*/5")` = every 5 minutes)

**Priority Levels**:
- 10: Critical (not used currently)
- 9: High (mainnet transaction confirmation)
- 7: Medium-High (testnet transaction confirmation)
- 5: Medium (user-triggered tasks)
- 3: Low (background refresh)
- 1: Lowest (maintenance, cleanup)

**Queue Assignment**:
- `default`: General-purpose tasks
- `low_priority`: Background refresh tasks
- `maintenance`: Cleanup and analytics tasks

---

## Task Configuration

### Global Task Settings

```python
# src/app/infrastructure/celery/celery_app.py

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task Execution
    task_track_started=True,  # Track when task starts
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit (warning)

    # Worker Configuration
    worker_prefetch_multiplier=4,  # Prefetch 4 tasks per worker
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks

    # Reliability
    task_acks_late=True,  # Acknowledge after task completes
    task_reject_on_worker_lost=True,  # Reject task if worker dies

    # Result Backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)
```

### Per-Task Configuration

Tasks can override global settings:

```python
@shared_task(
    name="custom_task",
    bind=True,  # Bind task instance as first argument
    max_retries=5,  # Override default retries
    default_retry_delay=120,  # 2 minutes between retries
    autoretry_for=(Exception,),  # Auto-retry on these exceptions
    retry_backoff=True,  # Exponential backoff
    retry_backoff_max=600,  # Max 10 minutes between retries
    retry_jitter=True,  # Add random jitter to avoid thundering herd
    time_limit=600,  # 10 minutes hard limit
    soft_time_limit=540,  # 9 minutes soft limit
    acks_late=True,  # Acknowledge after completion
    reject_on_worker_lost=True,  # Reject if worker dies
)
def custom_task(self, ...):
    ...
```

---

## Error Handling and Retries

### Retry Strategies

**Automatic Retries**:
```python
@shared_task(
    autoretry_for=(ConnectionError, TimeoutError),  # Auto-retry on these
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,  # Exponential backoff: 60s → 120s → 240s
    retry_jitter=True,  # Add random jitter: ±10%
)
def network_dependent_task(self):
    ...
```

**Manual Retries**:
```python
@shared_task(bind=True)
def manual_retry_task(self, ...):
    try:
        # Task logic
        result = do_something()
    except TemporaryError as exc:
        # Retry with custom countdown
        raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes
    except PermanentError as exc:
        # Don't retry, log and fail
        logger.error(f"Permanent error: {exc}")
        raise
```

**Exponential Backoff**:
```python
# With retry_backoff=True
# Retry 1: 60 seconds
# Retry 2: 120 seconds (2^1 * 60)
# Retry 3: 240 seconds (2^2 * 60)
# Retry 4: 480 seconds (2^3 * 60)
```

**Max Backoff**:
```python
@shared_task(
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes between retries
)
def capped_backoff_task(self):
    ...
```

### Error Categories

**Transient Errors** (should retry):
- Network errors (ConnectionError, TimeoutError)
- Rate limiting (429 status codes)
- Temporary RPC node unavailability
- Database connection errors

**Permanent Errors** (should NOT retry):
- Invalid transaction hash (malformed)
- Wallet not found (deleted)
- Authorization errors (user permissions)
- Data validation errors

**Error Handling Pattern**:
```python
@shared_task(bind=True, max_retries=3)
def robust_task(self, tx_hash: str):
    try:
        # Fetch transaction from blockchain
        receipt = await provider.get_transaction_receipt(tx_hash)

        if receipt is None:
            # Transient: Transaction not mined yet
            raise self.retry(countdown=30)

        # Process receipt
        ...

    except ValueError as e:
        # Permanent: Invalid transaction hash
        logger.error(f"Invalid tx_hash: {tx_hash}")
        raise  # Don't retry

    except (ConnectionError, TimeoutError) as e:
        # Transient: Network error
        raise self.retry(exc=e, countdown=60)

    except Exception as e:
        # Unknown error: Log and retry
        logger.error(f"Unexpected error: {e}")
        raise self.retry(exc=e, countdown=120)
```

---

## Performance Optimization

### Batch Processing

**Problem**: Processing transactions one-by-one is slow.

**Solution**: Batch by chain and process in parallel.

```python
# Group transactions by chain
transactions_by_chain = defaultdict(list)
for tx in pending_transactions:
    transactions_by_chain[tx.chain].append(tx)

# Process each chain in parallel
tasks = []
for chain, txs in transactions_by_chain.items():
    task = process_chain_transactions.delay(chain, txs)
    tasks.append(task)

# Wait for all tasks
results = [task.get() for task in tasks]
```

### Connection Pooling

**Problem**: Creating new database connections per task is expensive.

**Solution**: Use connection pooling.

```python
# SQLAlchemy connection pool
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # 10 connections in pool
    max_overflow=20,  # 20 additional connections if needed
    pool_pre_ping=True,  # Check connection before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

### Caching

**Problem**: Repeated RPC calls for token prices.

**Solution**: Cache token prices in Redis.

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=1)

async def get_token_price_usd(token_symbol: str) -> float:
    # Check cache first
    cache_key = f"token_price:{token_symbol}"
    cached_price = redis_client.get(cache_key)

    if cached_price:
        return float(cached_price)

    # Fetch from API
    price = await fetch_token_price_from_api(token_symbol)

    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, str(price))

    return price
```

### Rate Limiting

**Problem**: Overwhelming RPC nodes with too many requests.

**Solution**: Use rate limiting and backoff.

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=1)  # Max 10 calls per second
async def get_transaction_receipt(tx_hash: str):
    return await provider.eth.get_transaction_receipt(tx_hash)
```

### Worker Configuration

**Concurrency**:
```bash
# Start Celery worker with 4 concurrent processes
celery -A app.infrastructure.celery.celery_app worker \
  --concurrency=4 \
  --loglevel=info
```

**Autoscaling**:
```bash
# Autoscale between 2-8 workers
celery -A app.infrastructure.celery.celery_app worker \
  --autoscale=8,2 \
  --loglevel=info
```

**Multiple Queues**:
```bash
# Worker for default queue only
celery -A app.infrastructure.celery.celery_app worker \
  -Q default \
  --concurrency=4

# Worker for low_priority queue
celery -A app.infrastructure.celery.celery_app worker \
  -Q low_priority \
  --concurrency=2
```

---

## Monitoring and Observability

### Flower (Celery Monitoring)

**Installation**:
```bash
pip install flower
```

**Start Flower**:
```bash
make celery.flower
# Or manually:
celery -A app.infrastructure.celery.celery_app flower --port=5555
```

**Access**: http://localhost:5555

**Features**:
- Task history and statistics
- Worker monitoring
- Task runtime graphs
- Active task inspection
- Rate limiting controls

### Logging

**Task-Level Logging**:
```python
import logging

logger = logging.getLogger(__name__)

@shared_task
def logged_task(user_id: int):
    logger.info(f"[TASK] Processing user {user_id}")

    try:
        result = do_work(user_id)
        logger.info(f"[TASK] Success: {result}")
        return result
    except Exception as e:
        logger.error(f"[TASK] Error processing user {user_id}: {e}")
        raise
```

**Structured Logging**:
```python
import structlog

logger = structlog.get_logger()

@shared_task
def structured_logged_task(tx_hash: str):
    logger.info(
        "transaction_confirmation_started",
        tx_hash=tx_hash,
        task_id=self.request.id
    )

    # ...

    logger.info(
        "transaction_confirmation_completed",
        tx_hash=tx_hash,
        status="success",
        block_number=receipt.block_number
    )
```

### Metrics

**Custom Metrics** (with Prometheus):
```python
from prometheus_client import Counter, Histogram

# Metrics
transaction_confirmations = Counter(
    'transaction_confirmations_total',
    'Total transaction confirmations',
    ['chain', 'status']
)

task_duration = Histogram(
    'task_duration_seconds',
    'Task execution duration',
    ['task_name']
)

@shared_task
def monitored_task(tx: Transaction):
    with task_duration.labels(task_name='confirm_transaction').time():
        # Process transaction
        receipt = await provider.get_transaction_receipt(tx.tx_hash)

        if receipt.status == 1:
            transaction_confirmations.labels(
                chain=tx.chain.value,
                status='success'
            ).inc()
        else:
            transaction_confirmations.labels(
                chain=tx.chain.value,
                status='failed'
            ).inc()
```

### Health Checks

**Celery Inspect**:
```bash
# Check active tasks
celery -A app.infrastructure.celery.celery_app inspect active

# Check registered tasks
celery -A app.infrastructure.celery.celery_app inspect registered

# Check worker stats
celery -A app.infrastructure.celery.celery_app inspect stats
```

**Redis Health Check**:
```python
import redis

def check_redis_health() -> bool:
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        redis_client.ping()
        return True
    except redis.ConnectionError:
        return False
```

**Database Health Check**:
```python
async def check_database_health() -> bool:
    try:
        await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

---

## Summary

The Wallets & Transactions Celery tasks provide:

**Core Functionality**:
- **Transaction Confirmation**: Automated blockchain polling to update transaction status
- **User Context Updates**: Real-time wallet balance and transaction summary refresh
- **Scheduled Jobs**: Periodic batch processing for all active users

**Reliability**:
- Automatic retries with exponential backoff
- Error categorization (transient vs permanent)
- Connection pooling and health checks
- Graceful degradation on failures

**Performance**:
- Batch processing by blockchain
- Concurrent task execution
- Redis caching for token prices
- Rate limiting to avoid overwhelming RPC nodes

**Observability**:
- Flower monitoring dashboard
- Structured logging with contextual data
- Prometheus metrics for dashboards
- Health check endpoints

**Task Registry**:
- `confirm_pending_transactions`: Main confirmation task (every 30s)
- `confirm_pending_transactions_testnet`: Testnet only (every 60s)
- `confirm_pending_transactions_mainnet`: Mainnet only (every 30s)
- `update_user_context`: User-specific refresh (on-demand)
- `wallet_balance_refresh`: Batch refresh for active users (every 5 minutes)

**Next Steps**: See `README.md` for module overview and navigation.
