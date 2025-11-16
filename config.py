"""
Configuration for Catawiki scraper
"""

# Browser settings
HEADLESS = True  # Set to False to see browser in action
TIMEOUT = 60000  # Page load timeout in milliseconds

# Anti-detection settings
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

# Delays (in seconds)
MIN_DELAY = 1.0
MAX_DELAY = 3.0
SCROLL_DELAY = (0.1, 0.3)
RETRY_DELAY = (2.0, 4.0)

# Retry settings
MAX_RETRIES = 3

# Proxy settings (set to None if not using proxy)
PROXY = None  # Example: 'http://user:pass@proxy:port'

# Output settings
OUTPUT_DIR = 'output'
SAVE_SCREENSHOTS = True
SAVE_HTML = True

# Geolocation (Amsterdam, Netherlands - where Catawiki is based)
GEOLOCATION = {
    'latitude': 52.3676,
    'longitude': 4.9041
}

# Locale settings
LOCALE = 'en-US'
TIMEZONE = 'Europe/Amsterdam'

# Browser arguments
BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-web-security',
    '--disable-features=IsolateOrigins,site-per-process',
]
