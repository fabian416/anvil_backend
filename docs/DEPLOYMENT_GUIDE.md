```

# 🚀 Deployment Guide - Anvil Backend

**Status**: Production Ready  
**Date**: December 2024  
**Version**: 2.0.0 (with Distillation + Projects)  

---

## 📋 Prerequisites

### Required Services
- ✅ PostgreSQL 14+ (with `pgvector` extension)
- ✅ Redis 6+ (for Celery + caching)
- ✅ Python 3.12+ (strictly enforced)

### Required Extensions
```sql
-- In your PostgreSQL database:
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
```

---

## 🏗️ Step-by-Step Deployment

### Step 1: Database Setup (5 minutes)

#### 1.1: Start PostgreSQL
```bash
# Using Docker Compose (recommended)
make up.db

# Or start manually if already configured
```

#### 1.2: Run Migrations
```bash
# Apply all migrations (creates 18 tables)
alembic upgrade head
```

**Expected output**:
```
INFO  [alembic.runtime.migration] Running upgrade -> 20251201_001, add distillation system
INFO  [alembic.runtime.migration] Running upgrade 20251201_001 -> 20251201_002, add projects system
```

**Verify**:
```sql
-- Should show 18 new tables
\dt

-- Key tables:
-- Distillation: 7 tables
-- Projects: 11 tables
```

---

### Step 2: Seed Initial Data (2 minutes)

#### 2.1: Run Seed Script
```bash
python scripts/seed_data.py
```

**Expected output**:
```
🚀 Starting seed data script...

🌱 Seeding distillation configuration...
  ✅ Created default distillation configuration

🌱 Seeding static response templates...
  ✅ Created 3 static response templates

🔍 Verifying default projects...
  ✅ Found 10 projects:
      - General DeFi (general-defi) [active]
      - Yield Farming (yield-farming) [active]
      - Risk Analysis (risk-analysis) [active]
      - Trading Pro (trading-pro) [active]
      - Portfolio Manager (portfolio-manager) [active]
      ... and 5 more

✅ Seed data complete!
```

---

### Step 3: Environment Configuration (3 minutes)

#### 3.1: Verify Environment Variables
```bash
# Check APP_ENV is set
echo $APP_ENV  # Should be: local, dev, or prod

# Check TOML config exists
ls -la config/$APP_ENV/config.toml
ls -la config/$APP_ENV/.secrets.toml
```

#### 3.2: Required Configuration
**File**: `config/local/config.toml` (or `dev`/`prod`)

```toml
[database]
host = "localhost"
port = 5432
name = "anvil_db"
user = "postgres"
password = "postgres"

[redis]
host = "localhost"
port = 6379
db = 0

[celery]
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"

[openai]
api_key = "your-openai-api-key"  # Required for agents

[stripe]
secret_key = "your-stripe-key"  # If using subscriptions
```

**File**: `config/local/.secrets.toml` (not tracked in git)

```toml
[openai]
api_key = "sk-..."

[stripe]
secret_key = "sk_test_..."
```

---

### Step 4: Start Services (5 minutes)

#### 4.1: Terminal 1 - FastAPI Server
```bash
make start

# Or manually:
uvicorn app.run:make_app --factory --port 8000 --reload
```

**Expected output**:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify**:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

---

#### 4.2: Terminal 2 - Celery Worker
```bash
make celery.worker

# Or manually:
celery -A app.infrastructure.celery.app:celery_app worker --loglevel=info
```

**Expected output**:
```
 -------------- celery@hostname v5.3.4
---- **** ----- 
--- * ***  * -- [Configuration]
-- * - **** --- .> app: baseapi_hexagonal:0x...
- ** ---------- .> transport: redis://localhost:6379/0
- ** ---------- .> results:   redis://localhost:6379/1
- *** --- * --- .> concurrency: 8 (prefork)
-- ******* ---- .> task events: OFF
--- ***** ----- 

[tasks]
  . aggregate_distillation_telemetry
  . aggregate_project_analytics
  . cache_llm_response
  . check_knowledge_base_health
  . cleanup_expired_cache
  . cleanup_expired_password_resets
  . cleanup_expired_sessions
  . evaluate_auto_assignment_rules
  . process_agent_response
  . reindex_knowledge_base
  . update_agent_stats

