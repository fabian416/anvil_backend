# Privy Wallet Balance Sync Tasks

## Overview

Background Celery tasks that synchronize wallet balances from Privy API to the local database. This enables:

- **swap_workflow agent**: Balance validation before swaps
- **Portfolio state classification**: EMPTY, STARTER, ACTIVE, WHALE
- **Risk assessment**: Position value tracking

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Celery Beat    │────▶│  Celery      │────▶│  Privy API      │
│  (30 seconds)   │     │  Worker      │     │  GET /balance   │
└─────────────────┘     └──────┬───────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │  - wallets   │
                        │  - chain_    │
                        │    addresses │
                        └──────────────┘
```

## Tasks

### 1. `privy.sync_wallet_balances` (Periodic)

**Schedule**: Every 30 seconds  
**Queue**: `maintenance`  
**Max per run**: 10 wallets

Syncs balances for wallets that haven't been checked in 3+ minutes.

```python
# Query logic
SELECT id, privy_wallet_id, address, default_chain
FROM wallets
WHERE privy_wallet_id IS NOT NULL
  AND status = 1  -- ACTIVE
  AND (last_balance_checked_at IS NULL OR last_balance_checked_at < NOW() - INTERVAL '3 minutes')
ORDER BY last_balance_checked_at NULLS FIRST
LIMIT 10
```

### 2. `privy.sync_single_wallet_balance` (On-Demand)

**Queue**: `maintenance`  
**Use case**: Pre-transaction validation, user-triggered refresh

```python
from app.infrastructure.celery.tasks.privy_balance_tasks import sync_single_wallet_balance

# Trigger on-demand sync
sync_single_wallet_balance.delay(wallet_id=123, chain="base")
```

## Configuration

### Secrets (config/local/.secrets.toml)

```toml
[privy]
APP_ID = "cmix8nbke00fgju0c08x1088e"
CLIENT_ID = "client-WY6TQio5RWSAyH6NjHpccMFnkfddN252UBgL9xZn3uzW5"
APP_SECRET = "privy_app_secret_xxx..."
```

### Task Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_USERS_PER_RUN` | 10 | Max wallets processed per Celery run |
| `BALANCE_CHECK_INTERVAL_SECONDS` | 180 | Cooldown between checks (3 minutes) |
| `PRIVY_API_TIMEOUT` | 10.0 | HTTP timeout for Privy API calls |

## Database Schema

### wallets table

```sql
-- New column added by migration
last_balance_checked_at TIMESTAMPTZ NULL,
CREATE INDEX ix_wallets_last_balance_checked_at ON wallets(last_balance_checked_at);
```

### chain_addresses table

```sql
balance_usd NUMERIC(20, 2) DEFAULT 0.00,
last_balance_update TIMESTAMPTZ NULL
```

## Privy API

### Endpoint

```
GET https://api.privy.io/v1/wallets/{wallet_id}/balance
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `chain_id` | int | EVM chain ID (1=ETH, 8453=Base, 42161=Arbitrum) |
| `asset` | string | Asset to check (e.g., "usdc", "eth") |

### Authentication

```
Authorization: Basic base64(APP_ID:APP_SECRET)
privy-app-id: {APP_ID}
```

### Response

```json
{
  "balance": "1000000",
  "decimals": 6
}
```

## Monitoring

### Logs

```bash
# Watch balance sync logs
make logs-celery | grep "Privy balance"
```

### Metrics

- `processed_count`: Wallets checked this run
- `updated_count`: Balances updated
- `error_count`: API failures

## Troubleshooting

### "Privy credentials not configured"

Add secrets to `config/local/.secrets.toml`:

```toml
[privy]
APP_ID = "your-app-id"
APP_SECRET = "your-app-secret"
```

### Rate limiting (429 errors)

The task automatically handles rate limits by:
1. Processing only 10 wallets per run
2. 3-minute cooldown between checks per wallet
3. Graceful handling of 429 responses

### Wallet not found (404)

This is normal for wallets that don't exist in Privy. The task logs a debug message and continues.

## Related Components

- **swap_workflow_agent**: Uses balance data for validation
- **WalletBalanceDbAdapter**: Reads balance from chain_addresses table
- **PortfolioBalanceChecker**: IBalanceChecker implementation
- **UserContextService**: Updates portfolio_state based on balance
