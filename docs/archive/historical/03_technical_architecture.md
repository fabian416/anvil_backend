# 🏗️ Anvil Platform - Technical Architecture Document

## System Architecture for Development Team

**Version:** 1.0  
**Date:** November 2025  
**Backend:** Python 3.11+ with FastAPI & SQLAlchemy 2.0

---

## 📊 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                      │
├──────────────────────────┬──────────────────────────────────┤
│   iOS/Android App        │     Admin/Auditor Console        │
│   (React Native)         │     (Next.js + React)            │
└──────────────────────────┴──────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CDN & LOAD BALANCER                     │
│  CloudFront (Static) │ AWS ALB (API) │ WAF (Security)       │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                       │
│  • Authentication (JWT)                                      │
│  • Rate Limiting (Redis)                                     │
│  • Request Validation                                        │
│  • CORS Handling                                             │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION SERVERS                        │
│                   (Python 3.11 + FastAPI)                    │
├─────────────────────────────────────────────────────────────┤
│  Service Layer:                                              │
│  • User Service          • Trading Service                   │
│  • Wallet Service        • Earn Service                      │
│  • Transaction Service   • Perpetuals Service                │
│  • AI Service            • Notification Service              │
│  • Payment Service       • Admin Service                     │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKGROUND WORKERS                        │
│                    (Celery + Redis)                          │
├─────────────────────────────────────────────────────────────┤
│  • Blockchain monitoring                                     │
│  • Price updates                                             │
│  • Save schedule execution                                   │
│  • Position updates (perps)                                  │
│  • Notification delivery                                     │
│  • Report generation                                         │
└─────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                             │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  MySQL 8.0   │ Redis Cache  │ S3 Storage   │ CloudWatch     │
│  (RDS)       │ (ElastiCache)│ (Documents)  │ (Logs/Metrics) │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                      │
├─────────────────────────────────────────────────────────────┤
│  Blockchain:  Privy, Alchemy (RPC), 1inch, Aave, Compound   │
│  Payments:    Stripe                                         │
│  AI:          Google Vertex AI (Gemini)                      │
│  Perps:       Hyperliquid API                                │
│  Messaging:   SendGrid, Twilio, Firebase (FCM)              │
│  KYC:         Persona/Onfido                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐍 Backend Technology Stack (Python)

### Core Framework
```yaml
Language: Python 3.11+
Framework: FastAPI 0.104+
ASGI Server: Uvicorn 0.24+
ORM: SQLAlchemy 2.0+
Database Driver: PyMySQL 1.1+
Migration Tool: Alembic 1.12+
```

### Key Dependencies

**requirements.txt:**
```txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
pymysql==1.1.0
alembic==1.12.1

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Blockchain
web3==6.11.3
eth-account==0.10.0
eth-utils==2.3.1

# Redis & Caching
redis==5.0.1
hiredis==2.2.3

# Background Tasks
celery==5.3.4
flower==2.0.1

# External APIs
stripe==7.4.0
requests==2.31.0
httpx==0.25.2

# AI/ML
google-cloud-aiplatform==1.38.0

# Monitoring
sentry-sdk[fastapi]==1.38.0
prometheus-client==0.19.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Utilities
python-dotenv==1.0.0
pytz==2023.3
```

---

## 🏛️ Application Architecture

### Directory Structure

