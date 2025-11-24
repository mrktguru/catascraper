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
    echo "❌ Dependencies not installed"
    echo "Run: pip3 install -r requirements_api.txt"
    exit 1
fi
echo "✓ Dependencies OK"
echo ""

# Start server
cd /home/user/catascraper

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
