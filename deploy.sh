#!/bin/bash
# Deployment script for Catawiki scraper

SERVER="root@38.244.194.181"
REMOTE_DIR="/root/cataparser"
LOCAL_DIR="/home/user/catascraper"

echo "🚀 Deploying Catawiki Scraper to server..."
echo "Server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo ""

# Check if we can connect to server
echo "📡 Testing connection to server..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $SERVER "echo 'Connection successful'" 2>/dev/null; then
    echo "⚠️  Cannot connect with SSH key. You may need to enter password."
fi

# Create remote directory if it doesn't exist
echo "📁 Creating remote directory..."
ssh $SERVER "mkdir -p $REMOTE_DIR"

# Sync files (excluding git, cache, debug files)
echo "📤 Syncing files to server..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude 'venv' \
    --exclude 'debug_*' \
    --exclude 'error_*' \
    --exclude 'scraped_data.json' \
    --exclude 'output' \
    $LOCAL_DIR/ $SERVER:$REMOTE_DIR/

# Check Python version on server
echo ""
echo "🐍 Checking Python on server..."
ssh $SERVER "cd $REMOTE_DIR && python3 --version"

# Install dependencies
echo ""
echo "📦 Installing dependencies on server..."
ssh $SERVER "cd $REMOTE_DIR && pip3 install -r requirements.txt"

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright Chromium..."
ssh $SERVER "cd $REMOTE_DIR && playwright install chromium"

# Make scripts executable
echo ""
echo "🔧 Setting permissions..."
ssh $SERVER "cd $REMOTE_DIR && chmod +x *.py setup.sh"

# Show final status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "To run scraper on server:"
echo "  ssh $SERVER"
echo "  cd $REMOTE_DIR"
echo "  python3 advanced_scraper.py 'URL' --headless"
echo ""
