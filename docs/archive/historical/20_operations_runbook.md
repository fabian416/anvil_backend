# 📖 Anvil Platform - Operations Runbook

## Common Operations & Troubleshooting Guide

**Version:** 1.0  
**Date:** November 2025  
**Audience:** DevOps, On-Call Engineers

---

## 🎯 Purpose

This runbook provides step-by-step procedures for common operational tasks and troubleshooting scenarios. Use this as your first reference when issues arise.

---

## 🚨 Emergency Procedures

### Critical Incident Response

**When to Declare Critical Incident:**
- API down for >2 minutes
- Database unavailable
- >10% error rate
- Security breach detected
- Data loss detected

**Immediate Actions:**
```bash
# 1. Acknowledge in PagerDuty
# 2. Join incident channel
# 3. Start incident timeline

# Check service health
curl https://api.anvil.com/health

# Check ECS services
aws ecs describe-services \
  --cluster anvil-production \
  --services anvil-api

# Check database
mysql -h prod-db.anvil.com -u readonly -p -e "SELECT 1"

# Check recent deployments
aws ecs list-tasks --cluster anvil-production
```

---

## 🔍 Common Issues & Solutions

### Issue 1: API Returns 500 Errors

**Symptoms:**
- Users cannot access app
- 5xx errors in logs
- CloudWatch alarms firing

**Diagnosis:**
```bash
# Check error logs
aws logs tail /aws/ecs/anvil-api --follow --filter-pattern "ERROR"

# Check ECS task health
aws ecs describe-tasks \
  --cluster anvil-production \
  --tasks $(aws ecs list-tasks --cluster anvil-production --service-name anvil-api --query 'taskArns[0]' --output text)

# Check database connections
mysql -h prod-db.anvil.com -u admin -p -e "SHOW PROCESSLIST;"
```

**Solutions:**

**Solution 1: Restart unhealthy tasks**
```bash
# Force new deployment (rolling restart)
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --force-new-deployment

# Monitor deployment
aws ecs wait services-stable \
  --cluster anvil-production \
  --services anvil-api
```

**Solution 2: Scale up if resource exhaustion**
```bash
# Increase task count
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --desired-count 8

# Check if helped
curl https://api.anvil.com/health
```

**Solution 3: Rollback if recent deployment**
```bash
# Get previous task definition
CURRENT_VERSION=$(aws ecs describe-services \
  --cluster anvil-production \
  --services anvil-api \
  --query 'services[0].taskDefinition' \
  --output text | grep -oP '\d+$')

PREVIOUS_VERSION=$((CURRENT_VERSION - 1))

# Rollback
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --task-definition anvil-api:$PREVIOUS_VERSION
```

---

### Issue 2: Database Connection Errors

**Symptoms:**
- "Unable to connect to database"
- Transactions failing
- Slow queries

**Diagnosis:**
```bash
# Check RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier anvil-production

# Check connections
mysql -h prod-db.anvil.com -u admin -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Check slow queries
mysql -h prod-db.anvil.com -u admin -p -e "
SELECT * FROM information_schema.processlist 
WHERE command != 'Sleep' 
AND time > 5 
ORDER BY time DESC;
"
```

**Solutions:**

**Solution 1: Kill long-running queries**
```sql
-- Identify problematic query
SHOW FULL PROCESSLIST;

-- Kill specific query
KILL QUERY <process_id>;

-- Or kill connection
KILL <process_id>;
```

**Solution 2: Increase connection pool**
```python
# Update environment variable
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --task-definition <new-task-def-with-larger-pool>
```

**Solution 3: Force RDS failover (if Multi-AZ)**
```bash
# Only if primary is unresponsive
aws rds reboot-db-instance \
  --db-instance-identifier anvil-production \
  --force-failover
```

---

### Issue 3: Redis Cache Issues

**Symptoms:**
- Slow API responses
- Cache misses
- Redis timeouts

**Diagnosis:**
```bash
# Connect to Redis
redis-cli -h prod-redis.anvil.com

# Check memory usage
INFO memory

# Check hit rate
INFO stats

# Check slow log
SLOWLOG GET 10
```

**Solutions:**

**Solution 1: Clear cache if corrupted**
```bash
# Clear all cache (careful!)
redis-cli -h prod-redis.anvil.com FLUSHALL

# Or clear specific patterns
redis-cli -h prod-redis.anvil.com --scan --pattern "user:*" | xargs redis-cli DEL
```

