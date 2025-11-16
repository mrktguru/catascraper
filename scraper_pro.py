#!/usr/bin/env python3
"""
Professional Catawiki scraper with clean data extraction and CSV export
"""

import sys
import json
import asyncio
import time
import re
import csv
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Optional, Dict
from pathlib import Path


class CatawikiScraperPro:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy

    async def scrape_listing(self, url: str) -> Optional[Dict]:
        """Scrape Catawiki listing with clean data"""

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
                        '--single-process',
                    ],
                    'timeout': 30000,
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

                # Add stealth script
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                    window.chrome = {runtime: {}};
                """)

                page = await context.new_page()
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Page created")

                # Navigate
                print(f"[{time.strftime('%H:%M:%S')}] 🌐 Loading: {url[:80]}...")

                try:
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Page loaded (status: {response.status if response else 'unknown'})")

                    if response and response.status == 403:
                        print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Got 403 - Akamai blocked")
                        await browser.close()
                        return None

                except PlaywrightTimeout:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Timeout on goto, continuing...")

                # Wait for content
                print(f"[{time.strftime('%H:%M:%S')}] ⏳ Waiting for content...")
                try:
                    await page.wait_for_selector('h1', timeout=10000)
                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Title element found")
                except PlaywrightTimeout:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️  Title element not found, continuing...")

                await asyncio.sleep(2)

                # Extract data
                print(f"[{time.strftime('%H:%M:%S')}] 📊 Extracting data...")
                data = await self._extract_data(page)

                # Save screenshot
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
        """Extract clean data from page"""

        data = {
            'title': None,
            'images': [],
            'bottles_count': None,
            'seller_name': None,
            'current_price': None,
            'shipping_cost': None,
            'end_date': None,
            'url': page.url,
            'scraped_at': datetime.now().isoformat(),
        }

        # Get page text
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
                        print(f"[{time.strftime('%H:%M:%S')}] ✓ Title: {data['title'][:60]}...")
                        break
            except:
                continue

        # Extract product images only (filter out icons, flags, logos)
        image_selectors = [
            'img[src*="assets.catawiki"]',
            'main img[src*="catawiki"]',
            'picture img[src*="catawiki"]',
        ]

        all_images = []
        for selector in image_selectors:
            try:
                images = await page.query_selector_all(selector)
                for img in images:
                    src = await img.get_attribute('src')
                    if src and self._is_product_image(src):
                        all_images.append(src)
            except:
                continue

        # Remove duplicates and keep only unique product images
        data['images'] = list(dict.fromkeys(all_images))
        if data['images']:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Found {len(data['images'])} product images")

        # Extract bottles count
        bottle_patterns = [
            r'(\d+)\s*(?:x\s*)?bottle[s]?',
            r'(\d+)\s*x\s*0[.,]\d+\s*[lL]',
            r'(\d+)\s*Bottle[s]?',
        ]

        for pattern in bottle_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                data['bottles_count'] = int(match.group(1))
                print(f"[{time.strftime('%H:%M:%S')}] ✓ Bottles: {data['bottles_count']}")
                break

        # Extract seller name (clean version)
        data['seller_name'] = await self._extract_seller_name(page)
        if data['seller_name']:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Seller: {data['seller_name']}")

        # Extract price
        data['current_price'] = await self._extract_price(page, page_text)
        if data['current_price']:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Price: {data['current_price']}")

        # Extract shipping cost
        data['shipping_cost'] = await self._extract_shipping_cost(page, page_text)
        if data['shipping_cost']:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ Shipping: {data['shipping_cost']}")

        # Extract end date
        data['end_date'] = await self._extract_end_date(page, page_text)
        if data['end_date']:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ End date: {data['end_date']}")

        return data

    def _is_product_image(self, url: str) -> bool:
        """Check if image is a product photo (not icon/logo/flag)"""
        if not url:
            return False

        # Exclude non-product images
        exclude_patterns = [
            '/flags/',
            '/logos/',
            '/icons/',
            'payment',
            'cards/',
            '.svg',
            'flag-',
            'badge',
            'visa',
            'mastercard',
            'paypal',
            'apple_pay',
        ]

        url_lower = url.lower()
        for pattern in exclude_patterns:
            if pattern in url_lower:
                return False

        # Include only JPG/PNG/WEBP images from assets
        if 'assets.catawiki' in url and any(ext in url_lower for ext in ['.jpg', '.png', '.webp', '@webp']):
            return True

        return False

    async def _extract_seller_name(self, page) -> Optional[str]:
        """Extract clean seller name"""

        # Try different selectors
        seller_selectors = [
            'a[href*="/u/"] h2',
            'a[href*="/u/"] span',
            '[data-testid*="seller"] a',
            '.seller-name',
        ]

        for selector in seller_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.strip()
                    # Clean up seller name
                    if text and len(text) > 2 and len(text) < 100:
                        # Remove common prefixes/suffixes
                        text = text.replace('Sold by', '').strip()
                        text = text.replace('Follow', '').strip()
                        # Take first line only
                        text = text.split('\n')[0].strip()
                        if text:
                            return text
            except:
                continue

        # Fallback: try to find in page text
        try:
            page_text = await page.inner_text('body')
            # Look for "Sold by NAME"
            match = re.search(r'Sold by\s+([^\n]+)', page_text, re.IGNORECASE)
            if match:
                seller = match.group(1).strip()
                # Take only first line
                seller = seller.split('\n')[0].strip()
                if len(seller) < 100:
                    return seller
        except:
            pass

        return None

    async def _extract_price(self, page, page_text: str) -> Optional[str]:
        """Extract current price"""

        # Try selectors first
        price_selectors = [
            '[data-testid*="bid"]',
            '[data-testid*="price"]',
            '.current-bid',
            'span[class*="price"]',
            'div[class*="bid"]',
        ]

        for selector in price_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and ('€' in text or '$' in text or '£' in text):
                        # Clean price
                        price = re.search(r'[€$£]\s*[\d,]+(?:\.\d{2})?', text)
                        if price:
                            return price.group(0).strip()
            except:
                continue

        # Fallback: regex in page text
        price_patterns = [
            r'Current bid[:\s]+([€$£]\s*[\d,]+(?:\.\d{2})?)',
            r'Price[:\s]+([€$£]\s*[\d,]+(?:\.\d{2})?)',
            r'([€$£]\s*[\d,]+(?:\.\d{2})?)',
        ]

        for pattern in price_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    async def _extract_shipping_cost(self, page, page_text: str) -> Optional[str]:
        """Extract shipping cost"""

        # Try selectors
        shipping_selectors = [
            '[data-testid*="shipping"]',
            '.shipping-cost',
            'span[class*="shipping"]',
        ]

        for selector in shipping_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and ('€' in text or '$' in text or '£' in text or 'free' in text.lower()):
                        return text.strip()
            except:
                continue

        # Fallback: regex patterns
        shipping_patterns = [
            r'Shipping[:\s]+([€$£]\s*[\d,]+(?:\.\d{2})?)',
            r'Delivery[:\s]+([€$£]\s*[\d,]+(?:\.\d{2})?)',
            r'Shipping[:\s]+(Free|free)',
            r'Free shipping',
        ]

        for pattern in shipping_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return None

    async def _extract_end_date(self, page, page_text: str) -> Optional[str]:
        """Extract auction end date"""

        # Try selectors
        date_selectors = [
            '[data-testid*="end"]',
            '[data-testid*="time"]',
            '.auction-end',
            'time',
        ]

        for selector in date_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    # Look for date patterns
                    if any(word in text.lower() for word in ['end', 'closing', 'until', 'day', 'hour', 'min']):
                        return text.strip()
                    # Check datetime attribute
                    datetime_attr = await element.get_attribute('datetime')
                    if datetime_attr:
                        return datetime_attr
            except:
                continue

        # Fallback: regex patterns
        date_patterns = [
            r'End[s]?[:\s]+([^\n]+)',
            r'Closing[:\s]+([^\n]+)',
            r'Auction ends[:\s]+([^\n]+)',
            r'Time left[:\s]+([^\n]+)',
            r'(\d+\s+days?\s+\d+\s+hours?)',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                end_time = match.group(1).strip()
                # Take only first line
                end_time = end_time.split('\n')[0].strip()
                if len(end_time) < 100:
                    return end_time

        return None

    def save_to_csv(self, data_list: list, filename: str = 'catawiki_data.csv'):
        """Save scraped data to CSV file"""

        if not data_list:
            print("No data to save")
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
            'url',
            'scraped_at',
        ]

        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

            writer.writeheader()

            for item in data_list:
                # Add images count
                item['images_count'] = len(item.get('images', []))

                # Write row
                row = {k: item.get(k, '') for k in fieldnames}
                writer.writerow(row)

        print(f"\n💾 CSV saved to: {filename}")
        print(f"📊 Total rows: {len(data_list)}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper_pro.py <URL> [--headless] [--csv]")
        print("\nExample:")
        print("  python scraper_pro.py 'https://www.catawiki.com/en/l/...'")
        print("  python scraper_pro.py 'URL' --headless --csv")
        sys.exit(1)

    url = sys.argv[1]
    headless = '--headless' in sys.argv
    save_csv = '--csv' in sys.argv

    print("=" * 70)
    print("🔍 Catawiki Scraper Pro")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Headless: {headless}")
    print(f"CSV Export: {save_csv}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    scraper = CatawikiScraperPro(headless=headless)
    result = await scraper.scrape_listing(url)

    if result:
        print()
        print("=" * 70)
        print("✅ SUCCESS - Scraped Data:")
        print("=" * 70)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

        # Save JSON
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("💾 JSON saved to scraped_data.json")

        # Save CSV if requested
        if save_csv:
            scraper.save_to_csv([result], 'catawiki_data.csv')

        print("=" * 70)
    else:
        print()
        print("=" * 70)
        print("❌ FAILED")
        print("=" * 70)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