[2024-12-02 00:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2024-12-02 00:00:00,000: INFO/MainProcess] celery@hostname ready.
```

---

#### 4.3: Terminal 3 - Celery Beat (Scheduler)
```bash
make celery.beat

# Or manually:
celery -A app.infrastructure.celery.app:celery_app beat --loglevel=info
```

**Expected output**:
```
celery beat v5.3.4 is starting.
__    -    ... __   -        _
LocalTime -> 2024-12-02 00:00:00
Configuration ->
    . broker -> redis://localhost:6379/0
    . loader -> celery.loaders.app.AppLoader
    . scheduler -> celery.beat.PersistentScheduler

[schedules]
  aggregate-distillation-telemetry   :  crontab(minute=5)
  aggregate-project-analytics        :  crontab(hour=4, minute=0)
  check-knowledge-base-health        :  crontab(hour=5, minute=0, day_of_week=0)
  cleanup-expired-cache              :  crontab(hour=3, minute=0)
  cleanup-expired-password-resets    :  crontab(minute=0)
  cleanup-expired-sessions           :  crontab(hour=0, minute=0)
  update-agent-stats                 :  crontab(minute='*/5')

beat: Starting...
```

---

#### 4.4: Terminal 4 - Flower (Monitoring UI)
```bash
make celery.flower

# Or manually:
celery -A app.infrastructure.celery.app:celery_app flower
```

**Expected output**:
```
[I 2024-12-02 00:00:00,000] Flower started on http://0.0.0.0:5555
```

**Access**: `http://localhost:5555`

---

### Step 5: Verify Deployment (5 minutes)

#### 5.1: Check API Documentation
```bash
# Visit Swagger UI
open http://localhost:8000/docs
```

**Expected**: You should see **50+ endpoints** including:
- `/api/v1/admin/distillation/*` (8 endpoints)
- `/api/v1/admin/projects/*` (14 endpoints)
- `/api/v1/projects/*` (5 endpoints)
- Plus all existing endpoints

---

#### 5.2: Test Distillation Config
```bash
curl http://localhost:8000/api/v1/admin/distillation/config
```

**Expected response**:
```json
{
  "enabled": true,
  "cache_enabled": true,
  "static_responses_enabled": true,
  "semantic_cache_enabled": true,
  "min_confidence_threshold": 0.7,
  "semantic_similarity_threshold": 0.85,
  "max_classification_latency_ms": 500
}
```

---

#### 5.3: Test Projects List
```bash
curl http://localhost:8000/api/v1/admin/projects/
```

**Expected response**: JSON array with 10 projects

---

#### 5.4: Test Static Responses
```bash
curl http://localhost:8000/api/v1/admin/distillation/static-responses
```

**Expected response**: JSON array with 3 static responses

---

#### 5.5: Check Celery Tasks
Visit `http://localhost:5555` (Flower UI)

**Expected**:
- **Registered tasks**: 11 tasks visible
- **Beat schedule**: 7 periodic tasks shown
- **Workers**: At least 1 worker online

---

#### 5.6: Test Background Task
```bash
# Manually trigger a task
python -c "from app.infrastructure.celery.tasks import cleanup_expired_cache; cleanup_expired_cache.delay()"
```

**Check Flower**: Task should appear in "Tasks" tab

---

## 📊 Health Checks

### API Health
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Database Health
```bash
# Check connection
curl http://localhost:8000/api/v1/general/health
```

### Celery Health
```bash
# Check worker is responsive
celery -A app.infrastructure.celery.app:celery_app inspect active
```

### Redis Health
```bash
redis-cli ping
# Expected: PONG
```

---

## 🐛 Troubleshooting

### Issue 1: Migrations Fail
**Error**: `sqlalchemy.exc.ProgrammingError: ... pgvector extension not found`

**Solution**:
```sql
-- Connect to your database
psql -U postgres -d anvil_db

-- Install extensions
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Retry migrations
alembic upgrade head
```

---

### Issue 2: Celery Won't Start
**Error**: `kombu.exceptions.OperationalError: ... Connection refused`

**Solution**:
```bash
# Check Redis is running
redis-cli ping

# Start Redis if needed
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

---

### Issue 3: API Returns 500 Errors
**Error**: `Internal Server Error` on any endpoint

**Solution**:
```bash
# Check logs
tail -f logs/app.log

