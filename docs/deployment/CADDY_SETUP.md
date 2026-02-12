# Caddy Reverse Proxy Setup

## 📋 Overview

Caddy provides automatic HTTPS, reverse proxy, and routing for the Anvil backend infrastructure.

## 🎯 Current Configuration

### Caddyfile Location
```
docker/Caddyfile
```

### Routes Configured

| Route Pattern | Target | Description |
|---------------|--------|-------------|
| `/` | FastAPI:8080 | Main API (catch-all) |
| `/health` | FastAPI:8080 | Health check endpoint |
| `/api/v1/*` | FastAPI:8080 | API v1 routes |
| `/flower/*` | Flower:5555 | Celery monitoring dashboard |
| `/mcp/1inch/*` | mcp-1inch:8081 | 1inch DEX aggregator |
| `/mcp/defillama/*` | mcp-defillama:8082 | DeFiLlama protocol data |
| `/mcp/thegraph/*` | mcp-thegraph:8083 | The Graph indexing |
| `/mcp/coingecko/*` | mcp-coingecko:8084 | CoinGecko market data |
| `/mcp/aave/*` | mcp-aave:8085 | Aave lending protocol |
| `/mcp/portfolio/*` | mcp-portfolio:8086 | Portfolio analytics |
| `/mcp/perplexity/*` | mcp-perplexity:8087 | AI-powered search |
| `/mcp/morpho/*` | mcp-morpho:8088 | Morpho lending optimization |
| `/mcp/curve/*` | mcp-curve:8089 | Curve stablecoin DEX |
| `/mcp/hyperliquid/*` | mcp-hyperliquid:8090 | Hyperliquid perpetuals |
| `/mcp/layerzero/*` | mcp-layerzero:8091 | LayerZero cross-chain |

## 🔧 Configuration Details

### Current Caddyfile

```caddyfile
{
	{$CADDY_GLOBAL_OPTIONS}
}

{$CADDY_EXTRA_CONFIG}

{$DOMAIN} {
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
```

## 🚀 Deployment

### Environment Variables

Set in `.env` file:
```bash
DOMAIN=getrampy.com  # Your production domain
FLOWER_DOMAIN=flower.getrampy.com  # Optional: separate Flower domain
FLOWER_USER=admin  # Basic auth username
FLOWER_HASH=<bcrypt_hash>  # Bcrypt hash of password
```

### Docker Compose Integration

Caddy is defined in `docker-compose.yaml`:
```yaml
caddy:
  image: caddy:latest
  container_name: anvil_caddy
  restart: unless-stopped
  depends_on:
    - fastapi
    - flower
  ports:
    - "80:80"
    - "443:443"
    - "443:443/udp"  # HTTP/3 support
  networks:
    - anvil-network
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile:ro
    - caddy_data:/data
    - caddy_config:/config
  environment:
    - DOMAIN=${DOMAIN:-getrampy.com}
    - FLOWER_DOMAIN=${FLOWER_DOMAIN}
    - FLOWER_USER=${FLOWER_USER}
    - FLOWER_HASH=${FLOWER_HASH}
```

## ✅ Verification

### Test Endpoints

```bash
# Health check
curl https://getrampy.com/health

# Guest chat
curl -X POST https://getrampy.com/api/v1/guest/chat \
  -H "Content-Type: application/json" \
  -d '{"content": "hello", "language": "en"}'

# MCP Aave
curl https://getrampy.com/mcp/aave/health

# MCP DeFiLlama
curl https://getrampy.com/mcp/defillama/health

# Flower (requires browser for auth)
open https://getrampy.com/flower/
```

### Check Caddy Status

```bash
# View Caddy logs
docker compose logs caddy

# Check if Caddy is running
docker compose ps caddy

# Reload configuration (if changed)
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## 🔒 Security Features

### Automatic HTTPS
- Caddy automatically obtains and renews SSL certificates from Let's Encrypt
- Certificates stored in `/data/caddy` volume
- No manual configuration required

### Security Headers
All responses include:
- `Strict-Transport-Security`: Enforce HTTPS
- `X-Content-Type-Options`: Prevent MIME sniffing
- `X-Frame-Options`: Prevent clickjacking
- `X-XSS-Protection`: XSS attack protection
- `Referrer-Policy`: Control referrer information

### Path Isolation
- Each MCP server isolated by URL path
- `uri strip_prefix` removes routing prefix before proxying
- Internal services only accessible via Caddy

## 📊 Monitoring

### Access Logs
```bash
# Follow Caddy access logs
docker compose logs -f caddy

# Filter by service
docker compose logs caddy | grep "mcp-aave"
```

### Common Log Patterns
```
INFO: HTTP Request: GET /health
INFO: HTTP Request: POST /api/v1/guest/chat
INFO: HTTP Request: GET /mcp/aave/health
```

## 🛠️ Troubleshooting

### MCP Returns 404

**Problem**: `/mcp/{service}/health` returns 404

**Solution**: Verify Caddyfile has `handle /mcp/{service}/*` block and `uri strip_prefix` directive

### Flower Returns 405

**Problem**: HEAD request to `/flower/` returns 405

**Solution**: This is expected. Flower only accepts GET requests. Use browser or `curl` (without `-I`)

### SSL Certificate Issues

**Problem**: Certificate not being issued

**Solution**: 
1. Verify domain DNS points to server
2. Check ports 80/443 are open
3. View Caddy logs: `docker compose logs caddy | grep -i "certificate"`

### Configuration Changes Not Applied

**Problem**: Updated Caddyfile but changes not reflected

**Solution**:
```bash
# Reload configuration
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile

# Or restart container
docker compose restart caddy
```

## 🔄 Updates & Maintenance

### Adding New MCP Server

1. Add to Caddyfile:
```caddyfile
handle /mcp/newservice/* {
    uri strip_prefix /mcp/newservice
    reverse_proxy mcp-newservice:8092
}
```

2. Reload Caddy:
```bash
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Updating Security Headers

Modify the `header` block in Caddyfile and reload.

### Certificate Renewal

Caddy automatically renews certificates 30 days before expiration. No manual action required.

## 📚 References

- [Caddy Documentation](https://caddyserver.com/docs/)
- [Reverse Proxy Guide](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Security Headers](https://caddyserver.com/docs/caddyfile/directives/header)

## 🎯 Production Checklist

- [x] Caddyfile configured with all routes
- [x] Security headers enabled
- [x] Automatic HTTPS configured
- [x] All MCP servers routed correctly
- [x] Flower monitoring accessible
- [x] Health checks responding
- [ ] Basic auth configured for Flower (optional)
- [ ] Custom domain configured in DNS
- [ ] Monitoring alerts configured

## ✅ Current Status (Jan 2026)

**Production Domain**: `https://getrampy.com`

**Services Verified**:
- ✅ FastAPI health endpoint
- ✅ Guest chat endpoint
- ✅ MCP Aave health
- ✅ MCP DeFiLlama health
- ✅ MCP CoinGecko health
- ✅ MCP 1inch health
- ✅ Flower monitoring
- ✅ All 11 MCP servers accessible

**Infrastructure Status**: Fully operational 🚀
