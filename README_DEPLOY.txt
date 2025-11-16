═══════════════════════════════════════════════════════════════════
  БЫСТРАЯ ИНСТРУКЦИЯ ПО ДЕПЛОЮ НА СЕРВЕР
═══════════════════════════════════════════════════════════════════

Сервер: root@38.244.194.181
Папка: /root/cataparser

═══════════════════════════════════════════════════════════════════
  ВАРИАНТ 1: Автоматический деплой через server_setup.sh
═══════════════════════════════════════════════════════════════════

1. Скопируйте файл server_setup.sh на сервер:

   scp server_setup.sh root@38.244.194.181:/root/

2. Подключитесь к серверу:

   ssh root@38.244.194.181

3. Запустите скрипт установки:

   chmod +x /root/server_setup.sh
   /root/server_setup.sh

4. Готово! Скрапер установлен в /root/cataparser


═══════════════════════════════════════════════════════════════════
  ВАРИАНТ 2: Ручная установка (если нет Git)
═══════════════════════════════════════════════════════════════════

1. На сервере создайте папку:

   ssh root@38.244.194.181
   mkdir -p /root/cataparser
   cd /root/cataparser

2. С вашей локальной машины скопируйте файлы:

   # Если вы на Linux/Mac:
   cd /home/user/catascraper
   tar czf cataparser.tar.gz --exclude='.git' --exclude='__pycache__' --exclude='venv' .
   scp cataparser.tar.gz root@38.244.194.181:/root/cataparser/

   # Или используйте rsync:
   rsync -avz --exclude .git --exclude __pycache__ --exclude venv \
     /home/user/catascraper/ root@38.244.194.181:/root/cataparser/

3. На сервере распакуйте и установите:

   ssh root@38.244.194.181
   cd /root/cataparser
   tar xzf cataparser.tar.gz  # если использовали tar
   pip3 install -r requirements.txt
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium
   chmod +x *.py


═══════════════════════════════════════════════════════════════════
  ВАРИАНТ 3: Через Git (если репозиторий на GitHub)
═══════════════════════════════════════════════════════════════════

1. Подключитесь к серверу:

   ssh root@38.244.194.181

2. Клонируйте репозиторий:

   cd /root
   git clone https://github.com/YOUR_USERNAME/catascraper.git cataparser
   cd cataparser

3. Установите зависимости:

   pip3 install -r requirements.txt
   python3 -m playwright install chromium
   python3 -m playwright install-deps chromium


═══════════════════════════════════════════════════════════════════
  ПРОВЕРКА УСТАНОВКИ
═══════════════════════════════════════════════════════════════════

После установки выполните на сервере:

ssh root@38.244.194.181

cd /root/cataparser

# Проверить файлы
ls -la

# Проверить Python
python3 --version

# Проверить Playwright
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"

# Тестовый запуск
python3 advanced_scraper.py \
  "https://www.catawiki.com/en/l/98998534-2022-beaune-1-cru-belissand-domaine-francoise-andre-burgundy-6-bottles-0-75l" \
  --headless


═══════════════════════════════════════════════════════════════════
  ИСПОЛЬЗОВАНИЕ
═══════════════════════════════════════════════════════════════════

# Одиночный URL:
python3 advanced_scraper.py "URL" --headless

# Batch режим:
python3 batch_scraper.py urls.txt --headless

# С прокси:
python3 advanced_scraper.py "URL" --headless --proxy "http://proxy:8080"


═══════════════════════════════════════════════════════════════════
  РЕШЕНИЕ ПРОБЛЕМ
═══════════════════════════════════════════════════════════════════

1. Если Python 3 не установлен:
   apt-get update && apt-get install -y python3 python3-pip

2. Если playwright не может установить браузер:
   python3 -m playwright install chromium --with-deps

3. Если не хватает памяти:
   # Создать swap файл
   fallocate -l 2G /swapfile
   chmod 600 /swapfile
   mkswap /swapfile
   swapon /swapfile

4. Если ошибка с системными библиотеками:
   apt-get update
   apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 \
     libcups2 libdrm2 libxkbcommon0 libxcomposite1


═══════════════════════════════════════════════════════════════════
  ПОЛНАЯ ДОКУМЕНТАЦИЯ
═══════════════════════════════════════════════════════════════════

Смотрите файл DEPLOY.md для детальных инструкций.


═══════════════════════════════════════════════════════════════════
