# Etherscan Balance Integration

## Overview

This document describes the Etherscan API integration for wallet balance checking, which replaces the Privy-based balance sync with direct on-chain ERC-20 token balance verification.

## Architecture

### Components

**1. Configuration** (`src/app/setup/config/etherscan.py`)
- `EtherscanSettings`: Pydantic settings for Etherscan API V2
- Supports 60+ EVM chains with single API key
- Configurable rate limits, retry logic, and anomaly detection

**2. Etherscan Client** (`src/app/infrastructure/adapters/external/etherscan_client.py`)
- Extended with `get_token_balance()` method
- Handles API errors, rate limits, and retries
- Supports multiple chains via chainid parameter

**3. Celery Tasks** (`src/app/infrastructure/celery/tasks/etherscan_balance_tasks.py`)
- `etherscan.sync_balances`: Periodic balance sync (every 5 minutes)
- `etherscan.sync_single_wallet`: On-demand balance check
- Priority queue: high-value wallets checked every 2 minutes

## API Endpoint

```
GET https://api.etherscan.io/v2/api
  ?chainid={chain_id}
  &module=account
  &action=tokenbalance
  &contractaddress={token_contract}
  &address={wallet_address}
  &tag=latest
  &apikey={api_key}
```

### Response Format

```json
{
  "status": "1",
  "message": "OK",
  "result": "3000000"  // Balance in smallest unit (6 decimals for USDT/USDC)
}
```

## Supported Chains

| Chain | Chain ID | USDC Contract |
|-------|----------|---------------|
| Ethereum | 1 | `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` |
| Base | 8453 | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| Arbitrum | 42161 | `0xaf88d065e77c8cC2239327C5EDb3A432268e5831` |
| Optimism | 10 | `0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85` |
| Polygon | 137 | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |

## Configuration

### 1. Add API Key to Secrets

**File**: `config/local/.secrets.toml`

```toml
[etherscan]
# Etherscan API V2 - Single key works for 60+ EVM chains
# Documentation: https://docs.etherscan.io/etherscan-v2
# Get key from: https://etherscan.io/myapikey
api_key = "YOUR_API_KEY_HERE"
```

### 2. Optional: Customize Settings

**File**: `config/local/config.toml`

```toml
[etherscan]
# Override defaults from EtherscanSettings if needed
request_timeout = 15.0
max_wallets_per_batch = 20
balance_check_interval_seconds = 300  # 5 minutes
high_value_threshold_usd = 10000.0
high_value_check_interval_seconds = 120  # 2 minutes
```

## Celery Beat Schedule

### Periodic Sync (Every 5 Minutes)

```python
"etherscan-sync-balances": {
    "task": "etherscan.sync_balances",
    "schedule": 300.0,  # Every 5 minutes
    "options": {"queue": "maintenance"},
}
```

**Task Flow**:
1. Query wallets eligible for balance check
   - Active wallets (`status = 1`)
   - Not checked within interval (5 min for normal, 2 min for high-value)
   - Priority: high-value wallets (>$10k) first
2. Fetch ERC-20 token balance from Etherscan API V2
3. Update `chain_addresses.balance_usd` in database
4. Update `wallets.last_balance_checked_at` timestamp
5. Detect anomalies (>50% change or >$1000 change)

### On-Demand Sync

```python
from app.infrastructure.celery.tasks.etherscan_balance_tasks import sync_single_wallet_balance

# Trigger for specific wallet
sync_single_wallet_balance.delay(wallet_id=123, chain="base")
```

## Rate Limits

**Etherscan Free Tier**:
- 5 calls/second
- 100,000 calls/day

**Rate Budget**:
- 100,000 calls/day ÷ 1,440 minutes = ~69 calls/minute max
- At 20 wallets/batch every 5 minutes = ~4 calls/minute
- Leaves headroom for on-demand checks and burst traffic

## Database Schema

### wallets Table

```sql
-- Balance check tracking
last_balance_checked_at TIMESTAMPTZ NULL;

CREATE INDEX ix_wallets_last_balance_checked_at
ON wallets(last_balance_checked_at);
```

### chain_addresses Table

```sql
-- Token balance in USD
balance_usd NUMERIC(20, 2) DEFAULT 0.00;
last_balance_update TIMESTAMPTZ NULL;
```

## Testing

### Run Test Suite

```bash
python test_etherscan_balance.py
```

**Test Cases**:
1. **Etherscan Client**: Direct API call to fetch token balance
2. **Database Wallet**: Verify test wallet exists in database
3. **Celery Task Simulation**: Simulate full balance sync workflow

### Expected Output

```
================================================================================
TEST SUMMARY
================================================================================
✅ PASS - Etherscan Client
✅ PASS - Database Wallet
✅ PASS - Celery Task Simulation

Total: 3/3 tests passed

🎉 All tests passed!
```

### Test Wallet

- **Address**: `0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B`
- **Chain**: Base
- **Expected Balance**: Variable (check current on-chain balance)

## Monitoring

### Logs

```bash
# Watch Etherscan balance sync logs
make logs-celery | grep "Etherscan balance"
```

### Metrics

- `processed_count`: Wallets checked this run
- `updated_count`: Balances updated successfully
- `error_count`: API failures or errors

### Log Messages

