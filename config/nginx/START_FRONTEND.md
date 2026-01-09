# How to Start the Frontend to Fix 502 Bad Gateway

## Problem

The 502 Bad Gateway error occurs because the frontend (Vite dev server) is not running on port 5173.

## Solution: Start the Frontend

### Option 1: Start Frontend Manually

```bash
cd /home/ubuntu/anvil_frontend
npm install  # If dependencies are not installed
npm run dev -- --host 0.0.0.0 --port 5173
```

### Option 2: Start Frontend in Background (Recommended)

```bash
cd /home/ubuntu/anvil_frontend
nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/vite.log 2>&1 &
```

### Option 3: Create a Systemd Service (Production)

Create `/etc/systemd/system/anvil-frontend.service`:

```ini
[Unit]
Description=Anvil Frontend Vite Dev Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/anvil_frontend
Environment="NODE_ENV=development"
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable anvil-frontend
sudo systemctl start anvil-frontend
sudo systemctl status anvil-frontend
```

## Verify Frontend is Running

```bash
# Check if port 5173 is listening
lsof -i :5173

# Or test the connection
curl http://127.0.0.1:5173
```

## Current Status

- ✅ Backend (FastAPI): Running on port 8080
- ❌ Frontend (Vite): Not running on port 5173
- ✅ Nginx: Configured and running
- ✅ SSL: Configured with Let's Encrypt

## Temporary Workaround

While the frontend is starting, you can access:
- **API Documentation**: https://testanvilcrypto.ddnsking.com/docs
- **API Endpoints**: https://testanvilcrypto.ddnsking.com/api/*

The nginx configuration now shows a helpful message when the frontend is down instead of a generic 502 error.
