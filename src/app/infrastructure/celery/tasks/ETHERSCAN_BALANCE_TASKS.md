# Etherscan Balance Sync Tasks - Orchestration Design

## Overview

On-chain ERC-20 token balance verification via Etherscan V2 API. This system runs as Celery periodic tasks alongside the existing Privy balance sync, providing direct blockchain-level balance verification.

**Relationship to Privy sync**: Privy sync (every 30s) gives fast reads from Privy's cached state. Etherscan sync (every 5m) provides ground-truth on-chain verification. Both update the same `chain_addresses.balance_usd` column.

## Architecture

```
                                    Etherscan V2 API
                                    (5 calls/sec free tier)
                                           ^
                                           |
+-----------------+     +---------------+  |  +-----------------+
|  Celery Beat    |---->|  Celery       |--+->|  PostgreSQL     |
|  (every 5 min)  |     |  Worker       |     |  - wallets      |
+-----------------+     +-------+-------+     |  - chain_        |
                                |             |    addresses     |
                        +-------v-------+     +-----------------+
                        | Priority Queue|
                        | 1. High-value |
                        | 2. Regular    |
                        | 3. Never-     |
                        |    checked    |
                        +---------------+
```

## Task Inventory

### 1. `etherscan.sync_balances` (Periodic)

| Property | Value |
|----------|-------|
| Schedule | Every 5 minutes |
| Queue | `maintenance` |
| Max wallets/run | 20 |
| Retries | 2 (with exponential backoff) |
| acks_late | true (re-queues on worker crash) |

**Processing order (priority queue):**
1. Wallets never checked (`last_balance_checked_at IS NULL`) -- oldest first
2. Wallets not checked in 5+ minutes -- oldest first

**Per wallet:**
1. Fetch USDC balance from Etherscan V2 (`module=account&action=tokenbalance`)
2. Convert raw balance using token decimals
3. Compare with previous balance for anomaly detection
4. Upsert into `chain_addresses` table
5. Update `wallets.last_balance_checked_at`

### 2. `etherscan.sync_single_wallet` (On-Demand)

| Property | Value |
|----------|-------|
| Queue | `maintenance` |
| Retries | 3 (with exponential backoff) |
| Use case | Pre-swap validation, manual refresh |

```python
from app.infrastructure.celery.tasks.etherscan_balance_tasks import sync_single_wallet_etherscan

# On-demand check for a specific wallet
result = sync_single_wallet_etherscan.delay(
    wallet_address="0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
    chain="ethereum",
    contract_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
    decimals=6,
)
```

### 3. `etherscan.verify_test_wallet` (Verification)

| Property | Value |
|----------|-------|
| Queue | `maintenance` |
| Purpose | Integration test / deployment verification |

Read-only check against test wallet `0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B`.
Verifies USDT balance is in expected range (2.5-3.5 USDT on Ethereum mainnet).

```python
from app.infrastructure.celery.tasks.etherscan_balance_tasks import verify_test_wallet

result = verify_test_wallet.delay()
# Returns: {"status": "verified", "usdt_balance": "3.0", ...}
```

## Rate Limiting Strategy

### Etherscan Free Tier Constraints

| Limit | Value |
|-------|-------|
| Calls per second | 5 |
| Calls per day | 100,000 |
| Calls per minute (derived) | ~69 |

### Budget Allocation

| Consumer | Calls/min | Daily budget |
|----------|-----------|-------------|
| Periodic sync (20 wallets / 5 min) | ~4 | ~5,760 |
| On-demand checks (estimated) | ~2 | ~2,880 |
| Test verification (occasional) | <1 | ~10 |
| **Total** | **~6** | **~8,650** |
| **Headroom** | **~63** | **~91,350** |

This leaves 91% of the daily budget unused for burst traffic and scaling.

### Rate Limiter Implementation

The `EtherscanClient` uses a **token bucket** algorithm:

```python
# Sliding window: max 5 calls per 1-second window
# If window is full, sleep until oldest call expires
async def _enforce_rate_limit(self):
    now = time.monotonic()
    self._call_timestamps = [ts for ts in self._call_timestamps if now - ts < 1.0]
    if len(self._call_timestamps) >= self.max_calls_per_second:
        sleep_time = 1.0 - (now - self._call_timestamps[0])
        await asyncio.sleep(sleep_time)
    self._call_timestamps.append(time.monotonic())
```

### Exponential Backoff

On rate limit (429) or server error (5xx):

