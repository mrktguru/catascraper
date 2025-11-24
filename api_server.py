#!/usr/bin/env python3
"""
FastAPI server for Catawiki scraper - n8n integration
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, List, Union
import asyncio
import json
from datetime import datetime
from pathlib import Path
import uuid

# Import our scrapers
import sys
import csv
sys.path.append('/root/cataparser')
from scraper_pro import CatawikiScraperPro
from category_scraper import CatawikiCategoryScraper

app = FastAPI(
    title="Catawiki Scraper API",
    description="API for scraping Catawiki listings with n8n integration",
    version="1.0.0"
)

# Enable CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (for production use Redis/Database)
jobs = {}

# Request models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    headless: bool = True
    save_csv: bool = False

class BatchScrapeRequest(BaseModel):
    urls: List[HttpUrl]
    headless: bool = True
    save_csv: bool = True

class CategoryScrapeRequest(BaseModel):
    category_url: HttpUrl
    max_pages: Optional[Union[int, str]] = None
    headless: Union[bool, str] = True
    save_csv: Union[bool, str] = True

    @field_validator('max_pages', mode='before')
    @classmethod
    def parse_max_pages(cls, v):
        """Convert string 'null' or empty to None, otherwise parse as int"""
        if v is None or v == '' or v == 'null' or v == 'None':
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @field_validator('headless', 'save_csv', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Convert string 'true'/'false' to boolean"""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)

# Response models
class ScrapeResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    job_id: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "running",
        "service": "Catawiki Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "scrape": "/scrape",
            "scrape_async": "/scrape-async",
            "batch": "/scrape-batch",
            "category": "/scrape-category",
            "job_status": "/job/{job_id}",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len([j for j in jobs.values() if j["status"] == "running"])
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    """
    Scrape a single Catawiki URL (synchronous)

    This endpoint will wait for scraping to complete before returning.
    For long-running tasks, use /scrape-async instead.
    """
    try:
        scraper = CatawikiScraperPro(headless=request.headless)
        result = await scraper.scrape_listing(str(request.url))

        if result and result.get('title'):
            return ScrapeResponse(
                success=True,
                data=result
            )
        else:
            return ScrapeResponse(
                success=False,
                error="Failed to scrape data from URL"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape-async", response_model=ScrapeResponse)
async def scrape_url_async(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape a single URL asynchronously

    Returns immediately with job_id. Check status with /job/{job_id}
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None
    }

    background_tasks.add_task(
        run_scrape_job,
        job_id,
        str(request.url),
        request.headless
    )

    return ScrapeResponse(
        success=True,
        job_id=job_id,
        data={"message": "Job started", "check_status_at": f"/job/{job_id}"}
    )


@app.post("/scrape-batch", response_model=ScrapeResponse)
async def scrape_batch(request: BatchScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape multiple URLs (asynchronous)

    Returns job_id. Check status with /job/{job_id}
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "total_urls": len(request.urls),
        "processed": 0
    }

    background_tasks.add_task(
        run_batch_scrape_job,
        job_id,
        [str(url) for url in request.urls],
        request.headless,
        request.save_csv
    )

    return ScrapeResponse(
        success=True,
        job_id=job_id,
        data={
            "message": "Batch job started",
            "total_urls": len(request.urls),
            "check_status_at": f"/job/{job_id}"
        }
    )


@app.post("/scrape-category", response_model=ScrapeResponse)
async def scrape_category(request: CategoryScrapeRequest, background_tasks: BackgroundTasks):
    """
    Scrape entire Catawiki category with pagination (asynchronous)

    Returns job_id. Check status with /job/{job_id}
    """
    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "category_url": str(request.category_url),
        "max_pages": request.max_pages
    }

    background_tasks.add_task(
        run_category_scrape_job,
        job_id,
        str(request.category_url),
        request.max_pages,
        request.headless,
        request.save_csv
    )

    return ScrapeResponse(
        success=True,
        job_id=job_id,
        data={
            "message": "Category scraping job started",
            "category_url": str(request.category_url),
            "max_pages": request.max_pages or "ALL",
            "check_status_at": f"/job/{job_id}"
        }
    )


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Get status of a scraping job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatus(**jobs[job_id])


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100)
):
    """
    List recent jobs
    """
    job_list = list(jobs.values())

    # Filter by status
    if status:
        job_list = [j for j in job_list if j["status"] == status]

    # Sort by created_at (newest first)
    job_list.sort(key=lambda x: x["created_at"], reverse=True)

    # Limit results
    job_list = job_list[:limit]

    return {
        "total": len(job_list),
        "jobs": job_list
    }


@app.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from history
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]
    return {"success": True, "message": f"Job {job_id} deleted"}


# Background task functions
async def run_scrape_job(job_id: str, url: str, headless: bool):
    """Run scraping job in background"""
    try:
        jobs[job_id]["status"] = "running"

        scraper = CatawikiScraperPro(headless=headless)
        result = await scraper.scrape_listing(url)

        if result and result.get('title'):
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = result
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "No data extracted"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

    finally:
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


