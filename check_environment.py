#!/usr/bin/env python3
"""
Check if the environment is properly configured for Catawiki scraper
"""

import sys
import subprocess
import os


def check_python():
    """Check Python version"""
    print("=" * 60)
    print("1. Checking Python...")
    print("=" * 60)
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠️  WARNING: Python 3.8+ recommended")
    else:
        print("✓ Version OK")
    print()


def check_packages():
    """Check required packages"""
    print("=" * 60)
    print("2. Checking Python packages...")
    print("=" * 60)

    packages = {
        'playwright': 'Playwright',
        'beautifulsoup4': 'BeautifulSoup4',
        'lxml': 'lxml',
    }

    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            all_ok = False

    if not all_ok:
        print("\n⚠️  Install missing packages:")
        print("   pip3 install -r requirements.txt")
    print()


def check_playwright():
    """Check Playwright browser"""
    print("=" * 60)
    print("3. Checking Playwright browser...")
    print("=" * 60)

    try:
        from playwright.sync_api import sync_playwright
        print("✓ Playwright module loaded")

        # Try to launch browser
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, timeout=10000)
                print("✓ Chromium browser can launch")
                browser.close()
                print("✓ Browser test successful")
        except Exception as e:
            print(f"✗ Browser launch failed: {e}")
            print("\n⚠️  Install browser:")
            print("   python3 -m playwright install chromium")
            print("   python3 -m playwright install-deps chromium")

    except ImportError:
        print("✗ Playwright not installed")
    print()


def check_system_libs():
    """Check system libraries"""
    print("=" * 60)
    print("4. Checking system libraries...")
    print("=" * 60)

    required_libs = [
        'libnss3.so',
        'libatk-1.0.so.0',
        'libcups.so.2',
    ]

    # Try to find libraries
    for lib in required_libs:
        try:
            result = subprocess.run(
                ['ldconfig', '-p'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if lib in result.stdout:
                print(f"✓ {lib} found")
            else:
                print(f"⚠️  {lib} might be missing")
        except:
            print(f"⚠️  Could not check {lib}")

    print("\n💡 If libraries are missing, run:")
    print("   python3 -m playwright install-deps chromium")
    print("   # OR manually:")
    print("   apt-get install -y libnss3 libatk1.0-0 libcups2 libdrm2")
    print()


def check_memory():
    """Check available memory"""
    print("=" * 60)
    print("5. Checking system resources...")
    print("=" * 60)

    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'MemTotal' in line or 'MemAvailable' in line or 'MemFree' in line:
                    parts = line.split()
                    mem_kb = int(parts[1])
                    mem_mb = mem_kb / 1024
                    print(f"  {parts[0]:<20} {mem_mb:>8.0f} MB")

        print("\n💡 Chromium needs ~500MB RAM minimum")
        print("   If memory is low, use --single-process flag or add swap")

    except Exception as e:
        print(f"⚠️  Could not check memory: {e}")
    print()


def check_network():
    """Check network connectivity"""
    print("=" * 60)
    print("6. Checking network...")
    print("=" * 60)

    import socket
    try:
        # Try to resolve Catawiki
        ip = socket.gethostbyname('www.catawiki.com')
        print(f"✓ Can resolve www.catawiki.com ({ip})")

        # Try to connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('www.catawiki.com', 443))
        sock.close()

        if result == 0:
            print("✓ Can connect to www.catawiki.com:443")
        else:
            print("⚠️  Cannot connect to www.catawiki.com:443")

    except Exception as e:
        print(f"⚠️  Network check failed: {e}")
    print()


def check_files():
    """Check if required files exist"""
    print("=" * 60)
    print("7. Checking project files...")
    print("=" * 60)

    files = [
        'requirements.txt',
        'advanced_scraper.py',
        'fast_scraper.py',
        'batch_scraper.py',
    ]

    for file in files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} missing")
    print()


def main():
    print("\n" + "=" * 60)
    print("🔧 Catawiki Scraper - Environment Check")
    print("=" * 60)
    print()

    check_python()
    check_packages()
    check_playwright()
    check_system_libs()
    check_memory()
    check_network()
    check_files()

    print("=" * 60)
    print("✅ Environment check complete!")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("1. Fix any issues shown above")
    print("2. Test with: python3 fast_scraper.py 'URL' --headless")
    print()


if __name__ == '__main__':
    main()
