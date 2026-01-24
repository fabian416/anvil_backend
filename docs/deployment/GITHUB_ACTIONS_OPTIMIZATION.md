# GitHub Actions CI/CD Optimization

## Overview

The GitHub Actions workflow has been restructured to solve resource exhaustion issues during Docker image builds. The original single-job matrix approach building all 23 services in parallel was causing:
- "No space left on device" errors during image export
- "Exporting layers" timeout
- Runner memory exhaustion

## Solution: 3-Job Parallel Strategy

Instead of one massive matrix job (23 services), the workflow now uses **3 parallel jobs** that run independently:

### 1. **build-core** (3 services)
Builds the primary services:
- FastAPI API (~250MB)
- Celery Beat (~180MB) 
- Celery Worker (~200MB)

**Why separate:** Core services are critical path; smaller builds complete faster.

### 2. **build-workers** (10 services)
Builds specialized Celery workers and utilities:
- 9 specialized workers (agents, transactions, graph, distillation, projects, llm, maintenance, risk, email)
- 1 utility (tx-confirmation)

**Why separate:** Worker services can build in parallel without blocking core services.

### 3. **build-mcps** (11 services)
Builds all MCP servers (parametrized builds):
- 1inch, Defillama, TheGraph, Coingecko, Aave, Portfolio, Perplexity, Morpho, Curve, Hyperliquid, Layerzero

**Why separate:** MCPs reuse the same Dockerfile with different build args; don't need to compete with heavier builds.

### 4. **build-summary** (depends on all 3)
Generates a summary report after all builds complete (success or failure).

## Branch to Environment Mapping

| Branch | Environment | Image Tags |
|--------|-------------|-----------|
| `master` / `main` | production | `production`, `latest`, `sha-xxxx` |
| `staging` | staging | `staging`, `latest`, `sha-xxxx` |
| `infra` | development | `development`, `sha-xxxx` |

## Key Optimizations

### 1. **Split Matrix Strategy**
- Reduces parallel load from 23 concurrent builds to max 11 (during build-mcps)
- Prevents runner disk exhaustion
- Allows cache reuse across related services

### 2. **Docker Build Args**
```yaml
build-args: |
  APP_ENV=${{ env.IMAGE_VERSION }}  # Sets environment at build time
  ${{ matrix.build_args }}          # Service-specific args (e.g., MCP_SERVER)
```

### 3. **GHA Cache**
Each job uses GitHub Actions cache (type=gha) for layer reuse:
```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

### 4. **Buildx Optimization**
```yaml
driver-options: |
  image=moby/buildkit:latest
  network=host
```

### 5. **Dockerfile Optimizations** (in progress)
All Dockerfiles include:
```dockerfile
ARG APP_ENV=local
ENV APP_ENV=${APP_ENV}

# During build, remove cache:
RUN uv pip install --no-cache-dir . && \
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "*.pyo" -delete
```

### 6. **Expanded .dockerignore**
Excludes ~45+ items (docs/, tests/, examples/, *.m, *.sh, *.pyc, etc.)
Expected savings: ~200MB per image

## Expected Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Peak parallel jobs | 23 | 3 | ~87% |
| Typical build time | 45-60m (timeout) | 15-25m | ~50% |
| Average image size | 10-12GB | 5-6GB | ~50% |
| Runner disk usage | ~150GB+ | ~60GB | ~60% |

## Testing the Changes

### Local Testing
```bash
# Test build-core services locally
docker build -f docker/Dockerfile.fastapi --build-arg APP_ENV=production -t test:latest .
docker build -f docker/Dockerfile.celery-beat --build-arg APP_ENV=production -t test:latest .
docker build -f docker/Dockerfile.celery --build-arg APP_ENV=production -t test:latest .
```

### GitHub Actions Testing
1. Commit changes to `infra` branch
2. Monitor GitHub Actions dashboard
3. Verify all 3 jobs (build-core, build-workers, build-mcps) start in parallel
4. Confirm builds complete without "exporting layers" timeout
5. Check that images are tagged correctly with environment and SHA

### Staging Verification (after infra succeeds)
1. Merge changes to `staging` branch
2. Verify images tagged as `staging`
3. Pull images and test locally: `docker pull ghcr.io/lucholeonel/anvil-backend-api:staging`

## Rollback Plan

If 3-job strategy still causes issues:

1. **Split further into 5-6 jobs:** Break workers into smaller groups
2. **Use scheduled builds:** Stagger builds across time windows
3. **Use self-hosted runners:** Add larger runners for heavy dependencies
4. **Reduce dependencies:** Remove pytorch if not essential for all services

## Future Improvements

1. **Dependency Analysis:** Identify which services actually need torch/numpy/pandas
2. **Slim Dockerfiles:** Create separate "slim" versions for services that don't need ML deps
3. **Multi-registry:** Push to both ghcr.io and potentially ECR or Docker Hub
4. **Pre-built base images:** Create intermediate base image with dependencies pre-installed
5. **Layer caching improvements:** Use BuildKit secrets for private dependency sources

## Debugging Failed Builds

### If "exporting layers" still times out:
1. Check build log for which service is hanging
2. Verify that service's Dockerfile has cache cleanup code
3. Consider splitting that service's job further

### If authentication fails:
1. Verify `GITHUB_TOKEN` has `packages:write` permission
2. Check branch protection rules aren't blocking push

### If cache isn't working:
1. Run: `docker buildx du` to check cache size
2. Clear cache: `docker buildx prune -a`
3. Re-push to rebuild cache

## References

- [GitHub Actions Buildx Documentation](https://github.com/docker/build-push-action)
- [BuildKit Cache Documentation](https://docs.docker.com/build/cache/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
