# 🚀 Инструкция по установке на продакшн сервере

## Текущие исправленные ошибки
- ✅ **404 Error** - API endpoint `/scrape-category` теперь доступен
- ✅ **422 Error** - API теперь правильно обрабатывает строковые параметры от n8n

## Установка на сервере (root@a141930414:~/cataparser)

### Шаг 1: Подключитесь к серверу
```bash
ssh root@ваш_сервер
cd /root/cataparser
```

### Шаг 2: Получите последние изменения
```bash
git fetch origin
git pull origin claude/fix-404-category-error-01EnBeZezDLB5Bn3HepuyJ7A
```

### Шаг 3: Установите зависимости API (если еще не установлены)
```bash
pip3 install -r requirements_api.txt
```

### Шаг 4: **ВАЖНО!** Установите браузеры Playwright
```bash
python3 -m playwright install chromium
```

Эта команда загрузит браузер Chromium (~200MB). Без этого шага скрапинг не будет работать!

### Шаг 5: Перезапустите API сервер
```bash
# Остановите старый процесс
kill -9 $(lsof -t -i:8000)

# Запустите обновленный сервер
nohup python3 api_server.py > /tmp/catawiki-api.log 2>&1 &
```

### Шаг 6: Проверьте, что всё работает
```bash
# Подождите 3 секунды
sleep 3

# Проверьте здоровье API
curl http://localhost:8000/health

# Тест скрапинга (должен вернуть success: true и job_id)
curl -X POST http://localhost:8000/scrape-category \
  -H "Content-Type: application/json" \
  -d '{
    "category_url": "https://www.catawiki.com/en/s?q=burgundy",
    "max_pages": "1",
    "headless": "true",
    "save_csv": "true"
  }'
```

**Ожидаемый результат:**
```json
{
  "success": true,
  "job_id": "какой-то-uuid",
  "data": {
    "message": "Category scraping job started",
    ...
  }
}
```

### Шаг 7: Проверьте статус задачи (замените job_id на полученный)
```bash
curl http://localhost:8000/job/ВАШ_JOB_ID
```

Статус должен быть `completed` (не `failed`).

---

## Альтернативный метод (использование скрипта)

После выполнения шагов 1-4, можете использовать готовый скрипт:

```bash
cd /root/cataparser
chmod +x restart_api.sh
./restart_api.sh
```

---

## Проверка логов

Если что-то не работает:

```bash
# Посмотреть последние 50 строк логов
tail -n 50 /tmp/catawiki-api.log

# Следить за логами в реальном времени
tail -f /tmp/catawiki-api.log
```

Нажмите `Ctrl+C` для выхода.

---

## Решение проблем

### Ошибка "Executable doesn't exist" (браузер не найден)
```bash
python3 -m playwright install chromium
```

### Ошибка "Port 8000 already in use"
```bash
kill -9 $(lsof -t -i:8000)
```

### API не отвечает
```bash
# Проверьте, запущен ли процесс
lsof -i :8000

# Если не запущен, запустите
nohup python3 api_server.py > /tmp/catawiki-api.log 2>&1 &
```

### Ошибки в n8n (404, 422)
Убедитесь, что вы выполнили все шаги выше и API сервер запущен на правильной ветке.

---

## Автоматический запуск при перезагрузке сервера

Если хотите, чтобы API запускался автоматически:

```bash
# Отредактируйте systemd service
nano /etc/systemd/system/catawiki-api.service
```

Добавьте:
```ini
[Unit]
Description=Catawiki Scraper API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cataparser
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 /root/cataparser/api_server.py
Restart=always
RestartSec=10

StandardOutput=append:/var/log/catawiki-api.log
StandardError=append:/var/log/catawiki-api-error.log

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
systemctl daemon-reload
systemctl enable catawiki-api
systemctl start catawiki-api
systemctl status catawiki-api
```

---

## Что было исправлено

1. **API endpoint доступен** - `/scrape-category` теперь работает
2. **Валидация параметров** - API принимает строковые значения от n8n:
   - `"null"` → `None`
   - `"true"` → `True`
   - `"1"` → `1`
3. **Скрипт перезапуска** - `restart_api.sh` для удобства

---

## Контакты

Если возникнут проблемы, проверьте логи и статус процесса.
