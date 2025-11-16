# 🚀 Инструкция по деплою на сервер

Сервер: `root@38.244.194.181`
Папка: `/root/cataparser`

## Способ 1: Деплой через Git (Рекомендуется)

### На сервере выполните:

```bash
# 1. Подключитесь к серверу
ssh root@38.244.194.181

# 2. Перейдите в нужную директорию или создайте её
cd /root
mkdir -p cataparser
cd cataparser

# 3. Клонируйте репозиторий (замените URL на ваш)
# Если репозиторий уже был клонирован, используйте git pull вместо clone
git clone YOUR_GIT_REPO_URL .

# Или если репозиторий уже есть:
git pull origin main

# 4. Проверьте версию Python
python3 --version

# 5. Установите зависимости
pip3 install -r requirements.txt

# 6. Установите Playwright Chromium
playwright install chromium

# Если playwright команда не найдена:
python3 -m playwright install chromium

# 7. Установите системные зависимости для Playwright (если нужно)
playwright install-deps chromium

# 8. Сделайте скрипты исполняемыми
chmod +x *.py setup.sh

# 9. Проверьте, что всё работает
python3 advanced_scraper.py --help
```

### Тестовый запуск:

```bash
cd /root/cataparser
python3 advanced_scraper.py "https://www.catawiki.com/en/l/98998534-2022-beaune-1-cru-belissand-domaine-francoise-andre-burgundy-6-bottles-0-75l" --headless
```

---

## Способ 2: Деплой через SCP/rsync (с вашего локального компьютера)

### С вашей локальной машины (где есть SSH доступ):

```bash
# Вариант A: Используя deploy.sh скрипт
./deploy.sh

# Вариант B: Вручную через rsync
rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude 'venv' \
    --exclude 'debug_*' \
    /home/user/catascraper/ root@38.244.194.181:/root/cataparser/

# Затем на сервере:
ssh root@38.244.194.181 "cd /root/cataparser && pip3 install -r requirements.txt && playwright install chromium"
```

---

## Способ 3: Ручное копирование файлов

Если у вас нет прямого доступа через SSH с этой машины:

1. Скачайте все файлы из репозитория
2. Используйте SFTP клиент (FileZilla, WinSCP, etc.)
3. Подключитесь к `root@38.244.194.181`
4. Загрузите файлы в `/root/cataparser/`
5. Выполните установку через SSH терминал

---

## После деплоя

### Проверка установки:

```bash
ssh root@38.244.194.181

cd /root/cataparser

# Проверить структуру файлов
ls -la

# Проверить Python
python3 --version

# Проверить установленные пакеты
pip3 list | grep playwright

# Проверить Playwright
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

### Запуск скрапера:

```bash
# Одиночный URL
python3 advanced_scraper.py "URL" --headless

# Batch режим
python3 batch_scraper.py example_urls.txt --headless

# С прокси
python3 advanced_scraper.py "URL" --headless --proxy "http://proxy:port"
```

### Настройка cron для автоматического запуска (опционально):

```bash
# Открыть crontab
crontab -e

# Добавить задачу (например, каждый день в 3:00)
0 3 * * * cd /root/cataparser && python3 batch_scraper.py urls.txt --headless >> /var/log/cataparser.log 2>&1
```

---

## Проблемы и решения

### Проблема: "playwright: command not found"

```bash
# Используйте полный путь через Python
python3 -m playwright install chromium
python3 -m playwright install-deps chromium
```

### Проблема: Недостаточно прав

```bash
# Убедитесь что вы под root или используйте sudo
sudo pip3 install -r requirements.txt
```

### Проблема: Браузер не запускается в headless режиме

```bash
# Установите системные зависимости
apt-get update
apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2
```

### Проблема: Мало памяти

```bash
# Проверить память
free -h

# Если мало памяти, используйте swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## Проверка логов

```bash
# Посмотреть последние ошибки
tail -f /var/log/cataparser.log

# Посмотреть debug файлы
ls -la /root/cataparser/debug_*
ls -la /root/cataparser/error_*
```

---

## Обновление кода

```bash
cd /root/cataparser
git pull origin main
pip3 install -r requirements.txt --upgrade
```
