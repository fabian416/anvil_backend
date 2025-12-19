# 💰 Anvil Platform - Cost Optimization Guide

## AWS & Infrastructure Cost Management

**Version:** 1.0  
**Date:** November 2025  
**Goal:** Minimize costs while maintaining performance

---

## 📊 Current Cost Breakdown

### Monthly Costs (Estimated)

```yaml
AWS Infrastructure (~$900/month):
  Compute (ECS Fargate):
    API Servers (4 tasks): $200
    Workers (3 tasks): $150
    Subtotal: $350
  
  Database (RDS MySQL):
    db.t3.large Multi-AZ: $250
    Backups & Storage: $50
    Subtotal: $300
  
  Cache (ElastiCache Redis):
    cache.t3.medium: $100
  
  Storage (S3):
    KYC Documents: $10
    Logs & Backups: $10
    Subtotal: $20
  
  Network:
    Data Transfer: $50
    CloudFront CDN: $50
    Subtotal: $100
  
  Monitoring:
    CloudWatch: $30

Third-Party Services (~$930/month):
  Privy: $500
  Stripe: 2.9% + $0.30 per transaction
  Alchemy RPC: $199
  Vertex AI: $100 (estimated)
  SendGrid: $80
  Twilio: $50 (estimated)
  Firebase: Free tier

Total Monthly: ~$1,830 + transaction fees
```

---

## 🎯 Cost Optimization Strategies

### 1. Right-Sizing Compute Resources

**ECS Task Optimization:**
```yaml
Before:
  Task Size: 2 vCPU, 4GB RAM
  Cost per task: $60/month
  Total (7 tasks): $420/month

After (Right-sized):
  API Tasks: 1 vCPU, 2GB RAM
  Cost per task: $30/month
  Worker Tasks: 0.5 vCPU, 1GB RAM
  Cost per task: $15/month
  Total (4 API + 3 Workers): $165/month
  Savings: $255/month (60%)

Implementation:
  # Task definition with right-sized resources
  resource "aws_ecs_task_definition" "api" {
    cpu    = "1024"  # 1 vCPU
    memory = "2048"  # 2GB
  }
```

**Auto-Scaling to Match Demand:**
```yaml
Strategy:
  - Scale down during low traffic (nights, weekends)
  - Scale up during peaks
  - Use target tracking based on CPU/memory

Configuration:
  Business Hours (9 AM - 6 PM): 4 tasks
  Off Hours: 2 tasks
  Weekend: 2 tasks
  
Savings:
  Average tasks: 2.5 (vs 4 always-on)
  Cost reduction: 37.5%
  Monthly savings: ~$130
```

### 2. Database Cost Optimization

**Use Appropriate Instance Size:**
```yaml
Current: db.t3.large ($250/month)

Options:
  db.t3.medium ($125/month):
    - Good for < 50 active users
    - Save: $125/month
  
  db.t3.large ($250/month):
    - Good for 50-500 users
    - Current choice (appropriate for launch)
  
  Aurora Serverless v2 (Variable):
    - Only pay for actual usage
    - Could be cheaper at low volumes
    - Estimated: $150-300/month
```

**Read Replica Strategy:**
```yaml
Instead of: Adding expensive read replicas early

Do: Wait until metrics show need
  - Monitor read query times
  - Add read replica only when P95 > 100ms
  - Start with one replica, not three

Savings: $250/month until needed
```

**Storage Optimization:**
```sql
-- Regularly clean up old data
DELETE FROM notifications 
WHERE created_at < NOW() - INTERVAL 30 DAY;

DELETE FROM llm_conversations 
WHERE created_at < NOW() - INTERVAL 90 DAY;

-- Use partitioning for large tables
CREATE TABLE transactions_2025_01 PARTITION OF transactions
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Archive old data to S3 (much cheaper)
-- Monthly cost: $0.023/GB in S3 vs $0.115/GB in RDS
```

---

### 3. Caching to Reduce Database Load

