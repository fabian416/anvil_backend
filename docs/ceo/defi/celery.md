# DeFi Operations Celery Tasks Specification

> **Last Updated**: 2026-01-25  
> **Status**: Partial Implementation  
> **Maintainers**: @backend-engineer @error-detective @code-reviewer

---

## Executive Summary

The DeFi Operations module has **limited Celery task implementation**. Currently, only general data refresh tasks exist that interact with DeFi data providers.

---

## 1. Existing Celery Tasks

### 1.1 Refresh DeFi Knowledge Graph Stats
**Task Name**: `refresh_defi_graph_stats`  
**Location**: `src/app/infrastructure/celery/tasks.py`

**Purpose**: Update DeFi knowledge graph statistics.

**Implementation**:
```python
@celery_app.task(name="refresh_defi_graph_stats")
def refresh_defi_graph_stats():
    async def runner(container):
        from app.domain.ports.external_data import DefiDataProvider
        
        data_provider = await container.get(DefiDataProvider)
        # Update graph stats
        await data_provider.execute_sql(
            "SELECT update_graph_stats('defi_knowledge_graph')"
        )
    
    asyncio.run(_run_task(runner))
```

**Schedule**: Part of periodic task updates

---

## 2. Recommended Celery Tasks

### 2.1 Refresh Market Data Cache

**Task Name**: `refresh_defi_market_data`  
**Priority**: HIGH  
**Schedule**: Every 5 minutes

**Purpose**: Refresh cached market data for all DeFi protocols.

**Implementation Recommendation**:
```python
@celery_app.task(name="refresh_defi_market_data")
def refresh_defi_market_data():
    """
    Refresh cached market data for all DeFi protocols.
    
    - Aave markets
    - Morpho vaults
    - Curve pools
    - Hyperliquid perpetuals
    
    Runs every 5 minutes.
    """
    async def runner(container):
        from app.domain.ports.aave_gateway import AaveGateway
        from app.domain.ports.morpho_gateway import MorphoGateway
        from app.domain.ports.curve_gateway import CurveGateway
        
        aave = await container.get(AaveGateway)
        morpho = await container.get(MorphoGateway)
        curve = await container.get(CurveGateway)
        
        # Refresh Aave markets for all chains
        for chain in ["ethereum", "polygon", "arbitrum", "base"]:
            await aave.get_markets(asset=None, chain=chain)
        
        # Refresh Morpho vaults
        await morpho.get_vaults(GetVaultsRequest(limit=100))
        
        # Refresh Curve pools
        await curve.get_pools(chain="ethereum", sort_by="tvl", limit=100)
        
        print("DeFi market data refreshed")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"refresh-defi-market-data": {
    "task": "refresh_defi_market_data",
    "schedule": crontab(minute="*/5"),
},
```

---

### 2.2 Monitor Liquidation Risk

**Task Name**: `monitor_liquidation_risk`  
**Priority**: HIGH  
**Schedule**: Every 15 minutes

**Purpose**: Monitor user positions and alert on liquidation risk.

**Implementation Recommendation**:
```python
@celery_app.task(name="monitor_liquidation_risk")
def monitor_liquidation_risk():
    """
    Monitor user positions for liquidation risk.
    
    - Check Aave health factors
    - Check Hyperliquid positions
    - Send alerts for critical positions
    
    Runs every 15 minutes.
    """
    async def runner(container):
        from app.domain.ports.aave_gateway import AaveGateway
        from app.application.notification.ports import NotificationRepository
        from app.infrastructure.persistence_sqla.adapters import UserRepository
        
        aave = await container.get(AaveGateway)
        notif_repo = await container.get(NotificationRepository)
        user_repo = await container.get(UserRepository)
        
        # Get users with DeFi positions
        users_with_positions = await user_repo.read_users_with_defi_alerts()
        
        alerts_sent = 0
        for user in users_with_positions:
            for wallet in user.wallets:
                try:
                    hf = await aave.get_health_factor(address=wallet.address, chain="ethereum")
                    
                    if hf.risk_level == RiskLevel.CRITICAL:
                        await notif_repo.create_liquidation_alert(
                            user_id=user.id,
                            wallet_address=wallet.address,
                            health_factor=str(hf.value),
                            risk_level="CRITICAL",
                        )
                        alerts_sent += 1
                except Exception:
                    continue
        
        print(f"Liquidation monitoring complete: {alerts_sent} alerts sent")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"monitor-liquidation-risk": {
    "task": "monitor_liquidation_risk",
    "schedule": crontab(minute="*/15"),
},
```

