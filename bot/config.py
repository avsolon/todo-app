import os
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Токен бота (получить у @BotFather в Telegram)
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Создайте файл .env с токеном.")

# API бекенда
API_URL = os.getenv("API_URL", "http://backend:8000/api")