**Aggressive Caching Strategy:**
```python
# Cache frequently accessed data
CACHE_STRATEGY = {
    # Nearly static data - long TTL
    "token_list": 3600,           # 1 hour
    "protocol_configs": 1800,     # 30 min
    
    # Semi-dynamic data - medium TTL
    "apy_rates": 300,             # 5 min
    "user_balances": 60,          # 1 min
    
    # Dynamic data - short TTL
    "swap_quotes": 30,            # 30 sec
    "gas_prices": 10,             # 10 sec
}

# Result: 70% cache hit rate
# Database load reduction: 70%
# Potential to downgrade DB instance: $125/month savings
```

**Redis Cost vs. Database Cost:**
```yaml
Redis (cache.t3.medium): $100/month
  - Handles 70% of reads
  - Prevents need for read replica ($250/month)
  
Net Savings: $150/month
ROI: 150% return on Redis investment
```

---

### 4. Storage Cost Optimization

**S3 Lifecycle Policies:**
```python
# Configure S3 lifecycle rules
lifecycle_config = {
    "Rules": [
        {
            "Id": "ArchiveLogs",
            "Status": "Enabled",
            "Transitions": [
                {
                    # Move to Infrequent Access after 30 days
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    # Move to Glacier after 90 days
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365  # Delete after 1 year
            }
        },
        {
            "Id": "DeleteTempFiles",
            "Status": "Enabled",
            "Expiration": {
                "Days": 7  # Delete temp files after 7 days
            }
        }
    ]
}

# Cost comparison (per GB/month):
# S3 Standard: $0.023
# S3 IA: $0.0125
# Glacier: $0.004

# Example with 1TB logs:
# All Standard: $23.50/month
# With lifecycle: $8.50/month
# Savings: $15/month
```

**Image Optimization:**
```yaml
Strategy:
  - Convert images to WebP (30% smaller)
  - Implement lazy loading
  - Use CloudFront (cheaper than S3 direct)
  - Delete unused assets

Savings:
  Storage: $5/month
  Bandwidth: $15/month
  Total: $20/month
```

---

### 5. Network Cost Optimization

**Data Transfer Optimization:**
```yaml
Most Expensive:
  - Cross-region transfer: $0.02/GB
  - Internet egress: $0.09/GB
  - Inter-AZ: $0.01/GB

Cheapest:
  - Same AZ: FREE
  - CloudFront to internet: $0.085/GB
  
Strategy:
  1. Use same AZ when possible
  2. Use CloudFront for static assets
  3. Enable compression (gzip)
  4. Minimize API response size
  
Potential Savings: $30/month
```

**Response Compression:**
```python
# Enable gzip compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Result: 70% reduction in response size
# Data transfer savings: 70% of $50 = $35/month
```

---

### 6. Third-Party Service Optimization

**Privy Cost Management:**
```yaml
Current: $500/month (Pro plan)

Optimization:
  - Review user count monthly
  - Ensure not paying for inactive users
  - Consider volume discounts at scale
  
At 10,000 users: Negotiate custom pricing
Potential: $300/month (40% discount)
```

**Alchemy RPC Optimization:**
```yaml
Current: $199/month (Growth plan)

Optimization:
  - Cache blockchain data aggressively
  - Batch RPC calls
  - Use webhooks instead of polling
  - Monitor daily usage
  
Strategies:
  # Batch balance checks
  balances = await web3.eth.get_balance(addresses)  # 1 call
  # vs
  for addr in addresses:
      balance = await web3.eth.get_balance(addr)  # N calls

  # Cache chain data
  @cache(ttl=60)
  async def get_block_number():
      return await web3.eth.block_number
  
Result: Stay on Growth plan vs Enterprise ($999)
Savings: $800/month
```

**Vertex AI (Gemini) Optimization:**
```yaml
Current: ~$100/month (estimated)

Optimization:
  - Use smaller model (Gemini Flash vs Pro)
  - Limit context window size
  - Cache common responses
  - Implement prompt compression
  
Cost per 1M tokens:
  Input: $0.075
  Output: $0.30
  
Strategies:
  # Use shorter prompts
  prompt = f"User has {balance} USDC. Suggest action."
  # vs
  prompt = f"User profile: {...long context...}"
  
  # Cache AI responses
  @cache(ttl=3600)
  async def get_ai_advice(scenario: str):
      return await vertex_ai.generate(scenario)

Result: $50/month (50% reduction)
```

