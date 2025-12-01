# Performance Testing Suite

Comprehensive performance, load, and stress testing for the DeFi Chat Platform.

## Overview

This suite includes:
- **Load Testing:** Simulates realistic user traffic (Locust)
- **Benchmarking:** Measures component performance
- **Stress Testing:** Tests system under extreme load

## Quick Start

### 1. Load Testing with Locust

```bash
# Install locust
pip install locust

# Run with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Set users, spawn rate, and start test

# Run headless
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --html=report.html
```

### 2. Benchmarking

```bash
# Run all benchmarks
python tests/performance/benchmark.py

# Expected output:
# - Message Sending: ~XXms avg, YY ops/sec
# - Cache Read: ~5ms avg, 200 ops/sec
# - Cache Write: ~10ms avg, 100 ops/sec
# - Rate Limiter: ~1ms avg, 1000 ops/sec
# - Intent Refinement: ~2ms avg, 500 ops/sec
```

### 3. Stress Testing

```bash
# Run stress tests
python tests/performance/stress_test.py

# Tests:
# - 100 concurrent users, 10 req/user (1000 total)
# - 500 concurrent cache reads
# - Rate limiter enforcement
# - Batch processor throughput
```

## Load Testing Scenarios

### ChatUser (Realistic Usage)
Simulates normal user behavior:
- **Task Distribution:**
  - 50% swap queries
  - 25% trading queries
  - 20% portfolio queries
  - 5% navigation

- **Wait Time:** 1-5 seconds between actions
- **Realistic:** Mimics actual user patterns

### CachingPerformanceUser (Cache Testing)
Tests cache effectiveness:
- **Fast Requests:** 0.1-0.5s between requests
- **Same Data:** Requests identical data repeatedly
- **Measures:** Cache hit rates and latency

## Benchmarking

### What's Measured

- **Average Time:** Mean response time
- **Median Time:** 50th percentile
- **P95 Time:** 95th percentile (SLA target)
- **P99 Time:** 99th percentile (outlier detection)
- **Throughput:** Operations per second
- **Min/Max:** Best and worst case

### Performance Targets

| Component | Target P95 | Target Throughput |
|-----------|------------|-------------------|
| Message Send | < 100ms | > 100 ops/sec |
| Cache Read | < 10ms | > 500 ops/sec |
| Cache Write | < 20ms | > 200 ops/sec |
| Rate Limiter | < 5ms | > 1000 ops/sec |
| Intent Refine | < 10ms | > 500 ops/sec |

## Stress Testing

### Scenarios

**1. Message Sending Load**
- 100 concurrent users
- 10 requests per user
- Total: 1000 requests
- Target: < 5% error rate

**2. Concurrent Cache Access**
- 500 concurrent readers
- 20 requests per reader
- Total: 10,000 requests
- Target: < 1% error rate

**3. Rate Limiter Enforcement**
- 50 concurrent users
- Exceed rate limit deliberately
- Verify: Properly blocks excess requests

**4. Batch Processor Throughput**
- 100 concurrent users
- 20 items per user
- Total: 2000 items
- Verify: Batched correctly

## Expected Results

### Load Testing (100 users)

With caching:
```
Total Requests: 10,000
Response Time (P95): 50ms
Response Time (P99): 100ms
Requests/sec: 200
Error Rate: < 1%
```

Without caching:
```
Total Requests: 10,000
Response Time (P95): 800ms
Response Time (P99): 1500ms
Requests/sec: 20
Error Rate: < 5%
```

### Benchmarks

```
Message Sending:
  Average: 45ms
  P95: 80ms
  Throughput: 150 ops/sec

Cache Read (hit):
  Average: 2ms
  P95: 5ms
  Throughput: 800 ops/sec

Cache Write:
  Average: 8ms
  P95: 15ms
  Throughput: 250 ops/sec
```

### Stress Tests

```
Message Sending (1000 requests):
  Successful: 990 (99%)
  Failed: 10 (1%)
  Avg Response: 65ms
  Throughput: 185 req/s

Concurrent Cache (10,000 requests):
  Successful: 9,950 (99.5%)
  Failed: 50 (0.5%)
  Avg Response: 3ms
  Throughput: 750 req/s
```

## Monitoring During Tests

### System Metrics

**CPU Usage:**
```bash
# Monitor CPU
top -p $(pgrep -f uvicorn)
```

**Memory Usage:**
```bash
# Monitor memory
ps aux | grep uvicorn
```

**Redis Stats:**
```bash
# Redis monitoring
redis-cli info stats
redis-cli info keyspace
```

**PostgreSQL:**
```bash
# Active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Query performance
psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

## Optimization Tips

### If Response Times Are High:

1. **Check Cache Hit Rate:**
   ```python
   # Should be > 80% for price/quote requests
   redis-cli info stats | grep keyspace_hits
   ```

2. **Check Rate Limits:**
   ```python
   # Ensure not hitting external API limits
   ```

3. **Check Database Connections:**
   ```python
   # Pool should not be exhausted
   ```

### If Error Rate Is High:

1. **Check Logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Check External APIs:**
   - 1inch API status
   - Hyperliquid status
   - CoinGecko rate limits

3. **Check Database:**
   - Connection pool size
   - Query timeouts
   - Lock contention

## CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run benchmarks
        run: python tests/performance/benchmark.py
      - name: Run stress tests
        run: python tests/performance/stress_test.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-results
          path: results/
```

## Troubleshooting

### Locust Won't Start

```bash
# Check installation
pip install locust

# Check Python version (3.8+)
python --version
```

### Redis Connection Failed

```bash
# Start Redis
docker run -d -p 6379:6379 redis

# Or
redis-server
```

### High Error Rates

1. Reduce concurrent users
2. Increase wait times
3. Check external API limits
4. Verify database connections

## Best Practices

1. **Baseline First:** Run tests before changes
2. **Compare:** Measure improvements
3. **Realistic Load:** Use production patterns
4. **Monitor:** Watch system metrics
5. **Iterate:** Optimize based on results

## Results Storage

Results are saved in:
```
tests/performance/results/
├── load-test-YYYY-MM-DD.html
├── benchmark-YYYY-MM-DD.json
└── stress-test-YYYY-MM-DD.json
```

## Contact

For performance issues or questions, see `docs/performance-tuning.md`
