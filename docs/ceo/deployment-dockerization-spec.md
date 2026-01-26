# Complete Dockerization & CI/CD Deployment Specification

> **Framework:** MIT Systems Thinking + Stanford Design Thinking + First Principles Analysis
> **Agents:** @deployment-specialist + @backend-engineer
> **Status:** Phase 1 - Analysis Complete | Phase 2 - Solution Design | GitHub Actions Optimized
> **Date:** 2026-01-26 (Updated)

---

## Executive Summary

**Problem:** The current deployment architecture has significant gaps between development (`make start-dev`) and production (Docker). Only 4 of 11 MCP servers are containerized, GitHub Actions references outdated tooling, and there's no environment parity between local development and production deployments.

**Impact:**
- 🔴 **Production Risk**: Missing 7 MCP servers in containerized deployment
- 🟡 **Developer Experience**: Manual process orchestration with `start_dev.sh`
- 🟢 **CI/CD Reliability**: ✅ **FULLY OPTIMIZED** - All workflows use uv, path filters, concurrency limits (77% usage reduction)
- 🟢 **Security**: Existing security scans and health checks

**Recommended Solution:** Multi-stage Docker architecture with complete service orchestration, GitHub Actions modernization, and environment-specific configuration management.

---

## 📚 Phase 1: Problem Decomposition & Root Cause Analysis

### 1.1 Current State Assessment

#### ✅ **What Works**
- **Development Script (`scripts/start_dev.sh`)**: Successfully orchestrates all 11 services
  - FastAPI (port 8080)
  - 11 MCP servers (ports 8081-8091)
  - Celery workers (light: 1 worker, full: 9 specialized workers)
  - Celery Beat scheduler
  - Flower monitoring UI (port 5555)
  - Proper signal handling and cleanup
  - Health checks and status monitoring

- **Existing Docker Infrastructure**:
  - PostgreSQL 16 with health checks
  - Redis 7 with health checks
  - FastAPI application with multi-stage build
  - Celery worker and beat services
  - Flower monitoring
  - Transaction confirmation worker (profile-based)

- **GitHub Actions CI/CD** ✅ **RECENTLY OPTIMIZED (2026-01-26)**:
  - ✅ Using `uv` for dependency management (not Poetry)
  - ✅ Path filters (workflows only run when relevant files change)
  - ✅ Concurrency limits (cancel in-progress runs on new commits)
  - ✅ Optimized frequency (coverage weekly vs daily)
  - ✅ Lint, test, security scanning pipeline
  - ✅ 77% reduction in GitHub Actions usage (885 → 200 min/week)
  - ✅ Deleted 3 duplicate workflows (ci.yml, tests.yml, pre-commit-api-docs.yml)
  - ❌ No Docker build/push workflows for MCP servers yet
  - ❌ No Kubernetes deployment automation yet

#### ❌ **Critical Gaps**

**1. Incomplete MCP Server Dockerization**
```bash
# Current: docker-compose-mcp.yml
✅ mcp_oneinch (port 8081)
✅ mcp_defillama (port 8082)
✅ mcp_thegraph (port 8083)
✅ mcp_coingecko (port 8084)
❌ mcp_aave (port 8085)          # MISSING
❌ mcp_portfolio (port 8086)     # MISSING
❌ mcp_perplexity (port 8087)    # MISSING
❌ mcp_morpho (port 8088)        # MISSING
❌ mcp_curve (port 8089)         # MISSING
❌ mcp_hyperliquid (port 8090)   # MISSING
❌ mcp_layerzero (port 8091)     # MISSING
```

**2. Development vs Production Parity**
- `make start-dev` runs all 11 MCP servers ✅
- Docker Compose only runs 4 MCP servers ❌
- Different port exposure strategies
- Different process management approaches