---

### 2.3 Track Cross-Chain Transfers

**Task Name**: `track_cross_chain_transfers`  
**Priority**: MEDIUM  
**Schedule**: Every 10 minutes

**Purpose**: Track pending LayerZero and Axelar transfers.

**Implementation Recommendation**:
```python
@celery_app.task(name="track_cross_chain_transfers")
def track_cross_chain_transfers():
    """
    Track pending cross-chain transfers.
    
    - Check LayerZero message status
    - Check Axelar transfer status
    - Update database with progress
    - Notify users on completion
    
    Runs every 10 minutes.
    """
    async def runner(container):
        from app.domain.ports.layerzero_gateway import LayerZeroGateway
        from app.domain.ports.axelar_gateway import AxelarGateway
        
        lz = await container.get(LayerZeroGateway)
        axelar = await container.get(AxelarGateway)
        
        # Get pending transfers from DB
        pending_lz = await get_pending_lz_transfers()
        pending_axelar = await get_pending_axelar_transfers()
        
        for transfer in pending_lz:
            status = await lz.track_message(transfer.tx_hash)
            if status.message.status == MessageStatus.DELIVERED:
                await mark_transfer_complete(transfer.id)
        
        for transfer in pending_axelar:
            status = await axelar.track_transfer(transfer.tx_hash)
            if status.transfer.status == TransferStatus.COMPLETED:
                await mark_transfer_complete(transfer.id)
        
        print(f"Tracked {len(pending_lz) + len(pending_axelar)} transfers")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"track-cross-chain-transfers": {
    "task": "track_cross_chain_transfers",
    "schedule": crontab(minute="*/10"),
},
```

---

### 2.4 Aggregate DeFi Analytics

**Task Name**: `aggregate_defi_analytics`  
**Priority**: LOW  
**Schedule**: Daily at 3 AM UTC

**Purpose**: Generate daily DeFi analytics and trends.

**Implementation Recommendation**:
```python
@celery_app.task(name="aggregate_defi_analytics")
def aggregate_defi_analytics():
    """
    Aggregate daily DeFi analytics.
    
    - TVL changes across protocols
    - Yield trends
    - Trading volume
    - User activity metrics
    
    Runs daily at 3 AM.
    """
    async def runner(container):
        from datetime import datetime, UTC, timedelta
        
        yesterday = datetime.now(UTC) - timedelta(days=1)
        
        # Aggregate by protocol
        metrics = {
            "aave": await aggregate_aave_metrics(yesterday),
            "morpho": await aggregate_morpho_metrics(yesterday),
            "curve": await aggregate_curve_metrics(yesterday),
            "hyperliquid": await aggregate_hyperliquid_metrics(yesterday),
        }
        
        # Store in analytics table
        await store_daily_defi_analytics(yesterday.date(), metrics)
        
        print(f"DeFi analytics aggregated for {yesterday.date()}")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"aggregate-defi-analytics": {
    "task": "aggregate_defi_analytics",
    "schedule": crontab(hour=3, minute=0),
},
```

---

### 2.5 Sync Protocol Stats

**Task Name**: `sync_protocol_stats`  
**Priority**: MEDIUM  
**Schedule**: Hourly

**Purpose**: Sync protocol TVL and stats from DeFiLlama.

**Implementation Recommendation**:
```python
@celery_app.task(name="sync_protocol_stats")
def sync_protocol_stats():
    """
    Sync protocol stats from DeFiLlama.
    
    - Total TVL per protocol
    - Chain breakdowns
    - Historical trends
    
    Runs hourly.
    """
    async def runner(container):
        from app.infrastructure.defi.providers.defillama import DefiLlamaClient
        
        client = DefiLlamaClient()
        
        protocols = ["aave", "morpho", "curve", "lido", "uniswap"]
        
        for protocol in protocols:
            stats = await client.get_protocol_tvl(protocol)
            await cache_protocol_stats(protocol, stats)
        
        print(f"Synced stats for {len(protocols)} protocols")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"sync-protocol-stats": {
    "task": "sync_protocol_stats",
    "schedule": crontab(minute=30),  # Hourly at :30
},
```

---