**Solution 2: Restart Redis**
```bash
aws elasticache reboot-cache-cluster \
  --cache-cluster-id anvil-production-redis
```

---

### Issue 4: High Latency

**Symptoms:**
- API responses slow (>1s)
- User complaints
- CloudWatch P95 latency high

**Diagnosis:**
```bash
# Check API latency by endpoint
aws cloudwatch get-metric-statistics \
  --namespace Anvil/API \
  --metric-name ResponseTime \
  --dimensions Name=Endpoint,Value=/user/wallet \
  --start-time 2025-11-17T00:00:00Z \
  --end-time 2025-11-17T23:59:59Z \
  --period 300 \
  --statistics Average,p95

# Check database query times
# In application logs, look for slow queries

# Check external API latency
aws cloudwatch get-metric-statistics \
  --namespace Anvil/ExternalAPIs \
  --metric-name ResponseTime
```

**Solutions:**

**Solution 1: Scale up compute**
```bash
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --desired-count 8
```

**Solution 2: Add database indexes**
```sql
-- Analyze slow queries
SELECT * FROM mysql.slow_log 
ORDER BY query_time DESC 
LIMIT 10;

-- Add missing indexes (example)
CREATE INDEX idx_transactions_user_created 
ON transactions(user_id, created_at DESC);
```

**Solution 3: Increase cache TTL**
```python
# Update cache configuration
CACHE_TTL = {
    "user_balance": 60,  # Increase from 30
    "token_prices": 30,  # Increase from 10
}
```

---

## 🔧 Common Operational Tasks

### Deploy New Version

```bash
#!/bin/bash
# scripts/deploy_production.sh

# 1. Build and push Docker image
docker build -t anvil-api:latest .
docker tag anvil-api:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/anvil-api:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/anvil-api:latest

# 2. Register new task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Update service
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --task-definition anvil-api:latest

# 4. Wait for deployment
aws ecs wait services-stable \
  --cluster anvil-production \
  --services anvil-api

# 5. Verify health
curl https://api.anvil.com/health

echo "Deployment complete!"
```

---

### Scale Services

**Scale Up:**
```bash
# Increase task count
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --desired-count 8

# Verify
aws ecs describe-services \
  --cluster anvil-production \
  --services anvil-api \
  --query 'services[0].{desired:desiredCount,running:runningCount}'
```

**Scale Down:**
```bash
# Decrease task count
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --desired-count 4
```

---

### Database Maintenance

**Run Database Backup:**
```bash
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier anvil-production \
  --db-snapshot-identifier anvil-manual-$(date +%Y%m%d-%H%M%S)

# Verify snapshot
aws rds describe-db-snapshots \
  --db-snapshot-identifier anvil-manual-20251117-120000
```

**Optimize Database:**
```sql
-- Run on read replica during low traffic
ANALYZE TABLE users;
ANALYZE TABLE transactions;
ANALYZE TABLE earn_positions;

-- Rebuild indexes
OPTIMIZE TABLE users;
OPTIMIZE TABLE transactions;
```

---

### Update Environment Variables

```bash
# 1. Get current task definition
aws ecs describe-task-definition \
  --task-definition anvil-api \
  --query 'taskDefinition' > task-def.json

# 2. Edit task-def.json to update environment variables

# 3. Register new version
aws ecs register-task-definition \
  --cli-input-json file://task-def.json

# 4. Update service
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --task-definition anvil-api:<new-version>
```

---

### Rotate Secrets

**Rotate Database Password:**
```bash
#!/bin/bash
# scripts/rotate_db_password.sh

# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update RDS password
aws rds modify-db-instance \
  --db-instance-identifier anvil-production \
  --master-user-password "$NEW_PASSWORD" \
  --apply-immediately

# 3. Update in Secrets Manager
aws secretsmanager update-secret \
  --secret-id anvil/database/password \
  --secret-string "$NEW_PASSWORD"

# 4. Force service redeployment to pick up new secret
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api \
  --force-new-deployment

echo "Database password rotated successfully"
```

---

## 📊 Monitoring & Alerts

### Check System Health