---

### 7. Monitoring Cost Optimization

**CloudWatch Cost Reduction:**
```yaml
Current: $30/month

Optimization:
  - Use metric filters instead of storing all logs
  - Adjust log retention (7 days vs 30 days)
  - Export logs to S3 for long-term storage
  - Use sampling for high-volume metrics
  
Retention Strategy:
  Application Logs: 7 days (CloudWatch) → 90 days (S3)
  Error Logs: 30 days (CloudWatch)
  Access Logs: 3 days (CloudWatch) → 30 days (S3)
  
Result: $15/month (50% reduction)
```

---

### 8. Development Environment Costs

**Separate Dev/Staging/Prod:**
```yaml
Mistake: Running dev/staging at same scale as prod

Dev Environment:
  - Single small instance
  - Minimal monitoring
  - Shut down nights/weekends
  Cost: $50/month

Staging Environment:
  - Smaller than prod
  - Only run during business hours
  - Auto-stop after 8 PM
  Cost: $150/month

Prod Environment:
  - Full scale
  - 24/7 availability
  Cost: $900/month

Without optimization: $900 × 3 = $2,700/month
With optimization: $1,100/month
Savings: $1,600/month
```

**Auto-Stop for Non-Prod:**
```bash
#!/bin/bash
# scripts/auto_stop_dev.sh

# Stop dev environment at 8 PM
aws ecs update-service \
  --cluster anvil-dev \
  --service anvil-api \
  --desired-count 0

# Start at 8 AM
# (Scheduled via EventBridge)
```

---

## 📊 Cost Monitoring & Alerts

### AWS Cost Explorer Configuration

```yaml
Budget Alerts:
  - Monthly Budget: $1,000
  - Alert at 80%: $800
  - Alert at 100%: $1,000
  - Alert at 120%: $1,200

Weekly Reviews:
  - Check cost by service
  - Identify anomalies
  - Review largest line items
  
Monthly Reviews:
  - Full cost breakdown
  - Year-over-year comparison
  - Optimization opportunities
```

### Cost Anomaly Detection

```python
# scripts/monitor_costs.py
import boto3
from datetime import datetime, timedelta

def check_cost_anomalies():
    """Alert on unexpected cost increases."""
    ce = boto3.client('ce')
    
    # Get last 7 days costs
    end = datetime.now().date()
    start = end - timedelta(days=7)
    
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start.strftime('%Y-%m-%d'),
            'End': end.strftime('%Y-%m-%d')
        },
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'SERVICE', 'Key': 'SERVICE'}]
    )
    
    # Check for >20% day-over-day increases
    for service_costs in response['ResultsByTime']:
        # Alert logic
        pass
```

---

## 💡 Cost Optimization Best Practices

### Development Practices

```yaml
DO:
  ✅ Use pagination for list endpoints
  ✅ Implement aggressive caching
  ✅ Batch database queries
  ✅ Use connection pooling
  ✅ Compress responses
  ✅ Clean up unused resources
  ✅ Monitor query performance
  ✅ Use appropriate indexes

DON'T:
  ❌ Query database in loops (N+1)
  ❌ Return full objects when not needed
  ❌ Skip caching layers
  ❌ Leave dev resources running 24/7
  ❌ Store unnecessary data
  ❌ Ignore slow queries
  ❌ Over-provision resources
```

### Architecture Decisions

```yaml
Serverless vs Containers:
  Serverless (Lambda):
    - Good for: Sporadic workloads
    - Cost: Pay per invocation
    - Anvil: Not ideal (steady traffic)
  
  Containers (ECS Fargate):
    - Good for: Steady workloads
    - Cost: Pay per hour
    - Anvil: Better choice ✓

Reserved Instances vs On-Demand:
  On-Demand:
    - Flexibility
    - Higher cost
  
  Reserved (1-year):
    - 30% discount
    - Less flexibility
    - Anvil: Consider after 6 months

  Savings Plans:
    - Flexible
    - 10-15% discount
    - Good middle ground
```

---

## 📈 Cost Scaling Strategy

### As User Base Grows

