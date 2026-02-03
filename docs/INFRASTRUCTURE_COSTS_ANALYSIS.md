# Infrastructure Cost Analysis - Anvil Backend

## Executive Summary

This document details the Digital Ocean infrastructure for 3 environments (Development, Staging, Production) without Kubernetes, optimized for a DeFi/fintech application with 28 Docker services.

**Total Monthly Cost:** $209.20/month
- Development: $48/month (droplet only, local database)
- Staging: $63/month (droplet + managed database)
- Production: $98.20/month (droplet + backups + managed database)

---

## 🛠️ Development Environment

### Current Configuration

**Droplet: `anvil-dev`**
- **Plan:** Basic - Shared CPU (Regular)
- **Specs:** 4 vCPUs / 8 GB RAM / 160 GB SSD
- **Region:** SFO2 (San Francisco Datacenter 2)
- **Cost:** $48/month ($0.071/hour)

**Database: Local (Docker Container)**
- **Engine:** PostgreSQL 18 (containerized)
- **Plan:** N/A - Runs inside droplet
- **Storage:** Uses droplet disk space
- **Cost:** $0 (included in droplet)
- **Features:**
  - ❌ Managed backups: Manual only
  - ❌ High Availability: No
  - ❌ Automatic failover: No
  - ✅ Fast local development
  - ✅ No network latency

**Total Development:** $48/month

### Justification

**✅ Correct decision:**
- **Local DB for dev:** Perfect for development, no need for managed service overhead
- **Shared CPU appropriate:** Development doesn't need consistent 24/7 performance
- **8 GB RAM sufficient:** 28 services can run with throttling, no real users
- **No managed DB cost:** Saves $15/month, adequate for dev environment
- **No backups needed:** Dev data is disposable and reproducible

**⚠️ Future consideration:**
- If team grows > 5 developers, consider managed DB for consistency
- Cost impact: +$15/month for 1GB managed PostgreSQL

**Recommendation:** Keep current configuration ✅

---

## 🧪 Staging Environment

### Current Configuration

**Droplet: `anvil-staging`**
- **Plan:** Basic - Shared CPU (Regular)
- **Specs:** 4 vCPUs / 8 GB RAM / 160 GB SSD
- **Region:** SFO2 (San Francisco Datacenter 2)
- **Cost:** $48/month ($0.071/hour)

**Database: `dbaas-staging-postgres`**
- **Engine:** PostgreSQL 18
- **Plan:** Basic - Shared CPU (Managed)
- **Specs:** 1 vCPU / 1 GB RAM / 10 GiB SSD
- **Connection Limit:** 22 connections
- **Cost:** $15/month
- **Features:**
  - ❌ Autoscaling: Not enabled
  - ❌ High Availability: No (Primary only)
  - ❌ Daily Backups: Not configured (not critical for staging)
  - ✅ SSL/TLS: Included
  - ✅ Managed service: DO handles maintenance

**Total Staging:** $63/month

### Justification

**✅ Correct decision:**
- **First managed DB:** Staging is where you test production-like infrastructure
- **Shared CPU appropriate:** Staging is used intermittently for QA/testing
- **8 GB RAM adequate:** Sufficient to simulate limited production loads
- **DB Basic sufficient:** Staging doesn't receive real user traffic
- **No autoscaling needed:** Autoscaling testing can be simulated manually
- **No backups needed:** Staging data is ephemeral, can be recreated from prod snapshots

**Recommendation:** Keep current configuration ✅

**⚠️ Future consideration:**
- When staging becomes critical for continuous QA, add daily backups (+$2-5/month)

---

## 🚀 Production Environment (CURRENT SETUP)

### Current Configuration

**Droplet: `anvil-production`**
- **Plan:** Basic - Premium Intel
- **Specs:** 4 Intel vCPUs / 8 GB RAM / 240 GB NVMe SSD
- **Region:** SFO2 (San Francisco Datacenter 2)
- **Cost:** $64/month ($0.095/hour)
- **Transfer:** 6 TB/month included

