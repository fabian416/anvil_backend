# 📊 Anvil Platform - Monitoring & Observability Guide

## Complete Monitoring, Logging, and Alerting Strategy

**Version:** 1.0  
**Date:** November 2025  
**Tools:** CloudWatch, Sentry, Prometheus, Grafana

---

## 🎯 Observability Strategy

### Three Pillars

```
┌──────────────────────────────────────────────────┐
│               METRICS                            │
│  What is happening? (quantitative)               │
│  • Request rates                                 │
│  • Error rates                                   │
│  • Latency                                       │
│  • Resource usage                                │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│               LOGS                               │
│  What happened? (events)                         │
│  • Application logs                              │
│  • Access logs                                   │
│  • Error logs                                    │
│  • Audit logs                                    │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│               TRACES                             │
│  Why did it happen? (context)                    │
│  • Request flows                                 │
│  • Service dependencies                          │
│  • Performance bottlenecks                       │
│  • Error context                                 │
└──────────────────────────────────────────────────┘
```

---

## 📈 Metrics Collection

### Infrastructure Metrics (CloudWatch)

**ECS Task Metrics:**
```yaml
CPU Utilization:
  - Metric: ECSServiceCPUUtilization
  - Threshold: > 70% for 5 minutes
  - Action: Scale up tasks

Memory Utilization:
  - Metric: ECSServiceMemoryUtilization
  - Threshold: > 80% for 5 minutes
  - Action: Scale up tasks / investigate memory leaks

Task Count:
  - Metric: RunningTaskCount
  - Monitor: Ensure matches desired count
  - Alert: If drops below minimum
```

**RDS Metrics:**
```yaml
Database Connections:
  - Metric: DatabaseConnections
  - Threshold: > 80% of max
  - Action: Scale connection pool / add read replica

CPU Utilization:
  - Metric: CPUUtilization
  - Threshold: > 75% for 10 minutes
  - Action: Upgrade instance size

Free Storage Space:
  - Metric: FreeStorageSpace
  - Threshold: < 10GB
  - Action: Increase storage

Read/Write Latency:
  - Metric: ReadLatency, WriteLatency
  - Threshold: > 50ms (P95)
  - Action: Investigate slow queries
```

**ElastiCache Redis Metrics:**
```yaml
CPU Utilization:
  - Metric: CPUUtilization
  - Threshold: > 80%
  - Action: Scale up node

Memory Usage:
  - Metric: DatabaseMemoryUsagePercentage
  - Threshold: > 90%
  - Action: Increase memory / review cache strategy

Cache Hit Rate:
  - Metric: CacheHitRate
  - Target: > 95%
  - Action: Review cache keys and TTLs

Evictions:
  - Metric: Evictions
  - Threshold: > 100/min
  - Action: Increase memory or adjust TTL
```

### Application Metrics (Custom + Prometheus)

**API Metrics:**
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request counters
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Latency histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Active users gauge
active_users_total = Gauge(
    'active_users_total',
    'Number of currently active users'
)

# Business metrics
transactions_total = Counter(
    'transactions_total',
    'Total transactions',
    ['type', 'status', 'chain']
)

transaction_volume_usd = Counter(
    'transaction_volume_usd',
    'Total transaction volume in USD',
    ['type', 'chain']
)


# Middleware for automatic metrics
from fastapi import Request
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect metrics for each request"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

**Business Metrics:**
```python
# Track in service layer
class TradingService:
    async def execute_swap(self, ...):
        # Execute swap
        transaction = await self._execute_swap(...)
        
        # Record metrics
        transactions_total.labels(
            type='swap',
            status=transaction.status,
            chain=transaction.chain
        ).inc()
        
        transaction_volume_usd.labels(
            type='swap',
            chain=transaction.chain
        ).inc(float(transaction.amount_in_usd))
        
        return transaction
```

---

## 📝 Structured Logging

### Logging Configuration

**Python (Structlog):**
```python
# app/core/logging.py
import structlog
import logging
from pythonjsonlogger import jsonlogger

def configure_logging():
    """Configure structured logging"""
    
    # JSON formatter for CloudWatch
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    logHandler.setFormatter(formatter)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logHandler]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

### Logging Best Practices

**Example Logging:**
```python
import structlog

logger = structlog.get_logger()

# ✅ GOOD - Structured with context
logger.info(
    "swap_executed",
    user_id=user.id,
    from_asset="USDC",
    to_asset="ETH",
    amount=50.0,
    tx_hash="0x123...",
    duration_ms=2340
)

logger.warning(
    "rate_limit_exceeded",
    user_id=user.id,
    endpoint="/api/v1/user/trade/quote",
    ip_address=request.client.host
)

