#!/usr/bin/env python3
"""
Advanced Catawiki scraper with enhanced Akamai bypass techniques
"""

import sys
import json
import asyncio
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Optional, Dict, List
import re


class AdvancedCatawikiScraper:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None):
        self.headless = headless
        self.proxy = proxy

    async def scrape_listing(self, url: str) -> Optional[Dict]:
        """
        Scrape a Catawiki listing page with advanced anti-detection

        Args:
            url: URL of the listing page

        Returns:
            Dictionary with scraped data or None if failed
        """
        async with async_playwright() as p:
            # Browser launch arguments for stealth
            launch_args = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            }

            if self.proxy:
                launch_args['proxy'] = {'server': self.proxy}

            browser = await p.chromium.launch(**launch_args)

            # Create context with realistic fingerprint
            context_options = {
                'viewport': {'width': 1920, 'height': 1080},
                'user_agent': self._get_random_user_agent(),
                'locale': 'en-US',
                'timezone_id': 'Europe/Amsterdam',  # Catawiki is based in Netherlands
                'permissions': ['geolocation'],
                'geolocation': {'latitude': 52.3676, 'longitude': 4.9041},  # Amsterdam
                'color_scheme': 'light',
                'extra_http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            }

            context = await browser.new_context(**context_options)

            # Enhanced stealth scripts
            await context.add_init_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            name: 'Chrome PDF Plugin',
                            filename: 'internal-pdf-viewer',
                            description: 'Portable Document Format'
                        },
                        {
                            name: 'Chrome PDF Viewer',
                            filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                            description: ''
                        },
                        {
                            name: 'Native Client',
                            filename: 'internal-nacl-plugin',
                            description: ''
                        }
                    ]
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Mock chrome object
                window.chrome = {
                    runtime: {}
                };
            """)

            page = await context.new_page()

            try:
                print(f"🌐 Loading page: {url}")

                # Add random delay before navigation
                await asyncio.sleep(random.uniform(1, 3))

                # Navigate with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                        if response and response.status == 403:
                            print(f"⚠️  Got 403, attempt {attempt + 1}/{max_retries}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(random.uniform(3, 6))
                                continue
                            else:
                                print("❌ Failed to bypass protection after all retries")
                                return None
                        break
                    except PlaywrightTimeout:
                        if attempt < max_retries - 1:
                            print(f"⚠️  Timeout, retrying... ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(random.uniform(2, 4))
                        else:
                            raise

                # Wait for main content
                print("⏳ Waiting for content...")
                await page.wait_for_load_state('networkidle', timeout=30000)

                # Random human-like delay
                await asyncio.sleep(random.uniform(2, 4))

                # Scroll to simulate human behavior
                await self._human_like_scroll(page)

                # Extract data
                print("📊 Extracting data...")
                data = await self._extract_data(page)

                # Screenshot for debugging
                await page.screenshot(path='debug_screenshot.png')
                print("📸 Screenshot saved to debug_screenshot.png")

                return data

            except PlaywrightTimeout as e:
                print(f"❌ Timeout error: {e}")
                await page.screenshot(path='error_screenshot.png')
                return None
            except Exception as e:
                print(f"❌ Error scraping page: {e}")
                await page.screenshot(path='error_screenshot.png')
                return None
            finally:
                await browser.close()

    async def _human_like_scroll(self, page):
        """Simulate human-like scrolling behavior"""
        try:
            # Get page height
            height = await page.evaluate('document.body.scrollHeight')

            # Scroll in steps
            current = 0
            step = random.randint(300, 500)

            while current < height:
                current += step
                await page.evaluate(f'window.scrollTo(0, {current})')
                await asyncio.sleep(random.uniform(0.1, 0.3))

                if current > height // 2:
                    break

            # Scroll back to top
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(random.uniform(0.5, 1))

        except Exception as e:
            print(f"⚠️  Scroll simulation failed: {e}")

    async def _extract_data(self, page) -> Dict:
        """Extract listing data from the page using multiple strategies"""

        data = {
            'title': None,
            'images': [],
            'bottles_count': None,
            'seller': None,
            'current_price': None,
            'url': page.url,
        }

        # Get page content for text analysis
        page_content = await page.content()
        page_text = await page.inner_text('body')

        # Strategy 1: Try structured selectors
        await self._extract_with_selectors(page, data)

        # Strategy 2: Try data attributes
        await self._extract_with_data_attributes(page, data)

        # Strategy 3: Regex patterns from text
        self._extract_with_regex(page_text, data)

        # Strategy 4: Try to find in JSON-LD or structured data
        await self._extract_structured_data(page, data)

        # Save debug info if extraction failed
        if not data['title']:
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("⚠️  Could not extract title. Saved HTML to debug_page.html")

        return data

    async def _extract_with_selectors(self, page, data: Dict):
        """Extract data using CSS selectors"""

        # Title selectors
        title_selectors = [
            'h1',
            '[data-testid="lot-title"]',
            '.lot-title',
            'h1.title',
            'main h1',
        ]

        for selector in title_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 5:
                        data['title'] = text.strip()
                        print(f"✓ Title found: {data['title'][:50]}...")
                        break
            except:
                continue

        # Image selectors
        image_selectors = [
            'img[data-testid*="lot-image"]',
            'img[data-testid*="image"]',
            '.lot-images img',
            '.image-gallery img',
            'main img[src*="catawiki"]',
            'picture img',
        ]

        for selector in image_selectors:
            try:
                images = await page.query_selector_all(selector)
                for img in images:
                    src = await img.get_attribute('src')
                    srcset = await img.get_attribute('srcset')

                    if src and 'catawiki' in src and not src.startswith('data:'):
                        data['images'].append(src)

                    if srcset:
                        # Parse srcset
                        urls = re.findall(r'(https?://[^\s,]+)', srcset)
                        data['images'].extend(urls)

                if data['images']:
                    break
            except:
                continue

        # Remove duplicates and limit to reasonable number
        if data['images']:
            data['images'] = list(dict.fromkeys(data['images']))[:10]
            print(f"✓ Found {len(data['images'])} images")

        # Seller selectors
        seller_selectors = [
            '[data-testid*="seller"]',
            'a[href*="/u/"]',
            '.seller-name',
            '.seller a',
            'div[class*="seller"] a',
        ]

        for selector in seller_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and len(text) > 2:
                        data['seller'] = text.strip()
                        print(f"✓ Seller found: {data['seller']}")
                        break
            except:
                continue

        # Price selectors
        price_selectors = [
            '[data-testid*="bid"]',
            '[data-testid*="price"]',
            '.current-bid',
            '.price',
            'span[class*="bid"]',
            'div[class*="price"] span',
        ]

        for selector in price_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    if text and ('€' in text or '$' in text or '£' in text):
                        data['current_price'] = text.strip()
                        print(f"✓ Price found: {data['current_price']}")
                        break
            except:
                continue

    async def _extract_with_data_attributes(self, page, data: Dict):
        """Try to extract from data-* attributes"""
        try:
            # Execute script to find elements with data attributes
            result = await page.evaluate("""
                () => {
                    const data = {};

                    // Find all elements with data-testid
                    document.querySelectorAll('[data-testid]').forEach(el => {
                        const testId = el.getAttribute('data-testid');
                        if (testId.includes('lot') || testId.includes('title') ||
                            testId.includes('price') || testId.includes('bid') ||
                            testId.includes('seller')) {
                            data[testId] = el.innerText || el.textContent;
                        }
                    });

                    return data;
                }
            """)

            if result:
                print(f"📋 Found data attributes: {list(result.keys())}")

        except Exception as e:
            print(f"⚠️  Data attribute extraction failed: {e}")

    def _extract_with_regex(self, text: str, data: Dict):
        """Extract data using regex patterns from page text"""

        # Bottle count patterns
        if not data['bottles_count']:
            bottle_patterns = [
                r'(\d+)\s*(?:x\s*)?bottle[s]?',
                r'(\d+)\s*x\s*0[.,]\d+\s*[lL]',
                r'Quantity[:\s]+(\d+)',
            ]

            for pattern in bottle_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data['bottles_count'] = match.group(1)
                    print(f"✓ Bottles count found: {data['bottles_count']}")
                    break

        # Price patterns (if not found yet)
        if not data['current_price']:
            price_patterns = [
                r'€\s*[\d,]+(?:\.\d{2})?',
                r'\$\s*[\d,]+(?:\.\d{2})?',
                r'£\s*[\d,]+(?:\.\d{2})?',
                r'Current\s+bid[:\s]+(€|£|\$)\s*[\d,]+',
            ]

            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data['current_price'] = match.group(0).strip()
                    print(f"✓ Price found via regex: {data['current_price']}")
                    break

    async def _extract_structured_data(self, page, data: Dict):
        """Try to extract from JSON-LD or other structured data"""
        try:
            structured_data = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    const data = [];
                    scripts.forEach(script => {
                        try {
                            data.push(JSON.parse(script.textContent));
                        } catch(e) {}
                    });
                    return data;
                }
            """)

            if structured_data:
                print(f"📋 Found {len(structured_data)} structured data blocks")

                for item in structured_data:
                    if isinstance(item, dict):
                        if not data['title'] and 'name' in item:
                            data['title'] = item['name']
                        if not data['images'] and 'image' in item:
                            if isinstance(item['image'], list):
                                data['images'].extend(item['image'])
                            else:
                                data['images'].append(item['image'])

        except Exception as e:
            print(f"⚠️  Structured data extraction failed: {e}")

    def _get_random_user_agent(self) -> str:
        """Return a random realistic user agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        return random.choice(user_agents)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python advanced_scraper.py <URL> [--headless] [--proxy PROXY_URL]")
        print("\nExample:")
        print("  python advanced_scraper.py 'https://www.catawiki.com/en/l/98998534-...'")
        print("  python advanced_scraper.py 'URL' --headless")
        print("  python advanced_scraper.py 'URL' --proxy 'http://proxy:port'")
        sys.exit(1)

    url = sys.argv[1]
    headless = '--headless' in sys.argv
    proxy = None

    if '--proxy' in sys.argv:
        proxy_index = sys.argv.index('--proxy')
        if proxy_index + 1 < len(sys.argv):
            proxy = sys.argv[proxy_index + 1]

    print("="*60)
    print("🔍 Catawiki Advanced Scraper")
    print("="*60)
    print(f"URL: {url}")
    print(f"Headless: {headless}")
    print(f"Proxy: {proxy or 'None'}")
    print("="*60)

    scraper = AdvancedCatawikiScraper(headless=headless, proxy=proxy)
    result = await scraper.scrape_listing(url)

    if result:
        print("\n" + "="*60)
        print("✅ SCRAPED DATA:")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Save to file
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n💾 Data saved to scraped_data.json")
    else:
        print("\n❌ Failed to scrape data")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
