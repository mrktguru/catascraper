# 📂 Catawiki Category Scraper Guide

## 📋 Overview

The Category Scraper allows you to scrape **entire categories** from Catawiki, automatically visiting each lot and extracting data from all pages with pagination support.

**Flow:**
1. Paste category/filter URL in Google Sheets "URL-CAT" page
2. n8n workflow triggers and scrapes all wines in that category
3. Results are written to Google Sheets "CATALOG" page

---

## 🎯 What Gets Scraped

**Input:** Category or filter URLs like:
```
https://www.catawiki.com/en/s?q=burgundy&filters=l2_categories%255B%255D%3D463
```

**Output Data Fields:**
- `first_image` - 100x100px preview (IMAGE formula)
- `title` - Wine title
- `bottles_count` - Number of bottles
- `seller_name` - Seller name
- `current_price` - Current bid price
- `shipping_cost` - Shipping cost
- `end_date` - Live countdown timer (formula)
- `images_count` - Total number of images
- `url` - Clickable link (HYPERLINK formula)
- `scraped_at` - Timestamp
- `producer_rating` - AI rating (if configured)
- `vintage_rating` - AI rating (if configured)
- `region_rating` - AI rating (if configured)
- `overall_appeal` - AI rating (if configured)
- `investment_potential` - AI rating (if configured)

---

## 🔧 Setup Instructions

### Step 1: Create Google Sheets Pages

1. Open your Google Spreadsheet
2. Create two new sheets:
   - **URL-CAT** (for input category URLs)
   - **CATALOG** (for output results)

#### URL-CAT Sheet Structure:

| A |
|---|
| category_url |
| https://www.catawiki.com/en/s?q=burgundy&filters=... |

**Instructions:**
- Column A header: `category_url`
- Row 2: Paste your category/filter URL
- Only the first URL will be processed per workflow run

#### CATALOG Sheet Structure:

Headers (Row 1):
```
| title | bottles_count | seller_name | current_price | shipping_cost | end_date | images_count | first_image | url | scraped_at | producer_rating | vintage_rating | region_rating | overall_appeal | investment_potential |
```

Leave the rest empty - the workflow will populate it.

---

### Step 2: Import n8n Workflow

1. Open n8n
2. Click **"Workflows"** → **"Add Workflow"** → **"Import from File"**
3. Select `n8n_workflow_category.json`
4. Workflow imported!

---

### Step 3: Configure Google Sheets Credentials

#### Node: "Read Category URLs"

1. Click on the node
2. **Document**: Select your spreadsheet
3. **Sheet**: Enter `URL-CAT` (exact name)
4. **Options** → **Range**: `A2:A` (skips header row)

#### Node: "Write to CATALOG Sheet"

1. Click on the node
2. **Document**: Select your spreadsheet
3. **Sheet**: Enter `CATALOG` (exact name)
4. **Columns**: Already configured ✅

---

### Step 4: Configure API Server URL

If your API server is NOT running on `http://172.17.0.1:8000`, update these nodes:

#### Node: "Start Category Scraping Job"
- **URL**: Change to your API server address
- Example: `http://localhost:8000/scrape-category`

#### Node: "Check Status"
- **URL**: Change to your API server address
- Example: `http://localhost:8000/job/{{ $json.job_id }}`

---

### Step 5: Adjust Wait Times (Optional)

Category scraping can take a long time depending on:
- Number of pages in category
- Number of lots per page
- Network speed

**Default wait times:**
- Initial wait: **5 minutes**
- Retry wait: **2 minutes**

To change:

#### Node: "Wait 5 Minutes"
- Change `amount` to desired minutes
- For large categories (100+ lots): use 10-15 minutes

#### Node: "Wait 2 More Minutes"
- Change `amount` for retry interval

---

## 🚀 Usage

### Method 1: Manual Trigger

1. Open Google Sheets "URL-CAT"
2. Paste category URL in cell A2
3. Open n8n workflow
4. Click **"Execute Workflow"**
5. Wait for completion
6. Check Google Sheets "CATALOG" for results

### Method 2: Scheduled Trigger

The workflow runs daily at **10:00 AM** by default.

To change schedule:

1. Click on "Schedule Trigger" node
2. Change `cronExpression`:
   - `0 9 * * *` - Every day at 9 AM
   - `0 */6 * * *` - Every 6 hours
   - `0 12 * * 1` - Every Monday at 12 PM

---

## 📊 Example Category URLs

### Burgundy Wines:
```
https://www.catawiki.com/en/s?q=burgundy&filters=l2_categories%255B%255D%3D463
```

### Bordeaux Wines Ending in 20 Days:
```
https://www.catawiki.com/en/s?q=bordeaux&filters=l2_categories%255B%255D%3D463%26bidding_end_days%255B%255D%3D20251125
```

### Search by Region:
```
https://www.catawiki.com/en/s?q=champagne&filters=l2_categories%255B%255D%3D463
```

---

## 🔄 Workflow Flow Diagram

```
┌─────────────────────┐
│ Schedule Trigger    │ (Daily at 10 AM)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Read Category URLs  │ (From URL-CAT sheet)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Prepare Category URL│ (Extract URL from column A)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Start Category Job  │ (POST /scrape-category)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Wait 5 Minutes      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check Status        │ (GET /job/{job_id})
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check If Completed  │
└──────┬──────┬───────┘
       │      │      │
   Complete  Error  Running
       │      │      │
       ▼      ▼      ▼
   ┌────┐  ┌────┐  ┌────────────┐
   │ OK │  │Err │  │Wait 2 More │ → Retry
   └────┘  └────┘  └────────────┘
       │
       ▼
┌─────────────────────┐
│ Format Results      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Write to CATALOG    │
└─────────────────────┘
```

---

