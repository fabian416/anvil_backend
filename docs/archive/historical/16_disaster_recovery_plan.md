# 🚨 Anvil Platform - Disaster Recovery & Business Continuity Plan

## Complete DR/BC Strategy

**Version:** 1.0  
**Date:** November 2025  
**Classification:** Critical - Internal Only

---

## 🎯 Executive Summary

This document outlines Anvil's disaster recovery (DR) and business continuity (BC) strategy to ensure minimal disruption in the event of system failures, data loss, or catastrophic events.

### Key Objectives

```yaml
Recovery Time Objective (RTO):
  Critical Systems: 1 hour
  Non-Critical Systems: 4 hours

Recovery Point Objective (RPO):
  Database: 15 minutes
  User Data: 1 hour
  Logs: 24 hours

Availability Target:
  Production: 99.9% uptime
  Critical Services: 99.95% uptime
```

---

## 🏗️ System Architecture - Resilience

### High Availability Setup

```
┌─────────────────────────────────────────────┐
│              Route 53 (DNS)                 │
│     Health Checks + Failover Routing        │
└──────────────┬──────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│         CloudFront (CDN + WAF)               │
│     Multi-Region Distribution                │
└──────────────┬───────────────────────────────┘
               ↓
┌──────────────────────────────────────────────┐
│     Application Load Balancer (ALB)          │
│  Multi-AZ + Health Checks + Auto-Scaling    │
└──────────────┬───────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│         ECS Fargate Tasks (Multi-AZ)            │
│  ┌──────┬──────┬──────┐  ┌──────┬──────┬──────┐│
│  │ AZ-A │ AZ-B │ AZ-C │  │ AZ-A │ AZ-B │ AZ-C ││
│  └──────┴──────┴──────┘  └──────┴──────┴──────┘│
└─────────────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────┐
│            RDS MySQL (Multi-AZ)                 │
│  Primary (AZ-A) ←→ Standby (AZ-B)              │
│  Automated Backups + Read Replicas              │
└─────────────────────────────────────────────────┘
```

---

## 💾 Backup Strategy

### Database Backups (RDS MySQL)

**Automated Backups:**
```yaml
Frequency: Continuous (Transaction Logs)
Snapshot: Daily at 3:00 AM UTC
Retention: 7 days (automated)
Manual Snapshots: 30 days
Cross-Region Copy: Enabled (us-west-2)

Backup Schedule:
  - Point-in-Time Recovery: Any point in last 7 days
  - Daily Snapshots: 3:00 AM UTC
  - Weekly Full Backup: Sunday 2:00 AM UTC
  - Monthly Archive: First Sunday, retained 1 year
```

**Backup Verification:**
```bash
#!/bin/bash
# scripts/verify_backup.sh

# Daily backup verification script
DATE=$(date +%Y-%m-%d)

# 1. Verify snapshot exists
SNAPSHOT=$(aws rds describe-db-snapshots \
  --db-instance-identifier anvil-production \
  --snapshot-type automated \
  --query "DBSnapshots[0].DBSnapshotIdentifier" \
  --output text)

if [ -z "$SNAPSHOT" ]; then
  echo "ERROR: No snapshot found for $DATE"
  send_alert "Database backup verification failed"
  exit 1
fi

# 2. Test restore to temporary instance (weekly)
if [ "$(date +%u)" -eq 7 ]; then
  aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier anvil-restore-test-$DATE \
    --db-snapshot-identifier $SNAPSHOT
  
  # Wait for restore
  aws rds wait db-instance-available \
    --db-instance-identifier anvil-restore-test-$DATE
  
  # Run smoke tests
  ./scripts/test_restored_db.sh anvil-restore-test-$DATE
  
  # Cleanup
  aws rds delete-db-instance \
    --db-instance-identifier anvil-restore-test-$DATE \
    --skip-final-snapshot
fi

echo "Backup verification passed"
```

### Application Data Backups

**S3 Backups:**
```yaml
KYC Documents:
  Location: s3://anvil-production-kyc/
  Versioning: Enabled
  Lifecycle: Never delete
  Cross-Region: Replicated to us-west-2
  Encryption: AES-256

Logs:
  Location: s3://anvil-production-logs/
  Retention: 90 days
  Lifecycle: Archive to Glacier after 30 days
  
Configuration:
  Location: s3://anvil-production-config/
  Versioning: Enabled
  Retention: All versions kept
```

**Redis Backups:**
```yaml
Strategy: RDB Snapshots
Frequency: Every 6 hours
Retention: 7 days
Storage: S3
Automated: Via ElastiCache backup feature
```

