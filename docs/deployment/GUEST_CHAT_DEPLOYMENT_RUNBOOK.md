# Guest Chat System Deployment Runbook

**Version:** 1.0
**Last Updated:** 2026-01-11
**Status:** Production Ready ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Post-Deployment Validation](#post-deployment-validation)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)
8. [Incident Response](#incident-response)
9. [Maintenance Windows](#maintenance-windows)

---

## Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Guest Chat System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   FastAPI    │───→│  PostgreSQL  │    │    Redis     │  │
│  │   Server     │    │   Database   │    │    Cache     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                         │          │
│         ↓                                         ↓          │
│  ┌──────────────┐                        ┌──────────────┐  │
│  │  Hunter AI   │                        │ Rate Limiter │  │
│  │   Services   │                        │   Service    │  │
│  └──────────────┘                        └──────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Strategy

- **Type**: Blue-Green Deployment
- **Zero Downtime**: Yes
- **Auto-Rollback**: Yes (on health check failure)
- **Traffic Shifting**: Gradual (10% → 50% → 100%)

---

## Pre-Deployment Checklist

### 1. Code Quality

- [ ] All tests passing (91/91 ✅)
  ```bash
  pytest tests/integration/test_guest_*.py -v
  ```
- [ ] Code review approved (2+ reviewers)
- [ ] Security scan passed (`bandit`, `safety`)
- [ ] No critical or high vulnerabilities

### 2. Database

- [ ] Database migrations tested in staging
  ```bash
  alembic upgrade head --sql > migration.sql
  # Review migration.sql before applying
  ```
- [ ] Backup created and verified
  ```bash
  pg_dump anvil_db > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Migration rollback script ready
- [ ] Indexes verified (7 guest performance indexes)
  ```sql
  SELECT indexname, tablename
  FROM pg_indexes
  WHERE tablename LIKE 'guest%';
  ```

### 3. Redis Cache

- [ ] Redis cluster healthy
  ```bash
  redis-cli ping
  redis-cli info replication
  ```
- [ ] Cache keys TTL configured correctly
- [ ] Memory usage < 50%
  ```bash
  redis-cli info memory | grep used_memory_human
  ```

### 4. Dependencies

- [ ] All Python dependencies installed
  ```bash
  pip freeze > requirements.lock
  ```
- [ ] Environment variables set in production
  ```bash
  # Required env vars:
  # - APP_ENV=prod
  # - DATABASE_URL
  # - REDIS_URL
  # - SENTRY_DSN
  ```
- [ ] Secrets rotated (if needed)

### 5. Infrastructure

- [ ] Load balancer health checks configured
- [ ] Auto-scaling rules defined
- [ ] CloudWatch dashboards created
- [ ] Alert thresholds configured
- [ ] SSL certificates valid (>30 days)

### 6. Documentation

- [ ] API documentation up to date
- [ ] CHANGELOG.md updated
- [ ] Deployment notes written
- [ ] Rollback plan documented

---

## Deployment Steps

### Step 1: Pre-Deployment Validation (15 minutes)

**1.1 Run Pre-Deployment Tests**

```bash
# Navigate to project directory
cd /home/ubuntu/anvil_backend

# Run full test suite
pytest tests/integration/test_guest_*.py -v --tb=short

# Expected: 91/91 passing
```

**1.2 Verify Database Connection**

```bash
# Test database connectivity
python -c "
from app.infrastructure.persistence_sqla.database import Database
import asyncio

async def test():
    db = Database()
    await db.connect()
    print('✅ Database connection successful')
    await db.disconnect()

asyncio.run(test())
"
```

**1.3 Verify Redis Connection**

```bash
# Test Redis connectivity
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
# Expected: PONG

# Check memory usage
redis-cli -h $REDIS_HOST info memory | grep used_memory_human
# Expected: < 500MB
```

### Step 2: Create Database Backup (5 minutes)

```bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backups/anvil_db_${TIMESTAMP}.sql"

# Dump database
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Verify backup
ls -lh ${BACKUP_FILE}.gz

# Upload to S3 (if configured)
aws s3 cp ${BACKUP_FILE}.gz s3://anvil-backups/guest-chat/
```

### Step 3: Apply Database Migrations (5 minutes)

```bash
# Review migration SQL (dry run)
alembic upgrade head --sql > /tmp/migration_preview.sql
cat /tmp/migration_preview.sql

# Apply migrations
alembic upgrade head

# Verify migrations
alembic current
# Expected: 1bc72b16a56e (add_guest_performance_indexes)

# Check indexes
psql $DATABASE_URL -c "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE tablename LIKE 'guest%'
ORDER BY tablename, indexname;
"
```

**Expected Output:**

```
 schemaname |      tablename       |              indexname
------------+----------------------+--------------------------------------
 public     | guest_conversations  | idx_guest_conversations_created_at
 public     | guest_conversations  | idx_guest_conversations_user_status_created
 public     | guest_messages       | idx_guest_messages_conversation_created
 public     | guest_messages       | idx_guest_messages_created_at
 public     | guest_messages       | idx_guest_messages_intent
 public     | guest_users          | idx_guest_users_is_blocked
 public     | guest_users          | idx_guest_users_last_seen_at
```

### Step 4: Build & Deploy Application (10 minutes)

**4.1 Build Docker Image**

```bash
# Build production image
docker build -t anvil/api:guest-chat-v1.0 -f Dockerfile.prod .

# Tag for registry
docker tag anvil/api:guest-chat-v1.0 $REGISTRY_URL/anvil/api:guest-chat-v1.0
docker tag anvil/api:guest-chat-v1.0 $REGISTRY_URL/anvil/api:latest

# Push to registry
docker push $REGISTRY_URL/anvil/api:guest-chat-v1.0
docker push $REGISTRY_URL/anvil/api:latest
```

**4.2 Update Kubernetes Deployment**

```bash
# Update deployment configuration
kubectl set image deployment/anvil-api \
  api=$REGISTRY_URL/anvil/api:guest-chat-v1.0 \
  -n production

# Or apply full deployment
kubectl apply -f k8s/production/deployment.yaml

# Watch rollout status
kubectl rollout status deployment/anvil-api -n production
```

**4.3 Gradual Traffic Shifting**

```bash
# Start with 10% traffic to new version
kubectl patch service anvil-api -p '{"spec":{"trafficPolicy":{"canary":{"weight":10}}}}' -n production

# Wait 5 minutes, monitor metrics

# Increase to 50%
kubectl patch service anvil-api -p '{"spec":{"trafficPolicy":{"canary":{"weight":50}}}}' -n production

# Wait 5 minutes, monitor metrics

# Full rollout (100%)
kubectl patch service anvil-api -p '{"spec":{"trafficPolicy":{"canary":{"weight":100}}}}' -n production
```

### Step 5: Warm Redis Cache (5 minutes)

```bash
# Pre-warm cache for popular tokens
python scripts/warm_cache.py --tokens BTC ETH SOL --languages en es pt zh

# Expected output:
# ✅ Warmed BTC sentiment (en, es, pt, zh)
# ✅ Warmed ETH sentiment (en, es, pt, zh)
# ✅ Warmed SOL sentiment (en, es, pt, zh)
# ✅ Cache warming complete: 12 entries cached
```

---

## Post-Deployment Validation

### Automated Health Checks (5 minutes)

**1. Application Health**

```bash
# Check health endpoint
curl https://api.anvil.fi/health
# Expected: {"status": "healthy", "version": "1.0", "timestamp": "..."}

# Check guest chat endpoint
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "language": "en"}'

# Expected: 200 OK with greeting response
```

**2. Database Performance**

```bash
# Check query performance
psql $DATABASE_URL -c "
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename LIKE 'guest%'
ORDER BY idx_scan DESC;
"
```

**3. Cache Performance**

```bash
# Check cache hit rate
redis-cli info stats | grep keyspace
redis-cli info stats | grep hits

# Expected hit rate: >80% after 1 hour
```

### Manual Testing (10 minutes)

**Test Suite:**

1. **Greeting** ✅
   ```bash
   curl -X POST https://api.anvil.fi/api/v1/guest/chat \
     -H "Content-Type: application/json" \
     -d '{"content": "Hello", "language": "en"}'
   ```

2. **Sentiment Analysis** ✅
   ```bash
   curl -X POST https://api.anvil.fi/api/v1/guest/chat \
     -H "Content-Type: application/json" \
     -d '{"content": "What is the sentiment for BTC?", "language": "en"}'
   ```

3. **Trading Signals** ✅
   ```bash
   curl -X POST https://api.anvil.fi/api/v1/guest/chat \
     -H "Content-Type: application/json" \
     -d '{"content": "Give me trading signals for ETH", "language": "en"}'
   ```

4. **Rate Limiting** ✅
   ```bash
   # Send 21 requests rapidly
   for i in {1..21}; do
     curl -X POST https://api.anvil.fi/api/v1/guest/chat \
       -H "Content-Type: application/json" \
       -d "{\"content\": \"test $i\", \"language\": \"en\"}"
   done
   # Expected: First 20 succeed, 21st returns 429
   ```

5. **Multi-Language** ✅
   ```bash
   # Spanish
   curl -X POST https://api.anvil.fi/api/v1/guest/chat \
     -H "Content-Type: application/json" \
     -d '{"content": "¿Cuál es el sentimiento para BTC?", "language": "es"}'
   ```

### Performance Validation (15 minutes)

**Run Load Test:**

```bash
# Install k6 if not present
brew install k6  # macOS
# or
sudo apt install k6  # Ubuntu

# Run load test
k6 run tests/load/guest_chat_load_test.js

# Expected metrics:
# - P95 response time: <500ms
# - Error rate: <1%
# - Throughput: >100 req/s
```

**Load Test Results:**

```
     ✓ status is 200
     ✓ response time < 500ms

     checks.........................: 100.00% ✓ 5000      ✗ 0
     data_received..................: 15 MB   150 kB/s
     data_sent......................: 1.2 MB  12 kB/s
     http_req_duration..............: avg=245ms min=45ms med=210ms max=480ms p(95)=395ms
     http_reqs......................: 5000    50/s
     vus............................: 100     min=100 max=100
     vus_max........................: 100     min=100 max=100
```

---

## Rollback Procedures

### Automatic Rollback

Kubernetes will automatically rollback if:
- Health checks fail for >3 consecutive checks
- Error rate exceeds 5% for >5 minutes
- P95 latency exceeds 2000ms for >5 minutes

### Manual Rollback

**Step 1: Identify Issue** (2 minutes)

```bash
# Check pod status
kubectl get pods -n production | grep anvil-api

# Check logs
kubectl logs -f deployment/anvil-api -n production --tail=100

# Check error rate
kubectl top pods -n production
```

**Step 2: Execute Rollback** (5 minutes)

```bash
# Rollback to previous version
kubectl rollout undo deployment/anvil-api -n production

# Monitor rollback
kubectl rollout status deployment/anvil-api -n production

# Verify pods are healthy
kubectl get pods -n production | grep anvil-api
```

**Step 3: Rollback Database** (if needed)

```bash
# Identify target migration
alembic history

# Downgrade to previous version
alembic downgrade -1

# Or downgrade to specific revision
alembic downgrade <revision_id>

# Verify
alembic current
```

**Step 4: Clear Redis Cache** (1 minute)

```bash
# Clear all guest cache keys
redis-cli --scan --pattern "hunter:*" | xargs redis-cli del
redis-cli --scan --pattern "guest:*" | xargs redis-cli del
redis-cli --scan --pattern "ratelimit:*" | xargs redis-cli del

# Warm cache again
python scripts/warm_cache.py --tokens BTC ETH SOL
```

**Step 5: Verify Rollback** (5 minutes)

```bash
# Test guest chat endpoint
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "language": "en"}'

# Check error rate
# (Should return to normal within 2 minutes)
```

---

## Monitoring & Alerts

### Key Metrics

#### Application Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Error Rate | >1% | Warning |
| Error Rate | >5% | Critical |
| P95 Latency | >500ms | Warning |
| P95 Latency | >2000ms | Critical |
| Requests/Second | <10 | Warning |
| Cache Hit Rate | <70% | Warning |
| Memory Usage | >80% | Warning |
| CPU Usage | >80% | Warning |

#### Database Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Connection Pool Usage | >80% | Warning |
| Slow Queries (>1s) | >10/min | Warning |
| Deadlocks | >0 | Critical |
| Replication Lag | >5s | Warning |

#### Redis Metrics

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Memory Usage | >80% | Warning |
| Evicted Keys | >1000/min | Warning |
| Connection Errors | >0 | Critical |
| Cache Miss Rate | >30% | Warning |

### CloudWatch Dashboards

**Dashboard: Guest Chat Performance**

```
┌─────────────────────────────────────────────────────────────┐
│                   Guest Chat Performance                     │
├──────────────────────┬──────────────────────────────────────┤
│  Request Rate        │  Error Rate                          │
│  [Graph: 100 req/s]  │  [Graph: 0.5%]                      │
├──────────────────────┼──────────────────────────────────────┤
│  P95 Latency         │  Cache Hit Rate                      │
│  [Graph: 250ms]      │  [Graph: 85%]                       │
├──────────────────────┼──────────────────────────────────────┤
│  Hunter AI Success   │  Rate Limit Violations               │
│  [Graph: 98%]        │  [Graph: 12/hour]                   │
└──────────────────────┴──────────────────────────────────────┘
```

### Alert Configuration

**Sentry Alerts:**

```python
# config/sentry.py
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.app_env,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,

    # Alert on errors
    before_send=alert_on_error,

    # Group similar errors
    in_app_include=["app"],
)
```

**PagerDuty Integration:**

- **Critical Alerts**: Page on-call engineer immediately
- **Warning Alerts**: Slack #ops-alerts channel
- **Info Alerts**: Logged to CloudWatch only

---

## Troubleshooting

### Issue 1: High Error Rate

**Symptoms:**
- Error rate >5%
- 500 errors in logs
- Sentry alerts firing

**Diagnosis:**

```bash
# Check pod status
kubectl get pods -n production

