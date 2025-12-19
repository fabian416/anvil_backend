# Development Environment Setup

**Time Required**: 20-30 minutes  
**Prerequisites**: Python 3.12, Docker, Git

---

## Quick Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd anvil_backend

# 2. Set environment
export APP_ENV=local

# 3. Generate configuration
make dotenv

# 4. Setup virtual environment
make venv

# 5. Install dependencies
make clean-install

# 6. Start services (PostgreSQL, Redis)
make up.db

# 7. Initialize database
make init-db

# 8. Start application
make start
```

The application will be available at `http://localhost:8000`

---

## Detailed Setup

### 1. Prerequisites

#### Required Software

- **Python 3.12.*** (strictly enforced)
- **Docker & Docker Compose** (for local services)
- **Git** (latest version)
- **Make** (for automation)

#### Verify Prerequisites

```bash
python3.12 --version  # Should show 3.12.x
docker --version       # Should be installed
docker-compose --version
git --version
make --version
```

### 2. Environment Configuration

#### Set Environment Variable

```bash
export APP_ENV=local  # Options: local, dev, prod
```

#### Generate Configuration Files

```bash
make dotenv  # Creates .env.{APP_ENV} in config/{APP_ENV}/
```

This generates:
- `config/local/.env.local` - Environment variables
- Configuration from TOML files

### 3. Virtual Environment

#### Create Virtual Environment

```bash
make venv  # Creates .venv directory
```

Or manually:
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 4. Install Dependencies

#### Install All Dependencies

```bash
make clean-install  # Installs all dependencies including dev/test
```

Or manually:
```bash
source .venv/bin/activate
pip install -e '.[dev,test]'
```

### 5. Database Setup

#### Start PostgreSQL

```bash
make up.db  # Starts PostgreSQL in Docker
```

#### Initialize Database

```bash
make init-db  # Creates database and tables
```

Or manually:
```bash
make create-db        # Create database
alembic upgrade head  # Apply migrations
```

### 6. Redis Setup

Redis is started automatically with `make up.db`. If needed separately:

```bash
docker-compose -f config/local/docker-compose.yaml up -d redis
```

### 7. Start Application

#### Development Server

```bash
make start  # Starts with auto-reload on port 8000
```

Or manually:
```bash
source .venv/bin/activate
PYTHONPATH=src python3.12 -m uvicorn app.run:make_app --factory --port 8000 --reload
```

#### Verify Installation

```bash
# Check API documentation
curl http://localhost:8000/docs

# Check health endpoint
curl http://localhost:8000/health
```

---

## Background Services

### Celery Worker

```bash
make celery.worker  # Start Celery worker
```

### Celery Beat (Scheduler)

```bash
make celery.beat  # Start Celery scheduler
```

### Flower (Monitoring)

```bash
make celery.flower  # Start Flower UI (port 5555)
```

Access at: `http://localhost:5555`

---

## Configuration

### Environment Variables

Configuration is managed via TOML files in `config/{env}/`:

- `config.toml` - Main application settings
- `export.toml` - Fields to export to .env
- `.secrets.toml` - Sensitive data (not tracked in git)

### Generate .env Files

```bash
make dotenv  # Generates .env.{APP_ENV} from TOML config
```

### Required Environment Variables

- `APP_ENV` - Environment name (local, dev, prod)
- `POSTGRES_*` - Database connection (from TOML)
- `REDIS_URL` - Redis connection (from TOML)
- `JWT_SECRET` - JWT signing secret (from TOML)
- API keys for external services (from TOML)

---

## Verification

### Check Installation

```bash
# 1. Verify Python version
python3.12 --version

# 2. Verify dependencies
pip list | grep fastapi
pip list | grep sqlalchemy

# 3. Verify database connection
make check-db  # If available

# 4. Verify application starts
make start
# Should see: "Application startup complete"
```

### Run Tests

```bash
make code.test  # Run all tests
```

---

## Troubleshooting

### Common Issues

#### Issue: `ModuleNotFoundError`

**Solution**: Ensure virtual environment is activated and dependencies are installed:
```bash
source .venv/bin/activate
make clean-install
```

#### Issue: Database connection error

**Solution**: Ensure PostgreSQL is running:
```bash
make up.db
make init-db
```

#### Issue: Port already in use

**Solution**: Change port or stop conflicting service:
```bash
# Change port in Makefile or use:
uvicorn app.run:make_app --factory --port 8001 --reload
```

#### Issue: Configuration errors

**Solution**: Regenerate configuration:
```bash
make dotenv
```

---

## Next Steps

After setup is complete:

1. **[Architecture Overview](../architecture/README.md)** - Understand the system
2. **[Developer Guide](../developer/README.md)** - Start developing
3. **[API Reference](../api/README.md)** - Explore the API
4. **[Testing Guide](../testing/README.md)** - Write tests

---

**Need Help?** See [Troubleshooting Guide](../reference/troubleshooting.md)