---

## 🔄 Disaster Scenarios & Recovery Procedures

### Scenario 1: Database Failure

**Symptoms:**
```
- Application cannot connect to database
- Database CPU at 100%
- Database unresponsive
```

**Immediate Actions (Auto-Failover):**
```yaml
1. RDS Multi-AZ Automatic Failover:
   Time: 1-2 minutes
   Action: AWS automatically promotes standby
   
2. Application automatically reconnects:
   Connection retry: 3 attempts with exponential backoff
   Fallback: Read replica for read-only mode

3. Monitoring:
   CloudWatch alarm triggers
   PagerDuty pages on-call engineer
   Slack notification to #alerts
```

**Manual Recovery (if auto-failover fails):**
```bash
# Step 1: Verify issue
aws rds describe-db-instances \
  --db-instance-identifier anvil-production

# Step 2: Check recent snapshots
aws rds describe-db-snapshots \
  --db-instance-identifier anvil-production \
  --max-records 5

# Step 3: Restore from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier anvil-production-restored \
  --db-snapshot-identifier <latest-snapshot-id> \
  --db-instance-class db.t3.large \
  --multi-az \
  --publicly-accessible false

# Step 4: Wait for restore
aws rds wait db-instance-available \
  --db-instance-identifier anvil-production-restored

# Step 5: Update application endpoint
# Update environment variable DATABASE_URL
# Redeploy ECS tasks

# Step 6: Verify application
curl https://api.anvil.com/health
```

**Recovery Time:** 15-30 minutes  
**Data Loss:** < 15 minutes (RPO)

---

### Scenario 2: Complete Region Failure (us-east-1)

**Symptoms:**
```
- All services in us-east-1 unavailable
- Unable to reach API
- Database unreachable
```

**Recovery Procedure:**

**Step 1: Activate DR Region (us-west-2)**
```bash
#!/bin/bash
# scripts/failover_to_dr_region.sh

echo "Initiating failover to us-west-2..."

# 1. Update Route 53 to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.anvil.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z098765432CBA",
          "DNSName": "anvil-dr-alb.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'

# 2. Restore database from latest cross-region snapshot
LATEST_SNAPSHOT=$(aws rds describe-db-snapshots \
  --region us-west-2 \
  --query "DBSnapshots[?starts_with(DBSnapshotIdentifier, 'anvil-prod')]|[0].DBSnapshotIdentifier" \
  --output text)

aws rds restore-db-instance-from-db-snapshot \
  --region us-west-2 \
  --db-instance-identifier anvil-dr-db \
  --db-snapshot-identifier $LATEST_SNAPSHOT \
  --multi-az

# 3. Scale up ECS tasks in DR region
aws ecs update-service \
  --region us-west-2 \
  --cluster anvil-dr-cluster \
  --service anvil-api-service \
  --desired-count 4

# 4. Verify services
sleep 300  # Wait for tasks to start
curl https://api.anvil.com/health

echo "Failover complete"
```

**Recovery Time:** 30-60 minutes  
**Data Loss:** 1-4 hours (cross-region replication lag)

---

### Scenario 3: Data Corruption

**Symptoms:**
```
- Inconsistent data returned by API
- Users reporting wrong balances
- Transaction records corrupted
```

**Recovery Procedure:**

**Step 1: Identify corruption scope**
```sql
-- Check recent transactions
SELECT COUNT(*), status, created_at::date
FROM transactions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status, created_at::date;

-- Check for anomalies
SELECT user_id, COUNT(*) as tx_count
FROM transactions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) > 100;  -- Suspicious activity
```

**Step 2: Point-in-Time Recovery**
```bash
# Restore to point before corruption
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier anvil-production \
  --target-db-instance-identifier anvil-pitr-restore \
  --restore-time 2025-11-17T10:30:00Z \
  --db-instance-class db.t3.large

# Compare data
# Export affected records from production
# Export same records from restore
# Identify differences
```

**Step 3: Selective data recovery**
```python
# scripts/recover_corrupted_data.py
from app.core.database import SessionLocal
from app.models import Transaction, User

# Connect to both databases
prod_db = SessionLocal()
restore_db = SessionLocal(bind=restore_engine)

# Get corrupted transaction IDs
corrupted_ids = [1234, 1235, 1236]  # Identified manually

for tx_id in corrupted_ids:
    # Get clean version from restore
    clean_tx = restore_db.query(Transaction).filter(
        Transaction.id == tx_id
    ).first()
    
    if clean_tx:
        # Update production with clean data
        prod_tx = prod_db.query(Transaction).filter(
            Transaction.id == tx_id
        ).first()
        
        prod_tx.amount = clean_tx.amount
        prod_tx.status = clean_tx.status
        # Update other fields...
        
        prod_db.commit()
        print(f"Recovered transaction {tx_id}")
```

