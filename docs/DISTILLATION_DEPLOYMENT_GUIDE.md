# Request Distillation System - Deployment Guide

## Overview

Step-by-step deployment guide for the Request Distillation System across all environments.

**Environments**: Development, Staging, Production  
**Last Updated**: 2025-12-01  
**Version**: 1.0

---

## Prerequisites

### Required Services

- PostgreSQL 13+ (with `distillation_telemetry` table)
- Redis 6+ (for rate limiting, optional)
- Google Cloud Project (for Vertex AI)
- DeepInfra API Account

### Required Credentials

- Vertex AI service account key (JSON file)
- DeepInfra API key
- PostgreSQL connection string
- Redis connection string (optional)

---

## Phase 1: Pre-Deployment

###Step 1: Set Up Vertex AI

```bash
# 1. Create service account
gcloud iam service-accounts create distillation-sa \
  --display-name="Distillation Service Account"

# 2. Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:distillation-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 3. Create key
gcloud iam service-accounts keys create vertex-ai-key.json \
  --iam-account=distillation-sa@PROJECT_ID.iam.gserviceaccount.com

# 4. Store key securely
mv vertex-ai-key.json /secure/path/
chmod 600 /secure/path/vertex-ai-key.json
```

### Step 2: Set Up DeepInfra

```bash
# 1. Sign up at https://deepinfra.com
# 2. Generate API key
# 3. Store in secrets manager
echo "DEEPINFRA_API_KEY=your-key-here" >> .env
```

### Step 3: Database Migration

```bash
# 1. Backup existing database
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB > backup.sql

# 2. Run migration
alembic upgrade head

# 3. Verify table exists
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB \
  -c "\d distillation_telemetry"
```

---

## Phase 2: Development Deployment

### Step 1: Configuration

```bash
# config/dev/config.toml
[distillation]
enabled = true
provider = "vertex_ai"
fallback_provider = "deepinfra"
temperature = 0.3
max_tokens = 200
timeout_seconds = 5.0
fail_open = true

[distillation.vertex_ai]
project_id = "anvil-dev"
location = "us-central1"
model = "gemini-1.5-flash"

[distillation.deepinfra]
model = "meta-llama/Llama-3.2-3B-Instruct"
```

### Step 2: Environment Variables

```bash
# .env.dev
DISTILLATION_ENABLED=true
VERTEX_AI_PROJECT_ID=anvil-dev
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_CREDENTIALS_PATH=/path/to/vertex-ai-key-dev.json
DEEPINFRA_API_KEY=your-dev-api-key
```

### Step 3: Deploy

```bash
# 1. Deploy code
git checkout develop
git pull origin develop

# 2. Install dependencies
uv pip install -e '.[dev]'

# 3. Run migrations
alembic upgrade head

# 4. Restart application
systemctl restart anvil-backend-dev

# 5. Verify
curl -H "Authorization: Bearer $TOKEN" \
  https://dev-api.example.com/admin/distillation/validation/health
```

---

## Phase 3: Staging Deployment

### Step 1: Smoke Testing

```bash
# Test in dev first
pytest tests/integration/distillation/ -v

# Manual testing
curl -X POST https://dev-api.example.com/api/v1/chat/conversations/ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"content": "What is the TVL of Aave?"}'
```

### Step 2: Configuration

```bash
# config/staging/config.toml
[distillation]
enabled = true
provider = "vertex_ai"
fallback_provider = "deepinfra"
# ... same as dev
```

### Step 3: Deploy

```bash
# 1. Merge to staging
git checkout staging
git merge develop

# 2. Deploy
./scripts/deploy-staging.sh

# 3. Run migrations
alembic upgrade head

# 4. Monitor for 1 hour
watch -n 60 'curl -H "Authorization: Bearer $TOKEN" \
  https://staging-api.example.com/admin/distillation/validation/health'
```

---

## Phase 4: Production Deployment

### Step 1: Pre-Production Checklist

- [ ] All tests passing in staging
- [ ] Performance validated (latency, throughput)
- [ ] Security review completed
- [ ] Runbook reviewed
- [ ] Rollback plan documented
- [ ] On-call engineer notified
- [ ] Monitoring dashboards ready
- [ ] Alert thresholds configured

### Step 2: Blue-Green Deployment

```bash
# Phase 1: Deploy to Green (50% traffic)
kubectl set image deployment/anvil-backend \
  anvil-backend=anvil-backend:v2.0.0-distillation \
  --namespace=production-green

# Wait 30 minutes, monitor metrics

# Phase 2: Route 100% traffic to Green
kubectl patch service anvil-backend \
  -p '{"spec":{"selector":{"version":"v2.0.0-distillation"}}}' \
  --namespace=production

# Phase 3: Update Blue as backup
kubectl set image deployment/anvil-backend \
  anvil-backend=anvil-backend:v2.0.0-distillation \
  --namespace=production-blue
```

