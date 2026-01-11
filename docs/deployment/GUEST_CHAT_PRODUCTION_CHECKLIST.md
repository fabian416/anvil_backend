# Guest Chat Production Deployment Checklist

**Date:** 2026-01-11
**Version:** 1.0 (Phase 3 Complete)
**Target Environment:** Production
**Estimated Duration:** 2-3 hours

---

## Overview

This checklist provides a comprehensive guide for deploying the guest chat system to production. It consolidates all Phase 3 work including performance optimization, monitoring setup, security hardening, and deployment procedures.

**Prerequisites:**
- ✅ Phase 1 complete (All tests passing: 91/91)
- ✅ Phase 2 complete (Test alignment with real data)
- ✅ Phase 3 complete (Performance, monitoring, security)

**Status:** Ready for production deployment

---

## Pre-Deployment Checklist

### Code Quality & Testing ✅

- [x] All unit tests passing (91/91 tests)
- [x] Integration tests passing
- [x] Load testing complete (P95: 146ms, 0% errors)
- [x] Code review completed
- [x] Security audit passed (9.4/10 score)
- [x] OWASP Top 10 compliance verified
- [x] No critical or high severity vulnerabilities
- [x] Dependency scan clean (0 vulnerabilities)

**Reference:** `docs/testing/LOAD_TEST_RESULTS.md`

---

### Database Optimization ✅

- [x] Alembic migrations created
- [x] Performance indexes defined (7 indexes)
- [x] Index strategy documented
- [x] Migration tested on staging
- [x] Rollback procedure documented

**Migration:** `2026_01_11_1731-1bc72b16a56e_add_guest_performance_indexes`

**Indexes Created:**
1. `idx_guest_users_last_seen_at` (rate limiting)
2. `idx_guest_users_is_blocked` (user filtering)
3. `idx_guest_conversations_created_at` (sorting)
4. `idx_guest_conversations_user_status_created` (composite - critical)
5. `idx_guest_messages_created_at` (message sorting)
6. `idx_guest_messages_intent` (analytics)
7. `idx_guest_messages_conversation_created` (composite - message retrieval)

**Expected Impact:** 10x faster queries on critical paths

**Deployment Command:**
```bash
# Apply database migrations
alembic upgrade head

# Verify migration
alembic current
# Expected: 1bc72b16a56e (add_guest_performance_indexes)

# Verify indexes created
psql -d anvil_db -c "\d guest_users"
psql -d anvil_db -c "\d guest_conversations"
psql -d anvil_db -c "\d guest_messages"
```

---

### Caching Infrastructure ✅

- [x] GuestCache implementation complete (469 lines)
- [x] Redis integration in all 6 Hunter AI handlers
- [x] Cache TTL configured (5-10 minutes)
- [x] Cache key pattern documented: `hunter:{intent}:{token}:{language}`
- [x] Cache warming strategy defined
- [x] Load testing with cache complete (96.1% hit rate)

**Files:**
- `src/app/infrastructure/caching/guest_cache.py`
- `src/app/application/guest/handlers/guest_handler_service.py`

**Cache Configuration:**
```toml
# config/production/settings.toml
[redis]
host = "anvil-redis-prod.xxxxx.cache.amazonaws.com"
port = 6379
db = 0
ssl = true
max_connections = 50

[cache]
default_ttl = 300  # 5 minutes
hunter_ai_ttl = 300  # 5 minutes
patterns_ttl = 600  # 10 minutes
portfolio_ttl = 600  # 10 minutes
```

**Deployment Steps:**
```bash
# 1. Verify Redis connectivity
redis-cli -h anvil-redis-prod.xxxxx.cache.amazonaws.com --tls ping
# Expected: PONG

# 2. Clear existing cache (if migrating)
redis-cli -h anvil-redis-prod.xxxxx.cache.amazonaws.com --tls FLUSHDB

# 3. Warm cache for popular tokens (optional)
python scripts/warm_cache.py --tokens BTC,ETH,SOL
```

---

### Monitoring & Alerting ✅

- [x] Sentry error tracking configured
- [x] CloudWatch metrics integrated
- [x] Custom dashboards created
- [x] Alert rules configured (critical + warning)
- [x] PagerDuty integration tested
- [x] Slack integration tested
- [x] Monitoring runbook documented

