# 🛠️ LLM Orchestration System - Operations Guide

## Overview

This guide provides operational procedures for managing the Enterprise Multi-LLM Orchestration System in production.

**Audience**: DevOps, SREs, Engineering Managers, Business Stakeholders

---

## 📊 Monitoring & Alerts

### **Key Metrics to Monitor**

| Metric | Normal Range | Alert Threshold | Action Required |
|--------|--------------|-----------------|-----------------|
| **System Uptime** | >99.9% | <99.5% | Investigate provider health |
| **Success Rate** | >98% | <95% | Check circuit breakers |
| **P95 Latency** | <2s | >3s | Review model selection |
| **P99 Latency** | <3s | >5s | Check for timeouts |
| **Daily Cost** | <$500 | >$600 | Review budget settings |
| **Circuit Breakers Open** | 0 | >2 | Investigate failing providers |
| **Retry Rate** | <5% | >10% | Check provider reliability |

### **Alert Configuration**

```yaml
# alerts.yaml (Prometheus/Grafana)
groups:
  - name: llm_orchestration
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(llm_requests_total{status="failed"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High LLM error rate detected"
          
      - alert: BudgetThresholdExceeded
        expr: llm_budget_used_percentage > 80
        for: 1m
        annotations:
          summary: "Budget warning threshold reached"
          
      - alert: CircuitBreakerOpen
        expr: llm_circuit_breaker_state{state="open"} > 0
        for: 5m
        annotations:
          summary: "Circuit breaker opened for LLM provider"
```

---

## 🚀 Deployment Procedures

### **Initial Deployment**

```bash
# 1. Database migration
alembic upgrade head

# 2. Seed initial data
psql $DATABASE_URL < scripts/seed_llm_providers.sql

# 3. Verify configuration
python -m app.setup.config.llm_orchestration

# 4. Start application
make start

# 5. Verify health
curl http://localhost:8000/admin/llm/dashboard/health
```

### **Rolling Update (Zero Downtime)**

```bash
# 1. Deploy new version to staging
kubectl apply -f k8s/staging/deployment.yaml

# 2. Run smoke tests
./scripts/smoke_test_llm.sh

# 3. Deploy to production (canary)
kubectl set image deployment/llm-orchestration \
  api=anvil/llm-orchestration:v1.1.0 --record

# 4. Monitor for 15 minutes
kubectl rollout status deployment/llm-orchestration

# 5. If issues, rollback
kubectl rollout undo deployment/llm-orchestration

# 6. If successful, scale up
kubectl scale deployment/llm-orchestration --replicas=5
```

### **Rollback Procedure**

```bash
# Quick rollback
kubectl rollout undo deployment/llm-orchestration

# Rollback to specific version
kubectl rollout undo deployment/llm-orchestration --to-revision=3

# Verify rollback
kubectl rollout status deployment/llm-orchestration
```

---

## 🔧 Common Operations

### **1. Enable/Disable a Provider**

**Via Admin API:**
```bash
# Disable provider
curl -X PUT http://localhost:8000/admin/llm/providers/{provider_id} \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": false}'

# Re-enable provider
curl -X PUT http://localhost:8000/admin/llm/providers/{provider_id} \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true}'
```

**Direct Database:**
```sql
-- Disable Vertex AI
UPDATE llm_providers 
SET is_enabled = false, updated_at = NOW()
WHERE name = 'vertex_ai';

-- Re-enable
UPDATE llm_providers 
SET is_enabled = true, updated_at = NOW()
WHERE name = 'vertex_ai';
```

### **2. Reset Circuit Breaker**

**Via Admin API:**
```bash
curl -X POST http://localhost:8000/admin/llm/circuit-breakers/{breaker_id}/reset
```

**Direct Database:**
```sql
UPDATE circuit_breakers
SET state = 'closed',
    failure_count = 0,
    consecutive_failures = 0,
    updated_at = NOW()
WHERE entity_name = 'gemini-1.5-pro';
```

### **3. Adjust Budget**

**Via Admin API:**
```bash
curl -X PUT http://localhost:8000/admin/llm/budgets/{budget_id} \
  -H "Content-Type: application/json" \
  -d '{"budget_amount_usd": 1000.00}'
```

**Direct Database:**
```sql
UPDATE llm_cost_budgets
SET budget_amount_usd = 1000.00,
    updated_at = NOW()
WHERE name = 'Daily Operations';
```