logger.error(
    "external_api_error",
    service="1inch",
    error=str(e),
    user_id=user.id,
    exc_info=True  # Include stack trace
)


# ❌ BAD - Unstructured string
logger.info(f"User {user.id} swapped {amount} USDC to ETH")
```

### Log Levels

```yaml
DEBUG:
  Use: Development only
  Example: "Cache hit for key user:123:balance"

INFO:
  Use: Normal operations
  Example: "User 123 executed swap"

WARNING:
  Use: Degraded but functional
  Example: "High latency from 1inch API: 3.5s"

ERROR:
  Use: Request failed but service ok
  Example: "Failed to execute swap: insufficient balance"

CRITICAL:
  Use: Service degradation
  Example: "Database connection pool exhausted"
```

---

## 🔍 Distributed Tracing (Sentry)

### Sentry Setup

**Backend:**
```python
# app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENVIRONMENT,
    traces_sample_rate=0.1,  # Sample 10% of requests
    profiles_sample_rate=0.1,
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
    ],
    before_send=before_send_filter,
)

def before_send_filter(event, hint):
    """Filter out noise from Sentry"""
    # Don't send health check errors
    if event.get('request', {}).get('url', '').endswith('/health'):
        return None
    
    # Don't send validation errors (400s)
    if event.get('response', {}).get('status_code') == 400:
        return None
    
    return event
```

**Mobile:**
```typescript
import * as Sentry from '@sentry/react-native'

Sentry.init({
  dsn: Config.SENTRY_DSN,
  environment: Config.ENVIRONMENT,
  tracesSampleRate: 0.1,
  beforeSend(event, hint) {
    // Filter out network errors from third-party services
    if (event.exception?.values?.[0]?.type === 'NetworkError') {
      return null
    }
    return event
  },
})
```

### Custom Traces

```python
# Add custom spans for performance monitoring
from sentry_sdk import start_span

async def execute_swap(...):
    with start_span(op="swap", description="Execute token swap"):
        # Get quote
        with start_span(op="http", description="Get 1inch quote"):
            quote = await oneinch.get_quote(...)
        
        # Sign transaction
        with start_span(op="crypto", description="Sign transaction"):
            signed_tx = await privy.sign_transaction(...)
        
        # Submit to blockchain
        with start_span(op="blockchain", description="Submit transaction"):
            tx_hash = await web3.send_transaction(...)
        
        return tx_hash
```

---

## 🚨 Alerting Strategy

### Alert Definitions

**Critical Alerts (Page On-Call):**
```yaml
API Down:
  Condition: Health check fails for 2 consecutive minutes
  Severity: P0
  Channel: PagerDuty
  Response: Immediate

Database Down:
  Condition: Cannot connect to RDS for 1 minute
  Severity: P0
  Channel: PagerDuty
  Response: Immediate

High Error Rate:
  Condition: Error rate > 10% for 5 minutes
  Severity: P0
  Channel: PagerDuty
  Response: Immediate

Transaction Failures:
  Condition: >50% transaction failure rate for 3 minutes
  Severity: P0
  Channel: PagerDuty
  Response: Immediate
```

**Warning Alerts (Slack):**
```yaml
High Latency:
  Condition: P95 latency > 1s for 5 minutes
  Severity: P1
  Channel: Slack #alerts
  Response: 1 hour

Resource Utilization:
  Condition: CPU/Memory > 80% for 10 minutes
  Severity: P1
  Channel: Slack #alerts
  Response: 2 hours

Cache Miss Rate:
  Condition: Cache hit rate < 80% for 10 minutes
  Severity: P2
  Channel: Slack #alerts
  Response: 4 hours

Failed Deployments:
  Condition: Deployment fails
  Severity: P1
  Channel: Slack #deployments
  Response: Immediate
```

### Alert Configuration (CloudWatch)

```python
# Infrastructure as Code (Terraform)
resource "aws_cloudwatch_metric_alarm" "api_high_error_rate" {
  alarm_name          = "anvil-api-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "50"
  alarm_description   = "API error rate > 10%"
  alarm_actions       = [aws_sns_topic.pagerduty.arn]

  dimensions = {
    LoadBalancer = aws_lb.anvil.arn_suffix
  }
}