**3. GitHub Actions Remaining Gaps** ✅ **PARTIALLY RESOLVED (2026-01-26)**
- ✅ **FIXED**: Now using `uv` (not Poetry)
- ✅ **FIXED**: Path filters added (only run on code changes)
- ✅ **FIXED**: Concurrency limits implemented
- ✅ **FIXED**: Reduced workflow frequency (77% usage reduction)
- ❌ **REMAINING**: Missing Docker build/push workflows for MCP servers
- ❌ **REMAINING**: No multi-architecture builds (amd64/arm64)
- ❌ **REMAINING**: No automated Kubernetes deployment
- ❌ **REMAINING**: Hardcoded credentials (need GitHub Secrets migration)
- ❌ **REMAINING**: No comprehensive E2E deployment health checks

**4. Configuration Management**
- TOML-based config ✅
- Environment-specific secrets ✅
- But: Docker env var mapping incomplete
- Missing: Secret rotation strategy
- Missing: Runtime config validation

### 1.2 Root Cause Identification

#### **Essential Problem**
The MCP server containerization was implemented incrementally (4 of 11 servers) and never completed. ~~GitHub Actions workflow hasn't been updated to reflect the transition from Poetry to uv~~ ✅ **RESOLVED (2026-01-26)** - workflows now use uv with path filters and concurrency optimization. **REMAINING**: Docker build/push workflows for MCP servers and automated Kubernetes deployment.

#### **Causal Chain**
```
Initial Prototype (4 MCP servers)
    ↓
Development shifted to start_dev.sh (all 11 servers)
    ↓
Docker Compose never updated to match
    ↓
GitHub Actions still references old tooling ← ✅ PARTIALLY FIXED (2026-01-26)
    ↓                                           (uv, path filters, concurrency)
Production deployment incomplete ← 🚧 IN PROGRESS
    ↓
Missing: Docker build workflows for MCP servers
Missing: Automated K8s deployment
```

#### **System Invariants**
- All MCP servers share the same FastAPI + Python 3.12 runtime
- Each MCP server is an independent module with its own port
- All servers require PYTHONPATH=src configuration
- Environment variables for API keys vary by service
- Health check pattern: `GET /health` on each port

### 1.3 Solution Space Mapping

#### **Design Degrees of Freedom**
1. **MCP Server Deployment Strategy**
   - Option A: Monolithic (all MCP servers in one container)
   - Option B: Separate containers per MCP server
   - Option C: Grouped containers (core vs advanced)
   - Option D: Dynamic service mesh with auto-discovery

2. **Orchestration Approach**
   - Option A: Docker Compose (development + simple production)
   - Option B: Kubernetes (enterprise production)
   - Option C: Hybrid (Docker Compose + Kubernetes manifests)

3. **CI/CD Strategy**
   - Option A: GitHub Actions only
   - Option B: Multi-cloud (GitHub Actions + GitLab CI)
   - Option C: External CI/CD (Jenkins, CircleCI)

#### **Hard Constraints**
- ✅ Must use Python 3.12
- ✅ Must use uv for dependency management
- ✅ Must support PostgreSQL 16 + Redis 7
- ✅ Must maintain hexagonal architecture principles
- ✅ Must support environment-specific configuration (local/dev/prod)
- ✅ Must include health checks for all services
- ✅ Must support graceful shutdown

#### **Soft Constraints**
- 🟡 Prefer Docker Compose for simplicity (can migrate to K8s later)
- 🟡 Prefer separate containers for better isolation
- 🟡 Prefer GitHub Actions (already in use)
- 🟡 Balance between resource usage and isolation
- 🟡 Optimize for developer experience

---

## 🎯 Phase 2: Solution Generation & Trade-off Analysis

### 2.1 Solution Divergence

#### **Solution A: Separate Container Per MCP Server** ⭐ RECOMMENDED
**Architecture:**
```yaml
services:
  fastapi:          # Main application
  postgres:         # Database
  redis:            # Cache/Broker
  celery_worker:    # Background tasks
  celery_beat:      # Scheduler
  flower:           # Monitoring
  mcp_oneinch:      # MCP Server 1
  mcp_defillama:    # MCP Server 2
  ...               # (11 total MCP services)
  mcp_layerzero:    # MCP Server 11
```

