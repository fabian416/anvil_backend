# Guest Chat Production Monitoring

**Date:** 2026-01-11
**Status:** Production Ready
**Environment:** All (local, dev, staging, production)

---

## Overview

This document provides comprehensive monitoring configuration for the guest chat system, including error tracking, metrics collection, alerting, and dashboards.

---

## Table of Contents

1. [Error Tracking (Sentry)](#error-tracking-sentry)
2. [Metrics & Dashboards (CloudWatch)](#metrics--dashboards-cloudwatch)
3. [Alert Configuration](#alert-configuration)
4. [Monitoring Runbook](#monitoring-runbook)
5. [Troubleshooting Guide](#troubleshooting-guide)

---

## Error Tracking (Sentry)

### Configuration

**File:** `src/app/infrastructure/monitoring/sentry_config.py`

```python
"""Sentry error tracking configuration for guest chat system."""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from app.config import settings


def init_sentry():
    """Initialize Sentry error tracking."""
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=f"anvil-backend@{settings.version}",

        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],

        # Performance monitoring
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1,  # 10% of transactions

        # Error filtering
        before_send=before_send_filter,

        # Tags
        tags={
            "service": "guest-chat",
            "component": "api",
        },
    )


def before_send_filter(event, hint):
    """Filter events before sending to Sentry."""
    # Ignore rate limiting errors (expected behavior)
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if exc_type.__name__ == "RateLimitExceeded":
            return None

    # Add custom context
    event["tags"]["guest_system"] = "true"

    return event


# Custom error context for guest chat
def set_guest_context(ip_address: str, conversation_id: str = None):
    """Set guest-specific context for error tracking."""
    with sentry_sdk.configure_scope() as scope:
        scope.set_user({"ip_address": ip_address})
        scope.set_tag("user_type", "guest")
        if conversation_id:
            scope.set_context("conversation", {
                "id": conversation_id,
                "type": "guest_conversation"
            })


# Capture custom events
def capture_hunter_error(
    intent: str,
    token: str,
    error: Exception,
    **extra_context
):
    """Capture Hunter AI errors with context."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("hunter_intent", intent)
        scope.set_tag("token", token)
        scope.set_context("hunter_ai", extra_context)
        sentry_sdk.capture_exception(error)


def capture_cache_error(
    operation: str,
    key: str,
    error: Exception
):
    """Capture Redis cache errors."""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("cache_operation", operation)
        scope.set_tag("cache_key", key)
        sentry_sdk.capture_exception(error)
```

### Environment Variables

**File:** `config/production/.secrets.toml`

```toml
[sentry]
dsn = "https://[key]@[org].ingest.sentry.io/[project]"
environment = "production"
traces_sample_rate = 0.1
profiles_sample_rate = 0.1
```

### Sentry Dashboard Setup

**Custom Dashboards:**

1. **Guest Chat Overview**
   - Total errors (24h)
   - Error rate trend
   - Top 5 error types
   - Response time P95/P99
   - Cache hit rate

2. **Hunter AI Performance**
   - Errors by intent
   - Average response time by intent
   - Cache hit rate by token
   - External API failures

3. **Rate Limiting & Abuse**
   - Rate limit violations (by IP)
   - Blocked IPs
   - Suspicious activity patterns

### Alert Rules

**Critical Alerts:**
- Error rate > 5% (5 min window) → PagerDuty
- P95 response time > 1000ms (5 min window) → PagerDuty
- Database connection errors → PagerDuty
- Redis connection errors → PagerDuty

**Warning Alerts:**
- Error rate > 1% (15 min window) → Slack
- Cache hit rate < 70% (15 min window) → Slack
- Hunter AI failures > 10/min → Slack

---

## Metrics & Dashboards (CloudWatch)

### Custom Metrics

**Application Metrics:**

```python
"""CloudWatch metrics for guest chat system."""
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def put_guest_chat_metric(
    metric_name: str,
    value: float,
    unit: str = 'None',
    dimensions: dict = None
):
    """Send custom metric to CloudWatch."""
    cloudwatch.put_metric_data(
        Namespace='AnvilBackend/GuestChat',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {'Name': k, 'Value': v}
                    for k, v in (dimensions or {}).items()
                ]
            }
        ]
    )


# Track response times
def track_response_time(intent: str, duration_ms: float):
    """Track response time by intent."""
    put_guest_chat_metric(
        'ResponseTime',
        duration_ms,
        'Milliseconds',
        {'Intent': intent}
    )


# Track cache performance
def track_cache_hit(intent: str, token: str, hit: bool):
    """Track cache hit/miss."""
    put_guest_chat_metric(
        'CacheHitRate',
        1.0 if hit else 0.0,
        'None',
        {'Intent': intent, 'Token': token}
    )


# Track Hunter AI errors
def track_hunter_error(intent: str, error_type: str):
    """Track Hunter AI errors."""
    put_guest_chat_metric(
        'HunterAIErrors',
        1.0,
        'Count',
        {'Intent': intent, 'ErrorType': error_type}
    )


# Track rate limiting
def track_rate_limit_violation(ip_address: str):
    """Track rate limit violations."""
    put_guest_chat_metric(
        'RateLimitViolations',
        1.0,
        'Count',
        {'IPAddress': ip_address[:10] + '***'}  # Anonymize
    )
```

### CloudWatch Dashboard JSON

**File:** `infrastructure/cloudwatch/guest_chat_dashboard.json`

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AnvilBackend/GuestChat", "ResponseTime", {"stat": "Average"}],
          ["...", {"stat": "p95"}],
          ["...", {"stat": "p99"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Response Times",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 1000
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AnvilBackend/GuestChat", "CacheHitRate", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Cache Hit Rate",
        "yAxis": {
          "left": {
            "min": 0,
            "max": 100
          }
        }
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AnvilBackend/GuestChat", "HunterAIErrors", {"stat": "Sum"}],
          ["...", {"stat": "Sum", "label": "Errors/5min"}]
        ],
        "period": 300,
        "stat": "Sum",
        "region": "us-east-1",
        "title": "Hunter AI Errors"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "DatabaseConnections"],
          ["AWS/RDS", "CPUUtilization"],
          ["AWS/RDS", "FreeableMemory"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Database Health"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ElastiCache", "CurrConnections"],
          ["AWS/ElastiCache", "CPUUtilization"],
          ["AWS/ElastiCache", "NetworkBytesIn"],
          ["AWS/ElastiCache", "NetworkBytesOut"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Redis Cache Health"
      }
    }
  ]
}
```

### Metrics to Track

| Metric | Unit | Target | Alert Threshold |
|--------|------|--------|-----------------|
| **Response Times** |
| Average Response Time | ms | <200 | >500 |
| P95 Response Time | ms | <500 | >1000 |
| P99 Response Time | ms | <1000 | >2000 |
| **Cache Performance** |
| Cache Hit Rate | % | >80% | <70% |
| Cache Miss Rate | % | <20% | >30% |
| Redis Memory Usage | MB | <500 | >800 |
| **Error Rates** |
| Total Errors | count/min | <5 | >20 |
| Error Rate | % | <1% | >5% |
| Hunter AI Failures | count/min | <2 | >10 |
| **Database** |
| Connection Count | count | <50 | >80 |
| Query Time P95 | ms | <50 | >200 |
| **Rate Limiting** |
| Violations | count/hour | <100 | >500 |
| Blocked IPs | count | <50 | >200 |

---

## Alert Configuration

### CloudWatch Alarms

**Critical Alarms (PagerDuty):**

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-high-error-rate \
  --alarm-description "Guest chat error rate > 5%" \
  --metric-name ErrorRate \
  --namespace AnvilBackend/GuestChat \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:pagerduty-critical

# Slow response time alarm
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-slow-responses \
  --alarm-description "Guest chat P95 > 1000ms" \
  --metric-name ResponseTime \
  --namespace AnvilBackend/GuestChat \
  --statistic p95 \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1000.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:pagerduty-critical

# Database connection errors
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-db-connection-errors \
  --alarm-description "Database connection failures" \
  --metric-name DatabaseErrors \
  --namespace AnvilBackend/GuestChat \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:pagerduty-critical

# Redis connection errors
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-redis-connection-errors \
  --alarm-description "Redis connection failures" \
  --metric-name RedisErrors \
  --namespace AnvilBackend/GuestChat \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 1 \
  --threshold 5.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:pagerduty-critical
```

**Warning Alarms (Slack):**

```bash
# Low cache hit rate
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-low-cache-hit-rate \
  --alarm-description "Cache hit rate < 70%" \
  --metric-name CacheHitRate \
  --namespace AnvilBackend/GuestChat \
  --statistic Average \
  --period 900 \
  --evaluation-periods 2 \
  --threshold 70.0 \
  --comparison-operator LessThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:slack-warnings

# High Hunter AI failure rate
aws cloudwatch put-metric-alarm \
  --alarm-name guest-chat-hunter-failures \
  --alarm-description "Hunter AI failures > 10/min" \
  --metric-name HunterAIErrors \
  --namespace AnvilBackend/GuestChat \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 10.0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:slack-warnings
```

### Alert Channels

**PagerDuty (Critical):**
- On-call engineer notified immediately
- 5-minute escalation if not acknowledged
- Incidents automatically created

**Slack (Warnings):**
- `#alerts-guest-chat` channel
- Context-rich messages with links to dashboards
- Auto-resolve when alarm clears

**Email (Informational):**
- Daily digest of metrics
- Weekly performance reports
- Monthly capacity planning reports

---

## Monitoring Runbook

### Daily Monitoring Tasks

**Morning Check (9 AM):**
1. Review overnight errors in Sentry
2. Check CloudWatch dashboard for anomalies
3. Verify cache hit rate > 80%
4. Check for any rate limiting spikes

**Afternoon Check (2 PM):**
1. Monitor P95 response times during peak traffic
2. Review database connection pool usage
3. Check Redis memory usage
4. Verify no critical alarms triggered

### Weekly Monitoring Tasks

**Every Monday:**
1. Review error trends from past week
2. Analyze cache performance by token
3. Identify top rate-limited IPs
4. Review Hunter AI performance by intent
5. Check for security incidents

### Monthly Monitoring Tasks

**First of Month:**
1. Generate monthly performance report
2. Review capacity planning metrics
3. Analyze cost optimization opportunities
4. Update alert thresholds based on trends

### Health Check Queries

**PostgreSQL Performance:**
```sql
-- Top slow queries
SELECT
    query,
    calls,
    total_time / calls AS avg_time_ms,
    min_time,
    max_time
FROM pg_stat_statements
WHERE query LIKE '%guest%'
ORDER BY total_time DESC
LIMIT 10;

-- Index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename IN ('guest_users', 'guest_conversations', 'guest_messages')
ORDER BY idx_scan DESC;

-- Connection pool status
SELECT
    datname,
    numbackends,
    xact_commit,
    xact_rollback
FROM pg_stat_database
WHERE datname = 'anvil_db';
```

**Redis Performance:**
```bash
# Cache hit rate
redis-cli INFO stats | grep keyspace_hits
redis-cli INFO stats | grep keyspace_misses

# Memory usage
redis-cli INFO memory | grep used_memory_human

# Slow operations
redis-cli SLOWLOG GET 10

# Key distribution
redis-cli --scan --pattern 'hunter:*' | wc -l
```

---

## Troubleshooting Guide

### High Error Rate (>5%)

**Symptoms:**
- Error rate alarm triggered
- Multiple errors in Sentry
- User complaints about failures

**Investigation Steps:**
1. Check Sentry for error patterns
2. Review CloudWatch logs for stack traces
3. Check external service status (CoinGecko, RSS feeds)
4. Verify database connectivity
5. Check Redis connectivity

**Common Causes:**
- External API downtime → Switch to fallback data
- Database connection pool exhausted → Increase pool size
- Redis cache unavailable → Disable caching temporarily
- Rate limiting issues → Review rate limit logic

**Resolution:**
```bash
# Check external services
curl https://api.coingecko.com/api/v3/ping

# Check database
psql -h localhost -U postgres -d anvil_db -c "SELECT 1;"

# Check Redis
redis-cli ping

# Review error logs
tail -f logs/guest_chat_errors.log
```

### Slow Response Times (P95 > 1000ms)

**Symptoms:**
- Slow response alarm triggered
- Users reporting delays
- High CPU/memory usage

**Investigation Steps:**
1. Check cache hit rate (should be >80%)
2. Review database query performance
3. Check external API response times
4. Monitor CPU/memory usage
5. Check for database locks

**Common Causes:**
- Low cache hit rate → Increase TTL or pre-warm cache
- Slow database queries → Add missing indexes
- External API slow → Increase timeout, add circuit breaker
- High traffic → Scale horizontally

**Resolution:**
```bash
# Check cache stats
redis-cli INFO stats

# Check slow queries
psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Monitor system resources
top -b -n 1 | head -20
```

### Low Cache Hit Rate (<70%)

**Symptoms:**
- Cache hit rate alarm triggered
- High response times
- Increased external API calls

**Investigation Steps:**
1. Check Redis memory usage
2. Review cache key patterns
3. Check TTL configuration
4. Monitor cache evictions
5. Verify cache warming is working

**Common Causes:**
- Cache keys evicted due to memory → Increase Redis memory
- TTL too short → Increase TTL for stable data
- Cache not warmed → Implement cache warming
- Too many unique keys → Optimize key patterns

**Resolution:**
```bash
# Check cache memory
redis-cli INFO memory

# Check evicted keys
redis-cli INFO stats | grep evicted_keys

# Manually warm cache
python scripts/warm_cache.py

# Increase Redis maxmemory
redis-cli CONFIG SET maxmemory 2gb
```

### Database Connection Issues

**Symptoms:**
- Database connection errors in Sentry
- Connection pool exhausted warnings
- Slow database queries

**Investigation Steps:**
1. Check connection pool size
2. Review active connections
3. Check for long-running queries
4. Monitor database CPU/memory
5. Check for locks

**Common Causes:**
- Pool size too small → Increase pool size
- Connection leaks → Fix connection handling
- Long-running queries → Optimize or kill
- Database overloaded → Scale up or add read replicas

**Resolution:**
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'anvil_db';

-- Kill long-running queries
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

### Rate Limiting Issues

**Symptoms:**
- High rate limit violations
- Legitimate users blocked
- Suspicious IP patterns

**Investigation Steps:**
1. Check rate limit violation logs
2. Review blocked IP addresses
3. Analyze traffic patterns
4. Check for DDoS attempts
5. Verify rate limit thresholds

**Common Causes:**
- DDoS attack → Block IPs, enable WAF
- Threshold too low → Increase limits
- Shared IPs (NAT) → Implement fingerprinting
- Bot traffic → Add CAPTCHA

**Resolution:**
```python
# Review rate limit violations
SELECT ip_address, COUNT(*) as violations
FROM guest_messages
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) > 20
ORDER BY violations DESC;

# Unblock IP
UPDATE guest_users SET is_blocked = false WHERE ip_address = '1.2.3.4';

# Adjust rate limit
# Update config/production/settings.toml
[rate_limiting]
max_messages_per_hour = 30  # Increase from 20
```

---

## Performance Baselines

**Normal Operating Conditions:**
- Response Time P95: 100-200ms
- Cache Hit Rate: 85-95%
- Error Rate: <0.5%
- Database Connections: 20-40
- Redis Memory: 200-400MB
- CPU Usage: 20-40%
- Memory Usage: 1-2GB

**Peak Traffic Conditions:**
- Response Time P95: 200-400ms
- Cache Hit Rate: 80-90%
- Error Rate: <1%
- Database Connections: 40-60
- Redis Memory: 400-600MB
- CPU Usage: 40-60%
- Memory Usage: 2-3GB

**Alert Conditions:**
- Response Time P95: >1000ms
- Cache Hit Rate: <70%
- Error Rate: >5%
- Database Connections: >80
- Redis Memory: >800MB
- CPU Usage: >80%
- Memory Usage: >4GB

---

## Monitoring Checklist

**Initial Setup:**
- [ ] Sentry DSN configured in production secrets
- [ ] CloudWatch dashboard created
- [ ] Custom metrics integrated in application code
- [ ] Alert rules configured (critical and warning)
- [ ] PagerDuty integration tested
- [ ] Slack integration tested
- [ ] Health check endpoints working
- [ ] Log aggregation configured

**Ongoing Maintenance:**
- [ ] Daily error review
- [ ] Weekly performance analysis
- [ ] Monthly capacity planning
- [ ] Quarterly threshold tuning
- [ ] Alert response time < 5 minutes
- [ ] Incident post-mortems documented

---

**Last Updated:** 2026-01-11
**Version:** 1.0
**Owner:** Backend Team
