# ⚡ Anvil Platform - Performance Optimization Guide

## Complete Performance Tuning Strategy

**Version:** 1.0  
**Date:** November 2025  
**Goal:** Achieve sub-500ms P95 latency

---

## 🎯 Performance Targets

### Target Metrics

```yaml
API Response Times (P95):
  Health Check: < 50ms
  Wallet Balance: < 200ms
  Swap Quote: < 500ms
  Transaction History: < 300ms
  AI Chat: < 3000ms (includes AI inference)

Database Queries (P95):
  Simple Queries: < 10ms
  Complex Queries: < 100ms
  Joins: < 50ms

Mobile App:
  App Launch: < 3 seconds
  Screen Transitions: < 100ms
  API Response Handling: < 50ms
  Frame Rate: 60 FPS

Frontend (Admin Portal):
  First Contentful Paint: < 1.5s
  Time to Interactive: < 3.5s
  Largest Contentful Paint: < 2.5s
```

---

## 🗄️ Database Optimization

### 1. Indexing Strategy

**Critical Indexes:**
```sql
-- Users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_last_login ON users(last_login_at DESC);

-- Transactions table
CREATE INDEX idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_type_status ON transactions(type, status);
CREATE INDEX idx_transactions_tx_hash ON transactions(tx_hash);

-- Earn positions
CREATE INDEX idx_earn_positions_user_status ON earn_positions(user_id, status);
CREATE INDEX idx_earn_positions_protocol ON earn_positions(protocol);

-- Audit logs
CREATE INDEX idx_audit_logs_actor_action ON audit_logs(actor_user_id, action, created_at DESC);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);

-- Token balances
CREATE INDEX idx_token_balances_wallet_asset ON token_balances(wallet_id, asset);
```

**Composite Index Strategy:**
```sql
-- For queries that filter by multiple columns
CREATE INDEX idx_transactions_complex ON transactions(
    user_id,
    status,
    type,
    created_at DESC
);

-- For covering index (includes all columns in SELECT)
CREATE INDEX idx_users_covering ON users(
    id,
    email,
    firstname,
    lastname,
    status
) WHERE status = 'active';
```

### 2. Query Optimization

**SQLAlchemy Best Practices:**
```python
# ✅ GOOD: Eager loading to avoid N+1 queries
from sqlalchemy.orm import joinedload, selectinload

# Use joinedload for single relationships
users = db.query(User).options(
    joinedload(User.profile),
    joinedload(User.wallet)
).all()

# Use selectinload for collections
users = db.query(User).options(
    selectinload(User.transactions),
    selectinload(User.earn_positions)
).all()

# ❌ BAD: N+1 query problem
users = db.query(User).all()
for user in users:
    print(user.transactions)  # Each iteration = 1 query!


# ✅ GOOD: Pagination with limit/offset
def get_transactions_paginated(user_id: int, page: int, limit: int):
    offset = (page - 1) * limit
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(
        Transaction.created_at.desc()
    ).limit(limit).offset(offset).all()


# ✅ GOOD: Use specific columns instead of SELECT *
def get_transaction_summary(user_id: int):
    return db.query(
        Transaction.id,
        Transaction.type,
        Transaction.amount_in_usd,
        Transaction.status
    ).filter(
        Transaction.user_id == user_id
    ).all()


# ✅ GOOD: Use aggregations in database
from sqlalchemy import func

def get_user_stats(user_id: int):
    result = db.query(
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount_in_usd).label('volume')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.status == 'success'
    ).first()
    
    return {
        'transaction_count': result.count,
        'total_volume': result.volume
    }
```

### 3. Connection Pooling

```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # Base connections
    max_overflow=20,        # Additional connections
    pool_pre_ping=True,     # Check connection before use
    pool_recycle=3600,      # Recycle connections every hour
    echo=False,             # Don't log SQL in production
    connect_args={
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30
    }
)
```

### 4. Query Caching

