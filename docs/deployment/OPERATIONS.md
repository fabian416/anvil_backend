# Operations Guide

Complete guide for deploying, monitoring, and operating the DeFi Chat Platform.

## Table of Contents

1. [Deployment](#deployment)
2. [Health Checks](#health-checks)
3. [Monitoring](#monitoring)
4. [Scaling](#scaling)
5. [Security](#security)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

---

## Deployment

### Prerequisites

- **Python 3.12+**
- **PostgreSQL 14+**
- **Redis 7+**
- **Docker & Docker Compose** (recommended)
- **Kubernetes** (for production)

### Environment Setup

```bash
# 1. Clone repository
git clone https://github.com/yourorg/defi-chat-platform
cd defi-chat-platform

# 2. Set environment
export APP_ENV=prod

# 3. Configure secrets
cp config/prod/.secrets.toml.example config/prod/.secrets.toml
# Edit .secrets.toml with actual values

# 4. Generate .env
make dotenv

# 5. Start dependencies
make up.db

# 6. Run migrations
alembic upgrade head

# 7. Start application
make start
```

### Docker Deployment

```bash
# Build image
docker build -t defi-chat:latest .

# Run with Docker Compose
docker-compose -f config/prod/docker-compose.yaml up -d

# View logs
docker-compose logs -f app
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: defi-chat
spec:
  replicas: 3
  selector:
    matchLabels:
      app: defi-chat
  template:
    metadata:
      labels:
        app: defi-chat
    spec:
      containers:
      - name: app
        image: defi-chat:latest
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "prod"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

---

## Health Checks

### Endpoints

**Basic Health** - Always returns 200 if running:
```bash
curl http://localhost:8000/health
```

**Liveness** - Kubernetes liveness probe:
```bash
curl http://localhost:8000/health/live
```

**Readiness** - Kubernetes readiness probe:
```bash
curl http://localhost:8000/health/ready
```

### Health Check Response

```json
{
  "status": "healthy",
  "timestamp": 1701432000.0,
  "version": "1.0.0",
  "checks": {
    "database": true,
    "redis": true,
    "external_apis": true
  }
}
```

### Readiness Criteria

Service is ready when:
- ✅ Database connection established
- ✅ Redis connection established
- ✅ External APIs reachable (optional)

---

## Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Collected Metrics

**Requests:**
- Total request count
- Requests per endpoint
- Average duration per endpoint

**Errors:**
- Total error count
- Errors by type (HTTP_500, ValueError, etc.)

**Cache:**
- Cache hits
- Cache misses
- Hit rate percentage

**Agents:**
- Total agent invocations
- Invocations by agent (Swap, Trading, Portfolio)

**Tools:**
- Total tool usage
- Usage by tool (get_swap_quote, etc.)

### Metrics Response Example

```json
{
  "uptime_seconds": 3600,
  "timestamp": "2024-12-01T12:00:00",
  "requests": {
    "total": 10000,
    "by_endpoint": {
      "POST /api/v1/chat/messages": 8000,
      "GET /api/v1/chat/conversations": 2000
    },
    "avg_duration_ms": {
      "POST /api/v1/chat/messages": 45.2,
      "GET /api/v1/chat/conversations": 12.8
    }
  },
  "errors": {
    "total": 50,
    "by_type": {
      "HTTP_500": 30,
      "ValueError": 20
    }
  },
  "cache": {
    "hits": 8000,
    "misses": 2000,
    "hit_rate": 0.8
  },
  "agents": {
    "total_invocations": 8000,
    "by_agent": {
      "SwapAgent": 5000,
      "TradingAgent": 2000,
      "PortfolioAgent": 1000
    }
  }
}
```

### Prometheus Integration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'defi-chat'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboards

**Key Metrics to Monitor:**

1. **Request Rate** (req/sec)
   - Normal: 10-100 req/sec
   - Alert: > 500 req/sec

2. **Response Time** (P95)
   - Normal: < 100ms
   - Warning: > 200ms
   - Alert: > 500ms

3. **Error Rate** (%)
   - Normal: < 1%
   - Warning: > 2%
   - Alert: > 5%

4. **Cache Hit Rate** (%)
   - Normal: > 80%
   - Warning: < 70%
   - Alert: < 50%

5. **Database Connections**
   - Normal: < 50
   - Warning: > 80
   - Alert: > 95

---

## Scaling

### Horizontal Scaling

**Kubernetes:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: defi-chat-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: defi-chat
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

**Resource Limits:**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Database Scaling

**Connection Pool:**
```python
# config/prod/config.toml
[database]
pool_size = 20
max_overflow = 10
pool_timeout = 30
```

**Read Replicas:**
- Use read replicas for queries
- Write to primary database
- PostgreSQL replication

### Redis Scaling

**Redis Cluster:**
- Shard data across multiple nodes
- Use consistent hashing
- Configure in redis_cache.py

---

## Security

### Authentication

- JWT tokens with expiration
- Session-based management
- Token refresh mechanism
- Logout invalidates tokens

### Rate Limiting

**Per User:**
- 100 requests/minute (default)
- Configurable per endpoint

**Per IP:**
- 200 requests/minute (default)
- Protects against abuse

**Per API:**
- CoinGecko: 50 req/min
- 1inch: 60 req/min
- DeFiLlama: 100 req/min

### Input Validation

- Pydantic model validation
- SQL injection prevention (parameterized queries)
- XSS prevention (HTML escaping)
- Path traversal prevention
- Size limits enforced

### Secrets Management

**DO NOT commit to git:**
- API keys
- Database passwords
- JWT secrets
- Encryption keys

**Use:**
- `.secrets.toml` (local)
- Kubernetes Secrets (prod)
- AWS Secrets Manager (AWS)
- HashiCorp Vault (enterprise)

---

## Troubleshooting

### High Response Times

**Check:**
1. Cache hit rate (should be > 80%)
2. Database query performance
3. External API latency
4. Number of concurrent requests

**Fix:**
```bash
# Check cache
redis-cli info stats

# Check database
psql -c "SELECT * FROM pg_stat_activity;"

# Check application metrics
curl http://localhost:8000/metrics
```

### High Error Rate

**Check:**
1. Application logs
2. Database errors
3. External API status
4. Rate limit violations

**Fix:**
```bash
# View logs
docker-compose logs app | tail -100

# Check external APIs
curl https://api.coingecko.com/api/v3/ping
```

### Memory Issues

**Check:**
```bash
# Memory usage
docker stats defi-chat

# Python memory profiling
import tracemalloc
tracemalloc.start()
```

**Fix:**
- Increase pod memory limit
- Fix memory leaks
- Reduce cache size
- Implement memory limits

### Database Connection Issues

**Check:**
```bash
# Active connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Check pool
# In application metrics
```

**Fix:**
- Increase connection pool size
- Close idle connections
- Use connection pooling (PgBouncer)

---

## Maintenance

### Database Backups

```bash
# Daily backup
pg_dump -h localhost -U postgres anvil_backend > backup-$(date +%Y%m%d).sql

# Restore
psql -h localhost -U postgres anvil_backend < backup-20241201.sql
```

### Cache Clearing

```bash
# Clear all cache
redis-cli FLUSHALL

# Clear specific pattern
redis-cli --scan --pattern "price:*" | xargs redis-cli DEL
```

### Log Rotation

```bash
# logrotate config
/var/log/defi-chat/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}
```

### Dependency Updates

```bash
# Check outdated
pip list --outdated

# Update
uv pip install -U package-name

# Test
make code.test
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Review migration
cat alembic/versions/xxxx_description.py

# Apply
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Alerts Configuration

### Recommended Alerts

**Critical:**
- Error rate > 5%
- Response time P95 > 1s
- Database connections > 95%
- Service down

**Warning:**
- Error rate > 2%
- Response time P95 > 500ms
- Cache hit rate < 70%
- High CPU (> 80%)

**Info:**
- Deploy completed
- Scaling event
- Cache cleared

### PagerDuty Integration

```python
import requests

def send_alert(severity, message):
    requests.post(
        "https://events.pagerduty.com/v2/enqueue",
        json={
            "routing_key": "YOUR_INTEGRATION_KEY",
            "event_action": "trigger",
            "payload": {
                "summary": message,
                "severity": severity,
                "source": "defi-chat-platform",
            }
        }
    )
```

---

## Contact

**Ops Team:** ops@example.com  
**On-Call:** +1-555-0123  
**Slack:** #defi-chat-ops