## 🧪 Testing

### Test with Small Category:

1. Find a small category (2-3 pages, ~30-50 lots)
2. Paste URL in URL-CAT
3. Execute workflow manually
4. Monitor n8n execution logs
5. Check CATALOG sheet for results

### Check Job Status Manually:

```bash
# Get job_id from workflow execution
curl http://172.17.0.1:8000/job/YOUR_JOB_ID

# Response example:
{
  "job_id": "abc-123",
  "status": "running",  # or "completed" / "failed"
  "result": { ... },
  "created_at": "2025-11-24T10:00:00",
  "completed_at": null
}
```

---

## 🎛️ API Endpoint Details

### POST /scrape-category

**Request:**
```json
{
  "category_url": "https://www.catawiki.com/en/s?q=burgundy",
  "max_pages": null,
  "headless": true,
  "save_csv": true
}
```

**Parameters:**
- `category_url` (required) - Catawiki category/filter URL
- `max_pages` (optional) - Limit pages to scrape (null = all pages)
- `headless` (optional) - Run browser in headless mode (default: true)
- `save_csv` (optional) - Save results to CSV file (default: true)

**Response:**
```json
{
  "success": true,
  "job_id": "abc-123-def-456",
  "data": {
    "message": "Category scraping job started",
    "category_url": "https://www.catawiki.com/en/s?q=burgundy",
    "max_pages": "ALL",
    "check_status_at": "/job/abc-123-def-456"
  }
}
```

### GET /job/{job_id}

**Response (completed):**
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "result": {
    "category_url": "https://...",
    "max_pages": null,
    "total_lots": 45,
    "results": [
      {
        "title": "1989 Veuve Clicquot",
        "bottles_count": "1 bottle",
        "current_price": "€50",
        ...
      }
    ],
    "output_files": {
      "json": "/root/cataparser/output/category_abc_20251124.json",
      "csv": "/root/cataparser/output/category_abc_20251124.csv"
    }
  },
  "created_at": "2025-11-24T10:00:00",
  "completed_at": "2025-11-24T10:15:00"
}
```

---

## 🐛 Troubleshooting

### Problem: "No valid category URL found in URL-CAT sheet"

**Solution:**

1. **Check Range setting in "Read Category URLs" node:**
   - Open the node
   - Go to **Options** → **Range**
   - Should be `A2:A` (not `A:A` or `A1:A`)
   - This skips the header row

2. **Check URL format:**
   - URL must start with `http://` or `https://`
   - Example: `https://www.catawiki.com/en/s?q=burgundy&filters=...`
   - Remove any spaces before/after URL

3. **Check cell location:**
   - URL should be in cell **A2** (first data row)
   - Cell A1 should be header: `category_url` (optional)

4. **Debug in n8n:**
   - Execute workflow manually
   - Click on "Read Category URLs" node
   - Check output - should see your URL
   - Click on "Prepare Category URL" node
   - Check logs in browser console (F12)

### Problem: Job stuck in "running" status

**Solution:**
- Category might be very large
- Increase wait time to 10-15 minutes
- Check API server logs for errors
- Manually check job status with curl

### Problem: No results in CATALOG sheet

**Solution:**
- Check job status shows "completed"
- Verify CATALOG sheet name is exact (case-sensitive)
- Check n8n execution logs for errors
- Ensure Google Sheets credentials are valid

### Problem: Some lots missing

**Solution:**
- Check category scraper logs for errors
- Some lots might fail to load (network issues)
- Check `total_lots` in job result vs actual rows in CATALOG
- Failed lots are skipped, not retried

---

## ⚙️ Advanced Configuration

### Limit Pages to Scrape

To scrape only first N pages (faster testing):

**Node: "Start Category Scraping Job"**

Change:
```json
{
  "name": "max_pages",
  "value": "=null"
}
```

To:
```json
{
  "name": "max_pages",
  "value": "=2"  // Only scrape first 2 pages
}
```

### Change Delay Between Lots

Edit `category_scraper.py`:

```python
# Line 179
await asyncio.sleep(3)  # Change to desired seconds
```

**Recommended:**
- Fast scraping: 2-3 seconds
- Safe scraping: 5-7 seconds
- Very safe: 10 seconds

---

## 📝 Notes

- **Pagination:** Automatically detects and scrapes all pages
- **Deduplication:** Duplicate lot URLs are automatically removed
- **Error handling:** Failed lots are skipped, workflow continues
- **Output files:** JSON and CSV saved to `/root/cataparser/output/`
- **Rate limiting:** 3 second delay between lots (configurable)
- **Browser:** Uses Playwright with Akamai bypass
- **AI ratings:** Supported if configured (see AI_INTEGRATION_GUIDE.md)

---

## 🔗 Related Documentation

- **AI Integration:** See `AI_INTEGRATION_GUIDE.md` for adding AI wine ratings
- **API Server:** See `api_server.py` for endpoint details
- **Category Scraper:** See `category_scraper.py` for implementation
- **Batch Scraper:** See `n8n_workflow_complete.json` for batch scraping

---

## ✅ Ready to Use!

1. ✅ Create URL-CAT and CATALOG sheets
2. ✅ Import n8n_workflow_category.json
3. ✅ Configure Google Sheets credentials
4. ✅ Paste category URL in URL-CAT
5. ✅ Execute workflow
6. ✅ Check CATALOG sheet for results

**Example Result:**

| title | bottles_count | seller_name | current_price | ... |
|-------|---------------|-------------|---------------|-----|
| 1989 Veuve Clicquot | 1 bottle | Wine Seller Pro | €50 | ... |
| 2010 Bordeaux Grand Cru | 6 bottles | French Wines | €120 | ... |
| ... | ... | ... | ... | ... |

🎉 **Enjoy automated category scraping!**