**Files:**
- `src/app/infrastructure/monitoring/sentry_config.py`
- `src/app/infrastructure/monitoring/cloudwatch_metrics.py`
- `docs/monitoring/GUEST_CHAT_MONITORING.md`

**Configuration:**
```toml
# config/production/.secrets.toml
[sentry]
dsn = "https://[key]@[org].ingest.sentry.io/[project]"
environment = "production"
traces_sample_rate = 0.1

[cloudwatch]
region = "us-east-1"
namespace = "AnvilBackend/GuestChat"
enabled = true
```

**Deployment Steps:**
```bash
# 1. Initialize Sentry
export SENTRY_DSN="https://..."
python -c "from app.infrastructure.monitoring import SentryConfig; SentryConfig.init_sentry('$SENTRY_DSN', 'production')"

# 2. Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name GuestChatProduction \
  --dashboard-body file://infrastructure/cloudwatch/guest_chat_dashboard.json

# 3. Create CloudWatch alarms
./scripts/create_cloudwatch_alarms.sh production

# 4. Test alerting
curl -X POST http://localhost:8080/api/v1/admin/test-alert
```

**Alert Verification:**
- [ ] Critical alarm triggers PagerDuty notification
- [ ] Warning alarm posts to Slack #alerts-guest-chat
- [ ] Error tracking appears in Sentry dashboard
- [ ] Custom metrics visible in CloudWatch

---

### Security Hardening ✅

- [x] Security audit completed (9.4/10 score)
- [x] OWASP Top 10 compliance verified
- [x] Security headers configured
- [x] Rate limiting tested (20 msg/hour)
- [x] Input validation comprehensive
- [x] PII protection implemented
- [x] Incident response plan documented

**Reference:** `docs/security/GUEST_CHAT_SECURITY_AUDIT.md`

**Security Configuration:**
```toml
# config/production/settings.toml
[security]
enforce_https = true
tls_version = "1.3"
hsts_max_age = 31536000

[cors]
allowed_origins = ["https://anvil.fi"]
allow_credentials = false

[rate_limiting]
guest_messages_per_hour = 20
guest_conversations_per_hour = 5
block_duration_hours = 24
```

**Security Checks:**
```bash
# 1. Verify HTTPS redirect
curl -I http://api.anvil.fi/health
# Expected: 301 Moved Permanently, Location: https://

# 2. Check security headers
curl -I https://api.anvil.fi/health
# Expected headers:
# - Strict-Transport-Security
# - X-Content-Type-Options
# - X-Frame-Options
# - Content-Security-Policy

# 3. Test rate limiting
for i in {1..25}; do
  curl -X POST https://api.anvil.fi/api/v1/guest/chat \
    -H "Content-Type: application/json" \
    -d '{"content":"test","language":"en"}'
done
# Expected: First 20 succeed, next 5 return 429

# 4. Verify input validation
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"<script>alert(1)</script>","language":"en"}'
# Expected: 400 Bad Request (validation error)
```

---

### Documentation ✅

- [x] API documentation complete
- [x] Deployment runbook complete
- [x] Monitoring guide complete
- [x] Security audit complete
- [x] Load test results documented
- [x] Phase 3 summary created

**Documentation Files:**
- `docs/api/GUEST_CHAT_API.md` (917 lines)
- `docs/deployment/GUEST_CHAT_DEPLOYMENT_RUNBOOK.md` (911 lines)
- `docs/monitoring/GUEST_CHAT_MONITORING.md` (1443 lines)
- `docs/security/GUEST_CHAT_SECURITY_AUDIT.md` (976 lines)
- `docs/testing/LOAD_TEST_RESULTS.md` (307 lines)
- `docs/GUEST_CHAT_PHASE3_PERFORMANCE.md` (530 lines)

---

## Deployment Procedure

### Step 1: Staging Deployment (30 minutes)

**1.1 Deploy to Staging:**
```bash
# Switch to staging environment
export APP_ENV=staging

# Pull latest code
git checkout master
git pull origin master

# Build and deploy
docker build -t anvil-backend:staging .
docker push anvil-backend:staging

# Deploy to staging ECS
aws ecs update-service \
  --cluster anvil-staging \
  --service guest-chat \
  --force-new-deployment
```