```
anvil-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry
│   ├── config.py                  # Configuration management
│   ├── dependencies.py            # Dependency injection
│   │
│   ├── api/                       # API Layer
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── wallets.py
│   │   │   │   ├── transactions.py
│   │   │   │   ├── trading.py
│   │   │   │   ├── earn.py
│   │   │   │   ├── save.py
│   │   │   │   ├── perpetuals.py
│   │   │   │   ├── ai.py
│   │   │   │   ├── notifications.py
│   │   │   │   ├── subscriptions.py
│   │   │   │   └── admin.py
│   │   │   └── dependencies.py
│   │   └── middleware/
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       ├── logging.py
│   │       └── error_handler.py
│   │
│   ├── models/                    # SQLAlchemy Models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── wallet.py
│   │   ├── transaction.py
│   │   ├── earn.py
│   │   ├── perpetual.py
│   │   ├── ai.py
│   │   ├── notification.py
│   │   ├── subscription.py
│   │   └── audit.py
│   │
│   ├── schemas/                   # Pydantic Schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── wallet.py
│   │   ├── transaction.py
│   │   ├── trading.py
│   │   ├── earn.py
│   │   ├── perpetual.py
│   │   └── common.py
│   │
│   ├── services/                  # Business Logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── wallet_service.py
│   │   ├── trading_service.py
│   │   ├── earn_service.py
│   │   ├── save_service.py
│   │   ├── perpetual_service.py
│   │   ├── ai_service.py
│   │   ├── notification_service.py
│   │   ├── subscription_service.py
│   │   └── audit_service.py
│   │
│   ├── integrations/              # External APIs
│   │   ├── __init__.py
│   │   ├── privy.py
│   │   ├── stripe.py
│   │   ├── oneinch.py
│   │   ├── aave.py
│   │   ├── compound.py
│   │   ├── hyperliquid.py
│   │   ├── vertex_ai.py
│   │   ├── sendgrid.py
│   │   ├── twilio.py
│   │   └── firebase.py
│   │
│   ├── blockchain/                # Blockchain Logic
│   │   ├── __init__.py
│   │   ├── web3_client.py
│   │   ├── contracts/
│   │   │   ├── aave.py
│   │   │   ├── compound.py
│   │   │   └── erc20.py
│   │   └── utils.py
│   │
│   ├── workers/                   # Celery Tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── blockchain_tasks.py
│   │   ├── price_tasks.py
│   │   ├── save_tasks.py
│   │   ├── notification_tasks.py
│   │   └── report_tasks.py
│   │
│   ├── core/                      # Core Utilities
│   │   ├── __init__.py
│   │   ├── security.py           # JWT, password hashing
│   │   ├── database.py           # DB session management
│   │   ├── cache.py              # Redis operations
│   │   ├── exceptions.py         # Custom exceptions
│   │   └── logging.py            # Logging configuration
│   │
│   └── utils/                     # Helper Functions
│       ├── __init__.py
│       ├── validators.py
│       ├── formatters.py
│       └── constants.py
│
├── alembic/                       # Database Migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/                         # Test Suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   ├── test_integrations/
│   └── test_workers/
│
├── scripts/                       # Utility Scripts
│   ├── init_db.py
│   ├── seed_data.py
│   └── deploy.sh
│
├── .env.example
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🔧 Core Components

### 1. FastAPI Application (main.py)

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import settings
from app.core.database import engine
from app.models import Base
from app.api.v1.routes import (
    auth, users, wallets, transactions, 
    trading, earn, save, perpetuals, 
    ai, notifications, subscriptions, admin
)
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware

# Sentry initialization
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)

# Create FastAPI app
app = FastAPI(
    title="Anvil API",
    description="DeFi Trading Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1/user/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/user", tags=["users"])
app.include_router(wallets.router, prefix="/api/v1/user/wallet", tags=["wallet"])
app.include_router(transactions.router, prefix="/api/v1/user/transactions", tags=["transactions"])
app.include_router(trading.router, prefix="/api/v1/user/trade", tags=["trading"])
app.include_router(earn.router, prefix="/api/v1/user/earn", tags=["earn"])
app.include_router(save.router, prefix="/api/v1/user/save", tags=["save"])
app.include_router(perpetuals.router, prefix="/api/v1/user/perpetuals", tags=["perpetuals"])
app.include_router(ai.router, prefix="/api/v1/user/chat", tags=["ai"])
app.include_router(notifications.router, prefix="/api/v1/user/notifications", tags=["notifications"])
app.include_router(subscriptions.router, prefix="/api/v1/user/subscription", tags=["subscriptions"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Application shutting down")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }
```

---

### 2. Configuration (config.py)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "Anvil API"
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str
    REDIS_DB: int = 0
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Privy
    PRIVY_APP_ID: str
    PRIVY_APP_SECRET: str
    
    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # Blockchain RPCs
    ARBITRUM_RPC_URL: str
    BASE_RPC_URL: str
    
    # 1inch
    ONEINCH_API_KEY: str
    
    # Hyperliquid
    HYPERLIQUID_API_URL: str = "https://api.hyperliquid.xyz"
    
    # Vertex AI
    GOOGLE_CLOUD_PROJECT: str
    GOOGLE_CLOUD_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-1.5-flash"
    
    # SendGrid
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str
    
    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_FROM_NUMBER: str
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str
    
    # Sentry
    SENTRY_DSN: str = ""
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

---

