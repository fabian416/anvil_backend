# 🚀 Production Deployment Checklist

**Version**: 1.0  
**Last Updated**: December 2, 2024  
**Status**: Phase 2 Complete - Ready for Production  

---

## 📋 Pre-Deployment Checklist

### ✅ Phase 1: Infrastructure Setup

- [ ] **1.1 Server Provisioning**
  - [ ] Provision Ubuntu 20.04+ server (minimum 4GB RAM, 2 CPU cores)
  - [ ] Configure firewall rules (ports: 80, 443, 8000-8084, 5555, 5432, 6379)
  - [ ] Set up SSL/TLS certificates (Let's Encrypt or custom)
  - [ ] Configure domain name and DNS records
  - [ ] Set up monitoring and logging (Datadog, New Relic, or similar)

- [ ] **1.2 Database Setup**
  - [ ] Install PostgreSQL 14+ with required extensions
    ```bash
    sudo apt-get install postgresql-14
    sudo apt-get install postgresql-14-pgvector
    sudo apt-get install postgresql-14-age
    ```
  - [ ] Create production database user and database
  - [ ] Configure PostgreSQL for production (connection pooling, memory)
  - [ ] Set up database backups (daily automated backups)
  - [ ] Test database connectivity from application server

- [ ] **1.3 Redis Setup**
  - [ ] Install Redis 6+ 
    ```bash
    sudo apt-get install redis-server
    ```
  - [ ] Configure Redis for production (persistence, max memory)
  - [ ] Enable Redis authentication (requirepass)
  - [ ] Set up Redis backups if using persistence
  - [ ] Test Redis connectivity

- [ ] **1.4 Environment Configuration**
  - [ ] Create `.env.production` file with all required variables
  - [ ] Set `APP_ENV=prod`
  - [ ] Generate secure `JWT_SECRET_KEY` (256-bit random)
  - [ ] Configure all API keys (OpenAI, Stripe, etc.)
  - [ ] Set production database credentials
  - [ ] Configure Redis URL with authentication
  - [ ] Set CORS allowed origins
  - [ ] Review and set all security-related env vars

---

### ✅ Phase 2: Application Deployment

- [ ] **2.1 Code Deployment**
  - [ ] Clone repository to production server
    ```bash
    git clone https://github.com/Anvil-com/anvil_backend.git
    cd anvil_backend
    git checkout master  # or specific release tag
    ```
  - [ ] Create Python virtual environment
    ```bash
    python3.12 -m venv .venv
    source .venv/bin/activate
    ```
  - [ ] Install dependencies
    ```bash
    uv pip install -e '.[prod]'
    ```
  - [ ] Verify installation
    ```bash
    python -c "import app; print('✅ App imports successfully')"
    ```

- [ ] **2.2 Database Migrations**
  - [ ] Run all migrations
    ```bash
    alembic upgrade head
    ```
  - [ ] Verify migration success
    ```bash
    psql -U [user] -d anvil_backend -c "SELECT version_num FROM alembic_version;"
    ```
  - [ ] Check table count (should be 18+ tables)
    ```bash
    psql -U [user] -d anvil_backend -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
    ```

- [ ] **2.3 Seed Initial Data**
  - [ ] Run seed script
    ```bash
    python scripts/seed_data.py
    ```
  - [ ] Verify seeded data
    - [ ] 10 default projects created
    - [ ] Distillation config initialized
    - [ ] Test user created (if applicable)

---

### ✅ Phase 3: Service Configuration

- [ ] **3.1 Systemd Services**
  - [ ] Create systemd service for main API
    ```bash
    sudo nano /etc/systemd/system/anvil-api.service
    ```
    ```ini
    [Unit]
    Description=Anvil Backend API
    After=network.target postgresql.service redis.service

    [Service]
    Type=simple
    User=ubuntu
    WorkingDirectory=/home/ubuntu/anvil_backend
    Environment="PATH=/home/ubuntu/anvil_backend/.venv/bin"
    Environment="APP_ENV=prod"
    ExecStart=/home/ubuntu/anvil_backend/.venv/bin/uvicorn app.run:make_app --factory --host 0.0.0.0 --port 8000 --workers 4
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

  - [ ] Create systemd service for Celery worker
    ```bash
    sudo nano /etc/systemd/system/anvil-celery-worker.service
    ```
    ```ini
    [Unit]
    Description=Anvil Celery Worker
    After=network.target redis.service

    [Service]
    Type=simple
    User=ubuntu
    WorkingDirectory=/home/ubuntu/anvil_backend
    Environment="PATH=/home/ubuntu/anvil_backend/.venv/bin"
    Environment="APP_ENV=prod"
    ExecStart=/home/ubuntu/anvil_backend/.venv/bin/celery -A app.infrastructure.celery.app worker --loglevel=info
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

  - [ ] Create systemd service for Celery beat
    ```bash
    sudo nano /etc/systemd/system/anvil-celery-beat.service
    ```
    ```ini
    [Unit]
    Description=Anvil Celery Beat Scheduler
    After=network.target redis.service

    [Service]
    Type=simple
    User=ubuntu
    WorkingDirectory=/home/ubuntu/anvil_backend
    Environment="PATH=/home/ubuntu/anvil_backend/.venv/bin"
    Environment="APP_ENV=prod"
    ExecStart=/home/ubuntu/anvil_backend/.venv/bin/celery -A app.infrastructure.celery.app beat --loglevel=info
    Restart=always
    RestartSec=10

    [Install]
    WantedBy=multi-user.target
    ```

  - [ ] Create systemd services for MCP servers (4 services)
    ```bash
    # Portfolio MCP (port 8081)
    sudo nano /etc/systemd/system/anvil-mcp-portfolio.service
    
    # 1inch MCP (port 8082)
    sudo nano /etc/systemd/system/anvil-mcp-oneinch.service
    
    # Aave MCP (port 8083)
    sudo nano /etc/systemd/system/anvil-mcp-aave.service
    
    # DeFiLlama MCP (port 8084)
    sudo nano /etc/systemd/system/anvil-mcp-defillama.service
    ```

  - [ ] Enable and start all services
    ```bash
    sudo systemctl daemon-reload
    
    # Main API
    sudo systemctl enable anvil-api
    sudo systemctl start anvil-api
    
    # Celery
    sudo systemctl enable anvil-celery-worker
    sudo systemctl start anvil-celery-worker
    sudo systemctl enable anvil-celery-beat
    sudo systemctl start anvil-celery-beat
    
    # MCP Servers
    sudo systemctl enable anvil-mcp-portfolio
    sudo systemctl start anvil-mcp-portfolio
    sudo systemctl enable anvil-mcp-oneinch
    sudo systemctl start anvil-mcp-oneinch
    sudo systemctl enable anvil-mcp-aave
    sudo systemctl start anvil-mcp-aave
    sudo systemctl enable anvil-mcp-defillama
    sudo systemctl start anvil-mcp-defillama
    ```

  - [ ] Verify all services are running
    ```bash
    sudo systemctl status anvil-api
    sudo systemctl status anvil-celery-worker
    sudo systemctl status anvil-celery-beat
    sudo systemctl status anvil-mcp-*
    ```

- [ ] **3.2 Nginx Reverse Proxy**
  - [ ] Install Nginx
    ```bash
    sudo apt-get install nginx
    ```
  - [ ] Configure Nginx for API
    ```bash
    sudo nano /etc/nginx/sites-available/anvil
    ```
    ```nginx
    upstream api {
        server 127.0.0.1:8000;
    }

    server {
        listen 80;
        server_name api.yourdomain.com;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /api/v1/ws/ {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
    ```
  - [ ] Enable site and reload Nginx
    ```bash
    sudo ln -s /etc/nginx/sites-available/anvil /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    ```
  - [ ] Set up SSL with Let's Encrypt
    ```bash
    sudo apt-get install certbot python3-certbot-nginx
    sudo certbot --nginx -d api.yourdomain.com
    ```

---

### ✅ Phase 4: Verification

- [ ] **4.1 Automated Verification**
  - [ ] Run deployment verification script
    ```bash
    python scripts/verify_deployment.py --verbose
    ```
  - [ ] All checks should pass (✅)

- [ ] **4.2 Manual Verification**
  - [ ] **Health Checks**
    - [ ] API health: `curl https://api.yourdomain.com/health`
    - [ ] API docs: `https://api.yourdomain.com/docs`
    - [ ] MCP servers (4): `curl http://localhost:8081/tools` (and 8082, 8083, 8084)
  
  - [ ] **Functional Tests**
    - [ ] User registration works
    - [ ] User login works
    - [ ] JWT token generation works
    - [ ] Authenticated endpoints work
    - [ ] Chat message sending works
    - [ ] WebSocket connection works
    - [ ] Agent routing works
    - [ ] MCP tools execute successfully
    - [ ] Caching works (Redis)
    - [ ] Background tasks execute (Celery)
  
  - [ ] **Performance Tests**
    - [ ] API response time < 500ms (uncached)
    - [ ] API response time < 100ms (cached)
    - [ ] WebSocket latency < 100ms
    - [ ] Agent response time < 3s (uncached)
    - [ ] Cache hit rate > 60% (after warmup)
    - [ ] Concurrent users: Test with 10, 50, 100 users
  
  - [ ] **Security Tests**
    - [ ] HTTPS enabled and working
    - [ ] Invalid JWT tokens rejected
    - [ ] Unauthorized access blocked
    - [ ] SQL injection protection verified
    - [ ] XSS protection verified
    - [ ] CORS policy enforced
    - [ ] Rate limiting working (if enabled)

- [ ] **4.3 Monitoring Setup**
  - [ ] Application logs accessible
    ```bash
    sudo journalctl -u anvil-api -f
    sudo journalctl -u anvil-celery-worker -f
    ```
  - [ ] Error tracking configured (Sentry or similar)
  - [ ] Performance monitoring configured (New Relic, Datadog, or similar)
  - [ ] Uptime monitoring configured (UptimeRobot or similar)
  - [ ] Database monitoring configured
  - [ ] Redis monitoring configured
  - [ ] Alerts configured for critical errors

---

### ✅ Phase 5: Post-Deployment

- [ ] **5.1 Documentation**
  - [ ] Update deployment documentation with production URLs
  - [ ] Document any production-specific configurations
  - [ ] Create runbook for common operations
  - [ ] Document rollback procedures
  - [ ] Update API documentation with production examples

- [ ] **5.2 Backup Verification**
  - [ ] Verify database backups are running
  - [ ] Test database restore from backup
  - [ ] Verify Redis backups (if using persistence)
  - [ ] Test code rollback procedure

- [ ] **5.3 Team Preparation**
  - [ ] Share production access credentials (securely)
  - [ ] Train team on monitoring dashboards
  - [ ] Establish on-call rotation (if applicable)
  - [ ] Document incident response procedures
  - [ ] Share production API endpoints with frontend team

- [ ] **5.4 User Communication**
  - [ ] Announce production launch
  - [ ] Share production API base URL
  - [ ] Provide API documentation link
  - [ ] Set up support channels
  - [ ] Create user onboarding materials

---

## 🚨 Troubleshooting Guide

### Issue: API Server Won't Start

**Symptoms**: `systemctl status anvil-api` shows failed status

**Checks**:
1. Check logs: `sudo journalctl -u anvil-api -n 50`
2. Verify environment variables: `cat /etc/systemd/system/anvil-api.service`
3. Test manually: `source .venv/bin/activate && uvicorn app.run:make_app --factory`
4. Check database connectivity
5. Check port 8000 availability: `sudo lsof -i :8000`

**Solutions**:
- Missing env vars: Update service file and reload
- Port in use: Kill process or change port
- Database connection: Fix database credentials

---

### Issue: MCP Servers Not Responding

**Symptoms**: `curl http://localhost:8081/tools` fails

**Checks**:
1. Check if services are running: `sudo systemctl status anvil-mcp-*`
2. Check logs: `sudo journalctl -u anvil-mcp-portfolio -n 50`
3. Check ports: `sudo lsof -i :8081-8084`
4. Test manually: `python -m app.infrastructure.mcp.servers.portfolio_mcp`

**Solutions**:
- Service not running: Start with `sudo systemctl start anvil-mcp-portfolio`
- Port in use: Change port in service config
- Import errors: Reinstall dependencies

---

### Issue: Agents Not Responding

**Symptoms**: Chat messages timeout or fail

**Checks**:
1. Check if MCP servers are running (all 4)
2. Check OpenAI API key is set
3. Check agent router initialization: `curl http://localhost:8000/api/v1/agno/stats`
4. Check logs for agent errors

**Solutions**:
- MCP servers down: Start MCP servers
- API key invalid: Update `OPENAI_API_KEY` in env
- Agent not initialized: Restart API service

---

### Issue: WebSocket Connection Fails

**Symptoms**: WebSocket connection closes immediately

**Checks**:
1. Check Nginx WebSocket configuration
2. Check JWT token is valid
3. Check firewall rules
4. Check logs for authentication errors

**Solutions**:
- Nginx config: Add WebSocket upgrade headers
- Invalid token: Generate new JWT token
- Firewall: Allow WebSocket port

---

### Issue: Poor Performance

**Symptoms**: Slow response times, high latency

**Checks**:
1. Check cache hit rate: `curl http://localhost:8000/api/v1/agno/stats`
2. Check Redis connectivity
3. Check database query performance
4. Check CPU/memory usage
5. Check slow queries: `curl http://localhost:8000/api/v1/agno/slow-queries`

**Solutions**:
- Low cache hit rate: Warm up cache, increase TTL
- Redis down: Start Redis service
- Slow queries: Optimize database indexes
- High CPU: Scale horizontally, add more workers

---

## 📊 Success Criteria

### ✅ Deployment is successful if:

1. **All Services Running**:
   - ✅ Main API (port 8000)
   - ✅ 4 MCP servers (ports 8081-8084)
   - ✅ Celery worker
   - ✅ Celery beat
   - ✅ PostgreSQL
   - ✅ Redis

2. **All Checks Passing**:
   - ✅ Health endpoint returns 200
   - ✅ Database has 18+ tables
   - ✅ All migrations applied
   - ✅ 27 MCP tools available
   - ✅ 4 agents initialized
   - ✅ WebSocket connects successfully

3. **Performance Targets Met**:
   - ✅ Cached responses < 100ms
   - ✅ Fresh responses < 3s
   - ✅ Cache hit rate > 60%
   - ✅ 100+ concurrent users supported

4. **Security Verified**:
   - ✅ HTTPS enabled
   - ✅ Authentication working
   - ✅ Authorization working
   - ✅ No security vulnerabilities

5. **Monitoring Active**:
   - ✅ Logs accessible
   - ✅ Error tracking active
   - ✅ Performance monitoring active
   - ✅ Alerts configured

---

## 🎉 Deployment Complete!

Once all checklist items are completed and verified, your production deployment is ready!

**Next Steps**:
1. Monitor application for first 24 hours
2. Gather user feedback
3. Optimize based on real usage patterns
4. Plan for Phase 3 (GraphRAG) deployment

**Support**:
- Documentation: `/docs/`
- API Reference: `https://api.yourdomain.com/docs`
- Deployment Guide: `/docs/DEPLOYMENT_GUIDE.md`
- Troubleshooting: This document

---

**🚀 Happy Deploying! 🚀**