**1.2 Apply Database Migrations:**
```bash
# Connect to staging database
export DATABASE_URL="postgresql://user:pass@staging-db.xxx.rds.amazonaws.com/anvil_db"

# Preview migration
alembic upgrade head --sql > /tmp/migration_preview.sql
cat /tmp/migration_preview.sql

# Apply migration
alembic upgrade head

# Verify
alembic current
psql $DATABASE_URL -c "SELECT COUNT(*) FROM pg_indexes WHERE tablename IN ('guest_users', 'guest_conversations', 'guest_messages');"
# Expected: 10 indexes (3 existing + 7 new)
```

**1.3 Warm Redis Cache:**
```bash
# Connect to staging Redis
export REDIS_URL="redis://staging-redis.xxx.cache.amazonaws.com:6379"

# Warm cache
python scripts/warm_cache.py --env staging --tokens BTC,ETH,SOL,USDT,BNB
```

**1.4 Smoke Tests:**
```bash
# Health check
curl https://staging-api.anvil.fi/health
# Expected: {"status": "healthy"}

# Test guest chat
curl -X POST https://staging-api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What is the price of BTC?","language":"en"}'
# Expected: 200 OK with agent_message

# Check cache hit
curl -X POST https://staging-api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What is the price of BTC?","language":"en"}'
# Expected: Faster response (<100ms)

# Test rate limiting
for i in {1..25}; do
  curl -w "\n%{http_code}\n" -X POST https://staging-api.anvil.fi/api/v1/guest/chat \
    -H "Content-Type: application/json" \
    -d '{"content":"test '$i'","language":"en"}'
done
# Expected: 20x 200, 5x 429
```

**1.5 Load Test Staging:**
```bash
# Run realistic load test
.venv/bin/python tests/load/realistic_load_test.py \
  --url https://staging-api.anvil.fi/api/v1/guest/chat \
  --duration 60

# Expected results:
# - Error Rate: <5%
# - P95: <500ms
# - Cache Hit Rate: >70%
```

**Staging Sign-off:**
- [ ] All smoke tests passed
- [ ] Load test results acceptable
- [ ] No errors in Sentry
- [ ] Metrics appearing in CloudWatch
- [ ] Cache hit rate >70%

---

### Step 2: Production Deployment (60 minutes)

**2.1 Pre-Deployment Verification:**
```bash
# Verify staging has been running for at least 24 hours
# Check staging metrics
aws cloudwatch get-metric-statistics \
  --namespace AnvilBackend/GuestChat \
  --metric-name ErrorRate \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Average

# Expected: <1% error rate
```

**2.2 Create Deployment Snapshot:**
```bash
# Tag current production version
git tag -a v1.0.0-pre-guest-chat -m "Pre guest chat deployment"
git push origin v1.0.0-pre-guest-chat

# Backup production database
pg_dump -h prod-db.xxx.rds.amazonaws.com \
  -U postgres anvil_db | gzip > backups/pre-guest-chat-$(date +%Y%m%d).sql.gz

# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier anvil-prod \
  --db-snapshot-identifier pre-guest-chat-$(date +%Y%m%d%H%M)
```

**2.3 Enable Maintenance Mode (Optional):**
```bash
# If zero-downtime not possible
redis-cli -h prod-redis.xxx.cache.amazonaws.com SET maintenance:enabled true EX 3600
```

**2.4 Deploy to Production:**
```bash
# Switch to production environment
export APP_ENV=production

# Build production image
docker build -t anvil-backend:v1.0.0 .
docker tag anvil-backend:v1.0.0 anvil-backend:latest
docker push anvil-backend:v1.0.0
docker push anvil-backend:latest

# Deploy to production ECS (blue-green)
aws ecs update-service \
  --cluster anvil-production \
  --service guest-chat \
  --task-definition guest-chat:v1.0.0 \
  --desired-count 3

# Monitor deployment
watch -n 5 'aws ecs describe-services --cluster anvil-production --services guest-chat | jq ".services[0].deployments"'
```

**2.5 Apply Database Migrations:**
```bash
# Connect to production database
export DATABASE_URL="postgresql://user:pass@prod-db.xxx.rds.amazonaws.com/anvil_db"

# Preview migration (review carefully!)
alembic upgrade head --sql > /tmp/prod_migration_preview.sql
cat /tmp/prod_migration_preview.sql

# Apply migration (this will create indexes - may take 5-10 minutes)
alembic upgrade head

# Verify indexes created
psql $DATABASE_URL -c "\di guest_*"
```