```bash
#!/bin/bash
# scripts/health_check.sh

echo "=== Checking API Health ==="
curl -s https://api.anvil.com/health | jq

echo -e "\n=== Checking ECS Services ==="
aws ecs describe-services \
  --cluster anvil-production \
  --services anvil-api \
  --query 'services[0].{name:serviceName,desired:desiredCount,running:runningCount,status:status}'

echo -e "\n=== Checking Database ==="
aws rds describe-db-instances \
  --db-instance-identifier anvil-production \
  --query 'DBInstances[0].{status:DBInstanceStatus,endpoint:Endpoint.Address}'

echo -e "\n=== Checking Redis ==="
aws elasticache describe-cache-clusters \
  --cache-cluster-id anvil-production-redis \
  --query 'CacheClusters[0].{status:CacheClusterStatus,endpoint:CacheNodes[0].Endpoint.Address}'

echo -e "\n=== Recent Errors ==="
aws logs tail /aws/ecs/anvil-api \
  --since 5m \
  --filter-pattern "ERROR" \
  --format short
```

---

### Review Metrics

```bash
# API request rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name RequestCount \
  --dimensions Name=LoadBalancer,Value=app/anvil-alb/xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# Error rate
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/anvil-alb/xxx \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## 🔐 Security Operations

### Respond to Security Alert

**Suspicious Activity Detected:**
```bash
# 1. Review security logs
aws logs filter-log-events \
  --log-group-name /aws/ecs/anvil-api \
  --filter-pattern "suspicious OR unauthorized" \
  --start-time $(($(date +%s) - 3600))000

# 2. Check recent logins
mysql -h prod-db.anvil.com -u admin -p -e "
SELECT * FROM audit_logs 
WHERE action = 'login' 
AND created_at > NOW() - INTERVAL 1 HOUR 
ORDER BY created_at DESC;
"

# 3. If compromised, block IP
aws wafv2 create-ip-set \
  --name BlockedIPs \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses <suspicious-ip>/32
```

---

### Investigate Failed Login Attempts

```sql
-- Check failed logins
SELECT 
    actor_user_id,
    ip_address,
    COUNT(*) as attempts,
    MAX(created_at) as last_attempt
FROM audit_logs
WHERE action = 'login_failed'
AND created_at > NOW() - INTERVAL 1 HOUR
GROUP BY actor_user_id, ip_address
HAVING attempts > 5
ORDER BY attempts DESC;

-- Check successful logins after failures
SELECT * FROM audit_logs
WHERE action = 'login_success'
AND actor_user_id IN (
    SELECT actor_user_id FROM audit_logs
    WHERE action = 'login_failed'
    AND created_at > NOW() - INTERVAL 1 HOUR
    GROUP BY actor_user_id
    HAVING COUNT(*) > 5
);
```

---

## 📞 Escalation

### When to Escalate

**To Team Lead:**
- Issue not resolved in 30 minutes
- Affecting >10% of users
- Security concern
- Need additional access

**To CTO:**
- Major outage (>1 hour)
- Data loss
- Security breach
- Legal/compliance issue

**To All Hands:**
- Complete service failure
- Data breach confirmed
- Major customer impact

---

## 📚 Reference Links

```yaml
Monitoring:
  CloudWatch: https://console.aws.amazon.com/cloudwatch
  Sentry: https://sentry.io/anvil
  Grafana: https://grafana.anvil.com

Logs:
  Application Logs: /aws/ecs/anvil-api
  Database Logs: /aws/rds/anvil-production
  Access Logs: /aws/alb/anvil-production

Documentation:
  Architecture: See technical_architecture.md
  Deployment: See deployment_devops.md
  Disaster Recovery: See disaster_recovery_plan.md

Communication:
  Slack: #incidents, #engineering
  PagerDuty: https://anvil.pagerduty.com
  Status Page: https://status.anvil.com
```

---

## ✅ Post-Incident Checklist

After resolving an incident:

```yaml
Immediate (Within 1 hour):
  - [ ] Verify service fully restored
  - [ ] Confirm no data loss
  - [ ] Update status page
  - [ ] Notify affected users
  - [ ] Document timeline

Within 24 hours:
  - [ ] Write incident summary
  - [ ] Identify root cause
  - [ ] List contributing factors
  - [ ] Propose preventive measures

Within 1 week:
  - [ ] Conduct post-mortem meeting
  - [ ] Create action items
  - [ ] Update runbooks
  - [ ] Implement quick fixes

Within 1 month:
  - [ ] Complete all action items
  - [ ] Update monitoring/alerts
  - [ ] Train team on learnings
  - [ ] Review similar incidents
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** DevOps Team  
**On-Call Reference:** Keep accessible 24/7
