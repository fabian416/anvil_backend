# Retry System Migration Guide

## Overview

This guide provides step-by-step instructions for migrating to the enterprise retry system with telemetry and admin dashboard.

## Pre-Migration Checklist

- [ ] Backup database
- [ ] Review current retry configuration
- [ ] Identify all services using retry
- [ ] Schedule maintenance window (2-4 hours)
- [ ] Notify stakeholders

## Migration Steps

### Step 1: Database Migration

**Apply Alembic Migration**:
```bash
# Backup database first
pg_dump anvil_db > backup_$(date +%Y%m%d).sql

# Apply migration
cd /home/ubuntu/anvil_backend
alembic upgrade head

# Verify tables created
psql -d anvil_db -c "\dt retry_*"
psql -d anvil_backend -c "\dt circuit_*"
psql -d anvil_db -c "\dt service_*"
```

**Expected Output**:
```
retry_attempts
retry_metrics_aggregate
circuit_breaker_events
service_override_events
```

### Step 2: Configuration Update

**Update config/prod/config.toml**:
```toml
[retry]
telemetry_enabled = true
circuit_breaker_enabled = true

[mcp.retry]
enabled = true
max_retries = 3
circuit_failure_threshold = 5
telemetry_enabled = true

[agno.retry]
enabled = true
max_attempts = 2
telemetry_enabled = true
```

### Step 3: Deploy Application

```bash
# Build new image
docker build -t anvil-backend:retry-system .

# Deploy (zero-downtime)
kubectl set image deployment/anvil-backend \
  anvil-backend=anvil-backend:retry-system

# Verify deployment
kubectl rollout status deployment/anvil-backend
```

### Step 4: Verify Functionality

**Check Retry Engine**:
```bash
# Check logs for retry attempts
kubectl logs -n anvil -l app=anvil-backend --tail=100 | grep retry

# Should see telemetry events
```

**Check Database**:
```sql
-- Verify telemetry is being recorded
SELECT COUNT(*) FROM retry_attempts;
SELECT COUNT(*) FROM circuit_breaker_events;
```

**Check Admin API**:
```bash
# Get services
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/services

# Should return 6 services
```

### Step 5: Configure Monitoring

**Grafana Dashboard**:
1. Import dashboard from `docs/ops/grafana-retry-dashboard.json`
2. Configure data source (PostgreSQL)
3. Verify metrics display

**Datadog Alerts**:
```bash
# Import alerts
datadog-ci synthetics import \
  --config docs/ops/datadog-retry-alerts.json
```

## Rollback Procedure

If issues occur, rollback using these steps:

```bash
# 1. Revert application deployment
kubectl rollout undo deployment/anvil-backend

# 2. Revert database migration
alembic downgrade -1

# 3. Restore config
git checkout config/prod/config.toml
```

## Post-Migration Validation

### Validation Checklist

- [ ] All services showing in admin dashboard
- [ ] Telemetry data populating database
- [ ] Circuit breakers responding to failures
- [ ] Metrics aggregating daily
- [ ] Grafana dashboard displaying metrics
- [ ] Alerts firing correctly

### Validation Queries

**Success Rate**:
```sql
SELECT 
  service_name,
  (successful_requests::float / NULLIF(total_requests, 0)) * 100 as success_rate
FROM retry_metrics_aggregate
WHERE date = CURRENT_DATE
ORDER BY service_name;
```

**Expected**: > 95% for all services

**Circuit Breaker Status**:
```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/circuit-breakers
```

**Expected**: All circuits in CLOSED state

## Troubleshooting

### Issue: Tables Not Created

**Symptoms**: Migration completes but tables missing

**Solution**:
```bash
# Check migration status
alembic current

# If not at head, rerun
alembic upgrade head

# If still failing, check PostgreSQL logs
kubectl logs -n anvil postgres-0
```

### Issue: Telemetry Not Recording

**Symptoms**: Database tables empty

**Solution**:
```bash
# Check application logs for errors
kubectl logs -n anvil -l app=anvil-backend | grep telemetry

# Verify config
kubectl get configmap anvil-config -o yaml | grep telemetry_enabled
```

### Issue: Admin API 404

**Symptoms**: Admin endpoints return 404

**Solution**:
```bash
# Verify routes registered
kubectl exec -it anvil-backend-xxx -- python -c "
from app.run import make_app
app = make_app()
for route in app.routes:
    if 'retry' in str(route.path):
        print(route.path, route.methods)
"
```

## FAQ

**Q: Will migration cause downtime?**
A: No. Migration can be done with zero downtime using rolling deployment.

**Q: How much database storage is needed?**
A: ~100MB/day for retry_attempts. Plan for 90-day retention = ~9GB.

**Q: Can I disable telemetry?**
A: Yes, set `telemetry_enabled = false` in config. Core retry still works.

**Q: How do I migrate existing retry logs?**
A: Not needed. System starts fresh with new telemetry.

---

**Last Updated**: December 1, 2025
**Version**: 1.0.0