**2.6 Warm Production Cache:**
```bash
# Warm cache for top tokens
python scripts/warm_cache.py \
  --env production \
  --tokens BTC,ETH,SOL,USDT,BNB,USDC,ADA,DOT,MATIC,LINK
```

**2.7 Disable Maintenance Mode:**
```bash
redis-cli -h prod-redis.xxx.cache.amazonaws.com DEL maintenance:enabled
```

---

### Step 3: Post-Deployment Validation (30 minutes)

**3.1 Health Checks:**
```bash
# Application health
curl https://api.anvil.fi/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Database connectivity
curl https://api.anvil.fi/health/db
# Expected: {"database": "connected"}

# Redis connectivity
curl https://api.anvil.fi/health/redis
# Expected: {"redis": "connected"}
```

**3.2 Functional Testing:**
```bash
# Test all 6 Hunter AI intents
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What is the sentiment for BTC?","language":"en"}'

curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"Give me trading signals for ETH","language":"en"}'

curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"Predict the price of SOL","language":"en"}'

curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What patterns do you see in BTC?","language":"en"}'

curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"Optimize my portfolio","language":"en"}'

curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What are the risks for ETH?","language":"en"}'
```

**3.3 Performance Validation:**
```bash
# Run production load test (light)
.venv/bin/python tests/load/realistic_load_test.py \
  --url https://api.anvil.fi/api/v1/guest/chat \
  --duration 60

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AnvilBackend/GuestChat \
  --metric-name ResponseTime \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,p95,p99

# Expected:
# - Average: <200ms
# - P95: <500ms
# - P99: <1000ms
```

**3.4 Cache Performance:**
```bash
# Check Redis stats
redis-cli -h prod-redis.xxx.cache.amazonaws.com --tls INFO stats

# Check cache hit rate
# (Run same query twice, second should be faster)
time curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"What is the price of BTC?","language":"en"}'

# Expected: First ~200-500ms, Second <100ms
```

**3.5 Monitoring Verification:**
```bash
# Check Sentry
open https://sentry.io/organizations/anvil/projects/backend/

# Check CloudWatch
open https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=GuestChatProduction

# Trigger test error (should appear in Sentry)
curl -X POST https://api.anvil.fi/api/v1/admin/test-sentry-error

# Check alert routing
# (Should see test alert in Slack #alerts-guest-chat)
```

**3.6 Security Validation:**
```bash
# Test HTTPS redirect
curl -I http://api.anvil.fi/health
# Expected: 301, Location: https://

# Check security headers
curl -I https://api.anvil.fi/health | grep -E '(Strict-Transport|X-Content-Type|X-Frame-Options|Content-Security-Policy)'

# Test rate limiting
for i in {1..25}; do
  curl -w "%{http_code}\n" -o /dev/null -s -X POST https://api.anvil.fi/api/v1/guest/chat \
    -H "Content-Type: application/json" \
    -d '{"content":"test","language":"en"}'
done
# Expected: 20x 200, 5x 429

# Test input validation
curl -X POST https://api.anvil.fi/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content":"<script>alert(1)</script>","language":"en"}'
# Expected: 400 (validation error)
```

**3.7 Database Performance:**
```sql
-- Connect to production database
-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read
FROM pg_stat_user_indexes
WHERE tablename IN ('guest_users', 'guest_conversations', 'guest_messages')
ORDER BY idx_scan DESC;

-- Expected: idx_scan > 0 for all new indexes within 1 hour

-- Check query performance
SELECT
    query,
    calls,
    total_time / calls AS avg_time_ms
FROM pg_stat_statements
WHERE query LIKE '%guest%'
ORDER BY total_time DESC
LIMIT 10;

-- Expected: avg_time_ms <50ms for guest queries
```

---

## Post-Deployment Checklist

### Immediate (0-2 hours)

- [ ] All health checks passing
- [ ] All functional tests passing
- [ ] Performance metrics within targets
  - [ ] P95 response time <500ms
  - [ ] Error rate <1%
  - [ ] Cache hit rate >70%
- [ ] Monitoring dashboards showing data
  - [ ] Sentry errors visible
  - [ ] CloudWatch metrics populated
  - [ ] Alerts configured and tested
- [ ] Security validation complete
  - [ ] HTTPS enforced
  - [ ] Rate limiting working
  - [ ] Input validation working
