# Deployment & Production Readiness Plan

## Executive Summary

**Goal:** Deploy Anvil Backend to production environment with full monitoring, security, and performance optimization.

**Duration:** 3-5 days

**Status:** Ready to execute

---

## Phase 1: Environment Setup (Day 1)

### 1.1 Production Environment Configuration

**Infrastructure:**
- [ ] AWS/GCP/Azure account setup
- [ ] VPC and networking configuration
- [ ] Security groups and firewall rules
- [ ] Load balancer setup
- [ ] Auto-scaling configuration

**Environment Variables:**
```bash
# Production .env
APP_ENV=prod
DEBUG=false

# Database
POSTGRES_HOST=prod-db.anvil.com
POSTGRES_PORT=5432
POSTGRES_DB=anvil_prod
POSTGRES_USER=anvil_prod_user
POSTGRES_PASSWORD=<secure-password>

# Redis
REDIS_URL=redis://prod-redis.anvil.com:6379

# API Keys
STRIPE_SECRET_KEY=<prod-key>
STRIPE_PUBLIC_KEY=<prod-key>
MAILGUN_API_KEY=<prod-key>
ANTHROPIC_API_KEY=<prod-key>
OPENAI_API_KEY=<prod-key>

# Security
JWT_SECRET_KEY=<secure-random-key>
SECRET_KEY=<secure-random-key>

# Monitoring
SENTRY_DSN=<sentry-dsn>
DATADOG_API_KEY=<datadog-key>
```

**Configuration Files:**
- [ ] Update `config/prod/config.toml`
- [ ] Create `config/prod/.secrets.toml`
- [ ] Generate production `.env` with `make dotenv`

### 1.2 Database Setup

**PostgreSQL:**
```bash
# Create production database
make create-db APP_ENV=prod

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_production.py
```

**Redis:**
```bash
# Start Redis
docker-compose -f config/prod/docker-compose.yaml up -d redis

# Verify connection
redis-cli -h prod-redis.anvil.com ping
```

**Backups:**
- [ ] Configure automated PostgreSQL backups (daily)
- [ ] Configure Redis persistence (AOF + RDB)
- [ ] Set up backup retention policy (30 days)

---

## Phase 2: CI/CD Pipeline (Day 2)

### 2.1 GitHub Actions Workflow

**File:** `.github/workflows/deploy-production.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [master]
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e '.[dev,test]'
      - name: Run tests
        run: pytest tests/ -v
      - name: Run linting
        run: make code.lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Deploy via SSH or container registry
          ./scripts/deploy.sh production
```

### 2.2 Container Configuration

**Dockerfile (Production):**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install uv && uv pip install -e '.[prod]'

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8000"]
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=prod
    depends_on:
      - postgres
      - redis
    restart: always

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: anvil_prod
      POSTGRES_USER: anvil_prod_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  celery-worker:
    build: .
    command: celery -A app.infrastructure.celery.app worker -l info
    depends_on:
      - redis
    restart: always

  celery-beat:
    build: .
    command: celery -A app.infrastructure.celery.app beat -l info
    depends_on:
      - redis
    restart: always

volumes:
  postgres_data:
  redis_data:
```

---

## Phase 3: SSL/TLS & Domain Setup (Day 2)

### 3.1 SSL Certificates

**Let's Encrypt (Recommended):**
```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Generate certificate
certbot --nginx -d api.anvil.com

# Auto-renewal
certbot renew --dry-run
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name api.anvil.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.anvil.com;

    ssl_certificate /etc/letsencrypt/live/api.anvil.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.anvil.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3.2 DNS Configuration

**A Records:**
- `api.anvil.com` → Production server IP
- `www.anvil.com` → Frontend server IP

**CNAME Records:**
- `*.anvil.com` → Load balancer

---

## Phase 4: Monitoring & Logging (Day 3)

### 4.1 Application Monitoring

**Sentry (Error Tracking):**
```python
# src/app/setup/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def setup_sentry():
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        environment="production",
        traces_sample_rate=0.1,
    )
```

**DataDog (Metrics & APM):**
```python
# Install datadog
pip install ddtrace

# Run with tracing
ddtrace-run uvicorn app.run:make_app --factory
```

### 4.2 Logging Setup

**Structured Logging:**
```python
# src/app/setup/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)
```

**Log Aggregation (ELK Stack):**
- Elasticsearch for storage
- Logstash for processing
- Kibana for visualization

### 4.3 Health Checks

**Endpoint:** `GET /health`
```python
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "celery": await check_celery(),
    }
```

**Monitoring:**
- Uptime monitoring (UptimeRobot, Pingdom)
- Response time tracking
- Error rate alerts

---

## Phase 5: Security Hardening (Day 3)

### 5.1 Security Headers

**FastAPI Middleware:**
```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.anvil.com", "*.anvil.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://anvil.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 5.2 Rate Limiting

**Slowapi (Rate Limiting):**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.get("/api/v1/endpoint")
@limiter.limit("100/minute")
async def endpoint():
    pass
```