### **4. Force Ranking Recalculation**

**Via Admin API:**
```bash
curl -X POST http://localhost:8000/admin/llm/rankings/recalculate \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "swap_agent"}'
```

**Via Celery:**
```bash
# Trigger task immediately
celery -A app.infrastructure.celery.app call recalculate_llm_rankings
```

### **5. Manual Ranking Override**

**Via Admin API:**
```bash
curl -X POST http://localhost:8000/admin/llm/rankings/override \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "swap_agent",
    "model_id": "uuid-of-model",
    "override_score": 1.0,
    "reason": "Emergency fallback to Claude"
  }'
```

### **6. Export Metrics**

**Via Admin API:**
```bash
curl -X POST http://localhost:8000/admin/llm/dashboard/export \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "data_type": "costs",
    "period": "30d"
  }'
```

---

## 🚨 Troubleshooting

### **Problem: High Error Rate**

**Symptoms:**
- Success rate drops below 95%
- Many failed requests in logs
- Circuit breakers opening

**Investigation:**
```bash
# Check provider health
curl http://localhost:8000/admin/llm/providers

# Check circuit breaker states
curl http://localhost:8000/admin/llm/circuit-breakers

# View recent errors
curl http://localhost:8000/admin/llm/telemetry/overview?period=1h
```

**Resolution:**
1. Identify failing provider(s)
2. Check provider status pages
3. Reset circuit breakers if transient
4. Disable provider if persistent issue
5. Monitor for recovery

### **Problem: Budget Exceeded**

**Symptoms:**
- Requests being blocked
- Budget alerts firing
- HTTP 429 responses

**Investigation:**
```bash
# Check current spend
curl http://localhost:8000/admin/llm/budgets

# View cost breakdown
curl http://localhost:8000/admin/llm/telemetry/cost?period=24h
```

**Resolution:**
1. Review cost by provider/agent
2. Adjust budget if legitimate spike
3. Investigate unexpected usage patterns
4. Consider cheaper models for non-critical agents
5. Enable response caching

### **Problem: High Latency**

**Symptoms:**
- P95 latency >3s
- User complaints about slow responses
- Timeout errors increasing

**Investigation:**
```bash
# Check latency by provider
curl http://localhost:8000/admin/llm/telemetry/overview?period=1h

# Check model performance
curl http://localhost:8000/admin/llm/models/{model_id}/performance
```

**Resolution:**
1. Identify slow provider(s)
2. Check if models are overloaded
3. Adjust ranking weights to prioritize latency
4. Enable faster models (e.g., Gemini Flash)
5. Review timeout settings

### **Problem: Circuit Breaker Stuck Open**

**Symptoms:**
- Circuit breaker remains open
- Provider appears healthy but not used
- Requests bypassing a working provider

**Investigation:**
```bash
# Check circuit breaker state
curl http://localhost:8000/admin/llm/circuit-breakers

# Check provider health
curl http://localhost:8000/admin/llm/providers/{provider_id}/health-check
```

**Resolution:**
1. Verify provider is actually healthy
2. Manually reset circuit breaker
3. Review circuit breaker thresholds
4. Check for configuration issues

---

## 📈 Performance Optimization

### **1. Enable Response Caching**

```sql
-- Enable caching in config
UPDATE llm_business_config
SET config_value = '{"enable_caching": true, "ttl_seconds": 3600}'::jsonb
WHERE config_key = 'feature_flags';
```

**Benefits:**
- 10-30% cost reduction
- 90% latency reduction for cached requests
- Reduced provider load

### **2. Optimize Model Selection**

```bash
# Adjust weights to prioritize cost
curl -X PUT http://localhost:8000/admin/llm/rankings/weights \
  -d '{
    "agent_type": "portfolio_agent",
    "weights": {
      "success_weight": 0.40,
      "latency_weight": 0.20,
      "cost_weight": 0.30,
      "recency_weight": 0.10
    }
  }'
```

### **3. Tune Circuit Breaker Settings**

```sql
-- Less aggressive circuit breaker for stable providers
UPDATE circuit_breakers
SET config = jsonb_set(
  config,
  '{failure_threshold}',
  '10'  -- Increased from 5
)
WHERE entity_type = 'provider' AND entity_name = 'vertex_ai';
```