# Check logs for errors
kubectl logs deployment/anvil-api -n production | grep ERROR

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

**Resolution:**

1. Check if database is reachable
2. Verify Redis connection
3. Check for Hunter AI service outages (CoinGecko, RSS feeds)
4. Review recent code changes
5. Consider rollback if issue persists >15 minutes

### Issue 2: High Latency

**Symptoms:**
- P95 latency >2000ms
- Slow response times
- Timeout errors

**Diagnosis:**

```bash
# Check database query performance
psql $DATABASE_URL -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Check cache hit rate
redis-cli info stats | grep keyspace_hits

# Check slow logs
kubectl logs deployment/anvil-api -n production | grep "duration > 1000"
```

**Resolution:**

1. Review slow queries and add indexes if needed
2. Increase cache TTL for frequently accessed data
3. Scale up pods: `kubectl scale deployment anvil-api --replicas=10`
4. Review Hunter AI API call patterns

### Issue 3: Cache Miss Rate High

**Symptoms:**
- Cache hit rate <70%
- High API calls to CoinGecko
- Increased latency

**Diagnosis:**

```bash
# Check cache statistics
redis-cli info stats

# Check cache key patterns
redis-cli --scan --pattern "hunter:*" | head -20

# Check cache TTLs
redis-cli --scan --pattern "hunter:*" | while read key; do
  echo "$key: $(redis-cli ttl $key)";
done | head -10
```

