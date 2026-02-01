# Etherscan Balance Integration - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### 1. Configure API Key

Edit `config/local/.secrets.toml`:

```toml
[etherscan]
api_key = "YOUR_API_KEY_HERE"
```

Get your API key: https://etherscan.io/myapikey

### 2. Start Services

```bash
# Start all development services (FastAPI + Celery + MCP)
make start-dev

# Or start individually:
make celery.worker  # Celery worker
make celery.beat    # Celery scheduler
```

### 3. Verify It's Working

```bash
# Watch logs
make logs-celery | grep "Etherscan"

# Expected output (every 5 minutes):
# 🔄 Starting Etherscan balance sync at 2026-02-01T15:30:00Z
# 📊 Processing 15 wallets for balance sync
# ✅ Updated balance for wallet 183: $100.50 USDC on base
# ✅ Etherscan balance sync complete
```

### 4. Test with Test Wallet

```bash
# Run integration tests
python test_etherscan_balance.py

# Expected: ✅ All 3 tests passing
```

## 📋 Common Operations

### Check Specific Wallet Balance

```python
from app.infrastructure.celery.tasks.etherscan_balance_tasks import sync_single_wallet_etherscan

# Trigger on-demand sync
result = sync_single_wallet_etherscan.delay(
    wallet_address="0x48659e3469Ff2c6bb80e711Ed136F6aE03c2794B",
    chain="base",
)
```

### Monitor Task Status

```bash
# Check Celery Flower UI
make celery.flower
# Open: http://localhost:5555

# View task history
make logs-celery | grep "etherscan"
```

### Adjust Sync Frequency

Edit `src/app/infrastructure/celery/app.py`:

```python
"etherscan-sync-balances": {
    "task": "etherscan.sync_balances",
    "schedule": 300.0,  # Change this (seconds)
    "options": {"queue": "maintenance"},
}
```

## 🔧 Configuration Options

### Etherscan Settings

Edit `config/local/config.toml`:

```toml
[etherscan]
# API timeout
request_timeout = 15.0

# Batch size (wallets per run)
max_wallets_per_batch = 20

# Check interval (seconds)
balance_check_interval_seconds = 300  # 5 minutes

# High-value wallet threshold
high_value_threshold_usd = 10000.0

# High-value check interval (seconds)
high_value_check_interval_seconds = 120  # 2 minutes

# Anomaly detection
anomaly_pct_change_threshold = 50.0  # Alert on >50% change
anomaly_absolute_threshold_usd = 1000.0  # Alert on >$1000 change
```

## 🎯 Supported Chains

| Chain | Chain ID | Default Token |
|-------|----------|---------------|
| Ethereum | 1 | USDC |
| Base | 8453 | USDC |
| Arbitrum | 42161 | USDC |
| Optimism | 10 | USDC |
| Polygon | 137 | USDC |

## 📊 Rate Limits

**Etherscan Free Tier:**
- 5 calls/second
- 100,000 calls/day

**Current Usage:**
- ~4 calls/minute
- ~5,760 calls/day
- **94% capacity available**

## 🐛 Troubleshooting

### Problem: "Etherscan API key not configured"

**Solution:**
```bash
# Add API key to secrets file
echo '[etherscan]' >> config/local/.secrets.toml
echo 'api_key = "YOUR_KEY"' >> config/local/.secrets.toml
```

### Problem: Rate limit errors (429)

**Solutions:**
1. Reduce batch size: `max_wallets_per_batch = 10`
2. Increase interval: `balance_check_interval_seconds = 600`
3. Upgrade to paid tier: https://etherscan.io/apis

### Problem: No wallets being processed

**Check:**
```bash
# View eligible wallets
psql -U anvil -d anvil_db -c "
SELECT id, address, default_chain, last_balance_checked_at
FROM wallets
WHERE status = 1
ORDER BY last_balance_checked_at NULLS FIRST
LIMIT 20;
"
```

## 📚 Learn More

- Full Documentation: [docs/ETHERSCAN_BALANCE_INTEGRATION.md](./ETHERSCAN_BALANCE_INTEGRATION.md)
- Implementation Summary: [ETHERSCAN_INTEGRATION_SUMMARY.md](../ETHERSCAN_INTEGRATION_SUMMARY.md)
- API Reference: https://docs.etherscan.io/etherscan-v2

## 🎉 That's It!

You're now using Etherscan API for direct on-chain balance verification.

**Benefits:**
- ✅ Direct blockchain data (no intermediary)
- ✅ Multi-chain support (5+ chains)
- ✅ Priority queue (high-value wallets first)
- ✅ Anomaly detection (suspicious changes)
- ✅ Cost-effective (free tier: 100k calls/day)