**Droplet Backups:**
- **Type:** Daily automated backups
- **Retention:** 7 days
- **Cost:** $19.20/month (30% of droplet cost)
- **Recovery:** Point-in-time restore up to 7 days back

**Database: `dbaas-prod-postgres`**
- **Engine:** PostgreSQL 18
- **Plan:** Basic - Shared CPU (Managed)
- **Specs:** 1 vCPU / 1 GB RAM / 10 GiB SSD
- **Connection Limit:** 22 connections
- **Cost:** $15/month
- **Features:**
  - ❌ Autoscaling: Not enabled (fixed 10 GiB)
  - ❌ High Availability: No (Primary only)
  - ✅ Daily Backups: Included in managed service
  - ✅ SSL/TLS: Included
  - ✅ Point-in-time recovery: Available
  - ✅ Automated maintenance: Included

**Total Production:** $98.20/month ($64 droplet + $19.20 backups + $15 DB)

### Justification

**✅ Current setup rationale:**
- **Premium Intel CPU:** Better single-thread performance for transaction processing
- **8 GB RAM adequate:** Sufficient for 28 services with moderate load (< 50 concurrent users)
- **240 GB NVMe:** Fast storage for logs, Redis, Celery results
- **Daily backups CRITICAL:** Protects against data loss, human error, ransomware
- **7-day retention:** Allows recovery from issues discovered days later
- **Managed DB:** DO handles patching, updates, monitoring

**⚠️ Known limitations (acceptable for MVP):**
- **DB Connection limit (22):** Low for production
  - Current usage: ~10-15 connections (FastAPI + Celery workers)
  - Risk: May hit limit with > 30 concurrent users
- **DB storage (10 GiB):** Will grow over time
  - No autoscaling configured
  - Need manual monitoring
- **No HA:** Single point of failure
  - Downtime if DB crashes: ~15-30 minutes for restore
  - Acceptable for MVP, not for scale

### Critical Production Decisions

#### 1️⃣ Why NOT 16GB RAM / 8 vCPUs?

**Digital Ocean requires special request for droplets > 8GB RAM**
- Approval process takes time
- Current 8GB configuration available immediately
- Decision: Start with 8GB, request upgrade when needed

**Trigger for RAM upgrade (8GB → 16GB):**
```
Current: $64/month (4 vCPU / 8GB)
Upgrade: Requires approval from Digital Ocean

Upgrade when:
- [ ] RAM usage consistently > 75%
- [ ] > 50 concurrent users
- [ ] OOM (Out of Memory) errors in logs
- [ ] Celery workers getting killed
- [ ] Redis evicting keys frequently

Note: Must request approval from DO support for larger droplets
```

#### 2️⃣ Why Daily Backups Only on Production?

**Cost-benefit analysis:**
```
Development: No backups needed
- Data is disposable
- Can rebuild from migrations
- Cost saved: $14.40/month (30% of $48)

Staging: No backups needed  
- Test data, not critical
- Can restore from prod snapshots
- Cost saved: $14.40/month

Production: Backups MANDATORY
- Real user data
- Financial transactions
- Regulatory compliance
- Cost: $19.20/month (30% of $64)
```

**Production backup strategy:**
- **Droplet backups:** 7-day retention for OS, configs, app code
- **DB backups:** Built into managed service (point-in-time recovery)
- **Combined coverage:** Full system restore capability

#### 3️⃣ Known Limitations

**Current DB: 1GB RAM / 10 GiB storage / 22 connections - $15/month**

**Connection limit:**
```
Current connections:
- FastAPI: 5 connections (connection pool)
- Celery workers (11): 11 connections (1 each)
- MCPs: Use FastAPI as proxy (no direct DB)
- TX confirmation: 1 connection
Total actual: ~17 connections (under 22 limit)

Status: Adequate for MVP
```

**Storage: 10 GiB**
```
Expected to be sufficient for first 6+ months
Monitor if experiencing rapid growth
```

