# GitHub Actions - Build & Push Docker Images

## Overview

Automated CI/CD pipeline that builds and pushes all 23 Docker images to GitHub Container Registry (GHCR) on every push to configured branches.

## What It Does

When you push to one of these branches:
- `master` / `main` → Tags as `production`
- `staging` → Tags as `staging`
- `infra` → Tags as `development`
- Pull requests → Builds only (no push)

The workflow automatically:
1. ✅ Builds all 23 Docker images in parallel using matrix strategy
2. ✅ Pushes to `ghcr.io/YOUR_USERNAME/anvil-backend-<service>:<version>`
3. ✅ Caches layers for faster subsequent builds
4. ✅ Tags with version, latest, and short SHA
5. ✅ Generates build summary report

## Images Built

### Core Services (3)
- `anvil-backend-api` (FastAPI)
- `anvil-backend-celery-beat` (Task Scheduler)
- `anvil-backend-celery-worker` (General Worker)

### Specialized Workers (9)
- `anvil-backend-celery-worker-agents`
- `anvil-backend-celery-worker-transactions`
- `anvil-backend-celery-worker-graph`
- `anvil-backend-celery-worker-distillation`
- `anvil-backend-celery-worker-projects`
- `anvil-backend-celery-worker-llm`
- `anvil-backend-celery-worker-maintenance`
- `anvil-backend-celery-worker-risk`
- `anvil-backend-celery-worker-email`

### MCP Servers (11)
- `anvil-backend-mcp-1inch`
- `anvil-backend-mcp-defillama`
- `anvil-backend-mcp-thegraph`
- `anvil-backend-mcp-coingecko`
- `anvil-backend-mcp-aave`
- `anvil-backend-mcp-portfolio`
- `anvil-backend-mcp-perplexity`
- `anvil-backend-mcp-morpho`
- `anvil-backend-mcp-curve`
- `anvil-backend-mcp-hyperliquid`
- `anvil-backend-mcp-layerzero`

### Utilities (1)
- `anvil-backend-tx-confirmation`

## Branch to Environment Mapping

```
master / main ──→ production  (ghcr.io/.../image:production)
staging      ──→ staging     (ghcr.io/.../image:staging)
infra        ──→ development (ghcr.io/.../image:development)
pull_request ──→ build only  (no push to registry)
```

## Tag Strategy

Each image gets tagged with:
```
ghcr.io/lucholeonel/anvil-backend-<service>:production
ghcr.io/lucholeonel/anvil-backend-<service>:latest
ghcr.io/lucholeonel/anvil-backend-<service>:sha-a1b2c3d
```

## Setup Requirements

### 1. GitHub Container Registry Access

Your GitHub account already has GHCR access. The workflow uses `${{ secrets.GITHUB_TOKEN }}` which is automatically available.

### 2. Repository Settings

- ✅ Already configured in `.github/workflows/build.yml`
- Permissions: `contents: read`, `packages: write`

### 3. How It Works

```
Push to master/staging/infra
        ↓
GitHub Actions triggered
        ↓
Matrix builds 23 images in parallel
        ↓
Docker Buildx compiles each image
        ↓
Cache layers for speed
        ↓
Login to GHCR with GITHUB_TOKEN
        ↓
Push all images with appropriate tags
        ↓
Build summary report
```

## Usage Examples

### Using Built Images

```bash
# Pull from GHCR
docker pull ghcr.io/lucholeonel/anvil-backend-api:production

# Run a specific service
docker run -d ghcr.io/lucholeonel/anvil-backend-celery-worker-agents:production

# Use in docker-compose.yml
services:
  fastapi:
    image: ghcr.io/lucholeonel/anvil-backend-api:production
  celery-worker-agents:
    image: ghcr.io/lucholeonel/anvil-backend-celery-worker-agents:production
```

### Update docker-compose.yaml

Replace local builds with registry pulls:

```yaml
services:
  fastapi:
    image: ghcr.io/lucholeonel/anvil-backend-api:production
    # Remove: build: ./docker/Dockerfile.fastapi
    
  celery-worker-agents:
    image: ghcr.io/lucholeonel/anvil-backend-celery-worker-agents:production
    # Remove: build: ./docker/Dockerfile.celery-workers.agents
```

Then:
```bash
docker-compose pull
docker-compose up -d
```

## Parallelization

The matrix strategy builds all 23 images **in parallel**, which is much faster than sequential building.

**Single job execution time**: ~5-15 minutes per image  
**Parallel with 23 jobs**: ~10-20 minutes total (all images built simultaneously)

Example:
- Sequential: 23 × 10 min = 230 minutes (~4 hours)
- Parallel: 10-20 minutes (all 23 at the same time)

## GitHub Actions Cache

The workflow uses GitHub Actions cache (`type=gha`) to cache Docker build layers:

- ✅ Automatically caches build artifacts
- ✅ Speeds up subsequent builds by ~50%
- ✅ Cache persists for 5 days

## Monitoring Builds

### View Build Status

1. Go to repository → **Actions** tab
2. Click on latest workflow run "Build & Push All Docker Images"
3. See all 23 matrix jobs running in parallel
4. Each job shows:
   - ✅ Build success
   - 📊 Build time
   - 📤 Images pushed
   - 📌 Tags applied

### Build Summary

At the end of workflow, you'll see:

```
✅ Build Summary
================
Status: success
Branch: refs/heads/master
Version: production

Built Services:
  • FastAPI API
  • Celery Beat
  • Celery Worker (General)
  • 9 Specialized Celery Workers
  • 11 MCP Servers
  • TX Confirmation

Total: 23 Docker images

🎉 All builds completed successfully!
```

## Pull Request Preview

When you open a PR to master/staging/infra:
- ✅ All 23 images are built for validation
- ✅ No push to GHCR (test only)
- ✅ Shows build success/failure
- ✅ Helps catch Dockerfile issues before merge

## Troubleshooting

### Build Fails

Check the specific job that failed:

```
Actions → Latest Run → Failed Job
```

Common issues:
- Missing files in build context
- Syntax errors in Dockerfile
- Missing dependencies
- Layer caching issues

### Fix: Run full rebuild without cache

The workflow automatically handles this on failure, but you can manually trigger:

1. Go to Actions
2. Click "Build & Push All Docker Images"
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow"

### Build Timeout

If a build takes too long:
- Check for inefficient layer caching
- Verify dependencies are available
- Check internet connectivity in build

## Adding New Services

To add a new service to the CI/CD:

1. Create `docker/Dockerfile.myservice`
2. Add entry to matrix in `.github/workflows/build.yml`:

```yaml
- service: myservice
  dockerfile: docker/Dockerfile.myservice
  image_name: anvil-backend-myservice
```

3. Commit and push
4. Workflow automatically includes new service

## Security Notes

- ✅ Uses `GITHUB_TOKEN` (automatic, time-limited)
- ✅ Only pushes on authenticated push events
- ✅ Registry is public but you can make it private
- ✅ Images inherit your repository permissions

## Cost Considerations

GitHub Actions provides free CI/CD minutes:
- 2,000 minutes/month for free tier
- 23 parallel builds × 15 min ≈ 345 minutes per run
- ~6 full builds per month with free tier

## Next Steps

1. **First push**: Push to `master` → watch workflow run
2. **Verify images**: 
   ```bash
   docker pull ghcr.io/lucholeonel/anvil-backend-api:production
   ```
3. **Update docker-compose.yml**: Replace local builds with registry pulls
4. **Deploy**: Use registry images in your Kubernetes cluster or docker-compose

## Links

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Created**: January 24, 2026  
**Status**: Production-ready  
**Last Updated**: January 24, 2026
