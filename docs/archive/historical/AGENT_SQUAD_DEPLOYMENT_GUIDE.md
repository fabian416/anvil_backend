# Agent Squad Deployment Guide

**Document**: AgentSquad-DeploymentGuide  
**Date**: December 1, 2025  
**Version**: 1.0  
**Environment**: Production

---

## 🚀 Production Deployment

### Prerequisites

- AWS Account (or equivalent cloud provider)
- Docker installed
- PostgreSQL 15+
- Redis 7+
- Domain name configured
- SSL certificate

---

## 📋 Deployment Checklist

### 1. Environment Setup

**Required Environment Variables**:

```bash
# Application
APP_ENV=prod
SECRET_KEY=<generate-secure-key>

# Database
POSTGRES_HOST=<rds-endpoint>
POSTGRES_PORT=5432
POSTGRES_DB=anvil_prod
POSTGRES_USER=anvil
POSTGRES_PASSWORD=<secure-password>

# Redis
REDIS_URL=redis://<elasticache-endpoint>:6379

# OpenAI
OPENAI_API_KEY=sk-...

# Enterprise Integrations (if enabled)
CHAINALYSIS_API_KEY=...
GNOSIS_SAFE_API_KEY=...
FORTA_API_KEY=...
TWILIO_API_KEY=...
TWILIO_PHONE_NUMBER=...

# Privy (Wallet)
PRIVY_APP_ID=...
PRIVY_API_SECRET=...

# Monitoring
SENTRY_DSN=https://...
DATADOG_API_KEY=...
```

---

### 2. Database Setup

```bash
# 1. Create RDS PostgreSQL instance
# - Instance type: db.t3.medium (minimum)
# - Storage: 100GB SSD
# - Backup retention: 7 days
# - Multi-AZ: Enabled

# 2. Create database
psql -h <rds-endpoint> -U postgres -c "CREATE DATABASE anvil_prod;"

# 3. Run migrations
export DATABASE_URL=postgresql://user:pass@host/anvil_prod
alembic upgrade head

# 4. Verify tables
psql $DATABASE_URL -c "\dt"
# Should show: agent_sessions, agent_telemetry, compliance_screening_logs,
#              multisig_proposals, crisis_events
```

---

### 3. Redis Setup

```bash
# Create ElastiCache Redis cluster
# - Node type: cache.t3.medium (minimum)
# - Number of nodes: 2 (replica enabled)
# - Encryption: Enabled (in-transit and at-rest)

# Test connection
redis-cli -h <elasticache-endpoint> PING
# Should return: PONG
```

---

### 4. Docker Build

```bash
# Build production image
docker build -t agent-squad:latest -f Dockerfile .

# Tag for ECR
docker tag agent-squad:latest <account>.dkr.ecr.<region>.amazonaws.com/agent-squad:latest

# Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker push <account>.dkr.ecr.<region>.amazonaws.com/agent-squad:latest
```

---

### 5. ECS/EKS Deployment

**ECS Task Definition**:

```json
{
  "family": "agent-squad",
  "taskRoleArn": "arn:aws:iam::<account>:role/agent-squad-task-role",
  "executionRoleArn": "arn:aws:iam::<account>:role/agent-squad-execution-role",
  "networkMode": "awsvpc",
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "agent-squad-api",
      "image": "<account>.dkr.ecr.<region>.amazonaws.com/agent-squad:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "APP_ENV", "value": "prod"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/agent-squad",
          "awslogs-region": "<region>",
          "awslogs-stream-prefix": "api"
        }
      }
    }
  ]
}
```

**ECS Service**:

```json
{
  "serviceName": "agent-squad-api",
  "cluster": "production",
  "taskDefinition": "agent-squad:latest",
  "desiredCount": 3,
  "launchType": "FARGATE",
  "loadBalancers": [
    {
      "targetGroupArn": "arn:aws:elasticloadbalancing:...",
      "containerName": "agent-squad-api",
      "containerPort": 8000
    }
  ],
  "networkConfiguration": {
    "awsvpcConfiguration": {
      "subnets": ["subnet-...", "subnet-..."],
      "securityGroups": ["sg-..."],
      "assignPublicIp": "DISABLED"
    }
  }
}
```

---

### 6. Load Balancer Setup

**Application Load Balancer**:

```bash
# Create ALB
aws elbv2 create-load-balancer \
  --name agent-squad-alb \
  --subnets subnet-... subnet-... \
  --security-groups sg-... \
  --scheme internet-facing

# Create target group
aws elbv2 create-target-group \
  --name agent-squad-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-... \
  --health-check-path /health

# Configure listener (HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn <alb-arn> \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=<cert-arn> \
  --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

---

### 7. Monitoring Setup

**Sentry (Error Tracking)**:

```python
# Already integrated in app