**🚨 Main Bottleneck: Droplet RAM (8GB for 28 services)**

The most likely upgrade needed is **droplet RAM**, not database:
```
Current: 8GB RAM shared by:
- FastAPI (1 instance)
- 11 Celery workers
- 11 MCP servers
- Redis
- Caddy
- Flower
- TX confirmation service

Risk: RAM exhaustion before DB limits
```

**Upgrade trigger:**
- RAM usage > 75% consistently
- OOM (Out of Memory) errors
- Services crashing or restarting
- Slow response times

**Upgrade action:**
- Request Digital Ocean approval for 16GB droplet
- Note: Requires special approval, plan 1-2 weeks ahead
```
Check Digital Ocean for HA pricing:
- Adds standby nodes for automatic failover
- Uptime: 99.95% SLA
- Failover: ~30 seconds
- Required for: > 200 users, > $50k TVL
```

---

## 📊 Cost Comparison

### Current Actual Setup
```
Development:  $48/month   (Droplet only, local DB)
Staging:      $63/month   (Droplet $48 + Managed DB $15)
Production:   $98.20/month (Droplet $64 + Backups $19.20 + DB $15)
─────────────────────────
Total:        $209.20/month
```

### Known Upgrade Triggers

**Primary Concern: Droplet RAM (most likely bottleneck)**
```
Monitor: RAM usage daily
Current: 8GB for 28 services
Alert: When RAM consistently > 75%
Action: Request DO approval for 16GB droplet
Impact: Biggest performance improvement
Note: Requires special approval, plan ahead
```

**Secondary: Database (if needed)**
```
Monitor: Storage usage and connection count
Current: 10 GiB storage, 22 connections
Alert: Storage > 7 GiB OR connection errors
Action: Check Digital Ocean for larger DB plan
Note: Less urgent, current size adequate for MVP
```

**High Availability (when scale demands it)**
```
Monitor: Uptime percentage and user count
Current: No HA, acceptable downtime for MVP
Alert: When users > 100 OR critical downtime events
Action: Add HA to database (check DO pricing)
Benefit: 99.95% uptime SLA, automatic failover
```

---

## 🎯 Final Recommendations

### ✅ Current Setup (Approved & Deployed)

**Development Environment:**
```
✅ Droplet: 4vCPU / 8GB RAM - $48/month
✅ Database: Local PostgreSQL container - $0
✅ No backups: Acceptable for dev
Total: $48/month
```

**Staging Environment:**
```
✅ Droplet: 4vCPU / 8GB RAM - $48/month
✅ Database: Managed PostgreSQL 1GB - $15/month
✅ No backups: Acceptable for staging
Total: $63/month
```

**Production Environment:**
```
✅ Droplet: 4 Intel vCPU / 8GB RAM / 240GB NVMe - $64/month
✅ Daily Backups: 7-day retention - $19.20/month
✅ Database: Managed PostgreSQL 1GB - $15/month
Total: $98.20/month
```

**Grand Total: $209.20/month**

### 🚨 Monitoring Triggers for Upgrades

**Priority 1: Droplet RAM (Most Likely Bottleneck)**
```
Monitor for:
- [ ] RAM usage consistently > 75%
- [ ] OOM killer events in dmesg
- [ ] Celery workers crashing or restarting
- [ ] Redis memory eviction warnings
- [ ] Slow response times under load

Action: Request DO approval for 16GB droplet upgrade
Impact: Biggest performance improvement for the money
Note: Requires special approval, plan 1-2 weeks ahead
```

**Priority 2: Database (Monitor but less urgent)**
```
Monitor for:
- [ ] Storage usage > 7 GiB (70% of capacity)
- [ ] Connection errors in logs
- [ ] Slow queries due to memory

Action: Check Digital Ocean pricing for larger DB plan
Note: Current 10 GiB adequate for 6+ months typically
```