```
Attempt 1: wait 2 seconds  (2^1)
Attempt 2: wait 4 seconds  (2^2)
Attempt 3: wait 8 seconds  (2^3)
Max backoff: 60 seconds
```

## Error Handling Flowchart

```
API Call
  |
  +-- HTTP 200 + status "1" --> SUCCESS --> Update DB --> Next wallet
  |
  +-- HTTP 200 + status "0"
  |     |
  |     +-- "Max rate limit reached" --> RETRY (exponential backoff)
  |     +-- "Invalid API key" --> ABORT (log critical, skip all)
  |     +-- Other error --> SKIP wallet (log warning)
  |
  +-- HTTP 429 --> RETRY (exponential backoff, max 3 attempts)
  |
  +-- HTTP 5xx --> RETRY (exponential backoff, max 3 attempts)
  |
  +-- HTTP 4xx (not 429) --> SKIP wallet (non-retryable)
  |
  +-- Timeout --> RETRY (exponential backoff, max 3 attempts)
  |
  +-- Network error --> RETRY (exponential backoff, max 3 attempts)
  |
  +-- All retries exhausted --> LOG error, increment error_count, continue
```

### Database Failure Recovery

| Scenario | Handling |
|----------|---------|
| DB write fails after API success | All updates batched in single transaction; if commit fails, everything rolls back. `last_balance_checked_at` is NOT updated, so wallet will be retried next run. |
| Duplicate updates | Idempotent: `SET balance_usd = X` (not increment). Safe to replay. |
| Worker crash mid-batch | `acks_late=True` re-queues the task. `last_balance_checked_at` only updates on commit, so no wallets are skipped. |
| Partial batch failure | Each wallet wrapped in try/except. Failed wallets are counted but don't abort the batch. |

## Anomaly Detection

The system detects three classes of anomalies:

### 1. Wallet Drain (CRITICAL)
Balance goes from non-zero (>$1) to exactly zero.

```
Severity: critical
Action: Log warning, include in task result anomalies list
Future: Trigger security alert, pause automated transactions
```

### 2. Large Balance Change (WARNING/CRITICAL)
Balance changes >50% AND >$1,000 in absolute terms.

```
>50% change: severity=warning
>90% change: severity=critical
```

### 3. Anomaly Response Format

```json
{
  "type": "wallet_drain",
  "severity": "critical",
  "direction": "decrease",
  "wallet_id": 42,
  "user_id": 7,
  "wallet_address": "0x48659...",
  "chain": "ethereum",
  "previous_balance_usd": 5000.00,
  "new_balance_usd": 0.00,
  "absolute_change_usd": 5000.00,
  "pct_change": 100.0
}
```

## Monitoring & Observability

### Metrics Tracked Per Run

| Metric | Description |
|--------|-------------|
| `processed` | Wallets checked this run |
| `updated` | Successful balance updates |
| `errors` | Failed wallet checks |
| `anomalies` | Anomalous balance changes detected |
| `api_calls` | Total Etherscan API calls |
| `api_successes` | Successful API responses |
| `api_failures` | Failed API calls (after retries) |
| `rate_limits_hit` | 429 / rate limit responses |
| `retries` | Total retry attempts |
| `total_latency_ms` | Cumulative API latency |
| `duration_seconds` | Total task execution time |

### Log Lines

```
INFO  Starting Etherscan balance sync at 2026-02-01T12:00:00
INFO  Processing 20 wallets via Etherscan
WARN  ANOMALY detected for wallet 42: wallet_drain ...
INFO  Etherscan balance sync complete: processed=20, updated=18, errors=2, anomalies=1, duration=8.50s
```

### Alert Thresholds (Recommendations)

| Condition | Severity | Action |
|-----------|----------|--------|
| Error rate > 10% (errors/processed) | Warning | Slack notification |
| Error rate > 50% | Critical | Page on-call, check API key |
| Any `wallet_drain` anomaly | Critical | Security team notification |
| API latency avg > 5000ms | Warning | Check Etherscan status |
| Rate limits > 5 per run | Warning | Reduce batch size |
| Task duration > 120s | Warning | Check for slow queries |

### Dashboard Panels (Grafana/Flower)

1. **Balance Sync Health**: Success/error/anomaly counts over time
2. **API Performance**: Latency percentiles (p50, p95, p99)
3. **Rate Limit Pressure**: Rate limit hits vs total calls
4. **Anomaly Feed**: Real-time list of detected anomalies
5. **Coverage**: Wallets checked in last 15 minutes vs total active wallets

## Test Wallet Verification Plan

