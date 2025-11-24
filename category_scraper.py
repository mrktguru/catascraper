#!/usr/bin/env python3
"""
Catawiki Category Scraper - парсинг всех лотов в категории с пагинацией
"""

import asyncio
import time
from typing import List, Optional
from playwright.async_api import async_playwright
from scraper_pro import CatawikiScraperPro


class CatawikiCategoryScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.scraper = CatawikiScraperPro(headless=headless)

    async def extract_lot_urls_from_page(self, page) -> List[str]:
        """Извлечь все URL лотов со страницы категории"""
        lot_urls = []

        try:
            # Найти все карточки лотов
            lot_cards = await page.query_selector_all('[data-testid^="lot-card-container-"]')
            print(f"[{time.strftime('%H:%M:%S')}] Найдено {len(lot_cards)} карточек лотов")

            for card in lot_cards:
                # Найти ссылку внутри карточки
                link = await card.query_selector('a[href*="/en/l/"]')
                if link:
                    href = await link.get_attribute('href')
                    if href:
                        # Полный URL
                        if href.startswith('http'):
                            lot_url = href.split('?')[0]  # Убрать query параметры
                        else:
                            lot_url = f"https://www.catawiki.com{href.split('?')[0]}"

                        lot_urls.append(lot_url)

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка извлечения URL: {e}")

        return lot_urls

    async def get_total_pages(self, page) -> int:
        """Определить общее количество страниц в категории"""
        try:
            # Найти навигацию пагинации
            pagination = await page.query_selector('nav.c-pagination__container')
            if not pagination:
                return 1

            # Найти все номера страниц
            page_numbers = await pagination.query_selector_all('[data-testid="page"]')

            max_page = 1
            for page_elem in page_numbers:
                text = await page_elem.inner_text()
                text = text.strip()

                # Пропустить "..."
                if text == '…' or text == '...':
                    continue

                try:
                    page_num = int(text)
                    if page_num > max_page:
                        max_page = page_num
                except ValueError:
                    continue

            print(f"[{time.strftime('%H:%M:%S')}] 📄 Всего страниц: {max_page}")
            return max_page

        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Не удалось определить количество страниц: {e}")
            return 1

    async def scrape_category(self, category_url: str, max_pages: Optional[int] = None) -> List[dict]:
        """
        Парсинг всей категории с пагинацией

        Args:
            category_url: URL категории
            max_pages: Максимальное количество страниц для парсинга (None = все страницы)

        Returns:
            Список данных всех лотов
        """
        print("=" * 70)
        print("🗂️ Catawiki Category Scraper")
        print("=" * 70)
        print(f"Category URL: {category_url}")
        print(f"Max pages: {max_pages or 'ALL'}")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        all_lot_urls = []

        async with async_playwright() as p:
            try:
                # Запустить браузер
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                    ]
                )

                page = await browser.new_page()

                # Загрузить первую страницу категории
                print(f"[{time.strftime('%H:%M:%S')}] 🌐 Загрузка категории...")
                await page.goto(category_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(3)  # Дать время на загрузку контента

                # Определить общее количество страниц
                total_pages = await self.get_total_pages(page)

                if max_pages:
                    total_pages = min(total_pages, max_pages)

                # Парсинг каждой страницы категории
                for page_num in range(1, total_pages + 1):
                    print(f"\n[{time.strftime('%H:%M:%S')}] 📑 Страница {page_num}/{total_pages}")

                    # Если не первая страница, перейти на нужную
                    if page_num > 1:
                        # Построить URL с параметром page
                        separator = '&' if '?' in category_url else '?'
                        page_url = f"{category_url}{separator}page={page_num}"

                        print(f"[{time.strftime('%H:%M:%S')}] 🌐 Переход на страницу {page_num}...")
                        await page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
                        await asyncio.sleep(3)

                    # Извлечь URL лотов со страницы
                    lot_urls = await self.extract_lot_urls_from_page(page)
                    all_lot_urls.extend(lot_urls)

                    print(f"[{time.strftime('%H:%M:%S')}] ✓ Извлечено {len(lot_urls)} URL лотов")

                await browser.close()

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка парсинга категории: {e}")
                return []

        # Удалить дубликаты
        all_lot_urls = list(set(all_lot_urls))
        print(f"\n[{time.strftime('%H:%M:%S')}] 📊 Всего уникальных лотов: {len(all_lot_urls)}")

        # Теперь парсим каждый лот
        print(f"\n[{time.strftime('%H:%M:%S')}] 🚀 Начинаем парсинг каждого лота...")
        all_results = []

        for i, lot_url in enumerate(all_lot_urls, 1):
            print(f"\n[{time.strftime('%H:%M:%S')}] 📦 Лот {i}/{len(all_lot_urls)}: {lot_url}")

            try:
                # Использовать существующий scraper для лота
                result = await self.scraper.scrape_listing(lot_url)

                if result and result.get('title'):
                    all_results.append(result)
                    print(f"[{time.strftime('%H:%M:%S')}] ✅ Успешно спарсено")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] ⚠️ Не удалось спарсить лот")

            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ❌ Ошибка парсинга лота: {e}")
                continue

            # Задержка между запросами
            if i < len(all_lot_urls):
                await asyncio.sleep(3)

        print("\n" + "=" * 70)
        print(f"✅ Парсинг категории завершен!")
        print(f"Всего лотов найдено: {len(all_lot_urls)}")
        print(f"Успешно спарсено: {len(all_results)}")
        print(f"Провалено: {len(all_lot_urls) - len(all_results)}")
        print("=" * 70)

        return all_results


async def main():
    """Пример использования"""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python category_scraper.py <category_url> [max_pages]")
        print("\nExample:")
        print('  python category_scraper.py "https://www.catawiki.com/en/s?q=burgundy&filters=..." 2')
        sys.exit(1)

    category_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None

    scraper = CatawikiCategoryScraper(headless=True)
    results = await scraper.scrape_category(category_url, max_pages=max_pages)

    # Сохранить результаты
    if results:
        output_file = f"category_results_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Результаты сохранены в: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