```python
# Cache expensive queries
from app.core.cache import cache

@cache(ttl=300)  # 5 minutes
def get_top_earn_opportunities():
    """Get top 10 earn opportunities (expensive query)."""
    return db.query(EarnOpportunity).order_by(
        EarnOpportunity.apy.desc()
    ).limit(10).all()


# Cache with dynamic key
@cache(ttl=60, key="user_balance:{user_id}")
def get_user_balance(user_id: int):
    """Get user balance (cached per user)."""
    return db.query(TokenBalance).filter(
        TokenBalance.user_id == user_id
    ).all()
```

---

## 🚀 API Optimization

### 1. Response Caching

**Redis Caching Layer:**
```python
# app/core/cache.py
import json
import hashlib
from functools import wraps
from app.core.redis_client import redis_client

def cache_response(ttl: int = 300, key_prefix: str = ""):
    """Cache API responses in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"
            
            # Add function args to key
            if args or kwargs:
                key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
                key_hash = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{cache_key}:{key_hash}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result, default=str)
            )
            
            return result
        return wrapper
    return decorator


# Usage
@router.get("/earn/opportunities")
@cache_response(ttl=300, key_prefix="earn_opportunities")
async def get_earn_opportunities():
    """Get earn opportunities (cached for 5 minutes)."""
    return await earn_service.get_opportunities()
```

### 2. Compression

```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Responses over 1KB will be compressed automatically
```

### 3. Async Processing

```python
# ✅ GOOD: Parallel external API calls
import asyncio
import httpx

async def get_multi_chain_balances(address: str):
    """Get balances from multiple chains in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://arbitrum-api.com/balance/{address}"),
            client.get(f"https://base-api.com/balance/{address}"),
            client.get(f"https://optimism-api.com/balance/{address}"),
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]


# ❌ BAD: Sequential calls (slow!)
async def get_multi_chain_balances_slow(address: str):
    async with httpx.AsyncClient() as client:
        arb = await client.get(f"https://arbitrum-api.com/balance/{address}")
        base = await client.get(f"https://base-api.com/balance/{address}")
        op = await client.get(f"https://optimism-api.com/balance/{address}")
        return [arb.json(), base.json(), op.json()]
```

### 4. Background Jobs

```python
# Move slow operations to background workers
from app.workers.celery_app import celery_app

@celery_app.task
def update_user_analytics(user_id: int):
    """Update user analytics in background (slow operation)."""
    # Expensive computation
    analytics = calculate_user_analytics(user_id)
    save_analytics(user_id, analytics)


# API endpoint returns immediately
@router.post("/user/refresh-analytics")
async def refresh_analytics(user_id: int):
    """Trigger analytics refresh (async)."""
    update_user_analytics.delay(user_id)
    return {"status": "processing"}
```

---

## 🔥 Caching Strategy

### Multi-Layer Cache Architecture

```
┌─────────────────────────────────────┐
│        Client Side (Mobile)         │
│  - React Query Cache (5 min)        │
│  - AsyncStorage (persistent)        │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│         CDN (CloudFront)            │
│  - Static Assets (forever)          │
│  - API Responses (1 min)            │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│     Application Cache (Redis)       │
│  - Hot data (30s - 5 min)           │
│  - Session data (30 min)            │
│  - Rate limits (1 min)              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│        Database (MySQL)             │
│  - Query Cache (auto)               │
│  - InnoDB Buffer Pool               │
└─────────────────────────────────────┘
```

### Cache TTL Strategy

```python
CACHE_TTL = {
    # Static data
    "token_list": 3600,              # 1 hour
    "protocol_list": 1800,           # 30 minutes
    
    # Semi-static data
    "apy_rates": 300,                # 5 minutes
    "gas_prices": 60,                # 1 minute
    
    # Dynamic data
    "user_balance": 30,              # 30 seconds
    "token_prices": 10,              # 10 seconds
    
    # Real-time data (minimal caching)
    "transaction_status": 5,         # 5 seconds
    "swap_quote": 30,                # 30 seconds (expires fast)
}
```

### Cache Invalidation

