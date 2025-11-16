#!/bin/bash
# Server setup script - run this ON THE SERVER (root@38.244.194.181)

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════"
echo "  Catawiki Scraper - Server Setup"
echo "════════════════════════════════════════════════════════════"
echo ""

# Configuration
INSTALL_DIR="/root/cataparser"
REPO_URL="https://github.com/mrktguru/catascraper.git"  # Update if different

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Not running as root. You may need sudo for some operations.${NC}"
fi

# Step 1: Create directory
echo -e "${GREEN}[1/7]${NC} Creating installation directory..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
echo "✓ Directory created: $INSTALL_DIR"
echo ""

# Step 2: Check Python
echo -e "${GREEN}[2/7]${NC} Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python 3 not found!${NC}"
    echo "Installing Python 3..."
    apt-get update && apt-get install -y python3 python3-pip
fi
echo ""

# Step 3: Get code
echo -e "${GREEN}[3/7]${NC} Getting code..."
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest changes..."
    git pull origin main || git pull origin master
else
    echo "Cloning repository..."
    git clone "$REPO_URL" . || {
        echo -e "${YELLOW}⚠️  Git clone failed. Files might be uploaded manually.${NC}"
    }
fi
echo ""

# Step 4: Install Python dependencies
echo -e "${GREEN}[4/7]${NC} Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt
echo "✓ Python packages installed"
echo ""

# Step 5: Install Playwright
echo -e "${GREEN}[5/7]${NC} Installing Playwright..."
python3 -m playwright install chromium
echo "✓ Chromium browser installed"
echo ""

# Step 6: Install system dependencies for Playwright
echo -e "${GREEN}[6/7]${NC} Installing system dependencies..."
python3 -m playwright install-deps chromium 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Auto-install failed, trying manual install...${NC}"
    apt-get update
    apt-get install -y \
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libasound2 \
        libxshmfence1
}
echo "✓ System dependencies installed"
echo ""

# Step 7: Set permissions
echo -e "${GREEN}[7/7]${NC} Setting permissions..."
chmod +x *.py *.sh 2>/dev/null || true
echo "✓ Permissions set"
echo ""

# Create output directory
mkdir -p output

# Final check
echo "════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ Installation complete!${NC}"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo "Python version: $(python3 --version)"
echo "Playwright: $(python3 -c 'import playwright; print(playwright.__version__)' 2>/dev/null || echo 'Error checking version')"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Quick Start"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Test scraper:"
echo "  cd $INSTALL_DIR"
echo '  python3 advanced_scraper.py "URL" --headless'
echo ""
echo "Batch scraping:"
echo "  cd $INSTALL_DIR"
echo "  python3 batch_scraper.py example_urls.txt --headless"
echo ""
echo "View help:"
echo "  python3 advanced_scraper.py --help"
echo ""
echo "════════════════════════════════════════════════════════════"
