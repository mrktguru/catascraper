#!/usr/bin/env python3
"""
Fast Catawiki scraper with improved timeout handling
"""

import sys
import json
import asyncio
import random
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Optional, Dict
import re


class FastCatawikiScraper:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy

    async def scrape_listing(self, url: str) -> Optional[Dict]:
        """Scrape Catawiki listing with faster timeouts"""

        print(f"[{time.strftime('%H:%M:%S')}] 🚀 Starting browser...")

        async with async_playwright() as p:
            try:
                # Launch browser
                launch_args = {
                    'headless': self.headless,
                    'args': [
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-gpu',
                        '--single-process',  # Better for low-memory servers
                    ],
                    'timeout': 30000,  # 30 second browser launch timeout
                }

                if self.proxy:
                    launch_args['proxy'] = {'server': self.proxy}

                browser = await p.chromium.launch(**launch_args)
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Browser launched")

                # Create context
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='Europe/Amsterdam',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                )
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Context created")

                # Add stealth script
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """)

                page = await context.new_page()
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Page created")

                # Navigate with shorter timeout
                print(f"[{time.strftime('%H:%M:%S')}] 🌐 Loading: {url[:80]}...")

                try:
                    # Use domcontentloaded instead of networkidle - much faster!
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Page loaded (status: {response.status if response else 'unknown'})")

                    if response and response.status == 403:
                        print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Got 403 - Akamai blocked")
                        await browser.close()
                        return None

                except PlaywrightTimeout:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Timeout on goto, but page might have loaded...")
                    # Continue anyway - page might be partially loaded

                # Wait a bit for dynamic content
                print(f"[{time.strftime('%H:%M:%S')}] ⏳ Waiting for content...")
                try:
                    await page.wait_for_selector('h1', timeout=10000)
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Title element found")
                except PlaywrightTimeout:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Title element not found, continuing...")

                # Small delay
                await asyncio.sleep(2)

                # Extract data
                print(f"[{time.strftime('%H:%M:%S')}] 📊 Extracting data...")
                data = await self._extract_data(page)

                # Save debug info
                try:
                    await page.screenshot(path='debug_screenshot.png')
                    print(f"[{time.strftime('%H:%M:%S')}] 📸 Screenshot saved")
                except Exception as e:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Screenshot failed: {e}")

                await browser.close()
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Browser closed")

                return data

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ Error: {e}")
                try:
                    await browser.close()
                except:
                    pass
                return None

    async def _extract_data(self, page) -> Dict:
        """Extract data from page"""

        data = {
            'title': None,
            'images': [],
            'bottles_count': None,
            'seller': None,
            'current_price': None,
            'url': page.url,
        }

        # Get page text for fallback parsing
        try:
            page_text = await page.inner_text('body')
        except:
            page_text = ""

        # Extract title
        title_selectors = ['h1', '[data-testid*="title"]', '.lot-title', 'main h1']
        for selector in title_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 5:
                        data['title'] = text.strip()
                        print(f"[{time.strftime('%H:%M:%S')}] ✓ Title: {data['title'][:50]}...")
                        break
            except:
                continue

        # Extract images
        image_selectors = [
            'img[src*="catawiki"]',
            'main img',
            'picture img',
            'img[alt]',
        ]

        for selector in image_selectors:
            try:
                images = await page.query_selector_all(selector)
                for img in images[:10]:  # Limit to 10 images
                    src = await img.get_attribute('src')
                    if src and 'catawiki' in src and not src.startswith('data:'):
                        data['images'].append(src)
                if data['images']:
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Found {len(data['images'])} images")
                    break
            except:
                continue

        # Remove duplicates
        data['images'] = list(dict.fromkeys(data['images']))

        # Extract bottles count from text
        bottle_patterns = [
            r'(\d+)\s*(?:x\s*)?bottle[s]?',
            r'(\d+)\s*x\s*0[.,]\d+\s*[lL]',
        ]

        for pattern in bottle_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                data['bottles_count'] = match.group(1)
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Bottles: {data['bottles_count']}")
                break

        # Extract seller
        seller_selectors = [
            '[data-testid*="seller"]',
            'a[href*="/u/"]',
            '.seller-name',
        ]

        for selector in seller_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 2:
                        data['seller'] = text.strip()
                        print(f"[{time.strftime('%H:%M:%S')}] ✓ Seller: {data['seller']}")
                        break
            except:
                continue

        # Extract price
        price_selectors = [
            '[data-testid*="bid"]',
            '[data-testid*="price"]',
            '.current-bid',
            'span[class*="price"]',
        ]

        for selector in price_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and ('€' in text or '$' in text or '£' in text):
                        data['current_price'] = text.strip()
                        print(f"[{time.strftime('%H:%M:%S')}] ✓ Price: {data['current_price']}")
                        break
            except:
                continue

        # Fallback: extract price from page text
        if not data['current_price']:
            price_match = re.search(r'€\s*[\d,]+(?:\.\d{2})?', page_text)
            if price_match:
                data['current_price'] = price_match.group(0).strip()
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Price (regex): {data['current_price']}")

        # Save HTML for debugging if extraction failed
        if not data['title']:
            try:
                html = await page.content()
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"[{time.strftime('%H:%M:%S')}] 💾 Saved HTML to debug_page.html")
            except:
                pass

        return data


async def main():
    if len(sys.argv) < 2:
        print("Usage: python fast_scraper.py <URL> [--headless]")
        print("\nExample:")
        print("  python fast_scraper.py 'https://www.catawiki.com/en/l/...'")
        print("  python fast_scraper.py 'URL' --headless")
        sys.exit(1)

    url = sys.argv[1]
    headless = '--headless' in sys.argv

    print("=" * 70)
    print("🔍 Fast Catawiki Scraper")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Headless: {headless}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    scraper = FastCatawikiScraper(headless=headless)
    result = await scraper.scrape_listing(url)

    if result:
        print()
        print("=" * 70)
        print("✅ SUCCESS - Scraped Data:")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

        # Save to file
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("💾 Data saved to scraped_data.json")
        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print("❌ FAILED - Could not scrape data")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Check debug_screenshot.png and debug_page.html")
        print("2. Try running without --headless to see what happens")
        print("3. Check if Akamai is blocking (403 error)")
        print("4. Ensure all dependencies are installed:")
        print("   python3 -m playwright install-deps chromium")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