**Benefits:**
- ✅ Perfect isolation (crash in one MCP doesn't affect others)
- ✅ Independent scaling (scale popular MCP servers)
- ✅ Easy debugging (dedicated logs per service)
- ✅ Matches development environment exactly
- ✅ Simple health check per service
- ✅ Easier to add/remove MCP servers

**Drawbacks:**
- ❌ More containers (resource overhead)
- ❌ Longer startup time (11 containers)
- ❌ More complex docker-compose.yml

**Implementation Complexity:** Medium  
**Resource Usage:** High (11 Python processes)  
**Operational Complexity:** Low

---

#### **Solution B: Monolithic MCP Server Container**
**Architecture:**
```yaml
services:
  fastapi:          # Main application
  postgres:         # Database
  redis:            # Cache/Broker
  celery_worker:    # Background tasks
  celery_beat:      # Scheduler
  flower:           # Monitoring
  mcp_all:          # ALL 11 MCP servers in one container
```

**Benefits:**
- ✅ Fewer containers (lower resource overhead)
- ✅ Faster startup (single container)
- ✅ Simpler docker-compose.yml
- ✅ Easier port management

**Drawbacks:**
- ❌ No isolation (one crash kills all MCP servers)
- ❌ Can't scale individual MCP servers
- ❌ Complex process management inside container
- ❌ Harder debugging (mixed logs)
- ❌ Doesn't match development environment

**Implementation Complexity:** High (need supervisord/systemd)  
**Resource Usage:** Medium (1 container, 11 processes)  
**Operational Complexity:** High

---

#### **Solution C: Grouped MCP Containers**
**Architecture:**
```yaml
services:
  fastapi:          # Main application
  postgres:         # Database
  redis:            # Cache/Broker
  celery_worker:    # Background tasks
  celery_beat:      # Scheduler
  flower:           # Monitoring
  mcp_core:         # Core MCP servers (6 servers)
  mcp_advanced:     # Advanced MCP servers (5 servers)
```

**Benefits:**
- ✅ Balance between isolation and resource usage
- ✅ Logical grouping (core vs advanced)
- ✅ Moderate resource overhead
- ✅ Simpler than 11 containers

**Drawbacks:**
- ❌ Still requires process management
- ❌ Partial isolation only
- ❌ Arbitrary grouping (what's "core" vs "advanced"?)
- ❌ Doesn't match development environment

**Implementation Complexity:** Medium-High  
**Resource Usage:** Medium  
**Operational Complexity:** Medium-High

---

### 2.2 Multi-Dimensional Trade-off Matrix

| Criterion | Solution A (Separate) | Solution B (Monolithic) | Solution C (Grouped) |
|-----------|----------------------|-------------------------|---------------------|
| **Isolation** | ⭐⭐⭐⭐⭐ Perfect | ⭐ None | ⭐⭐⭐ Partial |
| **Resource Efficiency** | ⭐⭐ High overhead | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Good |
| **Development Parity** | ⭐⭐⭐⭐⭐ Exact match | ⭐⭐ Different | ⭐⭐⭐ Close |
| **Debugging** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐ Hard | ⭐⭐⭐ Moderate |
| **Scalability** | ⭐⭐⭐⭐⭐ Per-service | ⭐ All-or-nothing | ⭐⭐⭐ Per-group |
| **Operational Complexity** | ⭐⭐⭐⭐ Simple | ⭐⭐ Complex | ⭐⭐⭐ Moderate |
| **Implementation Time** | ⭐⭐⭐⭐ ~2-3 days | ⭐⭐⭐ ~3-4 days | ⭐⭐⭐ ~3-4 days |
| **Maintenance** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐ Hard | ⭐⭐⭐ Moderate |

**🏆 WINNER: Solution A (Separate Containers)**
- Best alignment with development environment
- Best isolation and debugging
- Best scalability
- Acceptable resource overhead (modern servers can handle 11 Python processes)
- Lowest long-term maintenance burden

### 2.3 Constraint Priority Framework

**Priority 1: Correctness & Reliability**
- ✅ All 11 MCP servers must be containerized
- ✅ Must match development environment behavior
- ✅ Must have independent health checks

**Priority 2: Developer Experience**
- ✅ Easy local development (`docker compose up`)
- ✅ Clear logs per service
- ✅ Fast iteration cycles

**Priority 3: Operational Excellence**
- ✅ Simple deployment process
- ✅ Easy debugging in production
- ✅ Independent scaling capabilities

**Priority 4: Resource Efficiency**
- 🟡 Optimize container images (multi-stage builds)
- 🟡 Share base layers where possible
- 🟡 Acceptable: 11 containers vs 1 monolith

---

## ⚠️ Phase 3: Risk Assessment & Validation Design

### 3.1 Cognitive Limitation Analysis

**This analysis may overlook:**
- Network latency between containers in production
- MCP server startup race conditions
- Port conflicts in different deployment environments
- Secret management complexity at scale
- Log aggregation at 11+ service scale

**The solution assumes:**
- Modern container orchestration handles 11 services easily
- Each MCP server is truly stateless and independent
- Network performance between containers is acceptable
- Docker Compose is sufficient for production (or easy migration to K8s)
- Health check endpoints are reliable

**Areas requiring further validation:**
- Load testing with all 11 MCP servers under concurrent requests
- Network latency measurement between FastAPI ↔ MCP servers
- Resource usage monitoring (CPU, memory, network I/O)
- Startup time optimization (parallel vs sequential)
- Failover behavior when individual MCP servers crash

### 3.2 Technical Debt Assessment

**Immediate Implementation Compromises:**
1. **Docker Image Size**: Using full Python 3.12 image (not distroless)
   - **Impact:** Larger attack surface, slower pulls
   - **Mitigation:** Plan for distroless migration in Phase 2
   - **Timeline:** Q2 2026

2. **Secrets Management**: Using `.env` files (not Vault/AWS Secrets Manager)
   - **Impact:** Manual secret rotation, potential exposure
   - **Mitigation:** Document rotation procedures, plan Vault integration
   - **Timeline:** Q3 2026

3. **Monitoring**: Basic health checks only (no Prometheus/Grafana)
   - **Impact:** Limited observability in production
   - **Mitigation:** Add `/metrics` endpoints in Phase 2
   - **Timeline:** Q2 2026

**Long-term Architectural Impact:**
- Kubernetes migration path remains open (same container structure)
- Service mesh integration possible (Istio/Linkerd)
- Auto-scaling capabilities limited by Docker Compose

**Maintenance Cost Projection:**
- **Low Complexity**: Adding new MCP servers (copy-paste pattern)
- **Medium Complexity**: Upgrading Python dependencies (rebuild all images)
- **High Complexity**: Migrating to Kubernetes (re-architect orchestration)

### 3.3 Validation & Testing Strategy

#### **Success Criteria**
1. **Functional Requirements**
   - [ ] All 11 MCP servers start successfully
   - [ ] Each MCP server responds to health checks
   - [ ] FastAPI can communicate with all MCP servers
   - [ ] Celery workers can access MCP servers
   - [ ] All services shut down gracefully

2. **Performance Requirements**
   - [ ] Startup time < 60 seconds (all services)
   - [ ] Health check response < 100ms per service
   - [ ] MCP server API latency < 200ms (p99)
   - [ ] Memory usage < 4GB total (11 MCP services)

3. **Reliability Requirements**
   - [ ] Individual MCP server crash doesn't affect others
   - [ ] Automatic restart on failure (Docker restart policy)
   - [ ] Zero data loss on graceful shutdown
   - [ ] Health checks detect failures within 10 seconds

#### **Testing Phases**

**Phase 1: Local Development Testing**
```bash
# Test 1: Clean startup
docker compose down -v
docker compose up --build

# Test 2: Health checks
for port in {8081..8091}; do
  curl http://localhost:$port/health
done

# Test 3: Service isolation
docker compose stop mcp_oneinch
# Verify other MCP servers still respond

# Test 4: Graceful shutdown
docker compose down
# Verify no errors in logs
```

**Phase 2: Integration Testing**
```bash
# Test 1: FastAPI → MCP communication
pytest tests/integration/test_mcp_integration.py

# Test 2: Celery → MCP communication
pytest tests/integration/test_celery_mcp.py

# Test 3: Load testing
locust -f tests/load/mcp_load_test.py --users 100 --spawn-rate 10
```

**Phase 3: Production Validation**
```bash
# Test 1: Staging deployment
kubectl apply -f k8s/staging/
kubectl rollout status deployment/mcp-servers -n staging

# Test 2: Smoke tests
curl https://staging.api.example.com/health
curl https://staging.api.example.com/health/mcp

# Test 3: Canary deployment
# Deploy to 10% of production traffic
# Monitor error rates for 1 hour
# Rollback if error rate > 0.1%
```

#### **Error Detection & Rollback Mechanisms**

**1. Health Check Failures**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

**2. Automated Rollback Triggers**
- Health check failure rate > 10%
- Startup time > 120 seconds
- Memory usage > 8GB (threshold)
- Error rate spike > 5% increase

**3. Manual Rollback Procedure**
```bash
# GitHub Actions: revert to previous Docker image
git revert HEAD
git push origin master

# Kubernetes: rollback deployment
kubectl rollout undo deployment/mcp-servers -n production

# Docker Compose: use previous tag
docker compose pull --tag previous
docker compose up -d
```

---

## 🚀 Implementation Plan

### Phase 1: Complete Docker Compose Configuration (Week 1)

**Task 1.1: Update docker-compose-mcp.yml**
- Add 7 missing MCP server services
- Standardize configuration across all 11 services
- Add health checks to all MCP services
- Configure proper restart policies

**Task 1.2: Create Unified docker-compose.yml**
- Merge main app + MCP servers into single file
- Add service dependencies (app depends on MCP servers)
- Configure shared network
- Add volume mounts for development

**Task 1.3: Environment Configuration**
- Create `.env.local`, `.env.dev`, `.env.prod`
- Map all TOML config values to environment variables
- Document required secrets per environment
- Create secret templates

**Deliverables:**
- ✅ `config/local/docker-compose.yml` (complete, all services)
- ✅ `config/prod/docker-compose.yml` (production-ready)
- ✅ `.env.example` with all required variables
- ✅ `docs/DOCKER_SETUP.md` (setup guide)

---

### Phase 2: GitHub Actions Modernization ✅ **PARTIALLY COMPLETE (2026-01-26)**

**Task 2.1: Update CI Workflow** ✅ **PARTIALLY COMPLETE**
```yaml
# Active Workflows (optimized 2026-01-26):
✅ test.yml - Using uv, path filters, concurrency limits
✅ api-docs-validation.yml - Concurrency added
✅ security-scan-pr.yml - Path filters + concurrency
✅ security-scan-weekly.yml - Concurrency added
✅ performance.yml - Concurrency added
✅ coverage-report.yml - Weekly schedule (86% reduction)

# Remaining Work:
❌ Add Docker build/push workflows for MCP servers
❌ Multi-architecture builds (amd64, arm64)
❌ Automated deployment workflows (staging/production)
❌ E2E health checks post-deployment
```

**Task 2.2: Secrets Management**
- Migrate Docker Hub credentials to GitHub Secrets
- Add environment-specific secret templates
- Document secret rotation procedures
- Add secret validation step

**Task 2.3: Deployment Automation**
```yaml
# .github/workflows/deploy.yml
- Automated staging deployment
- Smoke tests after deployment
- Canary deployment for production
- Automated rollback on failure
```

**Deliverables:**
- ✅ `.github/workflows/ci.yml` (modernized)
- ✅ `.github/workflows/deploy-staging.yml`
- ✅ `.github/workflows/deploy-production.yml`
- ✅ `docs/CI_CD_GUIDE.md`

---

### Phase 3: Kubernetes Manifests (Week 3-4)

**Task 3.1: Create Kubernetes Resources**
```yaml
# k8s/base/
- deployment.yaml (FastAPI)
- deployment-mcp-*.yaml (11 MCP servers)
- service.yaml (LoadBalancer)
- configmap.yaml (configuration)
- secret.yaml (credentials)
```

**Task 3.2: Kustomize Overlays**
```yaml
# k8s/overlays/staging/
# k8s/overlays/production/
- Different resource limits
- Different replica counts
- Different ingress configurations
```

**Task 3.3: Observability**
- Add Prometheus ServiceMonitor
- Configure Grafana dashboards
- Set up alerting rules
- Add distributed tracing

**Deliverables:**
- ✅ `k8s/` directory with all manifests
- ✅ Helm chart (optional, advanced)
- ✅ `docs/KUBERNETES_DEPLOYMENT.md`
- ✅ Grafana dashboard JSON

---

## 📋 Appendix

### A. MCP Server Configuration Matrix

| Server | Port | Required Env Vars | External APIs | Critical? |
|--------|------|------------------|---------------|-----------|
| 1inch | 8081 | `ONEINCH_API_KEY` | 1inch Aggregator API | High |
| DeFiLlama | 8082 | None | DeFiLlama Public API | High |
| TheGraph | 8083 | `THEGRAPH_API_KEY` | The Graph Network | High |
| CoinGecko | 8084 | `COINGECKO_API_KEY` | CoinGecko API | High |
| Aave | 8085 | `AAVE_RPC_URL` | Ethereum RPC | Medium |
| Portfolio | 8086 | `PORTFOLIO_DB_URL` | Internal DB | Medium |
| Perplexity | 8087 | `PERPLEXITY_API_KEY` | Perplexity AI API | Low |
| Morpho | 8088 | `MORPHO_API_KEY` | Morpho Protocol API | Medium |
| Curve | 8089 | `CURVE_API_URL` | Curve Finance API | Medium |
| Hyperliquid | 8090 | `HYPERLIQUID_API_KEY` | Hyperliquid API | Low |
| LayerZero | 8091 | `LAYERZERO_API_KEY` | LayerZero API | Low |

### B. Resource Requirements

**Development Environment:**
- CPU: 4 cores minimum, 8 cores recommended
- RAM: 8GB minimum, 16GB recommended
- Disk: 20GB SSD
- Network: 10 Mbps minimum

**Production Environment:**
- CPU: 8 cores minimum, 16 cores recommended
- RAM: 16GB minimum, 32GB recommended
- Disk: 50GB SSD
- Network: 100 Mbps minimum

**Per-Service Resource Estimates:**
```yaml
fastapi:
  cpu: 1000m
  memory: 2Gi

mcp_server (each):
  cpu: 200m
  memory: 512Mi

celery_worker:
  cpu: 500m
  memory: 1Gi

postgres:
  cpu: 1000m
  memory: 4Gi

redis:
  cpu: 200m
  memory: 512Mi
```

### C. Security Considerations

**1. Container Security**
- Non-root user in all containers
- Read-only root filesystem where possible
- No privileged containers
- Network policies for inter-service communication

**2. Secret Management**
- Never commit secrets to git
- Use Docker secrets or Kubernetes secrets
- Rotate secrets every 90 days
- Audit secret access logs

**3. Image Security**
- Scan images with Trivy/Grype
- Use official Python base images
- Keep dependencies updated
- Pin all dependency versions

**4. Network Security**
- TLS for all external communication
- Internal service mesh (optional)
- API rate limiting
- DDoS protection (Cloudflare)

### D. Migration Path

**From Current State → Target State:**

**Step 1: Local Development (Week 1)**
```bash
# Current
make start-dev

# Target
docker compose up
```

**Step 2: Staging Environment (Week 2)**
```bash
# Current
Manual deployment

# Target
git push origin develop
# GitHub Actions auto-deploys to staging
```

**Step 3: Production Environment (Week 3-4)**
```bash
# Current
Manual kubectl apply

# Target
git push origin master
# GitHub Actions auto-deploys with canary
```

### E. Rollback Strategy

**Scenario 1: Docker Compose Deployment Failure**
```bash
# Immediate rollback
docker compose down
docker compose pull --tag previous
docker compose up -d

# Verify
curl http://localhost:8080/health
```

**Scenario 2: Kubernetes Deployment Failure**
```bash
# Immediate rollback
kubectl rollout undo deployment/mcp-servers -n production

# Verify
kubectl rollout status deployment/mcp-servers -n production
```

**Scenario 3: Data Migration Failure**
```bash
# Restore database backup
psql $DATABASE_URL < backups/pre-migration.sql

# Revert code
git revert HEAD
git push origin master --force
```

---

## 🎯 Success Metrics

**Technical Metrics:**
- [ ] All 11 MCP servers containerized (100%)
- [ ] Health check success rate > 99.9%
- [ ] Startup time < 60 seconds
- [ ] Resource usage < 8GB RAM total
- [ ] Zero manual deployment steps

**Business Metrics:**
- [ ] Deployment frequency: 10x increase
- [ ] Mean time to recovery: 5x reduction
- [ ] Developer onboarding time: 50% reduction
- [ ] Infrastructure cost: maintain or reduce

**Quality Metrics:**
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] 99.9% uptime SLA
- [ ] P99 latency < 500ms

---

## 📚 References

**Documentation:**
- FastAPI: https://fastapi.tiangolo.com/
- Docker Compose: https://docs.docker.com/compose/
- Kubernetes: https://kubernetes.io/docs/
- GitHub Actions: https://docs.github.com/en/actions

**Internal Documentation:**
- `CLAUDE.md` - Project overview
- `docs/AGENT_SQUAD_VERTEX_DEEPINFRA.md` - MCP server details
- `Makefile` - Build and deployment commands
- `scripts/start_dev.sh` - Development orchestration

**Architecture Diagrams:**
- `docs/architecture/hexagonal-architecture.md`
- `docs/architecture/deployment-architecture.md` (to be created)

---

## 🎉 Recent Progress: GitHub Actions Optimization (2026-01-26)

### What Was Completed

**Workflows Optimized:**
- ✅ Deleted 3 duplicate workflows (ci.yml, tests.yml, pre-commit-api-docs.yml)
- ✅ Added path filters to test.yml (only run on code changes)
- ✅ Added concurrency limits to all 6 workflows (cancel in-progress runs)
- ✅ Changed coverage-report.yml from daily to weekly (86% reduction)
- ✅ Migrated from Poetry to uv in all workflows

**Impact:**
- 📉 **77% reduction** in GitHub Actions usage (885 → 200 min/week)
- 💰 **~2,700 minutes/month** saved
- ⚡ **Faster feedback** with path-based triggering
- 🚀 **Automatic cancellation** of outdated runs

**Documentation:**
- ✅ Created `.github/workflows/OPTIMIZATION_SUMMARY.md` with complete details
- ✅ Includes testing instructions and rollback procedures
- ✅ Monthly maintenance recommendations

**Commit:** `9506abb4` - "ci: optimize GitHub Actions workflows - 77% usage reduction"

**Reference:** See [`.github/workflows/OPTIMIZATION_SUMMARY.md`](../../.github/workflows/OPTIMIZATION_SUMMARY.md) for complete optimization details.

### Next Steps

**Phase 2 Remaining Work:**
1. Create Docker build/push workflows for 11 MCP servers
2. Implement multi-architecture builds (amd64/arm64)
3. Add automated deployment workflows (staging/production)
4. Implement E2E health checks post-deployment
5. Migrate credentials to GitHub Secrets
6. Add canary deployment strategy

**Estimated Timeline:** 2-3 weeks to complete Phase 2

---

**Document Status:** ✅ Analysis Complete | ✅ GitHub Actions Optimized | 🚧 Docker Build Automation Pending
**Next Action:** Create Docker build/push workflows for MCP servers
**Timeline:** 3 weeks to full production deployment (reduced from 4 weeks)
**Risk Level:** 🟡 Medium (well-understood problem, clear solution, momentum established)