async def run_batch_scrape_job(job_id: str, urls: List[str], headless: bool, save_csv: bool):
    """Run batch scraping job in background"""
    try:
        jobs[job_id]["status"] = "running"
        results = []

        for i, url in enumerate(urls, 1):
            try:
                scraper = CatawikiScraperPro(headless=headless)
                result = await scraper.scrape_listing(url)

                if result and result.get('title'):
                    # Add first_image as Google Sheets formula for 100x100px preview
                    images = result.get('images', [])
                    if images:
                        result['first_image'] = f'=IMAGE("{images[0]}"; 4; 100; 100)'
                    else:
                        result['first_image'] = ''

                    # Format URL as clickable icon with HYPERLINK formula
                    url = result.get('url', '')
                    if url:
                        result['url'] = f'=HYPERLINK("{url}"; "🔗 View")'

                    # Format end_date as live countdown formula
                    end_date = result.get('end_date', '')
                    if end_date and len(end_date) == 19:  # Format: "2025-11-17 21:00:00"
                        date_part = end_date[:10]  # "2025-11-17"
                        time_part = end_date[11:]  # "21:00:00"
                        result['end_date'] = f'=DAYS(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}"); NOW()) & "d " & HOUR(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "h " & MINUTE(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "m"'

                    results.append(result)

                jobs[job_id]["processed"] = i

                # Delay between requests
                if i < len(urls):
                    await asyncio.sleep(5)

            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

        # Save results
        if results:
            # Save JSON
            output_dir = Path("/root/cataparser/output")
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = output_dir / f"batch_{job_id}_{timestamp}.json"

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Save CSV if requested
            if save_csv:
                csv_path = output_dir / f"batch_{job_id}_{timestamp}.csv"
                # Use imported save_to_csv function
                save_to_csv(results, str(csv_path))

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {
                "total_urls": len(urls),
                "successful": len(results),
                "failed": len(urls) - len(results),
                "results": results,
                "output_files": {
                    "json": str(json_path),
                    "csv": str(csv_path) if save_csv else None
                }
            }
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "No successful scrapes"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

    finally:
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


async def run_category_scrape_job(job_id: str, category_url: str, max_pages: Optional[int], headless: bool, save_csv: bool):
    """Run category scraping job in background"""
    try:
        jobs[job_id]["status"] = "running"

        # Create category scraper
        scraper = CatawikiCategoryScraper(headless=headless)

        # Scrape the category
        results = await scraper.scrape_category(category_url, max_pages=max_pages)

        # Format results with Google Sheets formulas
        formatted_results = []
        for result in results:
            # Add first_image as Google Sheets formula for 100x100px preview
            images = result.get('images', [])
            if images:
                result['first_image'] = f'=IMAGE("{images[0]}"; 4; 100; 100)'
            else:
                result['first_image'] = ''

            # Format URL as clickable icon with HYPERLINK formula
            url = result.get('url', '')
            if url:
                result['url'] = f'=HYPERLINK("{url}"; "🔗 View")'

            # Format end_date as live countdown formula
            end_date = result.get('end_date', '')
            if end_date and len(end_date) == 19:  # Format: "2025-11-17 21:00:00"
                date_part = end_date[:10]  # "2025-11-17"
                time_part = end_date[11:]  # "21:00:00"
                result['end_date'] = f'=DAYS(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}"); NOW()) & "d " & HOUR(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "h " & MINUTE(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "m"'

            formatted_results.append(result)

        # Save results
        if formatted_results:
            # Save JSON
            output_dir = Path("/root/cataparser/output")
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_path = output_dir / f"category_{job_id}_{timestamp}.json"

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)

            # Save CSV if requested
            if save_csv:
                csv_path = output_dir / f"category_{job_id}_{timestamp}.csv"
                save_to_csv(formatted_results, str(csv_path))

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["result"] = {
                "category_url": category_url,
                "max_pages": max_pages,
                "total_lots": len(formatted_results),
                "results": formatted_results,
                "output_files": {
                    "json": str(json_path),
                    "csv": str(csv_path) if save_csv else None
                }
            }
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "No lots scraped from category"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

    finally:
        jobs[job_id]["completed_at"] = datetime.now().isoformat()


def save_to_csv(data_list: list, filename: str):
    """Save scraped data to CSV file"""
    if not data_list:
        print("No data to save to CSV")
        return

    # CSV columns
    fieldnames = [
        'title',
        'bottles_count',
        'seller_name',
        'current_price',
        'shipping_cost',
        'end_date',
        'images_count',
        'first_image',
        'url',
        'scraped_at',
        'producer_rating',
        'vintage_rating',
        'region_rating',
        'overall_appeal',
        'investment_potential',
    ]

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for item in data_list:
            # Get first image URL
            first_img_url = item.get('images', [''])[0] if item.get('images') else ''
            # Create Google Sheets IMAGE formula for 100x100px preview
            first_image_formula = f'=IMAGE("{first_img_url}"; 4; 100; 100)' if first_img_url else ''

            # Get URL and format as clickable icon if not already formatted
            url = item.get('url', '')
            if url and not url.startswith('=HYPERLINK'):
                url = f'=HYPERLINK("{url}"; "🔗 View")'

            # Format end_date as live countdown formula if not already formatted
            end_date = item.get('end_date', '')
            if end_date and not end_date.startswith('=') and len(end_date) == 19:
                date_part = end_date[:10]
                time_part = end_date[11:]
                end_date = f'=DAYS(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}"); NOW()) & "d " & HOUR(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "h " & MINUTE(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW()) & "m"'

            # Prepare row data
            row = {
                'title': item.get('title', ''),
                'bottles_count': item.get('bottles_count', ''),
                'seller_name': item.get('seller_name', ''),
                'current_price': item.get('current_price', ''),
                'shipping_cost': item.get('shipping_cost', ''),
                'end_date': end_date,
                'images_count': len(item.get('images', [])),
                'first_image': first_image_formula,
                'url': url,
                'scraped_at': item.get('scraped_at', ''),
                'producer_rating': item.get('producer_rating', ''),
                'vintage_rating': item.get('vintage_rating', ''),
                'region_rating': item.get('region_rating', ''),
                'overall_appeal': item.get('overall_appeal', ''),
                'investment_potential': item.get('investment_potential', ''),
            }
            writer.writerow(row)

    print(f"💾 CSV saved to: {filename}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1  # Single worker to save memory
    )