### 3. Database Configuration (core/database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 4. Authentication Service Example (services/auth_service.py)

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User
from app.integrations.privy import PrivyClient

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.privy_client = PrivyClient()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
    
    async def authenticate_with_privy(self, privy_token: str) -> User:
        """Authenticate user with Privy token"""
        try:
            # Verify Privy token
            privy_user = await self.privy_client.verify_token(privy_token)
            
            # Get or create user
            user = self.db.query(User).filter(
                User.privy_user_id == privy_user["id"]
            ).first()
            
            if not user:
                # Create new user
                user = User(
                    uid=f"usr_{uuid.uuid4().hex[:16]}",
                    privy_user_id=privy_user["id"],
                    email=privy_user["email"],
                    role=2,  # CLIENT
                    status=1,  # ACTIVE
                    email_verified=privy_user.get("email_verified", False)
                )
                self.db.add(user)
                self.db.commit()
                self.db.refresh(user)
                
                # Create wallet asynchronously
                from app.workers.blockchain_tasks import create_user_wallet
                create_user_wallet.delay(user.id)
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            
            return user
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )
```

---

### 5. Celery Configuration (workers/celery_app.py)

```python
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "anvil",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.blockchain_tasks",
        "app.workers.price_tasks",
        "app.workers.save_tasks",
        "app.workers.notification_tasks",
        "app.workers.report_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    # Update prices every 30 seconds
    "update-token-prices": {
        "task": "app.workers.price_tasks.update_token_prices",
        "schedule": 30.0,
    },
    # Monitor blockchain transactions every minute
    "monitor-transactions": {
        "task": "app.workers.blockchain_tasks.monitor_pending_transactions",
        "schedule": 60.0,
    },
    # Execute save schedules every hour
    "execute-save-schedules": {
        "task": "app.workers.save_tasks.execute_scheduled_saves",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Update perpetual positions every 10 seconds
    "update-perp-positions": {
        "task": "app.workers.blockchain_tasks.update_perpetual_positions",
        "schedule": 10.0,
    },
    # Clean up old notifications daily
    "cleanup-notifications": {
        "task": "app.workers.notification_tasks.cleanup_old_notifications",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

---

## 🗄️ Database Layer

### Connection Pooling
```python
# Optimized for production
pool_size = 10          # Base connections
max_overflow = 20       # Additional connections
pool_recycle = 3600     # Recycle after 1 hour
pool_pre_ping = True    # Test connection before use
```

### Read Replicas (Production)
```python
# Master (Write)
MASTER_DB_URL = "mysql+pymysql://user:pass@master.rds.amazonaws.com/anvil"

# Replica (Read)
REPLICA_DB_URL = "mysql+pymysql://user:pass@replica.rds.amazonaws.com/anvil"
```

---

## 📦 Caching Strategy (Redis)

### Cache Keys
```python
# User data
user:{user_id}:profile           # TTL: 1 hour
user:{user_id}:wallet            # TTL: 5 minutes

# Token prices
price:{chain}:{token}            # TTL: 30 seconds

# Transaction status
tx:{tx_hash}:status              # TTL: 1 hour

# Rate limiting
rate_limit:{user_id}:{endpoint}  # TTL: 1 minute

# Session tokens
session:{token}                  # TTL: 1 hour
```

### Caching Implementation
```python
import redis
from app.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

async def get_cached(key: str):
    """Get from cache"""
    return redis_client.get(key)

async def set_cached(key: str, value: str, ttl: int = 3600):
    """Set in cache with TTL"""
    redis_client.setex(key, ttl, value)
```

---

## 🔄 Background Workers (Celery)

### Task Types

**1. Blockchain Monitoring**
```python
@celery_app.task
def monitor_pending_transactions():
    """Monitor pending blockchain transactions"""
    # Check pending transactions
    # Update status when confirmed
    # Send notifications
```

**2. Price Updates**
```python
@celery_app.task
def update_token_prices():
    """Update token prices from oracles"""
    # Fetch from Chainlink
    # Update cache
    # Trigger price alerts
```

**3. Save Execution**
```python
@celery_app.task
def execute_scheduled_saves():
    """Execute due save schedules"""
    # Find due schedules
    # Execute purchases
    # Update records
```

**4. Position Updates**
```python
@celery_app.task
def update_perpetual_positions():
    """Update perpetual position data"""
    # Fetch from Hyperliquid
    # Calculate P&L
    # Check liquidation risk
    # Send warnings if needed
```

---

## 🌐 API Layer Design

### Route Organization
```
/api/v1/
├── user/              # CLIENT endpoints
│   ├── auth/
│   ├── profile
│   ├── wallet/
│   ├── transactions/
│   ├── trade/
│   ├── earn/
│   ├── save/
│   ├── perpetuals/
│   ├── chat/
│   ├── notifications/
│   └── subscription/
│
└── admin/             # ADMIN/AUDITOR endpoints
    ├── auth/
    ├── dashboard/
    ├── users/
    ├── transactions/
    ├── settings/
    ├── ai/
    └── audit-logs/
```

### Middleware Stack
```
Request
  ↓
CORS Middleware
  ↓
GZip Middleware
  ↓
Logging Middleware
  ↓
Rate Limit Middleware
  ↓
Authentication Middleware
  ↓
Route Handler
  ↓
Response
```

---

## 🔐 Security Architecture

### Authentication Flow
```
1. User provides Privy token
2. Backend verifies with Privy API
3. Backend generates JWT
4. JWT stored in mobile app (secure storage)
5. JWT sent with all requests (Bearer token)
6. Backend validates JWT on each request
7. JWT refreshed before expiry
```

### Authorization Levels
- **PUBLIC**: No authentication required
- **CLIENT**: Valid JWT, role = 2
- **ADMIN**: Valid JWT, role = 0, 2FA verified
- **AUDITOR**: Valid JWT, role = 1, 2FA verified

---

## 📊 Monitoring & Observability

### Metrics (Prometheus)
```python
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# Business metrics
active_users = Gauge('active_users_total', 'Active users')
transaction_volume = Counter('transaction_volume_usd', 'Transaction volume')
```

### Logging (Structured)
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "transaction_created",
    user_id=user.id,
    tx_type="swap",
    amount=50.0,
    asset="USDC"
)
```

### Error Tracking (Sentry)
- Automatic error capture
- Performance monitoring
- Release tracking
- User feedback

---

## 🚀 Deployment Architecture

### AWS Infrastructure
```
┌─────────────────────┐
│   Route 53 (DNS)    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  CloudFront (CDN)   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   ALB (Load Bal.)   │
└──────────┬──────────┘
           ↓
┌─────────────────────────────────┐
│  ECS Fargate (API Containers)   │
│  ├── Task 1 (FastAPI)           │
│  ├── Task 2 (FastAPI)           │
│  └── Task N (FastAPI)           │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│    RDS MySQL (Multi-AZ)         │
│    ElastiCache Redis            │
│    S3 (Object Storage)          │
└─────────────────────────────────┘
```

### Container Configuration (Dockerfile)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 📈 Performance Optimization

### Database Optimization
- **Indexes**: All foreign keys, frequently queried fields
- **Connection Pooling**: 10 base + 20 overflow
- **Query Optimization**: Use of SQLAlchemy's lazy loading
- **Read Replicas**: For heavy read operations

### API Optimization
- **Response Caching**: Redis for frequent queries
- **Pagination**: Default 20, max 100 items
- **Compression**: GZip for responses >1KB
- **Async Operations**: Background tasks for heavy operations

### Blockchain Optimization
- **RPC Caching**: Cache blockchain data
- **Batch Requests**: Combine multiple RPC calls
- **Retry Logic**: Exponential backoff for failures

---

## 🔄 Data Flow Examples

### Transaction Flow
```
1. User initiates swap in mobile app
2. App calls POST /api/v1/user/trade/quote
3. Backend calls 1inch API
4. Backend returns quote to app
5. User confirms
6. App calls POST /api/v1/user/trade/swap
7. Backend creates transaction record (status=PENDING)
8. Backend signs and submits to blockchain
9. Background worker monitors tx_hash
10. Worker updates status to SUCCESS
11. User receives push notification
```

### Earn Flow
```
1. User selects Aave USDC opportunity
2. App calls POST /api/v1/user/earn/deposit
3. Backend validates balance
4. Backend calls Aave contract (deposit)
5. Transaction submitted to blockchain
6. Position record created (status=PENDING)
7. Background worker monitors confirmation
8. Worker updates position (status=ACTIVE)
9. Hourly worker updates APY and earnings
10. User sees updated position in app
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/test_services/test_auth_service.py
def test_create_access_token():
    token = auth_service.create_access_token({"sub": "123"})
    assert token is not None
    
def test_verify_password():
    hashed = auth_service.get_password_hash("password123")
    assert auth_service.verify_password("password123", hashed)
```

### Integration Tests
```python
# tests/test_api/test_trading.py
def test_create_swap(client, auth_headers):
    response = client.post(
        "/api/v1/user/trade/swap",
        json={"from_asset": "USDC", "amount": "50"},
        headers=auth_headers
    )
    assert response.status_code == 200
```

### Load Testing
- **Tool**: Locust or K6
- **Target**: 10,000 concurrent users
- **Metrics**: Response time, error rate, throughput

---

## 📚 Documentation

### API Documentation
- **Swagger UI**: `/docs` (FastAPI auto-generated)
- **ReDoc**: `/redoc` (FastAPI auto-generated)
- **Postman Collection**: Available for testing

### Code Documentation
- **Docstrings**: Google style for all functions
- **Type Hints**: All function signatures
- **Comments**: Complex business logic

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Ready for Implementation ✅
