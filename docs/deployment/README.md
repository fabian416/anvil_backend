# Deployment Documentation

## 📚 Quick Links

### Infrastructure & Docker

- **[INFRASTRUCTURE.md](./INFRASTRUCTURE.md)** - Complete Docker infrastructure guide
  - 27-service architecture overview
  - Quick start (one command to run everything)
  - Service details and access points
  - Operational guide and monitoring
  - Troubleshooting and emergency procedures
  - Production deployment checklist

- **[docker/README.md](./docker/README.md)** - Docker services documentation index
  - Complete service inventory with details
  - Setup and launch guides
  - Configuration and optimization
  - Quick start and common commands
  - 📁 **[docker/SETUP_COMPLETE.md](./docker/SETUP_COMPLETE.md)** - Infrastructure overview
  - 📁 **[docker/LAUNCH.md](./docker/LAUNCH.md)** - Operational guide
  - 📁 **[docker/IMPLEMENTATION_PLAN.md](./docker/IMPLEMENTATION_PLAN.md)** - Technical deep-dive

- **[../../docker/README.md](../../docker/README.md)** - Docker technical reference (root level)
  - Dockerfile reference from docker/ directory
  - Environment configuration
  - Performance optimization
  - Kubernetes conversion

### Environment-Specific Guides

- **[GUEST_CHAT_DEPLOYMENT_RUNBOOK.md](./GUEST_CHAT_DEPLOYMENT_RUNBOOK.md)** - Guest chat feature deployment
- **[GUEST_CHAT_PRODUCTION_CHECKLIST.md](./GUEST_CHAT_PRODUCTION_CHECKLIST.md)** - Production readiness checklist

---

## 🚀 Quick Start

**Start all 27 services with one command:**

```bash
cd /home/lucholeonel/CODE-werify/freelance/anvil_backend
docker-compose -f docker-compose.yaml up -d
```

**Verify everything is running:**

```bash
docker-compose ps
curl http://localhost:8080/health
```

That's it! ✅

---

## 📊 Current Infrastructure Status

**27/27 Services** ✅ All running and healthy

- 3 Core Services (FastAPI, PostgreSQL, Redis)
- 11 Celery Workers (1 general + 9 specialized)
- 11 MCP Servers (blockchain & protocol integrations)
- 2 Supporting Services (Celery Beat, Flower monitoring)
- 1 Utility (TX Confirmation)

---

## 🔗 Related Documentation

See [Main Documentation Index](../README.md) for complete documentation structure.

---

**Last Updated**: January 24, 2026  
**Status**: ✅ Infrastructure fully operational