**Resolution:**

1. Warm cache: `python scripts/warm_cache.py`
2. Review TTL configurations in `guest_cache.py`
3. Check if cache is being invalidated too frequently
4. Increase Redis memory if evictions are high

### Issue 4: Rate Limit Issues

**Symptoms:**
- Many 429 errors
- Users complaining about limits
- High rate limit violation count

**Diagnosis:**

```bash
# Check rate limit violations
redis-cli --scan --pattern "ratelimit:*" | wc -l

# Check blocked users
psql $DATABASE_URL -c "SELECT count(*) FROM guest_users WHERE is_blocked = true;"

# Check rate limit counter distribution
redis-cli --scan --pattern "ratelimit:counter:*" | while read key; do
  echo "$key: $(redis-cli get $key)";
done | sort -t: -k3 -nr | head -20
```

**Resolution:**

1. Review if limit is too strict (currently 20 msg/hour)
2. Check for bot traffic (repeated IPs)
3. Consider implementing CAPTCHA for high-volume IPs
4. Whitelist legitimate high-volume users

### Issue 5: Database Connection Pool Exhausted

**Symptoms:**
- "Connection pool exhausted" errors
- High connection count
- Slow response times

**Diagnosis:**

```bash
# Check active connections
psql $DATABASE_URL -c "
SELECT state, count(*)
FROM pg_stat_activity
WHERE datname = 'anvil_db'
GROUP BY state;
"

# Check long-running queries
psql $DATABASE_URL -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
AND now() - pg_stat_activity.query_start > interval '5 seconds'
ORDER BY duration DESC;
"
```

