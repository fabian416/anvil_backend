# Nginx SSL Configuration for testanvilcrypto.ddnsking.com

## ✅ Configuration Complete

SSL certificate has been successfully generated and configured using Let's Encrypt.

## Certificate Details

- **Domain**: testanvilcrypto.ddnsking.com
- **Certificate Type**: Let's Encrypt (ECDSA)
- **Expiry Date**: 2026-04-08 (89 days validity)
- **Certificate Path**: `/etc/letsencrypt/live/testanvilcrypto.ddnsking.com/fullchain.pem`
- **Private Key Path**: `/etc/letsencrypt/live/testanvilcrypto.ddnsking.com/privkey.pem`

## Configuration Files

- **Nginx Config**: `/etc/nginx/sites-enabled/testanvilcrypto.ddnsking.com.conf`
- **Source Config**: `config/nginx/testanvilcrypto.ddnsking.com.conf`

## Features Configured

✅ HTTP to HTTPS redirect (automatic)
✅ SSL/TLS encryption (TLS 1.2/1.3)
✅ Let's Encrypt certificate (auto-renewal enabled)
✅ Frontend reverse proxy to Vite dev server (port 5173) on root path
✅ Backend reverse proxy to FastAPI (port 8080) on /api path
✅ API documentation available at /docs
✅ WebSocket support (on /ws path)
✅ Security headers (HSTS, X-Frame-Options, etc.)
✅ Access and error logging
✅ 100MB file upload limit

## URLs

- **Frontend**: https://testanvilcrypto.ddnsking.com/
- **API Backend**: https://testanvilcrypto.ddnsking.com/api/*
- **API Docs**: https://testanvilcrypto.ddnsking.com/docs
- **OpenAPI Schema**: https://testanvilcrypto.ddnsking.com/openapi.json
- **WebSocket**: https://testanvilcrypto.ddnsking.com/ws

## Certificate Auto-Renewal

Certbot has automatically set up a systemd timer to renew the certificate before it expires. The certificate will be automatically renewed when it has less than 30 days remaining.

To test renewal:
```bash
sudo certbot renew --dry-run
```

To manually renew:
```bash
sudo certbot renew
```

## Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx

# View logs
sudo tail -f /var/log/nginx/testanvilcrypto-access.log
sudo tail -f /var/log/nginx/testanvilcrypto-error.log
```

## Troubleshooting

### 502 Bad Gateway Error

If you see a 502 error, it means nginx is working but cannot connect to the backend:

1. **Check if FastAPI is running**:
   ```bash
   lsof -i :8080
   # or
   ps aux | grep uvicorn
   ```

2. **Start the backend**:
   ```bash
   cd /home/ubuntu/anvil_backend
   make start
   ```

3. **Check if frontend is running** (if needed):
   ```bash
   lsof -i :5173
   ```

### Certificate Issues

1. **Check certificate status**:
   ```bash
   sudo certbot certificates
   ```

2. **View certbot logs**:
   ```bash
   sudo tail -f /var/log/letsencrypt/letsencrypt.log
   ```

3. **Force renewal** (if needed):
   ```bash
   sudo certbot renew --force-renewal
   sudo systemctl reload nginx
   ```

### DNS Issues

If the domain is not resolving:

1. **Check DNS resolution**:
   ```bash
   dig testanvilcrypto.ddnsking.com
   nslookup testanvilcrypto.ddnsking.com
   ```

2. **Verify DNS points to this server**:
   ```bash
   curl -I http://testanvilcrypto.ddnsking.com
   ```

## Security Notes

- The certificate is automatically renewed by certbot
- HTTP traffic is automatically redirected to HTTPS
- Security headers are configured (HSTS, X-Frame-Options, etc.)
- SSL protocols are restricted to TLS 1.2 and 1.3 only
- Modern cipher suites are enabled

## Next Steps

1. **Start the backend** (if not running):
   ```bash
   cd /home/ubuntu/anvil_backend
   make start
   ```

2. **Start the frontend** (if needed):
   ```bash
   cd /home/ubuntu/anvil_frontend
   npm run dev -- --host 0.0.0.0
   ```

3. **Test the setup**:
   ```bash
   curl -I https://testanvilcrypto.ddnsking.com
   curl -I https://testanvilcrypto.ddnsking.com/api/v1/health
   ```

## Configuration Management

The nginx configuration file is managed by certbot. If you need to make changes:

1. Edit the source file: `config/nginx/testanvilcrypto.ddnsking.com.conf`
2. Copy to nginx: `sudo cp config/nginx/testanvilcrypto.ddnsking.com.conf /etc/nginx/sites-available/testanvilcrypto.ddnsking.com.conf`
3. Test: `sudo nginx -t`
4. Reload: `sudo systemctl reload nginx`

**Note**: Certbot may modify the configuration file directly. Always test before reloading.
