# Production Deployment Guide

**Version**: 1.0  
**Last Updated**: December 1, 2025  
**Target Audience**: DevOps Engineers

---

## 📋 Overview

Complete guide for deploying Anvil Backend to production environments. Covers infrastructure setup, configuration, deployment process, and monitoring.

---

## 🚀 Pre-Deployment Checklist

### Code Quality
- ✅ All tests passing (`make code.test`)
- ✅ Linting passing (`make code.lint`)
- ✅ Type checking passing (mypy)
- ✅ Security audit completed
- ✅ Code review approved
- ✅ Documentation up to date

### Infrastructure
- [ ] Production database provisioned (PostgreSQL 14+)
- [ ] Redis instance provisioned
- [ ] Load balancer configured
- [ ] SSL certificates obtained
- [ ] DNS records configured
- [ ] CDN configured (optional)
- [ ] Backup system configured

### Configuration
- [ ] Environment variables set
- [ ] Secrets stored securely (AWS Secrets Manager / Vault)
- [ ] CORS origins configured
- [ ] Rate limits configured
- [ ] Monitoring enabled

---

## 🏗️ Infrastructure Requirements

### Minimum Requirements

**Application Servers** (2+ instances for HA):
- CPU: 2 cores
- RAM: 4 GB
- Storage: 20 GB SSD

**Database** (PostgreSQL 14+):
- CPU: 4 cores
- RAM: 16 GB
- Storage: 100 GB SSD (with auto-scaling)
- Apache AGE extension installed
- pgvector extension installed

**Redis**:
- RAM: 4 GB
- Persistence enabled (AOF)

**Celery Workers** (2+ instances):
- CPU: 2 cores
- RAM: 4 GB

---

## 🐳 Docker Deployment

### Build Production Image

```bash
# Build image
docker build -t anvil-backend:latest -f Dockerfile .

# Tag for registry
docker tag anvil-backend:latest registry.anvil.com/anvil-backend:1.0.0

# Push to registry
docker push registry.anvil.com/anvil-backend:1.0.0
```

### Docker Compose (Production)

```yaml
version: '3.8'

services:
  app:
    image: registry.anvil.com/anvil-backend:1.0.0
    restart: always
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=prod
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
  
  celery-worker:
    image: registry.anvil.com/anvil-backend:1.0.0
    restart: always
    command: celery -A app.infrastructure.celery.app worker -l info
    environment:
      - APP_ENV=prod
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
  
  celery-beat:
    image: registry.anvil.com/anvil-backend:1.0.0
    restart: always
    command: celery -A app.infrastructure.celery.app beat -l info
    environment:
      - APP_ENV=prod
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
  
  db:
    image: postgres:14-alpine
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  
  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## ☸️ Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anvil-backend
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: anvil-backend
  template:
    metadata:
      labels:
        app: anvil-backend
    spec:
      containers:
      - name: app
        image: registry.anvil.com/anvil-backend:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: APP_ENV
          value: "prod"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: anvil-secrets
              key: database-url
        resources:
          requests:
            cpu: "1"
            memory: "2Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: anvil-backend
  namespace: production
spec:
  selector:
    app: anvil-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 🗄️ Database Setup

### PostgreSQL Configuration

```sql
-- Create production database
CREATE DATABASE anvil_prod;

-- Create application user
CREATE USER anvil_app WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE anvil_prod TO anvil_app;

-- Install required extensions
\c anvil_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Apache AGE (for graph database)
CREATE EXTENSION IF NOT EXISTS age;