### **4. Database Query Optimization**

```sql
-- Create additional indexes for common queries
CREATE INDEX idx_requests_cost ON llm_requests(actual_cost_usd DESC, created_at DESC)
WHERE status = 'completed';

CREATE INDEX idx_telemetry_cost ON llm_telemetry_hourly(hour_bucket DESC, total_cost_usd DESC);
```

---

## 🔐 Security Operations

### **API Key Rotation**

```bash
# 1. Generate new API key from provider
# 2. Update secrets
kubectl create secret generic llm-secrets \
  --from-literal=VERTEX_AI_PROJECT_ID=new-project \
  --from-literal=DEEPINFRA_API_KEY=new-key \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Rolling restart
kubectl rollout restart deployment/llm-orchestration

# 4. Verify health
kubectl exec -it llm-orchestration-xxx -- \
  curl http://localhost:8000/admin/llm/dashboard/health
```

### **Audit Log Review**

```sql
-- View recent admin actions
SELECT 
  action_type,
  entity_type,
  entity_id,
  actor_id,
  before_value,
  after_value,
  timestamp
FROM llm_audit_log
ORDER BY timestamp DESC
LIMIT 50;

-- Find suspicious activity
SELECT 
  actor_id,
  COUNT(*) as action_count,
  ARRAY_AGG(DISTINCT action_type) as actions
FROM llm_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY actor_id
HAVING COUNT(*) > 20;
```

---

## 📊 Cost Management

### **Daily Cost Review**

```sql
-- Daily cost summary
SELECT 
  date,
  provider_id,
  p.display_name as provider,
  total_cost_usd,
  total_requests,
  total_cost_usd / NULLIF(total_requests, 0) as avg_cost_per_request
FROM llm_cost_daily lcd
JOIN llm_providers p ON p.id = lcd.provider_id
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC, total_cost_usd DESC;
```

### **Cost Anomaly Detection**

```sql
-- Detect unusual cost spikes
WITH daily_avg AS (
  SELECT 
    provider_id,
    AVG(total_cost_usd) as avg_daily_cost,
    STDDEV(total_cost_usd) as stddev_cost
  FROM llm_cost_daily
  WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY provider_id
)
SELECT 
  lcd.date,
  p.display_name,
  lcd.total_cost_usd,
  da.avg_daily_cost,
  (lcd.total_cost_usd - da.avg_daily_cost) / da.stddev_cost as z_score
FROM llm_cost_daily lcd
JOIN llm_providers p ON p.id = lcd.provider_id
JOIN daily_avg da ON da.provider_id = lcd.provider_id
WHERE (lcd.total_cost_usd - da.avg_daily_cost) / da.stddev_cost > 2
ORDER BY z_score DESC;
```

### **Budget Adjustment Strategy**

**When to Increase Budget:**
- Consistent budget warnings (80%+)
- Legitimate usage growth
- New features launched
- Seasonal traffic spikes

**When to Decrease Budget:**
- Consistently under 50% usage
- Cost optimization efforts working
- Feature deprecation

**Best Practice:**
- Review budgets monthly
- Set soft limits first (warnings only)
- Enable hard limits after baseline established
- Monitor for 1 week after changes

---

## 🔄 Maintenance Tasks

### **Weekly Tasks**

```bash
# 1. Review provider health trends
curl http://localhost:8000/admin/llm/providers

# 2. Check circuit breaker statistics
curl http://localhost:8000/admin/llm/circuit-breakers

# 3. Review cost trends
curl http://localhost:8000/admin/llm/telemetry/cost?period=7d

# 4. Verify ranking updates
curl http://localhost:8000/admin/llm/rankings

# 5. Check for alerts
curl http://localhost:8000/admin/llm/dashboard | jq '.data.active_alerts'
```

### **Monthly Tasks**

```bash
# 1. Review monthly costs
curl http://localhost:8000/admin/llm/telemetry/cost?period=30d > monthly_report.json

# 2. Export cost data
curl -X POST http://localhost:8000/admin/llm/dashboard/export \
  -d '{"format": "csv", "data_type": "costs", "period": "30d"}'

# 3. Review and adjust budgets
# 4. Update ranking weight profiles (if needed)
# 5. Review audit log for unusual activity
```

### **Quarterly Tasks**

