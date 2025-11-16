#!/usr/bin/env python3
"""
Catawiki scraper with Akamai bypass using Playwright
"""

import sys
import json
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from typing import Optional, Dict


class CatawikiScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_listing(self, url: str) -> Optional[Dict]:
        """
        Scrape a Catawiki listing page

        Args:
            url: URL of the listing page

        Returns:
            Dictionary with scraped data or None if failed
        """
        async with async_playwright() as p:
            # Launch browser with anti-detection measures
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )

            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
            )

            # Additional stealth settings
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)

            page = await context.new_page()

            try:
                print(f"Loading page: {url}")

                # Navigate to the page
                await page.goto(url, wait_until='networkidle', timeout=60000)

                # Wait for content to load
                await page.wait_for_selector('h1', timeout=30000)

                # Small delay to ensure all dynamic content loads
                await asyncio.sleep(2)

                # Extract data
                data = await self._extract_data(page)

                return data

            except PlaywrightTimeout as e:
                print(f"Timeout error: {e}")
                return None
            except Exception as e:
                print(f"Error scraping page: {e}")
                return None
            finally:
                await browser.close()

    async def _extract_data(self, page) -> Dict:
        """Extract listing data from the page"""

        data = {
            'title': None,
            'images': [],
            'bottles_count': None,
            'seller': None,
            'current_price': None,
        }

        # Extract title
        try:
            title = await page.query_selector('h1')
            if title:
                data['title'] = await title.inner_text()
                data['title'] = data['title'].strip()
        except Exception as e:
            print(f"Error extracting title: {e}")

        # Extract images
        try:
            # Try multiple selectors for images
            image_selectors = [
                'img[data-testid="lot-image"]',
                '.lot-image img',
                'img[alt*="lot"]',
                '.image-gallery img',
                'main img',
            ]

            for selector in image_selectors:
                images = await page.query_selector_all(selector)
                if images:
                    for img in images:
                        src = await img.get_attribute('src')
                        if src and not src.startswith('data:'):
                            data['images'].append(src)
                    if data['images']:
                        break

            # Remove duplicates
            data['images'] = list(dict.fromkeys(data['images']))

        except Exception as e:
            print(f"Error extracting images: {e}")

        # Extract bottle count from title or description
        try:
            text_content = await page.inner_text('body')

            # Look for patterns like "6 bottles", "1 bottle", etc.
            import re
            bottle_patterns = [
                r'(\d+)\s*bottle[s]?',
                r'(\d+)\s*x\s*0[.,]\d+l',
            ]

            for pattern in bottle_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data['bottles_count'] = match.group(1)
                    break

        except Exception as e:
            print(f"Error extracting bottle count: {e}")

        # Extract seller
        try:
            seller_selectors = [
                '[data-testid="seller-name"]',
                '.seller-name',
                'a[href*="/u/"]',
            ]

            for selector in seller_selectors:
                seller = await page.query_selector(selector)
                if seller:
                    data['seller'] = await seller.inner_text()
                    data['seller'] = data['seller'].strip()
                    break

        except Exception as e:
            print(f"Error extracting seller: {e}")

        # Extract current price
        try:
            price_selectors = [
                '[data-testid="current-bid"]',
                '.current-bid',
                '.price',
                'span[class*="bid"]',
                'div[class*="price"]',
            ]

            for selector in price_selectors:
                price = await page.query_selector(selector)
                if price:
                    price_text = await price.inner_text()
                    # Clean up price text
                    data['current_price'] = price_text.strip()
                    break

        except Exception as e:
            print(f"Error extracting price: {e}")

        # If we couldn't find specific elements, try to get all page content for debugging
        if not any([data['title'], data['seller'], data['current_price']]):
            print("\nCouldn't find data with selectors. Dumping page structure...")

            # Get all text content
            all_text = await page.inner_text('body')
            print(f"\nPage text preview (first 1000 chars):\n{all_text[:1000]}")

            # Try to get HTML for inspection
            html_content = await page.content()

            # Save HTML for debugging
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("\nSaved full page HTML to debug_page.html")

        return data


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <URL>")
        print("Example: python scraper.py 'https://www.catawiki.com/en/l/98998534-...'")
        sys.exit(1)

    url = sys.argv[1]

    scraper = CatawikiScraper(headless=False)  # Set to True for production
    result = await scraper.scrape_listing(url)

    if result:
        print("\n" + "="*60)
        print("SCRAPED DATA:")
        print("="*60)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Also save to file
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nData saved to scraped_data.json")
    else:
        print("Failed to scrape data")
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
