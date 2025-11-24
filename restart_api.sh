#!/bin/bash
# Restart Catawiki API server
# Usage: ./restart_api.sh

echo "🔄 Restarting Catawiki Scraper API..."
echo ""

# Find and kill existing process
PID=$(lsof -t -i:8000 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "Stopping existing API server (PID: $PID)..."
    kill -9 $PID
    sleep 2
    echo "✓ Stopped"
else
    echo "No existing API server found"
fi

# Verify port is free
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Port 8000 is still in use. Please kill the process manually:"
    lsof -i :8000
    exit 1
fi

# Check dependencies
echo ""
echo "Checking dependencies..."
python3 -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ API dependencies not installed"
    echo "Run: pip3 install -r requirements_api.txt"
    exit 1
fi
echo "✓ API dependencies OK"

# Check Playwright browsers
python3 -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Playwright browser not installed"
    echo ""
    echo "API will start, but scraping will fail until you run:"
    echo "  python3 -m playwright install chromium"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ Playwright browser OK"
fi
echo ""

# Determine working directory (try production path first, fallback to dev)
if [ -d "/root/cataparser" ]; then
    cd /root/cataparser
elif [ -d "/home/user/catascraper" ]; then
    cd /home/user/catascraper
else
    echo "❌ Cannot find project directory"
    exit 1
fi

echo "Working directory: $(pwd)"
echo ""

echo "Starting API server on http://0.0.0.0:8000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""

nohup python3 api_server.py > /tmp/catawiki-api.log 2>&1 &
NEW_PID=$!

sleep 3

# Verify server started
if ps -p $NEW_PID > /dev/null; then
    echo "✅ API server started successfully (PID: $NEW_PID)"
    echo ""
    echo "Logs: tail -f /tmp/catawiki-api.log"
    echo "Stop: kill -9 $NEW_PID"
else
    echo "❌ Failed to start API server. Check logs:"
    cat /tmp/catawiki-api.log
    exit 1
fi
