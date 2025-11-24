# Catawiki Scraper 🍷

Профессиональный scraper для сайта Catawiki с обходом Akamai защиты. Использует Playwright для эмуляции реального браузера и множественные стратегии извлечения данных.

## ✨ Возможности

- ✅ Обход Akamai защиты через эмуляцию браузера
- ✅ Множественные стратегии парсинга (селекторы, regex, structured data)
- ✅ Антидетект-механизмы (user agents, fingerprinting, поведение человека)
- ✅ Batch scraping для множественных URL
- ✅ **Category scraping** - парсинг всех лотов в категории с пагинацией
- ✅ **n8n integration** - автоматизация через Google Sheets
- ✅ **REST API** - FastAPI сервер для интеграции
- ✅ **AI wine rating** - автоматическая оценка вин через OpenAI/Claude
- ✅ Автоматическое сохранение скриншотов и HTML для отладки
- ✅ Поддержка прокси
- ✅ Retry логика при ошибках

## 📦 Установка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Установка браузера Chromium для Playwright
playwright install chromium
```

## 🚀 Использование

### Базовый scraper

```bash
python scraper.py "URL"
```

### Продвинутый scraper (рекомендуется)

```bash
# С видимым браузером (для отладки)
python advanced_scraper.py "https://www.catawiki.com/en/l/98998534-..."

# В headless режиме
python advanced_scraper.py "URL" --headless

# С прокси
python advanced_scraper.py "URL" --headless --proxy "http://proxy:port"
```

### Batch scraping

```bash
# Из файла
python batch_scraper.py example_urls.txt --headless

# Напрямую из командной строки
python batch_scraper.py "URL1" "URL2" "URL3" --headless
```

### Category scraping (NEW! 🎉)

Парсинг всех лотов в категории с автоматической пагинацией:

```bash
# Парсить все страницы категории
python category_scraper.py "https://www.catawiki.com/en/s?q=burgundy&filters=..."

# Парсить только первые 2 страницы
python category_scraper.py "https://www.catawiki.com/en/s?q=burgundy&filters=..." 2
```

### REST API Server

Запуск API сервера для интеграции с n8n:

```bash
# Запустить API сервер
python api_server.py