```python
# app/core/cache.py

class CacheInvalidator:
    @staticmethod
    def invalidate_user_cache(user_id: int):
        """Invalidate all user-related caches."""
        patterns = [
            f"user_balance:{user_id}",
            f"user_profile:{user_id}",
            f"user_transactions:{user_id}:*",
            f"user_positions:{user_id}",
        ]
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
    
    @staticmethod
    def invalidate_on_transaction(user_id: int, tx_type: str):
        """Invalidate caches when transaction occurs."""
        CacheInvalidator.invalidate_user_cache(user_id)
        
        # Invalidate global caches if needed
        if tx_type in ["earn_deposit", "earn_withdraw"]:
            redis_client.delete("earn_opportunities")
```

---

## 📱 Mobile App Optimization

### 1. List Optimization

```typescript
// ✅ GOOD: Use FlashList for large lists
import { FlashList } from '@shopify/flash-list'

<FlashList
  data={transactions}
  renderItem={({ item }) => <TransactionItem item={item} />}
  estimatedItemSize={80}
  keyExtractor={(item) => item.id.toString()}
  // Much faster than FlatList for 100+ items
/>


// ✅ GOOD: Pagination
const [page, setPage] = useState(1)
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery(
  ['transactions', userId],
  ({ pageParam = 1 }) => fetchTransactions(userId, pageParam),
  {
    getNextPageParam: (lastPage, pages) => {
      return lastPage.hasMore ? pages.length + 1 : undefined
    }
  }
)
```

### 2. Image Optimization

```typescript
// ✅ GOOD: Use FastImage for better performance
import FastImage from 'react-native-fast-image'

<FastImage
  source={{
    uri: tokenIconUrl,
    priority: FastImage.priority.normal,
    cache: FastImage.cacheControl.immutable
  }}
  style={{ width: 32, height: 32 }}
  resizeMode={FastImage.resizeMode.contain}
/>
```

### 3. Memoization

```typescript
// ✅ GOOD: Memoize expensive calculations
import { useMemo, useCallback } from 'react'

const TransactionList = ({ transactions }) => {
  // Memoize filtered/sorted list
  const sortedTransactions = useMemo(() => {
    return transactions
      .filter(tx => tx.status === 'success')
      .sort((a, b) => b.createdAt - a.createdAt)
  }, [transactions])
  
  // Memoize callback functions
  const handleTransactionPress = useCallback((txId) => {
    navigation.navigate('TransactionDetail', { txId })
  }, [navigation])
  
  return (
    <FlashList
      data={sortedTransactions}
      renderItem={({ item }) => (
        <TransactionItem
          item={item}
          onPress={handleTransactionPress}
        />
      )}
    />
  )
}

// Memoize entire component
export default React.memo(TransactionList)
```

### 4. Bundle Optimization

```javascript
// metro.config.js
module.exports = {
  transformer: {
    minifierConfig: {
      compress: {
        drop_console: true,  // Remove console.log in production
      },
    },
  },
}

// Enable Hermes engine for faster startup
// android/app/build.gradle
project.ext.react = [
  enableHermes: true
]
```

---

## 🌐 Network Optimization

### 1. Request Batching

```python
# Batch multiple requests into one
@router.post("/batch")
async def batch_requests(requests: List[BatchRequest]):
    """Handle multiple API calls in one request."""
    results = []
    
    for req in requests:
        try:
            result = await execute_request(req)
            results.append({"success": True, "data": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    
    return results


# Mobile usage
const batchedData = await api.batch([
  { method: 'GET', url: '/user/wallet' },
  { method: 'GET', url: '/user/transactions' },
  { method: 'GET', url: '/earn/opportunities' }
])
```

### 2. HTTP/2 and Connection Reuse

```python
# Use HTTP/2 for multiplexing
import httpx

# Reuse connection pool
client = httpx.AsyncClient(http2=True)

# Multiple requests use same connection
responses = await asyncio.gather(
    client.get(url1),
    client.get(url2),
    client.get(url3)
)
```