**Recovery Time:** 1-4 hours  
**Data Loss:** Affected records only

---

### Scenario 4: Security Breach / Ransomware

**Symptoms:**
```
- Unauthorized access detected
- Files encrypted
- Unusual database activity
```

**Immediate Actions:**

**Step 1: Isolate affected systems (5 minutes)**
```bash
# Disable all API access
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn <alb-arn> \
  --attributes Key=routing.http.drop_invalid_header_fields.enabled,Value=true

# Rotate all credentials
./scripts/rotate_all_credentials.sh

# Disable all user sessions
redis-cli FLUSHDB  # Clear session store

# Update security groups to block all traffic
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --ip-permissions IpProtocol=-1
```

**Step 2: Assess damage (30 minutes)**
```bash
# Check for unauthorized changes
git log --all --since="24 hours ago"

# Check database for unauthorized modifications
./scripts/audit_database_changes.sh

# Check S3 for file modifications
aws s3api list-object-versions \
  --bucket anvil-production-data \
  --query "Versions[?LastModified>'2025-11-17']"
```

**Step 3: Recovery from clean backup**
```bash
# Restore from pre-breach backup
# Identified clean snapshot from 2 days ago

# Restore database
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier anvil-clean-restore \
  --db-snapshot-identifier rds:anvil-2025-11-15-clean

# Restore S3 data
aws s3 sync \
  s3://anvil-backup-clean/ \
  s3://anvil-production-data/ \
  --delete

# Redeploy application from known good commit
git checkout <known-good-commit>
./scripts/deploy_production.sh
```

**Step 4: Harden security**
```bash
# Enable additional monitoring
# Implement additional access controls
# Force password reset for all users
# Review and revoke API keys
```

**Recovery Time:** 4-8 hours  
**Data Loss:** Up to 48 hours (clean backup)

---

## 🧪 Disaster Recovery Testing

### Quarterly DR Test Schedule

**Q1 Test: Database Failover**
```yaml
Date: First Saturday of January
Scope: Test RDS Multi-AZ failover
Duration: 2 hours
Team: Database team + DevOps
Success Criteria:
  - Failover completes in < 5 minutes
  - Application reconnects automatically
  - No data loss
  - All tests pass
```

**Q2 Test: Application Recovery**
```yaml
Date: First Saturday of April
Scope: Restore application from backup
Duration: 3 hours
Team: Full engineering team
Success Criteria:
  - Restore completes in < 30 minutes
  - All services operational
  - API tests pass
  - Mobile app connects successfully
```

**Q3 Test: Region Failover**
```yaml
Date: First Saturday of July
Scope: Full region failover to DR site
Duration: 4 hours
Team: Full engineering team + Management
Success Criteria:
  - Failover completes in < 1 hour
  - All services operational in DR region
  - Data loss < RPO (1 hour)
  - Customer notification process works
```

**Q4 Test: Security Incident**
```yaml
Date: First Saturday of October
Scope: Simulated security breach response
Duration: 4 hours
Team: Full engineering team + Security
Success Criteria:
  - Incident response plan followed
  - Systems isolated in < 15 minutes
  - Recovery completed in < 4 hours
  - All credentials rotated
```

---

## 📋 Recovery Checklists

### Pre-Disaster Preparation Checklist

```yaml
Documentation:
  - [ ] DR plan reviewed quarterly
  - [ ] All runbooks up to date
  - [ ] Contact list current
  - [ ] Credentials documented (in vault)

Backups:
  - [ ] Automated backups running
  - [ ] Backup verification passing
  - [ ] Cross-region replication active
  - [ ] Test restores performed monthly

Infrastructure:
  - [ ] Multi-AZ deployment configured
  - [ ] Auto-scaling configured
  - [ ] Health checks enabled
  - [ ] Monitoring alerts active

Team:
  - [ ] On-call rotation staffed
  - [ ] Team trained on procedures
  - [ ] Communication channels tested
  - [ ] DR drills conducted
```

### During-Disaster Response Checklist