**Priority 3: High Availability (When business critical)**
```
Trigger when:
- [ ] Daily active users > 100
- [ ] TVL (Total Value Locked) > $50k
- [ ] Monthly revenue > $1,000
- [ ] Experienced production outage with financial impact
- [ ] Compliance/regulation requires 99.95% uptime

Action: Check Digital Ocean pricing for HA database
Goal: 99.95% uptime SLA with automatic failover
```

### 📈 Scaling Roadmap

**Month 1-3: Current Setup ($209.20/month)**
```
Users: 0-50
Load: Light to moderate
Focus: Product-market fit
Monitor: RAM usage primarily
Risk: Acceptable downtime for MVP
```

**Month 4-6: Likely Droplet Upgrade Needed**
```
Users: 50-100  
Load: Moderate to heavy
Primary bottleneck: 8GB RAM for 28 services
Action: Request 16GB droplet approval from DO
Note: Most impactful upgrade
```

**Month 7-12: Consider HA**
```
Users: 100-200
Load: Heavy
Monitor: RAM consistently > 75%
Action: Request DO approval for 16GB droplet
Note: Requires special approval process
```

**Year 2: Enterprise Ready**
```
Users: 200-500+
Load: Very heavy
Consider:
- HA database for automatic failover
- Autoscaling storage
- General Purpose droplets for dedicated CPU
Goal: 99.95% uptime SLA, enterprise-grade reliability
```

---

## 🔐 DeFi/Fintech Considerations

### Security
- ✅ **SSL/TLS:** Included on all DBs
- ✅ **VPC Network:** Service isolation
- ✅ **Daily backups:** Included (PITR available on upgrade)
- ⚠️ **Secrets Management:** Use DigitalOcean Secrets or Vault ($0 extra)

### Compliance
- ⚠️ **Data Residency:** All in SFO2 (California, USA)
- ⚠️ **GDPR:** If you have EU users, need EU region
- ⚠️ **SOC 2:** DigitalOcean is SOC 2 Type II certified
- ⚠️ **Audit Logs:** Enable DigitalOcean Monitoring (free)

### Monitoring (Included Free)
```bash
# Enable in all environments:
- Droplet Metrics (CPU, RAM, Disk, Network)
- Database Metrics (Connections, Query time, Cache hit)
- Alerts (> 80% CPU, > 90% RAM, > 85% Disk)
- Uptime Monitoring (Health checks every 1 min)
```

---

## 💰 ROI Analysis

### Cost vs Downtime

### Cost vs Downtime

**Scenario: Production without HA suffers 2-hour outage**
```
Downtime cost:
- 100 users * 2 hours = 200 user-hours lost
- Average $50 GMV/user = $10,000 GMV not processed
- 1% fee = $100 revenue lost
- Reputation: priceless

HA Cost:
- Check Digital Ocean pricing for HA database
- Benefit: Automatic failover, ~30 second downtime vs hours
- ROI: Pays for itself if prevents even 1 major outage
```

**Recommendation:** Consider HA when you have > 20 active users paying money

---

## 📋 Implementation Checklist

### Development ✅
- [x] Droplet created: anvil-dev (8GB/4vCPU)
- [x] Database: Local PostgreSQL 18 container
- [x] VPC configured: default-sfo2
- [x] Docker Compose deployed (28 services)
- [x] No backups (dev data disposable)

### Staging ✅
- [x] Droplet created: anvil-staging (8GB/4vCPU)
- [x] Database created: dbaas-staging-postgres (1GB managed)
- [x] VPC configured: default-sfo2
- [x] Docker Compose deployed
- [x] SSL/TLS: Managed service handles

### Production ✅
- [x] Droplet created: anvil-production (8GB/4vCPU Intel Premium)
- [x] Daily Backups enabled: 7-day retention ($19.20/month)
- [x] Database created: dbaas-prod-postgres (1GB managed)
- [x] VPC configured: default-sfo2
- [x] SSL/TLS: Caddy with Let's Encrypt + DB managed SSL