### Step-by-step for `0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B`

```
Step 1: Trigger verification task
  $ python -c "
  from app.infrastructure.celery.tasks.etherscan_balance_tasks import verify_test_wallet
  result = verify_test_wallet()  # Synchronous call for testing
  print(result)
  "

Step 2: Expected output
  {
    "status": "verified",
    "test_wallet": "0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
    "chain": "ethereum",
    "usdt_balance": "3.000000",
    "eth_balance": "0.001234",
    "expected_range": "2.5-3.5",
    "in_expected_range": true,
    "api_metrics": {
      "api_calls": 2,
      "api_successes": 2,
      ...
    }
  }

Step 3: Verify on-demand single wallet check
  result = sync_single_wallet_etherscan(
    wallet_address="0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
    chain="ethereum",
    contract_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    decimals=6,
  )
  assert result["status"] == "success"
  assert Decimal(result["balance_human"]) >= Decimal("2.5")

Step 4: Verify DB update (if wallet exists in DB)
  SELECT ca.balance_usd, ca.last_balance_update
  FROM chain_addresses ca
  JOIN wallets w ON ca.wallet_id = w.id
  WHERE w.address = '0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B';
```

### Rollback Procedure

If the Etherscan sync produces incorrect data:

1. **Pause the task**: Remove `etherscan-sync-balances` from beat schedule
2. **Identify affected wallets**: Query `chain_addresses WHERE last_balance_update > <incident_time>`
3. **Restore from Privy**: Trigger `privy.sync_wallet_balances` to overwrite with Privy data
4. **Root cause**: Check `api_metrics` in task results for rate limit or API errors

## Configuration

### Secrets (`config/local/.secrets.toml`)

```toml
[etherscan]
API_KEY = "your-etherscan-v2-api-key"
```

### Settings (`src/app/setup/config/etherscan.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_key` | "" | Etherscan V2 API key |
| `base_url` | `https://api.etherscan.io/v2/api` | V2 unified endpoint |
| `max_calls_per_second` | 5 | Rate limiter ceiling |
| `max_calls_per_day` | 100,000 | Daily budget (informational) |
| `request_timeout` | 15.0 | HTTP timeout (seconds) |
| `max_retries` | 3 | Retry attempts per API call |
| `retry_backoff_base` | 2.0 | Exponential backoff base |
| `retry_backoff_max` | 60.0 | Max backoff (seconds) |
| `balance_check_interval_seconds` | 300 | Regular wallet check interval |
| `max_wallets_per_batch` | 20 | Max wallets per periodic run |
| `high_value_threshold_usd` | 10,000 | Priority queue threshold |
| `high_value_check_interval_seconds` | 120 | High-value wallet interval |
| `anomaly_pct_change_threshold` | 50.0 | Anomaly % change threshold |
| `anomaly_absolute_threshold_usd` | 1,000 | Anomaly $ change threshold |

## Agent Squad Integration

### Portfolio Agent

The Portfolio Agent can access real-time balances through the same `chain_addresses` table:

```python
# Portfolio Agent reads balance_usd from chain_addresses
# Both Privy sync (fast, cached) and Etherscan sync (ground truth)
# update the same column, so the agent always sees the latest value
balance = await session.execute(
    select(chain_addresses_table.c.balance_usd)
    .where(chain_addresses_table.c.wallet_id == wallet_id)
)
```

### ULTRA Hunter Risk Analysis

Anomaly detection feeds directly into risk assessment:
- `wallet_drain` anomalies should trigger immediate risk alerts
- `large_balance_change` events feed into position change tracking
- Historical balance data enables trend analysis

### swap_workflow Agent

Pre-transaction validation uses on-demand check:

```python
# Before executing a swap, verify balance is sufficient
result = sync_single_wallet_etherscan.apply_async(
    kwargs={
        "wallet_address": user_wallet,
        "chain": target_chain,
    },
    queue="maintenance",
)
balance = Decimal(result.get(timeout=30)["balance_human"])
if balance < required_amount:
    raise InsufficientBalanceError(...)
```

## Related Components

- `privy_balance_tasks.py` - Privy API balance sync (complementary, faster)
- `transaction_confirmation_tasks.py` - Transaction status verification
- `money_market_tasks.py` - DeFi rate caching (similar orchestration pattern)
- `WalletBalanceDbAdapter` - Reads balance from chain_addresses
- `PortfolioBalanceChecker` - IBalanceChecker port implementation
- `UserContextService` - Updates portfolio_state based on balance
