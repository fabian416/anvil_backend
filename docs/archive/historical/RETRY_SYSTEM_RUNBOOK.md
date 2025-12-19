# Retry System Operations Runbook

## Overview

This runbook provides operational procedures for monitoring, troubleshooting, and managing the enterprise retry system in production.

## Quick Reference

| Issue | Action | Command/Endpoint |
|-------|--------|------------------|
| High failure rate | Check circuit breaker status | `GET /api/v1/admin/retry/circuit-breakers` |
| Service down | Disable service temporarily | `POST /api/v1/admin/retry/services/{name}/disable` |
| Circuit stuck open | Reset circuit breaker | `POST /api/v1/admin/retry/circuit-breakers/{name}/reset` |
| Check metrics | View 7-day metrics | `GET /api/v1/admin/retry/metrics/{name}?days=7` |

## Monitoring

### Key Metrics

**Success Rate**:
```sql
SELECT 
  service_name,
  date,
  (successful_requests::float / NULLIF(total_requests, 0)) * 100 as success_rate_pct
FROM retry_metrics_aggregate
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, service_name;
```

**Circuit Breaker Opens**:
```sql
SELECT 
  service_name,
  COUNT(*) as open_count
FROM circuit_breaker_events
WHERE to_state = 'OPEN'
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY service_name
ORDER BY open_count DESC;
```

**Retry Rate**:
```sql
SELECT 
  service_name,
  SUM(retry_attempts)::float / NULLIF(SUM(total_requests), 0) as retry_rate
FROM retry_metrics_aggregate
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY service_name
ORDER BY retry_rate DESC;
```

### Alerts

**Critical Alerts** (PagerDuty):
- Success rate < 90% for 5 minutes
- Circuit breaker opens > 10/hour
- Service disabled for > 4 hours (check if intentional)

**Warning Alerts** (Slack):
- Success rate 90-95% for 10 minutes
- Retry rate > 30% for 15 minutes
- P99 latency > 10s for 5 minutes

## Common Issues

### Issue 1: High Failure Rate

**Symptoms**:
- Success rate < 95%
- Increased retry attempts
- Circuit breaker opens

**Diagnosis**:
```bash
# Check circuit breaker status
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/circuit-breakers

# Check recent failures
psql -d anvil_db -c "
SELECT service_name, error_type, COUNT(*)
FROM retry_attempts
WHERE success = false AND created_at >= NOW() - INTERVAL '1 hour'
GROUP BY service_name, error_type
ORDER BY count DESC;
"
```

**Resolution**:
1. **Rate Limit**: If error_type=`rate_limit`, disable service temporarily
2. **Timeout**: If error_type=`timeout`, check network/service health
3. **Service Unavailable**: Check external API status page

### Issue 2: Circuit Breaker Stuck Open

**Symptoms**:
- Circuit state = OPEN for > 5 minutes
- No requests getting through
- Success rate = 0%

**Diagnosis**:
```bash
# Check circuit breaker status
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/circuit-breakers

# Check when it opened
psql -d anvil_db -c "
SELECT service_name, to_state, reason, created_at
FROM circuit_breaker_events
WHERE service_name = 'defillama_mcp' AND to_state = 'OPEN'
ORDER BY created_at DESC LIMIT 5;
"
```

**Resolution**:
1. Verify external service is healthy
2. Reset circuit breaker manually:
```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Manual reset after verifying service health"}' \
  https://api.anvil.com/api/v1/admin/retry/circuit-breakers/defillama_mcp/reset
```

### Issue 3: Service Override Expired

**Symptoms**:
- Service was disabled, duration expired, but still seeing errors

**Resolution**:
```bash
# Check current status
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/services/defillama_mcp

# If override expired but service still down, disable again
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Service still down", "duration_minutes": 60}' \
  https://api.anvil.com/api/v1/admin/retry/services/defillama_mcp/disable
```

## Operational Procedures

### Planned Maintenance

**Scenario**: External API (e.g., 1inch) has scheduled downtime.

**Steps**:
1. Disable service before maintenance starts:
```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "1inch scheduled maintenance - https://status.1inch.io/",
    "duration_minutes": 180
  }' \
  https://api.anvil.com/api/v1/admin/retry/services/oneinch_mcp/disable
```

2. Verify service is disabled:
```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.anvil.com/api/v1/admin/retry/services/oneinch_mcp
```

3. After maintenance, enable service:
```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "1inch maintenance complete - verified API is online"}' \
  https://api.anvil.com/api/v1/admin/retry/services/oneinch_mcp/enable
```

### Emergency: Rate Limit Exhausted

**Scenario**: Service hitting rate limits repeatedly.

**Steps**:
1. Disable service immediately:
```bash
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Rate limit exhausted", "duration_minutes": 60}' \
  https://api.anvil.com/api/v1/admin/retry/services/coingecko_mcp/disable
```

2. Check rate limit details in logs:
```bash
kubectl logs -n anvil -l app=anvil-backend --tail=100 | grep rate_limit
```

3. Wait for rate limit window to reset (usually 1 hour)

4. Enable service after rate limit resets

### Database Maintenance

**Retention Cleanup** (run monthly):
```sql
-- Delete old retry_attempts (keep 90 days)
DELETE FROM retry_attempts WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete old circuit_breaker_events (keep 180 days)
DELETE FROM circuit_breaker_events WHERE created_at < NOW() - INTERVAL '180 days';

-- Delete old service_override_events (keep 365 days)
DELETE FROM service_override_events WHERE created_at < NOW() - INTERVAL '365 days';

-- Vacuum analyze
VACUUM ANALYZE retry_attempts;
VACUUM ANALYZE circuit_breaker_events;
VACUUM ANALYZE service_override_events;
VACUUM ANALYZE retry_metrics_aggregate;
```

## Dashboard Access

**Admin Dashboard**: https://admin.anvil.com/retry

**Grafana**: https://grafana.anvil.com/d/retry-system

**Datadog**: https://app.datadoghq.com/dashboard/retry-system

## Escalation

**On-Call Engineer**:
- PagerDuty: retry-system-oncall
- Slack: #ops-retry-system

**Subject Matter Experts**:
- Retry System: @backend-team
- MCP Servers: @integration-team
- Agno Agents: @ai-team

## Runbook Maintenance

**Last Updated**: December 1, 2025
**Next Review**: March 1, 2026
**Owner**: Backend Team