**Resolution:**

1. Kill long-running queries: `SELECT pg_terminate_backend(pid);`
2. Increase connection pool size in config
3. Review code for connection leaks
4. Add connection pooling middleware (PgBouncer)

---

## Incident Response

### Severity Levels

| Level | Description | Response Time | Escalation |
|-------|-------------|---------------|------------|
| **P0 - Critical** | Service down, data loss | Immediate | Page on-call + manager |
| **P1 - High** | Degraded service, high errors | <15 min | Page on-call |
| **P2 - Medium** | Partial functionality affected | <1 hour | Slack alert |
| **P3 - Low** | Minor issue, no impact | <4 hours | Log ticket |

### Incident Response Flow

```
┌─────────────────┐
│  Alert Fires    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Acknowledge    │  ← Acknowledge in PagerDuty
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Assess Impact  │  ← Check dashboards, logs
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Mitigate       │  ← Scale, rollback, or fix
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Resolve        │  ← Verify fix, close incident
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Post-Mortem    │  ← Document root cause
└─────────────────┘
```

### On-Call Runbook

**On-Call Engineer Responsibilities:**

1. Respond to pages within 5 minutes
2. Acknowledge incidents in PagerDuty
3. Follow troubleshooting guide
4. Escalate if needed
5. Update status page
6. Write post-mortem

