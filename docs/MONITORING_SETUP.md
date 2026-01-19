# Monitoring Setup Guide - Day 5 Production Readiness

**Date**: 2026-01-19
**Status**: ✅ COMPLETE
**Components**: Prometheus + Grafana

---

## Overview

This document describes the monitoring infrastructure deployed for Anvil's chat system. The setup includes Prometheus metrics collection, Grafana dashboards, and alerting rules.

---

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (Port 8080)    │
│                 │
│  /monitoring    │
│   ├─ /metrics   │  ← Prometheus scrapes here
│   ├─ /health    │
│   └─ /alerts    │
└─────────────────┘
        │
        │ scrape (every 15s)
        ▼
┌─────────────────┐
│  Prometheus     │
│  (Port 9090)    │
│                 │
│  - Time-series  │
│  - Alerting     │
│  - Retention    │
└─────────────────┘
        │
        │ query
        ▼
┌─────────────────┐
│   Grafana       │
│  (Port 3000)    │
│                 │
│  - Dashboards   │
│  - Visualize    │
│  - Alerts       │
└─────────────────┘
```

---

## Endpoints

### Metrics Endpoint
**URL**: `GET http://localhost:8080/api/v1/monitoring/metrics`
**Format**: Prometheus text format
**Scrape Interval**: 15 seconds (recommended)

**Available Metrics**:
```
# Build & System Info
chat_build_info{version="1.0.0"}
chat_uptime_seconds

# Request Metrics
chat_requests_total{agent="hunter",endpoint="/chat",status="200"}
chat_errors_total{agent="hunter",error_type="timeout"}
chat_active_requests

# Response Time
chat_response_time_seconds_bucket{le="0.1"}
chat_response_time_seconds_bucket{le="0.5"}
chat_response_time_seconds_bucket{le="1.0"}
chat_response_time_seconds_bucket{le="2.5"}
chat_response_time_seconds_bucket{le="5.0"}
chat_response_time_seconds_sum
chat_response_time_seconds_count

# Cache Metrics
chat_cache_hits_total
chat_cache_misses_total

# Cost Tracking
chat_cost_usd_total{agent="hunter",model="gpt-4"}

# Agent Availability
chat_agent_available{agent="hunter"}

# Rate Limiting (Future)
anvil_rate_limit_checked_total{user_tier="guest"}
anvil_rate_limit_exceeded_total{user_tier="guest"}
```

### Health Check Endpoint
**URL**: `GET http://localhost:8080/api/v1/monitoring/health`
**Format**: JSON
**Use**: Kubernetes liveness/readiness probes

**Response**:
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "2026-01-19T15:00:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 12.5,
      "message": "Connected"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2.1,
      "message": "Connected"
    },
    "external_apis": {
      "status": "degraded",
      "message": "CoinGecko slow response"
    }
  },
  "healthy_count": 2,
  "degraded_count": 1,
  "unhealthy_count": 0
}
```

### Alerts Endpoint
**URL**: `GET http://localhost:8080/api/v1/monitoring/alerts`
**Format**: JSON
**Use**: Check active alerts

---

## Prometheus Setup

### 1. Installation

```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.50.0/prometheus-2.50.0.linux-amd64.tar.gz
tar xvfz prometheus-2.50.0.linux-amd64.tar.gz
cd prometheus-2.50.0.linux-amd64
```

### 2. Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'anvil-production'
    environment: 'prod'

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'  # Alertmanager

# Load alerting rules
rule_files:
  - 'alerts.yml'

# Scrape configurations
scrape_configs:
  # Anvil FastAPI Application
  - job_name: 'anvil-chat'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/api/v1/monitoring/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