# API будет доступен на http://0.0.0.0:8000
```

**Endpoints:**
- `POST /scrape` - Парсинг одного URL (синхронно)
- `POST /scrape-async` - Парсинг одного URL (асинхронно)
- `POST /scrape-batch` - Batch парсинг (асинхронно)
- `POST /scrape-category` - Парсинг категории (асинхронно)
- `GET /job/{job_id}` - Статус задачи
- `GET /health` - Health check

### n8n Integration

**Batch Scraping Workflow:**
1. Импортируйте `n8n_workflow_complete.json` в n8n
2. Настройте Google Sheets credentials
3. Добавьте URLs в лист "URLs"
4. Результаты появятся в листе "Results"

**Category Scraping Workflow:**
1. Импортируйте `n8n_workflow_category.json` в n8n
2. Настройте Google Sheets credentials
3. Вставьте category URL в лист "URL-CAT"
4. Результаты появятся в листе "CATALOG"

📖 **Подробная инструкция:** См. `CATEGORY_SCRAPER_GUIDE.md`

### AI Wine Rating

Добавьте AI оценку вин в n8n workflow:

- **Producer Rating** (1-10)
- **Vintage Rating** (1-10)
- **Region Rating** (1-10)
- **Overall Appeal** (1-10)
- **Investment Potential** (1-10)

📖 **Подробная инструкция:** См. `AI_INTEGRATION_GUIDE.md`

## 📊 Парсируемые данные

**Основные поля:**
- **title** - полное название лота
- **images** - все изображения товара
- **first_image** - превью 100x100px (Google Sheets IMAGE formula)
- **bottles_count** - количество бутылок в лоте
- **seller_name** - имя продавца
- **current_price** - текущая ставка/цена
- **shipping_cost** - стоимость доставки
- **end_date** - дата окончания аукциона (live countdown formula)
- **images_count** - количество изображений
- **url** - ссылка на лот (HYPERLINK formula)
- **scraped_at** - время парсинга

**AI Rating поля (опционально):**
- **producer_rating** - оценка производителя (1-10)
- **vintage_rating** - оценка винтажа (1-10)
- **region_rating** - оценка региона (1-10)
- **overall_appeal** - общая привлекательность (1-10)
- **investment_potential** - инвестиционная привлекательность (1-10)

## 📁 Структура проекта

```
catascraper/
├── scraper.py                      # Базовый scraper
├── scraper_pro.py                  # Продвинутый scraper (рекомендуется)
├── batch_scraper_pro.py            # Batch scraping
├── category_scraper.py             # Category scraping (NEW!)
├── api_server.py                   # REST API server (NEW!)
├── n8n_workflow_complete.json      # n8n workflow для batch scraping
├── n8n_workflow_category.json      # n8n workflow для category scraping (NEW!)
├── AI_INTEGRATION_GUIDE.md         # Гайд по интеграции AI (NEW!)
├── CATEGORY_SCRAPER_GUIDE.md       # Гайд по category scraping (NEW!)
├── config.py                       # Конфигурация
├── requirements.txt                # Python зависимости
├── example_urls.txt                # Пример файла с URL
└── README.md                       # Документация
```

## 🔧 Конфигурация

Настройки можно изменить в файле `config.py`:

- `HEADLESS` - запуск браузера в фоновом режиме
- `TIMEOUT` - таймаут загрузки страницы
- `MAX_RETRIES` - количество попыток при ошибках
- `PROXY` - прокси сервер
- `GEOLOCATION` - геолокация (по умолчанию Амстердам)

## 🛡️ Обход защиты Akamai

Scraper использует следующие техники:

1. **Эмуляция браузера** - Playwright с Chromium
2. **Антидетект**:
   - Скрытие webdriver флагов
   - Реалистичные user agents
   - Моки plugins, languages, permissions
   - Chrome runtime object
3. **Человекоподобное поведение**:
   - Случайные задержки
   - Имитация скроллинга
   - Естественные таймауты
4. **Множественные стратегии парсинга**:
   - CSS селекторы
   - Data-атрибуты
   - Regex паттерны
   - Structured data (JSON-LD)

## 📝 Примеры

### Пример вывода

```json
{
  "title": "2022 Beaune 1 Cru Belissand, Domaine Françoise André - Burgundy - 6 bottles (0.75L)",
  "images": [
    "https://assets.catawiki.nl/assets/2024/...",
    "https://assets.catawiki.nl/assets/2024/..."
  ],
  "bottles_count": "6",
  "seller": "WineCollector123",
  "current_price": "€ 125",
  "url": "https://www.catawiki.com/en/l/98998534-..."
}
```

### Создание списка URL для batch scraping

Создайте файл `my_urls.txt`:

```
# Мои Catawiki лоты
https://www.catawiki.com/en/l/98998534-...
https://www.catawiki.com/en/l/98998535-...
https://www.catawiki.com/en/l/98998536-...
```

Запустите:

```bash
python batch_scraper.py my_urls.txt --headless
```

## 🐛 Отладка

При проблемах scraper автоматически сохраняет:

- `debug_screenshot.png` - скриншот страницы
- `error_screenshot.png` - скриншот при ошибке
- `debug_page.html` - HTML код страницы

Для детальной отладки запускайте без `--headless`:

```bash
python advanced_scraper.py "URL"
```

## ⚠️ Важные замечания

1. **Rate limiting**: Используйте задержки между запросами
2. **Прокси**: Для массового парсинга рекомендуется использовать прокси
3. **Легальность**: Проверьте Terms of Service сайта
4. **Robots.txt**: Убедитесь, что парсинг разрешен

## 🔄 Возможные улучшения

- [x] API wrapper (FastAPI server)
- [x] n8n integration
- [x] Category scraping with pagination
- [x] AI wine rating integration
- [ ] Rotating proxies
- [ ] Captcha solving
- [ ] Database integration
- [ ] Docker containerization
- [ ] Monitoring и алерты
- [ ] Multi-category batch scraping

## 📄 Лицензия

MIT

## 🤝 Вклад

Pull requests приветствуются!