- Evaluate new provider options
- Review model pricing changes
- Update cost projections
- Optimize ranking weights based on data
- Security audit (API key rotation)

---

## 🎯 Performance Tuning

### **Optimizing for Cost**

```bash
# Increase cost weight for all agents
for agent in swap_agent trading_agent portfolio_agent; do
  curl -X PUT http://localhost:8000/admin/llm/rankings/weights \
    -d "{
      \"agent_type\": \"$agent\",
      \"weights\": {
        \"success_weight\": 0.40,
        \"latency_weight\": 0.20,
        \"cost_weight\": 0.30,
        \"recency_weight\": 0.10
      }
    }"
done
```

### **Optimizing for Speed**

```bash
# Increase latency weight
curl -X PUT http://localhost:8000/admin/llm/rankings/weights \
  -d '{
    "agent_type": "swap_agent",
    "weights": {
      "success_weight": 0.45,
      "latency_weight": 0.40,
      "cost_weight": 0.10,
      "recency_weight": 0.05
    }
  }'
```

### **Optimizing for Accuracy**

```bash
# Increase success weight
curl -X PUT http://localhost:8000/admin/llm/rankings/weights \
  -d '{
    "agent_type": "risk_analyzer",
    "weights": {
      "success_weight": 0.70,
      "latency_weight": 0.15,
      "cost_weight": 0.10,
      "recency_weight": 0.05
    }
  }'
```

---

## 🐛 Debugging Guide

### **Debug High Latency**

```sql
-- Find slow requests
SELECT 
  request_id,
  agent_type,
  selected_provider_id,
  selected_model_id,
  total_latency_ms,
  attempt_count,
  status,
  created_at
FROM llm_requests
WHERE total_latency_ms > 5000
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY total_latency_ms DESC
LIMIT 20;

-- Check if specific model is slow
SELECT 
  m.display_name,
  COUNT(*) as request_count,
  AVG(r.total_latency_ms) as avg_latency,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY r.total_latency_ms) as p95_latency
FROM llm_requests r
JOIN llm_models m ON m.id = r.selected_model_id
WHERE r.created_at > NOW() - INTERVAL '24 hours'
  AND r.status = 'completed'
GROUP BY m.id, m.display_name
ORDER BY avg_latency DESC;
```

### **Debug High Error Rate**

```sql
-- Error breakdown by type
SELECT 
  error_code,
  COUNT(*) as count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM llm_requests
WHERE status = 'failed'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY error_code
ORDER BY count DESC;

-- Errors by provider
SELECT 
  p.display_name,
  COUNT(*) as error_count,
  COUNT(DISTINCT r.error_code) as unique_errors,
  ARRAY_AGG(DISTINCT r.error_code) as error_codes
FROM llm_requests r
JOIN llm_providers p ON p.id = r.selected_provider_id
WHERE r.status = 'failed'
  AND r.created_at > NOW() - INTERVAL '24 hours'
GROUP BY p.id, p.display_name
ORDER BY error_count DESC;
```

### **Debug Circuit Breaker Issues**

