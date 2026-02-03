# Server Setup Guide

Step-by-step guide to deploy Anvil Backend on a fresh Ubuntu server.

## Prerequisites

- Ubuntu 20.04+ server with root access
- SSH key configured (`~/.ssh/anvil_keys`)
- Domain name configured (for production)
- GitHub Container Registry credentials

## Server Access

```bash
# SSH into server
ssh -i ~/.ssh/anvil_keys root@SERVER_IP
```

**Server IPs**:
- **Development**: `165.22.168.155`
- **Staging**: `159.89.142.197`
- **Production**: `157.230.162.65`

---

## 1. Install Docker

Add Docker's official GPG key and repository:

```bash
# Update package index
sudo apt-get update
sudo apt-get install ca-certificates curl

# Add Docker GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker repository to Apt sources
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index again
sudo apt-get update
```

Install Docker Engine and plugins:

```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

## 2. Create Directory Structure

```bash
mkdir -p /opt/docker/shared
mkdir -p /opt/docker/anvil
mkdir -p /opt/docker/anvil/config/local
mkdir -p /opt/docker/anvil/config/staging
mkdir -p /opt/docker/anvil/config/prod
```

---

## 3. Configure GitHub Container Registry Access

```bash
cat <<EOF > ~/.docker/config.json
{
  "auths": {
    "ghcr.io": {
      "auth": "YOUR_BASE64_ENCODED_GITHUB_TOKEN"
    }
  }
}
EOF
```

> **Note**: Replace `YOUR_BASE64_ENCODED_GITHUB_TOKEN` with base64 encoded GitHub token: `echo -n "USERNAME:TOKEN" | base64`

---

## 4. Setup Watchtower

```bash
cd /opt/docker/shared

cat <<EOF > docker-compose.yml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /root/.docker/config.json:/config.json
    command: --interval 30 --label-enable
    environment:
      WATCHTOWER_LABEL_ENABLE: 'true'
      WATCHTOWER_POLL_INTERVAL: 30
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
EOF
```

---

## 5. Create Systemd Services

```bash
cd /etc/systemd/system

cat <<EOF > docker-compose@.service
[Unit]
Description=%i service with docker compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/docker/%i
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > docker-prune.service
[Unit]
Description=Remove unused docker resources
Documentation=https://docs.docker.com/v17.09/engine/admin/pruning/
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/docker system prune -f
TimeoutSec=10m

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > docker-prune.timer
[Unit]
Description=Run docker-prune daily

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF
```

---

## 6. Setup Anvil Application

```bash
cd /opt/docker/anvil

cat <<EOF > .env
# ===================================================
# DEPLOYMENT CONFIGURATION
# ===================================================

# GitHub Container Registry
GHCR_USERNAME=anvil-com

# Image Tag - Use one of:
# - sha-XXXXXXX (specific commit)
# - production (master branch)
# - staging (staging branch)
# - development (infra branch)
IMAGE_TAG=development

# ===================================================
# APPLICATION ENVIRONMENT
# ===================================================
APP_ENV=local

# ===================================================
# DATABASE CONFIGURATION
# ===================================================
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_HERE
POSTGRES_DB=anvil_db
DATABASE_URL=postgresql://postgres:YOUR_SECURE_PASSWORD_HERE@postgres:5432/anvil_db

# ===================================================
# REDIS CONFIGURATION
# ===================================================
REDIS_URL=redis://redis:6379

# ===================================================
# CELERY CONFIGURATION
# ===================================================
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# ===================================================
# MONITORING
# ===================================================
FLOWER_BASIC_AUTH=admin:YOUR_FLOWER_PASSWORD_HERE

# ===================================================
# CADDY (HTTPS)
# ===================================================
DOMAIN=your-domain.com

# ===================================================
# MCP API KEYS (Add as needed)
# ===================================================
ONEINCH_API_KEY=
THEGRAPH_API_KEY=
COINGECKO_API_KEY=
AAVE_RPC_URL=
PERPLEXITY_API_KEY=
MORPHO_API_KEY=
CURVE_API_URL=
HYPERLIQUID_API_KEY=
LAYERZERO_API_KEY=
EOF

cat <<EOF > Caddyfile
{
    {\$CADDY_GLOBAL_OPTIONS}
}

{\$CADDY_EXTRA_CONFIG}