# Common issues:
# 1. Database not migrated: run `alembic upgrade head`
# 2. Missing config: check `config/local/config.toml`
# 3. Wrong APP_ENV: export APP_ENV=local
```

---

### Issue 4: Seed Script Fails
**Error**: `No module named 'app'`

**Solution**:
```bash
# Ensure you're in project root
cd /home/ubuntu/anvil_backend

# Run with correct path
PYTHONPATH=src python scripts/seed_data.py
```

---

### Issue 5: OpenAI API Errors
**Error**: `Authentication error` or `Invalid API key`

**Solution**:
```toml
# Add to config/local/.secrets.toml
[openai]
api_key = "sk-your-actual-key-here"
```

---

## 🔐 Production Deployment

### Additional Steps for Production

#### 1. Security
```toml
# config/prod/.secrets.toml
[database]
password = "strong-random-password"

[jwt]
secret_key = "random-256-bit-key"

[stripe]
secret_key = "sk_live_..."
```

#### 2. Gunicorn (Production Server)
```bash
# Replace uvicorn with gunicorn
gunicorn app.run:make_app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

#### 3. Celery with Supervisor
```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery-worker]
command=/path/to/venv/bin/celery -A app.infrastructure.celery.app:celery_app worker
directory=/path/to/anvil_backend
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/worker.err.log
stdout_logfile=/var/log/celery/worker.out.log

[program:celery-beat]
command=/path/to/venv/bin/celery -A app.infrastructure.celery.app:celery_app beat
directory=/path/to/anvil_backend
user=ubuntu
autostart=true
autorestart=true
stderr_logfile=/var/log/celery/beat.err.log
stdout_logfile=/var/log/celery/beat.out.log
```

#### 4. Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name api.anvil.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 5. SSL with Let's Encrypt
```bash
sudo certbot --nginx -d api.anvil.com
```

---

## 📈 Monitoring & Observability

### Celery Flower
- **URL**: `http://localhost:5555`
- **Monitors**: Task execution, worker status, beat schedule
- **Alerts**: Failed tasks, slow tasks

### Prometheus Metrics
```bash
# Add to FastAPI app
from prometheus_fastapi_instrumentator import Instrumentator

app = make_app()
Instrumentator().instrument(app).expose(app)
```

### Logging
```python
# Logs location
logs/
  app.log          # Application logs
  celery.log       # Celery worker logs
  access.log       # HTTP access logs
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] PostgreSQL running with extensions installed
- [ ] Redis running
- [ ] Environment variables configured
- [ ] Secrets configured (`.secrets.toml`)
- [ ] Dependencies installed (`uv pip install -e '.[dev,test]'`)

### Deployment
- [ ] Migrations applied (`alembic upgrade head`)
- [ ] Seed data loaded (`python scripts/seed_data.py`)
- [ ] API server started (`make start`)
- [ ] Celery worker started (`make celery.worker`)
- [ ] Celery beat started (`make celery.beat`)
- [ ] Flower started (`make celery.flower`)

### Verification
- [ ] API docs accessible (`http://localhost:8000/docs`)
- [ ] Health endpoint returns 200 (`/health`)
- [ ] Distillation config returns data (`/api/v1/admin/distillation/config`)
- [ ] Projects list returns 10 items (`/api/v1/admin/projects/`)
- [ ] Celery tasks visible in Flower (`http://localhost:5555`)
- [ ] Background tasks executing (check Flower logs)

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Check Celery task success rate
- [ ] Verify database connections
- [ ] Test critical API endpoints
- [ ] Set up alerts for failures

---

## 🚀 Quick Start (TL;DR)

```bash
# 1. Migrations
alembic upgrade head

# 2. Seed data
python scripts/seed_data.py

# 3. Start services (4 terminals)
make start           # Terminal 1
make celery.worker   # Terminal 2
make celery.beat     # Terminal 3
make celery.flower   # Terminal 4

# 4. Verify
open http://localhost:8000/docs
open http://localhost:5555
```

---

## 📞 Support

**Documentation**:
- [NEXT_STEPS.md](./NEXT_STEPS.md) - Implementation roadmap
- [docs/steering/](./docs/steering/) - Architecture docs

**Issues**: Check logs in `logs/` directory

**Questions**: Review Swagger UI at `/docs`

---

**Status**: ✅ Deployment guide complete! Follow these steps to get your system running! 🚀
