#!/bin/bash
# Test Catawiki API

API_URL="http://localhost:8000"
TEST_URL="https://www.catawiki.com/en/l/98998534-2022-beaune-1-cru-belissand-domaine-francoise-andre-burgundy-6-bottles-0-75l"

echo "🧪 Testing Catawiki Scraper API"
echo "================================"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "--------------------"
response=$(curl -s "$API_URL/health")
if [ $? -eq 0 ]; then
    echo "✓ API is responding"
    echo "$response" | python3 -m json.tool
else
    echo "✗ API is not responding"
    echo "Make sure API server is running: ./start_api.sh"
    exit 1
fi
echo ""

# Test 2: Root endpoint
echo "Test 2: Root Endpoint"
echo "---------------------"
curl -s "$API_URL/" | python3 -m json.tool
echo ""
echo ""

# Test 3: Single scrape (sync)
echo "Test 3: Single URL Scrape (synchronous)"
echo "----------------------------------------"
echo "This will take ~10-20 seconds..."
echo ""

response=$(curl -s -X POST "$API_URL/scrape" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$TEST_URL\",
    \"headless\": true
  }")

echo "$response" | python3 -m json.tool

# Check if successful
success=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")
if [ "$success" = "True" ]; then
    echo ""
    echo "✓ Scraping successful!"
else
    echo ""
    echo "✗ Scraping failed"
fi
echo ""

# Test 4: Async scrape
echo "Test 4: Async Scrape"
echo "--------------------"
response=$(curl -s -X POST "$API_URL/scrape-async" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$TEST_URL\",
    \"headless\": true
  }")

echo "$response" | python3 -m json.tool

job_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('job_id', ''))")

if [ -n "$job_id" ]; then
    echo ""
    echo "Job ID: $job_id"
    echo "Waiting 15 seconds for job to complete..."
    sleep 15

    echo ""
    echo "Checking job status..."
    curl -s "$API_URL/job/$job_id" | python3 -m json.tool
fi
echo ""

# Test 5: List jobs
echo "Test 5: List Recent Jobs"
echo "------------------------"
curl -s "$API_URL/jobs?limit=5" | python3 -m json.tool
echo ""

echo "================================"
echo "✅ API tests completed!"
echo ""
echo "Next steps:"
echo "1. Open Swagger UI: http://your-server:8000/docs"
echo "2. Import n8n workflows from n8n_workflow_*.json"
echo "3. Create your automation!"