{\$DOMAIN} {
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }

    # Flower (Celery Monitoring) - with basic auth
    handle /flower/* {
        uri strip_prefix /flower
        reverse_proxy flower:5555
    }

    # MCP Servers - route based on path
    handle /mcp/1inch/* {
        uri strip_prefix /mcp/1inch
        reverse_proxy mcp-1inch:8081
    }

    handle /mcp/defillama/* {
        uri strip_prefix /mcp/defillama
        reverse_proxy mcp-defillama:8082
    }

    handle /mcp/thegraph/* {
        uri strip_prefix /mcp/thegraph
        reverse_proxy mcp-thegraph:8083
    }

    handle /mcp/coingecko/* {
        uri strip_prefix /mcp/coingecko
        reverse_proxy mcp-coingecko:8084
    }

    handle /mcp/aave/* {
        uri strip_prefix /mcp/aave
        reverse_proxy mcp-aave:8085
    }

    handle /mcp/portfolio/* {
        uri strip_prefix /mcp/portfolio
        reverse_proxy mcp-portfolio:8086
    }

    handle /mcp/perplexity/* {
        uri strip_prefix /mcp/perplexity
        reverse_proxy mcp-perplexity:8087
    }

    handle /mcp/morpho/* {
        uri strip_prefix /mcp/morpho
        reverse_proxy mcp-morpho:8088
    }

    handle /mcp/curve/* {
        uri strip_prefix /mcp/curve
        reverse_proxy mcp-curve:8089
    }

    handle /mcp/hyperliquid/* {
        uri strip_prefix /mcp/hyperliquid
        reverse_proxy mcp-hyperliquid:8090
    }

    handle /mcp/layerzero/* {
        uri strip_prefix /mcp/layerzero
        reverse_proxy mcp-layerzero:8091
    }

    # FastAPI - catch all remaining traffic
    handle {
        reverse_proxy fastapi:8080
    }
}
EOF
```

> **Note**: Copy `docker-compose.production.yaml` from the project root to `/opt/docker/anvil/docker-compose.yaml`

---

## 7. Configuration Files

Create configuration files in `config/$ENV/` directory:

```bash
# Create config.toml (non-sensitive settings)
nano /opt/docker/anvil/config/local/config.toml

# Create .secrets.toml (API keys, credentials)
nano /opt/docker/anvil/config/local/.secrets.toml
```

> **Note**: Copy templates from the repository. `.secrets.toml` should contain API keys, LLM credentials, and blockchain RPC endpoints.

---

## 8. Enable and Start Services

```bash
# 1. Reload systemd daemon
sudo systemctl daemon-reload

# 2. Enable services
sudo systemctl enable docker-prune.service
sudo systemctl enable docker-prune.timer
sudo systemctl enable docker-compose@shared.service
sudo systemctl enable docker-compose@anvil.service

# 3. Start services
sudo systemctl start docker-prune.service
sudo systemctl start docker-prune.timer
sudo systemctl start docker-compose@shared.service
sudo systemctl start docker-compose@anvil.service

# 4. Check status
sudo systemctl status docker-prune.service
sudo systemctl status docker-prune.timer
sudo systemctl status docker-compose@shared.service
sudo systemctl status docker-compose@anvil.service
```

---

## 9. Environment-Specific Configuration

### Development
- **Server**: 8 GB / 160 GB Disk / SFO2
- **IP**: `165.22.168.155`
- **SSH**: `ssh -i ~/.ssh/anvil_keys root@165.22.168.155`
- **Database**: Local PostgreSQL container
- **Config**: `APP_ENV=local`, `IMAGE_TAG=development`

### Staging
- **Server**: 8 GB / 160 GB Disk / SFO2
- **IP**: `159.89.142.197`
- **SSH**: `ssh -i ~/.ssh/anvil_keys root@159.89.142.197`
- **Database**: Digital Ocean Managed PostgreSQL (port 25060, SSL required)
- **Config**: `APP_ENV=staging`, `IMAGE_TAG=staging`
- **Note**: Comment out `postgres` service in docker-compose.yaml

### Production
- **Server**: 8 GB / 4 Intel vCPUs / 240 GB Disk / SFO2
- **IP**: `157.230.162.65`
- **SSH**: `ssh -i ~/.ssh/anvil_keys root@157.230.162.65`
- **Database**: Digital Ocean Managed PostgreSQL + Daily Backups
- **Config**: `APP_ENV=production`, `IMAGE_TAG=production`
- **Security**: Strong passwords, monitoring alerts, daily backups enabled

---

## 10. Useful Commands

```bash
# View logs
docker compose logs -f
docker compose logs -f fastapi

# Check status
docker ps
systemctl status docker-compose@anvil

# Restart services
systemctl restart docker-compose@anvil

# Update images (Watchtower does this automatically)
docker compose pull && docker compose up -d
```