**0-100 Users:**
```yaml
Infrastructure:
  - 2 API tasks (minimal)
  - db.t3.small ($60/month)
  - cache.t3.micro ($15/month)
  
Total: ~$300/month
Cost per user: $3.00
```

**100-1,000 Users:**
```yaml
Infrastructure:
  - 4 API tasks
  - db.t3.large ($250/month)
  - cache.t3.medium ($100/month)
  - Read replica ($250/month)
  
Total: ~$1,000/month
Cost per user: $1.00
```

**1,000-10,000 Users:**
```yaml
Infrastructure:
  - 8 API tasks (auto-scaling)
  - db.t3.xlarge ($500/month)
  - cache.t3.large ($200/month)
  - 2 read replicas ($500/month)
  
Total: ~$2,500/month
Cost per user: $0.25
```

**10,000+ Users:**
```yaml
Infrastructure:
  - 20+ API tasks (auto-scaling)
  - Aurora Serverless or RDS clusters
  - ElastiCache cluster
  - Multi-region (if needed)
  
Total: ~$5,000-10,000/month
Cost per user: $0.50-1.00

Note: At scale, per-user costs decrease
Revenue should far exceed infrastructure costs
```

---

## 🎯 Monthly Cost Optimization Checklist

```yaml
Week 1:
  - [ ] Review AWS Cost Explorer
  - [ ] Check for unused resources
  - [ ] Verify auto-scaling working
  - [ ] Review RDS performance metrics

Week 2:
  - [ ] Analyze CloudWatch costs
  - [ ] Check S3 storage growth
  - [ ] Review third-party service usage
  - [ ] Optimize slow queries

Week 3:
  - [ ] Check cache hit rates
  - [ ] Review API endpoint usage
  - [ ] Analyze data transfer costs
  - [ ] Test dev environment auto-stop

Week 4:
  - [ ] Monthly cost report
  - [ ] Compare to budget
  - [ ] Identify optimization opportunities
  - [ ] Plan next month's optimizations
```

---

## 💰 ROI Calculations

### Cost Optimization Impact

```yaml
Without Optimization:
  Infrastructure: $2,700/month (dev+staging+prod at same scale)
  Services: $930/month
  Total: $3,630/month

With Optimization:
  Infrastructure: $900/month (right-sized, dev auto-stop)
  Services: $650/month (caching, batching)
  Total: $1,550/month

Monthly Savings: $2,080 (57% reduction)
Annual Savings: $24,960

Time Investment: 40 hours (one-time setup)
Hourly Value: $624 (incredible ROI!)
```

---

## 🎓 Resources

### Tools
```yaml
AWS Cost Explorer: Built-in cost analysis
AWS Budgets: Alerts and tracking
Infracost: Cost estimates for Terraform
CloudHealth: Multi-cloud cost management
Cost Anomaly Detection: AWS native feature
```

### Monitoring Commands
```bash
# Get current month costs
aws ce get-cost-and-usage \
  --time-period Start=2025-11-01,End=2025-11-30 \
  --granularity MONTHLY \
  --metrics UnblendedCost

# List all running EC2/ECS
aws ec2 describe-instances --filters "Name=instance-state-name,Values=running"
aws ecs list-tasks --cluster anvil-production

# Check RDS utilization
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --start-time 2025-11-01T00:00:00Z \
  --end-time 2025-11-30T23:59:59Z \
  --period 86400 \
  --statistics Average
```

---

## ✅ Summary: Quick Wins

**Immediate Actions (Week 1):**
1. Right-size ECS tasks → Save $255/month
2. Enable auto-scaling with time-based policies → Save $130/month
3. Implement response compression → Save $35/month
4. Auto-stop dev environment nights/weekends → Save $400/month

**Total Quick Wins: $820/month (52% reduction)**

**Medium-term Actions (Month 1):**
1. Aggressive caching strategy → Save $150/month
2. S3 lifecycle policies → Save $15/month
3. CloudWatch optimization → Save $15/month
4. Optimize third-party usage → Save $100/month

**Total Medium-term: $280/month additional**

**Grand Total Savings: $1,100/month (71% cost reduction)**

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Maintained By:** DevOps + Finance  
**Review:** Monthly

**Cost optimization is an ongoing process - review and improve continuously!**
