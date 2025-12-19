# Testing, Optimization & Polish Plan (Options 4-6)

Comprehensive plan for additional testing, performance optimization, and code quality improvements.

---

## Option 4: Testing & Quality Assurance

### Duration: 3-4 days
### Priority: LOW (we have 205 passing tests)
### Value: Higher confidence, fewer production bugs

---

### Phase 1: End-to-End Testing (Day 1)

#### 1.1 Playwright Setup

**Install Playwright:**
```bash
pip install playwright pytest-playwright
playwright install
```

**Test Structure:**
```
tests/
├── e2e/
│   ├── conftest.py
│   ├── test_authentication_flow.py
│   ├── test_hunter_ai_flow.py
│   ├── test_ultra_arbitrage_flow.py
│   └── test_subscription_flow.py
```

#### 1.2 Authentication Flow Tests

**File:** `tests/e2e/test_authentication_flow.py`

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_complete_auth_flow():
    """Test complete authentication flow"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Test signup
        await page.goto('http://localhost:3000/signup')
        await page.fill('[name="email"]', 'test@example.com')
        await page.fill('[name="password"]', 'Test123!')
        await page.click('button[type="submit"]')
        
        # Verify redirect to dashboard
        await page.wait_for_url('**/dashboard')
        
        # Test logout
        await page.click('[data-testid="logout-button"]')
        await page.wait_for_url('**/login')
        
        await browser.close()
```

#### 1.3 Hunter AI Flow Tests

```python
@pytest.mark.asyncio
async def test_hunter_ai_sentiment_flow():
    """Test Hunter AI sentiment analysis flow"""
    # Login
    # Navigate to Hunter AI
    # Select token
    # View sentiment analysis
    # Verify data displayed
    pass
```

#### 1.4 Coverage Targets

- [ ] Authentication: 100% coverage
- [ ] Hunter AI flows: 80% coverage
- [ ] ULTRA Arbitrage flows: 80% coverage
- [ ] Subscription flows: 100% coverage
- [ ] Error scenarios: 90% coverage

---

### Phase 2: Load Testing (Day 2)

#### 2.1 Locust Setup

**File:** `tests/load/locustfile.py`

```python
from locust import HttpUser, task, between
import random

class AnvilUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting"""
        response = self.client.post("/api/v1/account/login", json={
            "email": "test@example.com",
            "password": "Test123!",
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def get_conversations(self):
        self.client.get(
            "/api/v1/chat/conversations",
            headers=self.headers
        )
    
    @task(2)
    def get_sentiment(self):
        token = random.choice(['ETH', 'BTC', 'USDC'])
        self.client.get(
            f"/api/v1/hunter/sentiment/{token}",
            headers=self.headers
        )
    
    @task(1)
    def discover_arbitrage(self):
        self.client.get(
            "/api/v1/ultra/arbitrage/discover",
            params={"capital": 10000},
            headers=self.headers
        )
```

#### 2.2 Load Test Scenarios

**Scenario 1: Normal Load**
- Users: 100
- Duration: 5 minutes
- Target: < 200ms response time

**Scenario 2: Peak Load**
- Users: 1000
- Duration: 10 minutes
- Target: < 500ms response time

**Scenario 3: Stress Test**
- Users: 5000
- Duration: 5 minutes
- Target: No failures

**Run Tests:**
```bash
# Normal load
locust -f tests/load/locustfile.py --host https://api.anvil.com \
  --users 100 --spawn-rate 10 --run-time 5m --headless

# Peak load
locust -f tests/load/locustfile.py --host https://api.anvil.com \
  --users 1000 --spawn-rate 50 --run-time 10m --headless

# Stress test
locust -f tests/load/locustfile.py --host https://api.anvil.com \
  --users 5000 --spawn-rate 100 --run-time 5m --headless
```

---

### Phase 3: Security Testing (Day 3)

#### 3.1 OWASP ZAP Scanning

```bash
# Install OWASP ZAP
docker pull owasp/zap2docker-stable

# Run baseline scan
docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable \
  zap-baseline.py -t https://api.anvil.com -r zap_report.html

# Run full scan
docker run -v $(pwd):/zap/wrk/:rw -t owasp/zap2docker-stable \
  zap-full-scan.py -t https://api.anvil.com -r zap_full_report.html
```

#### 3.2 Dependency Scanning

```bash
# Install safety
pip install safety

# Check for known vulnerabilities
safety check

# Generate report
safety check --output json > security_report.json
```

#### 3.3 Bandit Security Linter

```bash
# Install bandit
pip install bandit

# Run security scan
bandit -r src/ -f json -o bandit_report.json

# High severity only
bandit -r src/ -ll -f json -o bandit_high.json
```

#### 3.4 Container Scanning

```bash
# Install trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh

# Scan Docker image
trivy image anvil-backend:latest

# Generate report
trivy image --format json --output trivy_report.json anvil-backend:latest
```

---

### Phase 4: Performance Profiling (Day 4)

#### 4.1 Python Profiling

```python
# tests/performance/test_profiling.py
import cProfile
import pstats
from io import StringIO

def profile_endpoint():
    """Profile endpoint performance"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Call endpoint
    response = client.get("/api/v1/hunter/sentiment/ETH")
    
    profiler.disable()
    
    # Print stats
    s = StringIO()
    stats = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    stats.print_stats(20)
    print(s.getvalue())
```

#### 4.2 Memory Profiling

```bash
# Install memory_profiler
pip install memory_profiler

# Profile memory usage
python -m memory_profiler src/app/run.py
```

#### 4.3 Database Query Analysis

```python
# Enable query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Analyze slow queries
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()
    if total > 0.1:  # Log queries > 100ms
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

## Option 5: New Features (Deferred)

### Priority: LOW
### Duration: 1-2 weeks per feature
### Value: Differentiation, additional revenue

### Feature Ideas (For Future Implementation)

1. **Social Trading**
   - Follow top traders
   - Copy trading strategies
   - Leaderboards

2. **Backtesting Engine**
   - Historical strategy testing
   - Performance metrics
   - Optimization suggestions

3. **Alert System**
   - Telegram bot integration
   - Discord webhooks
   - Email notifications
   - Price alerts
   - Arbitrage opportunities

4. **Advanced Analytics**
   - Custom dashboards
   - Performance reports
   - Risk analytics
   - Portfolio attribution

5. **Mobile App API**
   - Mobile-optimized endpoints
   - Push notifications
   - Offline support

6. **Multi-Chain Support**
   - Polygon integration
   - Arbitrum integration
   - Optimism integration
   - Cross-chain arbitrage

---

## Option 6: Optimization & Polish

### Duration: 2-3 days
### Priority: LOW (system performs well)
### Value: Better performance, maintainability

---

### Phase 1: Database Optimization (Day 1)

#### 1.1 Add Missing Indexes

```sql
-- Frequently queried columns
CREATE INDEX idx_conversations_user_id_created_at 
  ON conversations(user_id, created_at DESC);

CREATE INDEX idx_messages_conversation_id_created_at 
  ON messages(conversation_id, created_at DESC);

CREATE INDEX idx_subscriptions_user_id_active 
  ON subscriptions(user_id, is_active);

CREATE INDEX idx_trades_user_id_timestamp 
  ON trades(user_id, timestamp DESC);

-- Composite indexes for common queries
CREATE INDEX idx_arbitrage_opportunities_profit 
  ON arbitrage_opportunities(expected_profit_usd DESC, timestamp DESC);
```

#### 1.2 Query Optimization

```python
# Before: N+1 query problem
conversations = session.query(Conversation).filter_by(user_id=user_id).all()
for conv in conversations:
    messages = conv.messages  # N additional queries

# After: Eager loading
conversations = (
    session.query(Conversation)
    .filter_by(user_id=user_id)
    .options(joinedload(Conversation.messages))
    .all()
)
```

#### 1.3 Connection Pooling

```python
# config/prod/config.toml
[database]
pool_size = 20
max_overflow = 10
pool_pre_ping = true
pool_recycle = 3600
echo_pool = true
```

---

### Phase 2: Caching Layer (Day 2)

#### 2.1 Redis Caching

```python
# src/app/infrastructure/cache/redis_cache.py
import redis
import json
from functools import wraps

class RedisCache:
    def __init__(self, url: str):
        self.client = redis.from_url(url)
    
    def cache(self, ttl: int = 300):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key = f"{func.__name__}:{args}:{kwargs}"
                
                # Check cache
                cached = self.client.get(key)
                if cached:
                    return json.loads(cached)
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                self.client.setex(key, ttl, json.dumps(result))
                
                return result
            return wrapper
        return decorator

cache = RedisCache(REDIS_URL)
```

**Usage:**
```python
@cache.cache(ttl=300)  # Cache for 5 minutes
async def get_sentiment(token_symbol: str):
    # Expensive operation
    return sentiment_data
```

#### 2.2 Cache Invalidation

```python
def invalidate_cache(pattern: str):
    """Invalidate cache keys matching pattern"""
    for key in cache.client.scan_iter(pattern):
        cache.client.delete(key)

# Example: Invalidate all sentiment caches for a token
invalidate_cache("get_sentiment:ETH:*")
```

---

### Phase 3: Code Refactoring (Day 3)

#### 3.1 Remove Tech Debt

**Checklist:**
- [ ] Remove unused imports
- [ ] Remove commented code
- [ ] Fix TODO comments
- [ ] Simplify complex functions
- [ ] Extract magic numbers to constants
- [ ] Improve variable names

#### 3.2 Type Coverage

```bash
# Run mypy with strict mode
mypy src/ --strict

# Target: 95%+ type coverage
```

#### 3.3 Code Complexity

```bash
# Install radon
pip install radon

# Check complexity
radon cc src/ -a -nb

# Target: Average complexity < 5
```

#### 3.4 Dependency Updates

```bash
# Update dependencies
pip list --outdated

# Update safely
pip install --upgrade <package>

# Run tests after each update
pytest
```

---

## Success Metrics

### Testing (Option 4)
- [ ] E2E test coverage > 80%
- [ ] Load tests pass at 1000 concurrent users
- [ ] Zero critical security vulnerabilities
- [ ] All dependencies up to date

### Optimization (Option 6)
- [ ] API response time < 100ms (p95)
- [ ] Database query time < 50ms (avg)
- [ ] Cache hit rate > 80%
- [ ] Code complexity < 5 (avg)
- [ ] Type coverage > 95%

---

## Execution Priority

### Immediate (Do Now):
1. **Option 1:** Deployment & Production Setup ✅
2. **Option 2:** Documentation ✅

### Short-term (Next Week):
3. **Option 3:** Frontend Integration (User-facing)

### Medium-term (Next Month):
4. **Option 6:** Optimization & Polish
5. **Option 4:** Additional Testing

### Long-term (2+ Months):
6. **Option 5:** New Features (Based on user feedback)

---

## Maintenance Plan

### Weekly Tasks
- Run security scans
- Check for dependency updates
- Review performance metrics
- Monitor error rates

### Monthly Tasks
- Full load testing
- Code quality review
- Tech debt cleanup
- Documentation updates

### Quarterly Tasks
- Major dependency updates
- Architecture review
- Performance optimization
- Security audit

---

## Tools & Resources

### Testing
- **E2E:** Playwright
- **Load:** Locust, K6
- **Security:** OWASP ZAP, Bandit, Safety
- **Performance:** cProfile, memory_profiler

### Monitoring
- **APM:** DataDog, New Relic
- **Errors:** Sentry
- **Logs:** ELK Stack
- **Uptime:** UptimeRobot

### Optimization
- **Database:** pgAdmin, pg_stat_statements
- **Caching:** Redis, Redis Commander
- **Profiling:** Py-Spy, line_profiler