**Emergency Contacts:**

- **On-Call Engineer**: +1-XXX-XXX-XXXX (PagerDuty)
- **Engineering Manager**: manager@anvil.fi
- **DevOps Lead**: devops@anvil.fi
- **CTO**: cto@anvil.fi

---

## Maintenance Windows

### Scheduled Maintenance

- **Frequency**: Monthly (first Sunday, 2-6 AM UTC)
- **Duration**: 4 hours
- **Notification**: 7 days advance notice
- **Status Page**: https://status.anvil.fi

### Maintenance Checklist

**Pre-Maintenance:**

- [ ] Announce maintenance window (7 days prior)
- [ ] Create database backup
- [ ] Test rollback procedures
- [ ] Prepare deployment scripts
- [ ] Schedule team availability

**During Maintenance:**

- [ ] Put system in maintenance mode
- [ ] Apply database migrations
- [ ] Deploy new version
- [ ] Run validation tests
- [ ] Clear caches
- [ ] Re-enable traffic

**Post-Maintenance:**

- [ ] Verify system health
- [ ] Monitor metrics for 1 hour
- [ ] Update status page
- [ ] Send completion notification
- [ ] Document any issues

---

## Appendix

### Environment Variables

```bash
# Application
APP_ENV=prod
APP_DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@host:5432/anvil_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# External APIs
COINGECKO_API_KEY=xxx
TWITTER_API_KEY=xxx
```

### Useful Commands

```bash
# Check application version
curl https://api.anvil.fi/health | jq '.version'

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('anvil_db'));"

# Check Redis memory
redis-cli info memory | grep used_memory_human

# Check pod logs
kubectl logs -f deployment/anvil-api -n production --tail=100

# Scale pods
kubectl scale deployment anvil-api --replicas=10 -n production

# Force pod restart
kubectl rollout restart deployment/anvil-api -n production
```

### Quick Links

- **Production Dashboard**: https://dashboard.anvil.fi
- **Grafana**: https://grafana.anvil.fi
- **Sentry**: https://sentry.io/anvil/api
- **PagerDuty**: https://anvil.pagerduty.com
- **Status Page**: https://status.anvil.fi
- **Docs**: https://docs.anvil.fi

---

**© 2026 Anvil Operations Team. Internal Use Only.**