-- pgvector (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;
```

### Run Migrations

```bash
# Set environment
export APP_ENV=prod
export DATABASE_URL="postgresql://anvil_app:password@db.anvil.com:5432/anvil_prod"

# Run migrations
alembic upgrade head

# Verify
alembic current
```

---

## 🔧 Configuration

### Environment Variables

Create `config/prod/.secrets.toml`:

```toml
[database]
postgres_user = "anvil_app"
postgres_password = "strong_password_here"
postgres_host = "db.anvil.com"
postgres_port = 5432
postgres_db = "anvil_prod"

[redis]
redis_url = "redis://redis.anvil.com:6379/0"

[security]
jwt_secret_key = "generate-random-256-bit-key"
jwt_algorithm = "RS256"

[openai]
api_key = "sk-..."

[stripe]
secret_key = "sk_live_..."
webhook_secret = "whsec_..."

[monitoring]
sentry_dsn = "https://...@sentry.io/..."
```

Generate `.env` file:

```bash
make dotenv APP_ENV=prod
```

---

## 🚀 Deployment Process

### Zero-Downtime Deployment

```bash
# 1. Build new version
docker build -t anvil-backend:v1.1.0 .

# 2. Run database migrations (if any)
kubectl exec -it deployment/anvil-backend -- alembic upgrade head

# 3. Rolling update
kubectl set image deployment/anvil-backend app=anvil-backend:v1.1.0

# 4. Monitor rollout
kubectl rollout status deployment/anvil-backend

# 5. Verify health
kubectl get pods
curl https://api.anvil.com/health
```

### Rollback Process

```bash
# Rollback to previous version
kubectl rollout undo deployment/anvil-backend

# Rollback to specific version
kubectl rollout undo deployment/anvil-backend --to-revision=3

# Check rollout history
kubectl rollout history deployment/anvil-backend
```

---

## 📊 Monitoring & Logging

### Health Checks

**Endpoint**: `GET /health`

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

### Metrics (Prometheus)

**Endpoint**: `GET /metrics`

**Key Metrics**:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `database_connections_active` - Active DB connections
- `celery_tasks_total` - Total background tasks
- `redis_operations_total` - Redis operation count

### Logging

**Configure Structured Logging**:

```python
# config/prod/config.toml
[logging]
level = "INFO"
format = "json"
output = "stdout"

[sentry]
dsn = "https://...@sentry.io/..."
environment = "production"
traces_sample_rate = 0.1
```

---

## 🔒 Security Hardening

### Production Security Checklist

- [ ] HTTPS enforced (TLS 1.3)
- [ ] Rate limiting enabled
- [ ] CORS configured (no wildcards)
- [ ] Security headers enabled
- [ ] Database encryption at rest
- [ ] Secrets stored securely
- [ ] Access logs enabled
- [ ] Firewall rules configured
- [ ] DDoS protection enabled
- [ ] Regular security scans scheduled

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale application pods
kubectl scale deployment/anvil-backend --replicas=5

# Scale Celery workers
kubectl scale deployment/celery-worker --replicas=3

# Auto-scaling (HPA)
kubectl autoscale deployment/anvil-backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

### Database Scaling

- Enable read replicas for read-heavy workloads
- Configure connection pooling (PgBouncer)
- Implement caching layer (Redis)
- Partition large tables
- Optimize indexes

---

## 🔄 Backup & Recovery

### Automated Backups

```bash
# Database backup (daily)
pg_dump -h db.anvil.com -U anvil_app anvil_prod | \
  gzip > backup-$(date +%Y%m%d).sql.gz

# Upload to S3
aws s3 cp backup-$(date +%Y%m%d).sql.gz \
  s3://anvil-backups/database/

# Retention: 30 days
```

### Disaster Recovery

```bash
# Restore from backup
gunzip -c backup-20251201.sql.gz | \
  psql -h db.anvil.com -U anvil_app anvil_prod

# Verify data integrity
python scripts/verify_data_integrity.py

# Re-run migrations if needed
alembic upgrade head
```

---

## 🎯 Post-Deployment Validation

### Smoke Tests

```bash
# Health check
curl https://api.anvil.com/health

# Authentication
curl -X POST https://api.anvil.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@anvil.com","password":"test123"}'

# GraphRAG search
curl https://api.anvil.com/api/v1/graph/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"safe staking protocols","limit":5}'
```

### Performance Testing

```bash
# Load test with hey
hey -n 10000 -c 100 https://api.anvil.com/api/v1/graph/search

# Monitor response times
kubectl top pods

# Check error rates
kubectl logs -f deployment/anvil-backend | grep ERROR
```

---

## 📞 Support & Troubleshooting

### Common Issues

**503 Service Unavailable**:
- Check pod status: `kubectl get pods`
- Check resource limits: `kubectl describe pod <pod-name>`
- Check database connectivity

**High Memory Usage**:
- Review memory limits in deployment
- Check for memory leaks in application code
- Scale horizontally

**Slow Database Queries**:
- Enable query logging
- Review indexes with `EXPLAIN ANALYZE`
- Check connection pool size

---

*Guide Version: 1.0*  
*Deployment Contact: devops@anvil.com*  
*Emergency Contact: oncall@anvil.com*