### 5.3 Security Scanning

**Tools:**
- [ ] OWASP ZAP (penetration testing)
- [ ] Bandit (Python security linter)
- [ ] Safety (dependency vulnerability scanning)
- [ ] Trivy (container scanning)

```bash
# Run security checks
bandit -r src/
safety check
trivy image anvil-backend:latest
```

---

## Phase 6: Performance Optimization (Day 4)

### 6.1 Database Optimization

**Indexes:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
```

**Connection Pooling:**
```python
# Update SQLAlchemy config
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
```

### 6.2 Caching Layer

**Redis Caching:**
```python
from redis import Redis
from functools import wraps

redis_client = Redis.from_url(REDIS_URL)

def cache(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 6.3 CDN Setup

**Static Assets:**
- [ ] CloudFlare CDN
- [ ] AWS CloudFront
- [ ] Cache API responses (public endpoints)

---

## Phase 7: Load Testing (Day 4)

### 7.1 Load Testing Tools

**Locust (Python-based):**
```python
# locustfile.py
from locust import HttpUser, task, between

class AnvilUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_conversations(self):
        self.client.get("/api/v1/chat/conversations")
    
    @task(3)
    def discover_arbitrage(self):
        self.client.get("/api/v1/ultra/arbitrage/discover?capital=10000")
```

**Run Load Test:**
```bash
locust -f locustfile.py --host https://api.anvil.com
```

**Targets:**
- 1000 concurrent users
- < 200ms response time (p95)
- < 1% error rate

### 7.2 Performance Benchmarks

**K6 (Load Testing):**
```javascript
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 1000 },
    { duration: '2m', target: 0 },
  ],
};

export default function () {
  let res = http.get('https://api.anvil.com/api/v1/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
}
```

---

## Phase 8: Deployment Automation (Day 5)

### 8.1 Deployment Script

**File:** `scripts/deploy.sh`
```bash
#!/bin/bash
set -e

ENV=$1

echo "🚀 Deploying to $ENV..."

# Pull latest code
git pull origin master

# Build Docker image
docker build -t anvil-backend:$ENV .

# Push to registry
docker push registry.anvil.com/anvil-backend:$ENV

# Deploy
kubectl apply -f k8s/$ENV/

# Run migrations
kubectl exec -it deployment/anvil-api -- alembic upgrade head

# Restart services
kubectl rollout restart deployment/anvil-api

echo "✅ Deployment complete!"
```

### 8.2 Rollback Strategy

**Quick Rollback:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/anvil-api

# Rollback database (if needed)
alembic downgrade -1
```

---

## Phase 9: Final Checks (Day 5)

### 9.1 Pre-Launch Checklist

**Configuration:**
- [ ] All environment variables set
- [ ] SSL certificates valid
- [ ] DNS records configured
- [ ] Database migrations applied
- [ ] Redis configured and running

**Security:**
- [ ] Rate limiting enabled
- [ ] CORS configured
- [ ] Security headers set
- [ ] API keys rotated (production)
- [ ] Secrets stored securely

**Monitoring:**
- [ ] Sentry configured
- [ ] Logging aggregation working
- [ ] Health checks passing
- [ ] Alerts configured

**Performance:**
- [ ] Load testing passed
- [ ] Database indexes created
- [ ] Caching enabled
- [ ] CDN configured

**Documentation:**
- [ ] API documentation live
- [ ] Deployment guide written
- [ ] Runbook created
- [ ] On-call procedures defined

### 9.2 Launch Plan

**Go-Live Steps:**
1. Final smoke tests in staging
2. Database backup
3. Deploy to production
4. Run smoke tests in production
5. Monitor for 1 hour
6. Announce launch

**Rollback Triggers:**
- Error rate > 5%
- Response time > 1s (p95)
- Database issues
- Critical bugs

---

## Ongoing Maintenance

### Daily Tasks
- [ ] Check error logs (Sentry)
- [ ] Review metrics (DataDog)
- [ ] Monitor uptime

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Check security alerts
- [ ] Update dependencies (security patches)

### Monthly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Backup restoration test
- [ ] Disaster recovery drill

---

## Success Metrics

**Performance:**
- Response time < 200ms (p95)
- Uptime > 99.9%
- Error rate < 0.1%

**Security:**
- Zero critical vulnerabilities
- All dependencies up to date
- Penetration test passed

**Scalability:**
- Handle 1000 concurrent users
- Auto-scale from 2-10 instances
- Database handles 10K queries/sec

---

## Support & On-Call

**On-Call Rotation:**
- Primary: DevOps engineer
- Secondary: Backend engineer
- Escalation: CTO

**Emergency Contacts:**
- Slack: #production-alerts
- PagerDuty: Production incidents
- Email: oncall@anvil.com

**Runbook:** `docs/PRODUCTION_RUNBOOK.md`