### Step 3: Configuration

```bash
# config/prod/config.toml
[distillation]
enabled = false  # Start disabled!
provider = "vertex_ai"
fallback_provider = "deepinfra"
temperature = 0.3
max_tokens = 200
timeout_seconds = 5.0
fail_open = true  # Critical for production

[distillation.telemetry]
enabled = true
async_recording = true
batch_size = 100
flush_interval_seconds = 60
```

### Step 4: Gradual Rollout

```bash
# Day 1: Enable for 1% of users (feature flag)
curl -X PATCH https://api.example.com/admin/feature-flags/distillation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true, "percentage": 1}'

# Monitor for 24 hours

# Day 2: Increase to 5%
curl -X PATCH https://api.example.com/admin/feature-flags/distillation \
  -d '{"percentage": 5}'

# Day 3: Increase to 25%
# Day 4: Increase to 50%
# Day 5: Increase to 100%
```

### Step 5: Post-Deployment Verification

```bash
# 1. Health check
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/admin/distillation/validation/health

# 2. Check metrics
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/admin/distillation/validation/metrics?days=1

# 3. Monitor error rates
psql -c "SELECT reason, COUNT(*) FROM distillation_telemetry \
  WHERE timestamp > NOW() - INTERVAL '1 hour' \
  AND success = false GROUP BY reason;"

# 4. Check costs
psql -c "SELECT SUM(cost_usd) FROM distillation_telemetry \
  WHERE timestamp > NOW() - INTERVAL '24 hours';"
```

---

## Phase 5: Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# Option 1: Disable via environment variable
kubectl set env deployment/anvil-backend \
  DISTILLATION_ENABLED=false \
  --namespace=production

# Option 2: Rollback deployment
kubectl rollout undo deployment/anvil-backend --namespace=production

# Option 3: Switch traffic to Blue
kubectl patch service anvil-backend \
  -p '{"spec":{"selector":{"version":"v1.9.0"}}}' \
  --namespace=production
```

### Partial Rollback (Feature Flag)

```bash
# Reduce to 0% (disable for all users)
curl -X PATCH https://api.example.com/admin/feature-flags/distillation \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"percentage": 0}'
```

### Database Rollback

```bash
# If migration causes issues
alembic downgrade -1

# Restore from backup
psql -h $POSTGRES_HOST -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

---

## Monitoring & Validation

### Key Metrics to Watch (First 24 Hours)

1. **Error Rate**: Should be < 2%
2. **P95 Latency**: Should be < 500ms
3. **Fallback Usage**: Should be < 5%
4. **Provider Costs**: Should match estimates

### SQL Queries

```sql
-- Hourly summary
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as requests,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success = true) / COUNT(*), 2) as success_rate,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
    SUM(cost_usd) as cost_usd
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Troubleshooting Deployment Issues

### Issue: Migration Fails

```bash
# Check current version
alembic current

# View pending migrations
alembic heads

# Run migration with verbose output
alembic upgrade head --verbose

# If fails, rollback and investigate
alembic downgrade -1
```

### Issue: Provider Authentication Fails

```bash
# Vertex AI
gcloud auth application-default print-access-token
# Should return valid token

# DeepInfra
curl -H "Authorization: Bearer $DEEPINFRA_API_KEY" \
  https://api.deepinfra.com/v1/openai/models
# Should return 200 OK
```

### Issue: High Latency After Deployment

```bash
# Check provider latency
time curl -X POST https://us-central1-aiplatform.googleapis.com/...
# Should be < 200ms

# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"
# Should be < max_connections

# Check network
traceroute us-central1-aiplatform.googleapis.com
```

---

## Post-Deployment Tasks

### Day 1-7

- [ ] Monitor error rates daily
- [ ] Review cost trends
- [ ] Check performance metrics
- [ ] Collect user feedback

### Week 2-4

- [ ] Analyze blocked requests (false positives?)
- [ ] Optimize confidence thresholds
- [ ] Review provider performance
- [ ] Update documentation

### Month 2+

- [ ] Quarterly security audit
- [ ] Cost optimization review
- [ ] Capacity planning
- [ ] Feature improvements

---

## Success Criteria

### Technical

- ✅ Error rate < 2%
- ✅ P95 latency < 500ms
- ✅ Zero downtime deployment
- ✅ All tests passing

### Business

- ✅ Cost savings > $10K/month
- ✅ Security incidents blocked
- ✅ User satisfaction maintained
- ✅ SLA targets met

---

## References

- Operations Runbook: `docs/DISTILLATION_OPERATIONS_RUNBOOK.md`
- Integration Guide: `docs/DISTILLATION_INTEGRATION_GUIDE.md`
- Technical Spec: `docs/specs/REQUEST_DISTILLATION_SPEC.md`

---

**Document Status**: ✅ Complete  
**Review Frequency**: After each major deployment
