#!/usr/bin/env python3
"""
Batch scraper for multiple Catawiki URLs
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from advanced_scraper import AdvancedCatawikiScraper


async def scrape_multiple_urls(urls: list, output_dir: str = 'output', headless: bool = True):
    """
    Scrape multiple Catawiki URLs and save results

    Args:
        urls: List of URLs to scrape
        output_dir: Directory to save results
        headless: Run browser in headless mode
    """

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    scraper = AdvancedCatawikiScraper(headless=headless)

    results = []
    successful = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"🔍 Batch Scraping {len(urls)} URLs")
    print(f"{'='*60}\n")

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        print("-" * 60)

        try:
            data = await scraper.scrape_listing(url)

            if data and data.get('title'):
                successful += 1
                results.append({
                    'url': url,
                    'status': 'success',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                })

                # Save individual result
                safe_filename = f"listing_{i:03d}.json"
                individual_path = output_path / safe_filename

                with open(individual_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"✅ Success! Saved to {individual_path}")

            else:
                failed += 1
                results.append({
                    'url': url,
                    'status': 'failed',
                    'data': None,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"❌ Failed to scrape")

        except Exception as e:
            failed += 1
            results.append({
                'url': url,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            print(f"❌ Error: {e}")

        # Delay between requests
        if i < len(urls):
            delay = 5
            print(f"⏳ Waiting {delay}s before next request...")
            await asyncio.sleep(delay)

    # Save summary
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

    # Print summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total URLs: {len(urls)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"💾 Summary saved to: {summary_path}")
    print(f"{'='*60}\n")

    return summary


async def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_scraper.py <urls_file.txt> [--headless]")
        print("  python batch_scraper.py url1 url2 url3 [--headless]")
        print("\nExamples:")
        print("  python batch_scraper.py urls.txt")
        print("  python batch_scraper.py 'URL1' 'URL2' 'URL3' --headless")
        sys.exit(1)

    headless = '--headless' in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != '--headless']

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

    await scrape_multiple_urls(urls, headless=headless)


if __name__ == '__main__':
    asyncio.run(main())