```sql
-- Circuit breaker history
SELECT 
  cb.entity_type,
  cb.entity_name,
  cb.state,
  cb.failure_count,
  cb.consecutive_failures,
  cb.last_failure_at,
  cb.opened_at,
  cb.config
FROM circuit_breakers cb
WHERE cb.state != 'closed'
ORDER BY cb.last_failure_at DESC;

-- Requests affected by circuit breaker
SELECT 
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as blocked_requests
FROM llm_requests
WHERE status = 'failed'
  AND error_code = 'circuit_breaker_open'
  AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## 📞 Escalation Procedures

### **Severity Levels**

**SEV-1 (Critical):**
- All providers down
- Circuit breakers open for all models
- Success rate <80%
- **Response**: Page on-call engineer immediately

**SEV-2 (High):**
- Single provider down
- Success rate 80-95%
- Budget hard limit reached
- **Response**: Alert engineering team, respond within 1 hour

**SEV-3 (Medium):**
- Single model degraded
- Success rate 95-98%
- Budget warning threshold (80%)
- **Response**: Create ticket, respond within 4 hours

**SEV-4 (Low):**
- Minor performance degradation
- Success rate >98%
- Budget approaching warning (70%)
- **Response**: Monitor, review in next sprint

### **Escalation Contacts**

| Issue | Primary Contact | Secondary Contact |
|-------|----------------|-------------------|
| Provider outage | DevOps on-call | Engineering lead |
| Budget exceeded | Engineering manager | Finance team |
| Performance issues | Backend team lead | DevOps |
| Security concerns | Security team | CTO |

---

## 🔄 Disaster Recovery

### **Scenario: All Providers Down**

**Immediate Actions:**
1. Check provider status pages
2. Verify API keys are valid
3. Test health checks manually
4. Review recent deployments

**Recovery Steps:**
1. Enable cached responses (if available)
2. Display maintenance message to users
3. Contact provider support
4. Monitor for recovery
5. Reset circuit breakers once recovered

### **Scenario: Database Corruption**

**Recovery Steps:**
1. Stop application
2. Restore from latest backup
3. Verify data integrity
4. Run migrations if needed
5. Restart application
6. Verify health

**Prevention:**
- Hourly backups
- Point-in-time recovery enabled
- Replication to standby
- Regular backup testing

---

## 📚 Useful Queries

### **Top 10 Most Expensive Requests**

```sql
SELECT 
  request_id,
  agent_type,
  m.display_name as model,
  actual_cost_usd,
  total_latency_ms,
  input_tokens,
  output_tokens,
  created_at
FROM llm_requests r
JOIN llm_models m ON m.id = r.selected_model_id
WHERE r.created_at > NOW() - INTERVAL '7 days'
  AND r.status = 'completed'
ORDER BY actual_cost_usd DESC
LIMIT 10;
```

### **Provider Success Rate (Last 24h)**

```sql
SELECT 
  p.display_name,
  COUNT(*) as total_requests,
  SUM(CASE WHEN r.status = 'completed' THEN 1 ELSE 0 END) as successful,
  SUM(CASE WHEN r.status = 'failed' THEN 1 ELSE 0 END) as failed,
  (SUM(CASE WHEN r.status = 'completed' THEN 1 ELSE 0 END)::float / COUNT(*)) * 100 as success_rate
FROM llm_requests r
JOIN llm_providers p ON p.id = r.selected_provider_id
WHERE r.created_at > NOW() - INTERVAL '24 hours'
GROUP BY p.id, p.display_name
ORDER BY success_rate DESC;
```

### **Ranking Changes Over Time**

```sql
SELECT 
  agent_type,
  m.display_name as model,
  ranking_score,
  success_rate,
  avg_latency_ms,
  total_requests,
  last_recalculated_at
FROM agent_model_rankings amr
JOIN llm_models m ON m.id = amr.model_id
WHERE agent_type = 'swap_agent'
ORDER BY ranking_score DESC;
```

---

## 🎓 Best Practices

### **DO:**
- ✅ Monitor dashboards daily
- ✅ Review budgets weekly
- ✅ Test provider health regularly
- ✅ Keep API keys rotated (30 days)
- ✅ Maintain audit trail
- ✅ Document all manual overrides
- ✅ Test disaster recovery procedures

### **DON'T:**
- ❌ Disable circuit breakers without investigation
- ❌ Set hard budget limits without baseline
- ❌ Manually edit ranking scores frequently
- ❌ Ignore budget warnings
- ❌ Skip health checks
- ❌ Deploy without testing in staging

---

## 📞 Support Contacts

### **Internal**
- **Engineering**: engineering@anvil.com
- **DevOps**: devops@anvil.com
- **On-Call**: oncall@anvil.com
- **Slack**: #llm-orchestration

### **External (Providers)**
- **Google Vertex AI**: [Support Portal](https://cloud.google.com/support)
- **DeepInfra**: support@deepinfra.com
- **AWS Bedrock**: [AWS Support](https://console.aws.amazon.com/support)

---

## 📝 Change Log

### **v1.0.0** (December 1, 2025)
- ✅ Initial release
- ✅ 3 providers (Vertex AI, DeepInfra, Bedrock)
- ✅ 9 models in carousel
- ✅ Adaptive ranking system
- ✅ Circuit breaker protection
- ✅ Admin API (23 endpoints)
- ✅ Celery background tasks (5 tasks)
- ✅ Complete telemetry

---

**Maintained by**: DevOps Team  
**Last Updated**: December 1, 2025  
**Version**: 1.0.0
