#!/usr/bin/env python3
"""
Batch scraper with CSV export for Catawiki
"""

import sys
import json
import asyncio
import csv
from pathlib import Path
from datetime import datetime
from scraper_pro import CatawikiScraperPro


async def scrape_multiple_urls(urls: list, output_dir: str = 'output', headless: bool = True, save_csv: bool = True):
    """
    Scrape multiple Catawiki URLs and save results

    Args:
        urls: List of URLs to scrape
        output_dir: Directory to save results
        headless: Run browser in headless mode
        save_csv: Export to CSV
    """

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    scraper = CatawikiScraperPro(headless=headless)

    results = []
    successful = 0
    failed = 0

    print(f"\n{'='*70}")
    print(f"🔍 Batch Scraping {len(urls)} URLs")
    print(f"{'='*70}\n")

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        print("-" * 70)

        try:
            data = await scraper.scrape_listing(url)

            if data and data.get('title'):
                successful += 1
                results.append(data)

                # Save individual JSON
                safe_filename = f"listing_{i:03d}.json"
                individual_path = output_path / safe_filename

                with open(individual_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"✅ Success! Saved to {individual_path}")

            else:
                failed += 1
                print(f"❌ Failed to scrape")

        except Exception as e:
            failed += 1
            print(f"❌ Error: {e}")

        # Delay between requests
        if i < len(urls):
            delay = 5
            print(f"⏳ Waiting {delay}s before next request...")
            await asyncio.sleep(delay)

    # Save summary JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_path = output_path / f'summary_{timestamp}.json'

    summary = {
        'total': len(urls),
        'successful': successful,
        'failed': failed,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Save CSV
    if save_csv and results:
        csv_path = output_path / f'catawiki_export_{timestamp}.csv'
        save_to_csv(results, str(csv_path))

    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY")
    print(f"{'='*70}")
    print(f"Total URLs: {len(urls)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"💾 Summary JSON: {summary_path}")
    if save_csv and results:
        print(f"📊 CSV Export: {csv_path}")
    print(f"{'='*70}\n")

    return summary


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
    ]

    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

        writer.writeheader()

        for item in data_list:
            # Get first image URL
            first_img_url = item.get('images', [''])[0] if item.get('images') else ''
            # Create Google Sheets IMAGE formula for 100x100px preview
            first_image_formula = f'=IMAGE("{first_img_url}", 4, 100, 100)' if first_img_url else ''

            # Get URL and format as clickable icon
            url = item.get('url', '')
            if url:
                url = f'=HYPERLINK("{url}", "🔗 View")'

            # Format end_date as live countdown formula
            end_date = item.get('end_date', '')
            if end_date and len(end_date) == 19:  # Format: "2025-11-17 21:00:00"
                date_part = end_date[:10]
                time_part = end_date[11:]
                end_date = f'=TEXT(DATEVALUE("{date_part}") + TIMEVALUE("{time_part}") - NOW(), "[d]d [h]h [m]m")'

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
            }

            writer.writerow(row)

    print(f"💾 CSV saved to: {filename}")
    print(f"📊 Total rows: {len(data_list)}")


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_scraper_pro.py <urls_file.txt> [--headless] [--no-csv]")
        print("  python batch_scraper_pro.py url1 url2 url3 [--headless] [--no-csv]")
        print("\nExamples:")
        print("  python batch_scraper_pro.py urls.txt")
        print("  python batch_scraper_pro.py 'URL1' 'URL2' --headless")
        print("\nOptions:")
        print("  --headless    Run in headless mode")
        print("  --no-csv      Don't export to CSV")
        sys.exit(1)

    headless = '--headless' in sys.argv
    save_csv = '--no-csv' not in sys.argv
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]

    # Check if first argument is a file
    urls = []
    if len(args) == 1 and Path(args[0]).exists():
        # Read URLs from file
        with open(args[0], 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        print(f"📁 Loaded {len(urls)} URLs from {args[0]}")
    else:
        # Use command line arguments as URLs
        urls = args

    if not urls:
        print("❌ No URLs provided")
        sys.exit(1)

    await scrape_multiple_urls(urls, headless=headless, save_csv=save_csv)


if __name__ == '__main__':
    asyncio.run(main())
