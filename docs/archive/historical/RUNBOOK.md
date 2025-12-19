# Operations Runbook

## Overview

This runbook provides procedures for operating and troubleshooting the Multi-LLM Orchestration System.

---

## Quick Reference

### Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Basic health | `{"status": "ok"}` |
| `GET /admin/llm/health` | Detailed health | Full system status |
| `GET /metrics` | Prometheus metrics | Metrics text |

### Key Metrics to Monitor

| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | >2% | >5% |
| P95 Latency | >5s | >10s |
| Circuit Breakers Open | Any | >1 |
| Budget Usage | >80% | >95% |

---

## Common Operations

### 1. Force Provider Health Check

```bash
# Via API
curl -X POST https://api.anvil.finance/admin/llm/providers/{id}/health-check \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Via CLI
python manage.py llm health-check --provider vertex_ai
```

### 2. Reset Circuit Breaker

```bash
# Via API
curl -X POST https://api.anvil.finance/admin/llm/circuit-breakers/{id}/reset \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Via CLI
python manage.py llm circuit-breaker reset --entity model --id gemini-1.5-pro
```

### 3. Recalculate Rankings

```bash
# All agents
curl -X POST https://api.anvil.finance/admin/llm/rankings/recalculate \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Specific agent
curl -X POST https://api.anvil.finance/admin/llm/rankings/recalculate \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"agent_type": "swap_agent"}'
```

### 4. Emergency Model Override

```bash
curl -X POST https://api.anvil.finance/admin/llm/rankings/override \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "agent_type": "swap_agent",
    "model_id": "uuid-of-fallback-model",
    "override_score": 0.99,
    "reason": "Emergency fallback during incident",
    "expires_at": "2025-12-02T00:00:00Z"
  }'
```

### 5. Disable Provider

```bash
curl -X PUT https://api.anvil.finance/admin/llm/providers/{id} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"is_enabled": false}'
```

---

## Incident Response

### High Error Rate (>5%)

**Symptoms**: 
- Alert: `LLMHighErrorRate`
- Dashboard shows elevated failures

**Diagnosis**:
```bash
# Check error breakdown
curl "https://api.anvil.finance/admin/llm/telemetry/errors?period=1h"

# Check provider health
curl "https://api.anvil.finance/admin/llm/health"
```

**Resolution**:
1. Identify failing provider/model
2. Check circuit breaker status
3. If provider-wide issue, disable provider temporarily
4. If model-specific, disable model or add override
5. Monitor recovery

### Provider Down

**Symptoms**:
- Alert: `LLMProviderDown`
- Circuit breaker open
- Health check failing

**Diagnosis**:
```bash
# Check provider status
curl "https://api.anvil.finance/admin/llm/providers"

# Check circuit breaker
curl "https://api.anvil.finance/admin/llm/circuit-breakers"
```

**Resolution**:
1. Verify provider status on their status page
2. System should automatically failover
3. Monitor fallback provider load
4. If extended outage, consider disabling provider
5. When recovered, reset circuit breaker

### High Latency

**Symptoms**:
- Alert: `LLMHighLatency`
- P95 >10 seconds

**Diagnosis**:
```bash
# Check latency by model
curl "https://api.anvil.finance/admin/llm/telemetry/timeseries?metric=latency&group_by=model"
```

**Resolution**:
1. Identify slow model
2. Check if specific to one agent type
3. Rankings should auto-demote slow models
4. Force ranking recalculation if needed
5. Consider temporary override to faster model

### Budget Exceeded

**Symptoms**:
- Alert: `LLMBudgetCritical`
- Requests rejected (if hard limit)

**Resolution**:
1. Check current spend vs budget
2. Increase budget if approved
3. Or wait for period reset
4. Review high-cost usage patterns
5. Consider adding cost caps per user/agent

---

## Maintenance Procedures

### Database Maintenance

```bash
# Run hourly aggregation manually
python manage.py llm aggregate-telemetry --hour "2025-12-01T10:00:00Z"

# Cleanup old data (>90 days)
python manage.py llm cleanup --older-than 90d

# Vacuum tables
psql -c "VACUUM ANALYZE llm_requests;"
psql -c "VACUUM ANALYZE llm_telemetry_hourly;"
```

### Scaling

```bash
# Scale orchestrator pods
kubectl scale deployment llm-orchestrator --replicas=10

# Check HPA status
kubectl get hpa llm-orchestrator
```

### Configuration Updates

```bash
# Update retry config
curl -X PUT https://api.anvil.finance/admin/llm/config/retry_config \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "value": {"max_retries_per_provider": 3},
    "reason": "Increased retries for stability"
  }'
```

---

## Monitoring Dashboards

### Grafana Dashboards

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| LLM Overview | `/d/llm-overview` | High-level metrics |
| Provider Health | `/d/llm-providers` | Per-provider details |
| Cost Analysis | `/d/llm-costs` | Cost tracking |
| Error Analysis | `/d/llm-errors` | Error breakdown |

### Key Queries

```promql
# Error rate
sum(rate(llm_errors_total[5m])) / sum(rate(llm_requests_total[5m]))

# P95 latency
histogram_quantile(0.95, rate(llm_request_duration_seconds_bucket[5m]))

# Cost per hour
sum(increase(llm_cost_usd_total[1h]))

# Active requests
sum(llm_active_requests)
```

---

## Contacts

| Role | Contact | Escalation |
|------|---------|------------|
| On-Call | PagerDuty | Auto-escalates after 15m |
| Engineering Lead | Slack: #llm-ops | For P1 incidents |
| Provider Support | See provider docs | Extended outages |

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-01 | Initial runbook | DevOps |
