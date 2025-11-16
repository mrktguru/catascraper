#!/bin/bash
# Setup script for Catawiki scraper

echo "🚀 Setting up Catawiki Scraper..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium browser..."
playwright install chromium

# Create output directory
mkdir -p output

echo ""
echo "✅ Setup complete!"
echo ""
echo "To use the scraper:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run scraper: python advanced_scraper.py 'URL'"
echo ""
