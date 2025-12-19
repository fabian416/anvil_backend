# Operations Documentation

**Purpose**: Day-to-day operations, deployment, and monitoring  
**Audience**: DevOps, SRE, Operations team

---

## 📚 Operations Guide Index

### Deployment

- **[Deployment Guide](../deployment/README.md)** - Production deployment procedures
- **[Environment Setup](../getting-started/setup.md)** - Environment configuration
- **[Database Migrations](database-migrations.md)** - Migration procedures

### Monitoring & Observability

- **[Monitoring Guide](monitoring.md)** - Monitoring setup and dashboards
- **[Logging](logging.md)** - Logging configuration
- **[Metrics](metrics.md)** - Metrics collection

### Background Services

- **[Celery Operations](celery.md)** - Celery worker management
- **[Redis Management](redis.md)** - Redis operations
- **[Database Operations](database.md)** - Database management

### Troubleshooting

- **[Troubleshooting Guide](troubleshooting.md)** - Common issues and solutions
- **[Incident Response](incident-response.md)** - Incident handling procedures

### Runbooks

- **[Retry System Runbook](runbooks/retry-system.md)** - Retry system operations
- **[Database Runbook](runbooks/database.md)** - Database operations
- **[Deployment Runbook](runbooks/deployment.md)** - Deployment procedures

---

## 🚀 Quick Reference

### Common Commands

```bash
# Start services
make up.db              # Start PostgreSQL and Redis
make start              # Start FastAPI server

# Background services
make celery.worker      # Start Celery worker
make celery.beat        # Start Celery scheduler
make celery.flower      # Start Flower monitoring

# Database
make init-db            # Initialize database
alembic upgrade head   # Apply migrations

# Code quality
make code.format        # Format code
make code.lint          # Lint code
make code.test          # Run tests
```

---

## 📊 Monitoring

### Health Checks

- **API Health**: `GET /api/v1/guest/health`
- **Database**: Check connection status
- **Redis**: Check connection status
- **Celery**: Check worker status

### Metrics

- **Application Metrics**: Available via `/metrics` endpoint
- **Database Metrics**: PostgreSQL metrics
- **Redis Metrics**: Redis metrics
- **Celery Metrics**: Flower dashboard

---

## 🔧 Configuration

### Environment Variables

Configuration managed via TOML files in `config/{env}/`:

- `config.toml` - Main settings
- `export.toml` - Environment variables
- `.secrets.toml` - Sensitive data

### Generate Configuration

```bash
export APP_ENV=local  # or dev, prod
make dotenv
```

---

## 📖 Related Documentation

- **[Deployment Guide](../deployment/README.md)** - Deployment procedures
- **[Getting Started](../getting-started/README.md)** - Setup guide
- **[Architecture](../architecture/README.md)** - System architecture

---

**Last Updated**: December 19, 2025