### 2.6 Refresh Token Prices

**Task Name**: `refresh_token_prices`  
**Priority**: HIGH  
**Schedule**: Every 2 minutes

**Purpose**: Refresh token prices from CoinGecko.

**Implementation Recommendation**:
```python
@celery_app.task(name="refresh_token_prices")
def refresh_token_prices():
    """
    Refresh token prices from CoinGecko.
    
    - Major tokens (ETH, BTC, etc.)
    - DeFi tokens
    - Cache in Redis
    
    Runs every 2 minutes.
    """
    async def runner(container):
        from app.infrastructure.defi.providers.coingecko import CoinGeckoClient
        from app.infrastructure.cache.redis_cache import RedisCache
        
        client = CoinGeckoClient()
        cache = await container.get(RedisCache)
        
        tokens = [
            "bitcoin", "ethereum", "solana", "polygon",
            "aave", "curve-dao-token", "uniswap",
        ]
        
        prices = await client.get_price(tokens, ["usd"])
        
        for token_id, data in prices.items():
            await cache.set(f"price:{token_id}", data["usd"], ttl=300)
        
        print(f"Refreshed prices for {len(prices)} tokens")
    
    asyncio.run(_run_task(runner))
```

**Beat Schedule**:
```python
"refresh-token-prices": {
    "task": "refresh_token_prices",
    "schedule": crontab(minute="*/2"),
},
```

---

## 3. Recommended Beat Schedule

```python
celery_app.conf.beat_schedule.update({
    # DeFi tasks (to be implemented)
    "refresh-defi-market-data": {
        "task": "refresh_defi_market_data",
        "schedule": crontab(minute="*/5"),  # Every 5 min
    },
    "refresh-token-prices": {
        "task": "refresh_token_prices",
        "schedule": crontab(minute="*/2"),  # Every 2 min
    },
    "monitor-liquidation-risk": {
        "task": "monitor_liquidation_risk",
        "schedule": crontab(minute="*/15"),  # Every 15 min
    },
    "track-cross-chain-transfers": {
        "task": "track_cross_chain_transfers",
        "schedule": crontab(minute="*/10"),  # Every 10 min
    },
    "sync-protocol-stats": {
        "task": "sync_protocol_stats",
        "schedule": crontab(minute=30),  # Hourly at :30
    },
    "aggregate-defi-analytics": {
        "task": "aggregate_defi_analytics",
        "schedule": crontab(hour=3, minute=0),  # Daily 3 AM
    },
})
```

---

## 4. Implementation Priority

| Task | Priority | Effort | Business Impact |
|------|----------|--------|-----------------|
| refresh_token_prices | HIGH | Low | Real-time price data |
| refresh_defi_market_data | HIGH | Medium | User experience |
| monitor_liquidation_risk | HIGH | Medium | User asset protection |
| track_cross_chain_transfers | MEDIUM | Medium | Transaction tracking |
| sync_protocol_stats | MEDIUM | Low | Analytics accuracy |
| aggregate_defi_analytics | LOW | Medium | Business insights |

---

## 5. Task Design Patterns

### 5.1 Idempotency
All DeFi tasks should be idempotent - running multiple times should not cause issues.

### 5.2 Error Handling
```python
@celery_app.task(name="task_name", bind=True, max_retries=3)
def task_name(self):
    try:
        # Task logic
    except ExternalAPIError as e:
        # Retry with exponential backoff
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    except Exception as e:
        # Log and don't retry
        logger.error(f"Task failed: {e}")
```

### 5.3 Caching Strategy
- Use Redis for price data (TTL: 2-5 min)
- Use PostgreSQL for historical analytics
- Invalidate cache on significant data changes

---

## 6. Running Celery

### Start Worker
```bash
make celery.worker
# or
celery -A app.infrastructure.celery.app worker --loglevel=info
```

### Start Beat Scheduler
```bash
make celery.beat
# or
celery -A app.infrastructure.celery.app beat --loglevel=info
```

### Monitor with Flower
```bash
make celery.flower
# Access at http://localhost:5555
```

---

## References

- **Celery App**: `src/app/infrastructure/celery/app.py`
- **Main Tasks**: `src/app/infrastructure/celery/tasks.py`
- **DeFi Adapters**: `src/app/infrastructure/adapters/external/`
- **Data Providers**: `src/app/infrastructure/defi/providers/`