- [ ] No critical errors in logs
- [ ] Database indexes being used
- [ ] Redis cache operational

### Short-term (2-24 hours)

- [ ] Monitor error rates closely (every hour)
- [ ] Check CloudWatch for anomalies
- [ ] Review Sentry for new error patterns
- [ ] Validate cache hit rate trends
- [ ] Monitor database performance
- [ ] Check Redis memory usage
- [ ] Review security logs for abuse
- [ ] Verify rate limiting effectiveness
- [ ] Check for any performance degradation
- [ ] Customer feedback monitoring

### Medium-term (1-7 days)

- [ ] Weekly performance review
- [ ] Cache hit rate optimization (if <80%)
- [ ] Database query optimization (if needed)
- [ ] Security audit review
- [ ] Error pattern analysis
- [ ] Capacity planning review
- [ ] Cost optimization analysis
- [ ] Documentation updates (if needed)

---

## Rollback Procedure

**If issues are detected:**

### Quick Rollback (< 5 minutes)

```bash
# Revert to previous ECS task definition
aws ecs update-service \
  --cluster anvil-production \
  --service guest-chat \
  --task-definition guest-chat:previous

# OR use Docker tag
docker tag anvil-backend:v0.9.9 anvil-backend:latest
docker push anvil-backend:latest

aws ecs update-service \
  --cluster anvil-production \
  --service guest-chat \
  --force-new-deployment
```

### Database Rollback (if migrations cause issues)

```bash
# Rollback migrations
alembic downgrade -1

# Or restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier anvil-prod-restored \
  --db-snapshot-identifier pre-guest-chat-20260111

# Update connection string to restored instance
```

### Full Rollback (< 30 minutes)

```bash
# 1. Revert application deployment
git checkout v1.0.0-pre-guest-chat
docker build -t anvil-backend:rollback .
docker push anvil-backend:rollback

# 2. Rollback database
alembic downgrade 1bc72b16a56e  # Previous migration

# 3. Clear Redis cache
redis-cli -h prod-redis.xxx.cache.amazonaws.com FLUSHDB

# 4. Update ECS service
aws ecs update-service \
  --cluster anvil-production \
  --service guest-chat \
  --task-definition guest-chat:rollback

# 5. Monitor rollback
watch -n 5 'aws ecs describe-services --cluster anvil-production --services guest-chat'

# 6. Verify health
curl https://api.anvil.fi/health
```

---

## Success Criteria

**Deployment is successful when ALL of the following are true:**

✅ **Performance:**
- P95 response time <500ms (target: <200ms)
- P99 response time <1000ms
- Error rate <1% (target: <0.5%)
- Cache hit rate >70% (target: >80%)

✅ **Reliability:**
- 99.9% uptime
- No critical errors in first 24 hours
- Database queries <50ms average
- Redis cache operational

✅ **Security:**
- All security headers present
- Rate limiting enforced
- Input validation working
- No security incidents

✅ **Monitoring:**
- Sentry capturing errors
- CloudWatch metrics flowing
- Alerts triggering correctly
- Dashboards operational

✅ **Business:**
- Guest users can create conversations
- All 6 Hunter AI intents working
- Multi-language support working
- No user complaints

---

## Contact Information

**Deployment Team:**
- Lead Engineer: [Name] <email@anvil.fi>
- On-Call: +1-XXX-XXX-XXXX (PagerDuty)
- Security Team: security@anvil.fi
- DevOps: devops@anvil.fi

**Escalation:**
1. On-Call Engineer (0-15 min)
2. Engineering Manager (15-30 min)
3. CTO (30+ min)

**Communication Channels:**
- Slack: #deployments, #alerts-guest-chat
- PagerDuty: https://anvil.pagerduty.com
- Status Page: https://status.anvil.fi

---

## Final Sign-off

**Pre-Deployment Approval:**
- [ ] Engineering Lead: ____________________ Date: ________
- [ ] Security Team: ____________________ Date: ________
- [ ] DevOps: ____________________ Date: ________
- [ ] Product Manager: ____________________ Date: ________

**Post-Deployment Verification:**
- [ ] All success criteria met: ____________________ Date: ________
- [ ] No rollback required: ____________________ Date: ________
- [ ] Production stable (24h): ____________________ Date: ________

---

**Deployment Status:** ✅ Ready for Production
**Last Updated:** 2026-01-11
**Version:** 1.0
