# 🚀 Anvil Platform - Deployment & DevOps Guide

## Infrastructure, CI/CD, and Operations

**Version:** 1.0  
**Date:** November 2025  
**Target:** AWS Cloud Infrastructure

---

## 🏗️ Infrastructure Architecture

### AWS Services Overview

```
┌────────────────────────────────────────────────────────┐
│                    Route 53 (DNS)                      │
│              anvil.com / api.anvil.com                 │
└──────────────────┬─────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│              CloudFront (CDN + WAF)                    │
│    Static Assets + DDoS Protection                     │
└──────────────────┬─────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│        Application Load Balancer (ALB)                 │
│         SSL/TLS Termination                            │
└──────────────────┬─────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│          ECS Fargate Cluster                           │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ API Task │ API Task │ API Task │ API Task │        │
│  │  (4 vCPU │  (4 vCPU │  (4 vCPU │  (4 vCPU │        │
│  │   8GB)   │   8GB)   │   8GB)   │   8GB)   │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
└────────────────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│         Worker Cluster (ECS Fargate)                   │
│  ┌──────────┬──────────┬──────────┐                   │
│  │ Celery   │ Celery   │ Celery   │                   │
│  │ Worker 1 │ Worker 2 │ Worker 3 │                   │
│  └──────────┴──────────┴──────────┘                   │
└────────────────────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────────────────────┐
│                  Data Layer                            │
│  ┌──────────┬──────────────┬─────────┬──────────┐     │
│  │RDS MySQL │ElastiCache   │   S3    │CloudWatch│     │
│  │Multi-AZ  │Redis Cluster │Documents│Logs/Metr.│     │
│  └──────────┴──────────────┴─────────┴──────────┘     │
└────────────────────────────────────────────────────────┘
```

---

## 📦 Containerization

### Dockerfile (API Server)

```dockerfile
# Base image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 anvil && chown -R anvil:anvil /app
USER anvil

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Dockerfile (Celery Worker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 anvil && chown -R anvil:anvil /app
USER anvil

# Run Celery worker
CMD ["celery", "-A", "app.workers.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
```

### docker-compose.yml (Local Development)

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app:/app/app
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    env_file:
      - .env
    depends_on:
      - db
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info

  beat:
    build:
      context: .
      dockerfile: Dockerfile.worker
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A app.workers.celery_app beat --loglevel=info

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: anvil
      MYSQL_USER: anvil
      MYSQL_PASSWORD: anvilpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  flower:
    build:
      context: .
      dockerfile: Dockerfile.worker
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
    command: celery -A app.workers.celery_app flower

volumes:
  mysql_data:
  redis_data:
```

---

## ☸️ Kubernetes Configuration (Optional)

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: anvil-api
  namespace: production
spec:
  replicas: 4
  selector:
    matchLabels:
      app: anvil-api
  template:
    metadata:
      labels:
        app: anvil-api
    spec:
      containers:
      - name: api
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/anvil-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: anvil-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: anvil-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: anvil-api-service
  namespace: production
spec:
  selector:
    app: anvil-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy.yml:**

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: anvil-api
  ECS_CLUSTER: anvil-production
  ECS_SERVICE: anvil-api-service

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: testpassword
          MYSQL_DATABASE: anvil_test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
        ports:
          - 3306:3306
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run linting
      run: |
        pip install flake8 black mypy
        flake8 app --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check app
        mypy app --ignore-missing-imports
    
    - name: Run tests
      env:
        DATABASE_URL: mysql+pymysql://root:testpassword@localhost:3306/anvil_test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/ -v --cov=app --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
  
  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1
    
    - name: Build, tag, and push image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
  
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}
    
    - name: Update ECS service
      run: |
        aws ecs update-service \
          --cluster ${{ env.ECS_CLUSTER }} \
          --service ${{ env.ECS_SERVICE }} \
          --force-new-deployment
    
    - name: Wait for deployment
      run: |
        aws ecs wait services-stable \
          --cluster ${{ env.ECS_CLUSTER }} \
          --services ${{ env.ECS_SERVICE }}
    
    - name: Notify Slack
      if: always()
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Deployment to production ${{ job.status }}'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 🌍 Environment Configuration

### Environment Files

**.env.example:**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=mysql+pymysql://anvil:password@localhost:3306/anvil
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:19006"]

# Privy
PRIVY_APP_ID=your_privy_app_id
PRIVY_APP_SECRET=your_privy_secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Blockchain
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/your_key
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/your_key

# 1inch
ONEINCH_API_KEY=your_1inch_key

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# SendGrid
SENDGRID_API_KEY=SG.your_key
SENDGRID_FROM_EMAIL=noreply@anvil.com

# Twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=your_token
TWILIO_FROM_NUMBER=+1234567890

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/credentials.json

# Sentry
SENTRY_DSN=https://your_sentry_dsn

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Terraform Configuration (Infrastructure as Code)

**main.tf:**
```hcl
# Provider
provider "aws" {
  region = "us-east-1"
}

# VPC
resource "aws_vpc" "anvil" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "anvil-vpc"
    Environment = "production"
  }
}

# Subnets
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.anvil.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  
  tags = {
    Name = "anvil-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.anvil.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name = "anvil-private-b"
  }
}

