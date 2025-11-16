#!/bin/bash
# Quick deployment commands for server
# Copy and paste these commands in your SSH terminal

cat << 'EOF'

════════════════════════════════════════════════════════════
  QUICK DEPLOY - Catawiki Scraper
════════════════════════════════════════════════════════════

Скопируйте и выполните следующие команды на сервере:

1️⃣  Подключитесь к серверу:
────────────────────────────────────────────────────────────
ssh root@38.244.194.181


2️⃣  На сервере выполните (копируйте весь блок):
────────────────────────────────────────────────────────────
cd /root && \
mkdir -p cataparser && \
cd cataparser && \
git clone https://github.com/YOUR_USERNAME/catascraper.git . || git pull origin main && \
python3 --version && \
pip3 install -r requirements.txt && \
python3 -m playwright install chromium && \
python3 -m playwright install-deps chromium && \
chmod +x *.py setup.sh && \
echo "" && \
echo "✅ Деплой завершен!" && \
echo "" && \
echo "Для запуска:" && \
echo "python3 advanced_scraper.py 'URL' --headless"


3️⃣  Тестовый запуск:
────────────────────────────────────────────────────────────
cd /root/cataparser
python3 advanced_scraper.py "https://www.catawiki.com/en/l/98998534-2022-beaune-1-cru-belissand-domaine-francoise-andre-burgundy-6-bottles-0-75l" --headless


4️⃣  Если git репозитория нет, используйте rsync:
────────────────────────────────────────────────────────────
# С вашей локальной машины (где есть код):
rsync -avz --exclude .git --exclude __pycache__ --exclude venv \
  /path/to/catascraper/ root@38.244.194.181:/root/cataparser/

# Затем на сервере:
ssh root@38.244.194.181
cd /root/cataparser
pip3 install -r requirements.txt
python3 -m playwright install chromium


════════════════════════════════════════════════════════════

⚠️  ВАЖНО:
1. Замените YOUR_USERNAME на ваш GitHub username
2. Или используйте rsync если репозиторий не публичный
3. Убедитесь что на сервере установлен Python 3.8+

════════════════════════════════════════════════════════════

EOF