```
🔄 Starting Etherscan balance sync at 2026-02-01T15:30:00Z
📊 Processing 15 wallets for balance sync
✅ Updated balance for wallet 183: $100.50 USDC on base
⚠️  Anomaly detected for wallet 456: $500.00 -> $1500.00 (200.0% change)
✅ Etherscan balance sync complete: processed=15, updated=14, errors=1, duration=3.45s
```

## Anomaly Detection

Automatically detects suspicious balance changes:

**Thresholds**:
- Percentage change: >50%
- Absolute change: >$1,000

**Example**:
```
⚠️  Anomaly detected for wallet 123:
    $500.00 -> $1500.00 (200.0% change)
```

## Error Handling

### Rate Limit (429)
- Exponential backoff (2^attempt seconds, max 60s)
- Graceful retry with max 3 attempts

### API Errors
- Log warning and continue with next wallet
- Update `last_balance_checked_at` to prevent re-processing

### Network Timeouts
- 15-second timeout per request
- Retry on transient failures

## Migration from Privy

### Privy Balance Sync (Old)
- API: Privy embedded wallet API
- Interval: Every 30 seconds
- Batch size: 10 wallets
- Cooldown: 3 minutes

### Etherscan Balance Sync (New)
- API: Etherscan API V2 (direct on-chain)
- Interval: Every 5 minutes
- Batch size: 20 wallets
- Cooldown: 5 minutes (2 minutes for high-value)
- Priority queue for high-value wallets

### Coexistence

Both systems run in parallel:
- **Privy**: Checks Privy-managed wallets every 30 seconds
- **Etherscan**: Verifies on-chain balances every 5 minutes

This provides redundancy and cross-verification of balance data.

## Troubleshooting

### "Etherscan API key not configured"

**Solution**: Add API key to `config/local/.secrets.toml`:

```toml
[etherscan]
api_key = "YOUR_API_KEY_HERE"
```

### Rate limiting (429 errors)

**Causes**:
- Exceeding 5 calls/second
- Exceeding 100,000 calls/day

**Solutions**:
1. Reduce `max_wallets_per_batch` in config
2. Increase `balance_check_interval_seconds`
3. Upgrade to paid Etherscan tier

### "No token contracts configured for chain"

**Solution**: Add token contracts to `EtherscanSettings.TOKEN_CONTRACTS`:

```python
TOKEN_CONTRACTS: dict[str, dict[str, tuple[str, int]]] = {
    "your_chain": {
        "0xYourTokenContract": ("SYMBOL", decimals),
    },
}
```

### Wallet not found in database

**Solution**: Add wallet via Privy login or wallet import:

```python
# Via Privy login
POST /api/v1/account/privy/login

# Via wallet import
POST /api/v1/wallet/import
```

## Related Components

- **swap_workflow agent**: Uses balance data for pre-transaction validation
- **WalletBalanceDbAdapter**: Reads balance from `chain_addresses` table
- **PortfolioBalanceChecker**: `IBalanceChecker` implementation
- **UserContextService**: Updates `portfolio_state` based on balance

## API Reference

### EtherscanClient

```python
from app.infrastructure.adapters.external.etherscan_client import EtherscanClient

client = EtherscanClient(
    api_key="YOUR_API_KEY",
    network="ethereum",
    timeout=15.0,
    use_v2_api=True,
)

# Get token balance
result = await client.get_token_balance(
    wallet_address="0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
    contract_address="0xdAC17F958D2ee523a2206206994597C13D831ec7",
    decimals=6,
)

if result:
    raw_balance, formatted_balance = result
    print(f"Balance: {formatted_balance} USDT ({raw_balance} raw)")

await client.close()
```

### Celery Tasks

```python
from app.infrastructure.celery.tasks.etherscan_balance_tasks import (
    sync_wallet_balances,
    sync_single_wallet_balance,
)

# Periodic sync (called by Celery Beat)
sync_wallet_balances.delay()

# On-demand sync for specific wallet
sync_single_wallet_balance.delay(
    wallet_id=123,
    chain="base",
)
```

## Performance

### Latency
- API call: ~200-500ms per wallet
- Database update: ~50ms per wallet
- Total per wallet: ~250-550ms

### Throughput
- 20 wallets per batch
- 300-second interval
- ~4 wallets/minute sustained

### Scalability
- Free tier: 100,000 calls/day = ~4,166 wallets/hour
- Paid tier: 1,000,000 calls/day = ~41,666 wallets/hour

## Security

### API Key Protection
- Stored in `.secrets.toml` (gitignored)
- Never logged or exposed in responses
- Environment-specific keys (local, dev, prod)

### Rate Limiting
- Client-side throttling (5 calls/sec max)
- Exponential backoff on rate limit errors
- Daily budget tracking

### Input Validation
- Wallet addresses validated as hex strings
- Contract addresses checked against whitelist
- Chain IDs validated against supported chains

## Future Enhancements

1. **Multi-token Support**: Check multiple tokens per wallet
2. **Native Token Balances**: Support ETH, MATIC, etc.
3. **Historical Balance Tracking**: Store balance history over time
4. **Real-time Webhooks**: Etherscan webhooks for instant updates
5. **Cross-chain Aggregation**: Total portfolio across all chains
6. **Custom Token Lists**: User-defined tokens to track

## References

- [Etherscan API V2 Documentation](https://docs.etherscan.io/etherscan-v2)
- [Etherscan Rate Limits](https://docs.etherscan.io/support/rate-limits)
- [ERC-20 Token Standard](https://eips.ethereum.org/EIPS/eip-20)
