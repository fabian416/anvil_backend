# Request Distillation System - Operations Runbook

## Overview

This runbook provides operational procedures for monitoring, troubleshooting, and maintaining the Request Distillation System in production.

**Audience**: DevOps, SRE, Platform Engineers  
**Last Updated**: 2025-12-01  
**Version**: 1.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Monitoring](#monitoring)
3. [Troubleshooting](#troubleshooting)
4. [Common Issues](#common-issues)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Incident Response](#incident-response)
7. [Escalation](#escalation)

---

## System Overview

### Architecture

```
User Request → Rate Limit Check → Distillation (Vertex AI/DeepInfra) → Telemetry → Process/Block
```

### Components

- **Primary Provider**: Vertex AI (Gemini 1.5 Flash)
- **Fallback Provider**: DeepInfra (Llama 3.2 3B)
- **Database**: PostgreSQL (`distillation_telemetry` table)
- **Cache**: Redis (rate limiting)
- **Config**: TOML files + environment variables

### Dependencies

- Google Cloud Vertex AI API
- DeepInfra API
- PostgreSQL 13+
- Redis 6+

---

## Monitoring

### Key Metrics

**Golden Signals**:
1. **Latency**: P50/P95/P99 validation time
2. **Error Rate**: % of failed validations
3. **Throughput**: Requests per second
4. **Saturation**: Rate limit hits per hour

### SQL Queries

**Current Status (Last Hour)**:
```sql
SELECT
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE success = true) as successful,
    COUNT(*) FILTER (WHERE success = false) as failed,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) as p95_latency_ms,
    COUNT(*) FILTER (WHERE fallback_used = true) as fallback_used
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour';
```

**Provider Performance (Last 24 Hours)**:
```sql
SELECT
    provider,
    COUNT(*) as requests,
    ROUND(100.0 * COUNT(*) FILTER (WHERE success = true) / COUNT(*)::numeric, 2) as success_rate,
    ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
    ROUND(SUM(cost_usd)::numeric, 6) as total_cost_usd
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY provider;
```

**Error Analysis**:
```sql
SELECT
    reason,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER()::numeric, 2) as percentage
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '1 hour'
  AND success = false
GROUP BY reason
ORDER BY count DESC;
```

### Health Check

**Endpoint**: `GET /admin/distillation/validation/health`

**Expected Response**:
```json
{
  "healthy": true,
  "primary_provider": {
    "provider": "vertex_ai",
    "healthy": true,
    "latency_ms": 287.5,
    "error_rate": 0.02
  },
  "fallback_provider": {
    "provider": "deepinfra",
    "healthy": true,
    "latency_ms": 412.3,
    "error_rate": 0.03
  },
  "telemetry_enabled": true
}
```

### Alert Thresholds

**Critical** (Page On-Call):
- P95 latency > 2000ms for 5 minutes
- Error rate > 10% for 5 minutes
- Both providers unhealthy
- Database connection failures

**Warning** (Slack Notification):
- P95 latency > 1000ms for 10 minutes
- Error rate > 5% for 10 minutes
- Primary provider unhealthy
- Fallback usage > 20%

---

## Troubleshooting

### High Latency

**Symptoms**:
- P95 latency > 1000ms
- User complaints about slow responses

**Check**:
1. Provider health:
   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     https://api.example.com/admin/distillation/validation/health
   ```

2. Database performance:
   ```sql
   SELECT * FROM pg_stat_statements 
   WHERE query LIKE '%distillation_telemetry%' 
   ORDER BY mean_exec_time DESC LIMIT 10;
   ```

3. Network latency to providers:
   ```bash
   # Vertex AI
   curl -w "\nTime: %{time_total}s\n" \
     https://us-central1-aiplatform.googleapis.com

   # DeepInfra
   curl -w "\nTime: %{time_total}s\n" \
     https://api.deepinfra.com
   ```

**Resolution**:
- If provider latency high: Switch to fallback provider manually
- If database slow: Check connection pool, add indexes
- If network issues: Check firewall rules, DNS resolution

### High Error Rate

**Symptoms**:
- Error rate > 5%
- Failed validations in telemetry

**Check**:
1. Error reasons:
   ```sql
   SELECT error, COUNT(*) as count
   FROM distillation_telemetry
   WHERE timestamp > NOW() - INTERVAL '1 hour'
     AND error IS NOT NULL
   GROUP BY error
   ORDER BY count DESC;
   ```

2. Provider errors:
   ```bash
   grep "distillation.*error" /var/log/app.log | tail -50
   ```

**Resolution**:
- Authentication errors: Rotate API keys, check credentials
- Rate limit errors: Increase provider limits or add caching
- Timeout errors: Increase timeout or optimize prompts
- 500 errors: Check provider status pages

### Provider Failures

**Symptoms**:
- Fallback usage > 20%
- Primary provider unhealthy

**Check**:
1. Provider status:
   - Vertex AI: https://status.cloud.google.com
   - DeepInfra: https://status.deepinfra.com

2. API key validity:
   ```bash
   # Test Vertex AI
   gcloud auth application-default print-access-token

   # Test DeepInfra
   curl -H "Authorization: Bearer $DEEPINFRA_API_KEY" \
     https://api.deepinfra.com/v1/openai/models
   ```

**Resolution**:
- If provider down: Use fallback (automatic)
- If API key invalid: Rotate keys immediately
- If quota exceeded: Increase quota or throttle requests

---

## Common Issues

### Issue 1: Distillation Disabled

**Symptoms**: All requests allowed, no validation

**Check**:
```bash
echo $DISTILLATION_ENABLED
# Should output: true
```

**Fix**:
```bash
export DISTILLATION_ENABLED=true
# Restart application
systemctl restart anvil-backend
```

### Issue 2: Database Connection Lost

**Symptoms**: Error logs show connection failures

**Check**:
```bash
psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

**Fix**:
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Check connection limits
psql -c "SHOW max_connections;"

# Restart connection pool
systemctl restart anvil-backend
```

### Issue 3: Telemetry Not Recording

**Symptoms**: No new rows in `distillation_telemetry`

**Check**:
```sql
SELECT MAX(timestamp) FROM distillation_telemetry;
-- Should be recent (< 1 minute ago)
```

**Fix**:
1. Check telemetry collector is running
2. Check database write permissions
3. Check async batch queue:
   ```python
   # In production shell
   await telemetry_collector.flush()
   ```

### Issue 4: High Costs

**Symptoms**: Unexpectedly high provider bills

**Check**:
```sql
SELECT
    DATE(timestamp) as date,
    SUM(tokens_used) as total_tokens,
    SUM(cost_usd) as total_cost_usd
FROM distillation_telemetry
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp)
ORDER BY total_cost_usd DESC;
```

**Fix**:
- Switch to cheaper provider (DeepInfra)
- Reduce `max_tokens` in config
- Enable caching (future feature)
- Implement stricter rate limiting

---

## Maintenance Procedures

### Daily

1. **Check Health Status** (automated):
   ```bash
   ./scripts/check_distillation_health.sh
   ```

2. **Review Error Rates**:
   - Threshold: < 2% errors
   - Action: Investigate if > 5%

3. **Monitor Costs**:
   - Check daily spend
   - Alert if > $50/day

### Weekly

1. **Refresh Materialized View**:
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY distillation_metrics_daily;
   ```

2. **Review Performance Trends**:
   - Latency trending up?
   - Error rate increasing?
   - Fallback usage rising?

3. **Clean Old Telemetry** (optional):
   ```sql
   DELETE FROM distillation_telemetry 
   WHERE timestamp < NOW() - INTERVAL '90 days';
   ```

### Monthly

1. **Rotate API Keys**:
   - Generate new Vertex AI credentials
   - Generate new DeepInfra API key
   - Update secrets manager
   - Deploy with zero downtime

2. **Review Security Events**:
   ```sql
   SELECT COUNT(*) as injection_attempts
   FROM distillation_telemetry
   WHERE timestamp > NOW() - INTERVAL '30 days'
     AND reason = 'malicious';
   ```

3. **Capacity Planning**:
   - Review request volume trends
   - Estimate next month's costs
   - Plan for scale if needed

### Quarterly

1. **Performance Review**:
   - P95 latency trending?
   - Provider performance comparison
   - Cost optimization opportunities

2. **Security Audit**:
   - Review injection detection patterns
   - Update security rules if needed
   - Test fail-open behavior

3. **Disaster Recovery Test**:
   - Simulate provider outage
   - Test database failover
   - Verify backup restore

---

## Incident Response

### Severity Levels

**SEV-1** (Critical):
- System completely down
- Both providers failing
- Database unreachable
- **Response Time**: Immediate

**SEV-2** (High):
- High error rate (>10%)
- Primary provider down
- Severe performance degradation
- **Response Time**: < 15 minutes

**SEV-3** (Medium):
- Moderate error rate (5-10%)
- High latency (P95 > 1000ms)
- Fallback usage elevated
- **Response Time**: < 1 hour

### Incident Checklist

1. **Acknowledge** (within SLA)
2. **Assess Impact**:
   - How many users affected?
   - What's the error rate?
   - Is system degraded or down?

3. **Mitigate**:
   - Enable fail-open if needed
   - Switch providers manually
   - Scale up resources

4. **Communicate**:
   - Update status page
   - Notify stakeholders
   - Provide ETAs

5. **Resolve**:
   - Fix root cause
   - Verify recovery
   - Monitor for regression

6. **Post-Mortem**:
   - Document timeline
   - Identify root cause
   - Create prevention tasks

---

## Escalation

### On-Call Rotation

- **Primary**: Platform Team
- **Secondary**: Backend Team
- **Escalation**: Engineering Manager

### Contact Information

```
Platform Team: #platform-oncall (Slack)
PagerDuty: platform-team
Email: platform@example.com

Backend Team: #backend-oncall (Slack)
PagerDuty: backend-team
Email: backend@example.com
```

### Escalation Path

1. **< 15 min**: Platform on-call engineer
2. **< 30 min**: Platform team lead
3. **< 1 hour**: Engineering manager
4. **> 1 hour**: VP Engineering

---

## Appendix

### Useful Commands

**Check system status**:
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/admin/distillation/validation/health
```

**View recent errors**:
```bash
grep "distillation.*ERROR" /var/log/app.log | tail -50
```

**Check Redis rate limits**:
```bash
redis-cli
> KEYS distillation:ratelimit:*
> GET distillation:ratelimit:global
```

**Test provider connectivity**:
```bash
# Vertex AI
gcloud auth application-default print-access-token

# DeepInfra
curl -H "Authorization: Bearer $DEEPINFRA_API_KEY" \
  https://api.deepinfra.com/v1/openai/models
```

### Related Documentation

- Integration Guide: `docs/DISTILLATION_INTEGRATION_GUIDE.md`
- Security Guide: `docs/DISTILLATION_SECURITY_GUIDE.md`
- Technical Spec: `docs/specs/REQUEST_DISTILLATION_SPEC.md`

---

**Document Status**: ✅ Complete  
**Review Frequency**: Quarterly