### 3. Prefetching

```typescript
// Prefetch data user is likely to need
const { prefetchQuery } = useQueryClient()

// When user views wallet, prefetch transaction history
useEffect(() => {
  prefetchQuery(
    ['transactions', userId],
    () => fetchTransactions(userId)
  )
}, [userId])
```

---

## ⚙️ Infrastructure Optimization

### 1. Auto-Scaling Configuration

```yaml
ECS Service Auto-Scaling:
  Target Metrics:
    - CPU Utilization: 70%
    - Memory Utilization: 80%
    - Request Count: 1000/min per task
  
  Scaling Policy:
    Min Tasks: 4
    Max Tasks: 20
    Scale Up: +2 tasks when > target for 2 min
    Scale Down: -1 task when < target for 5 min
    Cooldown: 3 minutes
```

### 2. Database Read Replicas

```yaml
Strategy:
  - Use primary for writes
  - Use replicas for reads
  - Route read-only queries to replicas

Implementation:
  Primary: All INSERT, UPDATE, DELETE
  Replica 1: User queries (balance, profile)
  Replica 2: Transaction history
  Replica 3: Analytics queries
```

```python
# app/core/database.py

# Primary (write) engine
primary_engine = create_engine(DATABASE_PRIMARY_URL)

# Replica (read) engine
replica_engine = create_engine(DATABASE_REPLICA_URL)

# Session factories
PrimarySession = sessionmaker(bind=primary_engine)
ReplicaSession = sessionmaker(bind=replica_engine)

# Use in services
def get_transactions(user_id: int):
    """Read-only query uses replica."""
    db = ReplicaSession()
    return db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()

def create_transaction(tx_data: dict):
    """Write query uses primary."""
    db = PrimarySession()
    tx = Transaction(**tx_data)
    db.add(tx)
    db.commit()
    return tx
```

---

## 📊 Performance Monitoring

### Key Metrics to Track

```python
# app/core/metrics.py
from prometheus_client import Histogram, Counter

# API latency
api_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Database query time
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# External API latency
external_api_duration = Histogram(
    'external_api_duration_seconds',
    'External API call duration',
    ['service'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Cache hit rate
cache_hits = Counter('cache_hits_total', 'Cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Cache misses', ['cache_type'])
```

### Performance Testing

```python
# tests/performance/test_api_latency.py
import pytest
import time

@pytest.mark.performance
def test_api_response_time():
    """Test API response times meet SLA."""
    timings = []
    
    for _ in range(100):
        start = time.time()
        response = client.get("/api/v1/user/wallet")
        duration = time.time() - start
        timings.append(duration)
    
    # Calculate percentiles
    p50 = sorted(timings)[50]
    p95 = sorted(timings)[95]
    p99 = sorted(timings)[99]
    
    # Assert SLA
    assert p50 < 0.1, f"P50 latency {p50}s exceeds 100ms"
    assert p95 < 0.2, f"P95 latency {p95}s exceeds 200ms"
    assert p99 < 0.5, f"P99 latency {p99}s exceeds 500ms"
```

---

## ✅ Performance Checklist

### Backend
- [ ] All queries have appropriate indexes
- [ ] N+1 queries eliminated
- [ ] Connection pooling configured
- [ ] Response caching implemented
- [ ] Compression enabled
- [ ] Async operations where possible
- [ ] Background jobs for slow tasks
- [ ] Database queries optimized
- [ ] Read replicas configured

### Mobile
- [ ] FlashList for large lists
- [ ] Images optimized (FastImage)
- [ ] Components memoized
- [ ] Bundle size optimized
- [ ] Hermes engine enabled
- [ ] Pagination implemented
- [ ] Data prefetching
- [ ] Offline support

### Infrastructure
- [ ] Auto-scaling configured
- [ ] CDN enabled
- [ ] Load balancer configured
- [ ] Multi-AZ deployment
- [ ] Monitoring in place
- [ ] Alerts configured

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** Performance Team  
**Review:** Monthly + after major releases
