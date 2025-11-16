# 🔄 n8n Integration Guide - Catawiki Scraper

Полное руководство по интеграции Catawiki Scraper с n8n.

---

## 📋 **Оглавление**

1. [Установка API сервера](#установка-api-сервера)
2. [Настройка n8n](#настройка-n8n)
3. [Примеры Workflow](#примеры-workflow)
4. [API Endpoints](#api-endpoints)
5. [Автоматизация](#автоматизация)

---

## 🚀 **1. Установка API сервера**

### Шаг 1: Обновите код на сервере

```bash
ssh root@38.244.194.181
cd /root/cataparser
git pull origin main
```

### Шаг 2: Установите зависимости

```bash
pip3 install -r requirements_api.txt
```

### Шаг 3: Запустите API сервер

**Вариант A: Запуск вручную (для теста)**

```bash
python3 api_server.py
```

Сервер запустится на `http://localhost:8000`

**Вариант B: Автозапуск через systemd (рекомендуется)**

```bash
# Скопировать service файл
cp catawiki-api.service /etc/systemd/system/

# Перезагрузить systemd
systemctl daemon-reload

# Запустить сервис
systemctl start catawiki-api

# Включить автозапуск
systemctl enable catawiki-api

# Проверить статус
systemctl status catawiki-api

# Посмотреть логи
tail -f /var/log/catawiki-api.log
```

### Шаг 4: Проверьте что API работает

```bash
curl http://localhost:8000/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-16T11:00:00",
  "active_jobs": 0
}
```

---

## 🔧 **2. Настройка n8n**

### Вариант A: Локальный доступ (если n8n на том же сервере)

API доступен по адресу: `http://localhost:8000`

### Вариант B: Внешний доступ (если n8n на другом сервере)

Нужно открыть порт или настроить reverse proxy.

**Опция 1: Открыть порт через firewall**

```bash
# ufw (Ubuntu)
ufw allow 8000/tcp

# firewalld (CentOS)
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

API будет доступен: `http://38.244.194.181:8000`

**Опция 2: Nginx reverse proxy (рекомендуется)**

```nginx
# /etc/nginx/sites-available/catawiki-api
server {
    listen 80;
    server_name catawiki-api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/catawiki-api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## 📊 **3. Примеры Workflow**

### **Workflow 1: Простой парсинг по URL**

```
[Webhook] → [HTTP Request] → [Set] → [Google Sheets]
```

**Настройка:**

1. **Webhook Trigger**
   - Method: POST
   - Path: `/catawiki-scrape`
   - Body: `{"url": "https://catawiki.com/..."}`

2. **HTTP Request Node**
   - Method: POST
   - URL: `http://localhost:8000/scrape`
   - Body:
     ```json
     {
       "url": "{{ $json.url }}",
       "headless": true
     }
     ```

3. **Set Node** (форматирование)
   - Извлечь нужные поля

4. **Google Sheets Node**
   - Operation: Append
   - Sheet: "Catawiki Listings"
   - Columns: title, price, seller, etc.

---

### **Workflow 2: Batch парсинг из Google Sheets**

```
[Schedule] → [Google Sheets Read] → [HTTP Request] → [Wait] → [HTTP Request] → [Google Sheets Write]
```

**Настройка:**

1. **Schedule Trigger**
   - Cron: `0 9 * * *` (каждый день в 9:00)

2. **Google Sheets (Read)**
   - Operation: Read
   - Range: "URLs!A:A"
   - Get all URLs

3. **HTTP Request** (Start Batch Job)
   - Method: POST
   - URL: `http://localhost:8000/scrape-batch`
   - Body:
     ```json
     {
       "urls": {{ $json.urls }},
       "headless": true,
       "save_csv": true
     }
     ```
   - Returns: `job_id`

4. **Wait Node**
   - Wait: 2 minutes (или больше в зависимости от количества URL)

5. **HTTP Request** (Check Job Status)
   - Method: GET
   - URL: `http://localhost:8000/job/{{ $json.job_id }}`

6. **Google Sheets (Write)**
   - Append results

---

### **Workflow 3: Webhook → Scrape → Telegram**

```
[Webhook] → [HTTP Request] → [IF] → [Telegram]
```

**Настройка:**

1. **Webhook Trigger**
   - Принимает URL для парсинга

2. **HTTP Request**
   - Вызывает `/scrape`

3. **IF Node**
   - Condition: `{{ $json.success }} === true`

4. **Telegram Node** (success branch)
   - Message:
     ```
     ✅ Новый лот спарсен!

     Название: {{ $json.data.title }}
     Цена: {{ $json.data.current_price }}
     Продавец: {{ $json.data.seller_name }}
     Ссылка: {{ $json.data.url }}
     ```

---

### **Workflow 4: Airtable Integration**

```
[Airtable Trigger] → [HTTP Request] → [Airtable Update]
```

1. **Airtable Trigger**
   - Trigger: New record in "To Scrape" view
   - Get URL from field

2. **HTTP Request**
   - Scrape URL

3. **Airtable Node**
   - Operation: Update
   - Update record with scraped data

---

## 🔌 **4. API Endpoints**

### **GET /** - Health check
```bash
curl http://localhost:8000/
```

### **GET /health** - Status
```bash
curl http://localhost:8000/health
```

### **POST /scrape** - Scrape single URL (sync)
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.catawiki.com/en/l/98998534-...",
    "headless": true
  }'
```

Response:
```json
{
  "success": true,
  "data": {
    "title": "2022 Beaune...",
    "bottles_count": 6,
    "seller_name": "La cave de Jacques",
    "current_price": "€ 150",
    "shipping_cost": "€ 25",
    "end_date": "2 days",
    "images": [...],
    "url": "...",
    "scraped_at": "2025-11-16T11:00:00"
  }
}
```

### **POST /scrape-async** - Scrape single URL (async)
```bash
curl -X POST http://localhost:8000/scrape-async \
  -H "Content-Type: application/json" \
  -d '{"url": "https://catawiki.com/..."}'
```

Response:
```json
{
  "success": true,
  "job_id": "abc-123-def",
  "data": {
    "message": "Job started",
    "check_status_at": "/job/abc-123-def"
  }
}
```

### **POST /scrape-batch** - Scrape multiple URLs (async)
```bash
curl -X POST http://localhost:8000/scrape-batch \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://catawiki.com/url1",
      "https://catawiki.com/url2"
    ],
    "headless": true,
    "save_csv": true
  }'
```

### **GET /job/{job_id}** - Check job status
```bash
curl http://localhost:8000/job/abc-123-def
```

Response:
```json
{
  "job_id": "abc-123-def",
  "status": "completed",
  "result": {...},
  "created_at": "2025-11-16T11:00:00",
  "completed_at": "2025-11-16T11:05:00"
}
```

### **GET /jobs** - List recent jobs
```bash
curl http://localhost:8000/jobs?status=completed&limit=10
```

### **DELETE /job/{job_id}** - Delete job
```bash
curl -X DELETE http://localhost:8000/job/abc-123-def
```

---

## ⚙️ **5. Автоматизация**

### **Сценарий 1: Ежедневный парсинг списка URL**

1. В Google Sheets храните список URL в колонке A
2. n8n Workflow с Schedule Trigger (каждый день)
3. Читает URL из Google Sheets
4. Отправляет batch запрос
5. Ждет завершения
6. Записывает результаты обратно в Google Sheets
7. Отправляет уведомление в Telegram

### **Сценарий 2: Webhook для внешних систем**

1. Ваша CRM/другая система отправляет webhook с URL
2. n8n получает webhook
3. Запускает парсинг
4. Возвращает результат через webhook response
5. Сохраняет в базу данных

### **Сценарий 3: Мониторинг цен**

1. Schedule Trigger каждые 6 часов
2. Парсит список отслеживаемых лотов
3. Сравнивает с предыдущими ценами
4. Если цена изменилась - отправляет уведомление

---

## 🐛 **Troubleshooting**

### API не запускается

```bash
# Проверить логи
tail -f /var/log/catawiki-api-error.log

# Проверить порт
netstat -tulpn | grep 8000

# Перезапустить сервис
systemctl restart catawiki-api
```

### n8n не может подключиться

```bash
# Проверить firewall
ufw status
ufw allow 8000/tcp

# Проверить что API отвечает
curl http://localhost:8000/health
```

### Ошибки памяти

API использует single worker и headless браузер для экономии памяти.

Если проблемы с памятью:
```bash
# Убедитесь что swap включен
swapon -s

# Если нет - создайте
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## 📚 **Дополнительные ресурсы**

- **n8n Documentation**: https://docs.n8n.io/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **API Swagger UI**: http://localhost:8000/docs (когда сервер запущен)

---

## ✅ **Быстрый старт checklist**

- [ ] Обновить код: `git pull`
- [ ] Установить зависимости: `pip3 install -r requirements_api.txt`
- [ ] Запустить API: `systemctl start catawiki-api`
- [ ] Проверить: `curl http://localhost:8000/health`
- [ ] Открыть Swagger UI: `http://your-server:8000/docs`
- [ ] Создать первый workflow в n8n
- [ ] Протестировать парсинг

Готово! 🎉
