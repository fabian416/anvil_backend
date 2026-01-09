#!/bin/bash
# Script to start the Anvil Frontend Vite dev server

set -e

echo "🚀 Starting Anvil Frontend..."

cd /home/ubuntu/anvil_frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if port 5173 is already in use
if lsof -i :5173 > /dev/null 2>&1; then
    echo "⚠️  Port 5173 is already in use. Stopping existing process..."
    pkill -f "vite.*5173" || true
    sleep 2
fi

# Start Vite dev server in background
echo "✅ Starting Vite dev server on port 5173..."
nohup npm run dev -- --host 0.0.0.0 --port 5173 > /tmp/vite.log 2>&1 &

# Wait a moment for server to start
sleep 3

# Check if it's running
if lsof -i :5173 > /dev/null 2>&1; then
    echo "✅ Frontend is now running on port 5173"
    echo "📝 Logs: tail -f /tmp/vite.log"
    echo "🌐 Access: https://testanvilcrypto.ddnsking.com"
else
    echo "❌ Failed to start frontend. Check logs: tail -f /tmp/vite.log"
    exit 1
fi