# RDS MySQL
resource "aws_db_instance" "anvil" {
  identifier             = "anvil-production"
  engine                = "mysql"
  engine_version        = "8.0"
  instance_class        = "db.t3.large"
  allocated_storage     = 100
  storage_encrypted     = true
  
  db_name  = "anvil"
  username = "anvil_admin"
  password = var.db_password
  
  multi_az               = true
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.anvil.name
  
  skip_final_snapshot = false
  final_snapshot_identifier = "anvil-final-snapshot"
  
  tags = {
    Name = "anvil-db"
    Environment = "production"
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "anvil" {
  cluster_id           = "anvil-redis"
  engine              = "redis"
  engine_version      = "7.0"
  node_type           = "cache.t3.medium"
  num_cache_nodes     = 1
  parameter_group_name = "default.redis7"
  port                = 6379
  
  subnet_group_name    = aws_elasticache_subnet_group.anvil.name
  security_group_ids   = [aws_security_group.redis.id]
  
  tags = {
    Name = "anvil-redis"
    Environment = "production"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "anvil" {
  name = "anvil-production"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "anvil-cluster"
    Environment = "production"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "anvil-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "4096"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([
    {
      name  = "api"
      image = "${aws_ecr_repository.anvil.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = [
        { name = "ENVIRONMENT", value = "production" },
        { name = "DATABASE_URL", value = "mysql+pymysql://${aws_db_instance.anvil.username}:${var.db_password}@${aws_db_instance.anvil.endpoint}/anvil" }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/anvil-api"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "anvil-api-service"
  cluster         = aws_ecs_cluster.anvil.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 4
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups = [aws_security_group.ecs.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.api]
}

# Application Load Balancer
resource "aws_lb" "anvil" {
  name               = "anvil-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  
  enable_deletion_protection = true
  
  tags = {
    Name = "anvil-alb"
    Environment = "production"
  }
}
```

---

## 📊 Monitoring & Logging

### CloudWatch Dashboards

```python
# Create custom metrics
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_metric(metric_name, value, unit='Count'):
    """Publish custom metric to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='Anvil/API',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
        ]
    )

# Example usage
publish_metric('TransactionSuccess', 1)
publish_metric('APIResponseTime', 250, 'Milliseconds')
```

### Log Aggregation

**CloudWatch Log Groups:**
```
/ecs/anvil-api          # API server logs
/ecs/anvil-worker       # Celery worker logs
/aws/rds/anvil          # Database logs
/aws/lambda/anvil       # Lambda function logs
```

**Structured Logging:**
```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "transaction_created",
    user_id=user.id,
    transaction_type="swap",
    amount_usd=50.00,
    chain="arbitrum"
)
```

### Alerts Configuration

```yaml
Alerts:
  - Name: High Error Rate
    Metric: Errors per minute > 100
    Action: SNS notification to on-call
    
  - Name: High Latency
    Metric: P95 response time > 1000ms
    Action: Slack alert to engineering
    
  - Name: Database Connections
    Metric: Connection pool > 80% utilized
    Action: Scale up warning
    
  - Name: Failed Transactions
    Metric: Failed tx rate > 5%
    Action: Page on-call engineer
    
  - Name: Celery Queue Backup
    Metric: Queue length > 1000
    Action: Auto-scale workers
```

---

## 🔄 Database Migrations

### Alembic Setup

**alembic.ini:**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = mysql+pymysql://user:pass@localhost/anvil

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "add_subscription_tables"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Example Migration

```python
"""add_subscription_tables

Revision ID: abc123
Create Date: 2025-11-16

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )

def downgrade():
    op.drop_table('subscriptions')
```

---

## 🔒 Secrets Management

### AWS Secrets Manager

```python
import boto3
import json

def get_secret(secret_name):
    """Retrieve secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except Exception as e:
        raise Exception(f"Error retrieving secret: {str(e)}")

# Usage
secrets = get_secret('anvil/production/api')
database_url = secrets['DATABASE_URL']
stripe_key = secrets['STRIPE_SECRET_KEY']
```

---

## 📈 Scaling Strategy

### Auto-Scaling Configuration

**ECS Service Auto-Scaling:**
```hcl
resource "aws_appautoscaling_target" "ecs" {
  max_capacity       = 10
  min_capacity       = 4
  resource_id        = "service/${aws_ecs_cluster.anvil.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "ecs_cpu" {
  name               = "anvil-api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs.service_namespace
  
  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
  }
}
```

### Database Scaling

**Read Replicas:**
```hcl
resource "aws_db_instance" "replica" {
  identifier          = "anvil-replica"
  replicate_source_db = aws_db_instance.anvil.identifier
  instance_class      = "db.t3.large"
  
  tags = {
    Name = "anvil-read-replica"
  }
}
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code review approved
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets rotated (if needed)
- [ ] Backup verified
- [ ] Rollback plan documented

### Deployment
- [ ] Notify team of deployment
- [ ] Run database migrations
- [ ] Deploy new containers
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Monitor error rates
- [ ] Monitor performance metrics

### Post-Deployment
- [ ] Verify functionality in production
- [ ] Check CloudWatch metrics
- [ ] Review application logs
- [ ] Update documentation
- [ ] Notify stakeholders
- [ ] Document any issues

### Rollback Procedure
```bash
# Rollback ECS service to previous task definition
aws ecs update-service \
  --cluster anvil-production \
  --service anvil-api-service \
  --task-definition anvil-api:PREVIOUS_VERSION

# Rollback database migration
alembic downgrade -1
```

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Next Review:** Monthly  
**DevOps Contact:** devops@anvil.com