resource "aws_cloudwatch_metric_alarm" "db_connections_high" {
  alarm_name          = "anvil-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"  # 80% of max
  alarm_description   = "Database connections > 80%"
  alarm_actions       = [aws_sns_topic.slack_alerts.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.anvil.id
  }
}
```

---

## 📊 Dashboard Setup

### Grafana Dashboard (API Performance)

```json
{
  "dashboard": {
    "title": "Anvil API Performance",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Latency (P95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "active_users_total",
            "legendFormat": "Active Users"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

### CloudWatch Dashboard (Infrastructure)

```yaml
Widgets:
  - Type: Metric
    Title: ECS Task CPU/Memory
    Metrics:
      - ECSServiceCPUUtilization
      - ECSServiceMemoryUtilization
    Period: 5min
    
  - Type: Metric
    Title: Database Performance
    Metrics:
      - DatabaseConnections
      - ReadLatency
      - WriteLatency
    Period: 5min
    
  - Type: Metric
    Title: Cache Performance
    Metrics:
      - CacheHitRate
      - CacheMemoryUsage
    Period: 5min
    
  - Type: Log
    Title: Recent Errors
    Query: |
      fields @timestamp, @message
      | filter level = "ERROR"
      | sort @timestamp desc
      | limit 20
```

---

## 🔔 Incident Response

### On-Call Rotation

```yaml
Schedule:
  - Primary: 24/7 coverage
  - Secondary: Backup for escalation
  - Rotation: Weekly

Escalation:
  Level 1: On-call engineer (5 min)
  Level 2: Team lead (15 min)
  Level 3: CTO (30 min)
```

### Runbooks

**Example: High Error Rate**
```markdown
# Runbook: High API Error Rate

## Symptoms
- CloudWatch alarm: "anvil-api-high-error-rate"
- Error rate > 10% for 5 minutes

## Investigation Steps

1. Check error distribution:
   ```bash
   # CloudWatch Insights query
   fields @timestamp, endpoint, status, error
   | filter status >= 500
   | stats count() by endpoint, error
   ```

2. Check recent deployments:
   - Look for deployments in last hour
   - Check if errors started after deployment

3. Check external dependencies:
   - 1inch API status
   - Privy API status
   - Stripe API status
   - Blockchain RPC status

4. Check resource utilization:
   - ECS task CPU/memory
   - Database connections
   - Redis memory

## Resolution Steps

If caused by recent deployment:
1. Rollback to previous version
2. Verify error rate drops
3. Investigate failed deployment

If caused by external API:
1. Check if circuit breaker activated
2. Monitor external API status
3. Consider fallback options

If caused by resource exhaustion:
1. Scale up ECS tasks immediately
2. Investigate resource leak
3. Plan long-term fix

## Post-Incident
1. Write post-mortem
2. Identify root cause
3. Implement preventive measures
4. Update monitoring if needed
```

---

## 📈 Key Performance Indicators (KPIs)

### Technical KPIs

```yaml
Availability:
  Target: 99.9% uptime
  Measure: (Total time - Downtime) / Total time
  
Latency:
  Target: P95 < 500ms
  Measure: 95th percentile response time
  
Error Rate:
  Target: < 0.1%
  Measure: Failed requests / Total requests
  
Time to Detect (TTD):
  Target: < 5 minutes
  Measure: Time from incident to alert
  
Time to Resolve (TTR):
  Target: < 1 hour
  Measure: Time from alert to resolution
```

### Business KPIs

```yaml
Transaction Success Rate:
  Target: > 95%
  Measure: Successful transactions / Total transactions
  
Transaction Volume:
  Target: Growing MoM
  Measure: Total USD volume
  
Active Users:
  Target: Growing MoM
  Measure: Daily/Monthly active users
  
User Retention:
  Target: > 40% (30-day)
  Measure: Returning users / New users
```

---

## 🛠️ Monitoring Tools

### Tool Matrix

```yaml
CloudWatch:
  Use: Infrastructure metrics, logs
  Cost: Pay per GB/metric
  Retention: 15 months (metrics), configurable (logs)
  
Sentry:
  Use: Error tracking, performance monitoring
  Cost: ~$100/month
  Retention: 90 days
  
Prometheus + Grafana:
  Use: Application metrics, custom dashboards
  Cost: Self-hosted (EC2 costs)
  Retention: Configurable
  
PagerDuty:
  Use: On-call management, incident response
  Cost: ~$20/user/month
  
Slack:
  Use: Alerts, team communication
  Cost: Free tier sufficient
```

---

## ✅ Monitoring Checklist

### Setup
- [ ] CloudWatch agent installed
- [ ] Structured logging configured
- [ ] Sentry integrated (backend + mobile)
- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards created
- [ ] Alerts configured
- [ ] PagerDuty integration set up
- [ ] Slack integration set up
- [ ] On-call rotation scheduled
- [ ] Runbooks documented

### Daily Operations
- [ ] Check dashboards daily
- [ ] Review error trends
- [ ] Monitor resource usage
- [ ] Check alert fatigue
- [ ] Review slow queries

### Weekly Review
- [ ] Review all alerts
- [ ] Check KPI trends
- [ ] Optimize slow endpoints
- [ ] Review and update runbooks
- [ ] Incident post-mortems

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** DevOps Team  
**On-Call:** Use PagerDuty schedule
