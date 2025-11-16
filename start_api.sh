#!/bin/bash
# Start Catawiki API server

echo "🚀 Starting Catawiki Scraper API..."
echo ""

# Check if running as systemd service
if systemctl is-active --quiet catawiki-api; then
    echo "✓ API is already running as systemd service"
    echo ""
    echo "Status:"
    systemctl status catawiki-api --no-pager
    echo ""
    echo "Logs:"
    echo "  tail -f /var/log/catawiki-api.log"
    echo ""
    echo "Stop:"
    echo "  systemctl stop catawiki-api"
    exit 0
fi

# Check if port is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use"
    echo ""
    echo "Process:"
    lsof -i :8000
    echo ""
    echo "To kill: sudo kill -9 \$(lsof -t -i:8000)"
    exit 1
fi

# Check dependencies
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
cd /root/cataparser

echo "Starting API server on http://0.0.0.0:8000"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 api_server.py