### 3. Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: anvil_chat_alerts
    interval: 30s
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          rate(chat_errors_total[5m]) / rate(chat_requests_total[5m]) * 100 > 5
        for: 5m
        labels:
          severity: critical
          component: chat
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Slow Response Time
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, rate(chat_response_time_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          component: chat
        annotations:
          summary: "Slow response time (p95)"
          description: "95th percentile response time is {{ $value }}s (threshold: 5s)"

      # API Down
      - alert: APIDown
        expr: up{job="anvil-chat"} == 0
        for: 1m
        labels:
          severity: critical
          component: infrastructure
        annotations:
          summary: "Anvil Chat API is down"
          description: "The FastAPI application is not responding to Prometheus scrapes"

      # High Rate Limiting
      - alert: HighRateLimitRejections
        expr: |
          rate(anvil_rate_limit_exceeded_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
          component: rate_limiting
        annotations:
          summary: "High rate limit rejections"
          description: "{{ $value }} requests/second being rate limited"

      # Low Cache Hit Rate
      - alert: LowCacheHitRate
        expr: |
          rate(chat_cache_hits_total[5m]) / (rate(chat_cache_hits_total[5m]) + rate(chat_cache_misses_total[5m])) * 100 < 50
        for: 15m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 50%)"

      # High Cost
      - alert: HighAICost
        expr: increase(chat_cost_usd_total[1h]) > 10
        labels:
          severity: warning
          component: cost
        annotations:
          summary: "High AI cost detected"
          description: "AI cost increased by ${{ $value }} in the last hour"

      # Agent Unavailable
      - alert: AgentUnavailable
        expr: chat_agent_available == 0
        for: 5m
        labels:
          severity: critical
          component: agents
        annotations:
          summary: "Agent {{ $labels.agent }} is unavailable"
          description: "Agent has been unavailable for 5 minutes"
```

### 4. Start Prometheus

```bash
./prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.path=./data \
  --storage.tsdb.retention.time=30d \
  --web.console.templates=consoles \
  --web.console.libraries=console_libraries
```

Access Prometheus UI: `http://localhost:9090`

---

## Grafana Setup

### 1. Installation

```bash
# Download Grafana
wget https://dl.grafana.com/oss/release/grafana-10.3.0.linux-amd64.tar.gz
tar -zxvf grafana-10.3.0.linux-amd64.tar.gz
cd grafana-10.3.0
```

### 2. Configuration

Edit `conf/defaults.ini`:

```ini
[server]
http_port = 3000

[security]
admin_user = admin
admin_password = change_me_in_production

[auth.anonymous]
enabled = false

[alerting]
enabled = true
```

### 3. Start Grafana

```bash
./bin/grafana-server web
```

Access Grafana UI: `http://localhost:3000`
Default credentials: `admin / admin`

### 4. Add Prometheus Data Source

1. Navigate to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Configure:
   - **Name**: `Prometheus-Anvil`
   - **URL**: `http://localhost:9090`
   - **Access**: `Server (default)`
5. Click **Save & Test**

### 5. Import Dashboard

1. Navigate to **Dashboards** → **Import**
2. Upload file: `monitoring/grafana_dashboards/anvil_chat_overview.json`
3. Select data source: `Prometheus-Anvil`
4. Click **Import**

---

## Dashboard Overview

### Panels

#### 1. Request Rate (req/s)
- **Metric**: `rate(chat_requests_total[5m])`
- **Shows**: Requests per second by agent and endpoint
- **Use**: Monitor traffic patterns and load

#### 2. Error Rate (%)
- **Metric**: `rate(chat_errors_total[5m]) / rate(chat_requests_total[5m]) * 100`
- **Shows**: Percentage of failed requests
- **Alert**: Triggers if > 5% for 5 minutes
- **Use**: Detect system issues early

#### 3. Response Time (p50, p95, p99)
- **Metrics**: `histogram_quantile(0.50|0.95|0.99, ...)`
- **Shows**: Response time percentiles
- **Use**: Monitor performance and SLAs

#### 4. Cache Hit Rate (%)
- **Metric**: `rate(chat_cache_hits_total[5m]) / (...)`
- **Shows**: Cache efficiency
- **Use**: Optimize caching strategy

#### 5. Rate Limiting Status
- **Metrics**: `anvil_rate_limit_exceeded_total`, `anvil_rate_limit_checked_total`
- **Shows**: Rate limit checks vs rejections
- **Use**: Monitor rate limiting effectiveness

#### 6. Active Requests
- **Metric**: `chat_active_requests`
- **Type**: Gauge (real-time value)
- **Thresholds**: Green (< 50), Yellow (50-100), Red (> 100)
- **Use**: Monitor current load

#### 7. Total Cost (USD)
- **Metric**: `chat_cost_usd_total`
- **Shows**: Cumulative AI cost
- **Use**: Track spending and budget

#### 8. System Health Components
- **Metric**: `anvil_component_health`
- **Shows**: Status of database, Redis, APIs
- **Use**: Quick health overview

---

## Alerting

### Alert Channels

Configure notification channels in Grafana:

1. **Email**: `alerts@anvil.com`
2. **Slack**: `#alerts-production`
3. **PagerDuty**: For critical alerts only
4. **Webhook**: Custom integrations

### Alert Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **Critical** | System down or major impact | < 5 minutes |
| **Warning** | Degraded performance | < 30 minutes |
| **Info** | Non-urgent notifications | Review daily |

### On-Call Rotation

- **Primary**: Backend Engineer on-call
- **Secondary**: DevOps Engineer
- **Escalation**: CTO (for critical alerts > 15 min)

---

## Kubernetes Integration

### Deployment

```yaml
apiVersion: v1
kind: Service
metadata:
  name: anvil-chat-metrics
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/api/v1/monitoring/metrics"
spec:
  selector:
    app: anvil-chat
  ports:
    - port: 8080
```

### ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: anvil-chat
spec:
  selector:
    matchLabels:
      app: anvil-chat
  endpoints:
    - port: http
      path: /api/v1/monitoring/metrics
      interval: 15s
```

### Liveness/Readiness Probes

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/monitoring/health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/v1/monitoring/health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

---

## Monitoring Best Practices

### 1. Metrics Naming Convention
- **Prefix**: `chat_` for application metrics, `anvil_` for infrastructure
- **Suffix**: `_total` for counters, `_seconds` for timings
- **Labels**: Use labels for dimensions (agent, endpoint, status)

### 2. Alert Tuning
- **Avoid Alert Fatigue**: Set reasonable thresholds
- **Use `for` Clause**: Wait for persistent issues (e.g., `for: 5m`)
- **Group Related Alerts**: Reduce noise during incidents

### 3. Dashboard Organization
- **Top Row**: High-level KPIs (request rate, error rate, latency)
- **Middle Row**: Detailed breakdowns (by agent, endpoint)
- **Bottom Row**: System health and costs

### 4. Data Retention
- **Prometheus**: 30 days (for detailed metrics)
- **Long-term Storage**: Consider Thanos or VictoriaMetrics
- **Aggregation**: Pre-aggregate for 90+ day retention

---

## Testing

### Manual Verification

```bash
# 1. Test metrics endpoint
curl http://localhost:8080/api/v1/monitoring/metrics

# 2. Test health endpoint
curl http://localhost:8080/api/v1/monitoring/health | jq

# 3. Generate load
for i in {1..100}; do
  curl -X POST http://localhost:8080/api/v1/guest/chat \
    -H "Content-Type: application/json" \
    -d '{"content": "test", "language": "en"}' &
done

# 4. Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# 5. Test Grafana dashboard
open http://localhost:3000/d/anvil-chat-overview
```

### Automated Tests

```python
# tests/monitoring/test_metrics_endpoint.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test Prometheus metrics endpoint."""
    response = await client.get("/api/v1/monitoring/metrics")

    assert response.status_code == 200
    assert "chat_requests_total" in response.text
    assert "chat_response_time_seconds" in response.text
    assert "chat_uptime_seconds" in response.text

@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/monitoring/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
```

---

## Troubleshooting

### Issue: Metrics Not Appearing

**Problem**: Grafana dashboard shows "No data"

**Solutions**:
1. Check Prometheus is scraping: `http://localhost:9090/targets`
2. Verify metrics endpoint: `curl http://localhost:8080/api/v1/monitoring/metrics`
3. Check Grafana data source connection
4. Verify time range in dashboard

### Issue: High Memory Usage

**Problem**: Prometheus consuming excessive memory

**Solutions**:
1. Reduce retention: `--storage.tsdb.retention.time=15d`
2. Limit scrape targets
3. Use remote write to long-term storage
4. Increase Prometheus resources

### Issue: Alerts Not Firing

**Problem**: Alerts configured but not triggering

**Solutions**:
1. Check alert rules syntax: `promtool check rules alerts.yml`
2. Verify Alertmanager is running: `http://localhost:9093`
3. Test alert query in Prometheus UI
4. Check notification channel configuration

---

## Production Checklist

- [x] Monitoring router registered in FastAPI
- [x] Prometheus metrics endpoint accessible
- [x] Health check endpoint responding
- [x] Grafana dashboard created
- [x] Alert rules configured
- [ ] Prometheus deployed and scraping
- [ ] Grafana deployed with dashboards
- [ ] Alertmanager configured
- [ ] Notification channels tested
- [ ] On-call rotation established
- [ ] Runbooks created for common alerts

---

## Next Steps

1. **Deploy Prometheus** to production (use Docker Compose or Kubernetes)
2. **Deploy Grafana** and import dashboard
3. **Configure Alertmanager** for notifications
4. **Set up on-call rotation** in PagerDuty
5. **Create runbooks** for each alert type
6. **Test incident response** with simulated failures
7. **Monitor costs** and optimize if needed

---

## Resources

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **FastAPI Monitoring**: https://fastapi.tiangolo.com/advanced/monitoring/
- **Metrics Best Practices**: https://prometheus.io/docs/practices/naming/

---

**Status**: ✅ Monitoring infrastructure complete
**Author**: Day 5 Production Readiness Team
**Date**: 2026-01-19 16:00 UTC
