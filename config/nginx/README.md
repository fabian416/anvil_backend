# Nginx Configuration for Anvil Backend

This directory contains the nginx configuration for the Anvil Backend development server.

## Current Setup

- **Server IP**: 18.168.176.189
- **HTTP Port**: 80 (redirects to HTTPS)
- **HTTPS Port**: 443
- **Backend Port**: 8080 (FastAPI)
- **SSL**: Self-signed certificate (for development)

## Configuration Files

- `anvil-backend.conf` - Main nginx reverse proxy configuration

## Installation

The nginx configuration has been installed to:
- `/etc/nginx/sites-available/anvil-backend`
- `/etc/nginx/sites-enabled/anvil-backend` (symlink)

## SSL Certificates

Self-signed certificates are located at:
- Certificate: `/etc/nginx/ssl/selfsigned.crt`
- Private Key: `/etc/nginx/ssl/selfsigned.key`

**⚠️ Note**: These are self-signed certificates. Browsers will show a security warning. For production, use Let's Encrypt.

## Testing the Setup

### HTTP (redirects to HTTPS)
```bash
curl -I http://18.168.176.189
# Should return 301 redirect to https://
```

### HTTPS (with self-signed cert warning bypass)
```bash
curl -k https://18.168.176.189
# -k flag bypasses SSL certificate validation
```

## AWS Security Group Configuration

Make sure your EC2 instance's Security Group allows inbound traffic on:
- Port 80 (HTTP)
- Port 443 (HTTPS)

Go to: AWS Console → EC2 → Security Groups → Your Instance Security Group → Inbound Rules

Add rules:
1. HTTP (80) - Source: 0.0.0.0/0
2. HTTPS (443) - Source: 0.0.0.0/0

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
sudo tail -f /var/log/nginx/anvil-backend-access.log
sudo tail -f /var/log/nginx/anvil-backend-error.log
```

## Upgrading to Let's Encrypt (When You Have a Domain)

1. **Point your domain to this IP**:
   - Create an A record pointing to 18.168.176.189

2. **Install certbot**:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   ```

3. **Update nginx configuration**:
   Replace `server_name 18.168.176.189;` with `server_name yourdomain.com;`

4. **Get certificate**:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

5. **Auto-renewal** (certbot sets this up automatically):
   ```bash
   sudo certbot renew --dry-run
   ```

## Features Configured

✅ HTTP to HTTPS redirect
✅ SSL/TLS encryption (TLS 1.2/1.3)
✅ Reverse proxy to FastAPI on port 8080
✅ WebSocket support (on /ws path)
✅ Security headers (HSTS, X-Frame-Options, etc.)
✅ Access and error logging
✅ 100MB file upload limit
✅ Connection timeouts configured

## Troubleshooting

### nginx won't start
```bash
# Check configuration syntax
sudo nginx -t

# Check if port 80/443 is already in use
sudo lsof -i :80
sudo lsof -i :443

# View detailed error logs
sudo journalctl -u nginx -n 50
```

### Cannot connect from browser
1. Check if nginx is running: `sudo systemctl status nginx`
2. Check if FastAPI is running on port 8080: `lsof -i :8080`
3. Verify AWS Security Group rules allow ports 80 and 443
4. Check nginx logs for errors

### SSL certificate warnings
This is expected with self-signed certificates. You can:
- Accept the warning in your browser (for development)
- Use Let's Encrypt for a trusted certificate (requires domain name)