```yaml
Immediate (0-5 minutes):
  - [ ] Acknowledge incident in PagerDuty
  - [ ] Notify team in #incidents Slack channel
  - [ ] Assess severity (P0, P1, P2, P3)
  - [ ] Activate incident commander

Assessment (5-15 minutes):
  - [ ] Identify affected systems
  - [ ] Determine root cause (if obvious)
  - [ ] Estimate impact (users, data, revenue)
  - [ ] Determine appropriate recovery procedure

Recovery (15 minutes - 4 hours):
  - [ ] Execute recovery procedure
  - [ ] Monitor progress
  - [ ] Communicate status updates (every 30 min)
  - [ ] Document actions taken

Verification (After recovery):
  - [ ] Run smoke tests
  - [ ] Verify data integrity
  - [ ] Monitor for issues
  - [ ] Notify customers (if needed)
```

### Post-Disaster Checklist

```yaml
Immediate (Day 1):
  - [ ] Verify all systems operational
  - [ ] Document timeline of events
  - [ ] Collect logs and metrics
  - [ ] Begin root cause analysis

Week 1:
  - [ ] Complete post-mortem report
  - [ ] Identify contributing factors
  - [ ] List lessons learned
  - [ ] Create action items

Month 1:
  - [ ] Implement preventive measures
  - [ ] Update DR procedures
  - [ ] Train team on learnings
  - [ ] Update monitoring/alerts
```

---

## 📞 Emergency Contacts

### Internal Contacts

```yaml
Incident Commander:
  Primary: CTO - +1-XXX-XXX-XXXX
  Backup: VP Engineering - +1-XXX-XXX-XXXX

Database Team:
  Lead: Database Admin - +1-XXX-XXX-XXXX
  Backup: Senior DevOps - +1-XXX-XXX-XXXX

Security Team:
  Lead: Security Engineer - +1-XXX-XXX-XXXX
  Backup: CTO - +1-XXX-XXX-XXXX

Communications:
  Internal: Slack #incidents
  External: status.anvil.com
  Email: incidents@anvil.com
```

### External Contacts

```yaml
AWS Support:
  Enterprise Support: 1-800-XXX-XXXX
  TAM: John Smith - john.smith@amazon.com
  Severity 1 Cases: AWS Console

Vendors:
  Privy: support@privy.io
  Stripe: https://support.stripe.com/
  1inch: support@1inch.io
  Sentry: support@sentry.io

Legal:
  Law Firm: XYZ Legal - +1-XXX-XXX-XXXX
  Attorney: Jane Doe - jane@xyzlegal.com
```

---

## 📊 Recovery Metrics & SLAs

### Service Level Objectives

```yaml
Database:
  Availability: 99.95%
  RTO: 1 hour
  RPO: 15 minutes
  Backup Success Rate: 100%

API:
  Availability: 99.9%
  RTO: 30 minutes
  RPO: 1 hour (cached data loss acceptable)

Mobile App:
  Can operate in offline mode
  RTO: N/A (client-side)
  Data sync after recovery: < 5 minutes

Admin Portal:
  Availability: 99.5%
  RTO: 2 hours
  RPO: 1 hour
```

### Monthly DR Metrics

```yaml
Track and Report:
  - Backup success rate: 100%
  - Backup restore tests: >= 4 per month
  - Mean time to detect (MTTD): < 5 minutes
  - Mean time to recovery (MTTR): < 1 hour
  - DR drill completion: >= 1 per quarter
  - Number of incidents: N
  - Data loss events: 0
```

---

## 💰 Cost Analysis

### DR Infrastructure Costs

```yaml
Multi-AZ RDS:
  Additional Cost: ~2x single AZ
  Monthly: $500

Cross-Region Replication:
  Data Transfer: $50/month
  Snapshot Storage: $100/month

DR Region (Standby):
  Minimal ECS tasks: $200/month
  RDS snapshot storage: $100/month

Total DR Cost: ~$950/month
Insurance Value: Priceless
```

---

## ✅ Annual Review Checklist

```yaml
January:
  - [ ] Review and update DR plan
  - [ ] Validate all contact information
  - [ ] Review DR costs and optimize
  - [ ] Schedule quarterly DR tests

Quarterly:
  - [ ] Conduct DR test
  - [ ] Review test results
  - [ ] Update procedures based on findings
  - [ ] Train team on any changes

After Every Incident:
  - [ ] Update DR plan with lessons learned
  - [ ] Implement preventive measures
  - [ ] Communicate changes to team
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Next Review:** Quarterly  
**Owner:** DevOps Lead  
**Approved By:** CTO

**Critical Document - Review and Practice Regularly**
