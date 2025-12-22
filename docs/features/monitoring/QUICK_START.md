# Monitoring System Quick Start Guide

## 5-Minute Setup

### Step 1: Enable Monitoring in Your Application

```python
# src/app/main.py
from fastapi import FastAPI
from app.infrastructure.monitoring.middleware import setup_monitoring_middleware
from app.infrastructure.monitoring import initialize_monitoring

app = FastAPI()

# Setup monitoring middleware (automatic metrics collection)
setup_monitoring_middleware(app)

# Initialize monitoring infrastructure
@app.on_event("startup")
async def startup_monitoring():
    alert_manager, health_service = initialize_monitoring(
        daily_budget_usd=100.0,
        response_time_p95_ms=1000.0,
        webhook_url="https://hooks.slack.com/your-webhook",  # Optional
        alert_emails=["team@example.com"],  # Optional
    )
```

### Step 2: Add Monitoring Router

```python
# src/app/presentation/http/main.py
from app.presentation.http.controllers.monitoring.router import router as monitoring_router

app.include_router(monitoring_router)
```

### Step 3: Test Endpoints

```bash
# Check health
curl http://localhost:8000/monitoring/health

# View Prometheus metrics
curl http://localhost:8000/monitoring/metrics

# View active alerts
curl http://localhost:8000/monitoring/alerts
```

### Step 4: Configure Prometheus (Optional)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'anvil-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 30s
```

### Step 5: Setup Celery Background Tasks (Optional)

```python
# src/app/infrastructure/celery/beat_schedule.py
from app.infrastructure.monitoring.background_tasks import setup_monitoring_schedule

# Add to your Celery beat schedule
beat_schedule = setup_monitoring_schedule()
```

## Common Use Cases

### Track Custom Metrics

```python
from app.infrastructure.monitoring.metrics_collector import get_metrics_collector

collector = get_metrics_collector()

# In your endpoint or service
collector.increment_request_count(
    agent_name="my-agent",
    endpoint="/my/endpoint",
    status="success"
)

collector.record_response_time(
    duration_seconds=0.5,
    agent_name="my-agent"
)
```

### Add Custom Alert Rules

```python
from app.infrastructure.monitoring.alerting import (
    get_alert_manager,
    PerformanceAlert,
    AlertSeverity
)

manager = get_alert_manager()

# Add custom performance alert for specific agent
manager.add_rule(PerformanceAlert(
    threshold_p95_ms=500.0,  # More strict for critical agent
    severity=AlertSeverity.ERROR,
    agent_name="critical-agent"
))
```

### Add Custom Health Checks

```python
from app.infrastructure.monitoring.health_checks import (
    get_health_service,
    ExternalAPIHealthCheck
)

service = get_health_service()

# Add custom external API check
service.add_check(ExternalAPIHealthCheck(
    name="stripe",
    api_url="https://api.stripe.com/v1/charges",
    timeout_seconds=5.0
))
```

### Setup Webhook Notifications

```python
from app.infrastructure.monitoring.alerting import (
    get_alert_manager,
    WebhookNotificationChannel
)

manager = get_alert_manager()

# Add Slack webhook
manager.add_notification_channel(
    WebhookNotificationChannel("https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
)
```

## Environment Variables

```bash
# .env
MONITORING_ENABLED=true
MONITORING_DAILY_BUDGET_USD=100.0
MONITORING_RESPONSE_TIME_P95_MS=1000.0
MONITORING_WEBHOOK_URL=https://hooks.slack.com/...
MONITORING_ALERT_EMAILS=team@example.com,ops@example.com
```

## Docker Compose Example

```yaml
# docker-compose.yml
version: '3.8'

services:
  anvil-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONITORING_ENABLED=true
      - MONITORING_DAILY_BUDGET_USD=100.0

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

volumes:
  prometheus_data:
  grafana_data:
```

## Kubernetes Example

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
      - job_name: 'anvil-backend'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
            action: replace
            target_label: __metrics_path__
            regex: (.+)
          - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            regex: ([^:]+)(?::\d+)?;(\d+)
            replacement: $1:$2
            target_label: __address__

---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anvil-backend
spec:
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/monitoring/metrics"
    spec:
      containers:
        - name: api
          image: anvil-backend:latest
          env:
            - name: MONITORING_ENABLED
              value: "true"
          livenessProbe:
            httpGet:
              path: /monitoring/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /monitoring/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

## Verification Checklist

- [ ] Monitoring endpoints accessible (`/monitoring/health`, `/monitoring/metrics`)
- [ ] Metrics middleware collecting data
- [ ] Health checks passing
- [ ] Alerts configured
- [ ] Notification channels working
- [ ] Prometheus scraping metrics (if using)
- [ ] Grafana dashboards showing data (if using)
- [ ] Background tasks running (if using Celery)

## Next Steps

1. **Setup Grafana Dashboards** - Import pre-built dashboards or create custom ones
2. **Configure Alerts** - Tune thresholds based on your SLAs
3. **Add Custom Metrics** - Track business-specific metrics
4. **Enable Distributed Tracing** - For cross-service debugging
5. **Setup Log Aggregation** - Integrate with ELK or similar

## Troubleshooting

### Metrics Not Appearing

1. Check middleware is installed:
   ```python
   # Verify in logs
   "Monitoring middleware configured"
   ```

2. Test endpoint directly:
   ```bash
   curl http://localhost:8000/monitoring/metrics
   ```

3. Check for errors in logs

### Health Checks Failing

1. Verify database connection
2. Check Redis availability
3. Review health check configuration
4. Look for timeout issues

### Alerts Not Triggering

1. Verify alert rules are added
2. Check threshold values
3. Ensure metrics are being collected
4. Review alert cooldown periods

### High Memory Usage

1. Reduce metric retention
2. Implement external time-series DB
3. Aggregate old metrics
4. Reduce label cardinality

## Support

For issues or questions:
- Review documentation: `/docs/features/monitoring/MONITORING_SYSTEM.md`
- Check logs for errors
- Verify configuration settings