### Production TODOs Before Launch
```bash
# 1. Enable monitoring alerts
- Set CPU > 80% alert
- Set RAM > 85% alert  
- Set Disk > 80% alert
- Set DB connections > 18 (out of 22) alert

# 2. Configure health checks
- FastAPI /health endpoint
- Uptime monitoring (1 min intervals)
- Alert on 3 consecutive failures

# 3. Backup verification
- Test droplet restore procedure
- Test DB point-in-time recovery
- Document restore process

# 4. Connection pool tuning
- Monitor actual connection usage
- Tune FastAPI connection pool
- Document max connections per service

# 5. Storage monitoring
- Track DB storage growth weekly
- Set alert at 7 GiB (70% of 10 GiB)
- Plan upgrade timeline
```

---

## 🔄 Next Steps

1. **Current setup deployed:** $209.20/month ✅
   - Development running with local DB
   - Staging running with managed DB
   - Production running with backups + managed DB

2. **Immediate actions (pre-launch):**
   - [ ] Configure monitoring alerts (CPU, RAM, Disk, DB connections)
   - [ ] Test backup restore procedures
   - [ ] Document incident response playbook
   - [ ] Set up log aggregation (optional but recommended)

3. **Week 1-2 monitoring:**
   - Track actual resource usage vs allocated
   - Monitor DB connection patterns
   - Watch storage growth rate
   - Identify bottlenecks early

4. **Month 1 review:**
   - Evaluate if 1GB DB is sufficient
   - Check if 22 connection limit is being hit
   - Assess RAM usage patterns
   - Plan upgrades if needed

5. **Month 3-4 evaluation:**
   - If RAM > 75%: Request droplet upgrade approval (primary concern)
   - If DB storage > 7 GiB: Check DB upgrade pricing (secondary)
   - If uptime critical: Consider HA

6. **Ongoing optimization:**
   - Review costs monthly
   - Right-size resources based on actual usage
   - Scale proactively before hitting limits
   - Keep upgrade path clear

---

## ⚠️ Critical Risks & Mitigations

### Risk 1: RAM Exhaustion (Primary Risk)
**Problem:** 8GB shared by 28 services
```
Current mitigation:
✅ Services configured with memory limits
✅ Droplet backups allow quick recovery
✅ 8GB adequate for MVP load (< 50 users)

Monitor:
- Watch RAM usage: free -h
- Check for OOM events: dmesg | grep -i oom
- Alert at > 75% RAM consistently
- Upgrade requires DO approval (plan ahead)
```

### Risk 2: Database Limits (Secondary Risk)
**Problem:** 22 connection limit, 10 GiB storage
```
Current mitigation:
✅ MCPs proxy through FastAPI (no direct DB connections)
✅ Connection pooling configured
✅ Actual usage ~17 connections (under limit)
✅ 10 GiB adequate for 6+ months typically

Monitor:
- Watch pg_stat_activity for connection count
- Alert at > 18 connections (80% of limit)
- Check storage weekly: SELECT pg_size_pretty(pg_database_size('anvil'));
- Alert at > 7 GiB (70% threshold)
```

### Risk 3: No High Availability
```
Current mitigation:
✅ 8GB adequate for MVP load (< 50 users)
✅ Services configured with memory limits
✅ Droplet backups allow quick recovery

Monitor:
- Watch RAM usage: free -h
- Check for OOM events: dmesg | grep -i oom
- Alert at > 75% RAM consistently
- Upgrade requires DO approval (plan ahead)
```

### Risk 4: No High Availability
**Problem:** Single point of failure in production
```
Current mitigation:
✅ Daily droplet backups (RTO: ~15 min)
✅ Managed DB has built-in backups (RTO: ~30 min)
✅ Acceptable for MVP phase

Monitor:
- Track uptime percentage
- Document each outage
- When uptime < 99.5% or > 100 users: Add HA
```

---

**Document created:** 2026-02-02  
**Next review:** Post-deployment Production (30 days)  
**Owner:** Anvil DevOps Team