import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1,
)
```

**Datadog (Performance)**:

```python
# Add to Dockerfile

RUN pip install ddtrace

# Run with datadog
CMD ["ddtrace-run", "uvicorn", "app.run:make_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

**CloudWatch Alarms**:

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name agent-squad-high-errors \
  --metric-name 5XXError \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold

# High latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name agent-squad-high-latency \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 2.0 \
  --comparison-operator GreaterThanThreshold
```

---

### 8. Auto-Scaling

**ECS Auto-Scaling**:

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/production/agent-squad-api \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/production/agent-squad-api \
  --policy-name agent-squad-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    '{
      "TargetValue": 70.0,
      "PredefinedMetricSpecification": {
        "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
      }
    }'
```

---

### 9. Backup & Recovery

**Database Backups**:

```bash
# Automated RDS backups
# - Backup retention: 7 days
# - Backup window: 03:00-04:00 UTC
# - Maintenance window: Sunday 04:00-05:00 UTC

# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier agent-squad-prod \
  --db-snapshot-identifier agent-squad-manual-$(date +%Y%m%d)
```

**Disaster Recovery**:

```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier agent-squad-restore \
  --db-snapshot-identifier agent-squad-manual-20251201

# Point application to restored instance
# Update DATABASE_URL environment variable
```

---

### 10. Security Hardening

**Network Security**:

```bash
# VPC Configuration
# - Private subnets for ECS tasks
# - Public subnets for ALB
# - NAT Gateway for outbound traffic
# - Security groups (least privilege)

# Security Group Rules (ECS tasks)
# - Inbound: Port 8000 from ALB security group only
# - Outbound: PostgreSQL (5432), Redis (6379), HTTPS (443)

# Security Group Rules (ALB)
# - Inbound: Port 443 from 0.0.0.0/0
# - Outbound: Port 8000 to ECS tasks
```

**Secrets Management**:

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name agent-squad/openai-api-key \
  --secret-string "sk-..."

# Grant ECS task role access
# IAM policy: secretsmanager:GetSecretValue
```

---

## ✅ Post-Deployment Checklist

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] Secrets stored securely (AWS Secrets Manager)
- [ ] Load balancer health checks passing
- [ ] Auto-scaling configured
- [ ] Monitoring enabled (Sentry, Datadog)
- [ ] Alarms configured (CloudWatch)
- [ ] Backups enabled (RDS automated backups)
- [ ] SSL certificate configured
- [ ] Domain name configured (Route 53)
- [ ] Rate limiting enabled
- [ ] CORS configured
- [ ] Logging enabled (CloudWatch Logs)

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy-production.yml

name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }}
      
      - name: Build and push
        run: |
          docker build -t agent-squad:latest .
          docker tag agent-squad:latest ${{ secrets.ECR_REGISTRY }}/agent-squad:latest
          docker push ${{ secrets.ECR_REGISTRY }}/agent-squad:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster production \
            --service agent-squad-api \
            --force-new-deployment
```

---

## 📊 Monitoring Dashboard

### Key Metrics

**Performance**:
- Request latency (P50, P95, P99)
- Throughput (requests/second)
- Error rate (4xx, 5xx)
- Agent response times (per agent)

**Business**:
- Active conversations
- Messages per day
- Agent usage distribution
- User tier breakdown

**Infrastructure**:
- CPU utilization
- Memory usage
- Database connections
- Redis hit rate

---

## 🆘 Incident Response

### On-Call Procedures

**High Error Rate** (>5%):
1. Check CloudWatch logs
2. Review Sentry errors
3. Check external API status
4. Scale up if needed
5. Rollback if critical

**High Latency** (P95 > 3s):
1. Check database performance
2. Review slow queries
3. Check Redis connection
4. Increase cache TTL
5. Scale up resources

**External API Failures**:
1. Check API status pages
2. Implement circuit breaker
3. Use fallback responses
4. Notify users of degraded service

---

## ✅ Launch Readiness

**Pre-Launch**:
- ✅ All 18 agents implemented
- ✅ Security audit complete
- ✅ Load testing passed (1000+ users)
- ✅ Monitoring configured
- ✅ Documentation complete
- ⚠️ External penetration testing (recommended)
- ⚠️ Bug bounty program (recommended)

**Post-Launch**:
- Monitor error rates (first 24 hours)
- Scale based on traffic
- User feedback collection
- Performance optimization
- Feature flag adjustment

---

**Status**: 🟢 **READY FOR PRODUCTION**  
**Timeline**: Deploy Week 12  
**Support**: 24/7 on-call team

---
